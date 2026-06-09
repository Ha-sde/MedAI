from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app import db
from app.models import Patient, OTPRecord
from app.services.sms_service import send_otp_sms
from datetime import datetime, timedelta
import random
import string

auth_bp = Blueprint('auth', __name__)

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    phone = data.get('phone', '').strip()
    
    if not phone or len(phone) < 10:
        return jsonify({'error': 'Valid phone number required'}), 400
    
    patient = Patient.query.filter_by(phone=phone).first()
    if not patient:
        return jsonify({'error': 'Patient not found. Please register first.', 'not_found': True}), 404
    
    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    otp_record = OTPRecord(
        patient_id=patient.id,
        otp=otp,
        expires_at=expires_at
    )
    db.session.add(otp_record)
    db.session.commit()
    
    # Send SMS OTP via Twilio
    sms_sent = send_otp_sms(phone, otp)
    
    if sms_sent:
        print(f"[OTP] Phone: {phone} (SMS sent successfully via Twilio)")
        return jsonify({
            'message': 'OTP sent successfully',
            'expires_in': 600
        })
    else:
        # Fallback to demo mode if Twilio is not configured
        print(f"[OTP] Phone: {phone} | OTP: {otp} (Demo Mode fallback)")
        return jsonify({
            'message': 'OTP sent successfully (Demo Mode)',
            'otp': otp,
            'expires_in': 600
        })

@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    phone = data.get('phone', '').strip()
    otp = data.get('otp', '').strip()
    
    patient = Patient.query.filter_by(phone=phone).first()
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    otp_record = OTPRecord.query.filter_by(
        patient_id=patient.id,
        otp=otp,
        used=False
    ).filter(OTPRecord.expires_at > datetime.utcnow()).order_by(OTPRecord.created_at.desc()).first()
    
    if not otp_record:
        return jsonify({'error': 'Invalid or expired OTP'}), 401
    
    otp_record.used = True
    db.session.commit()
    
    access_token = create_access_token(identity=str(patient.id))
    
    return jsonify({
        'token': access_token,
        'patient': patient.to_dict()
    })

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    required = ['phone', 'name']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    phone = data['phone'].strip()
    if Patient.query.filter_by(phone=phone).first():
        return jsonify({'error': 'Phone number already registered'}), 409
    
    patient = Patient(
        phone=phone,
        name=data['name'].strip(),
        gender=data.get('gender'),
        age=data.get('age'),
        email=data.get('email', '').strip(),
        address=data.get('address', '').strip(),
        blood_group=data.get('blood_group', '').strip(),
        allergies=data.get('allergies', '').strip()
    )
    
    db.session.add(patient)
    db.session.commit()
    
    return jsonify({
        'message': 'Registration successful',
        'patient': patient.to_dict()
    }), 201

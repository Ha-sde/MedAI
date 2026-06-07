from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Patient, Consultation
from app.services.llm_service import analyze_transcript, analyze_image
from app.services.pdf_service import generate_report_pdf
import os, json, uuid
from werkzeug.utils import secure_filename

consultation_bp = Blueprint('consultation', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'dcm', 'bmp', 'tiff', 'webp'}
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
MEDIA_TYPES = {
    'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
    'gif': 'image/gif', 'bmp': 'image/bmp', 'tiff': 'image/tiff', 'webp': 'image/webp'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@consultation_bp.route('/analyze', methods=['POST'])
@jwt_required()
def analyze_consultation():
    """Main endpoint: takes transcript + files, returns AI analysis."""
    patient_id = int(get_jwt_identity())
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    transcript = request.form.get('transcript', '').strip()
    doctor_name = request.form.get('doctor_name', 'Dr. Attending').strip()
    
    if not transcript:
        return jsonify({'error': 'Transcript is required'}), 400
    
    # Handle file uploads
    uploaded_files = []
    attachments_analysis = []
    upload_folder = current_app.config['UPLOAD_FOLDER']
    patient_folder = os.path.join(upload_folder, str(patient_id))
    os.makedirs(patient_folder, exist_ok=True)
    
    files = request.files.getlist('files')
    for file in files:
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4()}.{ext}"
            filepath = os.path.join(patient_folder, filename)
            file.save(filepath)
            rel_path = f"uploads/{patient_id}/{filename}"
            uploaded_files.append(rel_path)
            
            # Analyze images with vision AI
            if ext in IMAGE_EXTENSIONS:
                with open(filepath, 'rb') as f:
                    image_data = f.read()
                media_type = MEDIA_TYPES.get(ext, 'image/jpeg')
                img_analysis = analyze_image(image_data, media_type)
                img_analysis['file'] = filename
                attachments_analysis.append(img_analysis)
    
    # Get patient history for context
    history = Consultation.query.filter_by(patient_id=patient_id)\
                .order_by(Consultation.date.desc()).limit(10).all()
    history_data = [h.to_dict() for h in history]
    
    # Run LLM analysis
    analysis = analyze_transcript(transcript, history_data, attachments_analysis)
    
    # Save consultation
    import json as j
    consultation = Consultation(
        patient_id=patient_id,
        raw_transcript=transcript,
        chief_complaint=analysis.get('chief_complaint', ''),
        symptoms=j.dumps(analysis.get('symptoms', [])),
        diagnosis=j.dumps(analysis.get('diagnosis', [])),
        medications=j.dumps(analysis.get('medications', [])),
        vitals=j.dumps(analysis.get('vitals', {})),
        lab_results=j.dumps(analysis.get('lab_results', {})),
        treatment_plan=analysis.get('treatment_plan', ''),
        follow_up=analysis.get('follow_up', ''),
        notes=analysis.get('notes', ''),
        severity=analysis.get('severity', 'medium'),
        ai_analysis=analysis.get('ai_analysis', ''),
        attachments=j.dumps(uploaded_files),
        doctor_name=doctor_name
    )
    
    db.session.add(consultation)
    db.session.flush()  # Get the ID
    
    # Generate PDF
    pdf_folder = os.path.join(upload_folder, 'reports')
    os.makedirs(pdf_folder, exist_ok=True)
    pdf_filename = f"report_{patient_id}_{consultation.id}.pdf"
    pdf_path = os.path.join(pdf_folder, pdf_filename)
    
    try:
        generate_report_pdf(patient, consultation, pdf_path)
        consultation.pdf_path = f"uploads/reports/{pdf_filename}"
    except Exception as e:
        print(f"[PDF Error] {e}")
    
    db.session.commit()
    
    result = consultation.to_dict()
    result['attachments_analysis'] = attachments_analysis
    return jsonify(result), 201

@consultation_bp.route('/<int:consultation_id>', methods=['GET'])
@jwt_required()
def get_consultation(consultation_id):
    patient_id = int(get_jwt_identity())
    c = Consultation.query.filter_by(id=consultation_id, patient_id=patient_id).first()
    if not c:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(c.to_dict())

@consultation_bp.route('/<int:consultation_id>/pdf', methods=['GET'])
@jwt_required()
def download_pdf(consultation_id):
    patient_id = int(get_jwt_identity())
    c = Consultation.query.filter_by(id=consultation_id, patient_id=patient_id).first()
    if not c or not c.pdf_path:
        return jsonify({'error': 'PDF not found'}), 404
    
    pdf_full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 
                                  '..', c.pdf_path)
    pdf_full_path = os.path.normpath(pdf_full_path)
    
    if not os.path.exists(pdf_full_path):
        # Try direct path
        upload_root = os.path.dirname(current_app.config['UPLOAD_FOLDER'])
        pdf_full_path = os.path.join(upload_root, c.pdf_path)
    
    if os.path.exists(pdf_full_path):
        return send_file(pdf_full_path, as_attachment=True, 
                        download_name=f"medical_report_{consultation_id}.pdf")
    
    return jsonify({'error': 'PDF file not found on disk'}), 404

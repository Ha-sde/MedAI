from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Patient, Consultation
import json

patient_bp = Blueprint('patient', __name__)

@patient_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    patient_id = get_jwt_identity()
    patient = Patient.query.get(int(patient_id))
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    return jsonify(patient.to_dict())

@patient_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    patient_id = get_jwt_identity()
    consultations = Consultation.query.filter_by(
        patient_id=int(patient_id)
    ).order_by(Consultation.date.desc()).all()
    return jsonify([c.to_dict() for c in consultations])

@patient_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_summary():
    patient_id = get_jwt_identity()
    patient = Patient.query.get(int(patient_id))
    consultations = Consultation.query.filter_by(
        patient_id=int(patient_id)
    ).order_by(Consultation.date.asc()).all()
    
    if not consultations:
        return jsonify({'summary': None, 'stats': {}, 'charts': {}})
    
    # Build summary stats
    all_diagnoses = []
    all_symptoms = []
    all_medications = []
    severity_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
    monthly_visits = {}
    
    for c in consultations:
        if c.diagnosis:
            try:
                all_diagnoses.extend(json.loads(c.diagnosis))
            except: pass
        if c.symptoms:
            try:
                all_symptoms.extend(json.loads(c.symptoms))
            except: pass
        if c.medications:
            try:
                all_medications.extend(json.loads(c.medications))
            except: pass
        if c.severity and c.severity in severity_counts:
            severity_counts[c.severity] += 1
        
        month_key = c.date.strftime('%b %Y') if c.date else 'Unknown'
        monthly_visits[month_key] = monthly_visits.get(month_key, 0) + 1
    
    # Frequency counts
    diag_freq = {}
    for d in all_diagnoses:
        diag_freq[d] = diag_freq.get(d, 0) + 1
    
    sym_freq = {}
    for s in all_symptoms:
        sym_freq[s] = sym_freq.get(s, 0) + 1
    
    med_freq = {}
    for m in all_medications:
        med_freq[m] = med_freq.get(m, 0) + 1
    
    stats = {
        'total_visits': len(consultations),
        'first_visit': consultations[0].date.isoformat() if consultations[0].date else None,
        'last_visit': consultations[-1].date.isoformat() if consultations[-1].date else None,
        'total_diagnoses': len(set(all_diagnoses)),
        'total_medications': len(set(all_medications)),
        'severity_distribution': severity_counts,
        'most_common_diagnoses': sorted(diag_freq.items(), key=lambda x: x[1], reverse=True)[:5],
        'most_common_symptoms': sorted(sym_freq.items(), key=lambda x: x[1], reverse=True)[:5],
        'most_prescribed_medications': sorted(med_freq.items(), key=lambda x: x[1], reverse=True)[:5],
        'monthly_visits': monthly_visits,
        'health_score': _calculate_health_score(severity_counts, len(consultations))
    }
    
    return jsonify({
        'patient': patient.to_dict(),
        'stats': stats,
        'recent_consultations': [c.to_dict() for c in consultations[-3:]]
    })

def _calculate_health_score(severity_counts, total_visits):
    if total_visits == 0:
        return 100
    weighted = (
        severity_counts.get('low', 0) * 10 +
        severity_counts.get('medium', 0) * 30 +
        severity_counts.get('high', 0) * 60 +
        severity_counts.get('critical', 0) * 100
    )
    score = max(0, 100 - int(weighted / max(total_visits, 1)))
    return score

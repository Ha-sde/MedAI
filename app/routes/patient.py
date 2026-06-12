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
    
    # Build detailed vitals and health history
    vitals_history = []
    health_score_history = []
    running_severity_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
    
    for idx, c in enumerate(consultations, 1):
        c_date = c.date.strftime('%d %b') if c.date else f'Visit {idx}'
        
        # Vitals extraction
        c_vitals = {}
        if c.vitals:
            try:
                c_vitals = json.loads(c.vitals)
            except: pass
            
        vitals_history.append({
            'date': c_date,
            'bp': c_vitals.get('bp', ''),
            'pulse': c_vitals.get('pulse', ''),
            'spo2': c_vitals.get('spo2', ''),
            'temp': c_vitals.get('temp', '')
        })
        
        # Health score tracking
        if c.severity and c.severity in running_severity_counts:
            running_severity_counts[c.severity] += 1
            
        score_so_far = _calculate_health_score(running_severity_counts, idx)
        health_score_history.append({
            'date': c_date,
            'score': score_so_far
        })
        
    # Generate clinical synthesis narrative in formal medical terms
    unique_diags = list(set(all_diagnoses))
    unique_syms = list(set(all_symptoms))
    latest_c = consultations[-1]
    
    latest_vitals = {}
    if latest_c.vitals:
        try:
            latest_vitals = json.loads(latest_c.vitals)
        except: pass
        
    diag_summary = ", ".join(unique_diags[:3]) if unique_diags else "no active diagnostic classifications"
    sym_summary = ", ".join(unique_syms[:4]) if unique_syms else "no chronic symptoms recorded"
    
    synthesis = f"Clinical Assessment: Patient {patient.name} ({patient.age or 'N/A'} yo {patient.gender or 'gender unspecified'}) "
    synthesis += f"presents with {len(consultations)} consultations. Longitudinal records indicate history of: {diag_summary}. "
    if unique_syms:
        synthesis += f"Associated symptom markers: {sym_summary}. "
    synthesis += f"During the latest encounter on {latest_c.date.strftime('%d-%b-%Y') if latest_c.date else 'recent checkup'}, "
    synthesis += f"patient presented with: '{latest_c.chief_complaint or 'routine checkup'}' (Severity Index: '{latest_c.severity or 'medium'}'). "
    
    v_parts = []
    if latest_vitals.get('bp'): v_parts.append(f"BP {latest_vitals.get('bp')} mmHg")
    if latest_vitals.get('pulse'): v_parts.append(f"HR {latest_vitals.get('pulse')} bpm")
    if latest_vitals.get('spo2'): v_parts.append(f"SpO2 {latest_vitals.get('spo2')}%")
    if v_parts:
        synthesis += f"Objective vitals at index encounter: {', '.join(v_parts)}. "
        
    synthesis += "\n\nRecommendations / Guidelines: "
    if any(k in diag_summary.lower() for k in ['hypertension', 'heart', 'cardiac', 'blood pressure']):
        synthesis += "Initiate routine metabolic panel and daily blood pressure logs. Recommend low-sodium diet, moderate aerobic exercises, and strict adherence to pharmacotherapy. Schedule cardiology follow-up if BP exceeds 140/90 mmHg."
    elif any(k in diag_summary.lower() for k in ['arthritis', 'fracture', 'joint', 'back pain', 'knee', 'spine', 'bone', 'muscle']):
        synthesis += "Maintain conservative orthopedic management. Initiate physical rehabilitation for joint range of motion (ROM) and structural offloading during acute flare-ups. Monitor analgesic usage."
    elif any(k in diag_summary.lower() for k in ['asthma', 'bronchitis', 'pneumonia', 'lung']):
        synthesis += "Recommend peak flow monitoring and check inhaler technique. Maintain active allergen avoidance and immunization schedule. Seek emergency care if SpO2 drops below 92%."
    else:
        synthesis += "Ensure regular clinical follow-ups. Monitor vital signs and maintain normal hydration. Follow up as symptoms evolve."
        
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
        'health_score': _calculate_health_score(severity_counts, len(consultations)),
        'vitals_history': vitals_history,
        'health_score_history': health_score_history,
        'clinical_synthesis': synthesis
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

from flask import Blueprint, send_file, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Consultation
import os

report_bp = Blueprint('report', __name__)

@report_bp.route('/<int:consultation_id>/download', methods=['GET'])
@jwt_required()
def download_report(consultation_id):
    patient_id = int(get_jwt_identity())
    c = Consultation.query.filter_by(id=consultation_id, patient_id=patient_id).first()
    if not c:
        return jsonify({'error': 'Report not found'}), 404
    
    # Resolve the expected PDF file path
    upload_folder = current_app.config['UPLOAD_FOLDER']
    pdf_folder = os.path.join(upload_folder, 'reports')
    os.makedirs(pdf_folder, exist_ok=True)
    pdf_filename = f"report_{patient_id}_{c.id}.pdf"
    pdf_full_path = os.path.normpath(os.path.join(pdf_folder, pdf_filename))
    
    # On-demand generation if missing
    if not c.pdf_path or not os.path.exists(pdf_full_path):
        from app.models import Patient
        from app.services.pdf_service import generate_report_pdf
        from app import db
        
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
            
        try:
            generate_report_pdf(patient, c, pdf_full_path)
            c.pdf_path = f"uploads/reports/{pdf_filename}"
            db.session.commit()
        except Exception as e:
            return jsonify({'error': f'Failed to generate PDF: {str(e)}'}), 500
            
    if os.path.exists(pdf_full_path):
        return send_file(pdf_full_path, mimetype='application/pdf',
                        as_attachment=True, 
                        download_name=f'MedAI_Report_{consultation_id}.pdf')
    
    return jsonify({'error': 'PDF file missing on server'}), 404

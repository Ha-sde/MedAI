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
    
    if not c.pdf_path:
        return jsonify({'error': 'PDF not generated yet'}), 404
    
    # Build the actual path
    base = os.path.dirname(os.path.dirname(current_app.config['UPLOAD_FOLDER']))
    pdf_path = os.path.join(base, c.pdf_path)
    
    if not os.path.exists(pdf_path):
        pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 
                                'reports', os.path.basename(c.pdf_path))
    
    if os.path.exists(pdf_path):
        return send_file(pdf_path, mimetype='application/pdf',
                        as_attachment=True, 
                        download_name=f'MedAI_Report_{consultation_id}.pdf')
    
    return jsonify({'error': 'PDF file missing'}), 404

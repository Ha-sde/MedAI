from app import db
from datetime import datetime
import json

class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10))
    age = db.Column(db.Integer)
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    blood_group = db.Column(db.String(5))
    allergies = db.Column(db.Text)
    photo_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    consultations = db.relationship('Consultation', backref='patient', lazy=True, cascade='all, delete-orphan')
    otp_records = db.relationship('OTPRecord', backref='patient', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'phone': self.phone,
            'name': self.name,
            'gender': self.gender,
            'age': self.age,
            'email': self.email,
            'address': self.address,
            'blood_group': self.blood_group,
            'allergies': self.allergies,
            'photo_url': self.photo_url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class OTPRecord(db.Model):
    __tablename__ = 'otp_records'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    used = db.Column(db.Boolean, default=False)


class Consultation(db.Model):
    __tablename__ = 'consultations'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Raw doctor input
    raw_transcript = db.Column(db.Text)
    
    # NLP extracted structured data
    chief_complaint = db.Column(db.Text)
    symptoms = db.Column(db.Text)       # JSON array
    diagnosis = db.Column(db.Text)      # JSON array
    medications = db.Column(db.Text)    # JSON array
    vitals = db.Column(db.Text)         # JSON object
    lab_results = db.Column(db.Text)    # JSON object
    treatment_plan = db.Column(db.Text)
    follow_up = db.Column(db.Text)
    notes = db.Column(db.Text)
    
    # AI analysis
    ai_analysis = db.Column(db.Text)    # Full AI reasoning
    severity = db.Column(db.String(20)) # low/medium/high/critical
    
    # Uploaded files
    attachments = db.Column(db.Text)    # JSON array of file paths
    
    # Generated PDF path
    pdf_path = db.Column(db.String(255))
    
    doctor_name = db.Column(db.String(100), default='Dr. Attending')

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'date': self.date.isoformat() if self.date else None,
            'raw_transcript': self.raw_transcript,
            'chief_complaint': self.chief_complaint,
            'symptoms': json.loads(self.symptoms) if self.symptoms else [],
            'diagnosis': json.loads(self.diagnosis) if self.diagnosis else [],
            'medications': json.loads(self.medications) if self.medications else [],
            'vitals': json.loads(self.vitals) if self.vitals else {},
            'lab_results': json.loads(self.lab_results) if self.lab_results else {},
            'treatment_plan': self.treatment_plan,
            'follow_up': self.follow_up,
            'notes': self.notes,
            'ai_analysis': self.ai_analysis,
            'severity': self.severity,
            'attachments': json.loads(self.attachments) if self.attachments else [],
            'pdf_path': self.pdf_path,
            'doctor_name': self.doctor_name
        }

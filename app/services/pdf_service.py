import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, 
                                 TableStyle, HRFlowable, KeepTogether)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
import json

# Color palette
BLACK = colors.HexColor('#0a0a0a')
WHITE = colors.HexColor('#ffffff')
ACCENT = colors.HexColor('#00d4ff')
DARK_GRAY = colors.HexColor('#1a1a2e')
MID_GRAY = colors.HexColor('#2d2d2d')
LIGHT_GRAY = colors.HexColor('#888888')
GREEN = colors.HexColor('#00ff88')
RED = colors.HexColor('#ff4444')
ORANGE = colors.HexColor('#ffaa00')

SEVERITY_COLORS = {
    'low': colors.HexColor('#00ff88'),
    'medium': colors.HexColor('#ffaa00'),
    'high': colors.HexColor('#ff6600'),
    'critical': colors.HexColor('#ff0000')
}

def generate_report_pdf(patient, consultation, output_path: str) -> str:
    """Generate a professional medical report PDF."""
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle('Title', fontSize=22, textColor=WHITE, 
                                  backColor=BLACK, spaceAfter=6, alignment=TA_CENTER,
                                  fontName='Helvetica-Bold', leading=28)
    
    subtitle_style = ParagraphStyle('Subtitle', fontSize=11, textColor=ACCENT,
                                     spaceAfter=4, alignment=TA_CENTER,
                                     fontName='Helvetica')
    
    section_style = ParagraphStyle('Section', fontSize=12, textColor=ACCENT,
                                    spaceBefore=14, spaceAfter=6,
                                    fontName='Helvetica-Bold')
    
    body_style = ParagraphStyle('Body', fontSize=10, textColor=colors.HexColor('#333333'),
                                 spaceAfter=4, fontName='Helvetica', leading=14)
    
    label_style = ParagraphStyle('Label', fontSize=9, textColor=LIGHT_GRAY,
                                  fontName='Helvetica-Bold', spaceAfter=2)
    
    # ─── HEADER ───
    header_data = [[
        Paragraph('MedAI', ParagraphStyle('H', fontSize=28, textColor=ACCENT, 
                                           fontName='Helvetica-Bold')),
        Paragraph('MEDICAL CONSULTATION REPORT', ParagraphStyle('H2', fontSize=13, 
                   textColor=WHITE, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
    ]]
    header_table = Table(header_data, colWidths=[8*cm, 9.5*cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BLACK),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 14),
        ('BOTTOMPADDING', (0,0), (-1,-1), 14),
        ('LEFTPADDING', (0,0), (0,-1), 14),
        ('RIGHTPADDING', (-1,0), (-1,-1), 14),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))
    
    # Accent line
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT))
    story.append(Spacer(1, 12))
    
    # ─── PATIENT INFO ───
    story.append(Paragraph('PATIENT INFORMATION', section_style))
    
    severity = consultation.severity or 'medium'
    sev_color = SEVERITY_COLORS.get(severity, ORANGE)
    
    patient_data = [
        ['Patient Name', patient.name, 'Date', consultation.date.strftime('%d %B %Y') if consultation.date else 'N/A'],
        ['Age / Gender', f"{patient.age or 'N/A'} yrs / {patient.gender or 'N/A'}", 'Phone', patient.phone or 'N/A'],
        ['Blood Group', patient.blood_group or 'N/A', 'Severity', severity.upper()],
        ['Consulting Doctor', consultation.doctor_name or 'Dr. Attending', 'Report ID', f'MED-{consultation.id:05d}'],
    ]
    
    pt_table = Table(patient_data, colWidths=[4*cm, 5.5*cm, 3.5*cm, 4.5*cm])
    pt_style = TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f0f0f0')),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#f0f0f0')),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
        ('FONTNAME', (3,0), (3,-1), 'Helvetica'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [WHITE, colors.HexColor('#fafafa')]),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('TEXTCOLOR', (3,2), (3,2), sev_color),
        ('FONTNAME', (3,2), (3,2), 'Helvetica-Bold'),
    ])
    pt_table.setStyle(pt_style)
    story.append(pt_table)
    story.append(Spacer(1, 14))
    
    # ─── CHIEF COMPLAINT ───
    if consultation.chief_complaint:
        story.append(Paragraph('CHIEF COMPLAINT', section_style))
        complaint_box = Table([[Paragraph(consultation.chief_complaint, body_style)]], 
                               colWidths=[17.5*cm])
        complaint_box.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fff8e1')),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('BOX', (0,0), (-1,-1), 1.5, ORANGE),
            ('ROUNDEDCORNERS', [4]),
        ]))
        story.append(complaint_box)
        story.append(Spacer(1, 10))
    
    # ─── SYMPTOMS & DIAGNOSIS ───
    syms = json.loads(consultation.symptoms) if consultation.symptoms else []
    diags = json.loads(consultation.diagnosis) if consultation.diagnosis else []
    
    if syms or diags:
        row = []
        
        if syms:
            sym_items = [Paragraph('SYMPTOMS', section_style)]
            for s in syms:
                sym_items.append(Paragraph(f'• {s}', body_style))
            row.append(sym_items)
        
        if diags:
            diag_items = [Paragraph('DIAGNOSIS', section_style)]
            for d in diags:
                diag_items.append(Paragraph(f'◆ {d}', ParagraphStyle('DiagP', fontSize=10, 
                    textColor=colors.HexColor('#1a237e'), fontName='Helvetica-Bold', spaceAfter=4)))
            row.append(diag_items)
        
        if len(row) == 2:
            sd_table = Table([row], colWidths=[8.5*cm, 8.5*cm])
            sd_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ]))
            story.append(sd_table)
        elif row:
            for item in row[0]:
                story.append(item)
        
        story.append(Spacer(1, 10))
    
    # ─── VITALS ───
    vitals = json.loads(consultation.vitals) if consultation.vitals else {}
    if vitals:
        story.append(Paragraph('VITAL SIGNS', section_style))
        vital_labels = {
            'bp': 'Blood Pressure', 'pulse': 'Pulse Rate', 'temp': 'Temperature',
            'spo2': 'SpO2', 'weight': 'Weight', 'height': 'Height',
            'respiratory_rate': 'Resp. Rate'
        }
        vital_rows = []
        vital_items = [(vital_labels.get(k, k.title()), v) for k, v in vitals.items() if v]
        
        for i in range(0, len(vital_items), 4):
            row_data = []
            for label, value in vital_items[i:i+4]:
                row_data.extend([label, value])
            while len(row_data) < 8:
                row_data.extend(['', ''])
            vital_rows.append(row_data)
        
        if vital_rows:
            v_table = Table(vital_rows, colWidths=[3.5*cm, 2.5*cm, 3.5*cm, 2.5*cm, 3*cm, 2*cm, 3*cm, 2*cm])
            v_table.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
                ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
                ('FONTNAME', (4,0), (4,-1), 'Helvetica-Bold'),
                ('FONTNAME', (6,0), (6,-1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0,0), (0,-1), LIGHT_GRAY),
                ('TEXTCOLOR', (2,0), (2,-1), LIGHT_GRAY),
                ('TEXTCOLOR', (4,0), (4,-1), LIGHT_GRAY),
                ('TEXTCOLOR', (6,0), (6,-1), LIGHT_GRAY),
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f5f5f5')),
                ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#dddddd')),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(v_table)
            story.append(Spacer(1, 10))
    
    # ─── MEDICATIONS ───
    meds = json.loads(consultation.medications) if consultation.medications else []
    if meds:
        story.append(Paragraph('PRESCRIBED MEDICATIONS', section_style))
        med_data = [['#', 'Medication', 'Instructions']]
        for i, med in enumerate(meds, 1):
            parts = med.split(' ', 2) if ' ' in med else [med, '', '']
            name = parts[0] if parts else med
            dosage = parts[1] if len(parts) > 1 else ''
            freq = parts[2] if len(parts) > 2 else ''
            med_data.append([str(i), f'{name} {dosage}'.strip(), freq])
        
        med_table = Table(med_data, colWidths=[1*cm, 8*cm, 8.5*cm])
        med_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), BLACK),
            ('TEXTCOLOR', (0,0), (-1,0), ACCENT),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, colors.HexColor('#f0f8ff')]),
            ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#cccccc')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ]))
        story.append(med_table)
        story.append(Spacer(1, 10))
    
    # ─── TREATMENT PLAN ───
    if consultation.treatment_plan:
        story.append(Paragraph('TREATMENT PLAN', section_style))
        story.append(Paragraph(consultation.treatment_plan, body_style))
        story.append(Spacer(1, 8))
    
    # ─── AI ANALYSIS ───
    if consultation.ai_analysis:
        story.append(Paragraph('CLINICAL AI ANALYSIS', section_style))
        ai_box = Table([[Paragraph(consultation.ai_analysis, ParagraphStyle('AI', 
                         fontSize=9.5, textColor=colors.HexColor('#1a1a1a'), 
                         fontName='Helvetica', leading=14, spaceAfter=0))]], 
                        colWidths=[17.5*cm])
        ai_box.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#e8f5e9')),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#00c853')),
        ]))
        story.append(ai_box)
        story.append(Spacer(1, 10))
    
    # ─── FOLLOW UP ───
    if consultation.follow_up:
        story.append(Paragraph('FOLLOW-UP INSTRUCTIONS', section_style))
        story.append(Paragraph(consultation.follow_up, body_style))
        story.append(Spacer(1, 10))
    
    # ─── FOOTER ───
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cccccc')))
    story.append(Spacer(1, 6))
    
    footer_data = [[
        Paragraph('Generated by MedAI Clinical Intelligence Platform', 
                   ParagraphStyle('F', fontSize=8, textColor=LIGHT_GRAY, fontName='Helvetica')),
        Paragraph(f'Report Date: {datetime.now().strftime("%d %b %Y, %I:%M %p")}',
                   ParagraphStyle('F2', fontSize=8, textColor=LIGHT_GRAY, fontName='Helvetica', alignment=TA_RIGHT))
    ]]
    footer_table = Table(footer_data, colWidths=[10*cm, 7.5*cm])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(footer_table)
    
    doc.build(story)
    return output_path

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

# Themes definitions for specialized clinical reports
THEMES = {
    'general': {
        'PRIMARY': colors.HexColor('#0a0a0a'),      # Dark Black
        'ACCENT': colors.HexColor('#0088cc'),       # Clean Blue
        'SECONDARY': colors.HexColor('#00d4ff'),    # Cyan Accent
        'BG_LIGHT': colors.HexColor('#f4fafd'),     # Light Blue Tint
        'CARD_BG': colors.HexColor('#e8f5e9'),      # Light Emerald
        'CARD_BORDER': colors.HexColor('#00c853'),  # Bold Green
        'TITLE_COLOR': colors.HexColor('#00d4ff'),
        'TITLE': 'GENERAL MEDICINE CLINICAL REPORT'
    },
    'cardiac': {
        'PRIMARY': colors.HexColor('#1f0808'),      # Dark Crimson
        'ACCENT': colors.HexColor('#b71c1c'),       # Cardiology Red
        'SECONDARY': colors.HexColor('#e53935'),    # Vivid Red
        'BG_LIGHT': colors.HexColor('#ffebee'),     # Light Red Tint
        'CARD_BG': colors.HexColor('#fffde7'),      # Warning Yellow Tint
        'CARD_BORDER': colors.HexColor('#fbc02d'),  # Warning Amber Border
        'TITLE_COLOR': colors.HexColor('#ff8a80'),
        'TITLE': 'CARDIOLOGY CLINICAL ASSESSMENT'
    },
    'ortho': {
        'PRIMARY': colors.HexColor('#0b1d33'),      # Steel Navy
        'ACCENT': colors.HexColor('#006064'),       # Deep Teal
        'SECONDARY': colors.HexColor('#00838f'),    # Slate Teal
        'BG_LIGHT': colors.HexColor('#e0f7fa'),     # Light Cyan Tint
        'CARD_BG': colors.HexColor('#f3e5f5'),      # Mobility Purple Tint
        'CARD_BORDER': colors.HexColor('#8e24aa'),  # Purple Border
        'TITLE_COLOR': colors.HexColor('#80deea'),
        'TITLE': 'ORTHOPEDIC CLINICAL ASSESSMENT'
    }
}

SEVERITY_COLORS = {
    'low': colors.HexColor('#00ff88'),
    'medium': colors.HexColor('#ffaa00'),
    'high': colors.HexColor('#ff6600'),
    'critical': colors.HexColor('#ff0000')
}

def classify_consultation_category(diagnosis, symptoms):
    """Classify the consultation into a specific clinical domain."""
    diag_str = str(diagnosis).lower()
    sym_str = str(symptoms).lower()
    
    ortho_keywords = ['fracture', 'arthritis', 'joint', 'ortho', 'back pain', 'knee', 'spine', 'bone', 'muscle', 'cervical', 'spondylitis', 'ligament', 'sprain', 'tendon', 'shoulder', 'disc', 'cramp']
    cardiac_keywords = ['cardiac', 'heart', 'hypertension', 'bp', 'pulse', 'coronary', 'angina', 'cardio', 'arrhythmia', 'palpitations', 'chest pain', 'valvular', 'cholesterol', 'tachycardia']
    
    for kw in ortho_keywords:
        if kw in diag_str or kw in sym_str:
            return 'ortho'
            
    for kw in cardiac_keywords:
        if kw in diag_str or kw in sym_str:
            return 'cardiac'
            
    return 'general'

def generate_report_pdf(patient, consultation, output_path: str) -> str:
    """Generate a professional, category-specific medical report PDF."""
    
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
    
    # Parse data lists
    try:
        syms = json.loads(consultation.symptoms) if consultation.symptoms else []
    except:
        syms = [consultation.symptoms] if consultation.symptoms else []
        
    try:
        diags = json.loads(consultation.diagnosis) if consultation.diagnosis else []
    except:
        diags = [consultation.diagnosis] if consultation.diagnosis else []
        
    try:
        vitals = json.loads(consultation.vitals) if consultation.vitals else {}
    except:
        vitals = {}
        
    try:
        meds = json.loads(consultation.medications) if consultation.medications else []
    except:
        meds = [consultation.medications] if consultation.medications else []
        
    # Classify clinical category and load theme
    category = classify_consultation_category(diags, syms)
    theme = THEMES[category]
    
    # Custom styles based on theme
    title_style = ParagraphStyle(
        'DocTitle', fontSize=12, textColor=theme['TITLE_COLOR'],
        fontName='Helvetica-Bold', alignment=TA_RIGHT
    )
    
    section_style = ParagraphStyle(
        'DocSection', fontSize=11, textColor=theme['ACCENT'],
        spaceBefore=14, spaceAfter=6, fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'DocBody', fontSize=10, textColor=colors.HexColor('#222222'),
        spaceAfter=4, fontName='Helvetica', leading=14
    )
    
    bold_body_style = ParagraphStyle(
        'DocBoldBody', fontSize=10, textColor=colors.HexColor('#111111'),
        spaceAfter=4, fontName='Helvetica-Bold', leading=14
    )
    
    # ─── HEADER BLOCK ───
    header_data = [[
        Paragraph('MedAI', ParagraphStyle('LogoStyle', fontSize=30, textColor=theme['SECONDARY'], fontName='Helvetica-Bold')),
        Paragraph(theme['TITLE'], title_style),
    ]]
    header_table = Table(header_data, colWidths=[6.5*cm, 11*cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), theme['PRIMARY']),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 16),
        ('BOTTOMPADDING', (0,0), (-1,-1), 16),
        ('LEFTPADDING', (0,0), (0,-1), 14),
        ('RIGHTPADDING', (-1,0), (-1,-1), 14),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))
    
    # Sub header line
    story.append(HRFlowable(width="100%", thickness=2, color=theme['SECONDARY']))
    story.append(Spacer(1, 12))
    
    # ─── PATIENT INFORMATION ───
    story.append(Paragraph('PATIENT CLINICAL FILE', section_style))
    
    severity = consultation.severity or 'medium'
    sev_color = SEVERITY_COLORS.get(severity, colors.HexColor('#ffaa00'))
    
    patient_data = [
        ['Patient Name', patient.name, 'Date', consultation.date.strftime('%d %B %Y') if consultation.date else 'N/A'],
        ['Age / Gender', f"{patient.age or 'N/A'} yrs / {patient.gender or 'N/A'}", 'Phone', patient.phone or 'N/A'],
        ['Blood Group', patient.blood_group or 'N/A', 'Severity Level', severity.upper()],
        ['Consulting Doctor', consultation.doctor_name or 'Dr. Attending', 'Case ID', f'MED-{consultation.id:05d}'],
    ]
    
    pt_table = Table(patient_data, colWidths=[4*cm, 5.5*cm, 3.5*cm, 4.5*cm])
    pt_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f5f5f5')),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#f5f5f5')),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dddddd')),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, colors.HexColor('#fcfcfc')]),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('TEXTCOLOR', (3,2), (3,2), sev_color),
        ('FONTNAME', (3,2), (3,2), 'Helvetica-Bold'),
    ]))
    story.append(pt_table)
    story.append(Spacer(1, 12))
    
    # ─── CHIEF COMPLAINT ───
    if consultation.chief_complaint:
        story.append(Paragraph('CHIEF COMPLAINT / PRESENTATION', section_style))
        complaint_box = Table([[Paragraph(consultation.chief_complaint, body_style)]], colWidths=[17.5*cm])
        complaint_box.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fff9c4') if category == 'cardiac' else colors.HexColor('#efebe9') if category == 'ortho' else colors.HexColor('#f9f9f9')),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('BOX', (0,0), (-1,-1), 1.5, theme['ACCENT']),
            ('ROUNDEDCORNERS', [4]),
        ]))
        story.append(complaint_box)
        story.append(Spacer(1, 10))
        
    # ─── CLINICAL SYMPTOMS & DIAGNOSIS ───
    if syms or diags:
        row = []
        
        if syms:
            sym_items = [Paragraph('SYMPTOMS IDENTIFIED', section_style)]
            for s in syms:
                sym_items.append(Paragraph(f'• {s}', body_style))
            row.append(sym_items)
        
        if diags:
            diag_items = [Paragraph('DIAGNOSES AND OBSERVATIONS', section_style)]
            for d in diags:
                diag_items.append(Paragraph(f'◆ {d}', ParagraphStyle('DiagText', fontSize=10, 
                    textColor=theme['PRIMARY'], fontName='Helvetica-Bold', spaceAfter=4)))
            row.append(diag_items)
            
        if len(row) == 2:
            sd_table = Table([row], colWidths=[8.5*cm, 9*cm])
            sd_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ]))
            story.append(sd_table)
        elif row:
            for item in row[0]:
                story.append(item)
                
        story.append(Spacer(1, 12))
        
    # ─── VITALS & PHYSIOLOGICAL METRICS ───
    if vitals:
        story.append(Paragraph('PHYSIOLOGICAL VITALS', section_style))
        vital_labels = {
            'bp': 'Blood Pressure', 'pulse': 'Heart Rate (Pulse)', 'temp': 'Temperature',
            'spo2': 'SpO2 Saturation', 'weight': 'Weight', 'height': 'Height',
            'respiratory_rate': 'Respiratory Rate'
        }
        
        vital_rows = []
        vital_items = [(vital_labels.get(k, k.title()), v) for k, v in vitals.items() if v]
        
        # Build 4-column structured grid (Label, Value, Label, Value)
        for i in range(0, len(vital_items), 2):
            row_data = []
            for label, value in vital_items[i:i+2]:
                row_data.extend([label, value])
            while len(row_data) < 4:
                row_data.extend(['', ''])
            vital_rows.append(row_data)
            
        if vital_rows:
            v_table = Table(vital_rows, colWidths=[4.5*cm, 4*cm, 4.5*cm, 4.5*cm])
            
            # Formulate detailed alert styling
            grid_styles = [
                ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
                ('FONTSIZE', (0,0), (-1,-1), 9.5),
                ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
                ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#555555')),
                ('TEXTCOLOR', (2,0), (2,-1), colors.HexColor('#555555')),
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f7f9fa')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e0e0e0')),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
            ]
            
            # Apply clinical highlights for cardiac warning signs
            if category == 'cardiac':
                bp_val = vitals.get('bp', '')
                if bp_val and '/' in bp_val:
                    try:
                        sys_bp, dia_bp = map(int, bp_val.replace(' ', '').split('/'))
                        if sys_bp >= 140 or dia_bp >= 90:
                            # Highlight the BP cells with red color
                            grid_styles.append(('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#c62828')))
                            grid_styles.append(('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'))
                            grid_styles.append(('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#ffebee')))
                    except: pass
                    
            v_table.setStyle(TableStyle(grid_styles))
            story.append(v_table)
            story.append(Spacer(1, 12))
            
    # ─── CATEGORY SPECIFIC REPORTS ───
    if category == 'cardiac':
        story.append(Paragraph('CARDIOVASCULAR OBSERVATION METRICS', section_style))
        bp = vitals.get('bp', 'N/A')
        hr = vitals.get('pulse', 'N/A')
        spo2 = vitals.get('spo2', 'N/A')
        
        bp_assessment = "Physiological Normal Range"
        bp_color = colors.HexColor('#2e7d32')
        if bp != 'N/A' and '/' in bp:
            try:
                sys_val, dia_val = map(int, bp.replace(' ', '').split('/'))
                if sys_val >= 140 or dia_val >= 90:
                    bp_assessment = "Stage 1/2 Hypertension Threshold Exceeded"
                    bp_color = colors.HexColor('#c62828')
                elif sys_val >= 120 or dia_val >= 80:
                    bp_assessment = "Pre-hypertension / Elevated Threshold"
                    bp_color = colors.HexColor('#ef6c00')
            except: pass
            
        hr_assessment = "Normal Sinus Rhythm"
        hr_color = colors.HexColor('#2e7d32')
        if hr != 'N/A':
            try:
                hr_val = int(str(hr).lower().replace('bpm','').strip())
                if hr_val > 100:
                    hr_assessment = "Elevated Heart Rate / Tachycardia Status"
                    hr_color = colors.HexColor('#c62828')
                elif hr_val < 60:
                    hr_assessment = "Bradycardia Status"
                    hr_color = colors.HexColor('#ef6c00')
            except: pass
            
        cardiac_data = [
            ['Cardiovascular Marker', 'Observed Value', 'Clinical Category Assessment'],
            ['Systolic/Diastolic Blood Pressure', bp, Paragraph(f"<font color='{bp_color.hexval()}'><b>{bp_assessment}</b></font>", body_style)],
            ['Heart Rate (Pulse Frequency)', f"{hr} bpm" if hr != 'N/A' else 'N/A', Paragraph(f"<font color='{hr_color.hexval()}'><b>{hr_assessment}</b></font>", body_style)],
            ['Peripheral Oxygen Saturation (SpO2)', f"{spo2}%" if spo2 != 'N/A' else 'N/A', "Hypoxia Alert: Monitor Close" if (spo2 != 'N/A' and int(str(spo2).replace('%','')) < 95) else "Satisfactory Oxygenation Status"]
        ]
        
        cardiac_table = Table(cardiac_data, colWidths=[6.5*cm, 3.5*cm, 7.5*cm])
        cardiac_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#ffebee')),
            ('TEXTCOLOR', (0,0), (-1,0), theme['PRIMARY']),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d32f2f')),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(cardiac_table)
        story.append(Spacer(1, 12))
        
    elif category == 'ortho':
        story.append(Paragraph('ORTHOPEDIC MOBILITY AND PAIN PROFILE', section_style))
        
        # Assess orthopedic parameters based on symptoms
        joint_stiff = "Negative / Not Observed"
        restricted_mob = "Mild Restriction"
        pain_level = "Moderate"
        
        sym_str = " ".join(syms).lower()
        if 'stiff' in sym_str or 'swelling' in sym_str:
            joint_stiff = "Active Swelling / Joint Stiffness Reported"
        if 'severe' in sym_str or 'fracture' in sym_str or 'intense' in sym_str:
            pain_level = "Severe Pain Status"
        if 'restricted' in sym_str or 'cannot walk' in sym_str or 'limp' in sym_str:
            restricted_mob = "Significant Mobility Restriction / Offloading Advised"
            
        ortho_data = [
            ['Mobility Parameters', 'Observation Status', 'Clinical Protocols'],
            ['Joint Congestion / Stiffness', joint_stiff, 'Check Range of Motion (ROM) & apply cold compression.'],
            ['Reported Pain Intensity', pain_level, 'Analgesic protocol as prescribed; avoid heavy loading.'],
            ['Functional Range of Mobility', restricted_mob, 'Referral to Physiotherapist / Brace immobilization as needed.']
        ]
        
        ortho_table = Table(ortho_data, colWidths=[5.5*cm, 5.5*cm, 6.5*cm])
        ortho_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e0f7fa')),
            ('TEXTCOLOR', (0,0), (-1,0), theme['PRIMARY']),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#00838f')),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(ortho_table)
        story.append(Spacer(1, 12))
        
    # ─── PRESCRIBED MEDICATIONS ───
    if meds:
        story.append(Paragraph('PHARMACOTHERAPY / RX PRESCRIBED', section_style))
        med_data = [['#', 'Medication Name', 'Frequency & Clinical Instructions']]
        for i, med in enumerate(meds, 1):
            parts = med.split(' ', 2) if ' ' in med else [med, '', '']
            name = parts[0] if parts else med
            dosage = parts[1] if len(parts) > 1 else ''
            freq = parts[2] if len(parts) > 2 else 'As directed'
            med_data.append([str(i), f'{name} {dosage}'.strip(), freq])
            
        med_table = Table(med_data, colWidths=[1*cm, 7.5*cm, 9*cm])
        med_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), theme['PRIMARY']),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9.5),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, theme['BG_LIGHT']]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ]))
        story.append(med_table)
        story.append(Spacer(1, 12))
        
    # ─── TREATMENT PROTOCOL ───
    if consultation.treatment_plan:
        story.append(Paragraph('MANAGEMENT AND TREATMENT PLAN', section_style))
        story.append(Paragraph(consultation.treatment_plan, body_style))
        story.append(Spacer(1, 10))
        
    # ─── CLINICAL AI SUMMARY ───
    if consultation.ai_analysis:
        story.append(Paragraph('CLINICAL ASSESSMENT (CLINICAL AI ANALYSIS)', section_style))
        
        # Parse the summary analysis into clean readable lines
        ai_lines = consultation.ai_analysis.replace('CLINICAL SUMMARY (Rule-Based NLP Analysis)\n================================================', '').strip()
        
        ai_box = Table([[Paragraph(ai_lines.replace('\n', '<br/>'), ParagraphStyle('AIStyle', fontSize=9, textColor=colors.HexColor('#111111'), fontName='Helvetica', leading=13))]], colWidths=[17.5*cm])
        ai_box.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), theme['CARD_BG']),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('BOX', (0,0), (-1,-1), 1.5, theme['CARD_BORDER']),
            ('ROUNDEDCORNERS', [4]),
        ]))
        story.append(ai_box)
        story.append(Spacer(1, 10))
        
    # ─── FOLLOW UP & ADVICE ───
    if consultation.follow_up:
        story.append(Paragraph('FOLLOW-UP PROTOCOL', section_style))
        story.append(Paragraph(consultation.follow_up, body_style))
        story.append(Spacer(1, 14))
        
    # ─── SIGNATURE BLOCK ───
    story.append(Spacer(1, 10))
    sig_data = [
        ['', ''],
        ['─────────────────────────────', '─────────────────────────────'],
        ['Consulting Medical Practitioner Signature', 'MedAI Automated Audit Sign-Off']
    ]
    sig_table = Table(sig_data, colWidths=[8.5*cm, 9*cm])
    sig_table.setStyle(TableStyle([
        ('FONTNAME', (0,2), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('TEXTCOLOR', (0,1), (-1,-1), colors.HexColor('#666666')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(sig_table)
    
    # ─── FOOTER ───
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#dddddd')))
    
    footer_data = [[
        Paragraph('Generated by MedAI Clinical Intelligence Platform — Official Audit Report', 
                   ParagraphStyle('FooterL', fontSize=7.5, textColor=colors.HexColor('#888888'), fontName='Helvetica')),
        Paragraph(f'Date: {datetime.now().strftime("%d %b %Y, %I:%M %p")}',
                   ParagraphStyle('FooterR', fontSize=7.5, textColor=colors.HexColor('#888888'), fontName='Helvetica', alignment=TA_RIGHT))
    ]]
    footer_table = Table(footer_data, colWidths=[11.5*cm, 6*cm])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(footer_table)
    
    doc.build(story)
    return output_path

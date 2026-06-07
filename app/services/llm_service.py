import os
import re

def analyze_transcript(transcript, patient_history=None, attachments_analysis=None):
    text = transcript.strip()
    text_lower = text.lower()
    symptoms = _extract_symptoms(text_lower)
    diagnosis = _extract_diagnosis(text_lower)
    medications = _extract_medications(text)
    vitals = _extract_vitals(text_lower)
    severity = _determine_severity(text_lower, diagnosis, symptoms)
    return {
        "chief_complaint": _extract_chief_complaint(text, text_lower),
        "symptoms": symptoms,
        "diagnosis": diagnosis,
        "medications": medications,
        "vitals": vitals,
        "lab_results": _extract_labs(text_lower),
        "treatment_plan": _extract_treatment(text, text_lower),
        "follow_up": _extract_followup(text_lower),
        "notes": "",
        "severity": severity,
        "ai_analysis": _generate_analysis(symptoms, diagnosis, medications, vitals, severity, patient_history, attachments_analysis),
    }

SYMPTOM_KEYWORDS = [
    "pain","ache","fever","cough","cold","headache","dizziness","nausea","vomiting",
    "fatigue","weakness","breathlessness","shortness of breath","chest pain","back pain",
    "stomach pain","abdominal pain","throat pain","ear pain","leg pain","joint pain",
    "muscle pain","swelling","rash","itching","bleeding","diarrhea","constipation",
    "loss of appetite","weight loss","insomnia","anxiety","palpitations","sweating",
    "chills","burning","numbness","tingling","blurred vision","runny nose","wheezing",
]

DIAGNOSIS_KEYWORDS = {
    "Hypertension": ["hypertension","high blood pressure","htn","high bp"],
    "Diabetes": ["diabetes","diabetic","sugar","type 2","type 1"],
    "Fever": ["fever","pyrexia","febrile"],
    "Viral Infection": ["viral","virus","flu","influenza"],
    "Pneumonia": ["pneumonia","lung infection"],
    "Bronchitis": ["bronchitis","bronchial"],
    "Asthma": ["asthma","asthmatic"],
    "GERD": ["gerd","acid reflux","reflux","heartburn"],
    "Gastritis": ["gastritis","gastric","peptic"],
    "Urinary Tract Infection": ["uti","urinary tract","cystitis"],
    "Anemia": ["anemia","anaemia","low hemoglobin"],
    "Thyroid Disorder": ["thyroid","hypothyroid","hyperthyroid"],
    "Arthritis": ["arthritis","rheumatoid","osteoarthritis"],
    "Migraine": ["migraine","cluster headache"],
    "Malaria": ["malaria"],
    "Dengue": ["dengue"],
    "Typhoid": ["typhoid","enteric fever"],
    "COVID-19": ["covid","covid-19","coronavirus"],
}

VITALS_PATTERNS = {
    "bp": [r'(?:bp|blood pressure)\s*[:\-]?\s*(\d{2,3}\s*/\s*\d{2,3})'],
    "pulse": [r'(?:pulse|heart rate|hr)\s*[:\-]?\s*(\d{2,3})\s*(?:bpm)?'],
    "temp": [r'(?:temp(?:erature)?)\s*[:\-]?\s*(\d{2,3}(?:\.\d)?)'],
    "spo2": [r'(?:spo2|oxygen saturation|o2 sat)\s*[:\-]?\s*(\d{2,3})\s*%?'],
    "weight": [r'(?:weight|wt)\s*[:\-]?\s*(\d{2,3}(?:\.\d+)?)\s*(?:kg|lbs?)'],
    "height": [r'(?:height|ht)\s*[:\-]?\s*(\d{2,3}(?:\.\d+)?)\s*(?:cm|ft)?'],
}

SEVERITY_RULES = {
    "critical": ["emergency","critical","heart attack","stroke","unconscious","cardiac arrest"],
    "high": ["severe","serious","hospital admission","difficulty breathing","pneumonia","sepsis","acute"],
    "medium": ["moderate","chronic","hypertension","diabetes","infection","bronchitis","asthma"],
    "low": ["mild","routine","checkup","follow up","cold","minor","general"],
}

def _extract_chief_complaint(text, text_lower):
    patterns = [
        r'(?:presenting with|complains? of|presents? with|c/o)\s+([^.]{10,120})',
        r'(?:chief complaint|main complaint)\s*[:\-]?\s*([^.]{10,120})',
    ]
    for pat in patterns:
        m = re.search(pat, text_lower)
        if m:
            return m.group(1).strip().rstrip('.,')[:200]
    first = text.split('.')[0].strip()
    return first[:200] if len(first) > 10 else "General consultation"

def _extract_symptoms(text_lower):
    found = []
    for sym in SYMPTOM_KEYWORDS:
        if re.search(r'\b' + re.escape(sym) + r'\b', text_lower):
            if not any(sym in e.lower() for e in found):
                found.append(sym.title())
    return list(dict.fromkeys(found))[:10]

def _extract_diagnosis(text_lower):
    found = []
    for diag_name, keywords in DIAGNOSIS_KEYWORDS.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                if diag_name not in found:
                    found.append(diag_name)
                break
    return list(dict.fromkeys(found))[:8]

def _extract_medications(text):
    found = []
    for m in re.finditer(r'\b([A-Z][a-zA-Z]{3,})\s+(\d+(?:\.\d+)?\s*(?:mg|mcg|ml|g|iu))\s*([\w\s]{3,30}?)(?=\.|,|\n|$)', text):
        entry = f"{m.group(1)} {m.group(2)} {m.group(3).strip()}".strip()
        if entry not in found:
            found.append(entry)
    return list(dict.fromkeys(found))[:10]

def _extract_vitals(text_lower):
    vitals = {}
    for vital_name, patterns in VITALS_PATTERNS.items():
        for pat in patterns:
            m = re.search(pat, text_lower)
            if m:
                vitals[vital_name] = m.group(1).strip()
                break
    return vitals

def _extract_labs(text_lower):
    labs = {}
    for pat, name in [
        (r'(?:hb|hemoglobin)\s*[:\-]?\s*([\d.]+)', 'hemoglobin'),
        (r'(?:blood sugar|fbs|rbs|glucose)\s*[:\-]?\s*([\d.]+)', 'blood_sugar'),
        (r'(?:hba1c)\s*[:\-]?\s*([\d.]+)', 'hba1c'),
    ]:
        m = re.search(pat, text_lower)
        if m:
            labs[name] = m.group(1)
    return labs

def _extract_treatment(text, text_lower):
    for pat in [r'(?:treatment|plan|management|advice)[:\-]?\s*([^.]{20,300})',
                r'(?:advised|recommended)\s+([^.]{20,200})']:
        m = re.search(pat, text_lower)
        if m:
            return m.group(1).strip().capitalize()
    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
    return '. '.join(sentences[-2:]) if sentences else "As per consultation."

def _extract_followup(text_lower):
    for pat in [r'(?:follow[\s\-]?up|review|come back)\s+(?:in|after)?\s*([\w\s]+?)(?:\.|,|$)',
                r'(?:after|in)\s+(\d+\s*(?:days?|weeks?|months?))']:
        m = re.search(pat, text_lower)
        if m:
            return f"Follow up {m.group(1).strip()}"
    return "Follow up as advised" if 'follow' in text_lower else ""

def _determine_severity(text_lower, diagnosis, symptoms):
    for level in ["critical", "high", "medium", "low"]:
        for kw in SEVERITY_RULES[level]:
            if kw in text_lower:
                return level
    for d in [x.lower() for x in diagnosis]:
        if any(s in d for s in ['pneumonia','sepsis','cardiac','cancer']): return "high"
        if any(s in d for s in ['hypertension','diabetes','asthma','uti','anemia']): return "medium"
    return "low" if len(symptoms) <= 2 else "medium"

def _generate_analysis(symptoms, diagnosis, medications, vitals, severity, patient_history, attachments_analysis):
    lines = ["CLINICAL SUMMARY (MedAI NLP Engine)", "=" * 40]
    if diagnosis:
        lines.append(f"\nASSESSMENT: {', '.join(diagnosis)}")
    if symptoms:
        lines.append(f"\nSYMPTOMS: {', '.join(symptoms)}")
    if vitals:
        bp = vitals.get('bp', '').replace(' ', '')
        if bp and '/' in bp:
            try:
                s, d = map(int, bp.split('/'))
                status = "ELEVATED" if s >= 140 or d >= 90 else "Normal"
                lines.append(f"\nBP {bp} mmHg — {status}")
            except: pass
    if medications:
        lines.append(f"\nMEDICATIONS: {len(medications)} prescribed")
    if patient_history:
        lines.append(f"\nHISTORY: {len(patient_history)} previous consultation(s) on record")
    sev_notes = {
        "critical": "CRITICAL — Immediate intervention required.",
        "high": "HIGH — Close monitoring needed.",
        "medium": "MODERATE — Regular monitoring important.",
        "low": "LOW — Routine management.",
    }
    lines.append(f"\nSEVERITY: {sev_notes.get(severity, '')}")
    lines.append("\n" + "─" * 40)
    lines.append("MedAI Rule-Based NLP — No API required.")
    return "\n".join(lines)

def analyze_image(image_data, media_type):
    return {
        "image_type": "Medical Image",
        "findings": ["Image attached to consultation"],
        "abnormalities": [],
        "clinical_significance": "Manual review required.",
        "recommendations": ["Review image manually"]
    }

def generate_summary_narrative(patient_data, stats):
    name = patient_data.get('name', 'Patient')
    visits = stats.get('total_visits', 0)
    return f"{name} has {visits} recorded consultation(s) on MedAI."

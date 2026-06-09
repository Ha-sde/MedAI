import os
import json
import re

# No API required - Smart Rule-Based Medical NLP

SYMPTOM_KEYWORDS = [
    "pain","ache","fever","cough","cold","headache","dizziness","nausea","vomiting",
    "fatigue","weakness","breathlessness","shortness of breath","chest pain","back pain",
    "stomach pain","abdominal pain","throat pain","ear pain","leg pain","joint pain",
    "muscle pain","swelling","rash","itching","bleeding","diarrhea","constipation",
    "loss of appetite","weight loss","weight gain","insomnia","anxiety","depression",
    "palpitations","sweating","chills","burning","numbness","tingling","blurred vision",
    "runny nose","sneezing","wheezing","sore throat","frequent urination",
]

DIAGNOSIS_KEYWORDS = {
    "Hypertension": ["hypertension","high blood pressure","htn","high bp"],
    "Diabetes": ["diabetes","diabetic","sugar","hyperglycemia","type 2","type 1"],
    "Fever": ["fever","pyrexia","febrile"],
    "Viral Infection": ["viral","virus","viral fever","flu","influenza"],
    "Pneumonia": ["pneumonia","lung infection"],
    "Bronchitis": ["bronchitis","bronchial"],
    "Asthma": ["asthma","asthmatic","bronchospasm"],
    "GERD": ["gerd","acid reflux","reflux","heartburn"],
    "Gastritis": ["gastritis","gastric","stomach inflammation","peptic"],
    "Urinary Tract Infection": ["uti","urinary tract","urinary infection","cystitis"],
    "Anemia": ["anemia","anaemia","low hemoglobin","low hb"],
    "Thyroid Disorder": ["thyroid","hypothyroid","hyperthyroid","tsh"],
    "Arthritis": ["arthritis","joint inflammation","rheumatoid","osteoarthritis"],
    "Migraine": ["migraine","severe headache","cluster headache"],
    "Anxiety Disorder": ["anxiety","panic attack","anxious"],
    "Depression": ["depression","depressed","mood disorder"],
    "Malaria": ["malaria","plasmodium"],
    "Dengue": ["dengue","dengue fever"],
    "Typhoid": ["typhoid","enteric fever"],
    "COVID-19": ["covid","covid-19","coronavirus"],
}

VITALS_PATTERNS = {
    "bp": [r'(?:bp|blood pressure)\s*[:\-]?\s*(\d{2,3}\s*/\s*\d{2,3})'],
    "pulse": [r'(?:pulse|heart rate|hr)\s*[:\-]?\s*(\d{2,3})\s*(?:bpm)?'],
    "temp": [r'(?:temp(?:erature)?)\s*[:\-]?\s*(\d{2,3}(?:\.\d)?)\s*(?:°?[fc])?'],
    "spo2": [r'(?:spo2|oxygen saturation|o2 sat)\s*[:\-]?\s*(\d{2,3})\s*%?'],
    "weight": [r'(?:weight|wt)\s*[:\-]?\s*(\d{2,3}(?:\.\d+)?)\s*(?:kg|lbs?)'],
    "height": [r'(?:height|ht)\s*[:\-]?\s*(\d{2,3}(?:\.\d+)?)\s*(?:cm|ft)?'],
    "respiratory_rate": [r'(?:rr|respiratory rate)\s*[:\-]?\s*(\d{1,2})'],
}

SEVERITY_RULES = {
    "critical": ["emergency","critical","severe chest pain","heart attack","stroke",
                 "unconscious","respiratory failure","icu","cardiac arrest"],
    "high": ["severe","serious","hospital admission","high fever","difficulty breathing",
             "pneumonia","sepsis","acute"],
    "medium": ["moderate","chronic","hypertension","diabetes","infection","bronchitis",
               "gastritis","uti","anemia","thyroid","arthritis","asthma"],
    "low": ["mild","routine","checkup","follow up","cold","minor","general"],
}


def analyze_transcript(transcript: str, patient_history: list = None, attachments_analysis: list = None) -> dict:
    text = transcript.strip()
    text_lower = text.lower()

    chief_complaint = _extract_chief_complaint(text, text_lower)
    symptoms = _extract_symptoms(text_lower)
    diagnosis = _extract_diagnosis(text_lower)
    medications = _extract_medications(text)
    vitals = _extract_vitals(text_lower)
    lab_results = _extract_labs(text_lower)
    treatment_plan = _extract_treatment(text, text_lower)
    follow_up = _extract_followup(text_lower)
    severity = _determine_severity(text_lower, diagnosis, symptoms)
    ai_analysis = _generate_analysis(
        chief_complaint, symptoms, diagnosis, medications,
        vitals, severity, patient_history, attachments_analysis
    )

    return {
        "chief_complaint": chief_complaint,
        "symptoms": symptoms,
        "diagnosis": diagnosis,
        "medications": medications,
        "vitals": vitals,
        "lab_results": lab_results,
        "treatment_plan": treatment_plan,
        "follow_up": follow_up,
        "notes": "",
        "severity": severity,
        "ai_analysis": ai_analysis,
    }


def _extract_chief_complaint(text, text_lower):
    patterns = [
        r'(?:presenting with|complains? of|comes? with|presents? with|c/o)\s+([^.]{10,120})',
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
    for m in re.finditer(r'(?:diagnosed with|diagnosis[:\s]+|impression[:\s]+)\s*([\w\s,]+?)(?:\.|,|\n|$)', text_lower):
        candidate = m.group(1).strip().title()
        if candidate and candidate not in found and len(candidate) > 3:
            found.append(candidate)
    return list(dict.fromkeys(found))[:8]


def _extract_medications(text):
    found = []
    pat = re.finditer(
        r'\b([A-Z][a-zA-Z]{3,})\s+(\d+(?:\.\d+)?\s*(?:mg|mcg|ml|g|iu))\s*([\w\s]{3,30}?)(?=\.|,|\n|$)',
        text
    )
    for m in pat:
        entry = f"{m.group(1)} {m.group(2)} {m.group(3).strip()}".strip()
        if entry not in found:
            found.append(entry)
    pat2 = re.finditer(
        r'(?:prescribe|give|start|tab|tablet|capsule)\s+([A-Z][a-zA-Z]{3,}(?:\s+\d+\s*(?:mg|mcg|ml|g))?)',
        text
    )
    for m in pat2:
        entry = m.group(1).strip()
        if entry not in found and len(entry) > 3:
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
    lab_patterns = [
        (r'(?:hb|hemoglobin)\s*[:\-]?\s*([\d.]+)\s*(?:g/?dl)?', 'hemoglobin'),
        (r'(?:blood sugar|fbs|rbs|glucose)\s*[:\-]?\s*([\d.]+)', 'blood_sugar'),
        (r'(?:hba1c)\s*[:\-]?\s*([\d.]+)\s*%?', 'hba1c'),
        (r'(?:cholesterol)\s*[:\-]?\s*([\d.]+)', 'cholesterol'),
        (r'(?:tsh|thyroid)\s*[:\-]?\s*([\d.]+)', 'tsh'),
    ]
    for pat, name in lab_patterns:
        m = re.search(pat, text_lower)
        if m:
            labs[name] = m.group(1)
    return labs


def _extract_treatment(text, text_lower):
    for pat in [r'(?:treatment plan|plan|management|advice)[:\-]?\s*([^.]{20,300})',
                r'(?:advised|recommended)\s+([^.]{20,200})']:
        m = re.search(pat, text_lower)
        if m:
            return m.group(1).strip().capitalize()
    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
    return '. '.join(sentences[-2:]) if sentences else "As per consultation."


def _extract_followup(text_lower):
    patterns = [
        r'(?:follow[\s\-]?up|review|come back)\s+(?:in|after)?\s*([\w\s]+?)(?:\.|,|$)',
        r'(?:after|in)\s+(\d+\s*(?:days?|weeks?|months?))',
    ]
    for pat in patterns:
        m = re.search(pat, text_lower)
        if m:
            return f"Follow up {m.group(1).strip()}"
    return "Follow up as advised" if 'follow' in text_lower else ""


def _determine_severity(text_lower, diagnosis, symptoms):
    for level in ["critical", "high", "medium", "low"]:
        for kw in SEVERITY_RULES[level]:
            if kw in text_lower:
                return level
    serious = ['pneumonia', 'sepsis', 'cardiac', 'cancer']
    moderate = ['hypertension', 'diabetes', 'asthma', 'uti', 'anemia', 'thyroid']
    for d in [x.lower() for x in diagnosis]:
        if any(s in d for s in serious): return "high"
        if any(s in d for s in moderate): return "medium"
    return "low" if len(symptoms) <= 2 else "medium"


def _generate_analysis(chief_complaint, symptoms, diagnosis, medications,
                        vitals, severity, patient_history, attachments_analysis):
    lines = ["CLINICAL SUMMARY (Rule-Based NLP Analysis)", "=" * 48]

    if chief_complaint:
        lines.append(f"\nPRESENTING COMPLAINT:\n{chief_complaint}")
    if diagnosis:
        lines.append(f"\nASSESSMENT:\nPatient presents with {', '.join(diagnosis)}.")
    if symptoms:
        lines.append(f"\nSYMPTOMS IDENTIFIED:\n{', '.join(symptoms)}")

    if vitals:
        vlines = []
        bp = vitals.get('bp', '').replace(' ', '')
        if bp and '/' in bp:
            try:
                s, d = map(int, bp.split('/'))
                if s >= 140 or d >= 90:
                    vlines.append(f"BP {bp} mmHg — ELEVATED, monitor for hypertension")
                else:
                    vlines.append(f"BP {bp} mmHg — within normal range")
            except: pass
        spo2 = vitals.get('spo2', '')
        if spo2:
            try:
                val = int(str(spo2).replace('%', ''))
                if val < 95:
                    vlines.append(f"SpO2 {val}% — BELOW NORMAL, consider oxygen support")
                else:
                    vlines.append(f"SpO2 {val}% — satisfactory")
            except: pass
        if vlines:
            lines.append("\nVITALS INTERPRETATION:\n" + "\n".join(f"  • {v}" for v in vlines))

    if medications:
        lines.append(f"\nMEDICATIONS:\n{len(medications)} medication(s) prescribed. Counsel patient on dosage and compliance.")

    if patient_history:
        lines.append(f"\nHISTORY:\nPatient has {len(patient_history)} previous consultation(s) on record.")

    if attachments_analysis:
        lines.append(f"\nATTACHMENTS:\n{len(attachments_analysis)} file(s) uploaded and attached to this record.")

    sev_notes = {
        "critical": "CRITICAL — Immediate intervention required.",
        "high": "HIGH SEVERITY — Close monitoring and possible specialist referral needed.",
        "medium": "MODERATE — Regular monitoring and medication compliance important.",
        "low": "LOW SEVERITY — Routine management. Lifestyle advice recommended.",
    }
    lines.append(f"\nSEVERITY: {sev_notes.get(severity, '')}")
    lines.append("\n" + "─" * 48)
    lines.append("Analysis by MedAI rule-based NLP engine. Add Anthropic API key for deep AI reasoning.")

    return "\n".join(lines)


def analyze_image(image_data: bytes, media_type: str) -> dict:
    return {
        "image_type": "Medical Image",
        "findings": ["Image received and attached to consultation"],
        "abnormalities": [],
        "clinical_significance": "Manual review required. Add Anthropic API key for AI image analysis.",
        "recommendations": ["Review image manually"]
    }


def generate_summary_narrative(patient_data: dict, stats: dict) -> str:
    name = patient_data.get('name', 'Patient')
    age = patient_data.get('age', 'Unknown')
    gender = patient_data.get('gender', '')
    visits = stats.get('total_visits', 0)
    score = stats.get('health_score', 0)
    top_diag = stats.get('most_common_diagnoses', [])
    narrative = f"{name} is a {age}-year-old {gender} patient with {visits} recorded consultation(s). "
    if top_diag:
        conditions = ', '.join([d[0] for d in top_diag[:3]])
        narrative += f"Primary conditions: {conditions}. "
    narrative += "Good" if score >= 70 else "Needs monitoring" if score >= 40 else "Requires attention"
    return narrative
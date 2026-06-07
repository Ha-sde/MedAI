import os
import json
import re
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY', ''))

EXTRACTION_SYSTEM = """You are a medical AI assistant specialized in clinical note analysis. 
You extract structured information from doctor's spoken consultation notes.
Always respond with valid JSON only. No markdown, no explanation, just raw JSON.

Extract and return this exact structure:
{
  "chief_complaint": "primary reason for visit",
  "symptoms": ["symptom1", "symptom2"],
  "diagnosis": ["diagnosis1", "diagnosis2"],
  "medications": ["Med 100mg twice daily", "Med2 50mg once daily"],
  "vitals": {
    "bp": "120/80",
    "pulse": "72",
    "temp": "98.6",
    "spo2": "99",
    "weight": "70kg",
    "height": "170cm",
    "respiratory_rate": "16"
  },
  "lab_results": {
    "test_name": "value with unit"
  },
  "treatment_plan": "detailed treatment plan",
  "follow_up": "follow up instructions and timeline",
  "notes": "any additional clinical notes",
  "severity": "low|medium|high|critical",
  "ai_analysis": "clinical reasoning, differential diagnosis considerations, red flags if any, evidence-based recommendations"
}

If a field is not mentioned, use empty string or empty array. For severity:
- low: routine checkup, minor issues
- medium: manageable chronic conditions, moderate symptoms  
- high: serious conditions requiring close monitoring
- critical: emergency or life-threatening conditions"""

IMAGE_ANALYSIS_SYSTEM = """You are a medical imaging AI assistant. Analyze the provided medical image (X-ray, MRI, CT scan, lab report, etc.) and provide:
1. Image type identification
2. Key findings
3. Abnormalities if any
4. Clinical significance
5. Recommendations

Respond in JSON format:
{
  "image_type": "X-ray chest / MRI brain / etc",
  "findings": ["finding1", "finding2"],
  "abnormalities": ["abnormality1"],
  "clinical_significance": "explanation",
  "recommendations": ["recommendation1"]
}"""

def analyze_transcript(transcript: str, patient_history: list = None, attachments_analysis: list = None) -> dict:
    """Analyze doctor's transcript using Claude with full reasoning."""
    
    history_context = ""
    if patient_history:
        recent = patient_history[-5:]  # Last 5 consultations
        history_context = f"\n\nPATIENT HISTORY CONTEXT (last {len(recent)} visits):\n"
        for h in recent:
            history_context += f"- {h.get('date', 'Unknown date')}: Diagnosis: {h.get('diagnosis', [])}, Medications: {h.get('medications', [])}\n"
    
    attachment_context = ""
    if attachments_analysis:
        attachment_context = "\n\nIMAGING/REPORT ANALYSIS:\n"
        for a in attachments_analysis:
            attachment_context += f"- {json.dumps(a)}\n"
    
    user_message = f"""Analyze this doctor's consultation note and extract structured medical information.

DOCTOR'S TRANSCRIPT:
{transcript}
{history_context}
{attachment_context}

Extract all medical information and provide comprehensive clinical analysis."""

    try:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4000,
            thinking={
                "type": "enabled",
                "budget_tokens": 2000
            },
            system=EXTRACTION_SYSTEM,
            messages=[{"role": "user", "content": user_message}]
        )
        
        # Extract text from response
        result_text = ""
        for block in response.content:
            if block.type == "text":
                result_text = block.text
                break
        
        # Parse JSON
        result_text = result_text.strip()
        if result_text.startswith('```'):
            result_text = re.sub(r'```json?\n?', '', result_text)
            result_text = result_text.rstrip('`').strip()
        
        return json.loads(result_text)
    
    except Exception as e:
        print(f"[LLM Error] {e}")
        # Fallback basic extraction
        return _basic_extraction(transcript)

def analyze_image(image_data: bytes, media_type: str) -> dict:
    """Analyze medical image using Claude vision."""
    import base64
    
    try:
        img_b64 = base64.standard_b64encode(image_data).decode('utf-8')
        
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1500,
            system=IMAGE_ANALYSIS_SYSTEM,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": img_b64
                        }
                    },
                    {"type": "text", "text": "Analyze this medical image and provide structured findings."}
                ]
            }]
        )
        
        result_text = response.content[0].text.strip()
        if result_text.startswith('```'):
            result_text = re.sub(r'```json?\n?', '', result_text)
            result_text = result_text.rstrip('`').strip()
        
        return json.loads(result_text)
    
    except Exception as e:
        print(f"[Image Analysis Error] {e}")
        return {"image_type": "Unknown", "findings": [], "abnormalities": [], "clinical_significance": "Analysis unavailable", "recommendations": []}

def generate_summary_narrative(patient_data: dict, stats: dict) -> str:
    """Generate a narrative health summary for the patient."""
    
    prompt = f"""Based on this patient's medical history, write a comprehensive clinical summary in 3-4 paragraphs.

Patient: {patient_data.get('name')}, {patient_data.get('age')} year old {patient_data.get('gender')}
Total Visits: {stats.get('total_visits')}
Most Common Diagnoses: {stats.get('most_common_diagnoses')}
Most Common Symptoms: {stats.get('most_common_symptoms')}
Current Medications: {stats.get('most_prescribed_medications')}
Severity Distribution: {stats.get('severity_distribution')}
Health Score: {stats.get('health_score')}/100

Write a professional clinical summary covering: overall health trajectory, key conditions, treatment patterns, and health recommendations."""

    try:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except:
        return "Summary generation requires API connection."

def _basic_extraction(transcript: str) -> dict:
    """Fallback basic extraction without LLM."""
    return {
        "chief_complaint": "See transcript",
        "symptoms": [],
        "diagnosis": [],
        "medications": [],
        "vitals": {},
        "lab_results": {},
        "treatment_plan": transcript,
        "follow_up": "",
        "notes": "",
        "severity": "medium",
        "ai_analysis": "Manual review required - LLM analysis unavailable."
    }

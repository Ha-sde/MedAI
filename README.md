# MedAI — Clinical Intelligence Platform

A full-stack medical consultation system powered by Claude AI. Doctors speak or type consultation notes, upload X-rays/reports, and MedAI automatically structures all data, stores it in patient history, and generates professional PDF medical reports.

---

## Features

- **OTP-based login** — mobile number + 6-digit OTP (no passwords)
- **Patient registration** — full profile (name, age, gender, blood group, allergies, etc.)
- **Voice recording** — real-time speech-to-text, every word appears as you speak (Chrome/Edge)
- **File uploads** — X-rays, MRI, CT, lab reports analyzed by AI vision
- **LLM analysis** — Claude with extended thinking extracts: diagnosis, symptoms, medications, vitals, treatment plan
- **Patient history** — all consultations stored, viewable, expandable
- **Summary dashboard** — health score, charts, visit trends, condition frequency
- **PDF report generation** — professional clinical reports with ReportLab
- **Dark theme UI** — clean, minimal, black & white design

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Flask + SQLAlchemy + Flask-JWT-Extended |
| AI/NLP | Anthropic Claude (claude-opus-4-5) with extended thinking |
| Image Analysis | Claude Vision |
| PDF | ReportLab |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Real-time | Flask-SocketIO + EventLet |
| Frontend | Vanilla JS + CSS (SPA, no frameworks) |
| Deployment | Docker + Docker Compose |

---

## Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- An Anthropic API key ([get one here](https://console.anthropic.com))

### 1. Set up virtual environment

```bash
cd medai
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your Anthropic API key:
# ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

### 4. Run the application

```bash
python run.py
```

Open your browser at: **http://localhost:5000**

---

## Usage Flow

### New Patient
1. Go to http://localhost:5000
2. Click "Register here" on the login page
3. Fill in your details and create account
4. Return to login, enter phone number → get OTP → verify

### Doctor Recording a Consultation
1. Login with patient's phone + OTP
2. You land on the **Console** screen
3. **Speak**: Click the 🎙 mic button → speak the consultation naturally
   - Every word appears on screen in real-time
   - Example: *"Patient is a 45-year-old male presenting with chest pain and shortness of breath for 2 days. Blood pressure 150/90. Diagnosed with hypertension stage 2. Prescribing amlodipine 5mg once daily. Follow up in 2 weeks."*
4. **Or type**: Type directly in the input box
5. **Upload files**: Click 📎 to attach X-rays, reports, or images
6. Click **Send** → MedAI analyzes everything
7. Results appear with: diagnosis, symptoms, medications, vitals, AI analysis
8. Download the **PDF report** instantly

### History & Summary
- Click **History** in the side panel → see all past consultations
- Click **Summary** → see health analytics, charts, condition frequency, health score

---

## Docker Deployment

### Build and run with Docker Compose

```bash
# Set your API key
export ANTHROPIC_API_KEY=sk-ant-your-key-here

# Build and start
docker-compose up --build

# Run in background
docker-compose up -d --build
```

App runs at: **http://localhost:5000**

### Stop

```bash
docker-compose down
```

---

## Project Structure

```
medai/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # SQLAlchemy models (Patient, Consultation, OTP)
│   ├── routes/
│   │   ├── auth.py          # OTP login, registration
│   │   ├── patient.py       # Profile, history, summary
│   │   ├── consultation.py  # AI analysis, file upload
│   │   └── report.py        # PDF download
│   ├── services/
│   │   ├── llm_service.py   # Claude AI integration
│   │   └── pdf_service.py   # ReportLab PDF generation
│   └── static/
│       ├── index.html       # Single-page app shell
│       ├── css/main.css     # Dark theme design
│       └── js/app.js        # Frontend logic
├── run.py                   # Entry point
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/send-otp` | Send OTP to phone |
| POST | `/api/auth/verify-otp` | Verify OTP, get JWT token |
| POST | `/api/auth/register` | Register new patient |
| GET | `/api/patient/me` | Get current patient profile |
| GET | `/api/patient/history` | Get all consultations |
| GET | `/api/patient/summary` | Get analytics summary |
| POST | `/api/consultation/analyze` | Submit consultation + files for AI analysis |
| GET | `/api/report/{id}/download` | Download PDF report |

---

## Notes

- **OTP in demo mode**: The OTP is returned in the API response for easy testing. In production, integrate Twilio or AWS SNS for real SMS delivery.
- **Speech recognition**: Uses the Web Speech API (built into Chrome/Edge). Works best in these browsers.
- **API key**: Keep your Anthropic API key secure. Never commit `.env` to git.
- **Database**: SQLite is used by default. For production, set `DATABASE_URL` to a PostgreSQL connection string.

---

## Production Checklist

- [ ] Change `SECRET_KEY` and `JWT_SECRET_KEY` to random secrets
- [ ] Set up PostgreSQL and update `DATABASE_URL`
- [ ] Remove OTP from API response, integrate SMS service (Twilio)
- [ ] Add HTTPS (nginx reverse proxy or Let's Encrypt)
- [ ] Set `FLASK_ENV=production`
- [ ] Set up persistent Docker volumes for uploads
- [ ] Configure backup for the database

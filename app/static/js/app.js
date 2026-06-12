/* ── MedAI Frontend Application ─────────────────────── */

const API = '';  // Same origin
let token = localStorage.getItem('medai_token');
let currentPatient = null;
let selectedFiles = [];
let isRecording = false;
let recognition = null;
let fullTranscript = '';
let currentDraftConsultation = null;

/* ── Startup ─────────────────────────────────────────── */
window.addEventListener('DOMContentLoaded', () => {
  // Splash then route
  setTimeout(() => {
    document.getElementById('splash').classList.add('done');
    setTimeout(() => {
      document.getElementById('splash').style.display = 'none';
      if (token) {
        loadPatientAndShow();
      } else {
        showPage('login');
      }
    }, 500);
  }, 2000);

  // OTP box auto-advance
  setupOTPBoxes();

  // Speech recognition
  setupSpeechRecognition();
});

/* ── Page routing ────────────────────────────────────── */
function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
  const page = document.getElementById(`page-${name}`);
  if (page) page.classList.remove('hidden');
}

function showLoginStep(step) {
  document.querySelectorAll('.login-step').forEach(s => s.classList.add('hidden'));
  document.getElementById(`login-step-${step}`).classList.remove('hidden');
}

function navTo(view) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`view-${view}`).classList.add('active');
  document.getElementById(`nav-${view}`).classList.add('active');
  if (view === 'history') loadHistory();
  if (view === 'summary') loadSummary();
}

/* ── Patient load ─────────────────────────────────────── */
async function loadPatientAndShow() {
  try {
    const res = await apiFetch('/api/patient/me');
    currentPatient = res;
    updatePatientUI(res);
    showPage('app');
    navTo('home');
  } catch {
    token = null;
    localStorage.removeItem('medai_token');
    showPage('login');
  }
}

function updatePatientUI(patient) {
  document.getElementById('patient-name').textContent = patient.name;
  const initials = patient.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
  document.getElementById('patient-initials').textContent = initials;
  const meta = [patient.age ? `${patient.age} yrs` : '', patient.gender || ''].filter(Boolean).join(' · ');
  document.getElementById('patient-meta').textContent = meta || patient.phone;
}

/* ── Auth ─────────────────────────────────────────────── */
async function sendOTP() {
  const phone = document.getElementById('login-phone').value.trim();
  if (!phone) { setStatus('login-status', 'Enter your phone number', 'error'); return; }
  
  setStatus('login-status', 'Sending OTP...', '');
  try {
    const res = await apiFetch('/api/auth/send-otp', 'POST', { phone });
    if (res.otp) {
      document.getElementById('otp-hint').textContent = `Demo OTP: ${res.otp}`;
    } else {
      document.getElementById('otp-hint').textContent = `Verification code sent to your phone.`;
    }
    setStatus('login-status', 'OTP sent!', 'success');
    showLoginStep('otp');
  } catch (e) {
    if (e.not_found) {
      setStatus('login-status', 'Number not found. Please register.', 'error');
    } else {
      setStatus('login-status', e.error || 'Failed to send OTP', 'error');
    }
  }
}

async function verifyOTP() {
  const phone = document.getElementById('login-phone').value.trim();
  const boxes = document.querySelectorAll('.otp-box');
  const otp = Array.from(boxes).map(b => b.value).join('');
  if (otp.length < 6) { setStatus('login-status', 'Enter 6-digit OTP', 'error'); return; }
  
  setStatus('login-status', 'Verifying...', '');
  try {
    const res = await apiFetch('/api/auth/verify-otp', 'POST', { phone, otp });
    token = res.token;
    localStorage.setItem('medai_token', token);
    currentPatient = res.patient;
    updatePatientUI(res.patient);
    showPage('app');
    navTo('home');
  } catch (e) {
    setStatus('login-status', e.error || 'Invalid OTP', 'error');
  }
}

async function registerPatient() {
  const data = {
    name: document.getElementById('reg-name').value.trim(),
    phone: document.getElementById('reg-phone').value.trim(),
    gender: document.getElementById('reg-gender').value,
    age: parseInt(document.getElementById('reg-age').value) || null,
    email: document.getElementById('reg-email').value.trim(),
    blood_group: document.getElementById('reg-blood').value,
    address: document.getElementById('reg-address').value.trim(),
    allergies: document.getElementById('reg-allergies').value.trim(),
  };
  
  if (!data.name || !data.phone) {
    setStatus('reg-status', 'Name and phone are required', 'error');
    return;
  }
  
  setStatus('reg-status', 'Creating account...', '');
  try {
    await apiFetch('/api/auth/register', 'POST', data);
    setStatus('reg-status', '✓ Account created! Please login.', 'success');
    setTimeout(() => {
      document.getElementById('login-phone').value = data.phone;
      showPage('login');
    }, 1500);
  } catch (e) {
    setStatus('reg-status', e.error || 'Registration failed', 'error');
  }
}

function logout() {
  token = null;
  localStorage.removeItem('medai_token');
  currentPatient = null;
  document.getElementById('messages-area').innerHTML = '';
  showPage('login');
  showLoginStep('phone');
}

/* ── OTP boxes ───────────────────────────────────────── */
function setupOTPBoxes() {
  const boxes = document.querySelectorAll('.otp-box');
  boxes.forEach((box, i) => {
    box.addEventListener('input', () => {
      if (box.value && i < boxes.length - 1) boxes[i + 1].focus();
    });
    box.addEventListener('keydown', (e) => {
      if (e.key === 'Backspace' && !box.value && i > 0) boxes[i - 1].focus();
    });
    box.addEventListener('paste', (e) => {
      const paste = (e.clipboardData || window.clipboardData).getData('text');
      if (paste.length === 6) {
        paste.split('').forEach((ch, j) => { if (boxes[j]) boxes[j].value = ch; });
        boxes[5].focus();
      }
    });
  });
}

/* ── File handling ───────────────────────────────────── */
function handleFiles(input) {
  const newFiles = Array.from(input.files);
  selectedFiles = [...selectedFiles, ...newFiles];
  renderAttachments();
  input.value = '';
}

function removeFile(index) {
  selectedFiles.splice(index, 1);
  renderAttachments();
}

function renderAttachments() {
  const bar = document.getElementById('attachments-bar');
  const list = document.getElementById('att-list');
  if (!selectedFiles.length) { bar.classList.add('hidden'); return; }
  
  bar.classList.remove('hidden');
  list.innerHTML = selectedFiles.map((f, i) => `
    <div class="att-item">
      <span>${fileIcon(f.name)}</span>
      <span>${f.name.length > 20 ? f.name.slice(0, 17) + '...' : f.name}</span>
      <span class="att-remove" onclick="removeFile(${i})">×</span>
    </div>
  `).join('');
}

function fileIcon(name) {
  const ext = name.split('.').pop().toLowerCase();
  if (['jpg','jpeg','png','gif','webp','bmp'].includes(ext)) return '🖼';
  if (ext === 'pdf') return '📄';
  return '📎';
}

/* ── Speech Recognition ──────────────────────────────── */
function setupSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) { console.warn('Speech recognition not supported'); return; }
  
  recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'en-IN';
  
  recognition.onresult = (e) => {
    let interim = '';
    let finalText = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const txt = e.results[i][0].transcript;
      if (e.results[i].isFinal) finalText += txt + ' ';
      else interim += txt;
    }
    if (finalText) fullTranscript += finalText;
    
    const display = document.getElementById('transcript-text');
    const input = document.getElementById('main-input');
    display.textContent = (fullTranscript + interim) || 'Listening...';
    input.value = fullTranscript + interim;
    autoResize(input);
    display.scrollTop = display.scrollHeight;
  };
  
  recognition.onerror = (e) => {
    console.error('Speech error:', e.error);
    if (isRecording) stopRecording();
  };
  
  recognition.onend = () => {
    if (isRecording) { recognition.start(); } // keep recording
  };
}

function toggleRecording() {
  if (!recognition) {
    alert('Speech recognition is not supported in this browser. Please use Chrome.');
    return;
  }
  if (isRecording) stopRecording();
  else startRecording();
}

function startRecording() {
  isRecording = true;
  fullTranscript = document.getElementById('main-input').value;
  
  document.getElementById('mic-btn').classList.add('recording');
  document.getElementById('transcript-display').classList.remove('hidden');
  document.getElementById('console-welcome').classList.add('hidden');
  document.getElementById('transcript-text').textContent = 'Listening...';
  
  try { recognition.start(); } catch(e) {}
}

function stopRecording() {
  isRecording = false;
  document.getElementById('mic-btn').classList.remove('recording');
  document.getElementById('transcript-display').classList.add('hidden');
  try { recognition.stop(); } catch(e) {}
  
  // Move transcript to input
  const final = fullTranscript.trim();
  if (final) document.getElementById('main-input').value = final;
  
  // Restore welcome console if the input is empty
  const currentVal = document.getElementById('main-input').value.trim();
  if (!currentVal) {
    document.getElementById('console-welcome').classList.remove('hidden');
  }
}

/* ── Submit Consultation ─────────────────────────────── */
async function submitConsultation() {
  if (isRecording) stopRecording();
  
  const transcript = document.getElementById('main-input').value.trim();
  if (!transcript) return;
  
  // Hide welcome, show processing
  document.getElementById('console-welcome').classList.add('hidden');
  document.getElementById('transcript-display').classList.add('hidden');
  document.getElementById('processing').classList.remove('hidden');
  document.getElementById('main-input').value = '';
  document.getElementById('main-input').style.height = 'auto';
  fullTranscript = '';
  
  const formData = new FormData();
  formData.append('transcript', transcript);
  formData.append('doctor_name', 'Dr. Attending');
  selectedFiles.forEach(f => formData.append('files', f));
  
  try {
    const res = await fetch(`${API}/api/consultation/analyze`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });
    
    document.getElementById('processing').classList.add('hidden');
    
    if (!res.ok) throw await res.json();
    const data = await res.json();
    
    currentDraftConsultation = data;
    renderResult(data, transcript);
    selectedFiles = [];
    renderAttachments();
    
  } catch (e) {
    document.getElementById('processing').classList.add('hidden');
    addMessage(`<div class="result-card"><p style="color:var(--red)">Error: ${e.error || 'Analysis failed. Check your API key.'}</p></div>`);
  }
}

function renderResult(data, transcript) {
  const diagList = (data.diagnosis || []).join(', ') || 'See notes';
  const symList = (data.symptoms || []).map(s => `<li>${s}</li>`).join('') || '<li>—</li>';
  const medList = (data.medications || []).map(m => `<li>${m}</li>`).join('') || '<li>None prescribed</li>';
  const severity = data.severity || 'medium';
  
  const vitals = data.vitals || {};
  const vitalsHtml = Object.entries(vitals).filter(([,v]) => v).map(([k,v]) => 
    `<span class="tag">${k.toUpperCase()}: ${v}</span>`
  ).join('') || '<span class="tag">Not recorded</span>';
  
  const html = `
    <div class="result-card">
      <div class="result-header">
        <div>
          <div class="result-title">Consultation Analysis</div>
          <div style="font-size:12px;color:var(--text3);margin-top:4px">${new Date().toLocaleString()}</div>
        </div>
        <span class="sev-badge sev-${severity}">${severity}</span>
      </div>
      
      ${data.chief_complaint ? `
      <div style="background:var(--bg2);border-left:3px solid var(--orange);padding:12px 16px;border-radius:6px;margin-bottom:16px">
        <div style="font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">Chief Complaint</div>
        <div style="font-size:14px">${data.chief_complaint}</div>
      </div>` : ''}
      
      <div class="result-grid">
        <div class="result-section">
          <h4>Symptoms</h4>
          <ul>${symList}</ul>
        </div>
        <div class="result-section">
          <h4>Diagnosis</h4>
          <ul>${(data.diagnosis || []).map(d => `<li><strong>${d}</strong></li>`).join('') || '<li>—</li>'}</ul>
        </div>
        <div class="result-section result-full">
          <h4>Vital Signs</h4>
          <div class="history-tags">${vitalsHtml}</div>
        </div>
        <div class="result-section">
          <h4>Medications</h4>
          <ul>${medList}</ul>
        </div>
        <div class="result-section">
          <h4>Follow Up</h4>
          <p>${data.follow_up || '—'}</p>
        </div>
        <div class="result-section result-full">
          <h4>Treatment Plan</h4>
          <p>${data.treatment_plan || '—'}</p>
        </div>
        ${data.ai_analysis ? `
        <div class="result-section result-full">
          <h4>🧠 AI Clinical Analysis</h4>
          <div class="ai-analysis-box">${data.ai_analysis}</div>
        </div>` : ''}
      </div>
      
      <div class="card-actions-area" style="margin-top: 20px;">
        ${data.id ? `
          <button class="pdf-btn" onclick="downloadPDF(${data.id})">
            📄 Download PDF Report
          </button>
        ` : `
          <button class="pdf-btn" id="save-history-btn" onclick="saveCurrentDraft(this)">
            📋 Add to History
          </button>
        `}
      </div>
    </div>
  `;
  
  addMessage(html);
}

function addMessage(html) {
  const area = document.getElementById('messages-area');
  const div = document.createElement('div');
  div.innerHTML = html;
  area.appendChild(div);
  div.scrollIntoView({ behavior: 'smooth' });
}

async function downloadPDF(consultationId) {
  window.open(`${API}/api/report/${consultationId}/download?token=${token}`, '_blank');
  // Fallback with auth header
  try {
    const res = await fetch(`${API}/api/report/${consultationId}/download`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `MedAI_Report_${consultationId}.pdf`;
      a.click();
    }
  } catch(e) {}
}

/* ── History ─────────────────────────────────────────── */
async function loadHistory() {
  const list = document.getElementById('history-list');
  list.innerHTML = '<div class="empty-state">Loading...</div>';
  
  try {
    const data = await apiFetch('/api/patient/history');
    document.getElementById('history-count').textContent = `${data.length} records`;
    
    if (!data.length) {
      list.innerHTML = '<div class="empty-state">No consultations recorded yet.</div>';
      return;
    }
    
    list.innerHTML = data.map(c => {
      const diags = (c.diagnosis || []).slice(0, 3).join(', ') || 'General Checkup';
      const syms = (c.symptoms || []).slice(0, 3);
      const meds = (c.medications || []).slice(0, 2);
      const date = c.date ? new Date(c.date).toLocaleDateString('en-IN', {day:'2-digit',month:'short',year:'numeric'}) : '—';
      const sev = c.severity || 'medium';
      
      return `
        <div class="history-item" onclick="toggleHistory(this)">
          <div class="history-item-header">
            <div>
              <div class="history-diag">${diags}</div>
              <div class="history-tags">
                ${syms.map(s => `<span class="tag">${s}</span>`).join('')}
              </div>
            </div>
            <div style="text-align:right">
              <div class="history-date">${date}</div>
              <span class="sev-badge sev-${sev}" style="font-size:10px">${sev}</span>
            </div>
          </div>
          
          <div class="history-expand">
            <div class="expand-section">
              <h4>Chief Complaint</h4>
              <p>${c.chief_complaint || '—'}</p>
              <h4>All Diagnoses</h4>
              <p>${(c.diagnosis || []).join(', ') || '—'}</p>
              <h4>Medications</h4>
              <p>${(c.medications || []).join(' · ') || '—'}</p>
              <h4>Treatment Plan</h4>
              <p>${c.treatment_plan || '—'}</p>
              ${c.ai_analysis ? `<h4>AI Analysis</h4><div class="ai-analysis-box" style="font-size:12px">${c.ai_analysis.slice(0,300)}${c.ai_analysis.length>300?'...':''}</div>` : ''}
              ${c.id ? `<button class="dl-link" onclick="event.stopPropagation(); dlHistoryPDF(${c.id})">📄 Download Report</button>` : ''}
            </div>
          </div>
        </div>
      `;
    }).join('');
    
  } catch(e) {
    list.innerHTML = '<div class="empty-state">Failed to load history.</div>';
  }
}

function toggleHistory(el) {
  el.classList.toggle('expanded');
}

async function dlHistoryPDF(id) {
  try {
    const res = await fetch(`${API}/api/report/${id}/download`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `MedAI_Report_${id}.pdf`;
      a.click();
    }
  } catch(e) {}
}

/* ── Summary ─────────────────────────────────────────── */
async function loadSummary() {
  const content = document.getElementById('summary-content');
  content.innerHTML = '<div class="empty-state">Loading analytics...</div>';
  
  try {
    const data = await apiFetch('/api/patient/summary');
    const stats = data.stats || {};
    const patient = data.patient || currentPatient;
    
    if (!stats.total_visits) {
      content.innerHTML = '<div class="empty-state">No consultation data yet. Record your first consultation to see analytics.</div>';
      return;
    }
    
    const healthScore = stats.health_score || 0;
    const scoreColor = healthScore >= 70 ? 'var(--green)' : healthScore >= 40 ? 'var(--orange)' : 'var(--red)';
    
    // Top medications pills
    const medsList = stats.most_prescribed_medications || [];
    const medsHtml = medsList.map(([m, c]) => 
      `<span class="tag">${m.split(' ')[0]} <strong style="color:var(--accent)">(×${c})</strong></span>`
    ).join('');
    
    // Recent timeline
    const recent = data.recent_consultations || [];
    const timelineHtml = recent.reverse().map(c => `
      <div class="tl-item">
        <div class="tl-date">${c.date ? new Date(c.date).toLocaleDateString('en-IN', {day:'2-digit',month:'short',year:'numeric'}) : '—'}</div>
        <div class="tl-diag">${(c.diagnosis || []).slice(0,2).join(', ') || 'General'}</div>
        <div class="tl-pills">
          ${(c.medications || []).slice(0,3).map(m => `<span class="tl-pill">${m.split(' ')[0]}</span>`).join('')}
        </div>
      </div>
    `).join('') || '<p style="color:var(--text3);font-size:13px">No recent visits</p>';
    
    content.innerHTML = `
      <!-- Stat cards -->
      <div class="summary-grid">
        <div class="stat-card">
          <div class="stat-number" style="color:var(--accent)">${stats.total_visits}</div>
          <div class="stat-label">Total Visits</div>
        </div>
        <div class="stat-card">
          <div class="stat-number" style="color:${scoreColor}">${healthScore}</div>
          <div class="stat-label">Health Score</div>
        </div>
        <div class="stat-card">
          <div class="stat-number" style="color:var(--orange)">${stats.total_diagnoses || 0}</div>
          <div class="stat-label">Unique Conditions</div>
        </div>
        <div class="stat-card">
          <div class="stat-number" style="color:var(--green)">${stats.total_medications || 0}</div>
          <div class="stat-label">Medications Prescribed</div>
        </div>
      </div>

      <!-- Patient Profile Info -->
      <div class="summary-section">
        <h3>Patient Profile</h3>
        <div class="chart-wrap" style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
          <div><span style="color:var(--text3);font-size:11px">NAME</span><p style="font-size:15px;font-weight:600;margin-top:4px">${patient.name || '—'}</p></div>
          <div><span style="color:var(--text3);font-size:11px">AGE / GENDER</span><p style="font-size:15px;font-weight:600;margin-top:4px">${patient.age || '—'} yrs · ${patient.gender || '—'}</p></div>
          <div><span style="color:var(--text3);font-size:11px">BLOOD GROUP</span><p style="font-size:15px;font-weight:600;margin-top:4px">${patient.blood_group || '—'}</p></div>
          <div><span style="color:var(--text3);font-size:11px">ALLERGIES</span><p style="font-size:15px;font-weight:600;margin-top:4px">${patient.allergies || 'None'}</p></div>
          <div><span style="color:var(--text3);font-size:11px">FIRST VISIT</span><p style="font-size:14px;margin-top:4px">${stats.first_visit ? new Date(stats.first_visit).toLocaleDateString('en-IN') : '—'}</p></div>
          <div><span style="color:var(--text3);font-size:11px">LAST VISIT</span><p style="font-size:14px;margin-top:4px">${stats.last_visit ? new Date(stats.last_visit).toLocaleDateString('en-IN') : '—'}</p></div>
        </div>
      </div>

      <!-- Clinical AI Synthesis -->
      <div class="summary-section">
        <h3>Clinical Synthesis Assessment</h3>
        <div class="ai-analysis-box" style="font-size: 13.5px; border-left: 4px solid var(--accent); line-height: 1.7; white-space: pre-line;">
          ${stats.clinical_synthesis || 'Clinical assessment history not compiled yet.'}
        </div>
      </div>

      <!-- Health Score Trend & Vitals Line Chart -->
      <div class="summary-section">
        <h3>Health Index & Vitals Trends</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px;">
          <div class="chart-wrap">
            <div class="chart-title" style="margin-bottom: 12px; font-weight:600;">Health Index Evolution</div>
            <div style="position: relative; height: 200px; width: 100%;">
              <canvas id="healthScoreChart"></canvas>
            </div>
          </div>
          <div class="chart-wrap">
            <div class="chart-title" style="margin-bottom: 12px; font-weight:600;">Vitals History Tracking</div>
            <div style="position: relative; height: 200px; width: 100%;">
              <canvas id="vitalsChart"></canvas>
            </div>
          </div>
        </div>
      </div>

      <!-- Diagnosis Distribution & Severity Chart -->
      <div class="summary-section">
        <h3>Clinical Metrics & Distributions</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px;">
          <div class="chart-wrap">
            <div class="chart-title" style="margin-bottom: 12px; font-weight:600;">Diagnosis Distribution</div>
            <div style="position: relative; height: 200px; width: 100%;">
              <canvas id="diagnosisChart"></canvas>
            </div>
          </div>
          <div class="chart-wrap">
            <div class="chart-title" style="margin-bottom: 12px; font-weight:600;">Consultation Severity Breakdown</div>
            <div style="position: relative; height: 200px; width: 100%;">
              <canvas id="severityChart"></canvas>
            </div>
          </div>
        </div>
      </div>

      <!-- Medications & Timeline -->
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px;">
        <!-- Top medications -->
        ${medsHtml ? `
        <div class="summary-section">
          <h3>Most Prescribed Medications</h3>
          <div class="chart-wrap" style="min-height: 140px;">
            <div class="history-tags">${medsHtml}</div>
          </div>
        </div>` : ''}

        <!-- Recent timeline -->
        <div class="summary-section">
          <h3>Consultation Timeline</h3>
          <div class="chart-wrap">
            <div class="timeline">${timelineHtml}</div>
          </div>
        </div>
      </div>
    `;
    
    // Draw Charts using Chart.js
    
    // 1. Health Score Evolution Line Chart
    const hsData = stats.health_score_history || [];
    const hsLabels = hsData.map(h => h.date);
    const hsScores = hsData.map(h => h.score);
    
    new Chart(document.getElementById('healthScoreChart'), {
      type: 'line',
      data: {
        labels: hsLabels,
        datasets: [{
          label: 'Health Score',
          data: hsScores,
          borderColor: '#00d4ff',
          backgroundColor: 'rgba(0, 212, 255, 0.1)',
          fill: true,
          tension: 0.3,
          borderWidth: 2,
          pointRadius: 4,
          pointBackgroundColor: '#00d4ff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { min: 0, max: 100, grid: { color: '#2a2a42' }, ticks: { color: '#9090aa' } },
          x: { grid: { color: 'transparent' }, ticks: { color: '#9090aa' } }
        }
      }
    });

    // 2. Vitals History Tracking Multi-line Chart
    const vHistory = stats.vitals_history || [];
    const vLabels = vHistory.map(v => v.date);
    const pulseData = vHistory.map(v => parseInt(v.pulse) || null);
    const sysData = [];
    const diaData = [];
    vHistory.forEach(v => {
      if (v.bp && v.bp.includes('/')) {
        const parts = v.bp.split('/');
        sysData.push(parseInt(parts[0]) || null);
        diaData.push(parseInt(parts[1]) || null);
      } else {
        sysData.push(null);
        diaData.push(null);
      }
    });

    new Chart(document.getElementById('vitalsChart'), {
      type: 'line',
      data: {
        labels: vLabels,
        datasets: [
          {
            label: 'Systolic BP (mmHg)',
            data: sysData,
            borderColor: '#ff4466',
            borderWidth: 2,
            pointRadius: 3,
            fill: false,
            tension: 0.1
          },
          {
            label: 'Diastolic BP (mmHg)',
            data: diaData,
            borderColor: '#ffaa00',
            borderWidth: 2,
            pointRadius: 3,
            fill: false,
            tension: 0.1
          },
          {
            label: 'Heart Rate (Pulse)',
            data: pulseData,
            borderColor: '#00ff88',
            borderWidth: 2,
            pointRadius: 3,
            fill: false,
            tension: 0.1
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            labels: { color: '#9090aa', boxWidth: 8, font: { size: 9 } },
            position: 'top'
          }
        },
        scales: {
          y: { grid: { color: '#2a2a42' }, ticks: { color: '#9090aa' } },
          x: { grid: { color: 'transparent' }, ticks: { color: '#9090aa' } }
        }
      }
    });

    // 3. Diagnosis Distribution Doughnut Chart
    const diagDist = stats.most_common_diagnoses || [];
    const diagLabels = diagDist.map(d => d[0]);
    const diagCounts = diagDist.map(d => d[1]);

    new Chart(document.getElementById('diagnosisChart'), {
      type: 'doughnut',
      data: {
        labels: diagLabels.length ? diagLabels : ['No active conditions'],
        datasets: [{
          data: diagCounts.length ? diagCounts : [1],
          backgroundColor: ['#00d4ff', '#ff6600', '#00ff88', '#ffaa00', '#9090aa'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: { color: '#9090aa', font: { size: 9 }, boxWidth: 10 }
          }
        }
      }
    });

    // 4. Severity Distribution Bar Chart
    const sevData = stats.severity_distribution || {};
    const sevLabels = ['Low', 'Medium', 'High', 'Critical'];
    const sevCounts = [
      sevData.low || 0,
      sevData.medium || 0,
      sevData.high || 0,
      sevData.critical || 0
    ];

    new Chart(document.getElementById('severityChart'), {
      type: 'bar',
      data: {
        labels: sevLabels,
        datasets: [{
          data: sevCounts,
          backgroundColor: ['#00ff88', '#ffaa00', '#ff6600', '#ff4466'],
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { grid: { color: '#2a2a42' }, ticks: { color: '#9090aa', stepSize: 1 } },
          x: { grid: { color: 'transparent' }, ticks: { color: '#9090aa' } }
        }
      }
    });
    
  } catch(e) {
    console.error('Error drawing summary charts:', e);
    content.innerHTML = '<div class="empty-state">Failed to load summary.</div>';
  }
}

/* ── Utilities ───────────────────────────────────────── */
async function apiFetch(url, method = 'GET', body = null) {
  const opts = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    }
  };
  if (body) opts.body = JSON.stringify(body);
  
  const res = await fetch(API + url, opts);
  const data = await res.json();
  if (!res.ok) throw data;
  return data;
}

function setStatus(id, msg, type) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.className = `login-status ${type === 'error' ? 'status-error' : type === 'success' ? 'status-success' : ''}`;
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

async function saveCurrentDraft(btn) {
  if (!currentDraftConsultation) return;
  
  btn.disabled = true;
  btn.textContent = 'Saving to History...';
  
  try {
    const res = await apiFetch('/api/consultation/save', 'POST', currentDraftConsultation);
    
    // Replace the button area with download button and success msg
    const actionsArea = btn.parentElement;
    actionsArea.innerHTML = `
      <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
        <button class="pdf-btn" onclick="downloadPDF(${res.id})">
          📄 Download PDF Report
        </button>
        <span style="color: var(--green); font-size: 13px; font-weight: 600;">✓ Saved to History</span>
      </div>
    `;
    
    // Clear draft
    currentDraftConsultation = null;
    
    // Refresh history and summary lists
    loadHistory();
    loadSummary();
  } catch (e) {
    btn.disabled = false;
    btn.textContent = '📋 Add to History';
    alert(e.error || 'Failed to save to history');
  }
}

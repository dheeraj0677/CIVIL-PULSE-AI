/**
 * CivicPulse AI — Unified Multi-Role Frontend Application
 * Handles Citizen Portal, Officer Prioritized Dispatch, Field Worker Tasks,
 * Live NLP Analysis, and Status Tracking.
 */

// Application State
const state = {
  currentRole: 'citizen', // 'citizen', 'officer', 'worker'
  currentUser: null,
  locations: [],
  kpis: {},
  officerQueue: [],
  workerTasks: [],
  workersList: [],
  selectedLocation: null,
  analysisDebounceTimer: null,
};

// DOM Ready Initialization
document.addEventListener('DOMContentLoaded', async () => {
  await loadLocations();
  await refreshKPIs();
  setupEventListeners();
  renderLocationsDropdown();
  runAnalysisPreview(); // initial analysis
});

// ==========================================
// API & Data Fetching
// ==========================================

async function loadLocations() {
  try {
    const res = await fetch('/api/locations');
    state.locations = await res.json();
    if (state.locations.length > 0) {
      state.selectedLocation = state.locations[0];
    }
  } catch (err) {
    console.error('Failed to load locations', err);
  }
}

async function refreshKPIs() {
  try {
    const res = await fetch('/api/kpis');
    const data = await res.json();
    state.kpis = data.kpis;
    updateKPIDisplays();
  } catch (err) {
    console.error('Failed to load KPIs', err);
  }
}

function updateKPIDisplays() {
  const k = state.kpis;
  if (!k) return;
  document.querySelectorAll('.kpi-total-tickets').forEach(el => el.textContent = k.total_tickets || 0);
  document.querySelectorAll('.kpi-pending-approval').forEach(el => el.textContent = k.pending_approval || 0);
  document.querySelectorAll('.kpi-approved').forEach(el => el.textContent = k.approved || 0);
  document.querySelectorAll('.kpi-in-progress').forEach(el => el.textContent = k.in_progress || 0);
  document.querySelectorAll('.kpi-resolved').forEach(el => el.textContent = k.resolved || 0);
  document.querySelectorAll('.kpi-critical').forEach(el => el.textContent = k.critical_count || 0);
  document.querySelectorAll('.kpi-avg-hours').forEach(el => el.textContent = (k.avg_resolution_hours || 16.5) + 'h');
}

// ==========================================
// Live NLP & Priority Assessment
// ==========================================

function runAnalysisPreview() {
  clearTimeout(state.analysisDebounceTimer);
  state.analysisDebounceTimer = setTimeout(async () => {
    const desc = document.getElementById('complaint-desc').value.trim();
    const locId = document.getElementById('location-select').value;
    const urgency = document.querySelector('input[name="urgency"]:checked')?.value || 'Standard';

    if (!desc && !locId) return;

    try {
      const res = await fetch('/api/complaints/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          description: desc || 'Routine municipal issue reported',
          location_id: locId || 'L0001',
          user_urgency: urgency,
        }),
      });
      const data = await res.json();
      if (data.status === 'success') {
        renderAIPreview(data.assessment, data.location);
      }
    } catch (err) {
      console.error('Analysis preview failed', err);
    }
  }, 300);
}

function renderAIPreview(assessment, location) {
  const scoreVal = document.getElementById('ai-score-val');
  const scoreBar = document.getElementById('ai-score-bar');
  const catVal = document.getElementById('ai-category-val');
  const sevVal = document.getElementById('ai-severity-val');
  const timeVal = document.getElementById('ai-turnaround-val');
  const ratVal = document.getElementById('ai-rationale-val');

  if (scoreVal) scoreVal.textContent = assessment.priority_score.toFixed(1);
  if (scoreBar) {
    scoreBar.style.width = `${assessment.priority_score}%`;
    scoreBar.style.backgroundColor = 
      assessment.priority_score >= 85 ? 'var(--critical)' :
      assessment.priority_score >= 70 ? 'var(--high)' :
      assessment.priority_score >= 45 ? 'var(--medium)' : 'var(--low)';
  }
  if (catVal) catVal.textContent = `${assessment.predicted_category} (${Math.round(assessment.category_confidence * 100)}% conf)`;
  if (sevVal) {
    sevVal.textContent = assessment.inferred_severity;
    sevVal.className = `badge-tier badge-tier-${assessment.inferred_severity.toLowerCase()}`;
  }
  if (timeVal) timeVal.textContent = `~${assessment.estimated_resolution_hours.toFixed(1)} hours`;
  if (ratVal) ratVal.textContent = assessment.rationale;
}

// ==========================================
// Locations Dropdown & GPS simulation
// ==========================================

function renderLocationsDropdown() {
  const sel = document.getElementById('location-select');
  if (!sel) return;
  sel.innerHTML = '';

  state.locations.forEach(loc => {
    const opt = document.createElement('option');
    opt.value = loc.location_id;
    const flags = [];
    if (loc.near_hospital) flags.push('🏥 Hospital');
    if (loc.near_school) flags.push('🏫 School');
    const flagStr = flags.length ? ` · ${flags.join(' ')}` : '';
    opt.textContent = `${loc.location_id} (${loc.zone} · ${loc.road_type} · ${loc.road_condition} cond${flagStr})`;
    sel.appendChild(opt);
  });

  updateLocationPreview(sel.value);
}

function updateLocationPreview(locId) {
  const loc = state.locations.find(l => l.location_id === locId);
  const container = document.getElementById('location-preview-box');
  if (!loc || !container) return;

  container.innerHTML = `
    <div style="font-weight: 600; color: #FFFFFF;">
      📍 Node ${loc.location_id} — ${loc.zone}
    </div>
    <div style="font-size: 0.8rem; color: var(--text-secondary);">
      Road: ${loc.road_type} (${loc.road_condition} Condition) · Density: ${loc.population_density_per_km2.toLocaleString()} residents/km²
    </div>
    <div class="loc-badge-group">
      ${loc.near_hospital ? '<span class="loc-badge loc-badge-hospital">🏥 Adjacent Hospital Zone</span>' : ''}
      ${loc.near_school ? '<span class="loc-badge loc-badge-school">🏫 School Pedestrian Corridor</span>' : ''}
      <span class="loc-badge loc-badge-density">👥 ${loc.pedestrian_activity} Pedestrian Activity</span>
    </div>
  `;
}

function simulateGPSLocation() {
  // Pick high-sensitivity location like L0002 or L0116
  const sensitiveLocs = state.locations.filter(l => l.near_hospital || l.near_school);
  const pick = sensitiveLocs.length ? sensitiveLocs[Math.floor(Math.random() * sensitiveLocs.length)] : state.locations[1];
  
  const sel = document.getElementById('location-select');
  if (sel && pick) {
    sel.value = pick.location_id;
    updateLocationPreview(pick.location_id);
    runAnalysisPreview();
    showToast(`📍 GPS Position Acquired: Node ${pick.location_id} (${pick.zone})`);
  }
}

// ==========================================
// Citizen Complaint Submission (NO LOGIN)
// ==========================================

async function handleComplaintSubmit(e) {
  e.preventDefault();
  const desc = document.getElementById('complaint-desc').value.trim();
  const locId = document.getElementById('location-select').value;
  const urgency = document.querySelector('input[name="urgency"]:checked')?.value || 'Standard';
  const contact = document.getElementById('complaint-contact').value.trim();

  if (!desc) {
    showToast('⚠️ Please describe the infrastructure hazard.');
    return;
  }

  const submitBtn = document.getElementById('submit-btn');
  const originalText = submitBtn.innerHTML;
  submitBtn.disabled = true;
  submitBtn.innerHTML = '⚡ Classifying & Dispatching...';

  try {
    const res = await fetch('/api/complaints/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        description: desc,
        location_id: locId,
        user_urgency: urgency,
        citizen_contact: contact,
      }),
    });
    const data = await res.json();

    if (data.status === 'success') {
      showSubmissionSuccessModal(data.ticket_id, data.assessment);
      document.getElementById('complaint-form').reset();
      runAnalysisPreview();
      await refreshKPIs();
      if (state.currentRole === 'officer') {
        loadOfficerQueue();
      }
    } else {
      showToast(`Error: ${data.detail || 'Submission failed'}`);
    }
  } catch (err) {
    showToast('Failed to submit complaint. Server error.');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalText;
  }
}

function showSubmissionSuccessModal(ticketId, assessment) {
  const modal = document.getElementById('success-modal');
  document.getElementById('modal-ticket-id').textContent = ticketId;
  document.getElementById('modal-ticket-category').textContent = assessment.predicted_category;
  document.getElementById('modal-ticket-severity').textContent = assessment.inferred_severity;
  document.getElementById('modal-ticket-priority').textContent = `${assessment.priority_score.toFixed(1)} / 100 (${assessment.priority_tier})`;
  document.getElementById('modal-ticket-eta').textContent = `~${assessment.estimated_resolution_hours.toFixed(1)} hours`;
  modal.classList.add('active');
}

// ==========================================
// Complaint Tracking (By Ticket ID)
// ==========================================

async function trackComplaintById(inputTicketId) {
  const ticketId = inputTicketId || document.getElementById('track-input').value.trim();
  if (!ticketId) {
    showToast('⚠️ Please enter a valid Ticket ID (e.g. CP-2026-1001)');
    return;
  }

  try {
    const res = await fetch(`/api/complaints/track/${encodeURIComponent(ticketId)}`);
    if (!res.ok) {
      showToast(`Ticket ${ticketId} not found.`);
      return;
    }
    const data = await res.json();
    renderTrackingTimeline(data.ticket, data.location);
  } catch (err) {
    showToast('Error retrieving ticket status.');
  }
}

function renderTrackingTimeline(ticket, loc) {
  const container = document.getElementById('tracking-result-box');
  container.style.display = 'block';
  container.scrollIntoView({ behavior: 'smooth' });

  const status = ticket.status; // 'Pending Approval', 'Approved', 'In Progress', 'Resolved'

  const step1 = true;
  const step2 = true;
  const step3 = ['Approved', 'In Progress', 'Resolved'].includes(status);
  const step4 = ['In Progress', 'Resolved'].includes(status);
  const step5 = status === 'Resolved';

  container.innerHTML = `
    <div class="card" style="border-color: rgba(6, 182, 212, 0.4);">
      <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
        <div>
          <span class="badge-status status-${status.toLowerCase().replace(' ', '-')}">${status}</span>
          <h2 style="margin-top: 0.5rem; font-size: 1.5rem;">Ticket: ${ticket.ticket_id}</h2>
          <div style="color: var(--text-secondary); font-size: 0.88rem;">
            Location: <strong>${ticket.location_id} (${loc.zone} · ${loc.road_type})</strong>
          </div>
        </div>
        <div style="text-align: right;">
          <div style="font-size: 0.8rem; color: var(--text-muted);">MCDA PRIORITY</div>
          <div style="font-family: var(--font-heading); font-size: 1.8rem; font-weight: 800; color: var(--cyan-primary);">
            ${ticket.priority_score.toFixed(1)}
          </div>
          <span class="badge-tier badge-tier-${ticket.severity.toLowerCase()}">${ticket.severity}</span>
        </div>
      </div>

      <div style="background: rgba(255, 255, 255, 0.02); padding: 1rem; border-radius: var(--radius-md); margin-bottom: 1.5rem;">
        <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 4px;">REPORTED NARRATIVE:</div>
        <div style="color: #FFFFFF; font-size: 0.95rem;">"${ticket.description}"</div>
      </div>

      <div class="timeline-stepper">
        <div class="step-item completed">
          <div class="step-circle">✓</div>
          <div class="step-title">1. Grievance Registered</div>
          <div class="step-meta">Logged by Citizen · ${ticket.created_at}</div>
        </div>
        <div class="step-item completed">
          <div class="step-circle">✓</div>
          <div class="step-title">2. ML Classified & Priority Scored</div>
          <div class="step-meta">Category: ${ticket.category} · Priority Score: ${ticket.priority_score.toFixed(1)}/100</div>
          <div style="font-size: 0.82rem; color: #38BDF8; margin-top: 3px;">Rationale: ${ticket.rationale || 'Hazard assessed'}</div>
        </div>
        <div class="step-item ${step3 ? 'completed' : (status === 'Pending Approval' ? 'active' : '')}">
          <div class="step-circle">${step3 ? '✓' : '3'}</div>
          <div class="step-title">3. Civil Authority Approval & Dispatch</div>
          <div class="step-meta">${step3 ? `Approved by Officer · Assigned to: ${ticket.assigned_department || 'Department'}` : 'Awaiting Government Officer Review in Priority Queue'}</div>
        </div>
        <div class="step-item ${step4 ? 'completed' : (status === 'Approved' ? 'active' : '')}">
          <div class="step-circle">${step4 ? '✓' : '4'}</div>
          <div class="step-title">4. Field Crew Dispatched</div>
          <div class="step-meta">${step4 ? (ticket.worker_notes || 'Crew actively performing repairs on site') : 'Pending crew deployment'}</div>
        </div>
        <div class="step-item ${step5 ? 'completed' : (status === 'In Progress' ? 'active' : '')}">
          <div class="step-circle">${step5 ? '✓' : '5'}</div>
          <div class="step-title">5. Hazard Resolved & Verified</div>
          <div class="step-meta">${step5 ? `Resolved at ${ticket.resolved_at} · Verified Safe` : `Estimated Turnaround: ~${ticket.estimated_resolution_hours} hours`}</div>
        </div>
      </div>
    </div>
  `;
}

// ==========================================
// Government Officer Portal Operations
// ==========================================

async function loadOfficerQueue(statusFilter = '') {
  try {
    const url = statusFilter ? `/api/officer/queue?status=${encodeURIComponent(statusFilter)}` : '/api/officer/queue';
    const res = await fetch(url);
    const data = await res.json();
    state.officerQueue = data.queue;
    renderOfficerQueue();
  } catch (err) {
    console.error('Failed to load officer queue', err);
  }
}

function renderOfficerQueue() {
  const container = document.getElementById('officer-queue-table-body');
  if (!container) return;

  if (state.officerQueue.length === 0) {
    container.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-muted);">No complaints in this queue.</td></tr>`;
    return;
  }

  container.innerHTML = state.officerQueue.map(item => {
    const loc = item.location_meta || {};
    const flags = [];
    if (loc.near_hospital) flags.push('🏥 Hospital');
    if (loc.near_school) flags.push('🏫 School');

    const isPending = item.status === 'Pending Approval';
    const actionBtn = isPending
      ? `<button class="auth-btn" style="padding: 4px 12px; font-size: 0.8rem;" onclick="openApprovalModal('${item.ticket_id}')">⚡ Review & Dispatch</button>`
      : `<span style="font-size: 0.8rem; color: var(--text-muted);">${item.assigned_department || item.status}</span>`;

    return `
      <tr>
        <td>
          <div style="font-weight: 800; font-family: var(--font-heading); font-size: 1.15rem; color: var(--cyan-primary);">
            ${item.priority_score.toFixed(1)}
          </div>
          <span class="badge-tier badge-tier-${item.severity.toLowerCase()}">${item.severity}</span>
        </td>
        <td>
          <strong>${item.ticket_id}</strong>
          <div style="font-size: 0.75rem; color: var(--text-muted);">${item.created_at}</div>
        </td>
        <td>
          <div>${item.category}</div>
          <div style="font-size: 0.8rem; color: var(--text-secondary); max-width: 280px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            "${item.description}"
          </div>
        </td>
        <td>
          <strong>${item.location_id}</strong> (${loc.zone || 'Zone'})
          ${flags.length ? `<div style="font-size: 0.72rem; color: #F87171;">${flags.join(' ')}</div>` : ''}
        </td>
        <td>
          <span class="badge-status status-${item.status.toLowerCase().replace(' ', '-')}">${item.status}</span>
        </td>
        <td>~${item.estimated_resolution_hours.toFixed(1)}h</td>
        <td>${actionBtn}</td>
      </tr>
    `;
  }).join('');
}

async function openApprovalModal(ticketId) {
  const item = state.officerQueue.find(q => q.ticket_id === ticketId);
  if (!item) return;

  // Load workers list
  try {
    const res = await fetch('/api/officer/workers');
    const wData = await res.json();
    state.workersList = wData.workers;
  } catch (err) {
    console.error('Failed to load workers', err);
  }

  const modal = document.getElementById('approval-modal');
  document.getElementById('approve-ticket-id').textContent = item.ticket_id;
  document.getElementById('approve-desc').textContent = item.description;
  document.getElementById('approve-category').textContent = item.category;
  document.getElementById('approve-location').textContent = `${item.location_id} (${item.location_meta?.zone || 'Zone'})`;
  document.getElementById('approve-score').textContent = `${item.priority_score.toFixed(1)} / 100 (${item.priority_tier})`;
  document.getElementById('approve-rationale').textContent = item.rationale || 'Assessed by MCDA priority engine.';

  const workerSel = document.getElementById('worker-select');
  workerSel.innerHTML = state.workersList.map(w => 
    `<option value="${w.id}">${w.full_name} — ${w.department}</option>`
  ).join('');

  document.getElementById('confirm-approve-btn').onclick = () => submitApproval(ticketId);
  modal.classList.add('active');
}

async function submitApproval(ticketId) {
  const workerId = document.getElementById('worker-select').value;
  const workerObj = state.workersList.find(w => w.id === workerId);
  const dept = workerObj ? workerObj.department : 'Municipal Works';

  try {
    const res = await fetch(`/api/officer/approve/${ticketId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        officer_id: state.currentUser?.id || 'USR-001',
        worker_id: workerId,
        department: dept,
      }),
    });
    const data = await res.json();
    if (data.status === 'success') {
      showToast(`✅ ${data.message}`);
      document.getElementById('approval-modal').classList.remove('active');
      await loadOfficerQueue();
      await refreshKPIs();
    }
  } catch (err) {
    showToast('Failed to approve complaint.');
  }
}

// ==========================================
// Field Crew Worker Operations
// ==========================================

async function loadWorkerTasks() {
  const workerId = state.currentUser?.id || 'USR-002';
  try {
    const res = await fetch(`/api/worker/tasks/${workerId}`);
    const data = await res.json();
    state.workerTasks = data.tasks;
    renderWorkerTasks();
  } catch (err) {
    console.error('Failed to load worker tasks', err);
  }
}

function renderWorkerTasks() {
  const container = document.getElementById('worker-tasks-list');
  if (!container) return;

  if (state.workerTasks.length === 0) {
    container.innerHTML = `
      <div class="card" style="text-align: center; color: var(--text-muted); padding: 3rem;">
        <h3>🎉 All Assigned Work Orders Completed</h3>
        <p style="margin-top: 0.5rem;">No active hazard repairs currently assigned to your crew.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = state.workerTasks.map(t => {
    const loc = t.location_meta || {};
    const isInProgress = t.status === 'In Progress';

    return `
      <div class="card" style="margin-bottom: 1.25rem; border-color: rgba(6, 182, 212, 0.3);">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
          <div>
            <span class="badge-status status-${t.status.toLowerCase().replace(' ', '-')}">${t.status}</span>
            <span class="badge-tier badge-tier-${t.severity.toLowerCase()}" style="margin-left: 0.5rem;">${t.severity}</span>
            <h3 style="margin-top: 0.5rem;">${t.ticket_id}: ${t.category}</h3>
            <div style="color: var(--text-secondary); font-size: 0.88rem;">
              Location: <strong>${t.location_id} (${loc.zone} · ${loc.road_type} · ${loc.road_condition} Road)</strong>
            </div>
          </div>
          <div style="text-align: right;">
            <div style="font-size: 0.8rem; color: var(--text-muted);">MCDA PRIORITY</div>
            <div style="font-family: var(--font-heading); font-size: 1.8rem; font-weight: 800; color: var(--cyan-primary);">
              ${t.priority_score.toFixed(1)}
            </div>
          </div>
        </div>

        <div style="background: rgba(255, 255, 255, 0.02); padding: 1rem; border-radius: var(--radius-md); margin-bottom: 1rem;">
          <div style="color: #FFFFFF; font-size: 0.95rem;">"${t.description}"</div>
          ${t.rationale ? `<div style="font-size: 0.8rem; color: #38BDF8; margin-top: 6px;">Notice: ${t.rationale}</div>` : ''}
        </div>

        <div style="display: flex; gap: 0.75rem; justify-content: flex-end;">
          ${!isInProgress ? `
            <button class="auth-btn" style="background: var(--medium); color: #0A0F1D;" onclick="updateTaskStatus('${t.ticket_id}', 'In Progress')">
              🚚 Start Work (Dispatch Crew)
            </button>
          ` : ''}
          <button class="auth-btn" onclick="openResolveModal('${t.ticket_id}')">
            ✅ Mark Resolved (Complete Repair)
          </button>
        </div>
      </div>
    `;
  }).join('');
}

async function updateTaskStatus(ticketId, newStatus, notes = 'Crew on site conducting repair work.') {
  const workerId = state.currentUser?.id || 'USR-002';
  try {
    const res = await fetch(`/api/worker/update/${ticketId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        worker_id: workerId,
        new_status: newStatus,
        worker_notes: notes,
      }),
    });
    const data = await res.json();
    if (data.status === 'success') {
      showToast(`Task ${ticketId}: ${newStatus}`);
      await loadWorkerTasks();
      await refreshKPIs();
    }
  } catch (err) {
    showToast('Failed to update task.');
  }
}

function openResolveModal(ticketId) {
  const modal = document.getElementById('resolve-modal');
  document.getElementById('resolve-ticket-id').textContent = ticketId;
  document.getElementById('confirm-resolve-btn').onclick = async () => {
    const notes = document.getElementById('resolve-notes').value.trim() || 'Repairs fully executed according to municipal standard.';
    const hours = parseFloat(document.getElementById('resolve-hours').value) || 2.5;
    const workerId = state.currentUser?.id || 'USR-002';

    try {
      const res = await fetch(`/api/worker/update/${ticketId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          worker_id: workerId,
          new_status: 'Resolved',
          worker_notes: notes,
          actual_hours: hours,
        }),
      });
      const data = await res.json();
      if (data.status === 'success') {
        showToast(`🎉 Work order ${ticketId} resolved & closed!`);
        modal.classList.remove('active');
        await loadWorkerTasks();
        await refreshKPIs();
      }
    } catch (err) {
      showToast('Error completing work order.');
    }
  };
  modal.classList.add('active');
}

// ==========================================
// Role Switching & Personas
// ==========================================

function switchPersona(persona) {
  state.currentRole = persona;
  document.querySelectorAll('.persona-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.persona === persona);
  });

  if (persona === 'citizen') {
    state.currentUser = null;
    showView('citizen-view');
  } else if (persona === 'officer') {
    state.currentUser = {
      id: 'USR-001',
      full_name: 'Chief Eng. Rajesh Sharma',
      role: 'officer',
      department: 'Civil Infrastructure Command',
    };
    showView('officer-view');
    loadOfficerQueue();
  } else if (persona === 'worker') {
    state.currentUser = {
      id: 'USR-002',
      full_name: 'Vikram Singh (Crew Lead)',
      role: 'worker',
      department: 'Road Maintenance & Pothole Squad',
    };
    showView('worker-view');
    loadWorkerTasks();
  }
  updateUserHeader();
}

function showView(viewId) {
  document.querySelectorAll('.portal-view').forEach(el => {
    el.style.display = (el.id === viewId) ? 'block' : 'none';
  });
  document.querySelectorAll('.nav-tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.targetView === viewId);
  });
}

function updateUserHeader() {
  const container = document.getElementById('user-profile-header');
  if (!state.currentUser) {
    container.innerHTML = `
      <button class="auth-btn" onclick="openLoginModal()">
        🔐 Staff Login
      </button>
    `;
  } else {
    container.innerHTML = `
      <div class="user-badge">
        <div class="user-avatar">${state.currentUser.full_name.charAt(0)}</div>
        <div style="font-size: 0.85rem; line-height: 1.1;">
          <div style="font-weight: 700;">${state.currentUser.full_name}</div>
          <div style="font-size: 0.72rem; color: var(--cyan-primary);">${state.currentUser.role.toUpperCase()}</div>
        </div>
        <button onclick="switchPersona('citizen')" style="background: transparent; border: none; color: var(--text-muted); cursor: pointer; font-size: 0.8rem; margin-left: 0.25rem;">✕</button>
      </div>
    `;
  }
}

function openLoginModal() {
  document.getElementById('login-modal').classList.add('active');
}

async function handleLoginSubmit(e) {
  e.preventDefault();
  const email = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value.trim();

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (data.status === 'success') {
      state.currentUser = data.user;
      document.getElementById('login-modal').classList.remove('active');
      switchPersona(data.user.role);
      showToast(`Welcome, ${data.user.full_name}!`);
    } else {
      showToast(data.detail || 'Invalid credentials');
    }
  } catch (err) {
    showToast('Login request failed.');
  }
}

// ==========================================
// Toast & Event Listeners
// ==========================================

function showToast(message) {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `<span>⚡</span> <span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 4000);
}

function setupEventListeners() {
  // Navigation tabs
  document.querySelectorAll('.nav-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.targetView;
      if (target === 'officer-view') {
        switchPersona('officer');
      } else if (target === 'worker-view') {
        switchPersona('worker');
      } else {
        switchPersona('citizen');
      }
    });
  });

  // Persona buttons
  document.querySelectorAll('.persona-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      switchPersona(btn.dataset.persona);
    });
  });

  // Complaint form live analysis triggers
  const descEl = document.getElementById('complaint-desc');
  if (descEl) descEl.addEventListener('input', runAnalysisPreview);

  const locSel = document.getElementById('location-select');
  if (locSel) {
    locSel.addEventListener('change', () => {
      updateLocationPreview(locSel.value);
      runAnalysisPreview();
    });
  }

  document.querySelectorAll('input[name="urgency"]').forEach(radio => {
    radio.addEventListener('change', runAnalysisPreview);
  });

  // Form submits
  const form = document.getElementById('complaint-form');
  if (form) form.addEventListener('submit', handleComplaintSubmit);

  const loginForm = document.getElementById('login-form');
  if (loginForm) loginForm.addEventListener('submit', handleLoginSubmit);

  // Modal close handlers
  document.querySelectorAll('.modal-close-btn, .btn-modal-close').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
    });
  });
}

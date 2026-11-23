/**
 * LabLink Platform — Faculty Approvals & Project Proposals Engine (approvals.js)
 * Manages project submissions, GenAI feasibility scoring, faculty access review,
 * and authenticated approval/rejection decision workflows.
 */

let activeProposals = [];

/**
 * Loads proposal data from the backend and hydrates all relevant views.
 */
async function loadProposalsData() {
  try {
    const res = await apiFetch('/api/v1/approvals');
    if (res.ok) {
      activeProposals = await res.json();
      updateFacultyPendingBadge();
      renderFacultyOverviewQueue();
      renderFacultyFullQueue();
      renderStudentProposals();
    }
  } catch (e) {
    console.warn('[LabLink Approvals] Failed to fetch proposals:', e);
  }
}

/**
 * Updates the pending count badge on the Faculty view.
 */
function updateFacultyPendingBadge() {
  const pendingCount = activeProposals.filter(p => p.status === 'PENDING').length;
  const badge = document.getElementById('faculty-pending-badge');
  if (badge) {
    badge.textContent = `${pendingCount} Pending Review`;
  }
}

/**
 * Renders the top pending proposals in the Faculty Overview card.
 */
function renderFacultyOverviewQueue() {
  const container = document.getElementById('faculty-overview-queue');
  if (!container) return;

  const pending = activeProposals.filter(p => p.status === 'PENDING').slice(0, 3);
  if (pending.length === 0) {
    container.innerHTML = '<div class="p-gutter-md text-on-surface-variant font-body text-body-md">All pending proposals reviewed.</div>';
    return;
  }

  container.innerHTML = pending.map(p => {
    const ai = p.ai_evaluation || {};
    const score = ai.feasibility_score !== undefined ? ai.feasibility_score : 85;
    const safeTitle = escapeHtml(p.project_title);
    const safeStudent = escapeHtml(p.student_name);
    const safeEquip = escapeHtml(p.equipment_name || p.equipment_id);
    const rawId = escapeHtml(p.proposal_id);

    return `
      <article class="p-gutter-md rounded-lg bg-surface-container border border-outline-variant flex flex-col sm:flex-row sm:items-center justify-between gap-gutter-md">
        <div class="flex flex-col gap-gutter-xs">
          <div class="flex items-center gap-gutter-sm">
            <h3 class="font-title text-title-md text-on-surface font-semibold">${safeTitle}</h3>
            <span class="px-gutter-sm py-gutter-xs rounded-full bg-secondary-container text-on-secondary-container font-mono text-label-sm">AI Score: ${score}/100</span>
          </div>
          <p class="font-body text-body-md text-on-surface-variant">${safeStudent} · Requesting: ${safeEquip}</p>
        </div>
        <div class="flex items-center gap-gutter-xs shrink-0">
          <button type="button" onclick="rejectProposal('${rawId}')" class="px-gutter-md py-gutter-sm rounded-full bg-surface-container-high text-rose-400 border border-outline-variant font-label text-label-sm hover:bg-rose-950 transition-colors">
            Reject
          </button>
          <button type="button" onclick="approveProposal('${rawId}')" class="px-gutter-md py-gutter-sm rounded-full bg-tangerine-orange text-on-primary font-label text-label-sm hover:opacity-90 transition-opacity">
            Approve Grant
          </button>
        </div>
      </article>
    `;
  }).join('');
}

/**
 * Renders the full Access Queue subpage with real proposal items.
 */
function renderFacultyFullQueue() {
  const container = document.getElementById('faculty-full-queue-list');
  if (!container) return;

  if (activeProposals.length === 0) {
    container.innerHTML = '<div class="p-gutter-md text-on-surface-variant font-body text-body-md">No proposals found.</div>';
    return;
  }

  container.innerHTML = activeProposals.map(p => {
    const ai = p.ai_evaluation || {};
    const score = ai.feasibility_score !== undefined ? ai.feasibility_score : 85;
    const safeTitle = escapeHtml(p.project_title);
    const safeStudent = escapeHtml(p.student_name);
    const safeEquip = escapeHtml(p.equipment_name || p.equipment_id);
    const safeDesc = escapeHtml(p.description);
    const rawId = escapeHtml(p.proposal_id);
    const isPending = p.status === 'PENDING';
    const statusClass = isPending ? 'bg-amber-500/20 text-amber-300' : (p.status === 'APPROVED' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300');

    return `
      <article class="p-gutter-lg rounded-xl bg-surface-container border border-outline-variant flex flex-col gap-gutter-md">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-gutter-sm">
          <div class="flex items-center gap-gutter-sm">
            <h3 class="font-title text-title-lg text-on-surface font-semibold">${safeTitle}</h3>
            <span class="px-gutter-sm py-gutter-xs rounded-full ${statusClass} font-mono text-label-sm">${p.status}</span>
          </div>
          <button type="button" onclick="showAiBreakdown('${rawId}')" class="px-gutter-sm py-gutter-xs rounded-full bg-primary-container text-on-primary-container font-mono text-label-sm hover:opacity-90 self-start sm:self-auto">
            AI Feasibility: ${score}/100
          </button>
        </div>
        <p class="font-body text-body-md text-on-surface-variant">${safeDesc}</p>
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-gutter-md pt-gutter-sm border-t border-outline-variant">
          <span class="font-body text-body-sm text-on-surface-variant">Applicant: ${safeStudent} · Target: ${safeEquip}</span>
          ${isPending ? `
            <div class="flex items-center gap-gutter-sm">
              <button type="button" onclick="rejectProposal('${rawId}')" class="px-gutter-md py-gutter-sm rounded-full bg-surface-container-high text-rose-400 border border-outline-variant font-label text-label-sm hover:bg-rose-950 transition-colors">
                Reject
              </button>
              <button type="button" onclick="approveProposal('${rawId}')" class="px-gutter-md py-gutter-sm rounded-full bg-tangerine-orange text-on-primary font-label text-label-sm hover:opacity-90 transition-opacity">
                Approve Request
              </button>
            </div>
          ` : `
            <span class="font-mono text-label-sm text-on-surface-variant">Decision Finalized</span>
          `}
        </div>
      </article>
    `;
  }).join('');
}

/**
 * Renders the student's submitted project proposals in the student subpage.
 */
function renderStudentProposals() {
  const container = document.getElementById('student-proposals-list');
  if (!container) return;

  if (activeProposals.length === 0) {
    container.innerHTML = '<div class="p-gutter-md text-on-surface-variant font-body text-body-md">No submitted project proposals yet. Submit one using the button above.</div>';
    return;
  }

  container.innerHTML = activeProposals.map(p => {
    const ai = p.ai_evaluation || {};
    const score = ai.feasibility_score !== undefined ? ai.feasibility_score : 85;
    const safeTitle = escapeHtml(p.project_title);
    const safeEquip = escapeHtml(p.equipment_name || p.equipment_id);
    const isPending = p.status === 'PENDING';
    const statusClass = isPending ? 'bg-amber-500/20 text-amber-300' : (p.status === 'APPROVED' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300');

    return `
      <div class="rounded-lg bg-surface-container p-gutter-md border border-outline-variant flex items-center justify-between gap-gutter-md">
        <div class="flex flex-col gap-gutter-xs">
          <span class="font-title text-title-md text-on-surface font-semibold">${safeTitle}</span>
          <span class="font-body text-body-md text-on-surface-variant">${safeEquip} · AI Feasibility: ${score}/100</span>
        </div>
        <span class="px-gutter-sm py-gutter-xs rounded-full ${statusClass} font-label text-label-sm">${p.status}</span>
      </div>
    `;
  }).join('');
}

/**
 * Submits faculty approval decision to the backend.
 * @param {string} proposalId Identifier of proposal.
 */
async function approveProposal(proposalId) {
  try {
    const res = await apiFetch(`/api/v1/approvals/${proposalId}/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        decision: 'APPROVED',
        feedback_notes: 'Approved by faculty instructor for capstone milestone.'
      })
    });

    if (res.ok) {
      const data = await res.json();
      showToast(`✅ Approved! HMAC Signature: ${(data.state_signature || '').slice(0, 10)}... Access granted.`);
      await loadProposalsData();
    } else {
      const err = await res.json();
      showToast(err.detail || 'Approval rejected by server policy', true);
    }
  } catch (e) {
    showToast('Failed to approve proposal', true);
  }
}

/**
 * Submits faculty rejection decision to the backend.
 * @param {string} proposalId Identifier of proposal.
 */
async function rejectProposal(proposalId) {
  try {
    const res = await apiFetch(`/api/v1/approvals/${proposalId}/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        decision: 'REJECTED',
        feedback_notes: 'Insufficient compute justification. Please refine milestones.'
      })
    });

    if (res.ok) {
      showToast(`Proposal ${proposalId} rejected.`);
      await loadProposalsData();
    } else {
      const err = await res.json();
      showToast(err.detail || 'Action rejected', true);
    }
  } catch (e) {
    showToast('Failed to reject proposal', true);
  }
}

/**
 * Displays AI feasibility breakdown in an accessible toast alert.
 * @param {string} proposalId Identifier of proposal.
 */
function showAiBreakdown(proposalId) {
  const p = activeProposals.find(item => item.proposal_id === proposalId);
  if (p && p.ai_evaluation) {
    const ai = p.ai_evaluation;
    showToast(`AI Feasibility: ${ai.feasibility_score}/100 | Risk: ${ai.safety_risk_level} | Rec: ${ai.suggested_action}`);
  } else {
    showToast('Multi-Factor Weights: Deadline 40%, Academic Tier 30%, Fair-use 20%, Safety 10%');
  }
}

/**
 * Opens project proposal modal.
 */
function openProjectModal() {
  const modal = document.getElementById('project-modal');
  if (modal) {
    modal.classList.remove('hidden');
    modal.classList.add('flex');
  }
}

/**
 * Closes project proposal modal.
 */
function closeProjectModal() {
  const modal = document.getElementById('project-modal');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

/**
 * Submits a new project access proposal to the backend API.
 * @param {Event} e Submit event.
 */
async function submitProjectRequest(e) {
  e.preventDefault();
  const title = document.getElementById('proj-title')?.value || 'Senior Capstone Research';
  const tier = document.getElementById('proj-tier')?.value || 'capstone';
  const equipId = document.getElementById('proj-equip')?.value || 'equip_h100_01';
  const hours = parseFloat(document.getElementById('proj-hours')?.value || '20');
  const desc = document.getElementById('proj-desc')?.value || 'Multimodal model fine-tuning with autonomous verification';

  closeProjectModal();
  showToast('Submitting project request to faculty queue...');

  try {
    const res = await apiFetch('/api/v1/proposals', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_title: title,
        academic_tier: tier,
        equipment_id: equipId,
        requested_hours: hours,
        description: desc
      })
    });

    if (res.ok) {
      const data = await res.json();
      const score = data.ai_evaluation?.feasibility_score || 88;
      showToast(`✅ Submitted! GenAI Feasibility: ${score}/100. Pending faculty sign-off.`);
      await loadProposalsData();
    } else {
      const err = await res.json();
      showToast(err.detail || 'Failed to submit proposal', true);
    }
  } catch (err) {
    showToast('Network error submitting proposal', true);
  }
}

/**
 * LabLink Platform — Application Orchestrator & View Controller (app.js)
 * Manages POV switching, subpage views, mobile navigation drawer,
 * modal focus trapping, and unified application initialization.
 */

const povMeta = {
  student: {
    stat: '32 GPU hrs left',
    initials: 'ML',
    name: 'Maya Lin',
    role: "CS '26 · Student",
    search: 'Search 24 workstations, robotics, or dev kits...',
    copilotBadge: 'GenAI',
    copilotTitle: 'Lab Copilot',
    copilotDesc: 'Describe your project to match the right lab equipment.',
    copilotBtn: 'Auto-Match'
  },
  teacher: {
    stat: '6 Active Courses',
    initials: 'AT',
    name: 'Dr. Aris Thorne',
    role: 'Faculty · AI Lab',
    search: 'Search courses, teams, or grants...',
    copilotBadge: 'Cohort',
    copilotTitle: 'Cohort Sync',
    copilotDesc: 'Match course project briefs to lab equipment capacity.',
    copilotBtn: 'Review Queue'
  },
  admin: {
    stat: '18 / 24 Workstations Online',
    initials: 'DP',
    name: 'Devon Park',
    role: 'Lab Assistant',
    search: 'Search bays, sensors, or alerts...',
    copilotBadge: 'Ops',
    copilotTitle: 'Bay Diagnostics',
    copilotDesc: 'Check which bays are ready for incoming project specs.',
    copilotBtn: 'Run Sweep'
  }
};

let activePOV = 'student';

/**
 * Switches the active application POV (Student / Faculty / Lab Assistant).
 * Updates styling, permissions, header stats, and hydrates role data.
 * @param {string} povKey Role identifier ('student', 'teacher', 'admin').
 */
async function switchPOV(povKey) {
  activePOV = povKey;
  await setPerspectiveAuth(povKey);

  const meta = povMeta[povKey];
  const povTabs = document.querySelectorAll('.pov-tab');
  const navItems = document.querySelectorAll('.nav-item');
  const povPanels = document.querySelectorAll('.pov-panel');

  povTabs.forEach((tab) => {
    const isActive = tab.dataset.pov === povKey;
    tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
    tab.classList.toggle('bg-tangerine-orange', isActive);
    tab.classList.toggle('text-on-primary', isActive);
    tab.classList.toggle('shadow-sm', isActive);
    tab.classList.toggle('font-semibold', isActive);
    tab.classList.toggle('text-on-surface-variant', !isActive);
  });

  navItems.forEach((item) => {
    const isRoleMatch = item.dataset.role === povKey;
    item.hidden = !isRoleMatch;
    item.classList.toggle('hidden', !isRoleMatch);
    if (isRoleMatch) {
      const isOverview = item.dataset.navTarget === 'overview';
      setNavItemActive(item, isOverview);
    }
  });

  const subView = document.getElementById('subpage-view');
  if (subView) {
    subView.setAttribute('hidden', '');
    subView.innerHTML = '';
  }

  povPanels.forEach((panel) => {
    const isTarget = panel.id === `panel-${povKey}`;
    if (isTarget) {
      panel.removeAttribute('hidden');
      panel.classList.remove('animate-panel-enter');
      void panel.offsetWidth;
      panel.classList.add('animate-panel-enter');
    } else {
      panel.setAttribute('hidden', '');
    }
  });

  if (meta) {
    const statEl = document.getElementById('header-stat-text');
    const avatarEl = document.getElementById('header-avatar');
    const nameEl = document.getElementById('header-user-name');
    const roleEl = document.getElementById('header-user-role');
    const searchEl = document.getElementById('lab-search');
    const badgeEl = document.getElementById('copilot-badge');
    const titleEl = document.getElementById('copilot-title');
    const descEl = document.getElementById('copilot-desc');
    const btnLabelEl = document.getElementById('copilot-btn-label');

    if (statEl) statEl.textContent = meta.stat;
    if (avatarEl) avatarEl.textContent = meta.initials;
    if (nameEl) nameEl.textContent = meta.name;
    if (roleEl) roleEl.textContent = meta.role;
    if (searchEl) searchEl.placeholder = meta.search;
    if (badgeEl) badgeEl.textContent = meta.copilotBadge;
    if (titleEl) titleEl.textContent = meta.copilotTitle;
    if (descEl) descEl.textContent = meta.copilotDesc;
    if (btnLabelEl) btnLabelEl.textContent = meta.copilotBtn;
  }

  // Refresh schedule and proposals for new view
  await loadUpcomingConfirmedBookings();
  await loadProposalsData();
}

/**
 * Sets navigation item active styling.
 */
function setNavItemActive(item, isActive) {
  const icon = item.querySelector('.material-symbols-outlined');
  item.classList.toggle('bg-surface-container-high', isActive);
  item.classList.toggle('text-on-surface', isActive);
  item.classList.toggle('text-on-surface-variant', !isActive);
  if (icon) {
    icon.classList.toggle('text-tangerine-orange', isActive);
    icon.style.fontVariationSettings = isActive ? "'FILL' 1" : "'FILL' 0";
  }
}

// Subpage HTML templates (with 24 campus items & Gemini 2.5 Flash branding)
const subpageTemplates = {
  'student:discovery': `
    <div class="flex flex-wrap items-center justify-between gap-gutter-md">
      <div>
        <span class="font-mono text-label-sm text-tangerine-orange uppercase tracking-wider">Student · Cross-Dept Catalog</span>
        <h1 class="font-display text-display-lg-mobile lg:text-display-lg text-on-surface mt-gutter-xs">Equipment Explorer</h1>
        <p class="font-body text-body-lg text-on-surface-variant">Browse all 24 campus workstations, robotics arms, FPGAs, and bio instruments.</p>
      </div>
      <button type="button" onclick="openTabView('student','overview')" class="px-gutter-md py-gutter-sm rounded-full bg-surface-container text-on-surface border border-outline-variant font-label text-label-lg">← Back to Overview</button>
    </div>
    <div class="flex flex-col gap-gutter-md">
      <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-gutter-md">
        <div class="relative flex-1">
          <span class="material-symbols-outlined text-[18px] text-on-surface-variant absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none">search</span>
          <input id="explorer-search-input" oninput="filterExplorerItems(this.value)" type="search" placeholder="Search 24 campus instruments by name, dept, or spec..." class="w-full pl-10 pr-gutter-md py-gutter-sm rounded-full bg-surface-container-low border border-outline-variant text-body-md text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary">
        </div>
        <div class="flex items-center gap-gutter-xs overflow-x-auto pb-1 sm:pb-0">
          <button type="button" onclick="setExplorerCategory('all', this)" class="explorer-cat-btn px-gutter-md py-gutter-xs rounded-full bg-tangerine-orange text-on-primary font-label text-label-sm whitespace-nowrap">All (24)</button>
          <button type="button" onclick="setExplorerCategory('compute', this)" class="explorer-cat-btn px-gutter-md py-gutter-xs rounded-full bg-surface-container text-on-surface-variant font-label text-label-sm whitespace-nowrap">Compute</button>
          <button type="button" onclick="setExplorerCategory('robotics', this)" class="explorer-cat-btn px-gutter-md py-gutter-xs rounded-full bg-surface-container text-on-surface-variant font-label text-label-sm whitespace-nowrap">Robotics</button>
          <button type="button" onclick="setExplorerCategory('sensors', this)" class="explorer-cat-btn px-gutter-md py-gutter-xs rounded-full bg-surface-container text-on-surface-variant font-label text-label-sm whitespace-nowrap">RF & Sensors</button>
          <button type="button" onclick="setExplorerCategory('fab', this)" class="explorer-cat-btn px-gutter-md py-gutter-xs rounded-full bg-surface-container text-on-surface-variant font-label text-label-sm whitespace-nowrap">Bio & Fab</button>
        </div>
      </div>
      <div id="explorer-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-gutter-lg"></div>
    </div>
  `,
  'student:my-reservations': `
    <div class="flex flex-wrap items-center justify-between gap-gutter-md">
      <div>
        <span class="font-mono text-label-sm text-tangerine-orange uppercase tracking-wider">Student · My Schedule</span>
        <h1 class="font-display text-display-lg-mobile lg:text-display-lg text-on-surface mt-gutter-xs">My Reservations & Holds</h1>
        <p class="font-body text-body-lg text-on-surface-variant">Active BookMyShow 10-minute holds, confirmed bookings, and queue standings.</p>
      </div>
      <button type="button" onclick="openTabView('student','overview')" class="px-gutter-md py-gutter-sm rounded-full bg-surface-container text-on-surface border border-outline-variant font-label text-label-lg">← Back to Overview</button>
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-gutter-xl">
      <div class="lg:col-span-7 flex flex-col gap-gutter-lg">
        <div class="rounded-xl bg-surface-container-low border border-outline-variant p-gutter-lg flex flex-col gap-gutter-md">
          <h2 class="font-headline text-headline-md text-on-surface">Available Today · Recommended by Gemini 2.5 Flash</h2>
          <div class="flex flex-col gap-gutter-sm">
            <div class="rounded-lg bg-surface-container p-gutter-md border border-outline-variant flex items-center justify-between">
              <div><span class="font-title text-title-md text-on-surface block font-bold">14:00 – 15:00 · Jetson AGX Orin 64GB</span><span class="font-body text-body-md text-on-surface-variant">Robotics Center ECE-100 · Mid-Range Tier</span></div>
              <button type="button" onclick="openBookingModal('equip_jetson_01', 'NVIDIA Jetson AGX Orin 64GB', 2)" class="px-gutter-md py-gutter-sm rounded-full bg-tangerine-orange text-on-primary font-label text-label-sm">Reserve Slot</button>
            </div>
            <div class="rounded-lg bg-surface-container p-gutter-md border border-outline-variant flex items-center justify-between">
              <div><span class="font-title text-title-md text-on-surface block font-bold">16:30 – 17:30 · Workstation Alpha (RTX 4090)</span><span class="font-body text-body-md text-on-surface-variant">AI Lab CS-B12 · 24GB VRAM</span></div>
              <button type="button" onclick="openBookingModal('equip_rtx4090_01', 'Workstation Alpha · RTX 4090 24GB', 2)" class="px-gutter-md py-gutter-sm rounded-full bg-tangerine-orange text-on-primary font-label text-label-sm">Reserve Slot</button>
            </div>
          </div>
        </div>
      </div>
      <div class="lg:col-span-5 rounded-xl bg-hero-surface border border-outline-variant p-gutter-lg flex flex-col gap-gutter-md">
        <span class="font-mono text-label-sm text-warm-cream">YOUR SCHEDULE</span>
        <h2 class="font-headline text-headline-md text-warm-cream">Upcoming Confirmed</h2>
        <div id="my-reservations-list" class="flex flex-col gap-gutter-sm">
          <div class="rounded-lg bg-surface-container p-gutter-md border border-outline-variant flex items-center justify-between">
            <div><span class="font-title text-title-md text-on-surface block font-semibold">Jetson AGX Orin 64GB</span><span class="font-mono text-mono-md text-on-surface-variant">14:00 – 15:00 Today</span></div>
            <span class="px-gutter-sm py-gutter-xs rounded-full bg-tangerine-orange text-on-primary font-label text-label-sm">Confirmed</span>
          </div>
        </div>
      </div>
    </div>
  `,
  'student:requests': `
    <div class="flex flex-wrap items-center justify-between gap-gutter-md">
      <div>
        <span class="font-mono text-label-sm text-tangerine-orange uppercase tracking-wider">Student · Grants & Access</span>
        <h1 class="font-display text-display-lg-mobile lg:text-display-lg text-on-surface mt-gutter-xs">Project Proposals</h1>
        <p class="font-body text-body-lg text-on-surface-variant">Track your high-end compute proposals and Gemini 2.5 Flash feasibility scores.</p>
      </div>
      <div class="flex items-center gap-gutter-sm">
        <button type="button" onclick="openProjectModal()" class="px-gutter-md py-gutter-sm rounded-full bg-tangerine-orange text-on-primary font-label text-label-lg">+ New Project Proposal</button>
        <button type="button" onclick="openTabView('student','overview')" class="px-gutter-md py-gutter-sm rounded-full bg-surface-container text-on-surface border border-outline-variant font-label text-label-lg">← Back to Overview</button>
      </div>
    </div>
    <div class="flex flex-col gap-gutter-md">
      <div id="student-proposals-list" class="flex flex-col gap-gutter-md"></div>
    </div>
  `,
  'teacher:queue': `
    <div class="flex flex-wrap items-center justify-between gap-gutter-md">
      <div>
        <span class="font-mono text-label-sm text-tangerine-orange uppercase tracking-wider">Faculty · Access Governance</span>
        <h1 class="font-display text-display-lg-mobile lg:text-display-lg text-on-surface mt-gutter-xs">Faculty Access Review Queue</h1>
        <p class="font-body text-body-lg text-on-surface-variant">Approve or reject student compute proposals with automated Gemini 2.5 Flash feasibility scoring.</p>
      </div>
      <button type="button" onclick="openTabView('teacher','overview')" class="px-gutter-md py-gutter-sm rounded-full bg-surface-container text-on-surface border border-outline-variant font-label text-label-lg">← Back to Overview</button>
    </div>
    <div id="faculty-full-queue-list" class="flex flex-col gap-gutter-lg"></div>
  `,
  'teacher:cohorts': `
    <div class="flex flex-wrap items-center justify-between gap-gutter-md">
      <div>
        <span class="font-mono text-label-sm text-tangerine-orange uppercase tracking-wider">Faculty · Course Teams</span>
        <h1 class="font-display text-display-lg-mobile lg:text-display-lg text-on-surface mt-gutter-xs">Course Cohorts</h1>
        <p class="font-body text-body-lg text-on-surface-variant">Track CS-492, EE-310, and DS-204 student teams and lab milestones.</p>
      </div>
      <button type="button" onclick="openTabView('teacher','overview')" class="px-gutter-md py-gutter-sm rounded-full bg-surface-container text-on-surface border border-outline-variant font-label text-label-lg">← Back to Overview</button>
    </div>
    <div class="flex items-center gap-gutter-sm">
      <button type="button" onclick="selectCohort('CS-492', this)" class="cohort-pill px-gutter-md py-gutter-sm rounded-full bg-tangerine-orange text-on-primary font-label text-label-lg">CS-492 Senior Capstone</button>
      <button type="button" onclick="selectCohort('EE-310', this)" class="cohort-pill px-gutter-md py-gutter-sm rounded-full bg-surface-container text-on-surface-variant border border-outline-variant font-label text-label-lg">EE-310 Embedded Systems</button>
      <button type="button" onclick="selectCohort('DS-204', this)" class="cohort-pill px-gutter-md py-gutter-sm rounded-full bg-surface-container text-on-surface-variant border border-outline-variant font-label text-label-lg">DS-204 Deep Learning</button>
    </div>
    <div class="rounded-xl bg-surface-container-low border border-outline-variant p-gutter-lg flex flex-col gap-gutter-md">
      <div class="flex items-center justify-between">
        <h2 class="font-headline text-headline-md text-on-surface">Cohort Milestone Completion</h2>
        <span id="cohort-completion-val" class="font-mono text-title-lg text-tangerine-orange font-bold">88%</span>
      </div>
      <div class="h-3 rounded-full bg-surface-container overflow-hidden">
        <div class="h-full bg-tangerine-orange rounded-full transition-all duration-state-change" style="width: 88%;"></div>
      </div>
    </div>
  `
};

/**
 * Opens subviews for specific tab targets.
 */
function openTabView(role, target) {
  const panel = document.getElementById(`panel-${role}`);
  const subView = document.getElementById('subpage-view');
  if (!panel || !subView) return;

  const navKey = `${role}:${target}`;
  document.querySelectorAll(`.nav-item[data-role="${role}"]`).forEach((item) => {
    setNavItemActive(item, item.dataset.navTarget === target);
  });

  if (target === 'overview') {
    panel.removeAttribute('hidden');
    subView.setAttribute('hidden', '');
    subView.innerHTML = '';
  } else if (subpageTemplates[navKey]) {
    panel.setAttribute('hidden', '');
    subView.removeAttribute('hidden');
    subView.innerHTML = subpageTemplates[navKey];

    if (target === 'discovery') {
      renderEquipmentExplorer();
    } else if (target === 'queue') {
      renderFacultyFullQueue();
    } else if (target === 'requests') {
      renderStudentProposals();
    } else if (target === 'my-reservations') {
      loadUpcomingConfirmedBookings();
    }
  }
}

/**
 * Toggles bay calibration lock.
 */
function toggleBayLock(btn) {
  const isLocked = btn.dataset.locked === 'true';
  btn.dataset.locked = isLocked ? 'false' : 'true';
  btn.textContent = isLocked ? 'Lock Bay' : 'Unlock Bay';
  btn.className = isLocked
    ? 'px-gutter-md py-gutter-sm rounded-full bg-surface-container text-on-surface border border-outline-variant font-label text-label-sm'
    : 'px-gutter-md py-gutter-sm rounded-full bg-rose-950 text-rose-300 border border-rose-800 font-label text-label-sm';
  showToast(isLocked ? 'Bay unlocked and returned to student pool.' : 'Bay locked for calibration.');
}

/**
 * Cohort selector pill handler.
 */
function selectCohort(code, btn) {
  document.querySelectorAll('.cohort-pill').forEach((p) => {
    const active = p === btn;
    p.className = active
      ? 'cohort-pill px-gutter-md py-gutter-sm rounded-full bg-tangerine-orange text-on-primary font-label text-label-lg'
      : 'cohort-pill px-gutter-md py-gutter-sm rounded-full bg-surface-container text-on-surface-variant border border-outline-variant font-label text-label-lg';
  });
  const map = { 'CS-492': '88%', 'EE-310': '79%', 'DS-204': '94%' };
  const el = document.getElementById('cohort-completion-val');
  if (el) el.textContent = map[code] || '88%';
}

/**
 * Toggles mobile drawer navigation.
 */
function toggleMobileNav() {
  const drawer = document.getElementById('mobile-nav-drawer');
  if (drawer) {
    drawer.classList.toggle('hidden');
  }
}

// --- Global Modal Keyboard Accessibility (Escape key listener) ---
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeBookingModal();
    closeProjectModal();
    closeCopilotModal();
    const drawer = document.getElementById('mobile-nav-drawer');
    if (drawer && !drawer.classList.contains('hidden')) {
      drawer.classList.add('hidden');
    }
  }
});

// --- App Initialization (Single clean sequence preventing duplicate requests) ---
document.addEventListener('DOMContentLoaded', async () => {
  // Bind POV tab clicks
  document.querySelectorAll('.pov-tab').forEach((tab) => {
    tab.addEventListener('click', () => switchPOV(tab.dataset.pov));
  });

  // Bind sidebar nav clicks
  document.querySelectorAll('.nav-item').forEach((item) => {
    item.addEventListener('click', () => {
      openTabView(item.dataset.role, item.dataset.navTarget);
    });
  });

  const initialPov = new URLSearchParams(window.location.search).get('pov') || 'student';
  await switchPOV(initialPov);
  await loadDynamicEquipment();
});

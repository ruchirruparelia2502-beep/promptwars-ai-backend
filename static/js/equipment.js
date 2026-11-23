/**
 * LabLink Platform — Equipment Discovery & Explorer Module (equipment.js)
 * Manages cross-department hardware catalog, caching, category filtering,
 * and semantic search rendering across 24 campus workstations and instruments.
 */

let cachedEquipmentList = [];
let currentExplorerCategory = 'all';

/**
 * Normalizes hourly cost across backend schema variants (hourly_cost_estimate or hourly_rate).
 * @param {Object} item Equipment catalog record.
 * @returns {number} Hourly cost as a float.
 */
function getHourlyCost(item) {
  if (typeof item.hourly_rate === 'number') return item.hourly_rate;
  if (typeof item.hourly_cost_estimate === 'number') return item.hourly_cost_estimate;
  if (item.hourly_cost_estimate) {
    const parsed = parseFloat(String(item.hourly_cost_estimate).replace(/[^0-9.]/g, ''));
    if (!isNaN(parsed)) return parsed;
  }
  return 2.0;
}

/**
 * Resolves the visual icon and theme badge for an equipment item.
 * @param {Object} item Equipment catalog record.
 * @returns {{ category: string, icon: string, iconBg: string }}
 */
function getCategoryAndIcon(item) {
  let category = 'compute';
  let icon = 'memory';
  let iconBg = 'bg-tangerine-orange text-on-primary';
  const nameLower = ((item.name || '') + ' ' + (item.department || '') + ' ' + (item.category || '')).toLowerCase();

  if (nameLower.includes('robot') || nameLower.includes('arm') || nameLower.includes('kuka') || nameLower.includes('ur5e')) {
    category = 'robotics';
    icon = 'precision_manufacturing';
    iconBg = 'bg-secondary-container text-on-secondary-container';
  } else if (nameLower.includes('scope') || nameLower.includes('oscilloscope') || nameLower.includes('vna') || nameLower.includes('spectrum') || nameLower.includes('logic') || nameLower.includes('sdr') || nameLower.includes('sourcemeter') || nameLower.includes('sensor')) {
    category = 'sensors';
    icon = 'sensors';
    iconBg = 'bg-slate-blue text-on-secondary';
  } else if (nameLower.includes('3d') || nameLower.includes('print') || nameLower.includes('pcr') || nameLower.includes('hplc') || nameLower.includes('centrifuge') || nameLower.includes('solder') || nameLower.includes('fab') || nameLower.includes('biotech') || nameLower.includes('laser')) {
    category = 'fab';
    icon = 'build';
    iconBg = 'bg-warm-cream text-on-tertiary';
  } else if (nameLower.includes('pi') || nameLower.includes('stm32') || nameLower.includes('arduino') || nameLower.includes('msp430') || nameLower.includes('esp32') || nameLower.includes('fpga') || nameLower.includes('jetson')) {
    category = 'compute';
    icon = 'developer_board';
    iconBg = 'bg-secondary-container text-on-secondary-container';
  }
  return { category, icon, iconBg };
}

/**
 * Loads equipment from the backend API.
 * Uses in-memory caching to avoid duplicate GET requests on page load.
 */
async function loadDynamicEquipment() {
  if (cachedEquipmentList && cachedEquipmentList.length > 0) {
    // Already cached — avoid redundant network request
    return;
  }

  const list = document.getElementById('equipment-list');
  try {
    const res = await apiFetch('/api/v1/equipment');
    if (!res.ok) return;
    cachedEquipmentList = await res.json();
    if (!cachedEquipmentList || cachedEquipmentList.length === 0) return;

    if (list) {
      list.innerHTML = cachedEquipmentList.map(item => {
        const { category, icon, iconBg } = getCategoryAndIcon(item);
        const hourly = getHourlyCost(item);
        const tier = hourly <= 1.5 ? 'Frugal Entry' : (hourly <= 5.0 ? 'Mid-Range' : 'High-End');
        const tierClass = hourly <= 1.5 ? 'bg-secondary-container text-on-secondary-container' : (hourly <= 5.0 ? 'bg-surface-container-high text-on-surface' : 'bg-primary-container text-on-primary-container');
        const safeName = escapeHtml(item.name);
        const safeDept = escapeHtml(item.department);
        const safeLoc = escapeHtml(item.location);
        const rawNameJs = (item.name || '').replace(/'/g, "\\'");

        return `
          <article data-category="${category}" data-name="${safeName.toLowerCase()} ${safeDept.toLowerCase()} ${safeLoc.toLowerCase()}" class="equip-card rounded-xl bg-surface-container p-gutter-lg border border-outline-variant flex flex-col sm:flex-row sm:items-center justify-between gap-gutter-md transition-transform duration-state-change ease-state-change hover:-translate-y-0.5">
            <div class="flex items-start sm:items-center gap-gutter-md">
              <span class="inline-flex items-center justify-center w-11 h-11 rounded-full ${iconBg} shrink-0">
                <span class="material-symbols-outlined text-[22px]">${icon}</span>
              </span>
              <div class="flex flex-col gap-gutter-xs">
                <div class="flex flex-wrap items-center gap-gutter-sm">
                  <h3 class="font-title text-title-md text-on-surface font-semibold">${safeName}</h3>
                  <span class="px-gutter-sm py-gutter-xs rounded-full ${tierClass} font-label text-label-sm">${tier} · $${hourly.toFixed(2)}/hr</span>
                </div>
                <p class="font-body text-body-md text-on-surface-variant">${safeDept} · ${safeLoc}</p>
              </div>
            </div>
            <button type="button" onclick="openBookingModal('${item.id}', '${rawNameJs}', 2)" class="shrink-0 px-gutter-md py-gutter-sm rounded-full bg-warm-cream text-on-tertiary font-label text-label-lg transition-all duration-state-change ease-state-change hover:-translate-y-0.5 hover:bg-tangerine-orange hover:text-on-primary shadow-sm">
              <span>Book Slot</span>
            </button>
          </article>
        `;
      }).join('');
    }
  } catch (e) {
    console.warn('[LabLink Equipment] Failed to load dynamic equipment from API:', e);
  }
}

/**
 * Filters the equipment list on the Student Overview page by category.
 * @param {string} category Category identifier ('all', 'compute', 'robotics', 'sensors', 'fab').
 */
function filterEquipment(category) {
  const cards = document.querySelectorAll('.equip-card');
  const buttons = document.querySelectorAll('.equip-filter');
  buttons.forEach((btn) => {
    const active = btn.dataset.filter === category;
    btn.classList.toggle('bg-tangerine-orange', active);
    btn.classList.toggle('text-on-primary', active);
    btn.classList.toggle('bg-surface-container', !active);
    btn.classList.toggle('text-on-surface-variant', !active);
  });
  cards.forEach((card) => {
    const match = category === 'all' || card.dataset.category === category;
    card.classList.toggle('hidden', !match);
  });
}

/**
 * Renders all items in the Equipment Explorer subview grid.
 */
function renderEquipmentExplorer() {
  const grid = document.getElementById('explorer-grid');
  if (!grid || !cachedEquipmentList || cachedEquipmentList.length === 0) return;

  grid.innerHTML = cachedEquipmentList.map(item => {
    const { category, icon, iconBg } = getCategoryAndIcon(item);
    const hourly = getHourlyCost(item);
    const safeName = escapeHtml(item.name);
    const safeDept = escapeHtml(item.department);
    const safeLoc = escapeHtml(item.location);
    const rawNameJs = (item.name || '').replace(/'/g, "\\'");

    return `
      <article data-category="${category}" data-name="${safeName.toLowerCase()} ${safeDept.toLowerCase()} ${safeLoc.toLowerCase()}" class="explorer-card rounded-xl bg-surface-container p-gutter-lg border border-outline-variant flex flex-col justify-between gap-gutter-md transition-transform duration-state-change ease-state-change hover:-translate-y-0.5">
        <div class="flex flex-col gap-gutter-sm">
          <div class="flex items-center justify-between">
            <span class="inline-flex items-center justify-center w-10 h-10 rounded-full ${iconBg}">
              <span class="material-symbols-outlined text-[20px]">${icon}</span>
            </span>
            <span class="font-mono text-label-sm text-tangerine-orange">$${hourly.toFixed(2)}/hr</span>
          </div>
          <div>
            <h3 class="font-title text-title-md text-on-surface font-semibold">${safeName}</h3>
            <p class="font-body text-body-sm text-on-surface-variant">${safeDept} · ${safeLoc}</p>
          </div>
        </div>
        <div class="flex items-center justify-between pt-gutter-sm border-t border-outline-variant">
          <span class="font-label text-label-sm text-on-surface-variant uppercase tracking-wider">${category}</span>
          <button type="button" onclick="openBookingModal('${item.id}', '${rawNameJs}', 2)" class="px-gutter-md py-gutter-xs rounded-full bg-tangerine-orange text-on-primary font-label text-label-sm hover:opacity-90">
            Book
          </button>
        </div>
      </article>
    `;
  }).join('');
}

/**
 * Searches and filters the Equipment Explorer view in real time.
 * @param {string} query Search text entered by user.
 */
function filterExplorerItems(query) {
  const q = (query || '').toLowerCase().trim();
  const cards = document.querySelectorAll('.explorer-card');
  cards.forEach(card => {
    const nameData = card.dataset.name || '';
    const catData = card.dataset.category || '';
    const matchesSearch = !q || nameData.includes(q);
    const matchesCat = currentExplorerCategory === 'all' || catData === currentExplorerCategory;
    card.classList.toggle('hidden', !(matchesSearch && matchesCat));
  });
}

/**
 * Category filter pill handler on the Equipment Explorer view.
 * @param {string} cat Category identifier.
 * @param {HTMLElement} btn Clicked filter button.
 */
function setExplorerCategory(cat, btn) {
  currentExplorerCategory = cat;
  document.querySelectorAll('.explorer-cat-btn').forEach(b => {
    const active = b === btn;
    b.classList.toggle('bg-tangerine-orange', active);
    b.classList.toggle('text-on-primary', active);
    b.classList.toggle('bg-surface-container', !active);
    b.classList.toggle('text-on-surface-variant', !active);
  });
  const searchInput = document.getElementById('explorer-search-input');
  filterExplorerItems(searchInput ? searchInput.value : '');
}

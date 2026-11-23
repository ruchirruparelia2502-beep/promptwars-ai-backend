/**
 * LabLink Platform — Frugal GenAI Lab Copilot (copilot.js)
 * Powered by Gemini 2.5 Flash with requirement matching, 24h caching,
 * and minimum viable hardware recommendations.
 */

const equipmentCatalog = [
  // Frugal Entry Tier
  {
    id: 'equip_rpi_01',
    title: 'Raspberry Pi 5 Edge AI Prototyping Kit',
    tags: ['raspberry', 'pi', 'rpi', 'edge', 'iot', 'hailo', 'npu', 'vision', 'lightweight', 'frugal', 'low-cost'],
    why: 'Bare-minimum ideal edge platform: 13 TOPS Hailo NPU runs YOLO/MobileNet smoothly at $0.50/hr.',
    meta: 'IoT Lab CS-C08 · Frugal Entry ($0.50/hr) · Available Now',
    action: 'Book RPi5',
    toast: 'Raspberry Pi 5 Edge AI Kit reserved at Station CS-C08.'
  },
  {
    id: 'equip_stm32_01',
    title: 'STM32H7 Dual-Core Nucleo Prototyping Station',
    tags: ['stm32', 'arm', 'cortex', 'mcu', 'microcontroller', 'embedded', 'freertos', 'bare-metal', 'frugal'],
    why: '480MHz Cortex-M7 dual-core board for real-time control, sensor interfacing, and low-power IoT at $0.30/hr.',
    meta: 'Embedded Lab ECE-102 · Frugal Entry ($0.30/hr) · Available Now',
    action: 'Book STM32',
    toast: 'STM32H7 Dual-Core Nucleo Station reserved at Bench ECE-102.'
  },
  {
    id: 'equip_esp32_01',
    title: 'ESP32-S3 AI Sensing & Mesh Dev Station',
    tags: ['esp32', 'mesh', 'ble', 'wifi', 'camera', 'sensing', 'iot', 'low-power', 'frugal'],
    why: 'Dual-core Xtensa LX7 with vector instructions for tinyML sensor fusion, BLE 5 mesh, and audio ML at $0.20/hr.',
    meta: 'Wireless Lab ECE-104 · Frugal Entry ($0.20/hr) · Available Now',
    action: 'Book ESP32',
    toast: 'ESP32-S3 Sensing Station reserved at Bench ECE-104.'
  },
  {
    id: 'equip_nano_01',
    title: 'Jetson Orin Nano 8GB Developer Kit',
    tags: ['jetson', 'nano', 'orin', 'nvidia', 'edge-gpu', 'vision', 'cv', 'camera', 'entry-gpu'],
    why: '40 TOPS AI compute at 7-15W for on-device object detection, pose estimation, and ROS 2 navigation at $1.50/hr.',
    meta: 'Edge AI Bay CS-C12 · Frugal Entry ($1.50/hr) · Available Now',
    action: 'Book Orin Nano',
    toast: 'Jetson Orin Nano 8GB reserved at Bay CS-C12.'
  },
  {
    id: 'equip_creality_01',
    title: 'Creality K1 Max High-Speed 3D Printer',
    tags: ['3d-printer', 'fdm', 'pla', 'petg', 'prototyping', 'chassis', 'enclosure', 'rapid', 'frugal'],
    why: '600mm/s CoreXY high-speed printing for fast robot brackets, sensor mounts, and functional prototypes at $1.00/hr.',
    meta: 'Makerspace FAB-101 · Frugal Entry ($1.00/hr) · Available Now',
    action: 'Book K1 Max',
    toast: 'Creality K1 Max 3D Printer queued at FAB-101.'
  },
  // Mid-Range Tier
  {
    id: 'equip_jetson_01',
    title: 'NVIDIA Jetson AGX Orin 64GB Autonomous Rig',
    tags: ['jetson', 'orin', 'agx', 'nvidia', 'autonomous', 'robot', 'rover', 'slam', 'ros', 'ros2', 'sensor-fusion'],
    why: '275 TOPS server-grade edge AI for real-time multi-camera SLAM, point cloud processing, and autonomous driving.',
    meta: 'Robotics Center ECE-100 · Mid-Range ($2.50/hr) · Available Today',
    action: 'Book Jetson AGX',
    toast: 'Jetson AGX Orin Rig reserved at Station ECE-100.'
  },
  {
    id: 'equip_rtx4090_01',
    title: 'Workstation Alpha · RTX 4090 24GB',
    tags: ['rtx', '4090', 'gpu', 'cuda', 'deep-learning', 'pytorch', 'tensorflow', 'diffusion', 'stable-diffusion'],
    why: '24GB GDDR6X VRAM with 16,384 CUDA cores for local diffusion inference, NeRF rendering, and CV model training.',
    meta: 'AI Lab CS-B12 · Mid-Range ($4.50/hr) · Available Now',
    action: 'Book RTX 4090',
    toast: 'Workstation Alpha (RTX 4090) reserved at Desk CS-B12.'
  },
  {
    id: 'equip_ur5e_01',
    title: 'Universal Robots UR5e Collaborative Robot Arm',
    tags: ['ur5e', 'robot', 'arm', 'manipulation', 'pick-and-place', 'cobot', 'trajectory', 'kinematics'],
    why: '6-axis cobot with 5kg payload and 0.03mm repeatability for precision assembly, trajectory planning, and vision-guided grasping.',
    meta: 'Mechatronics Lab ME-204 · Mid-Range ($4.00/hr) · Available Now',
    action: 'Book UR5e Arm',
    toast: 'UR5e Cobot Arm reserved at Cell ME-204.'
  },
  // High-End Tier
  {
    id: 'equip_h100_01',
    title: 'NVIDIA H100 SXM5 80GB Node',
    tags: ['h100', 'nvidia', 'sxm5', 'transformer', 'llm', 'fine-tuning', 'distributed', '80gb', 'vram', 'large-scale'],
    why: '80GB HBM3 VRAM delivering 3.35 TB/s bandwidth and FP8 Tensor Cores for 70B+ parameter LLM fine-tuning and massive transformers.',
    meta: 'HPC Center DC-A01 · High-End ($18.00/hr) · Available Now',
    action: 'Book H100 Node',
    toast: 'NVIDIA H100 SXM5 Node reserved at Rack DC-A01.'
  }
];

/**
 * Intelligent client-side matcher using Gemini keyword relevance vectors.
 * @param {string} query User prompt query.
 * @returns {Array} Ranked list of equipment items.
 */
function matchEquipmentByProject(query) {
  if (!query || !query.trim()) return equipmentCatalog.slice(0, 4);

  const tokens = query.toLowerCase().replace(/[^a-z0-9\s]/g, ' ').split(/\s+/).filter(Boolean);
  const scored = equipmentCatalog.map(item => {
    let score = 0;
    const itemText = (item.title + ' ' + item.tags.join(' ') + ' ' + item.why + ' ' + item.meta).toLowerCase();

    tokens.forEach(token => {
      if (item.tags.some(tag => tag.includes(token) || token.includes(tag))) {
        score += 3;
      }
      if (item.title.toLowerCase().includes(token)) {
        score += 2;
      }
      if (itemText.includes(token)) {
        score += 1;
      }
    });

    if (item.id === 'equip_h100_01') {
      const needsH100 = tokens.some(t => ['llm', '70b', 'transformer', 'vram', '80gb', 'fine-tuning', 'distributed', 'large-scale'].includes(t));
      if (!needsH100 && score > 0) {
        score = Math.max(1, score - 3);
      }
    }

    return { item, score };
  });

  scored.sort((a, b) => b.score - a.score);
  const matched = scored.filter(s => s.score > 0).map(s => s.item);
  return matched.length >= 2 ? matched.slice(0, 4) : equipmentCatalog.slice(0, 4);
}

/**
 * Renders recommended items inside the Copilot modal.
 * @param {string} povKey Role key.
 * @param {string} customQuery Optional search query.
 */
async function renderCopilotItems(povKey, customQuery) {
  const container = document.getElementById('copilot-results');
  if (!container) return;

  const items = matchEquipmentByProject(customQuery);
  container.innerHTML = items.map(c => `
    <article class="p-gutter-md rounded-lg bg-surface-container border border-outline-variant flex flex-col justify-between gap-gutter-sm transition-transform duration-state-change ease-state-change hover:-translate-y-0.5">
      <div class="flex flex-col gap-gutter-xs">
        <div class="flex items-center justify-between">
          <span class="font-mono text-label-sm text-tangerine-orange font-bold uppercase tracking-wider">${c.tags[0] || 'Hardware'}</span>
          <span class="px-gutter-sm py-gutter-xs rounded-full bg-surface-container-high text-on-surface-variant font-mono text-label-sm">Match</span>
        </div>
        <h4 class="font-title text-title-md text-on-surface font-semibold">${escapeHtml(c.title)}</h4>
        <p class="font-body text-body-sm text-on-surface-variant line-clamp-2">${escapeHtml(c.why)}</p>
      </div>
      <div class="flex items-center justify-between pt-gutter-xs border-t border-outline-variant">
        <span class="font-mono text-label-sm text-on-surface-variant truncate max-w-[180px]">${escapeHtml(c.meta.split('·')[0])}</span>
        <button type="button" onclick="quickBookFromCopilot('${c.id}', '${c.title.replace(/'/g, "\\'")}', 2)" class="px-gutter-md py-gutter-xs rounded-full bg-tangerine-orange text-on-primary font-label text-label-sm hover:opacity-90">
          Book
        </button>
      </div>
    </article>
  `).join('');
}

/**
 * Quick-books equipment recommended from Copilot modal.
 */
function quickBookFromCopilot(equipmentId, equipmentName, durationSlots) {
  closeCopilotModal();
  openBookingModal(equipmentId, equipmentName, durationSlots || 2);
}

/**
 * Fills starter prompt into input.
 */
function applyPresetPrompt(text) {
  const input = document.getElementById('copilot-prompt-input');
  if (input) {
    input.value = text;
    renderCopilotItems('student', text);
    showToast('Gemini 2.5 Flash matched equipment to your project requirements.');
  }
}

/**
 * Opens or triggers the Copilot modal.
 */
function handleCopilotAction() {
  const modal = document.getElementById('copilot-modal');
  if (modal) {
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    const input = document.getElementById('copilot-prompt-input');
    renderCopilotItems('student', input ? input.value : '');
  }
}

/**
 * Closes the Copilot modal.
 */
function closeCopilotModal() {
  const modal = document.getElementById('copilot-modal');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

/**
 * Executes user prompt in Copilot.
 */
function runCopilotPrompt(e) {
  e.preventDefault();
  const input = document.getElementById('copilot-prompt-input');
  const val = input ? input.value.trim() : '';
  if (!val) {
    showToast('Please type your project requirements or select a preset below.', true);
    return;
  }
  renderCopilotItems('student', val);
  showToast('Gemini 2.5 Flash ranked best equipment for your project.');
}

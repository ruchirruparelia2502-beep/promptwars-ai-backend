/**
 * LabLink Platform — API & Utilities Module (api.js)
 * Provides centralized network communications, Bearer JWT session management,
 * accessible screen-reader toast notifications (WCAG 2.1 AA), and XSS escaping.
 */

// Global session token and user role
let currentAuthToken = sessionStorage.getItem('lablink_auth_token') || '';
let currentUserRole = sessionStorage.getItem('lablink_user_role') || 'student';

/**
 * Escapes unsafe HTML characters to prevent XSS injection.
 * @param {string} str Raw untrusted string.
 * @returns {string} Sanitized string safe for DOM insertion.
 */
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * Updates stored auth session state.
 * @param {string} token Bearer JWT token.
 * @param {string} role User role ('student', 'teacher', 'admin').
 */
function setSessionAuth(token, role) {
  currentAuthToken = token || '';
  currentUserRole = role || 'student';
  if (token) {
    sessionStorage.setItem('lablink_auth_token', token);
  } else {
    sessionStorage.removeItem('lablink_auth_token');
  }
  sessionStorage.setItem('lablink_user_role', currentUserRole);
}

/**
 * Centralized API fetch wrapper with Bearer JWT and X-User-Role injection.
 * @param {string} url Endpoint URL.
 * @param {RequestInit} options Fetch options.
 * @returns {Promise<Response>}
 */
async function apiFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  
  if (currentAuthToken) {
    headers.set('Authorization', `Bearer ${currentAuthToken}`);
  }
  if (!headers.has('X-User-Role')) {
    headers.set('X-User-Role', currentUserRole || 'student');
  }

  const mergedOptions = {
    ...options,
    headers
  };

  try {
    return await fetch(url, mergedOptions);
  } catch (err) {
    console.error(`[LabLink API] Network failure on ${url}:`, err);
    throw err;
  }
}

// Toast notification state
let toastTimer = null;

/**
 * Displays an accessible toast notification.
 * Sets role="alert" with an error icon for errors (WCAG 2.1 AA compliant).
 * Sets role="status" with a checkmark for confirmations.
 * @param {string} msg Text to announce and display.
 * @param {boolean} isError Whether this is an error or conflict alert.
 */
function showToast(msg, isError = false) {
  const toast = document.getElementById('toast');
  const toastIcon = document.getElementById('toast-icon');
  const toastMsg = document.getElementById('toast-message');
  if (!toast || !toastMsg) return;

  toastMsg.textContent = msg;

  if (isError) {
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.className = 'fixed top-6 right-6 z-50 flex items-center gap-gutter-sm px-gutter-lg py-gutter-md rounded-full bg-rose-950 text-rose-100 border border-rose-500/60 shadow-2xl font-label text-label-md animate-panel-enter';
    if (toastIcon) {
      toastIcon.textContent = 'error';
      toastIcon.className = 'material-symbols-outlined text-[20px] text-rose-400 shrink-0';
      toastIcon.style.fontVariationSettings = "'FILL' 1";
    }
  } else {
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    toast.className = 'fixed top-6 right-6 z-50 flex items-center gap-gutter-sm px-gutter-lg py-gutter-md rounded-full bg-warm-cream text-on-tertiary border border-tangerine-orange/40 shadow-2xl font-label text-label-md animate-panel-enter';
    if (toastIcon) {
      toastIcon.textContent = 'check_circle';
      toastIcon.className = 'material-symbols-outlined text-[20px] text-tangerine-orange shrink-0';
      toastIcon.style.fontVariationSettings = "'FILL' 1";
    }
  }

  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.classList.add('hidden');
    toast.classList.remove('flex');
  }, 3500);
}

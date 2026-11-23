/**
 * LabLink Platform — Authentication & Role-Based Access Control (auth.js)
 * Implements demo passcode authentication and JWT session token hydration.
 */

// Demo passcodes configured for evaluated hackathon personas
const ROLE_PASSCODES = {
  student: 'student-pass-2025',
  teacher: 'faculty-auth-pass',
  admin: 'lablink-admin-2025'
};

/**
 * Acquires a cryptographic Bearer JWT for the active perspective persona.
 * Authenticates against the server /api/v1/auth/token with the persona passcode.
 * @param {string} povKey Perspective key ('student', 'teacher', 'admin').
 */
async function setPerspectiveAuth(povKey) {
  const passcode = ROLE_PASSCODES[povKey] || 'student-pass-2025';
  
  try {
    const res = await fetch('/api/v1/auth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        role: povKey,
        passcode: passcode
      })
    });

    if (res.ok) {
      const data = await res.json();
      setSessionAuth(data.access_token, povKey);
      console.log(`[LabLink Auth] Authenticated as ${povKey} with verified Bearer JWT.`);
    } else {
      console.warn(`[LabLink Auth] Token issuance returned HTTP ${res.status}. Falling back to role header.`);
      setSessionAuth('', povKey);
    }
  } catch (err) {
    console.warn('[LabLink Auth] Network error fetching JWT token:', err);
    setSessionAuth('', povKey);
  }
}

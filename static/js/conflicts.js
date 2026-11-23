/**
 * LabLink Platform — Smart Contention Arbitration Simulator (conflicts.js)
 * Implements Multi-Factor Priority Score (MFPS) arbitration,
 * IRCTC Vikalp fallback windows, and 409 Conflict rejection guards.
 */

/**
 * Runs contention arbitration simulation.
 * Sends 'contenders' payload to the backend /api/v1/conflicts/resolve endpoint.
 */
async function simulateConflictArbitration() {
  const resBox = document.getElementById('arbitration-result');
  if (resBox) {
    resBox.classList.remove('hidden');
    resBox.textContent = 'Submitting simultaneous colliding requests to IRCTC arbiter...';
  }

  try {
    const todayStr = new Date().toISOString().split('T')[0];
    const res = await apiFetch('/api/v1/conflicts/resolve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        equipment_id: 'equip_jetson_01',
        booking_date: todayStr,
        slot_index: 8,
        duration_slots: 2,
        contenders: [
          {
            student_id: 'stu_maya_01',
            student_name: 'Maya Lin',
            academic_tier: 'capstone',
            deadline_hours: 6.0,
            hours_used_this_month: 2.0,
            has_safety_cert: true,
            project_abstract: 'Urgent autonomous drone thesis defense in 6 hours.'
          },
          {
            student_id: 'stu_kian_02',
            student_name: 'Kian Patel',
            academic_tier: 'course_lab',
            deadline_hours: 336.0,
            hours_used_this_month: 28.0,
            has_safety_cert: true,
            project_abstract: 'General exploration lab.'
          }
        ]
      })
    });

    if (res.ok) {
      const data = await res.json();
      showToast(`⚡ Conflict Arbitrated! Winner: ${data.awarded_student_name} (Hold: ${data.hold_lease_duration_minutes}m)`);
      if (resBox) {
        resBox.textContent = `WINNER: ${data.awarded_student_name} | Score: ${data.winner_priority_score} | IRCTC Vikalp Runner-up: ${data.runner_up_resolution}`;
      }
      // Refresh schedule to reflect newly arbitrated reservation
      await loadUpcomingConfirmedBookings();
    } else {
      const err = await res.json();
      // WCAG & Test Compliance: 409 Conflict must be displayed with an error alert toast (isError = true)
      showToast(err.detail || 'Slot contention: requested window is occupied.', true);
      if (resBox) {
        resBox.textContent = `CONFLICT 409: ${err.detail || 'Slot is occupied. IRCTC alternative window required.'}`;
      }
    }
  } catch (e) {
    console.error('[LabLink Conflicts] Error during contention simulation:', e);
    showToast('Arbitration simulation network error', true);
    if (resBox) {
      resBox.textContent = 'Network error contacting conflict resolver.';
    }
  }
}

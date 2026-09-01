/* DirectCredit Customer Portal - editable profile module. */
(function () {
  const STORE = 'dcCustomerProfiles';
  const fields = [
    ['name', 'Full Name', 'text', 'Enter full name'],
    ['dateOfBirth', 'Date of Birth', 'date', ''],
    ['gender', 'Gender', 'select', ''],
    ['occupation', 'Occupation', 'text', 'e.g. Business Owner'],
    ['businessName', 'Company / Business Name', 'text', 'Enter company or business name'],
    ['monthlyIncome', 'Monthly Income', 'number', 'Enter monthly income'],
    ['address', 'Current Address', 'textarea', 'Enter current residential address'],
    ['permanentAddress', 'Permanent Address', 'textarea', 'Enter permanent address']
  ];

  function read() { try { return JSON.parse(localStorage.getItem(STORE) || '{}'); } catch (_) { return {}; } }
  function write(data) { localStorage.setItem(STORE, JSON.stringify(data)); }
  function current() { return window.currentCustomer || null; }
  function save() {
    const p = current();
    if (!p || !p.customerId) return;
    const all = read();
    all[String(p.customerId)] = p;
    write(all);
    if (typeof window.hydrateCustomerUI === 'function') window.hydrateCustomerUI();
  }
  function esc(v) {
    return String(v == null ? '' : v).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function value(key) {
    const p = current() || {};
    return p[key] == null ? '' : p[key];
  }
  function fieldHtml(f) {
    const [key, label, type, placeholder] = f;
    const v = value(key);
    if (type === 'textarea') return `<label class="profile-edit-field"><span>${label}</span><textarea data-profile-key="${key}" placeholder="${esc(placeholder)}">${esc(v)}</textarea></label>`;
    if (type === 'select') return `<label class="profile-edit-field"><span>${label}</span><select data-profile-key="${key}"><option value="">Select gender</option><option ${v === 'Male' ? 'selected' : ''}>Male</option><option ${v === 'Female' ? 'selected' : ''}>Female</option><option ${v === 'Other' ? 'selected' : ''}>Other</option><option ${v === 'Prefer not to say' ? 'selected' : ''}>Prefer not to say</option></select></label>`;
    return `<label class="profile-edit-field"><span>${label}</span><input data-profile-key="${key}" type="${type}" value="${esc(v)}" placeholder="${esc(placeholder)}" ${type === 'number' ? 'min="0" step="1"' : ''}></label>`;
  }
  function render() {
    const section = document.getElementById('profile');
    const p = current();
    if (!section || !p) return;
    let editor = section.querySelector('.editable-profile-panel');
    if (!editor) {
      editor = document.createElement('div');
      editor.className = 'panel editable-profile-panel';
      const title = section.querySelector('.section-title');
      if (title) title.insertAdjacentElement('afterend', editor); else section.prepend(editor);
    }
    editor.innerHTML = `<div class="profile-edit-head"><div><span class="eyebrow">EDITABLE CUSTOMER PROFILE</span><h3>Personal, Employment & Address Details</h3><p>Enter and update the customer's details. Changes are saved to this customer account on this device.</p></div><span class="profile-save-state" id="profileSaveState">Saved</span></div><div class="profile-edit-grid">${fields.map(fieldHtml).join('')}</div><div class="profile-edit-actions"><button type="button" class="outline" id="profileResetBtn">Reset</button><button type="button" class="primary" id="profileSaveBtn">Save Profile</button></div>`;
    editor.querySelectorAll('[data-profile-key]').forEach(el => el.addEventListener('input', () => {
      const key = el.dataset.profileKey;
      p[key] = key === 'monthlyIncome' ? Number(el.value || 0) : el.value;
      const state = document.getElementById('profileSaveState'); if (state) state.textContent = 'Unsaved changes';
    }));
    editor.querySelectorAll('select[data-profile-key]').forEach(el => el.addEventListener('change', () => {
      p[el.dataset.profileKey] = el.value;
      const state = document.getElementById('profileSaveState'); if (state) state.textContent = 'Unsaved changes';
    }));
    editor.querySelector('#profileSaveBtn').onclick = function () {
      p.name = String(p.name || '').trim() || 'New Customer';
      p.occupation = String(p.occupation || '').trim();
      p.businessName = String(p.businessName || '').trim();
      p.address = String(p.address || '').trim();
      p.permanentAddress = String(p.permanentAddress || '').trim();
      save();
      render();
      if (typeof window.renderStep === 'function' && window.cCurrent === 4) window.renderStep();
      alert('Profile saved successfully.');
    };
    editor.querySelector('#profileResetBtn').onclick = function () { render(); };

    // Make the existing Edit Profile button open/focus the editor.
    const buttons = section.querySelectorAll('.section-title button');
    buttons.forEach(btn => {
      btn.textContent = '✎ Edit Profile';
      btn.onclick = function () { editor.scrollIntoView({ behavior: 'smooth', block: 'start' }); const first = editor.querySelector('input'); if (first) first.focus(); };
    });
  }
  function boot() {
    render();
    let lastId = '';
    setInterval(function () {
      const p = current();
      const id = p && p.customerId ? String(p.customerId) : '';
      if (id !== lastId) { lastId = id; render(); }
    }, 400);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();

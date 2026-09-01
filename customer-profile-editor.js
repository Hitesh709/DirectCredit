/* DirectCredit Customer Portal - editable profile module with persistent API sync. */
(function () {
  const STORE = 'dcCustomerProfiles';
  const API_BASE = (localStorage.getItem('directcredit_api_url') || window.DIRECTCREDIT_API_URL || '/api').replace(/\/$/, '');
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
  function saveLocal() {
    const p = current();
    if (!p || !p.customerId) return;
    const all = read();
    all[String(p.customerId)] = p;
    write(all);
  }
  async function syncToApi() {
    const p = current();
    if (!p) return false;
    const payload = {
      name: String(p.name || 'New Customer').trim() || 'New Customer',
      date_of_birth: p.dateOfBirth || null,
      gender: p.gender || null,
      occupation: p.occupation || '',
      business_name: p.businessName || null,
      monthly_income: Number(p.monthlyIncome || 0),
      address: p.address || null,
      permanent_address: p.permanentAddress || null,
      business_type: p.businessType || null,
      mobile: p.mobile || null,
      email: p.email || null,
      pan: p.pan || null,
      cibil_score: Number(p.cibil || 0),
      foir: Number(p.foir || 0),
      existing_emi: Number(p.existingEmi || 0),
      average_bank_balance: Number(p.averageBalance || 0),
      primary_bank: p.bank || null,
      customer_type: 'Individual'
    };
    try {
      const numericId = /^\d+$/.test(String(p.customerId)) ? Number(p.customerId) : null;
      let response;
      if (numericId) {
        response = await fetch(`${API_BASE}/customers/${numericId}/profile`, {
          method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
        });
      } else {
        response = await fetch(`${API_BASE}/customers`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
        });
        if (response.ok) {
          const created = await response.json();
          if (created && created.id != null) {
            p.serverCustomerId = created.id;
            p.customerId = String(created.id);
          }
        }
      }
      if (!response.ok) throw new Error(`API ${response.status}`);
      if (numericId) {
        const saved = await response.json();
        p.serverCustomerId = saved.id;
      }
      saveLocal();
      return true;
    } catch (e) {
      console.warn('DirectCredit customer profile API sync failed:', e.message);
      saveLocal();
      return false;
    }
  }
  function esc(v) {
    return String(v == null ? '' : v).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\"/g, '&quot;');
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
    editor.innerHTML = `<div class="profile-edit-head"><div><span class="eyebrow">EDITABLE CUSTOMER PROFILE</span><h3>Personal, Employment & Address Details</h3><p>Changes are saved to the DirectCredit database and then shown in the Admin Customer Profile.</p></div><span class="profile-save-state" id="profileSaveState">Saved</span></div><div class="profile-edit-grid">${fields.map(fieldHtml).join('')}</div><div class="profile-edit-actions"><button type="button" class="outline" id="profileResetBtn">Reset</button><button type="button" class="primary" id="profileSaveBtn">Save Profile</button></div>`;
    editor.querySelectorAll('[data-profile-key]').forEach(el => el.addEventListener('input', () => {
      const key = el.dataset.profileKey;
      p[key] = key === 'monthlyIncome' ? Number(el.value || 0) : el.value;
      const state = document.getElementById('profileSaveState'); if (state) state.textContent = 'Unsaved changes';
    }));
    editor.querySelectorAll('select[data-profile-key]').forEach(el => el.addEventListener('change', () => {
      p[el.dataset.profileKey] = el.value;
      const state = document.getElementById('profileSaveState'); if (state) state.textContent = 'Unsaved changes';
    }));
    editor.querySelector('#profileSaveBtn').onclick = async function () {
      p.name = String(p.name || '').trim() || 'New Customer';
      p.occupation = String(p.occupation || '').trim();
      p.businessName = String(p.businessName || '').trim();
      p.address = String(p.address || '').trim();
      p.permanentAddress = String(p.permanentAddress || '').trim();
      const state = document.getElementById('profileSaveState'); if (state) state.textContent = 'Saving…';
      const synced = await syncToApi();
      render();
      if (typeof window.renderStep === 'function' && window.cCurrent === 4) window.renderStep();
      alert(synced ? 'Profile saved successfully and synced to Admin.' : 'Profile saved on this device. Admin sync is currently unavailable.');
    };
    editor.querySelector('#profileResetBtn').onclick = function () { render(); };

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

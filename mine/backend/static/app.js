const HOST = location.origin;
const $ = s => document.querySelector(s);
const $$ = s => document.querySelectorAll(s);

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, ch => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[ch]));
}

function pathPart(value) {
  return encodeURIComponent(value).replace(/[!'()*]/g, ch =>
    `%${ch.charCodeAt(0).toString(16).toUpperCase()}`
  );
}

function toast(msg, type = 'info') {
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

function setServerStatus(ok) {
  $('#serverStatus').textContent = ok ? '后端在线' : '后端未连接';
}

$$('.tabs button').forEach(btn => {
  btn.addEventListener('click', () => {
    $$('.tabs button').forEach(b => b.classList.remove('active'));
    $$('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    $(`#tab-${btn.dataset.tab}`).classList.add('active');
    if (btn.dataset.tab === 'facedb') refreshFaces();
  });
});

function closeModal() {
  $$('.modal-overlay').forEach(m => m.classList.add('hidden'));
  stopCapture('newPerson');
  stopCapture('addImages');
}

let streams = {};

function stopCapture(prefix) {
  if (streams[prefix]) {
    streams[prefix].getTracks().forEach(t => t.stop());
    delete streams[prefix];
  }
  const video = $(`#${prefix}Video`);
  const canvas = $(`#${prefix}Canvas`);
  if (video) {
    video.pause();
    video.srcObject = null;
    video.style.display = 'none';
  }
  if (canvas) canvas.style.display = 'none';
}

async function startCapture(prefix) {
  const video = $(`#${prefix}Video`);
  const canvas = $(`#${prefix}Canvas`);
  try {
    stopCapture(prefix);
    const s = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
    streams[prefix] = s;
    video.srcObject = s;
    video.style.display = 'block';
    canvas.style.display = 'none';
  } catch {
    toast('无法打开摄像头，请检查浏览器权限。', 'error');
  }
}

function capturePhoto(prefix) {
  const video = $(`#${prefix}Video`);
  const canvas = $(`#${prefix}Canvas`);
  const preview = $(`#${prefix}Preview`);
  if (!streams[prefix]) {
    toast('请先打开摄像头。', 'error');
    return;
  }
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  canvas.getContext('2d').drawImage(video, 0, 0);
  preview.innerHTML = `<img src="${canvas.toDataURL('image/jpeg', 0.9)}" alt="拍照预览">`;
  canvas.style.display = 'block';
}

function getCapturedBlob(prefix) {
  const canvas = $(`#${prefix}Canvas`);
  if (!canvas || canvas.style.display === 'none') return null;
  return new Promise(resolve => canvas.toBlob(b => resolve(b), 'image/jpeg', 0.9));
}

let currentPerson = null;

async function refreshFaces() {
  const list = $('#facedb-list');
  const detail = $('#facedb-detail');
  detail.classList.add('hidden');
  list.classList.remove('hidden');
  $('#facedb-title').textContent = '所有人员';
  try {
    const resp = await fetch(`${HOST}/api/persons`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const persons = await resp.json();
    if (!persons.length) {
      list.innerHTML = '<div class="empty"><strong>人脸库为空</strong><span>新增人员并上传照片后，点击重新注册即可生效。</span></div>';
      return;
    }
    list.innerHTML = `<div class="person-grid">${persons.map(p => {
      const name = escapeHtml(p.name);
      const encodedName = pathPart(p.name);
      const src = p.images.length ? `${HOST}/api/images/${encodedName}/${pathPart(p.images[0])}` : '';
      const thumb = src
        ? `<img class="thumb" src="${src}" alt="${name}" onerror="this.replaceWith(createFallbackThumb())">`
        : `<div class="thumb">${name[0] || '?'}</div>`;
      return `<article class="person-card" onclick="showPerson('${encodedName}')">
        ${thumb}
        <div class="info">
          <div class="pname" title="${name}">${name}</div>
          <div class="pcount">${p.image_count} 张</div>
        </div>
      </article>`;
    }).join('')}</div>`;
  } catch {
    list.innerHTML = '<div class="empty"><strong>连接失败</strong><span>请确认后端服务正在运行。</span></div>';
  }
}

function createFallbackThumb() {
  const d = document.createElement('div');
  d.className = 'thumb';
  d.textContent = '?';
  return d;
}

async function showPerson(encodedName) {
  const name = decodeURIComponent(encodedName);
  currentPerson = name;
  const list = $('#facedb-list');
  const detail = $('#facedb-detail');
  list.classList.add('hidden');
  detail.classList.remove('hidden');
  $('#facedb-title').textContent = name;
  try {
    const resp = await fetch(`${HOST}/api/persons/${encodedName}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const p = await resp.json();
    const safeName = escapeHtml(p.name);
    detail.innerHTML = `
      <div class="detail-header">
        <div class="detail-left">
          <button class="btn btn-outline btn-sm" onclick="backToFaces()">返回</button>
          <h2>${safeName}</h2>
          <span class="status-pill">${p.image_count} 张照片</span>
        </div>
        <div class="actions">
          <button class="btn btn-outline btn-sm" onclick="renamePerson('${encodedName}')">重命名</button>
          <button class="btn btn-primary btn-sm" onclick="showAddImagesModal('${encodedName}')">添加照片</button>
          <button class="btn btn-success btn-sm" onclick="rebuildDB()">重新注册</button>
          <button class="btn btn-danger btn-sm" onclick="deletePerson('${encodedName}')">删除人员</button>
        </div>
      </div>
      <div class="upload-area" onclick="document.getElementById('detailFileInput').click()">
        点击或拖拽图片到这里上传
        <input type="file" id="detailFileInput" accept="image/*" multiple style="display:none" onchange="uploadDetailFiles('${encodedName}', this)">
      </div>
      ${p.images.length ? `<div class="image-grid">${p.images.map(f => {
        const safeFile = escapeHtml(f);
        const encodedFile = encodeURIComponent(f);
        return `<article class="image-card">
          <img src="${HOST}/api/images/${encodedName}/${encodedFile}" alt="${safeFile}">
          <div class="image-name">${safeFile}</div>
          <button class="image-del" title="删除照片" onclick="deleteImage('${encodedName}','${encodedFile}')">×</button>
        </article>`;
      }).join('')}</div>` : '<div class="empty"><strong>暂无照片</strong><span>上传照片后重新注册，识别库才会更新。</span></div>'}
    `;
  } catch {
    toast('人员详情加载失败。', 'error');
  }
}

function backToFaces() {
  currentPerson = null;
  refreshFaces();
}

document.addEventListener('dragover', e => {
  e.preventDefault();
  const area = document.querySelector('.upload-area');
  if (area && currentPerson) area.classList.add('dragover');
});

document.addEventListener('dragleave', e => {
  if (!e.relatedTarget) $$('.upload-area').forEach(el => el.classList.remove('dragover'));
});

document.addEventListener('drop', async e => {
  e.preventDefault();
  $$('.upload-area').forEach(el => el.classList.remove('dragover'));
  if (!currentPerson) return;
  const files = e.dataTransfer.files;
  if (!files.length) return;
    await uploadFiles(currentPerson, files, () => showPerson(pathPart(currentPerson)));
});

async function uploadFiles(personName, files, cb) {
  const fd = new FormData();
  let count = 0;
  for (const f of files) {
    if (f.type.startsWith('image/')) {
      fd.append('files', f);
      count++;
    }
  }
  if (!count) {
    toast('没有可上传的图片文件。', 'error');
    return;
  }
  try {
    const resp = await fetch(`${HOST}/api/persons/${pathPart(personName)}/images`, { method: 'POST', body: fd });
    const r = await resp.json();
    if (!resp.ok) throw new Error(r.error || 'upload failed');
    toast(`已保存 ${r.images_saved} 张照片，请重新注册。`, 'success');
    if (cb) cb();
    else showPerson(pathPart(personName));
  } catch {
    toast('上传失败。', 'error');
  }
}

async function renamePerson(encodedName) {
  const oldName = decodeURIComponent(encodedName);
  const newName = prompt(`将「${oldName}」重命名为：`, oldName);
  if (!newName || newName === oldName) return;
  if (!/^[^\\/:*?"<>|]+$/.test(newName)) {
    toast('姓名包含非法字符。', 'error');
    return;
  }
  const fd = new FormData();
  fd.append('new_name', newName);
  try {
    const resp = await fetch(`${HOST}/api/persons/${encodedName}/rename`, { method: 'PUT', body: fd });
    const r = await resp.json();
    if (resp.ok) {
      toast(r.message || '重命名成功，请重新注册。', 'success');
      refreshFaces();
    } else {
      toast(r.error || '重命名失败。', 'error');
    }
  } catch {
    toast('请求失败。', 'error');
  }
}

async function uploadDetailFiles(encodedName, input) {
  const files = input.files;
  if (!files.length) return;
  await uploadFiles(decodeURIComponent(encodedName), files);
  input.value = '';
}

async function deleteImage(encodedName, encodedFile) {
  if (!confirm('确定删除这张照片吗？')) return;
  try {
    const resp = await fetch(`${HOST}/api/persons/${encodedName}/images/${encodedFile}`, { method: 'DELETE' });
    if (!resp.ok) throw new Error('delete failed');
    toast('照片已删除，请重新注册。', 'success');
    showPerson(encodedName);
  } catch {
    toast('删除失败。', 'error');
  }
}

async function deletePerson(encodedName) {
  const name = decodeURIComponent(encodedName);
  if (!confirm(`确定删除「${name}」及其所有照片吗？`)) return;
  if (!confirm('此操作不可恢复，请再次确认。')) return;
  try {
    const resp = await fetch(`${HOST}/api/persons/${encodedName}`, { method: 'DELETE' });
    if (!resp.ok) throw new Error('delete failed');
    toast('人员已删除。', 'success');
    backToFaces();
  } catch {
    toast('删除失败。', 'error');
  }
}

async function rebuildDB() {
  if (!confirm('确认重新注册人脸库吗？')) return;
  const btn = $('#rebuildBtn');
  const oldText = btn.textContent;
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>注册中';
  try {
    const resp = await fetch(`${HOST}/api/register`, { method: 'POST' });
    const r = await resp.json();
    if (r.ok) toast(`注册成功：${r.message || 'ok'}`, 'success');
    else toast(`注册失败：${r.stderr || r.error || ''}`, 'error');
  } catch {
    toast('注册请求失败。', 'error');
  }
  btn.disabled = false;
  btn.textContent = oldText;
}

function showNewPersonModal() {
  $('#newPersonName').value = '';
  $('#newPersonPreview').innerHTML = '';
  $('#newPersonFiles').value = '';
  stopCapture('newPerson');
  $('#newPersonModal').classList.remove('hidden');
}

async function saveNewPerson() {
  const name = $('#newPersonName').value.trim();
  if (!name) {
    toast('请输入姓名。', 'error');
    return;
  }
  if (!/^[^\\/:*?"<>|]+$/.test(name)) {
    toast('姓名包含非法字符。', 'error');
    return;
  }
  const fd = new FormData();
  fd.append('name', name);
  const blob = await getCapturedBlob('newPerson');
  if (blob) fd.append('files', blob, 'capture.jpg');
  for (const f of $('#newPersonFiles').files) fd.append('files', f);

  const btn = $('#savePersonBtn');
  btn.disabled = true;
  btn.textContent = '保存中';
  try {
    const resp = await fetch(`${HOST}/api/persons`, { method: 'POST', body: fd });
    const r = await resp.json().catch(() => ({}));
    if (resp.status === 409) {
      toast('该姓名已存在。', 'error');
    } else if (!resp.ok) {
      toast(r.error || '保存失败。', 'error');
    } else {
      toast(`已添加「${name}」，请重新注册。`, 'success');
      closeModal();
      refreshFaces();
    }
  } catch {
    toast('请求失败。', 'error');
  }
  btn.disabled = false;
  btn.textContent = '保存';
}

function showAddImagesModal(encodedName) {
  $('#addImagesTitle').textContent = `为「${decodeURIComponent(encodedName)}」添加照片`;
  $('#addImagesPreview').innerHTML = '';
  $('#addImagesFiles').value = '';
  stopCapture('addImages');
  $('#addImagesModal').dataset.person = encodedName;
  $('#addImagesModal').classList.remove('hidden');
}

async function saveImages() {
  const encodedName = $('#addImagesModal').dataset.person;
  const fd = new FormData();
  const blob = await getCapturedBlob('addImages');
  if (blob) fd.append('files', blob, 'capture.jpg');
  for (const f of $('#addImagesFiles').files) fd.append('files', f);

  const btn = $('#saveImagesBtn');
  btn.disabled = true;
  btn.textContent = '保存中';
  try {
    const resp = await fetch(`${HOST}/api/persons/${encodedName}/images`, { method: 'POST', body: fd });
    const r = await resp.json();
    if (!resp.ok) throw new Error(r.error || 'save failed');
    toast(`已保存 ${r.images_saved} 张照片，请重新注册。`, 'success');
    closeModal();
    showPerson(encodedName);
  } catch {
    toast('上传失败。', 'error');
  }
  btn.disabled = false;
  btn.textContent = '保存';
}

let recData = [];
let recFiltered = [];

function scoreColor(s) {
  if (s >= 0.4) return '#62e6a8';
  if (s >= 0.3) return '#f2c94c';
  return '#ff8f8f';
}

function statusText(status) {
  return status === 'recognized' ? '已识别' : '未识别';
}

function populateCameras(rows) {
  const sel = $('#filterCamera');
  const cur = sel.value;
  const ids = [...new Set(rows.map(r => r.camera_id))].sort((a, b) => a - b);
  sel.innerHTML = '<option value="">全部摄像头</option>' + ids.map(i => `<option value="${i}">摄像头 #${i}</option>`).join('');
  if (cur) sel.value = cur;
}

function applyFilters() {
  const q = $('#searchName').value.trim().toLowerCase();
  const st = $('#filterStatus').value;
  const cam = $('#filterCamera').value;
  recFiltered = recData.filter(r => {
    if (q && !String(r.name).toLowerCase().includes(q)) return false;
    if (st && r.status !== st) return false;
    if (cam && r.camera_id !== Number(cam)) return false;
    return true;
  });
  renderStats(recFiltered);
  renderLatest(recFiltered);
  renderTable(recFiltered);
}

function renderStats(rows) {
  const total = rows.length;
  const known = rows.filter(r => r.status === 'recognized').length;
  const unique = new Set(rows.filter(r => r.status === 'recognized').map(r => r.name)).size;
  updateCount(rows);
  $('#stats').innerHTML = `
    <article class="stat-card"><div class="value">${total}</div><div class="label">筛选记录</div></article>
    <article class="stat-card"><div class="value">${unique}</div><div class="label">识别人员</div></article>
    <article class="stat-card"><div class="value">${known}</div><div class="label">已识别</div></article>
    <article class="stat-card"><div class="value">${total - known}</div><div class="label">未识别</div></article>`;
}

function renderLatest(rows) {
  if (!rows.length) {
    $('#latest').style.display = 'none';
    return;
  }
  $('#latest').style.display = 'grid';
  const r = rows[0];
  const known = r.status === 'recognized';
  const name = escapeHtml(r.name);
  $('#latest').innerHTML = `
    <div>
      <div class="latest-title">
        <h2>最近一次识别</h2>
        <div class="time">${escapeHtml(r.created_at || '')}</div>
      </div>
      <div class="person-row">
        <div class="avatar ${known ? '' : 'unknown'}">${known ? escapeHtml(name[0] || '?') : '?'}</div>
        <div>
          <div class="name-line">${name}<span class="tag ${known ? 'recognized' : 'unknown'}">${statusText(r.status)}</span></div>
          <div class="detail-line">置信度 ${Number(r.score).toFixed(3)} · 摄像头 #${r.camera_id} · ${escapeHtml(r.timestamp || '')}</div>
        </div>
      </div>
    </div>`;
}

function updateCount(rows) {
  $('#countLabel').textContent = `${rows.length} / ${recData.length} 条记录`;
}

function renderTable(rows) {
  const tbody = $('#records');
  const empty = $('#empty');
  if (!rows.length) {
    tbody.innerHTML = '';
    empty.style.display = 'block';
    return;
  }
  empty.style.display = 'none';
  tbody.innerHTML = rows.map(r => {
    const known = r.status === 'recognized';
    const score = Number(r.score || 0);
    const safeName = escapeHtml(r.name);
    return `<tr>
      <td style="color:var(--faint)">${r.id}</td>
      <td><span class="record-name ${known ? '' : 'unknown'}" title="${safeName}"><span class="record-name-text">${safeName}</span></span></td>
      <td><div class="score-bar"><span class="score-value">${score.toFixed(3)}</span><div class="bar"><div class="fill" style="width:${Math.min(Math.max(score, 0) * 100, 100)}%;background:${scoreColor(score)}"></div></div></div></td>
      <td><span class="tag ${known ? 'recognized' : 'unknown'}">${statusText(r.status)}</span></td>
      <td style="color:var(--muted)">摄像头 #${r.camera_id}</td>
      <td style="color:var(--muted);font-size:13px">${escapeHtml(r.timestamp || '')}</td>
    </tr>`;
  }).join('');
}

async function fetchRecords() {
  try {
    const resp = await fetch(`${HOST}/api/recognitions?limit=100`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    recData = await resp.json();
    setServerStatus(true);
    $('#connecting').style.display = 'none';
    populateCameras(recData);
    applyFilters();
  } catch {
    setServerStatus(false);
    $('#connecting').style.display = 'block';
    $('#records').innerHTML = '';
    $('#empty').style.display = 'none';
    $('#stats').innerHTML = '';
    $('#latest').style.display = 'none';
  }
}

fetchRecords();
setInterval(fetchRecords, 3000);
refreshFaces();

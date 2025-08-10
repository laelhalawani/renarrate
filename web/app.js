const jobListEl = document.getElementById('job-list');
const filtersEl = document.querySelector('.filters');
const videoEl = document.getElementById('video');
const playBtn = document.getElementById('playpause');
const fsBtn = document.getElementById('fullscreen');
const timelineEl = document.getElementById('timeline');
const progressEl = document.getElementById('progress');
const timeEl = document.getElementById('time');
const emptyStateEl = document.getElementById('empty-state');

const m = {
  title: document.getElementById('m-title'),
  uploader: document.getElementById('m-uploader'),
  duration: document.getElementById('m-duration'),
  uploadDate: document.getElementById('m-upload-date'),
  views: document.getElementById('m-views'),
  likes: document.getElementById('m-likes'),
  comments: document.getElementById('m-comments'),
  url: document.getElementById('m-url'),
  requestId: document.getElementById('m-request-id'),
  jobId: document.getElementById('m-job-id'),
};

/* ---------- New Job Modal elements (unchanged) ---------- */
const newBtn = document.getElementById('new-btn');
const modal = document.getElementById('new-modal');
const backdrop = document.getElementById('modal-backdrop');
const modalClose = document.getElementById('modal-close');
const modalCancel = document.getElementById('modal-cancel');
const form = document.getElementById('new-form');
const fUrl = document.getElementById('f-url');
const fLang = document.getElementById('f-language');
const fProvider = document.getElementById('f-provider');
const fVoice = document.getElementById('f-voice');
const formErr = document.getElementById('form-error');
const toastEl = document.getElementById('toast');

let jobs = [];
let activeJobId = null;
let currentFilter = '';

/* ---------- Jobs fetching & rendering ---------- */

async function fetchJobs(statusFilter = '') {
  currentFilter = statusFilter;
  const url = statusFilter ? `/jobs?status=${encodeURIComponent(statusFilter)}` : '/jobs';
  const res = await fetch(url);
  const data = await res.json();
  jobs = data.jobs || [];
  renderJobList();
}

function renderJobList() {
  jobListEl.innerHTML = '';
  if (!jobs.length) {
    const li = document.createElement('li');
    li.textContent = 'No jobs yet. Click “New” to create one.';
    jobListEl.appendChild(li);
    return;
  }
  for (const j of jobs) {
    const li = document.createElement('li');
    li.dataset.id = j.job_id;

    const title = document.createElement('div');
    title.className = 'job-title';
    title.textContent = j.title || '(no title yet)';

    const right = document.createElement('div');
    const badge = document.createElement('span');
    badge.className = 'badge ' + badgeClass(j.status);
    badge.textContent = j.status;
    right.appendChild(badge);

    li.appendChild(title);
    li.appendChild(right);
    li.addEventListener('click', () => selectJob(j.job_id));
    if (j.job_id === activeJobId) li.classList.add('active');

    jobListEl.appendChild(li);
  }
}

function badgeClass(s) {
  switch (s) {
    case 'SUCCESS': return 'success';
    case 'FAILED': return 'failed';
    case 'PENDING': return 'pending';
    case 'RUNNING': return 'running';
    default: return '';
  }
}

async function selectJob(jobId) {
  activeJobId = jobId;
  [...jobListEl.children].forEach(li => {
    li.classList.toggle('active', li.dataset.id === jobId);
  });

  // Fetch info for metadata
  const infoRes = await fetch(`/video_info/${encodeURIComponent(jobId)}`);
  if (!infoRes.ok) {
    // Maybe not ready yet
    clearMeta();
    emptyStateEl.hidden = false;
    videoEl.removeAttribute('src');
    videoEl.load();
    return;
  }
  const info = await infoRes.json();
  const v = info.video_info || {};

  // Set video src
  videoEl.src = `/video/${encodeURIComponent(jobId)}`;
  videoEl.load();
  emptyStateEl.hidden = true;

  // Fill metadata
  setMeta({
    title: v.title || '—',
    uploader: v.uploader || '—',
    duration: (v.duration != null) ? formatSeconds(v.duration) : '—',
    uploadDate: v.upload_date || '—',
    views: formatInt(v.view_count),
    likes: formatInt(v.like_count),
    comments: formatInt(v.comment_count),
    url: v.webpage_url || '—',
    requestId: findJob(jobId)?.request_id || '—',
    jobId: jobId,
  });
}

function findJob(jobId) {
  return jobs.find(j => j.job_id === jobId);
}

function clearMeta() {
  setMeta({
    title: '—', uploader: '—', duration: '—', uploadDate: '—',
    views: '—', likes: '—', comments: '—', url: '—',
    requestId: '—', jobId: '—',
  });
}
function setMeta(data) {
  m.title.textContent = data.title;
  m.uploader.textContent = data.uploader;
  m.duration.textContent = data.duration;
  m.uploadDate.textContent = data.uploadDate;
  m.views.textContent = data.views;
  m.likes.textContent = data.likes;
  m.comments.textContent = data.comments;
  m.url.textContent = data.url;
  m.requestId.textContent = data.requestId;
  m.jobId.textContent = data.jobId;
}

function formatInt(n) {
  if (n == null) return '—';
  try { return Number(n).toLocaleString(); } catch { return String(n); }
}
function formatSeconds(total) {
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = Math.floor(total % 60);
  return h > 0 ? `${h}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
               : `${m}:${String(s).padStart(2,'0')}`;
}

/* ---------- Player controls ---------- */

function togglePlay() {
  if (videoEl.paused) {
    videoEl.play();
  } else {
    videoEl.pause();
  }
}
function updatePlayButton() {
  playBtn.textContent = videoEl.paused ? '▶' : '⏸';
}

function seekFromClientX(clientX) {
  const rect = timelineEl.getBoundingClientRect();
  const pct = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
  if (isFinite(videoEl.duration)) {
    videoEl.currentTime = pct * videoEl.duration;
  }
}

function updateTimeAndProgress() {
  const cur = isFinite(videoEl.currentTime) ? videoEl.currentTime : 0;
  const dur = isFinite(videoEl.duration) ? videoEl.duration : 0;
  timeEl.textContent = `${formatSeconds(cur)} / ${formatSeconds(dur)}`;
  const pct = dur > 0 ? (cur / dur) * 100 : 0;
  progressEl.style.width = `${pct}%`;
}

function toggleFullscreen() {
  const root = document.getElementById('player-shell');
  if (!document.fullscreenElement) {
    root.requestFullscreen?.();
  } else {
    document.exitFullscreen?.();
  }
}

playBtn.addEventListener('click', togglePlay);
videoEl.addEventListener('play', updatePlayButton);
videoEl.addEventListener('pause', updatePlayButton);
videoEl.addEventListener('timeupdate', updateTimeAndProgress);
videoEl.addEventListener('loadedmetadata', updateTimeAndProgress);
fsBtn.addEventListener('click', toggleFullscreen);

timelineEl.addEventListener('click', (e) => seekFromClientX(e.clientX));
let dragging = false;
timelineEl.addEventListener('mousedown', (e) => { dragging = true; seekFromClientX(e.clientX); });
window.addEventListener('mousemove', (e) => { if (dragging) seekFromClientX(e.clientX); });
window.addEventListener('mouseup', () => { dragging = false; });

/* ---------- Filters ---------- */
filtersEl.addEventListener('click', (e) => {
  if (e.target.tagName === 'BUTTON') {
    const f = e.target.getAttribute('data-filter') || '';
    fetchJobs(f);
  }
});

/* ---------- New modal logic (unchanged) ---------- */
newBtn.addEventListener('click', openModal);
modalClose.addEventListener('click', closeModal);
modalCancel.addEventListener('click', closeModal);
backdrop.addEventListener('click', closeModal);
window.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });

function openModal() {
  form.reset();
  formErr.textContent = '';
  fProvider.value = 'elevenlabs';
  fVoice.value = '';
  show(modal);
  show(backdrop);
  fUrl.focus();
}
function closeModal() {
  hide(modal);
  hide(backdrop);
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  formErr.textContent = '';

  const yt_video_url = fUrl.value.trim();
  const target_language = fLang.value.trim();
  const tts_provider = fProvider.value;
  const voice_name = fVoice.value.trim();

  if (!yt_video_url || !target_language) {
    formErr.textContent = 'Please provide a valid YouTube URL and target language.';
    return;
  }

  try {
    const res = await fetch('/renarrate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        yt_video_url,
        target_language,
        tts_provider,
        voice_name: voice_name || null,
      }),
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`Server responded ${res.status}: ${txt}`);
    }
    const data = await res.json();
    closeModal();
    toast(`Job queued: ${data.job_id.slice(0,8)}…`);
    await fetchJobs(currentFilter);
    await selectJob(data.job_id);
  } catch (err) {
    formErr.textContent = String(err.message || err);
  }
});

/* ---------- Toast ---------- */
let toastTimer = null;
function toast(msg) {
  toastEl.textContent = msg;
  show(toastEl);
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => hide(toastEl), 2800);
}

/* ---------- Helpers ---------- */
function show(el) { el.classList.remove('hidden'); el.setAttribute('aria-hidden','false'); }
function hide(el) { el.classList.add('hidden'); el.setAttribute('aria-hidden','true'); }

/* ---------- Light polling to keep titles fresh ---------- */
setInterval(() => {
  fetchJobs(currentFilter);
}, 8000);

/* ---------- Initial load ---------- */
fetchJobs().then(() => {
  const s = jobs.filter(j => j.status === 'SUCCESS');
  if (s.length) selectJob(s[s.length - 1].job_id);
});

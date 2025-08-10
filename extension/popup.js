// Small helpers
const $ = (sel) => document.querySelector(sel);
const show = (el) => el.classList.remove('hidden');
const hide = (el) => el.classList.add('hidden');

const DEFAULT_BASE = 'http://localhost:8000';

const els = {
  setupCard: $('#setup'),
  apiBaseUrl: $('#apiBaseUrl'),
  saveBaseUrl: $('#saveBaseUrl'),
  setupMsg: $('#setupMsg'),

  formCard: $('#formCard'),
  ytUrl: $('#ytUrl'),
  targetLang: $('#targetLang'),
  provider: $('#provider'),
  voice: $('#voice'),
  submitBtn: $('#submitBtn'),
  status: $('#status'),

  openUi: $('#openUi'),
};

// Load config from storage
async function getConfig() {
  return new Promise((resolve) => {
    chrome.storage.sync.get({ apiBaseUrl: DEFAULT_BASE }, (data) => resolve(data));
  });
}
async function setConfig(patch) {
  return new Promise((resolve) => {
    chrome.storage.sync.set(patch, () => resolve(true));
  });
}

// Get current tab URL (needs "tabs" permission)
async function getActiveTabUrl() {
  return new Promise((resolve) => {
    try {
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (chrome.runtime.lastError) {
          resolve(null);
          return;
        }
        const t = tabs && tabs[0];
        resolve(t ? t.url : null);
      });
    } catch {
      resolve(null);
    }
  });
}

// Heuristics: is YouTube watch page?
function isYouTubeWatch(url) {
  try {
    const u = new URL(url);
    return /(^|\.)youtube\.com$/.test(u.hostname) && u.pathname === '/watch' && u.searchParams.has('v');
  } catch {
    return false;
  }
}

// Simple locale → language string
function detectLanguage() {
  // navigator.language e.g. "en-US" or "pl-PL"
  const loc = (navigator.language || '').trim();
  return loc || 'en-US';
}

// Boot
document.addEventListener('DOMContentLoaded', async () => {
  const cfg = await getConfig();

  // First-time experience: if user has never explicitly saved, still show setup but pre-fill default.
  // We’ll consider it "not set" if the exact key doesn't exist — detect via storage.get with no default:
  chrome.storage.sync.get(null, (raw) => {
    const hasExplicit = Object.prototype.hasOwnProperty.call(raw, 'apiBaseUrl');
    els.apiBaseUrl.value = hasExplicit ? cfg.apiBaseUrl : DEFAULT_BASE;
    if (!hasExplicit) {
      show(els.setupCard);
    } else {
      hide(els.setupCard);
    }
  });

  // Prefill the form
  const tabUrl = await getActiveTabUrl();
  if (tabUrl && isYouTubeWatch(tabUrl)) {
    els.ytUrl.value = tabUrl;
  }
  els.targetLang.value = detectLanguage();
  els.provider.value = 'elevenlabs';
  els.voice.value = '';

  // “See VO’ed videos” opens the Web UI
  els.openUi.addEventListener('click', async () => {
    const { apiBaseUrl } = await getConfig();
    const url = apiBaseUrl.replace(/\/+$/, ''); // trim trailing slash
    chrome.tabs.create({ url });
  });

  // Save base URL
  els.saveBaseUrl.addEventListener('click', async () => {
    const url = (els.apiBaseUrl.value || '').trim() || DEFAULT_BASE;
    await setConfig({ apiBaseUrl: url });
    els.setupMsg.textContent = `Saved: ${url}`;
    setTimeout(() => {
      els.setupMsg.textContent = '';
      hide(els.setupCard);
    }, 700);
  });

  // Submit job
  els.submitBtn.addEventListener('click', async () => {
    const { apiBaseUrl } = await getConfig();
    const base = (apiBaseUrl || DEFAULT_BASE).replace(/\/+$/, '');

    const yt_video_url = (els.ytUrl.value || '').trim();
    const target_language = (els.targetLang.value || '').trim();
    const tts_provider = els.provider.value;
    const voice_name = (els.voice.value || '').trim();

    if (!yt_video_url || !target_language) {
      els.status.textContent = 'Please fill YouTube URL and target language.';
      return;
    }

    els.status.textContent = 'Submitting…';
    try {
      const res = await fetch(`${base}/renarrate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          yt_video_url,
          target_language,
          tts_provider,
          voice_name: voice_name || null
        }),
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`HTTP ${res.status}: ${txt}`);
      }
      const data = await res.json();
      els.status.textContent = `Queued: ${data.job_id.slice(0,8)}…`;
    } catch (err) {
      els.status.textContent = `Error: ${err.message || err}`;
    }
  });
});

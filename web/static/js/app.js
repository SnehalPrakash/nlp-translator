// Offline Multilingual Translator - Client Application

let currentTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', currentTheme);

let typingTimer = null;
const TYPING_DELAY = 600; // ms

// DOM Elements
const srcSelect = document.getElementById('srcLang');
const tgtSelect = document.getElementById('tgtLang');
const swapBtn = document.getElementById('swapBtn');
const srcInput = document.getElementById('srcInput');
const tgtOutput = document.getElementById('tgtOutput');
const charCount = document.getElementById('charCount');
const clearBtn = document.getElementById('clearBtn');
const copyBtn = document.getElementById('copyBtn');
const themeToggleBtn = document.getElementById('themeToggleBtn');
const historyToggleBtn = document.getElementById('historyToggleBtn');
const historyDrawer = document.getElementById('historyDrawer');
const closeDrawerBtn = document.getElementById('closeDrawerBtn');
const clearHistoryBtn = document.getElementById('clearHistoryBtn');
const historyList = document.getElementById('historyList');
const statusBar = document.getElementById('statusBar');
const warningBanner = document.getElementById('warningBanner');
const dictCard = document.getElementById('dictCard');
const toast = document.getElementById('toast');

// Initialize Languages
async function loadLanguages() {
  try {
    const res = await fetch('/api/languages');
    const data = await res.json();
    const langs = data.languages;

    // Source languages with Auto-Detect option
    srcSelect.innerHTML = '<option value="auto">🌐 Auto-Detect</option>';
    langs.forEach(l => {
      srcSelect.innerHTML += `<option value="${l.code}">${l.name}</option>`;
    });

    // Target languages
    tgtSelect.innerHTML = '';
    langs.forEach(l => {
      const selected = l.code === 'kn' ? 'selected' : '';
      tgtSelect.innerHTML += `<option value="${l.code}" ${selected}>${l.name}</option>`;
    });
  } catch (err) {
    console.error('Failed to load language list:', err);
  }
}

// Robust Clipboard Copy Fallback (Required for LAN HTTP on mobile)
function copyToClipboard(text) {
  if (!text) return;
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(() => showToast('Copied to clipboard!'));
  } else {
    // Fallback using textarea for plain HTTP over LAN
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      document.execCommand('copy');
      showToast('Copied to clipboard!');
    } catch (err) {
      showToast('Failed to copy');
    }
    document.body.removeChild(textArea);
  }
}

function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2000);
}

// Perform Translation
async function performTranslation() {
  const text = srcInput.value.trim();
  if (!text) {
    tgtOutput.textContent = 'Translation will appear here...';
    tgtOutput.classList.add('placeholder');
    statusBar.textContent = 'Offline Engine Ready.';
    warningBanner.style.display = 'none';
    dictCard.style.display = 'none';
    return;
  }

  tgtOutput.classList.remove('placeholder');
  statusBar.textContent = 'Translating...';

  try {
    const res = await fetch('/api/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: text,
        source_lang: srcSelect.value,
        target_lang: tgtSelect.value,
        use_cache: true,
        save_history: true
      })
    });

    if (!res.ok) throw new Error('Translation request failed');

    const data = await res.json();
    tgtOutput.textContent = data.translated_text;

    // Status Bar & Metrics
    const cachedBadge = data.cached ? '⚡ Cached (0.5ms)' : '⚙️ CTranslate2 INT8';
    statusBar.innerHTML = `<span>⏱️ ${data.latency_ms} ms (${cachedBadge})</span> <span>Detected: ${data.source_lang.toUpperCase()}</span>`;

    // Warning Banner
    if (data.warning) {
      warningBanner.textContent = `⚠️ ${data.warning}`;
      warningBanner.style.display = 'flex';
    } else {
      warningBanner.style.display = 'none';
    }

    // Dictionary Card
    if (data.dictionary_entry) {
      renderDictionaryCard(data.dictionary_entry);
    } else {
      dictCard.style.display = 'none';
    }

    // Refresh history panel in background
    loadHistory();
  } catch (err) {
    console.error(err);
    statusBar.textContent = 'Translation error occurred.';
  }
}

function renderDictionaryCard(entry) {
  dictCard.style.display = 'block';
  document.getElementById('dictWord').textContent = entry.word.toUpperCase();
  document.getElementById('dictPos').textContent = entry.pos || '';
  document.getElementById('dictDef').textContent = entry.definition || '';

  const synContainer = document.getElementById('dictSynonyms');
  synContainer.innerHTML = '';
  if (entry.synonyms && entry.synonyms.length > 0) {
    entry.synonyms.forEach(s => {
      synContainer.innerHTML += `<span>${s}</span>`;
    });
  } else {
    synContainer.textContent = 'None';
  }

  const antContainer = document.getElementById('dictAntonyms');
  antContainer.innerHTML = '';
  if (entry.antonyms && entry.antonyms.length > 0) {
    entry.antonyms.forEach(a => {
      antContainer.innerHTML += `<span>${a}</span>`;
    });
  } else {
    antContainer.textContent = 'None';
  }
}

// History Management
async function loadHistory() {
  try {
    const res = await fetch('/api/history?limit=25');
    const data = await res.json();
    historyList.innerHTML = '';

    if (!data.history || data.history.length === 0) {
      historyList.innerHTML = '<div style="color: var(--text-secondary); text-align: center; margin-top: 2rem;">No recent translations</div>';
      return;
    }

    data.history.forEach(item => {
      const el = document.createElement('div');
      el.className = 'history-item';
      const timeStr = new Date(item.created_at * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      el.innerHTML = `
        <div class="hist-meta">
          <span>${item.src_lang.toUpperCase()} → ${item.tgt_lang.toUpperCase()}</span>
          <span>${timeStr}</span>
        </div>
        <div class="hist-src">${item.source_text}</div>
        <div class="hist-tgt">${item.translated_text}</div>
      `;
      el.onclick = () => {
        srcInput.value = item.source_text;
        tgtOutput.textContent = item.translated_text;
        tgtOutput.classList.remove('placeholder');
        srcSelect.value = item.src_lang;
        tgtSelect.value = item.tgt_lang;
        historyDrawer.classList.remove('open');
      };
      historyList.appendChild(el);
    });
  } catch (err) {
    console.error('Failed to load history:', err);
  }
}

// Event Listeners
srcInput.addEventListener('input', () => {
  charCount.textContent = srcInput.value.length;
  clearTimeout(typingTimer);
  typingTimer = setTimeout(performTranslation, TYPING_DELAY);
});

srcSelect.addEventListener('change', performTranslation);
tgtSelect.addEventListener('change', performTranslation);

swapBtn.addEventListener('click', () => {
  if (srcSelect.value === 'auto') {
    srcSelect.value = 'en';
  }
  const temp = srcSelect.value;
  srcSelect.value = tgtSelect.value;
  tgtSelect.value = temp;

  const inText = srcInput.value;
  const outText = tgtOutput.textContent;
  if (outText && !tgtOutput.classList.contains('placeholder')) {
    srcInput.value = outText;
    tgtOutput.textContent = inText;
  }
  performTranslation();
});

clearBtn.addEventListener('click', () => {
  srcInput.value = '';
  tgtOutput.textContent = 'Translation will appear here...';
  tgtOutput.classList.add('placeholder');
  charCount.textContent = '0';
  warningBanner.style.display = 'none';
  dictCard.style.display = 'none';
  statusBar.textContent = 'Offline Engine Ready.';
});

copyBtn.addEventListener('click', () => {
  const text = tgtOutput.textContent;
  if (text && !tgtOutput.classList.contains('placeholder')) {
    copyToClipboard(text);
  }
});

themeToggleBtn.addEventListener('click', () => {
  currentTheme = currentTheme === 'light' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', currentTheme);
  localStorage.setItem('theme', currentTheme);
  themeToggleBtn.textContent = currentTheme === 'light' ? '🌙' : '☀️';
});

historyToggleBtn.addEventListener('click', () => {
  historyDrawer.classList.add('open');
  loadHistory();
});

closeDrawerBtn.addEventListener('click', () => {
  historyDrawer.classList.remove('open');
});

clearHistoryBtn.addEventListener('click', async () => {
  await fetch('/api/history/clear', { method: 'POST' });
  loadHistory();
  showToast('History cleared');
});

// Initial startup
loadLanguages();
themeToggleBtn.textContent = currentTheme === 'light' ? '🌙' : '☀️';

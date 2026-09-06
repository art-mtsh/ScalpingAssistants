// Вербальна інтерпретація статусів
const STATUS_LABELS = {
  1: 'Open',
  2: 'Open/Crossed',
  3: 'Too far',
  4: 'Removed',
  5: 'Crossed',
  6: 'Not listed',
};

let repeatCounter = window.REPEAT_COUNTER_DEFAULT || 5;
let allRows = [];

const tbody = document.getElementById('tbody');
const searchInput = document.getElementById('search');
const rowCountEl = document.getElementById('rowCount');
const lastUpdateEl = document.getElementById('lastUpdate');
const errorBanner = document.getElementById('errorBanner');
const themeToggle = document.getElementById('themeToggle');

function fmtNum(v, digits = 4) {
  if (v === null || v === undefined || v === '') return '';
  const n = Number(v);
  if (Number.isNaN(n)) return v;
  return n.toLocaleString('en-US', { maximumFractionDigits: digits });
}

function escapeHtml(s) {
  const div = document.createElement('div');
  div.textContent = s ?? '';
  return div.innerHTML;
}

function statusClass(status) {
  if (status === 1) return 'status-1';
  if (status === 2) return 'status-2';
  if (status === 5) return 'status-5';
  return '';
}

function statusLabel(status) {
  return STATUS_LABELS[status] ?? (status ?? '');
}

// Повертає сьогоднішню дату в форматі YYYY-MM-DD за локальним часом браузера
function todayStr() {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

// Якщо дата рядка збігається із сьогоднішньою - показуємо "Today"
// (час, якщо він є в значенні, залишається поруч, напр. "Today 14:05:00")
function formatDate(dateStr) {
  if (!dateStr) return '';
  const [datePart, ...rest] = String(dateStr).split(/[ T]/);
  if (datePart === todayStr()) {
    return rest.length ? `Today ${rest.join(' ')}` : 'Today';
  }
  return dateStr;
}

// Стрілочка напрямку: 1 -> вгору, 0 -> вниз
function directionArrow(direction) {
  if (direction === 1 || direction === '1') return '<span class="dir-up">↑</span>';
  if (direction === 0 || direction === '0') return '<span class="dir-down">↓</span>';
  return '';
}

function render() {
  const q = searchInput.value.trim().toLowerCase();
  const filtered = q
    ? allRows.filter(r => (r.coin || '').toLowerCase().includes(q))
    : allRows;

  rowCountEl.textContent = `Рядків: ${filtered.length} / ${allRows.length}`;

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="12" class="empty">Немає даних</td></tr>';
    return;
  }

  const html = filtered.map(r => {
    const highlightRow = (r.status === 1 || r.status === 2)
      && Number(r.continuous_count) >= repeatCounter;
    const sClass = statusClass(r.status);
    const countCell = (r.total_count !== null && r.total_count !== undefined)
      ? `${r.continuous_count ?? ''} <span class="count-total">(${r.total_count})</span>`
      : (r.continuous_count ?? '');
    const distanceCell = `${directionArrow(r.direction)} ${fmtNum(r.distance)}`.trim();

    return `
      <tr class="${highlightRow ? 'repeat-highlight' : ''}">
        <td>${escapeHtml(formatDate(r.date))}</td>
        <td>${escapeHtml(r.coin)}</td>
        <td>${fmtNum(r.dom)}</td>
        <td>${fmtNum(r.chart)}</td>
        <td>${fmtNum(r.current_price)}</td>
        <td>${distanceCell}</td>
        <td>${fmtNum(r.size_vs_dom)}</td>
        <td>${fmtNum(r.size_vs_avg)}</td>
        <td>${escapeHtml(r.first_signal)}</td>
        <td>${escapeHtml(r.last_fixation)}</td>
        <td>${countCell}</td>
        <td class="status-cell ${sClass}">${escapeHtml(statusLabel(r.status))}</td>
      </tr>
    `;
  }).join('');

  tbody.innerHTML = html;
}

async function fetchData() {
  try {
    const res = await fetch('/api/data');
    const data = await res.json();

    if (!res.ok || data.error) {
      errorBanner.style.display = 'block';
      errorBanner.textContent = data.error || 'Помилка завантаження даних';
      return;
    }

    errorBanner.style.display = 'none';
    allRows = data.rows || [];
    repeatCounter = data.repeat_counter ?? repeatCounter;
    lastUpdateEl.textContent = 'Оновлено: ' + new Date().toLocaleTimeString();
    render();
  } catch (e) {
    errorBanner.style.display = 'block';
    errorBanner.textContent = "Немає з'єднання з сервером";
  }
}

searchInput.addEventListener('input', render);

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme.js', theme);
  localStorage.setItem('sizes_theme', theme);
}

themeToggle.addEventListener('click', () => {
  const current = document.documentElement.getAttribute('data-theme.js');
  applyTheme(current === 'dark' ? 'light' : 'dark');
});

(function initTheme() {
  const saved = localStorage.getItem('sizes_theme');
  applyTheme(saved === 'light' ? 'light' : 'dark');
})();

fetchData();
setInterval(fetchData, 1000);
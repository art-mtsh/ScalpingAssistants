const STATUS_LABELS = {
  0: 'Not listed',
  1: 'Active',
  2: 'Auto-ban',
  3: 'Manual-ban',
};

let allCoins = [];

const tbody = document.getElementById('tbody');
const searchInput = document.getElementById('search');
const rowCountEl = document.getElementById('rowCount');
const errorBanner = document.getElementById('errorBanner');
const toastContainer = document.getElementById('toastContainer');

function escapeHtml(s) {
  const div = document.createElement('div');
  div.textContent = s ?? '';
  return div.innerHTML;
}

function statusClass(status) {
  if (status === 1) return 'coin-status-active';
  if (status === 2) return 'coin-status-autoban';
  if (status === 3) return 'coin-status-manualban';
  return 'coin-status-neutral';
}

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  toastContainer.appendChild(toast);

  // невелика затримка, щоб CSS-transition спрацював при появі
  requestAnimationFrame(() => toast.classList.add('show'));

  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 2800);
}

function render() {
  const q = searchInput.value.trim().toLowerCase();
  const filtered = q
    ? allCoins.filter(c => (c.coin || '').toLowerCase().includes(q))
    : allCoins;

  const activeCount = allCoins.filter(c => c.status === 1).length;
  rowCountEl.textContent = `Active: ${activeCount}/${allCoins.length}`;

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="empty">Немає монет</td></tr>';
    return;
  }

  tbody.innerHTML = filtered.map(c => {
    const isBanned = c.status === 3;
    return `
      <tr>
        <td>${escapeHtml(c.coin)}</td>
        <td>${c.tick_size ?? ''}</td>
        <td>${c.avg_atr ?? ''}</td>
        <td><span class="coin-status ${statusClass(c.status)}">${STATUS_LABELS[c.status] ?? c.status}</span></td>
        <td>
          <button class="btn-disable ${isBanned ? 'active' : ''}" data-coin="${escapeHtml(c.coin)}">
            ${isBanned ? 'Disabled' : 'Disable'}
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

async function fetchCoins() {
  try {
    const res = await fetch('/api/coins');
    const data = await res.json();

    if (!res.ok || data.error) {
      errorBanner.style.display = 'block';
      errorBanner.textContent = data.error || 'Coin load error';
      return;
    }

    errorBanner.style.display = 'none';
    allCoins = data.coins || [];
    render();
  } catch (e) {
    errorBanner.style.display = 'block';
    errorBanner.textContent = "No server connection";
  }
}

async function toggleCoin(coin) {
  try {
    const res = await fetch(`/api/coins/${encodeURIComponent(coin)}/toggle`, {
      method: 'POST',
    });
    const data = await res.json();

    if (!res.ok || data.error) {
      showToast(data.error || `Не вдалося змінити статус ${coin}`, 'error');
      return;
    }

    const idx = allCoins.findIndex(c => c.coin === coin);
    if (idx !== -1) allCoins[idx].status = data.status;
    render();

    if (data.status === 3) {
      showToast(`${coin}: вимкнено`, 'error');
    } else {
      showToast(`${coin}: увімкнено`, 'success');
    }
  } catch (e) {
    showToast("No server connection", 'error');
  }
}

tbody.addEventListener('click', (e) => {
  const btn = e.target.closest('.btn-disable');
  if (!btn) return;
  toggleCoin(btn.dataset.coin);
});

searchInput.addEventListener('input', render);

fetchCoins();
// Періодичне оновлення (напр. якщо бот сам змінив статус монети на auto-ban)
setInterval(fetchCoins, 3000);
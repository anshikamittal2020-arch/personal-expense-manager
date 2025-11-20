// -------------------- UX / initial state --------------------
document.getElementById('year').innerText = new Date().getFullYear();

const expenseForm = document.getElementById('expenseForm');
const categorySelect = document.getElementById('category');
const customInput = document.getElementById('custom_category');
const customLabel = document.getElementById('custom_label');
const amountInput = document.getElementById('amount');
const clearBtn = document.getElementById('clearBtn');
const summaryDiv = document.getElementById('expenseSummary');

let expenses = JSON.parse(localStorage.getItem('expenses') || '{}');

// show/hide custom category input
categorySelect.addEventListener('change', () => {
  if (categorySelect.value === 'others') {
    customInput.style.display = 'block';
    customInput.required = true;
  } else {
    customInput.style.display = 'none';
    customInput.required = false;
  }
});

// -------------------- Chart setup using Chart.js --------------------
const ctx = document.getElementById('expenseChart').getContext('2d');

const chartConfig = {
  type: 'bar',
  data: {
    labels: [],
    datasets: [{
      label: 'Expenses (₹)',
      data: [],
      backgroundColor: 'rgba(255,255,255,0.18)',
      borderColor: 'rgba(255,255,255,0.85)',
      borderWidth: 1,
      borderRadius: 8
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: { ticks: { color: 'rgba(255,255,255,0.9)' } },
      y: { beginAtZero: true, ticks: { color: 'rgba(255,255,255,0.9)' } }
    },
    plugins: {
      legend: { labels: { color: 'rgba(255,255,255,0.9)' } }
    }
  }
};

const expenseChart = new Chart(ctx, chartConfig);

// -------------------- functions --------------------
function saveExpenses() {
  localStorage.setItem('expenses', JSON.stringify(expenses));
}

function updateChartAndSummary() {
  const labels = Object.keys(expenses);
  const data = Object.values(expenses);
  expenseChart.data.labels = labels;
  expenseChart.data.datasets[0].data = data;
  expenseChart.update();

  // summary
  renderSummary();
}

function renderSummary() {
  summaryDiv.innerHTML = '';
  const keys = Object.keys(expenses);
  if (keys.length === 0) {
    const p = document.createElement('p');
    p.className = 'muted';
    p.textContent = 'No expenses added yet.';
    summaryDiv.appendChild(p);
    return;
  }

  let total = 0;
  keys.forEach(k => {
    const v = expenses[k];
    total += v;
    const item = document.createElement('div');
    item.className = 'summary-item';
    item.innerHTML = `<div>${escapeHtml(k)}</div><div>₹${Number(v).toFixed(2)}</div>`;
    summaryDiv.appendChild(item);
  });

  const totalItem = document.createElement('div');
  totalItem.className = 'summary-item';
  totalItem.style.fontWeight = '800';
  totalItem.innerHTML = `<div>Total</div><div>₹${Number(total).toFixed(2)}</div>`;
  summaryDiv.appendChild(totalItem);
}

function escapeHtml(text) {
  const map = { '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;' };
  return String(text).replace(/[&<>"']/g, m => map[m]);
}

// -------------------- form submit --------------------
expenseForm.addEventListener('submit', (e) => {
  e.preventDefault();

  const category = categorySelect.value === 'others' ? customInput.value.trim() : categorySelect.value;
  const amount = parseFloat(amountInput.value);

  if (!category || isNaN(amount) || amount <= 0) {
    alert('Enter a valid category and amount.');
    return;
  }

  // accumulate
  expenses[category] = (expenses[category] || 0) + amount;
  saveExpenses();
  updateChartAndSummary();

  // reset inputs
  expenseForm.reset();
  customInput.style.display = 'none';
});

// clear all
clearBtn.addEventListener('click', () => {
  if (!confirm('Clear all saved expenses?')) return;
  expenses = {};
  saveExpenses();
  updateChartAndSummary();
});

// init
updateChartAndSummary();

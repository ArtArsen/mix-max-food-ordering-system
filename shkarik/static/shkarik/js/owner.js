// Получаем данные из HTML
const salesDataElement = document.getElementById('sales-data');
const salesData = salesDataElement ? JSON.parse(salesDataElement.textContent) : [];

// Создание графика
const ctx = document.getElementById('salesChart');

if (ctx && salesData.length > 0) {
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: salesData.map(d => d.date),
      datasets: [{
        label: 'Выручка (сом)',
        data: salesData.map(d => d.total),
        borderColor: '#ffcb05',
        backgroundColor: 'rgba(255, 203, 5, 0.1)',
        borderWidth: 3,
        tension: 0.4,
        fill: true,
        pointRadius: 5,
        pointBackgroundColor: '#ffcb05',
        pointBorderColor: '#000',
        pointBorderWidth: 2,
        pointHoverRadius: 7,
        pointHoverBackgroundColor: '#ffd633',
        pointHoverBorderColor: '#000',
        pointHoverBorderWidth: 3,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            color: '#fff',
            font: { size: 14, weight: 'bold' },
            padding: 15
          }
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.9)',
          titleColor: '#ffcb05',
          bodyColor: '#fff',
          padding: 12,
          borderColor: '#ffcb05',
          borderWidth: 2,
          displayColors: false,
          callbacks: {
            label: function(context) {
              return 'Выручка: ' + context.parsed.y.toLocaleString() + ' сом';
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { 
            color: '#9fb4d4',
            font: { size: 12 },
            callback: function(value) {
              return value.toLocaleString();
            }
          },
          grid: { 
            color: 'rgba(255, 255, 255, 0.1)',
            drawBorder: false
          }
        },
        x: {
          ticks: { 
            color: '#9fb4d4',
            font: { size: 12 }
          },
          grid: { 
            color: 'rgba(255, 255, 255, 0.05)',
            drawBorder: false
          }
        }
      },
      interaction: {
        intersect: false,
        mode: 'index'
      }
    }
  });
}

// Анимация прогресс-баров
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.progress[data-percent]').forEach(el => {
    const percent = parseFloat(el.dataset.percent) || 0;
    setTimeout(() => {
      el.style.width = Math.min(percent, 100) + '%';
    }, 100);
  });
});
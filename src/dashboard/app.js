// Dashboard JavaScript - handles data fetching and UI updates

const API_BASE = 'http://localhost:8000/api';
const REFRESH_INTERVAL = 30000; // 30 seconds

let successRateChart = null;
let errorDistChart = null;
let funnelChart = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    fetchDashboardData();
    setInterval(fetchDashboardData, REFRESH_INTERVAL);
});

// Initialize Chart.js charts
function initCharts() {
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                labels: {
                    color: '#d1d5db'
                }
            }
        },
        scales: {
            y: {
                ticks: { color: '#9ca3af' },
                grid: { color: '#374151' }
            },
            x: {
                ticks: { color: '#9ca3af' },
                grid: { color: '#374151' }
            }
        }
    };

    // Success Rate Chart
    const successCtx = document.getElementById('successRateChart').getContext('2d');
    successRateChart = new Chart(successCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Mensagens Enviadas',
                data: [],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#d1d5db' }
                }
            },
            scales: {
                y: {
                    ticks: { color: '#9ca3af' },
                    grid: { color: '#374151' }
                },
                x: {
                    ticks: { color: '#9ca3af' },
                    grid: { color: '#374151' }
                }
            }
        }
    });

    // Error Distribution Chart
    const errorCtx = document.getElementById('errorDistChart').getContext('2d');
    errorDistChart = new Chart(errorCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    '#ef4444',
                    '#f59e0b',
                    '#3b82f6',
                    '#8b5cf6',
                    '#ec4899'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { color: '#d1d5db' }
                }
            },
            layout: {
                padding: 20
            }
        }
    });

    // Funnel Chart
    const funnelCtx = document.getElementById('funnelChart').getContext('2d');
    funnelChart = new Chart(funnelCtx, {
        type: 'bar',
        data: {
            labels: ['Total Importado', 'Celulares Válidos', 'Enviados'],
            datasets: [{
                label: 'Funil de Conversão',
                data: [],
                backgroundColor: [
                    '#6b7280', // Gray
                    '#3b82f6', // Blue
                    '#10b981'  // Green
                ],
                borderRadius: 4,
                maxBarThickness: 50
            }]
        },
        options: {
            indexAxis: 'y', // Horizontal bars
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: '#374151' },
                    ticks: { color: '#9ca3af' }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#d1d5db', font: { weight: 'bold' } }
                }
            }
        }
    });
}

// Fetch all dashboard data
async function fetchDashboardData() {
    try {
        await Promise.all([
            fetchCurrentMetrics(),
            fetchSessionHistory(),
            fetchRecentLogs(),
            fetchCondominioStats(),
            fetchFunnelStats(),
            fetchEta(),
            fetchDailyStats()
        ]);
        updateLastUpdateTime();
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
        updateStatus('Erro', 'danger');
    }
}

// Fetch current session metrics
async function fetchCurrentMetrics() {
    try {
        const response = await fetch(`${API_BASE}/metrics/current`);
        if (!response.ok) throw new Error('Failed to fetch current metrics');
        
        const data = await response.json();
        updateCurrentMetrics(data);
        updateErrorDistChart(data);  // Update status distribution with same data
        updateStatus('Ativo', 'success');
    } catch (error) {
        console.error('Error fetching current metrics:', error);
        updateStatus('Ocioso', 'secondary');
    }
}

// Update current session metrics display
function updateCurrentMetrics(data) {
    document.getElementById('current-contacts').textContent = data.total_contacts || 0;
    document.getElementById('current-sent').textContent = data.phones_sent || 0;
    document.getElementById('current-failed').textContent = data.error_count || 0;
    
    // Calculate success rate from phones
    const phonesFound = data.phones_found || 0;
    const phonesSent = data.phones_sent || 0;
    const successRate = phonesFound > 0 ? (phonesSent / phonesFound * 100) : 0;
    document.getElementById('current-success-rate').textContent = `${successRate.toFixed(1)}%`;
}

// Fetch session history (now contacts)
async function fetchSessionHistory() {
    try {
        const response = await fetch(`${API_BASE}/metrics/history?limit=250`);
        if (!response.ok) throw new Error('Failed to fetch session history');
        
        const contacts = await response.json();
        updateSessionsTable(contacts);
    } catch (error) {
        console.error('Error fetching session history:', error);
    }
}

// Update sessions table (now shows contacts)
function updateSessionsTable(contacts) {
    const tbody = document.getElementById('sessions-tbody');
    
    if (!contacts || contacts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="no-data">Nenhum contato</td></tr>';
        return;
    }

    tbody.innerHTML = contacts.map(contact => {
        const statusColor = contact.status === 'SUCCESS' ? '#10b981' : 
                           contact.status === 'PARTIAL' ? '#f59e0b' : '#ef4444';
        return `
        <tr>
            <td><strong>${contact.name || 'Desconhecido'}</strong></td>
            <td>${formatDateTime(contact.timestamp)}</td>
            <td><span style="color: ${statusColor}">${contact.status}</span></td>
            <td>${contact.phones_found || 0}</td>
            <td>${contact.phones_sent || 0}</td>
            <td><span style="color: ${statusColor}">${contact.phones_found > 0 ? ((contact.phones_sent / contact.phones_found) * 100).toFixed(0) : 0}%</span></td>
            <td>-</td>
        </tr>
    `}).join('');
}

// Fetch and update daily stats chart
async function fetchDailyStats() {
    try {
        const response = await fetch(`${API_BASE}/stats/daily?days=7`);
        if (!response.ok) throw new Error('Failed to fetch daily stats');
        
        const stats = await response.json();
        updateDailyMessagesChart(stats);
    } catch (error) {
        console.error('Error fetching daily stats:', error);
    }
}

// Update daily messages chart
function updateDailyMessagesChart(stats) {
    if (!stats || stats.length === 0) return;

    const labels = stats.map(s => {
        const [y, m, d] = s.date.split('-');
        return `${d}/${m}`;
    });
    const data = stats.map(s => s.count);

    successRateChart.data.labels = labels;
    successRateChart.data.datasets[0].data = data;
    successRateChart.update();
}

// Fetch recent logs
async function fetchRecentLogs() {
    try {
        const response = await fetch(`${API_BASE}/logs/recent?limit=20`);
        if (!response.ok) throw new Error('Failed to fetch logs');
        
        const logs = await response.json();
        updateLogsDisplay(logs);
    } catch (error) {
        console.error('Error fetching logs:', error);
    }
}

// Fetch condominium stats
async function fetchCondominioStats() {
    try {
        const response = await fetch(`${API_BASE}/stats/by-condominio`);
        if (!response.ok) throw new Error('Failed to fetch condominio stats');
        
        const stats = await response.json();
        updateCondominioTable(stats);
    } catch (error) {
        console.error('Error fetching condominio stats:', error);
    }
}

// Fetch funnel stats
async function fetchFunnelStats() {
    try {
        const response = await fetch(`${API_BASE}/funnel`);
        if (!response.ok) throw new Error('Failed to fetch funnel stats');
        
        const stats = await response.json();
        updateFunnelChart(stats);
    } catch (error) {
        console.error('Error fetching funnel stats:', error);
    }
}

// Update condominium comparison table
function updateCondominioTable(stats) {
    const tbody = document.getElementById('condominio-tbody');
    
    if (!stats || stats.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="no-data">Sem dados ainda</td></tr>';
        return;
    }

    tbody.innerHTML = stats.map(s => {
        const rateColor = s.success_rate >= 80 ? '#10b981' : 
                         s.success_rate >= 50 ? '#f59e0b' : '#ef4444';
        return `
        <tr>
            <td><strong>${s.condominio}</strong></td>
            <td>${s.total_contacts}</td>
            <td>${s.phones_found}</td>
            <td>${s.phones_sent}</td>
            <td><span style="color: ${rateColor}; font-weight: bold">${s.success_rate}%</span></td>
        </tr>
    `}).join('');
}

// Update funnel chart
function updateFunnelChart(stats) {
    if (!stats || Object.keys(stats).length === 0) return;

    const data = [
        stats.total_imported || 0,
        stats.mobile_phones || 0,
        stats.phones_sent || 0
    ];

    funnelChart.data.datasets[0].data = data;
    funnelChart.update();
}

// Fetch ETA metrics
async function fetchEta() {
    try {
        const response = await fetch(`${API_BASE}/eta`);
        if (!response.ok) throw new Error('Failed to fetch ETA');
        
        const data = await response.json();
        updateEtaDisplay(data);
    } catch (error) {
        console.error('Error fetching ETA:', error);
    }
}

// Update ETA display
function updateEtaDisplay(data) {
    if (!data || Object.keys(data).length === 0) {
        document.getElementById('current-speed').textContent = '-';
        document.getElementById('current-eta').textContent = '-';
        return;
    }

    // Progress (X/Y)
    document.getElementById('current-speed').textContent = data.progress || '0/0';

    // ETA
    const etaSeconds = data.eta_seconds || 0;
    if (etaSeconds > 0) {
        if (etaSeconds < 60) {
            document.getElementById('current-eta').textContent = `${etaSeconds}s`;
        } else {
            const mins = Math.ceil(etaSeconds / 60);
            document.getElementById('current-eta').textContent = `${mins}m`;
        }
    } else {
        document.getElementById('current-eta').textContent = data.remaining > 0 ? 'Calcular' : 'Fim';
    }
}

// Update logs display
function updateLogsDisplay(logs) {
    const container = document.getElementById('logs-container');
    
    if (!logs || logs.length === 0) {
        container.innerHTML = '<div class="no-data">Nenhum log disponível</div>';
        return;
    }

    container.innerHTML = logs.map(log => {
        const level = log.level.toLowerCase();
        const levelClass = level === 'success' ? 'success' : 
                          level === 'error' ? 'error' : 
                          level === 'warning' ? 'warning' : '';
        
        return `
            <div class="log-entry ${levelClass}">
                <span class="log-timestamp">${formatTime(log.time)}</span>
                <span class="log-level ${levelClass}">${log.level}</span>
                <span class="log-message">${escapeHtml(log.message)}</span>
            </div>
        `;
    }).join('');
}

// Update status distribution chart (SUCCESS/PARTIAL/ERROR)
function updateErrorDistChart(data) {
    // Use stats from /api/metrics/current
    const success = data.success_count || 0;
    const partial = data.partial_count || 0;
    const error = data.error_count || 0;
    const total = success + partial + error;
    
    if (total === 0) {
        errorDistChart.data.labels = ['Sem Dados'];
        errorDistChart.data.datasets[0].data = [1];
        errorDistChart.data.datasets[0].backgroundColor = ['#6b7280'];
        errorDistChart.update();
        return;
    }
    
    // Build labels and data based on what exists
    const labels = [];
    const values = [];
    const colors = [];
    
    if (success > 0) {
        labels.push(`Sucesso (${Math.round(success/total*100)}%)`);
        values.push(success);
        colors.push('#10b981'); // Green
    }
    if (partial > 0) {
        labels.push(`Parcial (${Math.round(partial/total*100)}%)`);
        values.push(partial);
        colors.push('#f59e0b'); // Orange
    }
    if (error > 0) {
        labels.push(`Erro (${Math.round(error/total*100)}%)`);
        values.push(error);
        colors.push('#ef4444'); // Red
    }
    
    // If 100% success, show all green
    if (success === total) {
        labels.length = 0;
        values.length = 0;
        colors.length = 0;
        labels.push('100% Sucesso');
        values.push(total);
        colors.push('#10b981');
    }
    
    errorDistChart.data.labels = labels;
    errorDistChart.data.datasets[0].data = values;
    errorDistChart.data.datasets[0].backgroundColor = colors;
    errorDistChart.update();
}

// Helper functions
function updateStatus(status, type) {
    const statusEl = document.getElementById('status');
    statusEl.textContent = status;
    statusEl.style.color = type === 'success' ? '#10b981' : 
                          type === 'danger' ? '#ef4444' : '#3b82f6';
}

function updateLastUpdateTime() {
    document.getElementById('last-update').textContent = 
        new Date().toLocaleTimeString('pt-BR');
}

function formatDateTime(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatTime(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

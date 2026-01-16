// Globale variabelen
let powerChart = null;
let updateInterval = null;

// Initialize Chart.js
function initChart() {
    const ctx = document.getElementById('powerChart').getContext('2d');
    powerChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Opwekking (W)',
                    data: [],
                    borderColor: 'rgb(34, 197, 94)',
                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Verbruik (W)',
                    data: [],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Grid (W)',
                    data: [],
                    borderColor: 'rgb(168, 85, 247)',
                    backgroundColor: 'rgba(168, 85, 247, 0.1)',
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2.5,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += Math.round(context.parsed.y) + ' W';
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value + ' W';
                        }
                    }
                },
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            }
        }
    });
}

// Format tijd voor display
function formatTime(isoString) {
    if (!isoString) return '-';
    const date = new Date(isoString);
    return date.toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

// Format groot getal met duizendtallen
function formatNumber(num) {
    if (num === null || num === undefined || isNaN(num)) return '-';
    return Math.round(num).toLocaleString('nl-NL');
}

// Update dashboard met nieuwste data
async function updateDashboard() {
    try {
        // Haal status op
        const statusResponse = await fetch('/api/status');
        const status = await statusResponse.json();

        // Update status indicator
        const statusIndicator = document.getElementById('status-indicator');
        if (status.status === 'running') {
            statusIndicator.textContent = '🟢 Actief';
            statusIndicator.style.color = 'var(--success-color)';
        } else {
            statusIndicator.textContent = '🔴 Gestopt';
            statusIndicator.style.color = 'var(--danger-color)';
        }

        // Haal statistieken op
        const statsResponse = await fetch('/api/data/statistics');
        const stats = await statsResponse.json();

        // Update zonnepanelen
        const solarPower = stats.totals?.generation_w || 0;
        document.getElementById('solar-power').textContent = formatNumber(solarPower);
        document.getElementById('solar-total').textContent =
            (stats.kwh?.total_generated_kwh || 0).toFixed(2);

        // Update verbruik
        const consumption = stats.totals?.consumption_w || 0;
        document.getElementById('consumption-power').textContent = formatNumber(consumption);
        document.getElementById('self-consumption').textContent =
            formatNumber(stats.totals?.self_consumption_w || 0);

        // Update grid
        const gridPower = stats.totals?.grid_power_w || 0;
        const gridElement = document.getElementById('grid-power');
        gridElement.textContent = formatNumber(Math.abs(gridPower));

        if (gridPower > 0) {
            gridElement.classList.add('negative');
            gridElement.classList.remove('positive');
            document.getElementById('grid-label').textContent = 'Import:';
            document.getElementById('grid-status').textContent = 'Van net';
        } else if (gridPower < 0) {
            gridElement.classList.add('positive');
            gridElement.classList.remove('negative');
            document.getElementById('grid-label').textContent = 'Export:';
            document.getElementById('grid-status').textContent = 'Naar net';
        } else {
            gridElement.classList.remove('positive', 'negative');
            document.getElementById('grid-label').textContent = 'Status:';
            document.getElementById('grid-status').textContent = 'Geen flow';
        }

        // Update PVOutput status
        const pvoutputStatus = status.config.pvoutput_configured ? '✓ Actief' : '✗ Niet geconfigureerd';
        document.getElementById('pvoutput-status').textContent = pvoutputStatus;

        // Haal laatste data op voor timestamp
        const latestResponse = await fetch('/api/data/latest');
        const latest = await latestResponse.json();
        document.getElementById('last-update').textContent = formatTime(latest.last_update);

        // Update grafiek
        await updateChart();

    } catch (error) {
        console.error('Fout bij updaten dashboard:', error);
    }
}

// Update grafiek met historische data
async function updateChart() {
    try {
        const response = await fetch('/api/data/history?hours=1');
        const history = await response.json();

        const labels = [];
        const generationData = [];
        const consumptionData = [];
        const gridData = [];

        // Verwerk P1 en kWh data
        const maxLength = Math.max(history.p1?.length || 0, history.kwh?.length || 0);

        for (let i = 0; i < maxLength; i++) {
            const p1Item = history.p1?.[i];
            const kwhItem = history.kwh?.[i];

            // Gebruik timestamp van eerste beschikbare item
            const timestamp = p1Item?._timestamp || kwhItem?._timestamp;
            if (timestamp) {
                const time = new Date(timestamp);
                labels.push(time.toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' }));
            }

            // Opwekking
            const generation = kwhItem?.active_power_w || 0;
            generationData.push(generation);

            // Grid power
            const gridPower = p1Item?.active_power_w || 0;
            gridData.push(gridPower);

            // Verbruik = opwekking + grid (grid is negatief bij teruglevering)
            const consumption = generation + gridPower;
            consumptionData.push(consumption);
        }

        // Update chart data
        powerChart.data.labels = labels;
        powerChart.data.datasets[0].data = generationData;
        powerChart.data.datasets[1].data = consumptionData;
        powerChart.data.datasets[2].data = gridData;
        powerChart.update('none'); // 'none' voor betere performance

    } catch (error) {
        console.error('Fout bij updaten grafiek:', error);
    }
}

// Laad configuratie
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();

        document.getElementById('p1-enabled').checked = config.homewizard_p1.enabled;
        document.getElementById('p1-host').value = config.homewizard_p1.host || '';

        document.getElementById('kwh-enabled').checked = config.homewizard_kwh.enabled;
        document.getElementById('kwh-host').value = config.homewizard_kwh.host || '';

        document.getElementById('pvoutput-system-id').value = config.pvoutput.system_id || '';
        document.getElementById('update-interval').value = config.update_interval;

    } catch (error) {
        console.error('Fout bij laden configuratie:', error);
    }
}

// Sla configuratie op
async function saveConfig(event) {
    event.preventDefault();

    const config = {
        homewizard_p1: {
            enabled: document.getElementById('p1-enabled').checked,
            host: document.getElementById('p1-host').value
        },
        homewizard_kwh: {
            enabled: document.getElementById('kwh-enabled').checked,
            host: document.getElementById('kwh-host').value
        },
        pvoutput: {
            system_id: document.getElementById('pvoutput-system-id').value,
            api_key: document.getElementById('pvoutput-api-key').value || undefined
        },
        update_interval: parseInt(document.getElementById('update-interval').value)
    };

    // Verwijder api_key als deze leeg is
    if (!config.pvoutput.api_key) {
        delete config.pvoutput.api_key;
    }

    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });

        if (response.ok) {
            alert('Configuratie opgeslagen! De container zal herstarten.');
            location.reload();
        } else {
            alert('Fout bij opslaan configuratie');
        }
    } catch (error) {
        console.error('Fout bij opslaan configuratie:', error);
        alert('Fout bij opslaan configuratie');
    }
}

// Forceer update
async function forceUpdate() {
    try {
        const button = document.getElementById('update-now-btn');
        button.disabled = true;
        button.textContent = 'Bezig...';

        const response = await fetch('/api/update-now', { method: 'POST' });

        if (response.ok) {
            await updateDashboard();
            button.textContent = 'Gelukt!';
            setTimeout(() => {
                button.textContent = 'Nu updaten';
                button.disabled = false;
            }, 2000);
        } else {
            button.textContent = 'Fout!';
            setTimeout(() => {
                button.textContent = 'Nu updaten';
                button.disabled = false;
            }, 2000);
        }
    } catch (error) {
        console.error('Fout bij forceren update:', error);
    }
}

// Toggle configuratie sectie
function toggleConfig() {
    const content = document.getElementById('config-content');
    const button = document.getElementById('toggle-config-btn');

    if (content.style.display === 'none') {
        content.style.display = 'block';
        button.textContent = 'Verberg';
        loadConfig();
    } else {
        content.style.display = 'none';
        button.textContent = 'Toon';
    }
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    updateDashboard();

    // Start auto-update elke 5 seconden
    updateInterval = setInterval(updateDashboard, 5000);

    // Event listeners
    document.getElementById('update-now-btn').addEventListener('click', forceUpdate);
    document.getElementById('toggle-config-btn').addEventListener('click', toggleConfig);
    document.getElementById('config-form').addEventListener('submit', saveConfig);
});

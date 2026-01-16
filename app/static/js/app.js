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

// Update individuele kWh meters weergave
function updateIndividualMeters(meters) {
    const section = document.getElementById('individual-meters-section');
    const grid = document.getElementById('individual-meters-grid');

    if (!meters || meters.length === 0) {
        section.style.display = 'none';
        return;
    }

    section.style.display = 'block';
    grid.innerHTML = '';

    meters.forEach(meter => {
        const meterCard = document.createElement('div');
        meterCard.className = 'meter-card';
        meterCard.innerHTML = `
            <h4>${meter.meter_name || 'Onbekend'}</h4>
            <div class="meter-power">${formatNumber(meter.active_power_w || 0)} W</div>
            <div class="meter-total">${(meter.total_power_export_kwh || 0).toFixed(2)} kWh</div>
        `;
        grid.appendChild(meterCard);
    });
}

// Update dagelijkse totalen
async function updateDailyTotals() {
    try {
        const response = await fetch('/api/data/daily');
        const daily = await response.json();

        document.getElementById('daily-generation').textContent =
            (daily.energy_generation_wh / 1000).toFixed(2);
        document.getElementById('daily-consumption').textContent =
            (daily.energy_consumption_wh / 1000).toFixed(2);
        document.getElementById('daily-import').textContent =
            (daily.energy_import_wh / 1000).toFixed(2);
        document.getElementById('daily-export').textContent =
            (daily.energy_export_wh / 1000).toFixed(2);
    } catch (error) {
        console.error('Fout bij updaten dagelijkse totalen:', error);
    }
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

        // Update individuele meters
        if (stats.individual_kwh_meters) {
            updateIndividualMeters(stats.individual_kwh_meters);
        }

        // Update dagelijkse totalen
        await updateDailyTotals();

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

// Render kWh meters configuratie
function renderKwhMetersConfig(meters) {
    const container = document.getElementById('kwh-meters-config');
    container.innerHTML = '';

    if (!meters || meters.length === 0) {
        meters = [{ name: 'Omvormer 1', host: '', enabled: true }];
    }

    meters.forEach((meter, index) => {
        const meterDiv = document.createElement('div');
        meterDiv.className = 'kwh-meter-config';
        meterDiv.innerHTML = `
            <div class="meter-config-header">
                <h5>Meter ${index + 1}</h5>
                ${meters.length > 1 ? `<button type="button" class="btn-remove" onclick="removeKwhMeter(${index})">×</button>` : ''}
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" class="kwh-meter-enabled" data-index="${index}" ${meter.enabled ? 'checked' : ''}>
                    Ingeschakeld
                </label>
            </div>
            <div class="form-group">
                <label>Naam:</label>
                <input type="text" class="kwh-meter-name" data-index="${index}" value="${meter.name || ''}" placeholder="Omvormer 1">
            </div>
            <div class="form-group">
                <label>IP Adres:</label>
                <input type="text" class="kwh-meter-host" data-index="${index}" value="${meter.host || ''}" placeholder="192.168.1.101">
            </div>
        `;
        container.appendChild(meterDiv);
    });
}

// Voeg kWh meter toe
function addKwhMeter() {
    const container = document.getElementById('kwh-meters-config');
    const currentCount = container.querySelectorAll('.kwh-meter-config').length;

    const meterDiv = document.createElement('div');
    meterDiv.className = 'kwh-meter-config';
    meterDiv.innerHTML = `
        <div class="meter-config-header">
            <h5>Meter ${currentCount + 1}</h5>
            <button type="button" class="btn-remove" onclick="removeKwhMeter(${currentCount})">×</button>
        </div>
        <div class="form-group">
            <label>
                <input type="checkbox" class="kwh-meter-enabled" data-index="${currentCount}" checked>
                Ingeschakeld
            </label>
        </div>
        <div class="form-group">
            <label>Naam:</label>
            <input type="text" class="kwh-meter-name" data-index="${currentCount}" placeholder="Omvormer ${currentCount + 1}">
        </div>
        <div class="form-group">
            <label>IP Adres:</label>
            <input type="text" class="kwh-meter-host" data-index="${currentCount}" placeholder="192.168.1.10${currentCount + 1}">
        </div>
    `;
    container.appendChild(meterDiv);
}

// Verwijder kWh meter
function removeKwhMeter(index) {
    const container = document.getElementById('kwh-meters-config');
    const meters = container.querySelectorAll('.kwh-meter-config');

    if (meters.length > 1) {
        meters[index].remove();
        // Re-render om indices te updaten
        const currentConfig = getKwhMetersFromForm();
        currentConfig.splice(index, 1);
        renderKwhMetersConfig(currentConfig);
    }
}

// Haal kWh meters uit formulier
function getKwhMetersFromForm() {
    const container = document.getElementById('kwh-meters-config');
    const meters = [];

    container.querySelectorAll('.kwh-meter-config').forEach((meterDiv, index) => {
        const nameInput = meterDiv.querySelector('.kwh-meter-name');
        const hostInput = meterDiv.querySelector('.kwh-meter-host');
        const enabledInput = meterDiv.querySelector('.kwh-meter-enabled');

        meters.push({
            name: nameInput.value || `Omvormer ${index + 1}`,
            host: hostInput.value,
            enabled: enabledInput.checked
        });
    });

    return meters;
}

// Laad configuratie
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();

        document.getElementById('p1-enabled').checked = config.homewizard_p1.enabled;
        document.getElementById('p1-host').value = config.homewizard_p1.host || '';

        renderKwhMetersConfig(config.homewizard_kwh_meters);

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
        homewizard_kwh_meters: getKwhMetersFromForm(),
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
    document.getElementById('add-kwh-meter-btn').addEventListener('click', addKwhMeter);
});

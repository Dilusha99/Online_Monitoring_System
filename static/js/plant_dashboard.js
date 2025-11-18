// static/js/plant_dashboard.js

let plantChart = null;
let currentPlantId = null;
let updateInterval = null;
let isFirstLoad = true;
let previousStandbyUnits = null;
let previousRunningUnits = null;

/**
 * Initialize plant dashboard when page loads
 */
document.addEventListener('DOMContentLoaded', function() {
    // Extract plant ID from URL or data attribute
    const plantIdElement = document.getElementById('plantData');
    if (plantIdElement) {
        currentPlantId = parseInt(plantIdElement.dataset.plantId, 10);
    }
    
    // Validate plant ID
    if (isNaN(currentPlantId) || currentPlantId < 1) {
        console.error('Invalid plant ID, defaulting to 1');
        currentPlantId = 1;
    }
    
    console.log('🏭 Plant Dashboard initialized for Plant ID:', currentPlantId);
    
    // Animate initial values
    animateInitialValues();
    
    initializePlantDashboard();
    
    // Add chart legend after a short delay
    setTimeout(() => {
        addChartLegend();
    }, 1000);
});

/**
 * Animate initial stat values from 0
 */
function animateInitialValues() {
    const totalPowerEl = document.getElementById('totalPower');
    const onlineUnitsEl = document.getElementById('onlineUnits');
    const standbyUnitsEl = document.getElementById('standbyUnits');
    const runningUnitsEl= document.getElementById('runningUnits') ;
    //const avgPowerEl = document.getElementById('avgPower');
    
    if (totalPowerEl) {
        const targetValue = parseFloat(totalPowerEl.textContent);
        totalPowerEl.innerHTML = '0.00 <span class="unit">MW</span>';
        //totalPowerEl.textContent = '0.00';
        animateValue(totalPowerEl, 0, targetValue, 1500, 2);
    }
    
    if (onlineUnitsEl) {
        const targetValue = parseInt(onlineUnitsEl.textContent);
        onlineUnitsEl.textContent = '0';
        animateValue(onlineUnitsEl, 0, targetValue, 1200, 0);
    }
    
    if (standbyUnitsEl) {
        const targetValue = parseInt(standbyUnitsEl.textContent);
        standbyUnitsEl.textContent = '0';
        animateValue(standbyUnitsEl, 0, targetValue, 1200, 0);
    }
    
    // if (avgPowerEl) {
    //     const targetValue = parseFloat(avgPowerEl.textContent);
    //     avgPowerEl.textContent = '0.0';
    //     animateValue(avgPowerEl, 0, targetValue, 1200, 1);
    // }

    // Animate running units (NEW)
    if (runningUnitsEl) {
        const targetValue = parseInt(runningUnitsEl.textContent);
        runningUnitsEl.textContent = '0';
        animateValue(runningUnitsEl, 0,targetValue,1200, 0);
    }

    
    isFirstLoad = false;
}

/**
 * Main initialization function
 */
function initializePlantDashboard() {
    updateDateTime();
    loadPlantChart();
    initializeGauges();
    
    // Set up auto-refresh
    setInterval(updateDateTime, 1000); // Update time every second
    setInterval(refreshPlantData, 5000); // Refresh data every 5 seconds
    setInterval(refreshChartWithStatus, 30000); // Refresh chart every 30 seconds
}

/**
 * Update date and time display (Sri Lanka timezone)
 */
function updateDateTime() {
    const now = new Date();
    
    // Time options (24-hour format)
    const timeOptions = {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,  /* ← This makes it 24-hour format */
        timeZone: 'Asia/Colombo'
    };
    
    // Date options
    const dateOptions = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        timeZone: 'Asia/Colombo'
    };
    
    const formattedTime = now.toLocaleString('en-GB', timeOptions);  // 14:30:45
    const formattedDate = now.toLocaleString('en-CA', dateOptions);  // 2025-11-16
    
    const dateTimeElement = document.getElementById('currentDateTime');
    
    if (dateTimeElement) {
        dateTimeElement.textContent = `${formattedTime}`;  // Show only time
    }
    
    // Optional: Update timezone-info with date
    const timezoneElement = document.querySelector('.timezone-info');
    if (timezoneElement) {
        timezoneElement.textContent = formattedDate;  // Show date here
    }
}

/**
 * Initialize all gauges for units
 */
function initializeGauges() {
    const gaugeCanvases = document.querySelectorAll('.gauge-canvas');
    gaugeCanvases.forEach(canvas => {
        createGauge(canvas);
    });
}

/**
 * Create individual gauge
 */
function createGauge(canvas) {
    const ctx = canvas.getContext('2d');
    const id = canvas.id;
    
    // Get current value from the gauge-value element
    const valueElement = canvas.parentElement.querySelector('.gauge-value div');
    const value = parseFloat(valueElement.textContent) || 0;
    
    // Determine gauge type, color, and dynamic max value
    let type, color, maxValue, minMaxValue;
    if (id.includes('voltage')) {
        type = 'voltage';
        color = '#007bff';
        minMaxValue = 100; // Minimum scale for voltage
        maxValue = Math.max(minMaxValue, value + 100);
    } else if (id.includes('current')) {
        type = 'current';
        color = '#ffc107';
        minMaxValue = 50; // Minimum scale for current
        maxValue = Math.max(minMaxValue, value + 100);
    } else if (id.includes('power')) {
        type = 'power';
        color = '#28a745';
        minMaxValue = 100; // Minimum scale for power
        maxValue = Math.max(minMaxValue, value + 100);
    }  
    // Draw gauge
    drawGauge(ctx, value, maxValue, color, canvas.offsetWidth);
}

/**
 * Draw gauge on canvas
 */
function drawGauge(ctx, value, maxValue, color, size) {
    const centerX = size / 2;
    const centerY = size / 2;
    const radius = size * 0.38;
    const startAngle = -Math.PI;
    const endAngle = 0;
    
    // Clear canvas
    ctx.clearRect(0, 0, size, size);
    
    // Background arc
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, startAngle, endAngle);
    ctx.lineWidth = 20;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineCap = 'round';
    ctx.stroke();
    
    // Value arc
    const valueAngle = startAngle + (value / maxValue) * (endAngle - startAngle);
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, startAngle, valueAngle);
    ctx.lineWidth = 20;
    ctx.strokeStyle = color;
    ctx.lineCap = 'round';
    ctx.stroke();
    
    // Center dot
    ctx.beginPath();
    ctx.arc(centerX, centerY, 3, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();
}

/**
 * Update all gauges
 */
function updateGauges() {
    const gaugeCanvases = document.querySelectorAll('.gauge-canvas');
    gaugeCanvases.forEach(canvas => {
        const valueElement = canvas.parentElement.querySelector('.gauge-value div');
        const value = parseFloat(valueElement.textContent) || 0;
        
        let maxValue, color, minMaxValue;
        if (canvas.id.includes('voltage')) {
            minMaxValue = 100; // Minimum scale for voltage
            maxValue = Math.max(minMaxValue, value + 100);
            color = '#007bff';
        } else if (canvas.id.includes('current')) {
            minMaxValue = 50; // Minimum scale for current
            maxValue = Math.max(minMaxValue, value + 100);
            color = '#ffc107';
        } else if (canvas.id.includes('power')) {
            minMaxValue = 100; // Minimum scale for power
            maxValue = Math.max(minMaxValue, value + 100);
            color = '#28a745';
        }

        // let maxValue, color;
        // if (canvas.id.includes('voltage')) {
        //     maxValue = 6500;
        //     color = '#007bff';
        // } else if (canvas.id.includes('current')) {
        //     maxValue = 250;
        //     color = '#ffc107';
        // } else if (canvas.id.includes('power')) {
        //     maxValue = 5000;
        //     color = '#28a745';
        // }
        
        drawGauge(canvas.getContext('2d'), value, maxValue, color, canvas.offsetWidth);
    });
}

/**
 * Refresh plant data from API
 */
function refreshPlantData() {
    console.log('🔄 Refreshing plant data...');
    
    fetch(`/api/plant/${currentPlantId}/details`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('✓ Plant data received:', data);
            updatePlantStats(data);
            updateUnitsGrid(data);
            updateLiveIndicator();
        })
        .catch(error => {
            console.error('❌ Error refreshing plant data:', error);
            const indicator = document.getElementById('liveIndicator');
            if (indicator) {
                indicator.style.background = 'rgba(220, 53, 69, 0.9)';
                indicator.textContent = '⚠️ ERROR';
            }
        });
}

/**
 * Animate counter from current value to new value
 */
function animateValue(element, start, end, duration, decimals = 0) {
    if (!element) return;
    
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        
        // Check if this is the total power element (has MW unit)
        if (element.id === 'totalPower') {
            element.innerHTML = `${current.toFixed(decimals)} <span class="unit">MW</span>`;
        } else {
            element.textContent = current.toFixed(decimals);
        }

        //element.textContent = current.toFixed(decimals);
    }, 16);
}



/**
 * Reload page function
 */
function reloadPage() {
    console.log('🔄 Reloading page due to status change...');
    setTimeout(() => {
        window.location.reload();
    }, 5000); // 5 second delay for smooth transition
}

/**
 * Update plant statistics with animation and status change detection
 */
function updatePlantStats(data) {
    const elements = {
        totalPower: document.getElementById('totalPower'),
        onlineUnits: document.getElementById('onlineUnits'),
        offlineUnits: document.getElementById('offlineUnits'),
        standbyUnits: document.getElementById('standbyUnits'),
        runningUnits: document.getElementById('runningUnits')
    };

    // ===== CHECK FOR CHANGES FIRST (before updating anything) =====
    if (previousStandbyUnits !== null && previousRunningUnits !== null) {
        if (previousStandbyUnits !== data.standby_units) {
            console.log(`🔄 Standby units changed from ${previousStandbyUnits} to ${data.standby_units}, reloading...`);
            reloadPage();
            return; // Stop further updates
        }
        
        if (previousRunningUnits !== data.running_units) {
            console.log(`🔄 Running units changed from ${previousRunningUnits} to ${data.running_units}, reloading...`);
            reloadPage();
            return; // Stop further updates
        }
    }
    
    // ===== UPDATE PREVIOUS VALUES =====
    previousStandbyUnits = data.standby_units;
    previousRunningUnits = data.running_units;

    // ===== UPDATE UI =====
    if (elements.totalPower) {
        const newValue = (data.total_power / 1000);
        elements.totalPower.innerHTML = `${newValue.toFixed(2)} <span class="unit">MW</span>`;
    }
    
    if (elements.onlineUnits) {
        elements.onlineUnits.textContent = data.online_units;
    }
    
    if (elements.offlineUnits) {
        elements.offlineUnits.textContent = data.offline_units;
    }
    
    if (elements.standbyUnits) {
        elements.standbyUnits.textContent = data.standby_units;
    }
    
    if (elements.runningUnits) {
        elements.runningUnits.textContent = data.running_units;
    }
}

/**
 * Get status display text and emoji
 */
function getStatusDisplay(status) {
    switch(status) {
        case 'online':
        case 'running':
            return { text: 'Running', emoji: '⚡' };
        case 'standby':
            return { text: 'Standby', emoji: '⏸️' };
        case 'offline':
            return { text: 'Offline', emoji: '⚠️' };
        default:
            return { text: 'Unknown', emoji: '⚪' };
    }
}

/**
 * Get unit status from unit data
 */
function getUnitStatus(unit) {
    if (!unit.online) {
        return 'offline';
    }
    
    // Check if unit is in standby mode
    if (unit.standby === true || 
        (unit.power === 0 && unit.current_avg === 0 && unit.voltage_avg === 0)) {
        return 'standby';
    }
    
    return 'online';
}

/**
 * Update units grid with live data (updates existing elements only)
 */
function updateUnitsGrid(data) {
    if (!data.units) return;

    data.units.forEach(unit => {
        const status = getUnitStatus(unit);
        const statusDisplay = getStatusDisplay(status);
        
        // Find the existing unit card
        const unitCard = document.querySelector(`[data-unit-id="${unit.unit_id}"]`);
        if (!unitCard) return;
        
        // Update card status classes
        unitCard.className = `unit-card ${status}`;
        
        // Update status dot
        const statusDot = unitCard.querySelector('.status-dot');
        if (statusDot) {
            statusDot.className = `status-dot ${status}`;
        }
        
        // Update status badge
        const statusBadge = unitCard.querySelector('.unit-status');
        if (statusBadge) {
            statusBadge.className = `unit-status ${status}`;
            statusBadge.textContent = `${statusDisplay.emoji} ${statusDisplay.text}`;
        }
        
        // Update gauge values
        const voltageValue = unitCard.querySelector(`#voltageGauge${unit.unit_id}`)?.parentElement.querySelector('.gauge-value div');
        const currentValue = unitCard.querySelector(`#currentGauge${unit.unit_id}`)?.parentElement.querySelector('.gauge-value div');
        const powerValue = unitCard.querySelector(`#powerGauge${unit.unit_id}`)?.parentElement.querySelector('.gauge-value div');
        
        if (voltageValue) {
            voltageValue.textContent = unit.online ? unit.voltage_avg : '---';
        }
        if (currentValue) {
            currentValue.textContent = unit.online ? unit.current_avg : '---';
        }
        if (powerValue) {
            powerValue.textContent = unit.online ? unit.power : '---';
        }
        
        // Update gauge containers (add/remove offline class)
        const gaugeContainers = unitCard.querySelectorAll('.gauge-container');
        gaugeContainers.forEach(container => {
            if (status === 'offline') {
                container.classList.add('gauge-offline');
            } else {
                container.classList.remove('gauge-offline');
            }
        });
        
        // Update timestamp
        const timeElement = unitCard.querySelector('.unit-time');
        if (timeElement) {
            timeElement.innerHTML = `
                Last update: ${unit.online ? unit.timestamp : 'No data'}
                ${unit.online ? '<small style="color: #28a745;"> (LK Time)</small>' : ''}
            `;
        }
    });

    // Update gauges after data is updated
    setTimeout(() => {
        updateGauges();
    }, 100);
}

/**
 * Update live indicator
 */
function updateLiveIndicator() {
    const indicator = document.getElementById('liveIndicator');
    const onlineUnitsEl = document.getElementById('onlineUnits');
    if (!indicator || !onlineUnitsEl) return;

    const onlineUnits = Number(onlineUnitsEl.textContent) || 0;

    if (onlineUnits > 0) {
        indicator.style.background = 'rgba(40, 167, 69, 0.9)';
        indicator.textContent = '🟢 ONLINE';
        setTimeout(() => {
            indicator.style.background = 'rgba(40, 167, 69, 0.5)';
        }, 500);
    } else {
        indicator.style.background = 'rgba(220, 53, 69, 0.9)';
        indicator.textContent = '🔴 OFFLINE';
    }
}

/**
 * Load plant chart with offline gap detection
 */
function loadPlantChart() {
    console.log('📊 Loading chart for Plant', currentPlantId);
    
    fetch(`/api/plant/${currentPlantId}/history`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const ctx = document.getElementById('plantChart');
            if (!ctx) return;
            
            if (plantChart) {
                plantChart.destroy();
            }
            
            plantChart = new Chart(ctx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        label: `Plant ${currentPlantId} Total Power (kW)`,
                        data: data.power || [],
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: function(context) {
                            return context.parsed.y === 0 ? 6 : 4;
                        },
                        pointHoverRadius: 8,
                        pointBackgroundColor: function(context) {
                            return context.parsed.y === 0 ? '#dc3545' : '#28a745';
                        },
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        segment: {
                            borderColor: ctx => {
                                if (ctx.p0.parsed.y === 0 && ctx.p1.parsed.y === 0) {
                                    return '#dc3545';
                                }
                                return '#28a745';
                            },
                            borderDash: ctx => {
                                if (ctx.p0.parsed.y === 0 && ctx.p1.parsed.y === 0) {
                                    return [5, 5];
                                }
                                return [];
                            },
                            borderWidth: ctx => {
                                if (ctx.p0.parsed.y === 0 && ctx.p1.parsed.y === 0) {
                                    return 2;
                                }
                                return 3;
                            }
                        },
                        spanGaps: false
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: { 
                                display: true, 
                                text: 'Total Plant Power (kW)',
                                font: { size: 14, weight: 'bold' },
                                color: 'rgba(255, 255, 255, 0.9)'
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: 'rgba(255, 255, 255, 0.8)',
                                callback: function(value) {
                                    return value >= 1000 ? (value/1000).toFixed(1) + ' MW' : value + ' kW';
                                }
                            }
                        },
                        x: {
                            title: { 
                                display: true, 
                                text: 'Time (Last 5 Hours)',
                                font: { size: 14, weight: 'bold' },
                                color: 'rgba(255, 255, 255, 0.9)'
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: 'rgba(255, 255, 255, 0.8)'
                            }
                        }
                    },
                    plugins: {
                        legend: { 
                            display: true,
                            position: 'top',
                            labels: {
                                font: { size: 12, weight: 'bold' },
                                usePointStyle: true,
                                color: 'rgba(255, 255, 255, 0.9)'
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0,0,0,0.8)',
                            titleColor: 'white',
                            bodyColor: 'white',
                            borderColor: function(context) {
                                const value = context.tooltip.dataPoints[0].parsed.y;
                                return value === 0 ? '#dc3545' : '#28a745';
                            },
                            borderWidth: 2,
                            callbacks: {
                                label: function(context) {
                                    const value = context.parsed.y;
                                    
                                    if (value === 0) {
                                        return [
                                            '⚠️ OFFLINE',
                                            'Power: 0 kW',
                                            'Status: Not sending data'
                                        ];
                                    }
                                    
                                    const displayValue = value >= 1000 ? 
                                        `${(value/1000).toFixed(2)} MW` : 
                                        `${value.toFixed(2)} kW`;
                                    
                                    return [
                                        `✅ ONLINE`,
                                        `Power: ${displayValue}`
                                    ];
                                },
                                title: function(context) {
                                    return `${context[0].label} (Sri Lanka Time)`;
                                },
                                labelTextColor: function(context) {
                                    return context.parsed.y === 0 ? '#ff6b6b' : '#ffffff';
                                }
                            }
                        }
                    }
                }
            });
            
            console.log(`✓ Chart loaded: ${data.labels.length} data points`);
            const offlineCount = data.power.filter(p => p === 0).length;
            if (offlineCount > 0) {
                console.log(`⚠️ ${offlineCount} offline intervals detected`);
            }
        })
        .catch(error => {
            console.error('❌ Error loading chart:', error);
            
            const ctx = document.getElementById('plantChart');
            if (ctx) {
                const parent = ctx.parentElement;
                parent.innerHTML = `
                    <div style="padding: 40px; text-align: center; color: #dc3545;">
                        <h3>⚠️ Error Loading Chart</h3>
                        <p>${error.message}</p>
                        <button onclick="loadPlantChart()" style="padding: 10px 20px; margin-top: 10px; cursor: pointer;">
                            🔄 Retry
                        </button>
                    </div>
                `;
            }
        });
}

/**
 * Add visual legend for chart status colors
 */
function addChartLegend() {
    const legendHTML = `
        <div style="display: flex; justify-content: center; gap: 30px; margin-top: 15px; font-size: 14px; color: rgba(255, 255, 255, 0.9);">
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="width: 30px; height: 3px; background: #28a745;"></div>
                <span>🟢 Online (Running)</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="width: 30px; height: 3px; background: #dc3545; border-style: dashed;"></div>
                <span>🔴 Offline (No Data)</span>
            </div>
        </div>
    `;
    
    const chartContainer = document.getElementById('plantChart')?.parentElement;
    if (chartContainer && !document.getElementById('chart-status-legend')) {
        const legendDiv = document.createElement('div');
        legendDiv.id = 'chart-status-legend';
        legendDiv.innerHTML = legendHTML;
        chartContainer.appendChild(legendDiv);
    }
}

/**
 * Enhanced refresh function with status tracking
 */
let lastRefreshTime = null;
let refreshErrorCount = 0;

function refreshChartWithStatus() {
    const now = new Date();
    lastRefreshTime = now;
    
    console.log(`[${now.toLocaleTimeString()}] 🔄 Refreshing chart...`);
    
    loadPlantChart();
    refreshErrorCount = 0;
}

/**
 * Cleanup on page unload
 */
window.addEventListener('beforeunload', () => {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
    if (plantChart) {
        plantChart.destroy();
    }
});

/**
 * Debug helper
 */
function debugPlantState() {
    console.log('=== CURRENT PLANT STATE ===');
    console.log('Plant ID:', currentPlantId);
    console.log('Total Power:', document.getElementById('totalPower')?.textContent);
    console.log('Online Units:', document.getElementById('onlineUnits')?.textContent);
    console.log('Offline Units:', document.getElementById('offlineUnits')?.textContent);
    console.log('============================');
}

// Make functions available globally
window.loadPlantChart = loadPlantChart;
window.debugPlantState = debugPlantState;
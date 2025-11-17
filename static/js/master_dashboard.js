// static/js/master_dashboard.js

let isFirstLoad = true;

/**
 * Initialize dashboard when page loads
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Master Dashboard initialized');
    
    // Animate initial values on first load
    animateInitialValues();
    
    initializeDashboard();
});

/**
 * Animate all stat values from 0 on initial page load
 */
function animateInitialValues() {
    const totalPowerEl = document.getElementById('totalPower');
    const runningUnitsEl = document.getElementById('runningUnits');
    const standbyUnitsEl = document.getElementById('standbyUnits');
    const activePlantsEl = document.getElementById('activePlants');
    const totalUnitsEl = document.getElementById('totalUnitsDisplay');
    
    // Animate from 0 to current value
    if (totalPowerEl) {
        const targetValue = parseFloat(totalPowerEl.textContent);
        totalPowerEl.innerHTML = '0.00 <span class="unit">MW</span>';
        //totalPowerEl.textContent = '0.00';
        animateValue(totalPowerEl, 0, targetValue, 800, 2);
    }
    
    if (runningUnitsEl) {
        const targetValue = parseInt(runningUnitsEl.textContent);
        runningUnitsEl.textContent = '0';
        animateValue(runningUnitsEl, 0, targetValue, 1200, 0);
    }
    
    if (standbyUnitsEl) {
        const targetValue = parseInt(standbyUnitsEl.textContent);
        standbyUnitsEl.textContent = '0';
        animateValue(standbyUnitsEl, 0, targetValue, 1200, 0);
    }
    
    if (activePlantsEl) {
        const targetValue = parseInt(activePlantsEl.textContent);
        activePlantsEl.textContent = '0';
        animateValue(activePlantsEl, 0, targetValue, 1200, 0);
    }
    
    if (totalUnitsEl) {
        const targetValue = parseInt(totalUnitsEl.textContent);
        totalUnitsEl.textContent = '0';
        animateValue(totalUnitsEl, 0, targetValue, 1200, 0);
    }
    

    // Animate all plant button power values from 0
    const plantPowerElements = document.querySelectorAll('.plant-btn-power');
    plantPowerElements.forEach((powerEl, index) => {
        const targetValue = parseFloat(powerEl.textContent) || 0;
        powerEl.textContent = '0.0 kW';
        // Stagger animations slightly for a cascading effect
        setTimeout(() => {
            animatePlantPower(powerEl, 0, targetValue, 1200);
        }, index * 100); // 100ms delay between each plant
    });

    isFirstLoad = false;
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
        
        element.textContent = current.toFixed(decimals);
    }, 16);
}


/**
 * Main initialization function
 */
function initializeDashboard() {
    updateDateTime();
    setInterval(updateDateTime, 1000); // Update time every second
    setInterval(refreshMasterData, 5000); // Refresh data every 5 seconds
    console.log('✓ Auto-refresh enabled (5s interval)');
}

/**
 * Update date and time display (Sri Lanka timezone)
 */
function updateDateTime() {
    const now = new Date();
    const options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZone: 'Asia/Colombo'
    };
    
    const formattedTime = now.toLocaleString('en-CA', options).replace(',', '');
    const dateTimeElement = document.getElementById('currentDateTime');
    
    if (dateTimeElement) {
        dateTimeElement.textContent = formattedTime;
    }
}

/**
 * Refresh master dashboard data from API
 */
function refreshMasterData() {
    console.log('🔄 Refreshing master data...');
    
    fetch('/api/master/live')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('✓ Data received:', data);
            
            // Validate data structure
            if (!data || typeof data !== 'object') {
                throw new Error('Invalid data format received');
            }
            
            if (data.total_power === undefined) {
                console.warn('⚠️ total_power is undefined in response');
            }
            
            updateMasterStats(data);
            updatePlantButtons(data);
            console.log('✓ Dashboard updated successfully');
        })
        .catch(error => {
            console.error('❌ Error refreshing data:', error);
            showErrorNotification('Failed to refresh data: ' + error.message);
        });
}

/**
 * Update master statistics cards with animation
 */
function updateMasterStats(data) {
    // Update Total Power with animation
    const totalPowerEl = document.getElementById('totalPower');
    if (totalPowerEl) {
        //const currentValue = parseFloat(totalPowerEl.textContent) || 0;
        const totalPower = parseFloat(data.total_power) || 0;
        const powerMW = (totalPower / 1000);
        //totalPowerEl.textContent = powerMW.toFixed(2);
        totalPowerEl.innerHTML = `${powerMW.toFixed(2)} <span class="unit">MW</span>`;
        //animateValue(totalPowerEl, currentValue, powerMW, 1000, 2);
        console.log(`📊 Total Power: ${totalPower} kW = ${powerMW.toFixed(2)} MW`);
    }
    
    // Update Running Units with animation
    const runningUnitsEl = document.getElementById('runningUnits');
    if (runningUnitsEl) {
        //const currentValue = parseInt(runningUnitsEl.textContent) || 0;
        const runningUnits = parseInt(data.total_running_units) || 0;
        //animateValue(runningUnitsEl, currentValue, runningUnits, 800, 0);
        runningUnitsEl.textContent = runningUnits;
        console.log(`🟢 Running Units: ${runningUnits}`);
    }
    
    // Update Standby Units with animation
    const standbyUnitsEl = document.getElementById('standbyUnits');
    if (standbyUnitsEl) {
        //const currentValue = parseInt(standbyUnitsEl.textContent) || 0;
        const standbyUnits = parseInt(data.total_standby_units) || 0;
        //animateValue(standbyUnitsEl, currentValue, standbyUnits, 800, 0);
        standbyUnitsEl.innerHTML = standbyUnits;
        console.log(`🟡 Standby Units: ${standbyUnits}`);
    }
    
    // Update Total Units with animation
    const totalUnitsEl = document.getElementById('totalUnitsDisplay');
    if (totalUnitsEl) {
        //const currentValue = parseInt(totalUnitsEl.textContent) || 0;
        const totalUnits = parseInt(data.total_units) || 0;
        //animateValue(totalUnitsEl, currentValue, totalUnits, 800, 0);
        totalUnitsEl.textContent = totalUnits;
    }
    
    // Update Active Plants with animation
    const activePlantsEl = document.getElementById('activePlants');
    if (activePlantsEl) {
        //const currentValue = parseInt(activePlantsEl.textContent) || 0;
        const activePlants = parseInt(data.active_plants) || 0;
        //animateValue(activePlantsEl, currentValue, activePlants, 800, 0);
        activePlantsEl.textContent = activePlants;
        console.log(`🏭 Active Plants: ${activePlants}`);
    }
}

/**
 * Update plant buttons with live data
 */
function updatePlantButtons(data) {
    // Check if plant_data exists
    if (!data.plant_data) {
        console.warn('⚠️ No plant_data in response');
        return;
    }
    
    const buttons = document.querySelectorAll('.plant-btn');
    
    buttons.forEach(btn => {
        const onclick = btn.getAttribute('onclick');
        if (!onclick) return;
        
        // Extract plant ID from onclick attribute
        const match = onclick.match(/\/plant\/(\d+)/);
        if (!match) return;
        
        const plantId = match[1];
        const plantData = data.plant_data[plantId];
        
        if (!plantData) {
            console.warn(`⚠️ No data for plant ${plantId}`);
            return;
        }
        
        // Determine status based on running/standby units
        let statusClass = 'offline';
        if (plantData.running_units > 0) {
            statusClass = 'online';
        } else if (plantData.standby_units > 0) {
            statusClass = 'standby';
        }
        
        // Update status dot
        const statusDot = btn.querySelector('.status-dot');
        if (statusDot) {
            statusDot.className = `status-dot ${statusClass}`;
        }
        
        // Update info text (R: Running | S: Standby | O: Offline)
        const info = btn.querySelector('.plant-btn-info');
        if (info) {
            info.innerHTML = `
                <span class="status-dot ${statusClass}"></span>
                R: ${plantData.running_units || 0} | S: ${plantData.standby_units || 0} | O: ${plantData.offline_units || 0}
            `;
        }
        
        // Update power display
        const power = btn.querySelector('.plant-btn-power');
        if (power) {
            const plantPower = parseFloat(plantData.total_power) || 0;
            power.textContent = `${plantPower.toFixed(1)} kW`;
            // Only animate on first load, otherwise just update directly
            /*if (isFirstLoad) {
                power.textContent = `${newPower.toFixed(1)} kW`;
            } else {
                const currentPower = parseFloat(power.textContent) || 0;
                // Direct update without animation
                power.textContent = `${newPower.toFixed(1)} kW`;
            }*/
        
        }
        
        console.log(`🏭 Plant ${plantId}: R=${plantData.running_units || 0} S=${plantData.standby_units || 0} O=${plantData.offline_units || 0} P=${(plantData.total_power || 0).toFixed(1)}kW`);
    });
}

/**
 * Animate plant power value changes
 */
function animatePlantPower(element, start, end, duration) {
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
        
        element.textContent = `${current.toFixed(1)} kW`;
    }, 16);
}

/**
 * Show error notification (optional enhancement)
 */
function showErrorNotification(message) {
    // You can implement a toast notification here
    console.error('🔴 ' + message);
}

/**
 * Debug helper - logs current state
 */
function debugCurrentState() {
    console.log('=== CURRENT DASHBOARD STATE ===');
    console.log('Total Power:', document.getElementById('totalPower')?.textContent);
    console.log('Running Units:', document.getElementById('runningUnits')?.textContent);
    console.log('Standby Units:', document.getElementById('standbyUnits')?.textContent);
    console.log('Active Plants:', document.getElementById('activePlants')?.textContent);
    console.log('============================');
}

// Make debug function available globally
window.debugCurrentState = debugCurrentState;
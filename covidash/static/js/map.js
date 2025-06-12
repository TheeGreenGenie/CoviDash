/**
 * COVID-19 Tracker Interactive Map Module
 * 
 * Handles Leaflet map initialization, city markers, popups, and map interactions.
 * Provides dark-themed map with color-coded COVID-19 data visualization.
 */

class CovidMap {
    constructor() {
        console.log('🏗️ CovidMap constructor called');
        this.map = null;
        this.markers = [];
        this.markerLayer = null;
        this.currentData = [];
        this.isInitialized = false;
        
        // Map configuration
        this.config = {
            center: [20, 0],
            zoom: 2,
            minZoom: 2,
            maxZoom: 18,
            zoomControl: false, // We'll add custom controls
            attributionControl: true
        };
        
        console.log('✅ CovidMap configuration set:', this.config);
        
        // Dark tile layer URL with fallback
        this.tileLayer = {
            primary: {
                url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
                attribution: '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>',
                options: {
                    maxZoom: 19,
                    subdomains: 'abcd'
                }
            },
            fallback: {
                url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                attribution: '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors',
                options: {
                    maxZoom: 19
                }
            }
        };
    }

    /**
     * Initialize the map
     * @param {Array} citiesData - Array of city data objects
     */
    async initializeMap(citiesData = []) {
        try {
            console.log('🗺️ Initializing Leaflet map...');
            
            // Create map instance
            this.map = L.map('map', this.config);
            
            console.log('🗺️ Map instance created, adding tiles...');
            
            // Try primary dark tile layer first
            const primaryTiles = L.tileLayer(this.tileLayer.primary.url, {
                attribution: this.tileLayer.primary.attribution,
                ...this.tileLayer.primary.options
            });
            
            // Add error handling for tiles
            primaryTiles.on('tileerror', (e) => {
                console.warn('⚠️ Primary tile layer failed, trying fallback...');
                
                // Remove failed layer and add fallback
                this.map.removeLayer(primaryTiles);
                
                const fallbackTiles = L.tileLayer(this.tileLayer.fallback.url, {
                    attribution: this.tileLayer.fallback.attribution,
                    ...this.tileLayer.fallback.options
                });
                
                fallbackTiles.addTo(this.map);
                console.log('✅ Fallback tiles loaded');
            });
            
            primaryTiles.on('load', () => {
                console.log('✅ Primary tiles loaded successfully');
            });
            
            // Add primary tiles to map
            primaryTiles.addTo(this.map);
            
            // Create marker layer group
            this.markerLayer = L.layerGroup().addTo(this.map);
            
            // Add custom controls
            this.addCustomControls();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Add cities if provided
            if (citiesData && citiesData.length > 0) {
                this.addCityMarkers(citiesData);
            }
            
            this.isInitialized = true;
            console.log('✅ Map initialized successfully');
            
            // Force map to resize and show properly
            setTimeout(() => {
                if (this.map) {
                    this.map.invalidateSize();
                    console.log('🔧 Map size invalidated for proper display');
                }
            }, 100);
            
            // Debug map if tiles don't load quickly
            setTimeout(() => {
                this.debugMap();
            }, 2000);
            
            // Update map status
            this.updateMapStatus();
            
        } catch (error) {
            console.error('❌ Failed to initialize map:', error);
            throw error;
        }
    }

    /**
     * Add city markers to the map
     * @param {Array} citiesData - Array of city data objects
     */
    addCityMarkers(citiesData) {
        try {
            console.log(`📍 Adding ${citiesData.length} city markers...`);
            
            // Clear existing markers
            this.clearMarkers();
            
            this.currentData = citiesData;
            
            citiesData.forEach((city, index) => {
                try {
                    const marker = this.createCityMarker(city);
                    if (marker) {
                        this.markers.push(marker);
                        this.markerLayer.addLayer(marker);
                    }
                } catch (error) {
                    console.error(`❌ Failed to create marker for ${city.name}:`, error);
                }
            });
            
            console.log(`✅ Added ${this.markers.length} markers to map`);
            this.updateMapStatus();
            
        } catch (error) {
            console.error('❌ Failed to add city markers:', error);
            throw error;
        }
    }

    /**
     * Create a marker for a location (city, state, or country)
     * @param {Object} locationData - Location data object
     * @returns {L.CircleMarker} - Leaflet circle marker
     */
    createCityMarker(locationData) {
        try {
            // Validate location data
            if (!this.validateCityData(locationData)) {
                console.warn('⚠️ Invalid location data for:', locationData.name || 'Unknown');
                this.debugLocationData(locationData);
                return null;
            }
            
            const { 
                latitude, 
                longitude, 
                marker_color, 
                infection_rate, 
                risk_level,
                type = 'city',
                marker_size_multiplier = 1.0
            } = locationData;
            
            // Calculate marker size based on infection rate and type
            const radius = this.calculateMarkerSize(infection_rate, type, marker_size_multiplier);
            
            // Create circle marker with custom styling
            const marker = L.circleMarker([latitude, longitude], {
                radius: radius,
                fillColor: marker_color,
                color: marker_color,
                weight: type === 'country' ? 3 : type === 'state' ? 2.5 : 2,
                opacity: type === 'country' ? 0.9 : 0.8,
                fillOpacity: type === 'country' ? 0.7 : 0.6,
                className: `location-marker ${type}-marker risk-${risk_level}`
            });
            
            // Create popup content
            const popupContent = this.createPopupContent(locationData);
            marker.bindPopup(popupContent, {
                maxWidth: 300,
                className: `custom-popup ${type}-popup`
            });
            
            // Add hover effects
            this.addMarkerHoverEffects(marker, locationData);
            
            // Store location data with marker
            marker.locationData = locationData;
            
            return marker;
            
        } catch (error) {
            console.error(`❌ Failed to create marker for location:`, error);
            return null;
        }
    }

    /**
     * Calculate marker size based on infection rate
     * @param {number} infectionRate - Infection rate per 100k
     * @returns {number} - Marker radius
     */
    calculateMarkerSize(infectionRate, locationType = 'city', sizeMultiplier = 1.0) {
        // Base size: 6px, max size: 20px
        let baseSize = 6;
        let maxSize = 20;
        
        if (locationType === 'country') {
            baseSize = 8;
            maxSize = 25;
        } else if (locationType === 'state') {
            baseSize = 7;
            maxSize = 22;
        }
        
        // Apply multiplier
        baseSize *= sizeMultiplier;
        maxSize *= sizeMultiplier;
        
        const scaleFactor = Math.log10(Math.max(infectionRate, 1)) / 4; // Log scale
        
        return Math.min(baseSize + (scaleFactor * (maxSize - baseSize)), maxSize);
    }

    /**
     * Create popup content for a location marker
     * @param {Object} locationData - Location data object
     * @returns {string} - HTML content for popup
     */
    createPopupContent(locationData) {
        // Safely extract data with fallbacks
        const displayName = locationData.display_name || locationData.name || 'Unknown Location';
        const cases = locationData.cases_formatted || locationData.cases || 'N/A';
        const deaths = locationData.deaths_formatted || locationData.deaths || 'N/A';
        const active = locationData.active || 0;
        const population = locationData.population_formatted || locationData.population || 'N/A';
        const infectionRate = locationData.infection_rate || 0;
        const mortalityRate = locationData.mortality_rate || 0;
        const recoveryRate = locationData.recovery_rate || 0;
        const riskLevel = locationData.risk_level || 'unknown';
        const type = locationData.type || 'city';
        
        // Handle recovery data - check if we should use estimation
        let recoveredDisplay, hasReliableRecoveryData, isUsingEstimation = false;
        const recoveredNum = locationData.recovered || 0;
        const totalCases = locationData.cases || 0;
        const isEstimated = locationData.estimated === true;
        const estimationValue = locationData.estimation;
        const estimationFormatted = locationData.estimation_formatted;
        
        if (isEstimated && estimationValue) {
            // Use estimation if the estimated flag is true
            recoveredDisplay = estimationFormatted || estimationValue.toString();
            hasReliableRecoveryData = false;
            isUsingEstimation = true;
        } else {
            // Use original recovery data
            recoveredDisplay = locationData.recovered_formatted || recoveredNum.toString();
            hasReliableRecoveryData = (recoveredNum / totalCases) > 0.1; // If >10% recovered
        }
        
        // Safe risk level processing
        const riskLevelClass = `risk-${riskLevel}`;
        const riskLevelText = riskLevel && riskLevel.charAt ? 
            riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1) : 'Unknown';
        
        // Format active cases for display
        const activeFormatted = active > 1000000 ? 
            `${(active / 1000000).toFixed(1)}M` : 
            active > 1000 ? 
            `${(active / 1000).toFixed(1)}K` : 
            active.toString();
        
        return `
            <div class="popup-content">
                <h3 class="popup-title">${displayName}</h3>
                
                ${isUsingEstimation ? `
                <div style="background: #1a365d; padding: 6px 12px; border-radius: 6px; margin-bottom: 10px; text-align: center; font-size: 0.85rem; color: #63b3ed; border: 1px solid #3182ce;">
                    📊 Using Estimated Recovery Data
                </div>
                ` : ''}
                
                <div class="popup-risk-level ${riskLevelClass}">
                    <span class="risk-indicator">●</span>
                    <span class="risk-text">${riskLevelText} Risk</span>
                </div>
                
                <div class="popup-stats">
                    <div class="popup-stat">
                        <span class="popup-stat-label">Total Cases</span>
                        <span class="popup-stat-value">${cases}</span>
                    </div>
                    <div class="popup-stat">
                        <span class="popup-stat-label">Deaths</span>
                        <span class="popup-stat-value">${deaths}</span>
                    </div>
                    <div class="popup-stat" ${isUsingEstimation ? 'style="background: #2a4365; border: 1px solid #3182ce;"' : ''}>
                        <span class="popup-stat-label">
                            ${isUsingEstimation ? '🔮 Estimated Recovered' : 'Recovered'}
                        </span>
                        <span class="popup-stat-value">${recoveredDisplay}</span>
                    </div>
                    <div class="popup-stat">
                        <span class="popup-stat-label">Active Cases</span>
                        <span class="popup-stat-value">${activeFormatted}</span>
                    </div>
                    <div class="popup-stat">
                        <span class="popup-stat-label">Population</span>
                        <span class="popup-stat-value">${population}</span>
                    </div>
                </div>
                
                <div class="popup-rates">
                    <div class="popup-rate">
                        <span class="rate-label">Current Risk Rate:</span>
                        <span class="rate-value">${infectionRate} per 100k</span>
                    </div>
                    <div class="popup-rate">
                        <span class="rate-label">Mortality Rate:</span>
                        <span class="rate-value">${mortalityRate}%</span>
                    </div>
                    <div class="popup-rate" ${!hasReliableRecoveryData ? 'style="opacity: 0.7;"' : ''}>
                        <span class="rate-label">Recovery Rate:</span>
                        <span class="rate-value">${recoveryRate}% ${isUsingEstimation ? '(est.)' : hasReliableRecoveryData ? '' : '(proj.)'}</span>
                    </div>
                </div>
                
                ${isUsingEstimation ? `
                <div class="popup-disclaimer">
                    <small style="color: #63b3ed; font-size: 0.75rem; font-style: italic;">
                        📈 Recovery data estimated based on global patterns
                    </small>
                </div>
                ` : !hasReliableRecoveryData ? `
                <div class="popup-disclaimer">
                    <small style="color: #a0aec0; font-size: 0.75rem; font-style: italic;">
                        * Active cases projected due to limited recovery data
                    </small>
                </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Add hover effects to markers
     * @param {L.CircleMarker} marker - The marker
     * @param {Object} city - City data
     */
    addMarkerHoverEffects(marker, city) {
        marker.on('mouseover', (e) => {
            const layer = e.target;
            layer.setStyle({
                weight: 3,
                opacity: 1,
                fillOpacity: 0.8,
                radius: layer.options.radius * 1.2
            });
            
            // Update status bar with city info
            this.showCityHoverInfo(city);
        });
        
        marker.on('mouseout', (e) => {
            const layer = e.target;
            layer.setStyle({
                weight: 2,
                opacity: 0.8,
                fillOpacity: 0.6,
                radius: this.calculateMarkerSize(city.infection_rate)
            });
            
            // Clear hover info
            this.clearCityHoverInfo();
        });
        
        marker.on('click', (e) => {
            // Zoom to city when clicked
            this.map.setView(e.latlng, Math.max(this.map.getZoom(), 6), {
                animate: true,
                duration: 0.5
            });
        });
    }

    /**
     * Show city information on hover
     * @param {Object} city - City data
     */
    showCityHoverInfo(city) {
        const statusElement = document.getElementById('map-status');
        if (statusElement) {
            statusElement.innerHTML = `
                <div class="status-item">
                    <span class="status-label">Hovering:</span>
                    <span class="status-value">${city.display_name}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Cases:</span>
                    <span class="status-value">${city.cases_formatted}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Rate:</span>
                    <span class="status-value">${city.infection_rate} per 100k</span>
                </div>
            `;
        }
    }

    /**
     * Clear city hover information
     */
    clearCityHoverInfo() {
        this.updateMapStatus();
    }

    /**
     * Add custom map controls
     */
    addCustomControls() {
        // Custom zoom control
        const zoomControl = L.control.zoom({
            position: 'bottomright'
        });
        zoomControl.addTo(this.map);
        
        // Custom scale control
        const scaleControl = L.control.scale({
            position: 'bottomleft',
            imperial: false
        });
        scaleControl.addTo(this.map);
    }

    /**
     * Set up map event listeners
     */
    setupEventListeners() {
        // Update zoom level display
        this.map.on('zoomend', () => {
            this.updateMapStatus();
        });
        
        // Handle map clicks
        this.map.on('click', (e) => {
            console.log(`🗺️ Map clicked at: ${e.latlng.lat.toFixed(4)}, ${e.latlng.lng.toFixed(4)}`);
        });
        
        // Handle map ready
        this.map.whenReady(() => {
            console.log('🗺️ Map is ready');
            this.updateMapStatus();
        });
    }

    /**
     * Update map status display
     */
    updateMapStatus() {
        const citiesLoadedElement = document.getElementById('cities-loaded');
        const currentZoomElement = document.getElementById('current-zoom');
        
        if (citiesLoadedElement) {
            citiesLoadedElement.textContent = this.markers.length.toString();
        }
        
        if (currentZoomElement && this.map) {
            currentZoomElement.textContent = this.map.getZoom().toString();
        }
    }

    /**
     * Validate location data structure
     * @param {Object} locationData - Location data object
     * @returns {boolean} - Whether location data is valid
     */
    validateCityData(locationData) {
        const requiredFields = ['name', 'latitude', 'longitude', 'marker_color', 'infection_rate'];
        
        for (const field of requiredFields) {
            if (!(field in locationData)) {
                console.warn(`❌ Missing required field: ${field}`, locationData);
                return false;
            }
        }
        
        // Validate coordinate ranges
        if (locationData.latitude < -90 || locationData.latitude > 90) {
            console.warn(`❌ Invalid latitude: ${locationData.latitude}`);
            return false;
        }
        
        if (locationData.longitude < -180 || locationData.longitude > 180) {
            console.warn(`❌ Invalid longitude: ${locationData.longitude}`);
            return false;
        }
        
        return true;
    }

    /**
     * Debug location data for troubleshooting
     * @param {Object} locationData - Location data object
     */
    debugLocationData(locationData) {
        console.log('🔍 Debugging location data:', {
            name: locationData.name,
            latitude: locationData.latitude,
            longitude: locationData.longitude,
            marker_color: locationData.marker_color,
            infection_rate: locationData.infection_rate,
            type: locationData.type,
            hasAllFields: {
                name: 'name' in locationData,
                latitude: 'latitude' in locationData,
                longitude: 'longitude' in locationData,
                marker_color: 'marker_color' in locationData,
                infection_rate: 'infection_rate' in locationData
            }
        });
    }

    /**
     * Clear all markers from the map
     */
    clearMarkers() {
        if (this.markerLayer) {
            this.markerLayer.clearLayers();
        }
        this.markers = [];
        console.log('🗑️ Cleared all markers');
    }

    /**
     * Update map with new data
     * @param {Array} citiesData - New cities data
     */
    updateMapData(citiesData) {
        if (!this.isInitialized) {
            console.warn('⚠️ Map not initialized, cannot update data');
            return;
        }
        
        console.log('🔄 Updating map with new data...');
        this.addCityMarkers(citiesData);
    }

    /**
     * Fit map view to show all markers
     */
    fitToMarkers() {
        if (this.markers.length === 0) {
            return;
        }
        
        const group = new L.featureGroup(this.markers);
        this.map.fitBounds(group.getBounds(), {
            padding: [20, 20],
            maxZoom: 10
        });
    }

    /**
     * Reset map view to initial position
     */
    resetView() {
        this.map.setView(this.config.center, this.config.zoom, {
            animate: true,
            duration: 1
        });
    }

    /**
     * Get map instance
     * @returns {L.Map} - Leaflet map instance
     */
    getMap() {
        return this.map;
    }

    /**
     * Get current markers
     * @returns {Array} - Array of markers
     */
    getMarkers() {
        return this.markers;
    }

    /**
     * Filter markers by risk level
     * @param {Array} riskLevels - Array of risk levels to show
     */
    filterMarkersByRisk(riskLevels) {
        this.markers.forEach(marker => {
            const city = marker.cityData;
            if (riskLevels.includes(city.risk_level)) {
                marker.addTo(this.markerLayer);
            } else {
                this.markerLayer.removeLayer(marker);
            }
        });
    }

    /**
     * Show all markers
     */
    showAllMarkers() {
        this.markers.forEach(marker => {
            marker.addTo(this.markerLayer);
        });
    }

    /**
     * Get map statistics
     * @returns {Object} - Map statistics
     */
    getMapStats() {
        return {
            totalMarkers: this.markers.length,
            currentZoom: this.map ? this.map.getZoom() : null,
            mapCenter: this.map ? this.map.getCenter() : null,
            mapBounds: this.map ? this.map.getBounds() : null,
            isInitialized: this.isInitialized
        };
    }

    /**
     * Debug map issues
     */
    debugMap() {
        console.log('🔍 Map Debug Info:');
        console.log('- Map instance:', this.map);
        console.log('- Map container:', document.getElementById('map'));
        console.log('- Map size:', this.map ? this.map.getSize() : 'No map');
        console.log('- Map zoom:', this.map ? this.map.getZoom() : 'No map');
        console.log('- Map center:', this.map ? this.map.getCenter() : 'No map');
        console.log('- Markers count:', this.markers.length);
        
        // Check if Leaflet CSS is loaded
        const leafletCSS = document.querySelector('link[href*="leaflet"]');
        console.log('- Leaflet CSS loaded:', !!leafletCSS);
        
        // Check container size
        const mapElement = document.getElementById('map');
        if (mapElement) {
            const rect = mapElement.getBoundingClientRect();
            console.log('- Map element size:', rect.width, 'x', rect.height);
        }
        
        // Force map resize
        if (this.map) {
            console.log('🔧 Forcing map resize...');
            setTimeout(() => {
                this.map.invalidateSize();
            }, 100);
        }
    }
}


// Global map instance
console.log('🌍 Creating global CovidMap instance...');
window.covidMap = new CovidMap();
console.log('✅ Global map instance created:', window.covidMap);

/**
 * Initialize map with cities data
 * @param {Array} citiesData - Array of city data objects
 */
async function initializeMap(citiesData) {
    console.log('🚀 initializeMap function called with', citiesData ? citiesData.length : 0, 'cities');
    try {
        if (!window.covidMap) {
            console.error('❌ Global map instance not found');
            throw new Error('Global map instance not available');
        }
        
        console.log('📍 Calling covidMap.initializeMap...');
        await window.covidMap.initializeMap(citiesData);
        console.log('✅ Map initialization completed successfully');
    } catch (error) {
        console.error('❌ Map initialization failed:', error);
        throw error;
    }
}

/**
 * Update map data
 * @param {Array} citiesData - New cities data
 */
function updateMapData(citiesData) {
    console.log('🔄 updateMapData function called with', citiesData ? citiesData.length : 0, 'cities');
    try {
        if (!window.covidMap) {
            console.error('❌ Global map instance not found for update');
            throw new Error('Global map instance not available');
        }
        
        window.covidMap.updateMapData(citiesData);
        if (typeof showNotification === 'function') {
            showNotification('Map updated with latest data', 'success');
        }
        console.log('✅ Map data updated successfully');
    } catch (error) {
        console.error('❌ Failed to update map data:', error);
        if (typeof showNotification === 'function') {
            showNotification('Failed to update map', 'error');
        }
    }
}

/**
 * Export map functions for global access
 */
console.log('📤 Exporting map functions to global scope...');
window.initializeMap = initializeMap;
window.updateMapData = updateMapData;
console.log('✅ Map functions exported:', {
    initializeMap: typeof window.initializeMap,
    updateMapData: typeof window.updateMapData
});

// Add custom popup styles
const popupStyles = `
.popup-content {
    font-family: inherit;
    color: var(--text-primary, #f0f6fc);
    min-width: 250px;
}

.popup-title {
    color: var(--accent-blue, #58a6ff) !important;
    margin-bottom: 8px !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    text-align: center;
}

.popup-risk-level {
    text-align: center;
    padding: 4px 8px;
    border-radius: 4px;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
}

.popup-risk-level.risk-critical {
    background-color: rgba(128, 0, 38, 0.2);
    border: 1px solid #800026;
}

.popup-risk-level.risk-high {
    background-color: rgba(189, 0, 38, 0.2);
    border: 1px solid #BD0026;
}

.popup-risk-level.risk-medium {
    background-color: rgba(253, 141, 60, 0.2);
    border: 1px solid #FD8D3C;
}

.popup-risk-level.risk-low {
    background-color: rgba(254, 178, 76, 0.2);
    border: 1px solid #FEB24C;
}

.risk-indicator {
    font-size: 1.2rem;
}

.risk-text {
    font-weight: 600;
    font-size: 0.9rem;
}

.popup-stats {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 8px !important;
    margin: 12px 0 !important;
}

.popup-rates {
    margin-top: 12px;
    padding-top: 8px;
    border-top: 1px solid var(--border-primary, #30363d);
}

.popup-rate {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
    font-size: 0.85rem;
}

.rate-label {
    color: var(--text-tertiary, #6e7681);
}

.rate-value {
    font-weight: 600;
    color: var(--text-primary, #f0f6fc);
}
`;

// Inject popup styles
const mapStyleSheet = document.createElement('style');
mapStyleSheet.textContent = popupStyles;
document.head.appendChild(mapStyleSheet);

/**
 * Test basic Leaflet functionality
 */
function testLeafletBasic() {
    console.log('🧪 Testing basic Leaflet functionality...');
    
    // Check if Leaflet is loaded
    if (typeof L === 'undefined') {
        console.error('❌ Leaflet library not loaded!');
        return false;
    }
    
    console.log('✅ Leaflet version:', L.version);
    
    // Check if map container exists
    const mapElement = document.getElementById('map');
    if (!mapElement) {
        console.error('❌ Map container element not found!');
        return false;
    }
    
    console.log('✅ Map container found');
    
    // Check container size
    const rect = mapElement.getBoundingClientRect();
    console.log('📏 Container size:', rect.width, 'x', rect.height);
    
    if (rect.width === 0 || rect.height === 0) {
        console.error('❌ Map container has zero size!');
        return false;
    }
    
    console.log('✅ All basic tests passed');
    return true;
}

// Export functions for global access
window.testLeafletBasic = testLeafletBasic;

console.log('🗺️ COVID Map module loaded successfully');

// Auto-run basic test when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('🔍 DOM loaded - running Leaflet test...');
    setTimeout(() => {
        if (typeof testLeafletBasic === 'function') {
            testLeafletBasic();
        } else {
            console.error('❌ testLeafletBasic function not defined');
        }
    }, 500);
});
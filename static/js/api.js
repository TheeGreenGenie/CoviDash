/**
 * COVID-19 Tracker API Communication Module
 * 
 * Handles all communication with the Flask backend API endpoints.
 * Provides functions for fetching data, handling errors, and managing cache.
 */

class CovidAPI {
    constructor() {
        this.baseURL = window.location.origin;
        this.endpoints = {
            covidData: '/api/covid-data',
            health: '/api/health',
            statistics: '/api/statistics',
            refresh: '/api/refresh',
            cacheInfo: '/api/cache/info',
            cacheClear: '/api/cache/clear'
        };
        
        this.cache = new Map();
        this.lastFetch = null;
        this._isLoading = false; // Fixed: use private variable to avoid conflicts
    }

    /**
     * Generic fetch method with error handling and retries
     * @param {string} url - The URL to fetch
     * @param {object} options - Fetch options
     * @param {number} retries - Number of retry attempts
     * @returns {Promise<object>} - The response data
     */
    async fetchWithRetry(url, options = {}, retries = 3) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            timeout: 30000
        };

        const fetchOptions = { ...defaultOptions, ...options };

        for (let attempt = 1; attempt <= retries; attempt++) {
            try {
                console.log(`🌐 Fetching ${url} (attempt ${attempt}/${retries})`);
                
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), fetchOptions.timeout);
                
                const response = await fetch(url, {
                    ...fetchOptions,
                    signal: controller.signal
                });

                clearTimeout(timeoutId);

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                console.log(`✅ Successfully fetched ${url}`);
                return data;

            } catch (error) {
                console.warn(`⚠️ Attempt ${attempt} failed for ${url}:`, error.message);
                
                if (attempt === retries) {
                    throw new Error(`Failed to fetch ${url} after ${retries} attempts: ${error.message}`);
                }
                
                // Wait before retrying (exponential backoff)
                const delay = Math.min(1000 * Math.pow(2, attempt - 1), 5000);
                await this.sleep(delay);
            }
        }
    }

    /**
     * Sleep utility for delays
     * @param {number} ms - Milliseconds to sleep
     * @returns {Promise<void>}
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Fetch COVID-19 data for the map
     * @param {boolean} useCache - Whether to use cached data if available
     * @returns {Promise<object>} - COVID data with cities, statistics, and metadata
     */
    async getCovidData(useCache = true) {
        const cacheKey = 'covid-data';
        
        // Check cache first
        if (useCache && this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            const age = Date.now() - cached.timestamp;
            const maxAge = 5 * 60 * 1000; // 5 minutes
            
            if (age < maxAge) {
                console.log('📦 Using cached COVID data');
                return cached.data;
            }
        }

        try {
            this._isLoading = true; // Fixed: use private variable
            const data = await this.fetchWithRetry(`${this.baseURL}${this.endpoints.covidData}`);
            
            // Cache the data
            this.cache.set(cacheKey, {
                data: data,
                timestamp: Date.now()
            });
            
            this.lastFetch = new Date().toISOString();
            return data;

        } catch (error) {
            console.error('❌ Failed to fetch COVID data:', error);
            throw error;
        } finally {
            this._isLoading = false; // Fixed: use private variable
        }
    }

    /**
     * Get health status of the application
     * @returns {Promise<object>} - Health status data
     */
    async getHealthStatus() {
        try {
            return await this.fetchWithRetry(`${this.baseURL}${this.endpoints.health}`);
        } catch (error) {
            console.error('❌ Failed to fetch health status:', error);
            return {
                status: 'unhealthy',
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * Get detailed statistics
     * @returns {Promise<object>} - Statistics data
     */
    async getStatistics() {
        try {
            return await this.fetchWithRetry(`${this.baseURL}${this.endpoints.statistics}`);
        } catch (error) {
            console.error('❌ Failed to fetch statistics:', error);
            throw error;
        }
    }

    /**
     * Trigger manual data refresh
     * @returns {Promise<object>} - Refresh result
     */
    async refreshData() {
        try {
            console.log('🔄 Triggering manual data refresh...');
            const result = await this.fetchWithRetry(`${this.baseURL}${this.endpoints.refresh}`, {
                method: 'POST'
            });
            
            // Clear cache after successful refresh
            this.clearCache();
            
            console.log('✅ Data refresh completed:', result.message);
            return result;

        } catch (error) {
            console.error('❌ Failed to refresh data:', error);
            throw error;
        }
    }

    /**
     * Get cache information
     * @returns {Promise<object>} - Cache info
     */
    async getCacheInfo() {
        try {
            return await this.fetchWithRetry(`${this.baseURL}${this.endpoints.cacheInfo}`);
        } catch (error) {
            console.error('❌ Failed to fetch cache info:', error);
            throw error;
        }
    }

    /**
     * Clear server cache
     * @returns {Promise<object>} - Clear result
     */
    async clearServerCache() {
        try {
            const result = await this.fetchWithRetry(`${this.baseURL}${this.endpoints.cacheClear}`, {
                method: 'POST'
            });
            
            // Also clear local cache
            this.clearCache();
            
            return result;
        } catch (error) {
            console.error('❌ Failed to clear server cache:', error);
            throw error;
        }
    }

    /**
     * Clear local cache
     */
    clearCache() {
        this.cache.clear();
        console.log('🗑️ Local cache cleared');
    }

    /**
     * Get loading state
     * @returns {boolean} - Whether API is currently loading
     */
    isLoading() {
        return this._isLoading; // Fixed: use private variable
    }

    /**
     * Get cache statistics
     * @returns {object} - Local cache stats
     */
    getCacheStats() {
        const stats = {
            size: this.cache.size,
            entries: [],
            lastFetch: this.lastFetch
        };

        for (const [key, value] of this.cache.entries()) {
            stats.entries.push({
                key: key,
                timestamp: value.timestamp,
                age: Date.now() - value.timestamp,
                dataSize: JSON.stringify(value.data).length
            });
        }

        return stats;
    }
}

// Global API instance
window.covidAPI = new CovidAPI();

/**
 * Initialize application with data
 */
async function initializeApp() {
    try {
        console.log('🚀 Initializing COVID-19 Tracker...');
        console.log('🔍 Checking available functions:', {
            showLoading: typeof showLoading,
            hideLoading: typeof hideLoading,
            showError: typeof showError,
            initializeMap: typeof window.initializeMap,
            updateMapData: typeof window.updateMapData
        });
        
        // Show loading screen
        if (typeof showLoading === 'function') {
            console.log('📺 Showing loading screen...');
            showLoading();
        } else {
            console.warn('⚠️ showLoading function not available');
        }

        console.log('🏥 Checking API health...');
        // Check API health first
        const health = await window.covidAPI.getHealthStatus();
        console.log('🏥 API Health:', health.status);

        if (health.status !== 'healthy' && health.status !== 'degraded') {
            throw new Error('API is not healthy');
        }

        console.log('📊 Fetching COVID data...');
        // Fetch COVID data
        const covidData = await window.covidAPI.getCovidData();
        
        if (!covidData || !covidData.cities || covidData.cities.length === 0) {
            throw new Error('No COVID data available');
        }

        console.log(`📊 Loaded data for ${covidData.cities.length} cities`);

        console.log('🖥️ Updating UI with data...');
        // Update UI with data
        updateUI(covidData);

        console.log('🗺️ Initializing map...');
        // Initialize map with data
        if (typeof window.initializeMap === 'function') {
            console.log('✅ Found initializeMap function, calling it...');
            await window.initializeMap(covidData.cities);
            console.log('✅ Map initialization completed');
        } else {
            console.error('❌ initializeMap function not found - map.js may not be loaded');
            console.log('🔍 Available window functions:', Object.keys(window).filter(key => key.includes('map') || key.includes('Map')));
            throw new Error('Map initialization function not available');
        }

        // Hide loading screen
        if (typeof hideLoading === 'function') {
            console.log('📺 Hiding loading screen...');
            hideLoading();
        } else {
            console.warn('⚠️ hideLoading function not available');
        }

        console.log('✅ Application initialized successfully');

    } catch (error) {
        console.error('❌ Failed to initialize application:', error);
        console.log('🔍 Error stack:', error.stack);
        
        if (typeof showError === 'function') {
            showError(`Failed to load COVID-19 data: ${error.message}`);
        } else {
            console.error('⚠️ showError function not available, cannot display error to user');
        }
    }
}

/**
 * Refresh data and update the application
 */
async function refreshData() {
    try {
        console.log('🔄 Refreshing application data...');
        
        // Update refresh button state
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<span class="refresh-icon">⏳</span> Refreshing...';
        }

        // Trigger server refresh
        const refreshResult = await window.covidAPI.refreshData();
        
        // Fetch updated data
        const covidData = await window.covidAPI.getCovidData(false); // Force fresh fetch
        
        // Update UI
        updateUI(covidData);
        
        // Update map
        if (typeof window.updateMapData === 'function') {
            window.updateMapData(covidData.cities);
        } else {
            console.warn('⚠️ updateMapData function not available');
        }

        console.log('✅ Data refresh completed');
        
        // Show success message briefly
        if (refreshBtn) {
            refreshBtn.innerHTML = '<span class="refresh-icon">✅</span> Updated!';
            setTimeout(() => {
                refreshBtn.innerHTML = '<span class="refresh-icon">🔄</span> Refresh';
                refreshBtn.disabled = false;
            }, 2000);
        }

    } catch (error) {
        console.error('❌ Failed to refresh data:', error);
        
        // Reset refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.innerHTML = '<span class="refresh-icon">❌</span> Failed';
            refreshBtn.disabled = false;
            
            setTimeout(() => {
                refreshBtn.innerHTML = '<span class="refresh-icon">🔄</span> Refresh';
            }, 3000);
        }
        
        // Show error message
        alert(`Failed to refresh data: ${error.message}`);
    }
}

/**
 * Update UI elements with COVID data
 * @param {object} data - COVID data object
 */
function updateUI(data) {
    try {
        const { cities, statistics, metadata } = data;
        
        // Update header statistics
        updateElement('total-cases', statistics.total_cases_formatted || '0');
        updateElement('total-deaths', statistics.total_deaths_formatted || '0');
        updateElement('total-cities', cities.length.toString());
        
        // Update last updated info
        const lastUpdated = metadata.last_updated || data.last_update || 'Unknown';
        updateElement('last-updated', `Last updated: ${formatDateTime(lastUpdated)}`);
        
        // Update detailed statistics
        updateElement('avg-infection-rate', `${statistics.average_infection_rate || 0} per 100k`);
        updateElement('highest-rate', `${statistics.highest_infection_rate || 0} per 100k`);
        updateElement('lowest-rate', `${statistics.lowest_infection_rate || 0} per 100k`);
        
        // Update risk distribution
        updateRiskDistribution(statistics.risk_distribution || {});
        
        // Update map status
        updateElement('cities-loaded', cities.length.toString());
        
        console.log('📋 UI updated with latest data');
        
    } catch (error) {
        console.error('❌ Failed to update UI:', error);
    }
}

/**
 * Update risk distribution bars
 * @param {object} riskDist - Risk distribution data
 */
function updateRiskDistribution(riskDist) {
    const total = Object.values(riskDist).reduce((sum, count) => sum + count, 0);
    
    if (total === 0) return;
    
    const riskLevels = ['critical', 'high', 'medium', 'low'];
    
    riskLevels.forEach(level => {
        const count = riskDist[level] || 0;
        const percentage = (count / total) * 100;
        
        const barElement = document.getElementById(`${level}-bar`);
        const countElement = document.getElementById(`${level}-count`);
        
        if (barElement) {
            barElement.style.width = `${percentage}%`;
        }
        
        if (countElement) {
            countElement.textContent = count.toString();
        }
    });
}

/**
 * Update element text content safely
 * @param {string} id - Element ID
 * @param {string} content - New content
 */
function updateElement(id, content) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = content;
    }
}

/**
 * Format date/time string for display
 * @param {string} dateString - ISO date string
 * @returns {string} - Formatted date/time
 */
function formatDateTime(dateString) {
    try {
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            timeZoneName: 'short'
        });
    } catch (error) {
        return dateString;
    }
}

/**
 * Show notification message
 * @param {string} message - Message to show
 * @param {string} type - Type of notification (success, error, info)
 * @param {number} duration - Duration in milliseconds
 */
function showNotification(message, type = 'info', duration = 3000) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Style the notification
    Object.assign(notification.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        background: type === 'success' ? '#3fb950' : type === 'error' ? '#ff7b72' : '#58a6ff',
        color: 'white',
        padding: '12px 20px',
        borderRadius: '6px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.4)',
        zIndex: '10001',
        fontSize: '14px',
        fontWeight: '500',
        maxWidth: '300px',
        wordWrap: 'break-word',
        animation: 'slideInRight 0.3s ease-out'
    });
    
    // Add to document
    document.body.appendChild(notification);
    
    // Remove after duration
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-in';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, duration);
}

/**
 * Handle API errors with user feedback
 * @param {Error} error - The error object
 * @param {string} context - Context where error occurred
 */
function handleAPIError(error, context = 'API request') {
    console.error(`❌ ${context} failed:`, error);
    
    let userMessage = 'An unexpected error occurred';
    
    if (error.message.includes('Failed to fetch')) {
        userMessage = 'Unable to connect to server. Please check your internet connection.';
    } else if (error.message.includes('HTTP 503')) {
        userMessage = 'Service temporarily unavailable. Please try again later.';
    } else if (error.message.includes('HTTP 500')) {
        userMessage = 'Server error occurred. Please try refreshing the page.';
    } else if (error.message.includes('timeout')) {
        userMessage = 'Request timed out. Please try again.';
    }
    
    showNotification(userMessage, 'error', 5000);
}

/**
 * Validate COVID data structure
 * @param {object} data - Data to validate
 * @returns {boolean} - Whether data is valid
 */
function validateCovidData(data) {
    if (!data || typeof data !== 'object') {
        return false;
    }
    
    // Check required top-level properties
    if (!data.cities || !Array.isArray(data.cities)) {
        return false;
    }
    
    if (!data.statistics || typeof data.statistics !== 'object') {
        return false;
    }
    
    if (!data.metadata || typeof data.metadata !== 'object') {
        return false;
    }
    
    // Check if we have at least some cities
    if (data.cities.length === 0) {
        return false;
    }
    
    // Validate sample city structure
    const sampleCity = data.cities[0];
    const requiredFields = ['name', 'country', 'latitude', 'longitude', 'cases', 'marker_color'];
    
    for (const field of requiredFields) {
        if (!(field in sampleCity)) {
            console.warn(`❌ Missing required field: ${field}`);
            return false;
        }
    }
    
    return true;
}

/**
 * Get performance metrics
 * @returns {object} - Performance data
 */
function getPerformanceMetrics() {
    const cacheStats = window.covidAPI.getCacheStats();
    
    return {
        cacheStats: cacheStats,
        apiStatus: {
            isLoading: window.covidAPI.isLoading,
            lastFetch: window.covidAPI.lastFetch
        },
        browserInfo: {
            userAgent: navigator.userAgent,
            language: navigator.language,
            online: navigator.onLine,
            cookieEnabled: navigator.cookieEnabled
        },
        timing: performance.timing ? {
            domContentLoaded: performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart,
            loadComplete: performance.timing.loadEventEnd - performance.timing.navigationStart
        } : null
    };
}

/**
 * Auto-refresh data periodically
 * @param {number} intervalMinutes - Refresh interval in minutes
 */
function startAutoRefresh(intervalMinutes = 30) {
    console.log(`⏰ Starting auto-refresh every ${intervalMinutes} minutes`);
    
    setInterval(async () => {
        try {
            console.log('⏰ Auto-refresh triggered');
            await refreshData();
            showNotification('Data automatically updated', 'success', 2000);
        } catch (error) {
            console.error('❌ Auto-refresh failed:', error);
            // Don't show error notification for auto-refresh failures
        }
    }, intervalMinutes * 60 * 1000);
}

/**
 * Monitor API health periodically
 * @param {number} intervalMinutes - Check interval in minutes
 */
function startHealthMonitoring(intervalMinutes = 5) {
    console.log(`💓 Starting health monitoring every ${intervalMinutes} minutes`);
    
    setInterval(async () => {
        try {
            const health = await window.covidAPI.getHealthStatus();
            
            if (health.status !== 'healthy' && health.status !== 'degraded') {
                console.warn('⚠️ API health degraded:', health);
                showNotification('Service health degraded', 'error', 3000);
            }
        } catch (error) {
            console.error('❌ Health check failed:', error);
        }
    }, intervalMinutes * 60 * 1000);
}

/**
 * Export API functions for global access
 */
window.covidAPI = window.covidAPI || new CovidAPI();
window.initializeApp = initializeApp;
window.refreshData = refreshData;
window.updateUI = updateUI;
window.showNotification = showNotification;
window.handleAPIError = handleAPIError;
window.validateCovidData = validateCovidData;
window.getPerformanceMetrics = getPerformanceMetrics;
window.startAutoRefresh = startAutoRefresh;
window.startHealthMonitoring = startHealthMonitoring;

// Add CSS for notifications
const notificationStyles = `
@keyframes slideInRight {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes slideOutRight {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(100%);
        opacity: 0;
    }
}
`;

// Inject notification styles
const styleSheet = document.createElement('style');
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet);

console.log('📡 COVID API module loaded successfully');

// Start monitoring when document is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only start monitoring if we're on the main page (has map element)
    if (document.getElementById('map')) {
        // Start auto-refresh every 30 minutes
        startAutoRefresh(30);
        
        // Start health monitoring every 5 minutes
        startHealthMonitoring(5);
    }
    
    // Monitor online/offline status
    window.addEventListener('online', () => {
        if (typeof showNotification === 'function') {
            showNotification('Connection restored', 'success');
        }
        console.log('🌐 Connection restored');
    });
    
    window.addEventListener('offline', () => {
        if (typeof showNotification === 'function') {
            showNotification('Connection lost', 'error');
        }
        console.log('📶 Connection lost');
    });
});
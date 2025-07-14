// Immich Kiosk Gallery JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('Immich Kiosk Gallery loaded successfully!');
    
    // Check server health
    checkServerHealth();
    
    // Load configuration
    loadConfiguration();
});

async function checkServerHealth() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        console.log('Server health:', data);
    } catch (error) {
        console.error('Health check failed:', error);
    }
}

async function loadConfiguration() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();
        console.log('Configuration loaded:', config);
        
        // Update UI based on configuration
        updateConfigDisplay(config);
    } catch (error) {
        console.error('Failed to load configuration:', error);
    }
}

function updateConfigDisplay(config) {
    // This function can be extended to dynamically update the UI
    // based on the configuration
    console.log('Configuration:', config);
}

// Utility function for future slideshow functionality
function log(message) {
    console.log(`[Immich Kiosk] ${message}`);
}

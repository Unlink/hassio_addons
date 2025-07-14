// Immich Kiosk Gallery JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('Immich Kiosk Gallery loaded successfully!');
    
    // Check server health
    checkServerHealth();
    
    // Load configuration
    loadConfiguration();
    
    // Check Immich status
    checkImmichStatus();
    
    // Setup event listeners
    setupEventListeners();
});

function setupEventListeners() {
    const loadMemoriesBtn = document.getElementById('load-memories');
    if (loadMemoriesBtn) {
        loadMemoriesBtn.addEventListener('click', loadMemories);
    }
}

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

async function checkImmichStatus() {
    const statusDiv = document.getElementById('immich-status');
    const memoriesSection = document.getElementById('memories-section');
    
    try {
        const response = await fetch('/api/immich/status');
        const status = await response.json();
        
        if (status.connected) {
            statusDiv.innerHTML = '✅ Pripojený k Immich serveru';
            statusDiv.className = 'connected';
            memoriesSection.style.display = 'block';
        } else {
            statusDiv.innerHTML = `❌ Nepripojený: ${status.error || 'Neznáma chyba'}`;
            statusDiv.className = 'error';
            memoriesSection.style.display = 'none';
        }
    } catch (error) {
        statusDiv.innerHTML = '❌ Chyba pri kontrole pripojenia';
        statusDiv.className = 'error';
        memoriesSection.style.display = 'none';
        console.error('Immich status check failed:', error);
    }
}

async function loadMemories() {
    const button = document.getElementById('load-memories');
    const container = document.getElementById('memories-container');
    
    button.disabled = true;
    button.textContent = 'Načítavam...';
    container.innerHTML = '<div class="loading">Načítavam memories z Immich...</div>';
    
    try {
        const response = await fetch('/api/memories');
        const data = await response.json();
        
        if (data.success) {
            displayMemories(data.memories);
            log(`Načítané ${data.count} memories z Immich`);
        } else {
            container.innerHTML = `<div class="error">Chyba: ${data.error}</div>`;
        }
    } catch (error) {
        container.innerHTML = '<div class="error">Chyba pri načítavaní memories</div>';
        console.error('Failed to load memories:', error);
    } finally {
        button.disabled = false;
        button.textContent = 'Načítať Memories';
    }
}

let currentSlideIndex = 0;
let slideInterval = null;
let currentMemories = [];

function displayMemories(memories) {
    const container = document.getElementById('memories-container');
    
    if (memories.length === 0) {
        container.innerHTML = '<div class="info">Žiadne memories nenájdené</div>';
        return;
    }
    
    currentMemories = memories;
    
    // Create slideshow container
    container.innerHTML = `
        <div class="slideshow-container">
            <div class="slideshow-controls">
                <button id="toggle-slideshow" class="control-btn">▶️ Spustiť slideshow</button>
                <button id="prev-slide" class="control-btn">◀️ Predchádzajúci</button>
                <button id="next-slide" class="control-btn">▶️ Nasledujúci</button>
                <span class="slide-counter">1 / ${memories.length}</span>
            </div>
            <div class="slideshow-viewer">
                <div class="slide active" id="slide-0">
                    <img src="/api/proxy/image/${memories[0].id}" 
                         onerror="this.src='${memories[0].thumbnail_url}'"
                         alt="${memories[0].original_filename}" />
                    <div class="slide-info">
                        <div class="filename">${memories[0].original_filename}</div>
                        <div class="date">${formatDate(memories[0].created_at)}</div>
                        <div class="memory-type">${memories[0].memory_type || ''}</div>
                    </div>
                </div>
            </div>
            <div class="slideshow-thumbnails">
                ${memories.map((memory, index) => `
                    <div class="thumbnail ${index === 0 ? 'active' : ''}" data-slide="${index}">
                        <img src="${memory.thumbnail_url}" alt="${memory.original_filename}" />
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    
    // Setup slideshow event listeners
    setupSlideshowControls();
}

function setupSlideshowControls() {
    const toggleBtn = document.getElementById('toggle-slideshow');
    const prevBtn = document.getElementById('prev-slide');
    const nextBtn = document.getElementById('next-slide');
    const thumbnails = document.querySelectorAll('.thumbnail');
    
    toggleBtn.addEventListener('click', toggleSlideshow);
    prevBtn.addEventListener('click', previousSlide);
    nextBtn.addEventListener('click', nextSlide);
    
    thumbnails.forEach((thumb, index) => {
        thumb.addEventListener('click', () => goToSlide(index));
    });
    
    // Keyboard controls
    document.addEventListener('keydown', handleKeyboard);
}

function toggleSlideshow() {
    const toggleBtn = document.getElementById('toggle-slideshow');
    
    if (slideInterval) {
        clearInterval(slideInterval);
        slideInterval = null;
        toggleBtn.textContent = '▶️ Spustiť slideshow';
        toggleBtn.classList.remove('playing');
    } else {
        slideInterval = setInterval(nextSlide, 5000); // Change slide every 5 seconds
        toggleBtn.textContent = '⏸️ Zastaviť slideshow';
        toggleBtn.classList.add('playing');
    }
}

function nextSlide() {
    if (currentMemories.length === 0) return;
    
    currentSlideIndex = (currentSlideIndex + 1) % currentMemories.length;
    updateSlide();
}

function previousSlide() {
    if (currentMemories.length === 0) return;
    
    currentSlideIndex = currentSlideIndex === 0 ? currentMemories.length - 1 : currentSlideIndex - 1;
    updateSlide();
}

function goToSlide(index) {
    if (index >= 0 && index < currentMemories.length) {
        currentSlideIndex = index;
        updateSlide();
    }
}

function updateSlide() {
    const viewer = document.querySelector('.slideshow-viewer');
    const counter = document.querySelector('.slide-counter');
    const thumbnails = document.querySelectorAll('.thumbnail');
    
    if (!viewer || !currentMemories[currentSlideIndex]) return;
    
    const memory = currentMemories[currentSlideIndex];
    
    // Show loading state first
    viewer.innerHTML = `
        <div class="slide active">
            <div class="slide-loading">Načítavam obrázok...</div>
        </div>
    `;
    
    // Create image element with proper error handling
    const img = new Image();
    img.onload = function() {
        // Update slide content with loaded image
        viewer.innerHTML = `
            <div class="slide active">
                <img src="${img.src}" alt="${memory.original_filename}" />
                <div class="slide-info">
                    <div class="filename">${memory.original_filename}</div>
                    <div class="date">${formatDate(memory.created_at)}</div>
                    <div class="memory-type">${memory.memory_type || ''}</div>
                </div>
            </div>
        `;
    };
    
    img.onerror = function() {
        // Fallback to thumbnail if full image fails
        viewer.innerHTML = `
            <div class="slide active">
                <img src="${memory.thumbnail_url}" alt="${memory.original_filename}" />
                <div class="slide-info">
                    <div class="filename">${memory.original_filename}</div>
                    <div class="date">${formatDate(memory.created_at)}</div>
                    <div class="memory-type">${memory.memory_type || ''} (náhľad)</div>
                </div>
            </div>
        `;
    };
    
    // Try to load full image first
    img.src = `/api/proxy/image/${memory.id}`;
    
    // Update counter
    if (counter) {
        counter.textContent = `${currentSlideIndex + 1} / ${currentMemories.length}`;
    }
    
    // Update active thumbnail
    thumbnails.forEach((thumb, index) => {
        thumb.classList.toggle('active', index === currentSlideIndex);
    });
}

function handleKeyboard(event) {
    if (currentMemories.length === 0) return;
    
    switch(event.key) {
        case 'ArrowLeft':
            previousSlide();
            break;
        case 'ArrowRight':
            nextSlide();
            break;
        case ' ':
            event.preventDefault();
            toggleSlideshow();
            break;
        case 'Escape':
            if (slideInterval) {
                toggleSlideshow();
            }
            break;
    }
}

function formatDate(dateString) {
    if (!dateString) return 'Neznámy dátum';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('sk-SK', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    } catch (error) {
        return 'Neznámy dátum';
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

// Clean up function for slideshow
function cleanupSlideshow() {
    if (slideInterval) {
        clearInterval(slideInterval);
        slideInterval = null;
    }
    currentSlideIndex = 0;
    currentMemories = [];
    
    // Remove keyboard listener when not needed
    document.removeEventListener('keydown', handleKeyboard);
}

// Add cleanup when leaving the page
window.addEventListener('beforeunload', cleanupSlideshow);

// Auto-refresh memories every 5 minutes to check for new active memories
setInterval(() => {
    const container = document.getElementById('memories-container');
    if (container && currentMemories.length > 0) {
        log('Auto-refreshing memories...');
        loadMemories();
    }
}, 5 * 60 * 1000); // 5 minutes

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
    
    const loadAlbumsBtn = document.getElementById('load-albums');
    if (loadAlbumsBtn) {
        loadAlbumsBtn.addEventListener('click', loadAlbums);
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
    const albumsSection = document.getElementById('albums-section');
    
    try {
        const response = await fetch('/api/immich/status');
        const status = await response.json();
        
        if (status.connected) {
            statusDiv.innerHTML = '✅ Pripojený k Immich serveru';
            statusDiv.className = 'connected';
            memoriesSection.style.display = 'block';
            albumsSection.style.display = 'block';
        } else {
            statusDiv.innerHTML = `❌ Nepripojený: ${status.error || 'Neznáma chyba'}`;
            statusDiv.className = 'error';
            memoriesSection.style.display = 'none';
            albumsSection.style.display = 'none';
        }
    } catch (error) {
        statusDiv.innerHTML = '❌ Chyba pri kontrole pripojenia';
        statusDiv.className = 'error';
        memoriesSection.style.display = 'none';
        albumsSection.style.display = 'none';
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
    
    // Check if we're in albums mode or memories mode
    const albumsContainer = document.getElementById('albums-container');
    const isAlbumsMode = albumsContainer && albumsContainer.innerHTML.includes('slideshow-viewer-albums');
    
    switch(event.key) {
        case 'ArrowLeft':
            if (isAlbumsMode) {
                previousAlbumsSlide();
            } else {
                previousSlide();
            }
            break;
        case 'ArrowRight':
            if (isAlbumsMode) {
                nextAlbumsSlide();
            } else {
                nextSlide();
            }
            break;
        case ' ':
            event.preventDefault();
            if (isAlbumsMode) {
                toggleAlbumsSlideshow();
            } else {
                toggleSlideshow();
            }
            break;
        case 'Escape':
            if (isAlbumsMode && albumsSlideInterval) {
                toggleAlbumsSlideshow();
            } else if (slideInterval) {
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
    if (albumsSlideInterval) {
        clearInterval(albumsSlideInterval);
        albumsSlideInterval = null;
    }
    currentSlideIndex = 0;
    albumsSlideIndex = 0;
    currentMemories = [];
    
    // Remove keyboard listener when not needed
    document.removeEventListener('keydown', handleKeyboard);
}

// Add cleanup when leaving the page
window.addEventListener('beforeunload', cleanupSlideshow);

// Auto-refresh memories and albums every 5 minutes
setInterval(() => {
    const memoriesContainer = document.getElementById('memories-container');
    const albumsContainer = document.getElementById('albums-container');
    
    if (memoriesContainer && currentMemories.length > 0) {
        log('Auto-refreshing memories...');
        loadMemories();
    }
    
    if (albumsContainer && albumsContainer.innerHTML.includes('slideshow-container')) {
        log('Auto-refreshing albums...');
        loadAlbums();
    }
}, 5 * 60 * 1000); // 5 minutes

async function loadAlbums() {
    const button = document.getElementById('load-albums');
    const container = document.getElementById('albums-container');
    
    button.disabled = true;
    button.textContent = 'Načítavam...';
    container.innerHTML = '<div class="loading">Načítavam albumy z Immich...</div>';
    
    try {
        const response = await fetch('/api/albums');
        const data = await response.json();
        
        if (data.success) {
            displayAlbums(data.albums);
            log(`Načítané ${data.album_count} albumov s ${data.total_assets} fotkami`);
        } else {
            container.innerHTML = `<div class="error">Chyba: ${data.error}</div>`;
        }
    } catch (error) {
        container.innerHTML = '<div class="error">Chyba pri načítavaní albumov</div>';
        console.error('Failed to load albums:', error);
    } finally {
        button.disabled = false;
        button.textContent = 'Načítať Albumy';
    }
}

function displayAlbums(albums) {
    const container = document.getElementById('albums-container');
    
    if (albums.length === 0) {
        container.innerHTML = '<div class="info">Žiadne albumy nenájdené</div>';
        return;
    }
    
    // Collect all assets from all albums for slideshow
    const allAssets = [];
    albums.forEach(album => {
        album.assets.forEach(asset => {
            allAssets.push(asset);
        });
    });
    
    if (allAssets.length === 0) {
        container.innerHTML = '<div class="info">Žiadne fotky v albumoch nenájdené</div>';
        return;
    }
    
    // Set current memories to album assets for slideshow
    currentMemories = allAssets;
    
    // Create albums display with slideshow
    container.innerHTML = `
        <div class="albums-summary">
            <h3>Albumy (${albums.length})</h3>
            <p>Celkovo ${allAssets.length} fotiek zo všetkých albumov</p>
            ${albums.map(album => `
                <div class="album-info">
                    <strong>${album.name}</strong> - ${album.assets.length} fotiek
                    ${album.description ? `<br><span class="album-desc">${album.description}</span>` : ''}
                </div>
            `).join('')}
        </div>
        
        <div class="slideshow-container">
            <div class="slideshow-controls">
                <button id="toggle-slideshow-albums" class="control-btn">▶️ Spustiť slideshow</button>
                <button id="prev-slide-albums" class="control-btn">◀️ Predchádzajúci</button>
                <button id="next-slide-albums" class="control-btn">▶️ Nasledujúci</button>
                <span class="slide-counter-albums">1 / ${allAssets.length}</span>
            </div>
            <div class="slideshow-viewer-albums">
                <div class="slide active">
                    <img src="/api/proxy/image/${allAssets[0].id}" 
                         onerror="this.src='${allAssets[0].thumbnail_url}'"
                         alt="${allAssets[0].original_filename}" />
                    <div class="slide-info">
                        <div class="filename">${allAssets[0].original_filename}</div>
                        <div class="date">${formatDate(allAssets[0].created_at)}</div>
                        <div class="album-name">Album: ${allAssets[0].album_name}</div>
                    </div>
                </div>
            </div>
            <div class="slideshow-thumbnails">
                ${allAssets.map((asset, index) => `
                    <div class="thumbnail ${index === 0 ? 'active' : ''}" data-slide="${index}">
                        <img src="${asset.thumbnail_url}" alt="${asset.original_filename}" />
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    
    // Setup slideshow for albums
    setupAlbumsSlideshow();
}

function setupAlbumsSlideshow() {
    const toggleBtn = document.getElementById('toggle-slideshow-albums');
    const prevBtn = document.getElementById('prev-slide-albums');
    const nextBtn = document.getElementById('next-slide-albums');
    const thumbnails = document.querySelectorAll('#albums-container .thumbnail');
    
    toggleBtn.addEventListener('click', toggleAlbumsSlideshow);
    prevBtn.addEventListener('click', previousAlbumsSlide);
    nextBtn.addEventListener('click', nextAlbumsSlide);
    
    thumbnails.forEach((thumb, index) => {
        thumb.addEventListener('click', () => goToAlbumsSlide(index));
    });
}

let albumsSlideIndex = 0;
let albumsSlideInterval = null;

function toggleAlbumsSlideshow() {
    const toggleBtn = document.getElementById('toggle-slideshow-albums');
    
    if (albumsSlideInterval) {
        clearInterval(albumsSlideInterval);
        albumsSlideInterval = null;
        toggleBtn.textContent = '▶️ Spustiť slideshow';
        toggleBtn.classList.remove('playing');
    } else {
        albumsSlideInterval = setInterval(nextAlbumsSlide, 5000);
        toggleBtn.textContent = '⏸️ Zastaviť slideshow';
        toggleBtn.classList.add('playing');
    }
}

function nextAlbumsSlide() {
    if (currentMemories.length === 0) return;
    
    albumsSlideIndex = (albumsSlideIndex + 1) % currentMemories.length;
    updateAlbumsSlide();
}

function previousAlbumsSlide() {
    if (currentMemories.length === 0) return;
    
    albumsSlideIndex = albumsSlideIndex === 0 ? currentMemories.length - 1 : albumsSlideIndex - 1;
    updateAlbumsSlide();
}

function goToAlbumsSlide(index) {
    if (index >= 0 && index < currentMemories.length) {
        albumsSlideIndex = index;
        updateAlbumsSlide();
    }
}

function updateAlbumsSlide() {
    const viewer = document.querySelector('.slideshow-viewer-albums');
    const counter = document.querySelector('.slide-counter-albums');
    const thumbnails = document.querySelectorAll('#albums-container .thumbnail');
    
    if (!viewer || !currentMemories[albumsSlideIndex]) return;
    
    const asset = currentMemories[albumsSlideIndex];
    
    // Show loading state first
    viewer.innerHTML = `
        <div class="slide active">
            <div class="slide-loading">Načítavam obrázok...</div>
        </div>
    `;
    
    // Create image with error handling
    const img = new Image();
    img.onload = function() {
        viewer.innerHTML = `
            <div class="slide active">
                <img src="${img.src}" alt="${asset.original_filename}" />
                <div class="slide-info">
                    <div class="filename">${asset.original_filename}</div>
                    <div class="date">${formatDate(asset.created_at)}</div>
                    <div class="album-name">Album: ${asset.album_name}</div>
                </div>
            </div>
        `;
    };
    
    img.onerror = function() {
        viewer.innerHTML = `
            <div class="slide active">
                <img src="${asset.thumbnail_url}" alt="${asset.original_filename}" />
                <div class="slide-info">
                    <div class="filename">${asset.original_filename}</div>
                    <div class="date">${formatDate(asset.created_at)}</div>
                    <div class="album-name">Album: ${asset.album_name} (náhľad)</div>
                </div>
            </div>
        `;
    };
    
    img.src = `/api/proxy/image/${asset.id}`;
    
    // Update counter
    if (counter) {
        counter.textContent = `${albumsSlideIndex + 1} / ${currentMemories.length}`;
    }
    
    // Update active thumbnail
    thumbnails.forEach((thumb, index) => {
        thumb.classList.toggle('active', index === albumsSlideIndex);
    });
}

// Immich Kiosk Gallery - Fullscreen Slideshow

class ImmichKioskGallery {
    constructor() {
        this.images = [];
        this.currentIndex = 0;
        this.isPlaying = true;
        this.slideInterval = null;
        this.slideDuration = 8000; // 8 seconds default
        this.currentSource = 'memories'; // 'memories' or 'albums'
        this.autoRefresh = true;
        this.refreshInterval = null;
        this.isFullscreen = false;
        this.albumsAvailable = false;
        
        // DOM elements
        this.loadingScreen = document.getElementById('loading-screen');
        this.errorScreen = document.getElementById('error-screen');
        this.mainSlideshow = document.getElementById('main-slideshow');
        this.currentImage = document.getElementById('current-image');
        this.progressBar = document.getElementById('progress-fill');
        this.controlsPanel = document.getElementById('controls-panel');
        this.settingsPanel = document.getElementById('settings-panel');
        
        this.init();
    }
    
    async init() {
        this.setupEventListeners();
        this.updateCurrentTime();
        this.setLoadingStatus('Pripájam sa k Immich serveru...');
        
        try {
            await this.checkImmichStatus();
            await this.loadInitialData();
            this.showMainSlideshow();
            this.startSlideshow();
            this.setupAutoRefresh();
        } catch (error) {
            console.error('Initialization failed:', error);
            this.showError('Nepodarilo sa načítať údaje z Immich serveru');
        }
    }
    
    setupEventListeners() {
        // Playback controls
        document.getElementById('play-pause-btn').addEventListener('click', () => this.togglePlayPause());
        document.getElementById('prev-btn').addEventListener('click', () => this.previousSlide());
        document.getElementById('next-btn').addEventListener('click', () => this.nextSlide());
        
        // Source toggle
        document.getElementById('memories-btn').addEventListener('click', () => this.switchSource('memories'));
        document.getElementById('albums-btn').addEventListener('click', () => this.switchSource('albums'));
        
        // Settings
        document.getElementById('settings-btn').addEventListener('click', () => this.toggleSettings());
        document.getElementById('close-settings').addEventListener('click', () => this.hideSettings());
        document.getElementById('fullscreen-btn').addEventListener('click', () => this.toggleFullscreen());
        
        // Settings controls
        const durationSlider = document.getElementById('slide-duration');
        durationSlider.addEventListener('input', (e) => this.updateSlideDuration(e.target.value));
        
        const autoRefreshCheckbox = document.getElementById('auto-refresh');
        autoRefreshCheckbox.addEventListener('change', (e) => this.toggleAutoRefresh(e.target.checked));
        
        // Error retry
        document.getElementById('retry-button').addEventListener('click', () => this.retry());
        
        // Keyboard controls
        document.addEventListener('keydown', (e) => this.handleKeydown(e));
        
        // Mouse/touch controls
        let hideControlsTimeout;
        document.addEventListener('mousemove', () => {
            this.showControls();
            clearTimeout(hideControlsTimeout);
            hideControlsTimeout = setTimeout(() => this.hideControls(), 3000);
        });
        
        // Time update
        setInterval(() => this.updateCurrentTime(), 1000);
    }
    
    async checkImmichStatus() {
        try {
            const response = await fetch('/api/immich/status');
            const status = await response.json();
            
            if (!status.connected) {
                throw new Error(status.error || 'Immich server nedostupný');
            }
            
            this.setConnectionStatus('Pripojený', true);
            console.log('Immich server connected successfully');
        } catch (error) {
            this.setConnectionStatus('Odpojený', false);
            throw error;
        }
    }
    
    async loadInitialData() {
        this.setLoadingStatus('Načítavam memories...');
        
        // Try to load memories first
        try {
            await this.loadMemories();
            this.currentSource = 'memories';
        } catch (error) {
            console.warn('Failed to load memories:', error);
        }
        
        // Check if albums are available
        try {
            const albumsResponse = await fetch('/api/albums');
            const albumsData = await albumsResponse.json();
            
            if (albumsData.success && albumsData.images && albumsData.images.length > 0) {
                this.albumsAvailable = true;
                document.getElementById('source-toggle').classList.remove('hidden');
            }
        } catch (error) {
            console.warn('Albums not available:', error);
        }
        
        if (this.images.length === 0) {
            throw new Error('Žiadne obrázky na zobrazenie');
        }
    }
    
    async loadMemories() {
        const response = await fetch('/api/memories');
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Nepodarilo sa načítať memories');
        }
        
        this.images = data.memories || [];
        console.log(`Loaded ${this.images.length} memories`);
    }
    
    async loadAlbums() {
        const response = await fetch('/api/albums');
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Nepodarilo sa načítať albumy');
        }
        
        this.images = data.images || [];
        console.log(`Loaded ${this.images.length} album images`);
    }
    
    async switchSource(source) {
        if (source === this.currentSource) return;
        
        this.stopSlideshow();
        this.setLoadingStatus(`Načítavam ${source === 'memories' ? 'memories' : 'albumy'}...`);
        this.showLoadingScreen();
        
        try {
            if (source === 'memories') {
                await this.loadMemories();
            } else {
                await this.loadAlbums();
            }
            
            this.currentSource = source;
            this.currentIndex = 0;
            this.updateSourceButtons();
            this.showMainSlideshow();
            this.displayCurrentSlide();
            this.startSlideshow();
        } catch (error) {
            console.error(`Failed to switch to ${source}:`, error);
            this.showError(`Nepodarilo sa načítať ${source === 'memories' ? 'memories' : 'albumy'}`);
        }
    }
    
    showMainSlideshow() {
        this.loadingScreen.classList.add('hidden');
        this.errorScreen.classList.add('hidden');
        this.mainSlideshow.classList.remove('hidden');
        this.updateSlideCounter();
        this.displayCurrentSlide();
    }
    
    showLoadingScreen() {
        this.mainSlideshow.classList.add('hidden');
        this.errorScreen.classList.add('hidden');
        this.loadingScreen.classList.remove('hidden');
    }
    
    showError(message) {
        this.loadingScreen.classList.add('hidden');
        this.mainSlideshow.classList.add('hidden');
        this.errorScreen.classList.remove('hidden');
        document.getElementById('error-message').textContent = message;
    }
    
    displayCurrentSlide() {
        if (this.images.length === 0) return;
        
        const image = this.images[this.currentIndex];
        const imageUrl = `/api/proxy/image/${image.id}`;
        
        // Preload image
        const img = new Image();
        img.onload = () => {
            this.currentImage.src = imageUrl;
            this.currentImage.alt = image.originalFileName || 'Immich Image';
            this.updateSlideInfo(image);
        };
        img.onerror = () => {
            console.error('Failed to load image:', image.id);
            this.nextSlide(); // Skip to next image
        };
        img.src = imageUrl;
    }
    
    updateSlideInfo(image) {
        document.getElementById('image-filename').textContent = image.originalFileName || 'Neznámy súbor';
        
        const date = image.fileCreatedAt ? new Date(image.fileCreatedAt).toLocaleDateString('sk-SK') : 'Neznámy dátum';
        document.getElementById('image-date').textContent = date;
        
        const source = this.currentSource === 'memories' ? '🎞️ Memories' : '📁 Album';
        document.getElementById('image-source').textContent = source;
    }
    
    startSlideshow() {
        if (!this.isPlaying) return;
        
        this.slideInterval = setInterval(() => {
            this.nextSlide();
        }, this.slideDuration);
        
        this.startProgressBar();
    }
    
    stopSlideshow() {
        if (this.slideInterval) {
            clearInterval(this.slideInterval);
            this.slideInterval = null;
        }
        this.stopProgressBar();
    }
    
    togglePlayPause() {
        this.isPlaying = !this.isPlaying;
        
        if (this.isPlaying) {
            this.startSlideshow();
            document.getElementById('play-pause-btn').innerHTML = '<span>⏸️</span>';
        } else {
            this.stopSlideshow();
            document.getElementById('play-pause-btn').innerHTML = '<span>▶️</span>';
        }
    }
    
    nextSlide() {
        if (this.images.length === 0) return;
        
        this.currentIndex = (this.currentIndex + 1) % this.images.length;
        this.displayCurrentSlide();
        this.updateSlideCounter();
        
        if (this.isPlaying) {
            this.stopSlideshow();
            this.startSlideshow(); // Restart timer
        }
    }
    
    previousSlide() {
        if (this.images.length === 0) return;
        
        this.currentIndex = this.currentIndex === 0 ? this.images.length - 1 : this.currentIndex - 1;
        this.displayCurrentSlide();
        this.updateSlideCounter();
        
        if (this.isPlaying) {
            this.stopSlideshow();
            this.startSlideshow(); // Restart timer
        }
    }
    
    startProgressBar() {
        if (!this.progressBar) return;
        
        this.progressBar.style.transition = 'none';
        this.progressBar.style.width = '0%';
        
        setTimeout(() => {
            this.progressBar.style.transition = `width ${this.slideDuration}ms linear`;
            this.progressBar.style.width = '100%';
        }, 50);
    }
    
    stopProgressBar() {
        if (!this.progressBar) return;
        
        this.progressBar.style.transition = 'none';
        this.progressBar.style.width = '0%';
    }
    
    updateSlideCounter() {
        const counter = document.getElementById('slide-counter');
        counter.textContent = `${this.currentIndex + 1} / ${this.images.length}`;
    }
    
    updateSourceButtons() {
        const memoriesBtn = document.getElementById('memories-btn');
        const albumsBtn = document.getElementById('albums-btn');
        
        memoriesBtn.classList.toggle('active', this.currentSource === 'memories');
        albumsBtn.classList.toggle('active', this.currentSource === 'albums');
    }
    
    toggleSettings() {
        this.settingsPanel.classList.toggle('hidden');
    }
    
    hideSettings() {
        this.settingsPanel.classList.add('hidden');
    }
    
    updateSlideDuration(value) {
        this.slideDuration = value * 1000;
        document.getElementById('duration-value').textContent = `${value}s`;
        
        if (this.isPlaying) {
            this.stopSlideshow();
            this.startSlideshow();
        }
    }
    
    toggleAutoRefresh(enabled) {
        this.autoRefresh = enabled;
        
        if (enabled) {
            this.setupAutoRefresh();
        } else if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
    
    setupAutoRefresh() {
        if (!this.autoRefresh) return;
        
        // Refresh data every 5 minutes
        this.refreshInterval = setInterval(async () => {
            try {
                if (this.currentSource === 'memories') {
                    await this.loadMemories();
                } else {
                    await this.loadAlbums();
                }
                console.log('Auto-refreshed image data');
            } catch (error) {
                console.warn('Auto-refresh failed:', error);
            }
        }, 5 * 60 * 1000);
    }
    
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(console.error);
        } else {
            document.exitFullscreen().catch(console.error);
        }
    }
    
    handleKeydown(event) {
        if (this.settingsPanel && !this.settingsPanel.classList.contains('hidden')) {
            if (event.key === 'Escape') {
                this.hideSettings();
            }
            return;
        }
        
        switch (event.key) {
            case 'ArrowLeft':
                event.preventDefault();
                this.previousSlide();
                break;
            case 'ArrowRight':
                event.preventDefault();
                this.nextSlide();
                break;
            case ' ':
                event.preventDefault();
                this.togglePlayPause();
                break;
            case 'f':
            case 'F11':
                event.preventDefault();
                this.toggleFullscreen();
                break;
            case 's':
                event.preventDefault();
                this.toggleSettings();
                break;
            case 'Escape':
                if (document.fullscreenElement) {
                    document.exitFullscreen();
                }
                break;
            case '1':
                if (this.albumsAvailable) {
                    this.switchSource('memories');
                }
                break;
            case '2':
                if (this.albumsAvailable) {
                    this.switchSource('albums');
                }
                break;
        }
    }
    
    showControls() {
        this.controlsPanel.classList.remove('hidden-controls');
    }
    
    hideControls() {
        this.controlsPanel.classList.add('hidden-controls');
    }
    
    setLoadingStatus(message) {
        const statusEl = document.getElementById('loading-status');
        if (statusEl) {
            statusEl.textContent = message;
        }
    }
    
    setConnectionStatus(status, isConnected) {
        const statusEl = document.getElementById('connection-status');
        if (statusEl) {
            statusEl.textContent = isConnected ? '🟢 Pripojený' : '🔴 Odpojený';
            statusEl.className = isConnected ? 'connection-status connected' : 'connection-status disconnected';
        }
    }
    
    updateCurrentTime() {
        const timeEl = document.getElementById('current-time');
        if (timeEl) {
            timeEl.textContent = new Date().toLocaleTimeString('sk-SK', {
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    }
    
    async retry() {
        this.init();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.gallery = new ImmichKioskGallery();
});

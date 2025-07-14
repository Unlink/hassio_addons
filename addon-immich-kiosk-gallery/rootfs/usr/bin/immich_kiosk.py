#!/usr/bin/env python3
"""
Immich Kiosk Gallery - Simple photo slideshow from Immich
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime
from flask import Flask, render_template, jsonify, Response, request
from flask_cors import CORS

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='/usr/share/immich-kiosk/templates', static_folder='/usr/share/immich-kiosk/static')
CORS(app)

# Immich API Client
class ImmichAPIClient:
    """Client for communicating with Immich API"""
    
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'x-api-key': api_key,
            'Content-Type': 'application/json'
        })
        
    def test_connection(self):
        """Test connection to Immich server"""
        try:
            response = self.session.get(f"{self.base_url}/api/users/me", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to connect to Immich server: {e}")
            return False
    
    def get_memories(self):
        """Get memories from Immich API"""
        try:
            logger.info("Fetching memories from Immich API...")
            response = self.session.get(f"{self.base_url}/api/memories", timeout=30)
            
            if response.status_code == 200:
                memories = response.json()
                logger.info(f"Retrieved {len(memories)} memories from Immich")
                return memories
            else:
                logger.error(f"Failed to fetch memories: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching memories: {e}")
            return []
    
    def get_asset_info(self, asset_id):
        """Get detailed information about an asset"""
        try:
            response = self.session.get(f"{self.base_url}/api/assets/{asset_id}", timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error fetching asset info for {asset_id}: {e}")
            return None
    
    def get_asset_thumbnail_url(self, asset_id, size='preview'):
        """Get thumbnail URL for an asset - using local proxy"""
        return f"/api/proxy/thumbnail/{asset_id}?size={size}"
    
    def get_asset_image_data(self, asset_id, size='preview'):
        """Get image data from Immich API"""
        try:
            url = f"{self.base_url}/api/assets/{asset_id}/thumbnail?size={size}"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                return response.content, response.headers.get('Content-Type', 'image/jpeg')
            else:
                logger.error(f"Failed to fetch image {asset_id}: HTTP {response.status_code}")
                return None, None
                
        except Exception as e:
            logger.error(f"Error fetching image {asset_id}: {e}")
            return None, None

    def get_albums(self):
        """Get all albums from Immich API"""
        try:
            logger.info("Fetching albums from Immich API...")
            response = self.session.get(f"{self.base_url}/api/albums", timeout=30)
            
            if response.status_code == 200:
                albums = response.json()
                logger.info(f"Retrieved {len(albums)} albums from Immich")
                return albums
            else:
                logger.error(f"Failed to fetch albums: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching albums: {e}")
            return []
    
    def get_album_assets(self, album_id):
        """Get assets from a specific album"""
        try:
            logger.info(f"Fetching assets from album {album_id}...")
            response = self.session.get(f"{self.base_url}/api/albums/{album_id}", timeout=30)
            
            if response.status_code == 200:
                album_data = response.json()
                assets = album_data.get('assets', [])
                logger.info(f"Retrieved {len(assets)} assets from album {album_id}")
                return assets
            else:
                logger.error(f"Failed to fetch album {album_id}: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching album {album_id}: {e}")
            return []
    
    def find_albums_by_name(self, album_names):
        """Find albums by their names and return their IDs"""
        try:
            all_albums = self.get_albums()
            found_albums = []
            
            for album in all_albums:
                album_name = album.get('albumName', '')
                if album_name in album_names:
                    found_albums.append({
                        'id': album.get('id'),
                        'name': album_name,
                        'assetCount': album.get('assetCount', 0),
                        'description': album.get('description', ''),
                        'createdAt': album.get('createdAt')
                    })
                    logger.info(f"Found album: {album_name} (ID: {album.get('id')}, Assets: {album.get('assetCount', 0)})")
            
            return found_albums
            
        except Exception as e:
            logger.error(f"Error finding albums by name: {e}")
            return []

# Load configuration
def load_config():
    """Load configuration from Home Assistant options"""
    try:
        with open('/data/options.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Configuration file not found, using defaults")
        return {
            'log_level': 'info',
            'immich_url': '',
            'immich_api_key': '',
            'immich_show_memories': True,
            'immich_show_albums': True,
            'immich_albums': []
        }

config = load_config()

# Set log level from config
log_level = getattr(logging, config.get('log_level', 'info').upper())
logger.setLevel(log_level)

# Initialize Immich client
immich_client = None
if config.get('immich_url') and config.get('immich_api_key'):
    try:
        immich_client = ImmichAPIClient(
            base_url=config.get('immich_url'),
            api_key=config.get('immich_api_key')
        )
        if immich_client.test_connection():
            logger.info("Successfully connected to Immich server")
        else:
            logger.warning("Failed to connect to Immich server")
            immich_client = None
    except Exception as e:
        logger.error(f"Failed to initialize Immich client: {e}")
        immich_client = None
else:
    logger.info("Immich URL or API key not configured, running in demo mode")

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', config=config)

@app.route('/api/config')
def api_config():
    """API endpoint to get configuration"""
    return jsonify({
        'immich_url': config.get('immich_url', ''),
        'show_memories': config.get('immich_show_memories', True),
        'show_albums': config.get('immich_show_albums', True),
        'albums': config.get('immich_albums', [])
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Immich Kiosk Gallery is running'})

@app.route('/api/memories')
def api_memories():
    """API endpoint to get memories from Immich"""
    if not immich_client:
        return jsonify({
            'success': False,
            'error': 'Immich not configured or connection failed',
            'memories': []
        }), 400
    
    if not config.get('immich_show_memories', True):
        return jsonify({
            'success': False,
            'error': 'Memories are disabled in configuration',
            'memories': []
        }), 400
    
    try:
        memories = immich_client.get_memories()
        
        # Get current time in UTC
        current_time = datetime.utcnow()
        
        # Filter memories that should be shown now
        active_memories = []
        for memory in memories:
            show_at = memory.get('showAt')
            hide_at = memory.get('hideAt')
            
            # Parse timestamps
            try:
                if show_at:
                    show_time = datetime.fromisoformat(show_at.replace('Z', '+00:00')).replace(tzinfo=None)
                else:
                    continue  # Skip if no showAt time
                    
                if hide_at:
                    hide_time = datetime.fromisoformat(hide_at.replace('Z', '+00:00')).replace(tzinfo=None)
                else:
                    continue  # Skip if no hideAt time
                
                # Check if memory should be shown now
                if show_time <= current_time <= hide_time:
                    active_memories.append(memory)
                    logger.debug(f"Memory {memory.get('id')} is active (show: {show_time}, hide: {hide_time}, now: {current_time})")
                else:
                    logger.debug(f"Memory {memory.get('id')} is not active (show: {show_time}, hide: {hide_time}, now: {current_time})")
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse timestamps for memory {memory.get('id')}: {e}")
                continue
        
        logger.info(f"Filtered {len(active_memories)} active memories out of {len(memories)} total memories")
        
        # Process active memories to include thumbnail URLs
        processed_memories = []
        for memory in active_memories:
            if 'assets' in memory and memory['assets']:
                # Take first 5 assets from each memory
                for asset in memory['assets'][:5]:
                    processed_asset = {
                        'id': asset.get('id'),
                        'type': asset.get('type'),
                        'thumbnail_url': immich_client.get_asset_thumbnail_url(asset.get('id')),
                        'created_at': asset.get('fileCreatedAt'),
                        'original_filename': asset.get('originalFileName', ''),
                        'memory_id': memory.get('id'),
                        'memory_type': memory.get('type'),
                        'memory_data': memory.get('data', {}),
                        'show_at': memory.get('showAt'),
                        'hide_at': memory.get('hideAt')
                    }
                    processed_memories.append(processed_asset)
        
        return jsonify({
            'success': True,
            'memories': processed_memories,
            'count': len(processed_memories),
            'total_memories': len(memories),
            'active_memories': len(active_memories),
            'current_time': current_time.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in api_memories: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'memories': []
        }), 500

@app.route('/api/proxy/thumbnail/<asset_id>')
def proxy_thumbnail(asset_id):
    """Proxy endpoint for Immich thumbnails to hide API key"""
    if not immich_client:
        return jsonify({'error': 'Immich not configured'}), 400
    
    # Get size parameter, default to 'preview'
    size = request.args.get('size', 'preview')
    
    # Validate size parameter
    valid_sizes = ['webp', 'preview', 'thumbnail']
    if size not in valid_sizes:
        size = 'preview'
    
    try:
        image_data, content_type = immich_client.get_asset_image_data(asset_id, size)
        
        if image_data is not None:
            response = Response(image_data, mimetype=content_type)
            # Add cache headers
            response.headers['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
            response.headers['X-Proxy-Source'] = 'immich-kiosk'
            return response
        else:
            return jsonify({'error': 'Image not found'}), 404
            
    except Exception as e:
        logger.error(f"Error in proxy_thumbnail for {asset_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/proxy/image/<asset_id>')
def proxy_full_image(asset_id):
    """Proxy endpoint for full-size Immich images"""
    if not immich_client:
        return jsonify({'error': 'Immich not configured'}), 400
    
    try:
        # For full images, we use the original asset endpoint
        url = f"{immich_client.base_url}/api/assets/{asset_id}/original"
        response = immich_client.session.get(url, timeout=60, stream=True)
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    yield chunk
            
            proxy_response = Response(generate(), mimetype=content_type)
            proxy_response.headers['Cache-Control'] = 'public, max-age=3600'
            proxy_response.headers['X-Proxy-Source'] = 'immich-kiosk'
            return proxy_response
        else:
            return jsonify({'error': 'Image not found'}), 404
            
    except Exception as e:
        logger.error(f"Error in proxy_full_image for {asset_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/albums')
def api_albums():
    """API endpoint to get albums and their assets from Immich"""
    if not immich_client:
        return jsonify({
            'success': False,
            'error': 'Immich not configured or connection failed',
            'albums': []
        }), 400
    
    if not config.get('immich_show_albums', True):
        return jsonify({
            'success': False,
            'error': 'Albums are disabled in configuration',
            'albums': []
        }), 400
    
    album_names = config.get('immich_albums', [])
    if not album_names:
        return jsonify({
            'success': False,
            'error': 'No albums configured to display',
            'albums': []
        }), 400
    
    try:
        # Find albums by their names
        found_albums = immich_client.find_albums_by_name(album_names)
        
        processed_albums = []
        total_assets = 0
        
        for album in found_albums:
            # Get assets from each album
            assets = immich_client.get_album_assets(album['id'])
            
            processed_assets = []
            for asset in assets[:20]:  # Limit to first 20 assets per album
                processed_asset = {
                    'id': asset.get('id'),
                    'type': asset.get('type'),
                    'thumbnail_url': immich_client.get_asset_thumbnail_url(asset.get('id')),
                    'created_at': asset.get('fileCreatedAt'),
                    'original_filename': asset.get('originalFileName', ''),
                    'album_id': album['id'],
                    'album_name': album['name']
                }
                processed_assets.append(processed_asset)
                total_assets += 1
            
            processed_album = {
                'id': album['id'],
                'name': album['name'],
                'description': album.get('description', ''),
                'asset_count': album.get('assetCount', 0),
                'created_at': album.get('createdAt'),
                'assets': processed_assets
            }
            processed_albums.append(processed_album)
        
        return jsonify({
            'success': True,
            'albums': processed_albums,
            'album_count': len(processed_albums),
            'total_assets': total_assets,
            'configured_albums': album_names,
            'found_albums': [album['name'] for album in found_albums]
        })
        
    except Exception as e:
        logger.error(f"Error in api_albums: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'albums': []
        }), 500

@app.route('/api/immich/status')
def api_immich_status():
    """API endpoint to check Immich connection status"""
    if not immich_client:
        return jsonify({
            'connected': False,
            'error': 'Immich not configured',
            'url': config.get('immich_url', ''),
            'has_api_key': bool(config.get('immich_api_key'))
        })
    
    connected = immich_client.test_connection()
    return jsonify({
        'connected': connected,
        'url': config.get('immich_url', ''),
        'has_api_key': bool(config.get('immich_api_key'))
    })

@app.route('/api/image-proxy/<path:image_path>')
def image_proxy(image_path):
    """Proxy endpoint to serve Immich images"""
    if not immich_client:
        return jsonify({'success': False, 'error': 'Immich not configured'}), 500
    
    # For security, only allow access to certain paths
    if '..' in image_path or image_path.startswith('/'):
        return jsonify({'success': False, 'error': 'Invalid image path'}), 400
    
    try:
        # Forward the request to the Immich API
        response = immich_client.session.get(f"{immich_client.base_url}/api/assets/{image_path}/original", stream=True)
        
        if response.status_code == 200:
            # Return the image data directly
            return Response(response.iter_content(chunk_size=10*1024), content_type=response.headers['Content-Type'])
        else:
            logger.error(f"Failed to fetch image from Immich: HTTP {response.status_code}")
            return jsonify({'success': False, 'error': 'Failed to fetch image from Immich'}), 500
    
    except Exception as e:
        logger.error(f"Error in image_proxy: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Immich Kiosk Gallery...")
    logger.info(f"Configuration: {config}")
    
    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=8456,
        debug=False
    )

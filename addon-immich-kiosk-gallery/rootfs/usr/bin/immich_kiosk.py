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
from immich_api_client import ImmichAPIClient, Asset, Album, Memory, ImageData

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='/usr/share/immich-kiosk/templates', static_folder='/usr/share/immich-kiosk/static')
CORS(app)

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

@app.route('/api/proxy/thumbnail/<asset_id>')
def proxy_thumbnail(asset_id):
    """Proxy endpoint for Immich thumbnails to hide API key"""
    if not immich_client:
        return jsonify({'error': 'Immich not configured'}), 400
    
    try:
        image_data_obj = immich_client.get_asset_image_data(asset_id, 'preview')
        
        if image_data_obj is not None:
            response = Response(image_data_obj.content, mimetype=image_data_obj.content_type)
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
        # Get full-size image stream from API client
        response_stream, content_type = immich_client.get_asset_full_image_stream(asset_id)
        
        if response_stream is not None:
            def generate():
                for chunk in response_stream.iter_content(chunk_size=8192):
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

@app.route('/api/memories')
def api_memories():
    """API endpoint to get memories for today from Immich"""
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
        
        # Filter memories that should be shown today
        today_memories = []
        for memory in memories:
            show_at = memory.show_at
            hide_at = memory.hide_at
            
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
                
                # Check if memory should be shown today
                if show_time <= current_time <= hide_time:
                    today_memories.append(memory)
                    logger.debug(f"Memory {memory.id} is active for today (show: {show_time}, hide: {hide_time}, now: {current_time})")
                else:
                    logger.debug(f"Memory {memory.id} is not active for today (show: {show_time}, hide: {hide_time}, now: {current_time})")
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse timestamps for memory {memory.id}: {e}")
                continue
        
        logger.info(f"Found {len(today_memories)} memories for today out of {len(memories)} total memories")
        
        # Process memories to include URLs and metadata
        processed_memories = []
        for memory in today_memories:
            if memory.assets:
                for asset in memory.assets:
                    if asset.is_archived or asset.type is not 'IMAGE':
                        logger.debug(f"Skipping asset {asset.id} in memory {memory.id}")
                        continue
                    asset_data = {
                        'id': asset.id,
                        'type': asset.type,
                        'original_filename': asset.original_filename,
                        'file_created_at': asset.file_created_at,
                        'file_modified_at': asset.file_modified_at,
                        'updated_at': asset.updated_at,
                        'is_favorite': asset.is_favorite,
                        'thumbnail_url': f"/api/proxy/thumbnail/{asset.id}",
                        'full_image_url': f"/api/proxy/image/{asset.id}"
                    }
                    processed_memories.append(asset_data)
        
        return jsonify({
            'success': True,
            'memories': processed_memories,
            'count': len(processed_memories),
            'total_memories': len(memories),
            'current_time': current_time.isoformat(),
        })
        
    except Exception as e:
        logger.error(f"Error in api_memories: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'memories': []
        }), 500

@app.route('/api/randomPhotos')
def api_random_photos():
    """API endpoint to get random photos from configured albums"""
    if not immich_client:
        return jsonify({
            'success': False,
            'error': 'Immich not configured or connection failed',
            'photos': []
        }), 400
    
    if not config.get('immich_show_albums', True):
        return jsonify({
            'success': False,
            'error': 'Albums are disabled in configuration',
            'photos': []
        }), 400
    
    album_names = config.get('immich_albums', [])
    if not album_names:
        return jsonify({
            'success': False,
            'error': 'No albums configured to display',
            'photos': []
        }), 400
    
    try:
        # Get random photos from configured albums
        random_photos = immich_client.get_random_photos_from_albums(album_names, count=20)
        
        # Process photos to include URLs and metadata
        processed_photos = []
        for photo in random_photos:
            photo_data = {
                'id': photo.id,
                'type': photo.type,
                'original_filename': photo.original_filename,
                'file_created_at': photo.file_created_at,
                'file_modified_at': photo.file_modified_at,
                'updated_at': photo.updated_at,
                'is_favorite': photo.is_favorite,
                'thumbnail_url': f"/api/proxy/thumbnail/{photo.id}",
                'full_image_url': f"/api/proxy/image/{photo.id}"
            }
            processed_photos.append(photo_data)
        
        return jsonify({
            'success': True,
            'photos': processed_photos,
            'count': len(processed_photos),
            'configured_albums': album_names,
            'message': f"Found {len(processed_photos)} random photos from {len(album_names)} configured albums"
        })
        
    except Exception as e:
        logger.error(f"Error in api_random_photos: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'photos': []
        }), 500
        




if __name__ == '__main__':
    logger.info("Starting Immich Kiosk Gallery...")
    logger.info(f"Configuration: {config}")
    
    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=8456,
        debug=False
    )

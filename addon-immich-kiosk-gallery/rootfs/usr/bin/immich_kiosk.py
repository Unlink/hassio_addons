#!/usr/bin/env python3
"""
Immich Kiosk Gallery - Simple photo slideshow from Immich
"""

import os
import sys
import json
import logging
from flask import Flask, render_template, jsonify
from flask_cors import CORS

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

if __name__ == '__main__':
    logger.info("Starting Immich Kiosk Gallery...")
    logger.info(f"Configuration: {config}")
    
    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=8456,
        debug=False
    )

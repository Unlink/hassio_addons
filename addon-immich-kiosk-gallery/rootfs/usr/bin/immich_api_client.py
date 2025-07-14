#!/usr/bin/env python3
"""
Immich API Client - Client for communicating with Immich API
"""

import logging
import requests
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class Asset:
    """Represents an Immich asset (photo/video)"""
    id: str
    type: str
    original_filename: str
    file_created_at: Optional[str] = None
    file_modified_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_favorite: bool = False
    is_archived: bool = False
    duration: Optional[str] = None
    author: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

@dataclass
class Memory:
    """Represents an Immich memory"""
    id: str
    type: str
    show_at: Optional[str] = None
    hide_at: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    assets: List[Asset] = None
    
    def __post_init__(self):
        if self.assets is None:
            self.assets = []

@dataclass
class Album:
    """Represents an Immich album"""
    id: str
    name: str
    description: Optional[str] = None
    asset_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    assets: List[Asset] = None
    
    def __post_init__(self):
        if self.assets is None:
            self.assets = []

@dataclass
class ImageData:
    """Represents image data with content type"""
    content: bytes
    content_type: str

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
    
    def get_memories(self) -> List[Memory]:
        """Get memories from Immich API"""
        try:
            logger.info("Fetching memories from Immich API...")
            response = self.session.get(f"{self.base_url}/api/memories", timeout=30)
            
            if response.status_code == 200:
                memories_data = response.json()
                memories = []
                
                for memory_data in memories_data:
                    # Convert assets to Asset objects
                    assets = []
                    for asset_data in memory_data.get('assets', []):
                        asset = Asset(
                            id=asset_data.get('id', ''),
                            type=asset_data.get('type', ''),
                            original_filename=asset_data.get('originalFileName', ''),
                            file_created_at=asset_data.get('fileCreatedAt'),
                            file_modified_at=asset_data.get('fileModifiedAt'),
                            updated_at=asset_data.get('updatedAt'),
                            is_favorite=asset_data.get('isFavorite', False),
                            is_archived=asset_data.get('isArchived', False),
                            duration=asset_data.get('duration')
                        )
                        assets.append(asset)
                    
                    memory = Memory(
                        id=memory_data.get('id', ''),
                        type=memory_data.get('type', ''),
                        show_at=memory_data.get('showAt'),
                        hide_at=memory_data.get('hideAt'),
                        data=memory_data.get('data', {}),
                        assets=assets
                    )
                    memories.append(memory)
                
                logger.info(f"Retrieved {len(memories)} memories from Immich")
                return memories
            else:
                logger.error(f"Failed to fetch memories: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching memories: {e}")
            return []
    
    def get_asset_info(self, asset_id: str) -> Optional[Asset]:
        """Get detailed information about an asset, including author and location"""
        try:
            response = self.session.get(f"{self.base_url}/api/assets/{asset_id}", timeout=10)
            if response.status_code == 200:
                asset_data = response.json()
                # Author
                owner = asset_data.get('owner', {})
                author = owner.get('name') or owner.get('email')
                # Location
                exif = asset_data.get('exifInfo', {})
                city = exif.get('city')
                state = exif.get('state')
                country = exif.get('country')
                return Asset(
                    id=asset_data.get('id', ''),
                    type=asset_data.get('type', ''),
                    original_filename=asset_data.get('originalFileName', ''),
                    file_created_at=asset_data.get('fileCreatedAt'),
                    file_modified_at=asset_data.get('fileModifiedAt'),
                    updated_at=asset_data.get('updatedAt'),
                    is_favorite=asset_data.get('isFavorite', False),
                    is_archived=asset_data.get('isArchived', False),
                    duration=asset_data.get('duration'),
                    author=author,
                    city=city,
                    state=state,
                    country=country
                )
            return None
        except Exception as e:
            logger.error(f"Error fetching asset info for {asset_id}: {e}")
            return None
    
    def get_asset_thumbnail_url(self, asset_id: str, size: str = 'thumbnail') -> str:
        """Get thumbnail URL for an asset - using local proxy"""
        return f"/api/proxy/thumbnail/{asset_id}?size={size}"
    
    def get_asset_image_data(self, asset_id: str, size: str = 'thumbnail') -> Optional[ImageData]:
        """Get image data from Immich API"""
        try:
            url = f"{self.base_url}/api/assets/{asset_id}/thumbnail?size={size}"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                return ImageData(
                    content=response.content,
                    content_type=response.headers.get('Content-Type', 'image/jpeg')
                )
            else:
                logger.error(f"Failed to fetch image {asset_id}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching image {asset_id}: {e}")
            return None

    def get_asset_full_image_stream(self, asset_id: str):
        """Get full-size image stream from Immich API for streaming response"""
        try:
            url = f"{self.base_url}/api/assets/{asset_id}/original"
            response = self.session.get(url, timeout=60, stream=True)
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', 'image/jpeg')
                return response, content_type
            else:
                logger.error(f"Failed to fetch full image {asset_id}: HTTP {response.status_code}")
                return None, None
                
        except Exception as e:
            logger.error(f"Error fetching full image {asset_id}: {e}")
            return None, None

    def get_albums(self) -> List[Album]:
        """Get all albums from Immich API"""
        try:
            logger.info("Fetching albums from Immich API...")
            response = self.session.get(f"{self.base_url}/api/albums", timeout=30)
            
            if response.status_code == 200:
                albums_data = response.json()
                albums = []
                
                for album_data in albums_data:
                    album = Album(
                        id=album_data.get('id', ''),
                        name=album_data.get('albumName', ''),
                        description=album_data.get('description'),
                        asset_count=album_data.get('assetCount', 0),
                        created_at=album_data.get('createdAt'),
                        updated_at=album_data.get('updatedAt')
                    )
                    albums.append(album)
                
                logger.info(f"Retrieved {len(albums)} albums from Immich")
                return albums
            else:
                logger.error(f"Failed to fetch albums: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching albums: {e}")
            return []
    
    def get_album_assets(self, album_id: str) -> List[Asset]:
        """Get assets from a specific album"""
        try:
            logger.info(f"Fetching assets from album {album_id}...")
            response = self.session.get(f"{self.base_url}/api/albums/{album_id}", timeout=30)
            
            if response.status_code == 200:
                album_data = response.json()
                assets_data = album_data.get('assets', [])
                assets = []
                
                for asset_data in assets_data:
                    asset = Asset(
                        id=asset_data.get('id', ''),
                        type=asset_data.get('type', ''),
                        original_filename=asset_data.get('originalFileName', ''),
                        file_created_at=asset_data.get('fileCreatedAt'),
                        file_modified_at=asset_data.get('fileModifiedAt'),
                        updated_at=asset_data.get('updatedAt'),
                        is_favorite=asset_data.get('isFavorite', False),
                        is_archived=asset_data.get('isArchived', False),
                        duration=asset_data.get('duration')
                    )
                    assets.append(asset)
                
                logger.info(f"Retrieved {len(assets)} assets from album {album_id}")
                return assets
            else:
                logger.error(f"Failed to fetch album {album_id}: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching album {album_id}: {e}")
            return []
    
    def find_albums_by_name(self, album_names: List[str]) -> List[Album]:
        """Find albums by their names and return their IDs"""
        try:
            all_albums = self.get_albums()
            found_albums = []
            
            for album in all_albums:
                if album.name in album_names:
                    found_albums.append(album)
                    logger.info(f"Found album: {album.name} (ID: {album.id}, Assets: {album.asset_count})")
            
            return found_albums
            
        except Exception as e:
            logger.error(f"Error finding albums by name: {e}")
            return []

    def get_random_photos_from_albums(self, album_names: List[str], count: int = 20) -> List[Asset]:
        """Get random photos from specified albums"""
        import random
        
        try:
            # Find albums by their names
            found_albums = self.find_albums_by_name(album_names)
            
            if not found_albums:
                logger.warning(f"No albums found with names: {album_names}")
                return []
            
            # Collect all assets from all albums
            all_assets = []
            for album in found_albums:
                assets = self.get_album_assets(album.id)
                # Filter only images (not videos) for photos
                photo_assets = [asset for asset in assets if asset.type.upper() == 'IMAGE' and not asset.is_archived]
                all_assets.extend(photo_assets)
                logger.debug(f"Album '{album.name}' contributed {len(photo_assets)} photos")
            
            logger.info(f"Collected {len(all_assets)} total photos from {len(found_albums)} albums")
            
            # Return random selection
            if len(all_assets) <= count:
                logger.info(f"Returning all {len(all_assets)} available photos")
                return all_assets
            else:
                random_photos = random.sample(all_assets, count)
                logger.info(f"Returning {count} random photos from {len(all_assets)} total photos")
                return random_photos
                
        except Exception as e:
            logger.error(f"Error getting random photos from albums: {e}")
            return []

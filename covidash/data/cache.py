#Data Cache

import json
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCache:

    def __init__(self, cache_dir: str = 'cahce', max_age_hours: int = 24):
        self.cache_dir = cache_dir
        self.max_age_hours = max_age_hours
        self.memory_cache = {}
        self.cache_metadata = {}
        self.lock = threading.RLock()

        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            logger.info(f"Created cache directory: {self.cache_dir}")

    def _get_cache_file_path(self, key: str) -> str:
        safe_key = key.replace('/', '_').replace('\\', '_')
        return os.path.join(self.cache_dir, f"{safe_key}.json")
    
    def _get_metadata_file_path(self, key: str) -> str:
        safe_key = key.replace('/', '_').replace('\\', '_')
        return os.path.join(self.cache_dir, f"{safe_key}_meta.json")
    
    def _is_cache_valid(self, timestamp_str: str) -> bool:
        try:
            cache_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            current_time = datetime.now()
            age = current_time - cache_time.replace(tzinfo=None)
            return age.total_seconds() < (self.max_age_hours * 3600)
        except Exception as e:
            logger.warning(f"Error parsing cache timestamp: {e}")
            return False
        
    def set(self, key: str, data: Any) -> bool:
        with self.lock:
            try:
                timestamp = datetime.now().isoformat()

                self.memory_cache[key] = {
                    'data': data,
                    'timestamp': timestamp
                }

                self.cache_metadata[key] = {
                    'timestamp': timestamp,
                    'size': len(str(data)) if data else 0,
                    'type': type(data).__name__
                }

                cache_file = self._get_cache_file_path(key)
                meta_file = self._get_metadata_file_path(key)

                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'data': data,
                        'timestamp': timestamp
                    }, f, indent=2, default=str)

                with open(meta_file, 'w', encoding='utf-8') as f:
                    json.dump(self.cache_metadata[key], f, indent=2)

                logger.info(f"Cached data for key: {key}")
                return True
            
            except Exception as e:
                logger.error(f"Error caching data for key {key}: {e}")
                return False
            
    def get(self, key: str, use_file_fallback: bool = True) -> Optional[Any]:
        with self.lock:
            if key in self.memory_cache:
                cache_entry = self.memory_cache[key]
                if self._is_cache_valid(cache_entry['timestamp']):
                    logger.debug(f"Cache hit (memory) for key: {key}")
                    return cache_entry['data']
                else:
                    del self.memory_cache[key]
                    logger.debug(f"Expired cache entry removed from memory: {key}")

            if use_file_fallback:
                try:
                    cache_file = self._get_cache_file_path(key)
                    if os.path.exists(cache_file):
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            cache_entry = json.load(f)

                        if self._is_cache_valid(cache_entry['timestamp']):
                            self.memory_cache[key] = cache_entry
                            logger.debug(f"Cache hit (file) for key: {key}")
                            return cache_entry['data']
                        else:
                            os.remove(cache_file)
                            meta_file = self._get_metadata_file_path(key)
                            if os.path.exists(meta_file):
                                os.remove(meta_file)
                            logger.debug(f"Expired cache file removed: {key}")
                except Exception as e:
                    logger.error(f"Error reading cache file for key {key}: {e}")

        logger.debug(f"Cache miss for key: {key}")
        return None
    
    def delete(self, key: str) -> bool:
        with self.lock:
            success = True

            if key in self.memory_cache:
                del self.memory_cache[key]

            if key in self.cache_metadata:
                del self.cache_metadata[key]

            try:
                cache_file = self._get_cache_file_path(key)
                if os.path.exists(cache_file):
                    os.remove(cache_file)

                meta_file = self._get_metadata_file_path(key)
                if os.path.exists(meta_file):
                    os.remove(meta_file)

            except Exception as e:
                logger.error(f"Error deleting cache files for key {key}: {e}")
                success = False

            logger.info(f"Deleted cache for key: {key}")
            return success
        
    def clear_all(self) -> bool:
        with self.lock:
            success = True

            self.memory_cache.clear()
            self.cache_metadata.clear()

            try:
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith('.json'):
                        file_path = os.path.join(self.cache_dir, filename)
                        os.remove(file_path)

            except Exception as e:
                logger.error(f"Error clearing cache files: {e}")
                success = False

            logger.info("Cleared all cache data")
            return success
        
    def get_cache_info(self) -> Dict:
        with self.lock:
            memory_keys = list(self.memory_cache.keys())
            file_keys = []

            try:
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith('.json') and not filename.endswith('_meta.json'):
                        key = filename[:-5]
                        file_keys.append(key)
            except Exception as e:
                logger.error(f"Error reading cache directory: {e}")

            return {
                'memory_cache': {
                    'keys': memory_keys,
                    'count': len(memory_keys)
                },
                'file_cache': {
                    'keys': file_keys,
                    'count': len(file_keys)
                },
                'cache_dir': self.cache_dir,
                'max_age_hours': self.max_age_hours,
                'metadata': dict(self.cache_metadata)
            }
        
    def cleanup_expired(self) -> int:
        with self.lock:
            removed_count = 0

            expired_memory_keys = []
            for key, cache_entry in self.memory_cache.items():
                if not self._is_cache_valid(cache_entry['timestamp']):
                    expired_memory_keys.append(key)

            for key in expired_memory_keys:
                del self.memory_cache[key]
                if key in self.cache_metadata:
                    del self.cache_metadata[key]
                removed_count += 1

            try:
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith('.json') and not filename.endswith('_meta.json'):
                        file_path = os.path.join(self.cache_dir, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                cache_entry = json.load(f)

                            if not self._is_cache_valid(cache_entry['timestamp']):
                                os.remove(file_path)
                                meta_file = file_path.replace('.json', '_meta.json')
                                if os.path.exists(meta_file):
                                    os.remove(meta_file)
                                removed_count += 1
                        
                        except Exception as e:
                            logger.warning(f"Error checking cache file {filename}: {e}")

            except Exception as e:
                logger.error(f"Error during cache cleanup: {e}")

            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} expired cache entries")

            return removed_count
        
    def get_cache_size(self) -> Dict:
        with self.lock:
            memory_size = 0
            file_size = 0

            for cache_entry in self.memory_cache.values():
                memory_size += len(str(cache_entry))

            try:
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith('.json'):
                        file_path = os.path.join(self.cache_dir, filename)
                        file_size += os.path.getsize(file_path)
            except Exception as e:
                logger.error(f"Error calculating file cache size: {e}")

            return {
                'memory_size_bytes': memory_size,
                'file_size_bytes': file_size,
                'total_size_bytes': memory_size + file_size,
                'memory_size_mb': round(memory_size / (1024 * 1024), 2),
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'total_size_mb': round((memory_size + file_size) / (1024 * 1024), 2)
            }
        
_global_cache = None

def get_cache(cache_dir: str = 'cache', max_age_hours: int = 24) -> DataCache:
    global _global_cache
    if _global_cache is None:
        _global_cache = DataCache(cache_dir, max_age_hours)
    return _global_cache

def cache_covid_data(key: str, data: Any) -> bool:
    cache = get_cache()
    return cache.set(key, data)

def get_covid_data(key: str) -> Optional[Any]:
    cache = get_cache()
    return cache.get(key)

def clear_covid_cache() -> bool:
    cache = get_cache()
    return cache.clear_all()

CACHE_KEYS = {
    'CITIES_DATA': 'cities_data',
    'GLOBAL_DATA': 'global_data',
    'COUNTRIES_DATA': 'countries_data',
    'US_STATES_DATA': 'us_states_data',
    'PROCESSED_DATA': 'processed_data'
}
#Data init module

import logging
from .fetcher import DataFetcher, create_fetcher, fetch_cities_data
from .processor import DataProcessor, process_covid_data, format_for_map
from .cache import DataCache, get_cache, cache_covid_data, get_covid_data, clear_covid_cache, CACHE_KEYS

__version__ = '1.0.0'
__all__ = [
    # Fetcher classes and functions
    'DataFetcher',
    'create_fetcher', 
    'fetch_cities_data',
    
    # Processor classes and functions
    'DataProcessor',
    'process_covid_data',
    'format_for_map',
    
    # Cache classes and functions
    'DataCache',
    'get_cache',
    'cache_covid_data',
    'get_covid_data',
    'clear_covid_cache',
    'CACHE_KEYS'
]

def get_covid_tracker_data(disease_sh_api: str, cdc_api: str, use_cache: bool = True):
    logger = logging.getLogger(__name__)

    cache_key = CACHE_KEYS['PROCESSED_DATA']

    if use_cache:
        cached_data = get_covid_data(cache_key)
        if cached_data:
            logger.info("Using cached COVID data")
            return cached_data
        
    try:
        logger.info("Fetching fresh COVID data")
        fetcher = create_fetcher(disease_sh_api, cdc_api)
        raw_data = fetcher.fetch_major_cities_data()

        if not raw_data:
            logger.error("Failed to fetch COVID data")
            return None
        
        processor = DataProcessor()
        processed_data = processor.process_cities_data(raw_data)
        frontend_data = processor.format_for_fronted(processed_data)

        if use_cache:
            cache_covid_data(cache_key, frontend_data)

        logger.info(f"Succesfully processed data for {len(processed_data)} cities")
        return frontend_data
    
    except Exception as e:
        logger.error(f"Error getting COIVD tracker data: {e}")
        return None
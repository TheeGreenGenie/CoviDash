#Main app

import os
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_apscheduler import APScheduler

from data import get_covid_tracker_data, get_cache, clear_covid_cache, CACHE_KEYS
from config import app_config
from utils.scheduler import setup_scheduler, update_covid_data

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_name=None):
    #Return flask app
    app = Flask(__name__)

    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app.config.from_object(app_config[config_name])

    scheduler = APScheduler()
    scheduler.init_app(app)

    app.covid_data = None
    app.last_update = None
    app.scheduler = scheduler

    def initialize_app():
        logger.info("Initializing COVID-19 Tracker application...")

        try:
            app.covid_data = get_covid_tracker_data(
                app.config['DISEASE_SH_API'],
                app.config['CDC_API_BASE'],
                use_cache=True
            )
            app.last_update = datetime.now().isoformat()
            logger.info("Initial COVID data loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load intial COVID data: {e}")
            app.covid_data = None

        if not scheduler.running:
            scheduler.start()
            logger.info("Scheduler started for automatic data updates")

    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/api/covid-data')
    def api_covid_data():
        try:
            if app.covid_data is None:
                logger.info("No cached data avaqilable, fetching fresh data...")
                app.covid_data = get_covid_tracker_data(
                    app.config['DISEASE_SH_API'],
                    app.config['CDC_API_BASE'],
                    use_cache=True
                )
                app.last_update = datetime.now().isoformat()

            if app.covid_data:
                response_data = app.covid_data.copy()
                response_data['server_timestamp'] = datetime.now().isoformat()
                response_data['last_update'] = app.last_update

                return jsonify(response_data)
            else:
                return jsonify({
                    'error': 'Failed to fetch COVID data',
                    'cities': [],
                    'statistics': {},
                    'metadata': {
                        'error': True,
                        'message': 'Data temporarily unavailable'
                    }
                }), 503
            
        except Exception as e:
            logger.error(f"Error in /api/coivd-data endpoint: {e}")
            return jsonify({
                'error': str(e),
                'cities': [],
                'statistics': {},
                'metadata': {
                    'error': True,
                    'message': 'Internal server error'
                }
            }), 500
        
    @app.route('/api/health')
    def api_health():
        try:
            cache = get_cache()
            cache_info = cache.get_cache_info()
            
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'data_available': app.covid_data is not None,
                'last_data_update': app.last_update,
                'cache_status': {
                    'memory_entries': cache_info['memory_cache']['count'],
                    'file_entries': cache_info['file_cache']['count']
                },
                'scheduler_running': scheduler.running if scheduler else False,
                'config': {
                    'update_interval_hours': app.config.get('UPDATE_INTERVAL_HOURS', 24),
                    'debug_mode': app.config.get('DEBUG', False)
                }
            }
            
            try:
                from data.fetcher import DataFetcher
                fetcher = DataFetcher(
                    app.config['DISEASE_SH_API'],
                    app.config['CDC_API_BASE']
                )
                api_summary = fetcher.get_data_summary()
                health_status['api_status'] = api_summary['sources']
                
            except Exception as e:
                health_status['api_status'] = {'error': str(e)}
                health_status['status'] = 'degraded'
            
            return jsonify(health_status)
            
        except Exception as e:
            logger.error(f"Error in /api/health endpoint: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
        
    @app.route('/api/refresh', methods=['POST'])
    def api_refresh():
        try:
            logger.info("Manual data refresh requested")

            clear_covid_cache()

            app.covid_data = get_covid_tracker_data(
                app.config['DISEASE_SH_API'],
                app.config['CDC_API_BASE'],
                use_cache=False
            )
            app.last_update = datetime.now().isoformat()

            if app.covid_data:
                cities_count = len(app.covid_data.get('cities', []))
                return jsonify({
                    'success': True,
                    'message': f"Data refreshed successfully - {cities_count} cities updated",
                    'timestamp': app.last_update,
                    'cities_count': cities_count
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to refresh data',
                    'timestamp': datetime.now().isoformat()
                }), 500
            
        except Exception as e:
            logger.error(f"Error in /api/refresh endpoint: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
        
    @app.route('/api/cache/info')
    def api_cache_info():
        try:
            cache = get_cache()
            cache_info = cache.get_cache_info()
            cache_size = cache.get_cache_size()

            return jsonify({
                'cache_info': cache_info,
                'cache_size': cache_size,
                'timestamp': datetime.now().isoformat()
            })
        
        except Exception as e:
            logger.error(f"Error in /api/cache/info endpoint: {e}")
            return jsonify({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
        
    @app.route('/api/cache/clear', methods=['POST'])
    def api_cache_clear():
        try:
            success = clear_covid_cache()
            app.covid_data = None
            app.last_update = None

            return jsonify({
                'success': success,
                'message': 'Cache cleared successfully' if success else 'Failed to clear cache',
                'timestamp': datetime.now().isoformat()                
            })
        
        except Exception as e:
            logger.error(f"Error in /api/cache/clear endpoint: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
        
    @app.route('/api/statistics')
    def api_statistics():
        try:
            if app.covid_data and 'statistics' in app.covid_data:
                stats = app.covid_data['statistics'].copy()
                stats['server_timestamp'] = datetime.now().isoformat()
                stats['last_update'] = app.last_update
                return jsonify(stats)
            else:
                return jsonify({
                    'error': 'No statistics available',
                    'timestamp': datetime.now().isoformat()                    
                }), 404
            
        except Exception as e:
            logger.error(f"Error in /api/statistics endpoint: {e}")
            return jsonify({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
        
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'error': 'Not found',
            'message': 'The requested resource was not found',
            'timestamp': datetime.now().isoformat()
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred',
            'timestamp': datetime.now().isoformat()
        }), 500
    
    @scheduler.task('interval', id='update_covid_data', hours=app.config.get('UPDATE_INTERVAL_HOURS', 24))
    def scheduled_update():
        logger.info("Starting scheduled COVID data update...")

        try:
            new_data = get_covid_tracker_data(
                app.config['DISEASE_SH_API'],
                app.config['CDC_API_BASE'],
                use_cache=False
            )

            if new_data:
                app.covid_data = new_data
                app.last_update = datetime.now().isoformat()
                cities_count = len(new_data.get('cities', []))
                logger.info(f"Scheduled update completed - {cities_count} cities updated")
            else:
                logger.error("Scheduled update failed - no data received")

        except Exception as e:
            logger.error(f"Error in scheduled update: {e}")

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    logger.info(f"Starting COVID-19 Tracker on port {port} (debug={debug})")
    app.run(host='0.0.0.0', port=port, debug=debug)
#Scheduler Utilities

import logging
from datetime import datetime
from typing import Optional, Callable
from flask_apscheduler import APScheduler
from data import get_covid_tracker_data, clear_covid_cache, get_cache

logger = logging.getLogger(__name__)

class CovidScheduler:

    def __init__(self, scheduler: APScheduler):
        self.scheduler = scheduler
        self.update_job_id = 'covid_data_update'
        self.cleanup_job_id = 'cache_cleanup'

    def setup_data_update_job(self,
                              update_function: Callable,
                              interval_hours: int = 24,
                              immediate: bool = False) -> bool:
        try:
            if self.scheduler.get_job(self.update_job_id):
                self.scheduler.remove_job(self.update_job_id)
                logger.info(f"Removed existing job: {self.update_job_id}")
            
            self.scheduler.add_job(
                func=update_function,
                trigger='interval',
                hours=interval_hours,
                id=self.update_job_id,
                name='COVID Data Update',
                replace_existing=True,
                max_instances=1,
                coalesce=True,
                misfire_grace_time=3600
            )

            logger.info(f"Scheduled COVID data update every {interval_hours} hours")

            if immediate:
                self.run_update_now(update_function)

            return True
        
        except Exception as e:
            logger.error(f"Failed to setup data update job: {e}")
            return False
        
    def setup_cache_cleanup_job(self,
                                cleanup_function: Callable,
                                interval_hours: int = 6) -> bool:
        try:
            if self.scheduler.get_job(self.cleanup_job_id):
                self.scheduler.remove_job(self.cleanup_job_id)
                logger.info(f"Removed existing job: {self.cleanup_job_id}")

            self.scheduler.add_job(
                func=cleanup_function,
                trigger='interval',
                hours=interval_hours,
                id=self.cleanup_job_id,
                name='Cache Cleanup',
                replace_existing=True,
                max_instances=1,
                coalesce=True,
                misfire_grace_time=1800  # 30 minutes grace period
            )
            
            logger.info(f"Scheduled cache cleanup every {interval_hours} hours")
            return True
        
        except Exception as e:
            logger.error(f"Failed to setup cache cleanup job: {e}")
            return False
        
    def run_update_now(self, update_function: Callable) -> bool:
        try:
            logger.info("Running immediate COVID data update...")
            update_function()
            return True
        
        except Exception as e:
            logger.error(f"Immediate update failed: {e}")
            return False
        
    def get_job_status(self) -> dict:
        status = {
            'scheduler_running': self.scheduler.running,
            'jobs': {},
            'timestamp': datetime.now().isoformat()            
        }

        update_job = self.scheduler.get_job(self.update_job_id)
        if update_job:
            status['jobs']['data_update'] = {
                'id': update_job.id,
                'name': update_job.name,
                'next_run': update_job.next_run_time.isoformat() if update_job.next_run_time else None,
                'trigger': str(update_job.trigger)                
            }
        else:
            status['jobs']['data_update'] = None

        cleanup_job = self.scheduler.get_job(self.cleanup_job_id)
        if cleanup_job:
            status['jobs']['cache_cleanup'] = {
                'id': cleanup_job.id,
                'name': cleanup_job.name,
                'next_run': cleanup_job.next_run_time.isoformat() if cleanup_job.next_run_time else None,
                'trigger': str(cleanup_job.trigger)                
            }
        else:
            status['jobs']['cache_cleanup'] = None

        return status
    
    def pause_jobs(self) -> bool:
        try:
            if self.scheduler.get_job(self.update_job_id):
                self.scheduler.pause_job(self.update_job_id)
            if self.scheduler.get_job(self.cleanup_job_id):
                self.scheduler.pause_job(self.cleanup_job_id)

            logger.info("All scheduled jobs paused")
            return True
        
        except Exception as e:
            logger.error(f"Failed to pause jobs: {e}")
            return False
        
    def resume_jobs(self) -> bool:
        try:
            if self.scheduler.get_job(self.update_job_id):
                self.scheduler.resume_job(self.update_job_id)
            if self.scheduler.get_job(self.cleanup_job_id):
                self.scheduler.resume_job(self.cleanup_job_id)

            logger.info("All scheduled jobs resumed")
            return True
        
        except Exception as e:
            logger.error(f"Failed to resume jobs: {e}")
            return False
        
def setup_scheduler(app, scheduler: APScheduler) -> CovidScheduler:

    covid_scheduler = CovidScheduler(scheduler)

    def update_covid_data():
        try:
            logger.info("Scheduled COVID data update strating...")

            new_data = get_covid_tracker_data(
                app.config['DISEASE_SH_API'],
                app.config['CDC_API_BASE'],
                use_cache=False
            )

            if new_data:
                app.covid_data = new_data
                app.last_update = datetime.now().isoformat()
                cities_count = len(new_data.get('cities', []))
                logger.info(f"Scheduled update completed successfully - {cities_count} cities updated")
            else:
                logger.error("Scheduled update failed -  no data received")

        except Exception as e:
            logger.error(f"Error in scheduled COVID data update: {e}")

    def cleanup_cache():
        try:
            cache = get_cache()
            removed_count = cache.cleanup_expired()

            if removed_count > 0:
                logger.info(f"Cache cleanup completed - removed {removed_count} expired entries")
            else:
                logger.debug("Cache cleanup completed - no expired entries found")

        except Exception as e:
            logger.error(f"Error in cache cleanup:{e}")

    update_interval = app.config.get('UPDATE_INTERVAL_HOURS', 24)
    covid_scheduler.setup_data_update_job(update_covid_data, update_interval)
    covid_scheduler.setup_cache_cleanup_job(cleanup_cache, 6)

    return covid_scheduler

def create_manual_update_task(app) -> Callable:

    def manual_update():
        try:
            logger.info("Manual COVID data update requested...")

            new_data = get_covid_tracker_data(
                app.config['DISEASE_SH_API'],
                app.config['CDC_API_BASE'],
                use_cache=False
            )            

            if new_data:
                app.covid_data = new_data
                app.last_update = datetime.now().isoformat()
                cities_count = len(new_data.get('cities', []))
                logger.info(f"Manual update completed = {cities_count} cities updated")
                return True
            else:
                logger.error("Manual update failed - no data receieved")
                return False
            
        except Exception as e:
            logger.error(f"Error in manual update: {e}")
            return False
        
    return manual_update

def update_covid_data():

    logger.warning("Using legacy update_covid_data function - consider using app-specific updates")
    
    try:
        
        clear_covid_cache()
        data = get_covid_tracker_data(
            "https://disease.sh/v3/covid-19",
            "https://data.cdc.gov/resource",
            use_cache=False
        )
        
        if data:
            logger.info("Legacy update completed successfully")
        else:
            logger.error("Legacy update failed")
            
    except Exception as e:
        logger.error(f"Error in legacy update: {e}")
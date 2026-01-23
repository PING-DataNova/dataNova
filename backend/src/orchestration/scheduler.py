"""
Scheduler pour l'exécution automatique hebdomadaire

Utilise APScheduler pour planifier les exécutions.
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import structlog

from src.config import settings
from src.orchestration.pipeline import run_pipeline

logger = structlog.get_logger()


def scheduled_job():
    """Job planifié qui exécute le pipeline."""
    logger.info("job_planifié_démarré")
    
    try:
        result = run_pipeline()
        logger.info("job_planifié_terminé", result=result)
    except Exception as e:
        logger.error("job_planifié_erreur", error=str(e), exc_info=True)


def start_scheduler():
    """
    Démarre le scheduler en mode bloquant.
    
    Configure l'exécution hebdomadaire selon le cron configuré.
    Par défaut: chaque lundi à 8h00
    """
    
    if not settings.scheduler_enabled:
        logger.warning("scheduler_désactivé")
        return
    
    scheduler = BlockingScheduler()
    
    # Ajouter le job avec le cron configuré
    trigger = CronTrigger.from_crontab(settings.cron_schedule)
    
    scheduler.add_job(
        scheduled_job,
        trigger=trigger,
        id="weekly_regulatory_monitoring",
        name="Veille Réglementaire Hebdomadaire",
        replace_existing=True,
    )
    
    logger.info(
        "scheduler_configuré",
        cron=settings.cron_schedule,
        next_run=scheduler.get_jobs()[0].next_run_time if scheduler.get_jobs() else None
    )
    
    try:
        logger.info("scheduler_démarré")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("scheduler_arrêté")
        scheduler.shutdown()


# TODO (DEV 3): Ajouter la gestion des erreurs et retry logic

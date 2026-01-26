"""Point d'entrée principal de l'application."""

import argparse
import sys
from pathlib import Path

import structlog

from src.config import settings
from src.utils.logging_config import setup_logging

logger = structlog.get_logger()


def main():
    """Point d'entrée principal."""
    # Setup logging
    setup_logging(settings.log_level, settings.log_file)

    parser = argparse.ArgumentParser(description="Agent 1 - Veille Réglementaire")
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Exécuter l'agent une seule fois (mode développement)",
    )
    parser.add_argument(
        "--log-level",
        default=settings.log_level,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Niveau de log",
    )

    args = parser.parse_args()

    logger.info(
        "démarrage_agent",
        mode="once" if args.run_once else "scheduler",
        company_profile=settings.default_company_profile,
    )

    try:
        if args.run_once:
            # Mode exécution unique (développement)
            from src.orchestration.pipeline import run_pipeline

            logger.info("exécution_unique_démarrée")
            run_pipeline()
            logger.info("exécution_unique_terminée")
        else:
            # Mode scheduler (production)
            from src.orchestration.scheduler import start_scheduler

            logger.info("scheduler_démarré", cron=settings.cron_schedule)
            start_scheduler()

    except KeyboardInterrupt:
        logger.info("arrêt_manuel")
        sys.exit(0)
    except Exception as e:
        logger.error("erreur_fatale", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

"""APScheduler-driven worker.

Runs two jobs:
  * every ``SCHEDULER_POLL_SECONDS``: publish due posts;
  * daily: refresh tokens nearing expiry.

Can be embedded in the web process (``start_scheduler``) or run standalone
(``python -m app.scheduler.worker``). For production on a VPS, run it as its own
process so web restarts don't disturb scheduling.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.db import SessionLocal
from app.scheduler.service import refresh_expiring_tokens, run_due_posts

log = logging.getLogger("smap.scheduler")


def _publish_job() -> None:
    session = SessionLocal()
    try:
        count = run_due_posts(session)
        if count:
            log.info("Processed %s due post(s)", count)
    except Exception:  # never let a job exception kill the scheduler
        log.exception("publish job failed")
    finally:
        session.close()


def _refresh_job() -> None:
    session = SessionLocal()
    try:
        n = refresh_expiring_tokens(session)
        if n:
            log.info("Refreshed %s token(s)", n)
    except Exception:
        log.exception("token refresh job failed")
    finally:
        session.close()


def _configure(scheduler) -> None:
    scheduler.add_job(
        _publish_job,
        IntervalTrigger(seconds=settings.scheduler_poll_seconds),
        id="publish_due_posts",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    scheduler.add_job(
        _refresh_job,
        CronTrigger(hour=3, minute=0),  # 03:00 server time daily
        id="refresh_tokens",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )


def start_scheduler() -> BackgroundScheduler:
    """Start a background scheduler (for embedding in the web process)."""
    scheduler = BackgroundScheduler(timezone="UTC")
    _configure(scheduler)
    scheduler.start()
    log.info("Background scheduler started (poll=%ss)", settings.scheduler_poll_seconds)
    return scheduler


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    scheduler = BlockingScheduler(timezone="UTC")
    _configure(scheduler)
    log.info("Scheduler worker running (poll=%ss). Ctrl-C to stop.", settings.scheduler_poll_seconds)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler worker stopping")


if __name__ == "__main__":
    main()

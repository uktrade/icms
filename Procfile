web: scripts/entry.sh
celery_worker: celery --app=config.celery:app worker --loglevel=INFO -Q celery,mail,reports
celery_beat: celery --app=config.celery:app beat --loglevel=INFO

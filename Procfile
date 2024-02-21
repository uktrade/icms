web: bash scripts/entry.sh
celery_worker: celery --app=config.celery:app worker --loglevel=INFO -Q celery,mail
celery_beat: celery --app=config.celery:app beat --loglevel=INFO

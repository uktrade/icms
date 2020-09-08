import os
from psycogreen.gevent import patch_psycopg


ICMS_WEB_PORT = os.environ.get("ICMS_WEB_PORT", 8080)
ICMS_WORKER_CONNECTIONS = int(os.environ.get("ICMS_WORKER_CONNECTIONS", 1000))


bind = f"0:{ICMS_WEB_PORT}"
worker_class = "gevent"
worker_connections = f"{ICMS_WORKER_CONNECTIONS}"
accesslog = "-"
errorlog = "-"
proc_name = "icms"


def post_fork(server, worker):
    patch_psycopg()
    worker.log.info("Enabled async Psycopg2")

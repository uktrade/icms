import os

import gunicorn

# Gunicorn settings: https://docs.gunicorn.org/en/stable/settings.html
ICMS_WEB_PORT = os.environ.get("ICMS_WEB_PORT", 8080)
bind = f"0:{ICMS_WEB_PORT}"

# https://docs.gunicorn.org/en/stable/settings.html#worker-class
worker_class = "gevent"

# https://docs.gunicorn.org/en/stable/design.html#how-many-workers
# From the docs:
#   Gunicorn should only need 4-12 worker processes to handle hundreds or
#   thousands of requests per second.
# Try with 4 for now rather than something more complicated (2-4 x $(NUM_CORES))
workers = 4
worker_connections = int(os.environ.get("ICMS_WORKER_CONNECTIONS", 1000))

# '-' makes gunicorn log to stdout.
accesslog = "-"

# '-' makes gunicorn log to stderr.
errorlog = "-"

proc_name = "icms"
gunicorn.SERVER_SOFTWARE = proc_name

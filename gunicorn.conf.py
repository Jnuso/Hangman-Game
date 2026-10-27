"""One shared game store, with threads for overlapping HTTP requests."""

import os

bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
workers = 1
worker_class = "gthread"
threads = 4
reload = False
# This app needs HTTP only; its non-root container user has no writable home.
control_socket_disable = True
accesslog = "-"
errorlog = "-"

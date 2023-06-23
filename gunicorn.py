from multiprocessing import cpu_count

bind = "unix:/tmp/gunicorn.sock"

# Maximum number of backlog requests to hold onto before users get error messages.
backlog = 100
# workers = cpu_count() * 2 + 1
workers = 2

# Do not support persistent connections. Close after each request.
worker_class = "sync"

timeout = 30
keepalive = 2
spew = False
daemon = False
raw_env = []

pidfile = "/tmp/gunicorn_vm_api.pid"

umask = 755
user = 1000
group = 1000
tmp_upload_directory = None

# Log errors received to stdout with `-`
error_log = "-"
access_log = "-"

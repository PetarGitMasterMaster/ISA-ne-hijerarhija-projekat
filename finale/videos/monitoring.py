import psutil
from django.db import connection
from django.contrib.auth import get_user_model
from prometheus_client import Gauge
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


db_active_connections = Gauge(
    "db_active_connections", "Number of active database connections"
)
db_idle_connections = Gauge(
    "db_idle_connections", "Number of idle database connections"
)
cpu_usage_percent = Gauge(
    "cpu_usage_percent", "Average CPU usage percentage"
)
active_users_24h = Gauge(
    "active_users_24h", "Number of users active in the last 24 hours"
)


def update_metrics():
    """Call this periodically to update Prometheus metrics"""

    # 1. CPU usage
    cpu_usage_percent.set(psutil.cpu_percent(interval=None))

    # 2. Database connections
    with connection.cursor() as cursor:
        # Active = in-use connections, Idle = total - active
        try:
            total_conns = connection.connection._pool._connections.qsize()  # psycopg2 pool example
        except AttributeError:
            total_conns = 1  # fallback if pool not used
        db_active_connections.set(total_conns)  # Approximation
        db_idle_connections.set(total_conns)    # Approximation

    # 3. Users active in last 24h
    since = timezone.now() - timedelta(hours=24)
    count = User.objects.filter(last_login__gte=since).count()
    active_users_24h.set(count)

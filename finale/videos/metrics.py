import psutil
from django.db import connection
from django.contrib.auth import get_user_model
from prometheus_client import Gauge
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

db_active_connections = Gauge("db_active_connections", "Active DB connections")
db_idle_connections = Gauge("db_idle_connections", "Idle DB connections")
cpu_usage_percent = Gauge("cpu_usage_percent", "CPU usage percent")
active_users_24h = Gauge("active_users_24h", "Active users in last 24h")

memory_used_bytes = Gauge("memory_used_bytes", "Used memory")
memory_free_bytes = Gauge("memory_free_bytes", "Free memory")

disk_used_bytes = Gauge("disk_used_bytes", "Used disk")
disk_free_bytes = Gauge("disk_free_bytes", "Free disk")

network_bytes_sent_total = Gauge("network_bytes_sent_total", "Bytes sent")
network_bytes_recv_total = Gauge("network_bytes_recv_total", "Bytes received")


def update_metrics():
    cpu_usage_percent.set(psutil.cpu_percent())

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT count(*) FILTER (WHERE state='active'),
                   count(*) FILTER (WHERE state='idle')
            FROM pg_stat_activity
            WHERE datname = current_database();
        """)
        active, idle = cursor.fetchone()
        db_active_connections.set(active)
        db_idle_connections.set(idle)

    since = timezone.now() - timedelta(hours=24)
    active_users_24h.set(
        User.objects.filter(last_login__gte=since).count()
    )

    mem = psutil.virtual_memory()
    memory_used_bytes.set(mem.used)
    memory_free_bytes.set(mem.available)

    disk = psutil.disk_usage('/')
    disk_used_bytes.set(disk.used)
    disk_free_bytes.set(disk.free)

    net = psutil.net_io_counters()
    network_bytes_sent_total.set(net.bytes_sent)
    network_bytes_recv_total.set(net.bytes_recv)

from .metrics import update_metrics

class PrometheusMetricsMiddleware:
    """Update some real-time metrics on every request"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        update_metrics()  # update CPU, DB, active users
        response = self.get_response(request)
        return response

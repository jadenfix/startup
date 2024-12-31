# startup/services/metrics.py
from prometheus_client import start_http_server, Counter
from config.config import config
import time


REQUEST_COUNT = Counter("request_count", "Total number of requests")

def process_request():
    REQUEST_COUNT.inc()
    print("Request processed")

def main():
    start_http_server(config.PROMETHEUS_PORT)
    print(f"Prometheus metrics at http://localhost:{config.PROMETHEUS_PORT}")
    while True:
        process_request()
        time.sleep(1)


if __name__ == "__main__":
    main()
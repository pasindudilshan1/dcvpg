from prometheus_client import start_http_server, Counter, Histogram
import os
import threading

# Core metrics for DCVPG
PIPELINE_RUNS = Counter(
    'dcvpg_pipeline_runs_total',
    'Total number of pipeline runs validated',
    ['pipeline_name', 'contract_name']
)

PIPELINE_VIOLATIONS = Counter(
    'dcvpg_pipeline_violations_total',
    'Number of contract violations detected',
    ['pipeline_name', 'contract_name', 'violation_type']
)

QUARANTINE_EVENTS = Counter(
    'dcvpg_quarantine_events_total',
    'Number of batches quarantined',
    ['pipeline_name', 'contract_name']
)

VALIDATION_DURATION = Histogram(
    'dcvpg_validation_duration_seconds',
    'Time taken to validate a batch',
    ['pipeline_name', 'contract_name']
)

def start_metrics_server(port=9090):
    """
    Start the Prometheus metrics endpoint in a background thread.
    Can be loaded directly as a Fastapi/WSGI endpoint in prod via middleware too.
    """
    # Don't double-start in dev/testing
    if os.environ.get('DCVPG_TESTING') != '1':
         server_thread = threading.Thread(target=start_http_server, args=(port,), daemon=True)
         server_thread.start()
         print(f"Prometheus metrics exposed on port {port}")

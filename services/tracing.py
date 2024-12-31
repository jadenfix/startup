# startup/services/tracing.py
# Implement tracing setup here (e.g., using OpenTelemetry or similar)
# This file can be kept empty for now if you're not immediately using tracing
import logging
import opentracing
from jaeger_client import Config as JaegerConfig
from config.config import config
import json

def initialize_tracer(service_name):
    config = JaegerConfig(
        config={
            'sampler': {
                'type': 'const',
                'param': 1,
            },
            'logging': True,
             'reporter_batch_size':1
        },
        service_name=service_name,
        validate=True,
    )
    return config.initialize_tracer()


tracer = initialize_tracer("food-delivery-backend")

if __name__ == '__main__':
    with tracer.start_span('example-span') as scope:
       scope.log_kv({'event': 'test-log','test':'This is a test log from tracing'})
       logger = logging.getLogger('backend_logger')
       logger.info('test-log')
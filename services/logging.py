# startup/services/logging.py
import logging
from elasticsearch import Elasticsearch
from config.config import config


es = Elasticsearch([{"host": config.ELASTICSEARCH_HOST, "port": config.ELASTICSEARCH_PORT}])

logger = logging.getLogger("backend_logger")
logger.setLevel(logging.INFO)

class ElasticsearchHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        es.index(index="backend_logs", document={"log": log_entry})

handler = ElasticsearchHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

if __name__ == "__main__":
    logger.info("Logging initialized")
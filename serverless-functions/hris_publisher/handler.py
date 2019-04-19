import cis_logger
import logging
import socket
import sys

import cis_publisher
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all


patch_all()


def setup_logging():
    logger = logging.getLogger()
    for h in logger.handlers:
        logger.removeHandler(h)
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(cis_logger.JsonFormatter(extra={"hostname": socket.gethostname()}))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)

    # Quiet botocore verbose logging...
    logging.getLogger("botocore").setLevel(logging.WARNING)
    return logger


def handle(event, context={}):
    """Handle the publishing of users."""
    logger = setup_logging()
    hris = cis_publisher.hris.HRISPublisher(context=context)
    if isinstance(event, list):
        hris.publish(user_ids=event)
    else:
        hris.publish()
    return 200

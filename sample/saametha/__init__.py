import datetime
import logging
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
import azure.functions as func
from saametha_main import Saametha

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')

    sm = Saametha()
    sm.init()
    logging.info('Python timer trigger function ran at %s', utc_timestamp)
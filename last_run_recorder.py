import datetime

from loguru import logger

import collector_cookie


class LastRunRecorder:

    def __init__(self):
        pass

    def read_date_of_last_run(self, nid):
        logger.info("Trying to read the date of last run...")
        cookie = collector_cookie.read_cookie(nid)
        if cookie:
            date_of_last_run = cookie.date_of_last_run
            return date_of_last_run
        logger.info("Could not read cookie.")
        return -1

    def prepare_visit(self, nid: str) -> None:
        pass

    def finish_visit(self, nid: str) -> None:
        self.write_date_of_last_run(nid)

    def write_date_of_last_run(self, nid):
        cookie = collector_cookie.CollectorCookie(nid, datetime.date.today())
        collector_cookie.write_cookie(cookie)

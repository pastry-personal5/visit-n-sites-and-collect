import datetime

from loguru import logger

from src.visit_n_sites_and_collect.collector_cookie import CollectorCookie
from src.visit_n_sites_and_collect.collector_cookie import CollectorCookieController


class LastRunRecorder:

    def __init__(self):
        self.collector_cookie_controller = CollectorCookieController()

    def read_date_of_last_run(self, nid) -> datetime.date:
        logger.info("Trying to read the date of last run...")
        cookie = self.collector_cookie_controller.read_cookie(nid)
        if cookie:
            date_of_last_run = cookie.date_of_last_run
            return date_of_last_run
        logger.info("Could not read cookie.")
        return None

    def prepare_visit(self, nid: str) -> None:
        pass

    def finish_visit(self, nid: str) -> None:
        self._write_date_of_last_run(nid)

    def _write_date_of_last_run(self, nid):
        cookie = CollectorCookie(nid, datetime.date.today())
        self.collector_cookie_controller.write_cookie(cookie)

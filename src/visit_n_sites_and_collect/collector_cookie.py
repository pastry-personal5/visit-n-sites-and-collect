import datetime
import os
import yaml

from loguru import logger

from src.visit_n_sites_and_collect.constants import Constants


class CollectorCookie:
    nid = None
    date_of_last_run = None  # Type of |date_of_last_run| is Python |datetime.date|.

    def __init__(self, nid, date_of_last_run) -> None:
        self.nid = nid
        self.date_of_last_run = date_of_last_run


class CollectorCookieController:

    def __init__(self):
        pass

    def read_cookie(self, nid: str) -> CollectorCookie:
        file_path = self._create_cookie_file_path(nid)
        return self._read_cookie_from_file(file_path)

    def write_cookie(self, cookie: CollectorCookie) -> None:
        assert cookie.nid is not None
        file_path = self._create_cookie_file_path(cookie.nid)
        self._write_cookie_to_file(file_path, cookie)

    # |nid| means Naver ID.
    def _create_cookie_file_path(self, nid: str) -> str:
        assert nid is not None
        cookie_file_name = f"{nid}.cookie.yaml"
        file_path = os.path.join(Constants.data_dir_path, cookie_file_name)
        return file_path

    def _read_cookie_from_file(self, file_path: str) -> CollectorCookie:
        try:
            f = open(file_path, "rb")
            content = yaml.safe_load(f)
            nid = content["nid"]
            date_of_last_run_as_str = content["date_of_last_run"]
            date_of_last_run = datetime.date.fromisoformat(date_of_last_run_as_str)
            cookie = CollectorCookie(nid, date_of_last_run)
            f.close()
            return cookie
        except IOError:
            # There can be no cookie. i.e. After installation.
            return None

    def _write_cookie_to_file(self, file_path: str, cookie: CollectorCookie) -> None:
        """
        Write as a YAML file.
        ---
        nid: foo
        date_of_last_run: bar
        ---
        """
        assert cookie.nid is not None
        nid = cookie.nid
        content = {}
        content["nid"] = nid
        date_of_last_run = cookie.date_of_last_run
        content["date_of_last_run"] = "%04d-%02d-%02d" % (
            date_of_last_run.year,
            date_of_last_run.month,
            date_of_last_run.day,
        )
        try:
            f = open(file_path, "wb")
            f.write(yaml.safe_dump(content, default_style='"').encode("utf-8"))
            f.close()
        except IOError as e:
            logger.error("An IOError occurred.")
            logger.error(f"Error was {e}")

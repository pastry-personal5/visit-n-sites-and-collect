import datetime
import yaml

from loguru import logger


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
        filepath = self._create_cookie_filepath(nid)
        return self._read_cookie_from_file(filepath)

    def write_cookie(self, cookie: CollectorCookie) -> None:
        assert cookie.nid is not None
        filepath = self._create_cookie_filepath(cookie.nid)
        self._write_cookie_to_file(filepath, cookie)

    # |nid| means Naver ID.
    def _create_cookie_filepath(self, nid: str) -> str:
        assert nid is not None
        filepath = f"{nid}.cookie.yaml"
        return filepath

    def _read_cookie_from_file(self, filepath: str) -> CollectorCookie:
        try:
            f = open(filepath, "rb")
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

    def _write_cookie_to_file(self, filepath: str, cookie: CollectorCookie) -> None:
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
        content["date_of_last_run"] = "%04d-%002d-%02d" % (
            date_of_last_run.year,
            date_of_last_run.month,
            date_of_last_run.day,
        )
        try:
            f = open(filepath, "wb")
            f.write(yaml.safe_dump(content, default_style='"').encode("utf-8"))
            f.close()
        except IOError as e:
            logger.error("An IOError has been occurred.")
            logger.error(f"Error was {e}")

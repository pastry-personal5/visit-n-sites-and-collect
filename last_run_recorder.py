import datetime

import collector_cookie


def read_date_of_last_run(nid):
    cookie = collector_cookie.read_cookie(nid)
    if cookie:
        date_of_last_run = cookie.date_of_last_run
        return date_of_last_run
    else:
        return -1


def write_date_of_last_run(nid):
    cookie = collector_cookie.CollectorCookie(nid, datetime.date.today())
    collector_cookie.write_cookie(cookie)

import datetime

import collector_cookie


def read_last_run(nid):
    config = collector_cookie.read_link_publisher_config(nid)
    if config:
        the_day_of_last_run = datetime.date.fromisoformat(config)
        return the_day_of_last_run
    else:
        return -1


def write_last_run(nid):
    collector_cookie.write_link_publisher_config(nid)

import datetime

import last_run_recorder


def calculate_last_page_index(days):
    MAX_PAGE_INDEX = 10
    last_page_index = days
    if last_page_index > MAX_PAGE_INDEX:
        last_page_index = MAX_PAGE_INDEX
    elif last_page_index < 1:
        last_page_index = 1
    return last_page_index


def create_publisher_urls_to_visit_based_on_last_page_index(last_page_index):
    TARGET_BASE_URL_LIST = [
        # The base URL to start with
        'https://www.clien.net/service/board/jirum',
        'https://www.clien.net/service/board/park'
    ]

    TEMPLATE_LIST = [
        f'https://www.clien.net/service/board/jirum?&od=T31&category=0&po=%d',
        f'https://www.clien.net/service/board/park?&od=T31&category=0&po=%d',
    ]

    assert len(TARGET_BASE_URL_LIST) == len(TEMPLATE_LIST)

    urls = []

    index = 0
    for base_url in TARGET_BASE_URL_LIST:
        for i in range(0, last_page_index + 1):
            if i == 0:
                urls.append(base_url)
            else:
                template = TEMPLATE_LIST[index]
                urls.append(template % (i))
        index += 1
    return urls


def create_publisher_urls_to_visit(nid):
    MAX_PAGE_INDEX = 10
    last_page_index = MAX_PAGE_INDEX
    the_day_of_last_run = last_run_recorder.read_last_run(nid)
    if the_day_of_last_run != -1:
        today = datetime.date.today()
        days = (today - the_day_of_last_run).days
        print(f'[INFO] The day difference was (%d).' % (days))
        last_page_index = calculate_last_page_index(days)
    else:
        last_page_index = 1

    urls = create_publisher_urls_to_visit_based_on_last_page_index(last_page_index)

    return urls


def record_successful_visit(nid):
    last_run_recorder.write_last_run(nid)

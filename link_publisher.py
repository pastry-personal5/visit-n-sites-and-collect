import datetime

import link_publisher_config


def calculate_last_page_index(days):
    MAX_PAGE_INDEX = 10
    last_page_index = days
    if last_page_index > MAX_PAGE_INDEX:
        last_page_index = MAX_PAGE_INDEX
    elif last_page_index < 1:
        last_page_index = 1
    return last_page_index


def create_url_list(last_page_index):
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


def generate_urls_based_on_config(nid):
    MAX_PAGE_INDEX = 10
    last_page_index = MAX_PAGE_INDEX
    config = link_publisher_config.read_link_publisher_config(nid)
    if config:
        the_day_of_last_run = datetime.date.fromisoformat(config)
        today = datetime.date.today()
        days = (today - the_day_of_last_run).days
        print(f'[INFO] The day difference was (%d).' % (days))
        last_page_index = calculate_last_page_index(days)
    else:
        last_page_index = 1

    urls = create_url_list(last_page_index)

    print(urls)

    return urls


def record_sucessful_visit(nid):
    link_publisher_config.write_link_publisher_config(nid)


def test_all():
    nid = 'foobar'
    generate_urls_based_on_config(nid)


if __name__ == '__main__':
    test_all()

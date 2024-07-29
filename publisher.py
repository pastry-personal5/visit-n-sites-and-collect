import datetime

from loguru import logger

import meta_info_manager


def calculate_last_page_index(days):
    const_max_page_index = 10
    last_page_index = days
    if last_page_index > const_max_page_index:
        last_page_index = const_max_page_index
    elif last_page_index < 1:
        last_page_index = 1
    return last_page_index


def create_publisher_links_to_visit_based_on_last_page_index(last_page_index):
    const_target_base_url_list = [
        # The base URL to start with
        'https://www.clien.net/service/board/jirum',
        'https://www.clien.net/service/board/park'
    ]

    const_template_list = [
        'https://www.clien.net/service/board/jirum?&od=T31&category=0&po=%d',
        'https://www.clien.net/service/board/park?&od=T31&category=0&po=%d',
    ]

    assert len(const_target_base_url_list) == len(const_template_list)

    publisher_links = []

    index = 0
    for base_url in const_target_base_url_list:
        for i in range(0, last_page_index + 1):
            if i == 0:
                publisher_links.append(base_url)
            else:
                template = const_template_list[index]
                publisher_links.append(template % (i))
        index += 1
    return publisher_links


def create_publisher_links_to_visit(current_meta_info_manager: meta_info_manager.MetaInfoManager):
    const_max_page_index = 10
    last_page_index = const_max_page_index
    date_of_last_run = current_meta_info_manager.read_date_of_last_run()
    if date_of_last_run != -1:
        today = datetime.date.today()
        days = (today - date_of_last_run).days
        logger.info(f'The day difference was ({days}).')
        last_page_index = calculate_last_page_index(days)
    else:
        last_page_index = 1

    publisher_links = create_publisher_links_to_visit_based_on_last_page_index(last_page_index)

    return publisher_links

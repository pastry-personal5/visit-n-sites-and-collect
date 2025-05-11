from loguru import logger


class PublisherController:
    def __init__(self):
        pass

    def _calculate_last_page_index(self, days: int) -> int:
        const_max_page_index = 10
        last_page_index = days
        if last_page_index > const_max_page_index:
            last_page_index = const_max_page_index
        elif last_page_index < 1:
            last_page_index = 1
        return last_page_index

    def _create_publisher_links_to_visit_based_on_last_page_index(self, target_base_url_list, template_list, last_page_index) -> list:
        assert len(target_base_url_list) == len(template_list)

        publisher_links = []

        index = 0
        for base_url in target_base_url_list:
            for i in range(0, last_page_index + 1):
                if i == 0:
                    publisher_links.append(base_url)
                else:
                    logger.info(index)
                    template = template_list[index]
                    publisher_links.append(template % (i))
            index += 1
        return publisher_links

    def create_publisher_links_to_visit(self, target_base_url_list, template_list, days_difference_since_last_run: int) -> list:
        const_max_page_index = 10
        last_page_index = const_max_page_index
        if days_difference_since_last_run != -1:
            logger.info(f"The day difference was ({days_difference_since_last_run}).")
            last_page_index = self._calculate_last_page_index(days_difference_since_last_run)
        else:
            last_page_index = 1

        publisher_links = self._create_publisher_links_to_visit_based_on_last_page_index(target_base_url_list, template_list, last_page_index)

        return publisher_links

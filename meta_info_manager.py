import datetime

import last_run_recorder


# `LinkRecorder` records visited campaign URLs.
# It means visited campaign URLs belong to nid or Naver user ID.
class LinkRecorder:
    visited_links = set()
    nid = None

    # nid means Naver user ID.
    def __init__(self, nid: str):
        self.nid = nid

    def is_visited(self, url: str):
        return url in self.visited_links

    def add_link(self, url: str):
        self.visited_links.add(url)

    def get_visited_urls(self):
        return self.visited_links

    def get_full_visited_urls_file_path(self):
        full_visited_urls_file_path = f'visited_urls.{self.nid}.txt'
        return full_visited_urls_file_path

    def read_visited_campaign_links_from_file(self):
        file_path = self.get_full_visited_urls_file_path()
        # Read visited URLs from file
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.visited_links = set(file.read().splitlines())
        except FileNotFoundError:
            self.visited_links = set()
        return self.visited_links

    def write_visited_campaign_links_to_file(self):
        # Save the updated visited URLs to the file
        file_path = self.get_full_visited_urls_file_path()
        with open(file_path, 'w', encoding='utf-8') as file:
            for url in self.visited_links:
                file.write(url + '\n')


# `MetaInfoManager` manages "meta info" about collector.
#
# It contains "visited campaign links" and "the date of last run."
# It's not to visit campaign links twice.
# Also, it's not to visit too many publisher links.
#
# Please note that "meta info" can be extended.
class MetaInfoManager:
    link_recorder: LinkRecorder = None  # Visited campaign links are managed by this object.
    nid = None  # Naver ID

    def __init__(self, nid: str):
        self.nid = nid
        self.link_recorder = LinkRecorder(nid)

    def read_visited_campaign_links_from_file(self):
        assert self.link_recorder is not None
        return self.link_recorder.read_visited_campaign_links_from_file()

    def write_visited_campaign_links_to_file(self):
        assert self.link_recorder is not None
        self.link_recorder.write_visited_campaign_links_to_file()

    def is_visited_campaign_link(self, link):
        assert self.link_recorder is not None
        return self.link_recorder.is_visited(link)

    def record_visited_campaign_link(self, link):
        assert self.link_recorder is not None
        self.link_recorder.add_link(link)

    def read_date_of_last_run(self) -> datetime.date:
        return last_run_recorder.read_date_of_last_run(self.nid)

    def write_date_of_last_run(self):
        last_run_recorder.write_date_of_last_run(self.nid)

import datetime
import gzip
import os
import shutil

from loguru import logger

from cloud_file_storage import CloudFileStorage
import last_run_recorder


class SharedContext:
    '''
    A share context among n-site IDs.
    '''

    def __init__(self):
        self.flag_has_valid_cloud_file_storage_config = False
        self.folder_id_of_parent_of_cloud_file_storage = None

    def init_with_core_config(self, folder_id_of_parent_of_cloud_file_storage: str) -> None:
        self.flag_has_valid_cloud_file_storage_config = True
        self.folder_id_of_parent_of_cloud_file_storage = folder_id_of_parent_of_cloud_file_storage

    def has_valid_cloud_file_storage_config(self) -> bool:
        return self.flag_has_valid_cloud_file_storage_config


# `LinkRecorder` records visited campaign URLs.
# It means visited campaign URLs belong to nid or Naver user ID.
class LinkRecorder:

    # nid means Naver user ID.
    def __init__(self, nid: str, shared_context: SharedContext):
        self.visited_links = set()
        self.nid = nid
        self.cloud_file_storage = CloudFileStorage()
        self.shared_context = shared_context

    def is_visited(self, url: str):
        return url in self.visited_links

    def add_link(self, url: str):
        self.visited_links.add(url)

    def get_visited_urls(self):
        return self.visited_links

    def _get_full_visited_urls_file_path(self):
        full_visited_urls_file_path = f'visited_urls.{self.nid}.txt'
        return full_visited_urls_file_path

    def _get_gzipped_full_visited_urls_file_path(self):
        gzipped_full_visited_urls_file_path = f'visited_urls.{self.nid}.txt.gz'
        return gzipped_full_visited_urls_file_path

    def _compress_file(self, input_file, output_file):
        with open(input_file, 'rb') as f_in:
            with gzip.open(output_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

    def _decompress_file(self, input_file, output_file):
        with gzip.open(input_file, 'rb') as f_in:
            with open(output_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

    def read_visited_campaign_links_from_file(self):
        # Prepare
        gzipped_file_path = self._get_gzipped_full_visited_urls_file_path()
        file_path = self._get_full_visited_urls_file_path()
        # Dwonload a file from the cloud if available.
        if self.shared_context.has_valid_cloud_file_storage_config():
            self.cloud_file_storage.download(gzipped_file_path, self.shared_context.folder_id_of_parent_of_cloud_file_storage)
        else:
            logger.warning('While trying to read visited campaign links, one has found that the cloud file storage configuration is invalid. Look for the main configuration file.')
        # Gunzip
        try:
            self._decompress_file(gzipped_file_path, file_path)
        except FileNotFoundError:
            logger.warning(f'File not found: ({gzipped_file_path})')
            # Here, let's do not return. That means trying to read a plain text file.

        # Read visited URLs from file
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.visited_links = set(file.read().splitlines())
        except FileNotFoundError:
            self.visited_links = set()
        return self.visited_links

    def write_visited_campaign_links_to_file(self):
        # Save the updated visited URLs to the file
        file_path = self._get_full_visited_urls_file_path()
        with open(file_path, 'w', encoding='utf-8') as file:
            for url in self.visited_links:
                file.write(url + '\n')
        # Gzip
        gzipped_file_path = self._get_gzipped_full_visited_urls_file_path()
        self._compress_file(file_path, gzipped_file_path)
        logger.info(f'One has saved and gzipped: ({gzipped_file_path})')
        # Upload
        if self.shared_context.has_valid_cloud_file_storage_config():
            self.cloud_file_storage.upload(gzipped_file_path, self.shared_context.folder_id_of_parent_of_cloud_file_storage)
        else:
            logger.warning('While trying to write visited campaign links, one has found that the cloud file storage configuration is invalid. Look for the main configuration file.')


# `MetaInfoManager` manages "meta info" about collector.
#
# It contains "visited campaign links" and "the date of last run."
# It's not to visit campaign links twice.
# Also, it's not to visit too many publisher links.
#
# Please note that "meta info" can be extended.
class MetaInfoManager:

    def __init__(self, nid: str, shared_context: SharedContext):
        # Naver ID
        self.nid = nid
        # Visited campaign links are managed by this object.
        self.link_recorder = LinkRecorder(nid, shared_context)

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

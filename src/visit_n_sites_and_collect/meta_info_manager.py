import datetime
import gzip
import os
import shutil

from loguru import logger

from cloud_file_storage import CloudFileStorage
import last_run_recorder


# `MetaInfoManager` manages "meta info" about collector.
#
# It contains "visited campaign links" and "the date of last run."
# It's not to visit campaign links twice.
# Also, it's not to visit too many publisher links.
#
# Please note that "meta info" can be extended.
class MetaInfoManager:

    def __init__(self, nid: str):
        # Naver ID
        self.nid = nid

    def read_date_of_last_run(self) -> datetime.date:
        return last_run_recorder.read_date_of_last_run(self.nid)

    def write_date_of_last_run(self):
        last_run_recorder.write_date_of_last_run(self.nid)

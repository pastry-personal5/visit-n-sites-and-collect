src/visit_n_sites_and_collect/link_visitor.py:245 and :264 – Both _write_visited_campaign_links_to_file and delete_all call self.configuration_for_cloud_file_storage.has_valid_cloud_file_storage_config() without verifying that self.configuration_for_cloud_file_storage is not None. If cloud_file_storage.enabled is True but folder_id_for_parent is missing in the global config (a common misconfiguration), self.flag_use_cloud_file_storage becomes True while the configuration remains None, and the first write/delete attempt raises AttributeError, aborting the run. Guard for None before dereferencing or keep the flag False until a valid configuration exists.

src/visit_n_sites_and_collect/clean_visited_urls.py:30-45 and link_visitor.py:255 – The cleanup workflow never propagates the “use cloud storage” flag to VisitedCampaignLinkController. CleaningController.delete_all initializes the controller with a CloudFileStorage instance but never sets flag_use_cloud_file_storage; therefore VisitedCampaignLinkController.delete_all only removes local files and silently skips the Google Drive copy, leaving stale .gz files online. Expose a knob (e.g., a parameter or setter) so the cleanup path mirrors the visit path and deletes remote artifacts when cloud storage is enabled.

src/visit_n_sites_and_collect/link_visitor.py:255-263 – The local delete logic wraps removal of both the plain text and gzip file in a single try. If the text file is already gone, os.remove(file_path) raises FileNotFoundError, the except block swallows it, and the gzip removal is never attempted, leaving the compressed file behind. Remove each file inside its own try/except or use contextlib.suppress per file so both paths are always attempted.

src/visit_n_sites_and_collect/link_visitor.py:37-54 – wait_for_page_load spins indefinitely with while True and no timeout. When neither the title nor the “don’t save device” element ever appears (network hiccup, page change, etc.), the script hangs forever with no escape hatch. Add a time limit and surface a clear error so the caller can retry or bail out gracefully.

# Next Steps

Decide how you want the cleaning script to signal cloud usage, then wire that flag through before rerunning any destructive cleanup.

Harden the cloud-storage configuration handling: refuse to enable the feature without a valid folder id and guard every dereference.

Adjust the delete helpers and the page-wait loop so they can’t hang or leave artifacts silently; rerun automated checks once patched.

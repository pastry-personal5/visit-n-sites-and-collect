src/visit_n_sites_and_collect/link_visitor.py – Fixed: treat cloud storage as enabled only when `cloud_file_storage.enabled` is True *and* `folder_id_for_parent` is present (valid config). When the folder id is missing, the feature is disabled with a warning to avoid None dereferences and confusing partial behavior.

src/visit_n_sites_and_collect/clean_visited_urls.py and link_visitor.py – Fixed: expose a small knob (`VisitedCampaignLinkController.set_use_cloud_file_storage(...)`) and use it from both the cleanup path and the normal visit path so remote deletes are attempted when cloud storage is enabled.

src/visit_n_sites_and_collect/link_visitor.py – Fixed: delete now attempts both the plain text and gzip removal independently (using `contextlib.suppress(FileNotFoundError)`) so a missing `.txt` can’t prevent cleanup of the `.gz`.

src/visit_n_sites_and_collect/link_visitor.py:37-54 – wait_for_page_load spins indefinitely with while True and no timeout. When neither the title nor the “don’t save device” element ever appears (network hiccup, page change, etc.), the script hangs forever with no escape hatch. Add a time limit and surface a clear error so the caller can retry or bail out gracefully.

# Next Steps

Done: the cleaning script now signals cloud usage via `VisitedCampaignLinkController.set_use_cloud_file_storage(...)`.

Harden the cloud-storage configuration handling: refuse to enable the feature without a valid folder id and guard every dereference.

Adjust the page-wait loop so it can’t hang; rerun automated checks once patched.

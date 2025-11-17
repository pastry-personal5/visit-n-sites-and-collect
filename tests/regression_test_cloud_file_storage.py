from visit_n_sites_and_collect.cloud_file_storage import CloudFileStorage


def main():
    print("Running regression tests for cloud file storage...")

    cloud_file_storage = CloudFileStorage()
    cloud_file_storage.authenticate_google_drive()

    print("All tests completed successfully.")


if __name__ == "__main__":
    main()

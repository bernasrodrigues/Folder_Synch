import os
import unittest

from main import SyncManager, Logger


class TestSyncManager(unittest.TestCase):
    def setUp(self):
        # Set up source and replica folder paths relative to the current directory
        self.current_dir = os.getcwd()
        self.source_dir = os.path.join(self.current_dir, "test_source_folder")
        self.replica_dir = os.path.join(self.current_dir, "test_replica_folder")

        # Initialize logger and SyncManager
        self.logger = Logger("test_log.txt")
        self.logger.log_activity("Starting tests")
        self.sync_manager = SyncManager(self.source_dir, self.replica_dir, self.logger)

    def tearDown(self):
        # Clean up source and replica folders
        self.logger.log_activity("Completed tests")

    def test_sync_files_identical(self):
        """Test if synchronized files are identical."""
        # Perform synchronization
        self.sync_manager.synchronize()

        # Verify that files in the replica folder are identical to files in the source folder
        file1_source_path = os.path.join(self.source_dir, "File_1.txt")
        file1_replica_path = os.path.join(self.replica_dir, "File_1.txt")
        with open(file1_source_path, "r") as source_file, open(file1_replica_path, "r") as replica_file:
            source_content = source_file.read()
            replica_content = replica_file.read()
            self.assertEqual(source_content, replica_content)

        file2_source_path = os.path.join(self.source_dir, "test_folder", "File_2.txt")
        file2_replica_path = os.path.join(self.replica_dir, "test_folder", "File_2.txt")
        with open(file2_source_path, "r") as source_file, open(file2_replica_path, "r") as replica_file:
            source_content = source_file.read()
            replica_content = replica_file.read()
            self.assertEqual(source_content, replica_content)

        self.logger.log_activity(f"{self.replica_dir} contents match {self.source_dir}")
        self.logger.log_activity("Test for synchronizing files passed")


if __name__ == '__main__':
    unittest.main()

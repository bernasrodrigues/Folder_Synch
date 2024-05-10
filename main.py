import os
import sys
import argparse
import time
import datetime
import shutil
import hashlib
import threading


class Logger:
    def __init__(self, log_path):
        self.log_path = log_path

    def log_activity(self, activity: str):
        timestamp = datetime.datetime.now()
        log_entry = f"[{timestamp}] {activity}"
        print(log_entry)
        with open(self.log_path, "a") as log_file:
            log_file.write(f"{log_entry}\n")


class SyncManager:
    def __init__(self, source, replica, logger):
        """Initializes the SyncManager with the source folder, replica folder, and logger."""
        self.source = source
        self.replica = replica
        self.logger = logger

        self.logger.log_activity(f"Starting Synchronization")

    def synchronize(self):
        """Synchronizes files and folders between the source and replica directories."""
        self.logger.log_activity("Sync operation started")

        try:
            source_files, source_dirs = self.scan_directory(self.source)
            replica_files, replica_dirs = self.scan_directory(self.replica)

            self.delete_excess_folders(replica_dirs, source_dirs)
            self.create_missing_folders(replica_dirs, source_dirs)
            self.update_or_create_files(source_files, replica_files)
            self.delete_excess_files(replica_files, source_files)

            self.logger.log_activity("Sync operation completed")

        except Exception as e:
            self.logger.log_activity(f"Error occurred during synchronization: {e}")

    def delete_excess_folders(self, replica_dirs, source_dirs):
        """Delete excess folders in the replica directory."""
        for directory in replica_dirs:
            if directory not in source_dirs:
                subfolder_to_delete = os.path.join(self.replica, directory)
                shutil.rmtree(subfolder_to_delete)
                self.logger.log_activity(f"Deleted folder: {subfolder_to_delete}")

    def create_missing_folders(self, replica_dirs, source_dirs):
        """Create missing folders in the replica directory."""
        for directory in source_dirs:
            if directory not in replica_dirs:
                subfolder_to_create = os.path.join(self.replica, directory)
                os.makedirs(subfolder_to_create)
                self.logger.log_activity(f"Created folder: {subfolder_to_create}")

    def update_or_create_files(self, source_files, replica_files):
        """Update or create files in the replica directory."""
        for file in source_files:
            source_file_path = os.path.join(self.source, file)
            replica_file_path = os.path.join(self.replica, file)

            if file in replica_files:
                if not self.compare_hashes(source_file_path, replica_file_path):
                    shutil.copy(source_file_path, replica_file_path)
                    self.logger.log_activity(f"Updated file: {replica_file_path}")
            else:
                shutil.copy(source_file_path, replica_file_path)
                self.logger.log_activity(f"Created file: {replica_file_path}")

    def delete_excess_files(self, replica_files, source_files):
        """Delete excess files in the replica directory."""
        for file in replica_files:
            if file not in source_files:
                replica_file_path = os.path.join(self.replica, file)
                os.remove(replica_file_path)
                self.logger.log_activity(f"Deleted file: {replica_file_path}")

    @staticmethod
    def scan_directory(directory_path: str):
        """Scans a directory and returns the files and directories inside said directory."""
        files = []
        directories = []

        for root, dirs, file_names in os.walk(directory_path):
            for name in file_names:
                files.append(os.path.relpath(os.path.join(root, name), directory_path))
            for name in dirs:
                directories.append(os.path.relpath(os.path.join(root, name), directory_path))

        return files, directories

    @staticmethod
    def compare_hashes(source_file, replica_file):
        """Hashes chunks of 2 files and compares them to check if they are identical."""
        block_size = 65536  # 64 KB chunks

        with open(source_file, 'rb') as source, open(replica_file, 'rb') as replica:
            source_hash = hashlib.md5()
            replica_hash = hashlib.md5()

            while True:
                source_chunk = source.read(block_size)
                replica_chunk = replica.read(block_size)

                if not source_chunk and not replica_chunk:
                    break

                if (source_chunk and not replica_chunk) or (not source_chunk and replica_chunk):
                    return False

                source_hash.update(source_chunk)
                replica_hash.update(replica_chunk)

                if source_hash.digest() != replica_hash.digest():
                    return False

        return True


class SyncScheduler:
    def __init__(self, source, replica, log_path, sync_interval):
        """
        :param source: source folder
        :param replica: replica folder
        :param log_path: name of the logger file
        :param sync_interval: after each synchronization, wait "sync_interval" seconds until next synchronization
        """
        self.source = source
        self.replica = replica
        self.log_path = log_path
        self.sync_interval = sync_interval
        self.logger = Logger(log_path)

        # Check if source and replica folders exist
        if not os.path.exists(source):
            print(f"Error: Source folder '{source}' does not exist.")
            sys.exit(1)
        if not os.path.exists(replica):
            print(f"Warning: Replica folder '{replica}' does not exist. Folder will be created")

        self.sync_manager = SyncManager(source, replica, self.logger)

    def run(self):
        try:
            while True:
                print("--------------------------------\nSync operation in progress.\n")
                self.sync_manager.synchronize()
                print(f"\nSync operation completed. (Syncing again in {self.sync_interval} seconds)")
                time.sleep(self.sync_interval)

        except KeyboardInterrupt:
            print("\nSync operation interrupted. Exiting.")
            sys.exit(0)


class SyncThread(threading.Thread):
    """Runs the SyncScheduler in a thread"""

    def __init__(self, scheduler):
        super().__init__()
        self.scheduler = scheduler

    def run(self):
        self.scheduler.run()


class ArgumentBuilder:
    def __init__(self):
        """Initializes the ArgumentBuilder."""
        self.parser = argparse.ArgumentParser(
            description='Syncs content from a source folder to a replica folder, creating an exact copy')

    def add_arguments(self):
        """Adds arguments to the ArgumentParser."""
        self.parser.add_argument('-s', '--source', help='Source folder path', default='source_folder')
        self.parser.add_argument('-r', '--replica', help='Replica folder path', default='replica_folder')
        self.parser.add_argument('-l', '--log', help='Log file path', default='sync_log.txt')
        self.parser.add_argument('-t', '--time', help='Sync interval (seconds)', default=30)
        self.parser.add_argument('--threaded', action='store_true', help='Run scheduler on a separate thread')

    def parse_args(self):
        """Parses the command-line arguments."""
        return self.parser.parse_args()


def main():
    arg_builder = ArgumentBuilder()
    arg_builder.add_arguments()
    args = arg_builder.parse_args()

    scheduler = SyncScheduler(args.source, args.replica, args.log, int(args.time))

    if args.threaded:
        thread = SyncThread(scheduler)
        thread.start()
        thread.join()  # Wait for the thread to complete
    else:
        scheduler.run()


if __name__ == "__main__":
    main()

# Example usage python main.py -s source_folder -r replica_folder -l sync_log.txt -t 60

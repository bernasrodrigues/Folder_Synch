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

        self.logger.log_activity(f"Staring Synchronization")

    def synchronize(self):
        """Synchronizes files and folders between the source and replica directories."""
        self.logger.log_activity("Sync operation started")

        source_files, source_dirs = self.scan_directory(self.source)  # get the files and directories in source folder
        replica_files, replica_dirs = self.scan_directory(self.replica) # get the files and directories in replica folder

        # delete excess folders in replica
        for directory in replica_dirs:
            if directory not in source_dirs:
                subfolder_to_delete = os.path.join(self.replica, directory)
                if os.path.isdir(subfolder_to_delete):
                    shutil.rmtree(subfolder_to_delete)
                    self.logger.log_activity(f"Deleted folder: {subfolder_to_delete}")

        # Create missing folders in replica directory
        for directory in source_dirs:
            if directory not in replica_dirs:
                subfolder_to_create = os.path.join(self.replica, directory)
                if not os.path.isdir(subfolder_to_create):
                    os.makedirs(subfolder_to_create)
                    self.logger.log_activity(f"Created folder: {subfolder_to_create}")

        # Update or create files
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

        # Remove excess files
        for file in replica_files:
            if file not in source_files:
                replica_file_path = os.path.join(self.replica, file)
                os.remove(replica_file_path)
                self.logger.log_activity(f"Deleted file: {replica_file_path}")

        self.logger.log_activity("Sync operation completed")



        '''
        files_to_create = [file for file in source_files if file not in replica_files]  # files missing in replica folder
        files_to_delete = [file for file in replica_files if file not in source_files]  # excess files in source folder
        files_to_update = [file for file in source_files if file in replica_files]  # files with the same names in both folders that we will compare the content

        # Check if the content of the files is the same in both files (by hashing their contents)
        if files_to_update:
            for file in files_to_update:
                source_file = os.path.join(self.source, file)
                replica_file = os.path.join(self.replica, file)
                if not self.compare_hashes(source_file, replica_file):  # comparing the files
                    replica_file_path = os.path.join(self.replica, file)
                    os.remove(replica_file_path)

                    source_file_path = os.path.join(self.source, file)
                    replica_file_path = os.path.join(self.replica, file)
                    shutil.copy(source_file_path, replica_file_path)

                    self.logger.log_activity(f"File '{replica_file_path} was modified")
                else:
                    self.logger.log_activity(f"File '{file}' is up to date.")  # <- TODO may fill log file with redundant info (maybe remove so that only changes are noted)

        # Remove excess files
        for file in files_to_delete:
            replica_file_path = os.path.join(self.replica, file)
            os.remove(replica_file_path)
            self.logger.log_activity(f"Deleted file: {replica_file_path}")

        # Create missing files
        for file in files_to_create:
            source_file_path = os.path.join(self.source, file)
            replica_file_path = os.path.join(self.replica, file)
            shutil.copy(source_file_path, replica_file_path)
            self.logger.log_activity(f"Created file: {replica_file_path}")

        self.logger.log_activity("Sync operation completed")
        '''

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
        # print(f"Comparing files '{source_file}' with '{replica_file}'")

        block_size = 65536  # 64 KB chunks
        with open(source_file, 'rb') as source, open(replica_file, 'rb') as replica:
            source_hash = hashlib.md5()         # md5 -> fastest hash that provides decent results
            replica_hash = hashlib.md5()

            while True:
                source_chunk = source.read(block_size)
                replica_chunk = replica.read(block_size)

                # If both source_chunk and replica_chunk are empty, it means we reached the end of both files
                if not source_chunk and not replica_chunk:
                    break

                # If one chunk is empty while the other is not, files have different sizes and are considered different
                if (source_chunk and not source_chunk) or (not source_chunk and replica_chunk):
                    # print("Files are different")
                    return False

                source_hash.update(source_chunk)
                replica_hash.update(replica_chunk)
                if source_hash.digest() != replica_hash.digest():    # if a chunk is different return false (meaning files' contents are diferent)
                    # print("Files are different")
                    return False
        return True


class SyncScheduler:
    def __init__(self, source, replica, log_path, sync_interval):
        """
        :param source: source folder
        :param replica: replica folder
        :param log_path: name of the logger file
        :param sync_interval: after each synchronization, wait "sync_interval" seconds until next synch
        """
        self.source = source
        self.replica = replica
        self.log_path = log_path
        self.sync_interval = sync_interval
        self.logger = Logger(log_path)
        self.sync_manager = SyncManager(source, replica, self.logger)

    def run(self):
        try:
            while True:
                print(f"--------------------------------\n"
                      f"Sync operation in progress.\n")
                self.sync_manager.synchronize()
                print(f"\n"
                      f"Sync operation completed. (Syncing again in {self.sync_interval} seconds)")
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

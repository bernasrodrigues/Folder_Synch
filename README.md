# Folder Synchronization Tool

This tool synchronizes the contents of a source folder with a replica folder, ensuring they have identical files and directories.

## Usage

Run the main script `main.py` with the following command-line arguments:

- `-s` or `--source`: Path to the source folder. Default is `source_folder`.
- `-r` or `--replica`: Path to the replica folder. Default is `replica_folder`.
- `-l` or `--log`: Path to the log file. Default is `sync_log.txt`.
- `-t` or `--time`: Sync interval in seconds. Default is `30`.
- `--threaded`: Run the synchronization scheduler on a separate thread.

Example usage:
  python main.py -s source_folder -r replica_folder -l sync_log.txt -t 30

  Running: "python main.py" is the same as the above usage

## How it Works

The script compares the files and directories in the source and replica folders. It creates missing folders in the replica folder, updates or creates files, and deletes excess files or folders in the replica folder to match the source folder's structure.

## Running the Tests

To run the unit tests, execute the test script `test_sync_manager.py`. This script tests the synchronization functionality and verifies if synchronized files are identical.

Example usage:
  python test_cases.py


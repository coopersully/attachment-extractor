import json
import os
import sys
import time

import schedule as schedule

import extract
import ocr
import sqlite_manager

username: str = ""
password: str = ""
input_folder: str = ""
output_folder: str = ""


# Grab the email's login details from login.json
# and make the export directory if need be.
def fetch_login():

    global username
    global password
    global input_folder
    global output_folder

    # Load login file into memory
    login_file = open('login.json')
    login_json = json.load(login_file)

    # Parse login file and exit if fails
    try:
        username = login_json['username']
        password = login_json['password']

        # Fetch input_folder directory from file
        # If the directory doesn't exist, create it
        input_folder = login_json['input_directory']
        if not os.path.isdir(input_folder):
            print(f'Input directory "{ input_folder } does not exist; creating it now."')
            os.makedirs(input_folder, exist_ok=True)

        # Fetch output_folder directory from file
        # If the directory doesn't exist, create it
        output_folder = login_json['output_directory']
        if not os.path.isdir(output_folder):
            print(f'Output directory "{ output_folder } does not exist; creating it now."')
            os.makedirs(output_folder, exist_ok=True)

    except KeyError as e:
        print()
        print(f'Error loading username, password, or directory; please provide all fields in login.json')
        print(f'Cause of exception: { e }')
        sys.exit()


def refresh_library():
    # Connect to SQLite3 database
    sqlite_manager.create_or_connect()

    fetch_login()
    extract.attempt_login(username, password)

    # Get latest downloaded email
    exported_index = sqlite_manager.get_latest_exported_email()
    print(f'Starting exportation at email with UID: "{exported_index}"')

    # Download attachments
    extract.download_attachments(input_folder, exported_index)

    # Get latest scanned email
    scanned_index = sqlite_manager.get_latest_scanned_email()
    print(f'Starting optical-character-recognition at email with UID: "{scanned_index}"')

    # OCR new attachments
    ocr.ocr_files(input_folder, output_folder, scanned_index)


if __name__ == '__main__':

    # Repeat every 1hr
    schedule.every(1).hours.do(refresh_library)
    refresh_library()

    # Check for pending tasks and run them
    while True:
        schedule.run_pending()
        time.sleep(1)

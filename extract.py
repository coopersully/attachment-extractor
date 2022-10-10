import json
import os
import re
import sys
from imbox import Imbox
import filedate
from datetime import datetime

username = ""
password = ""
directory = ""
account: Imbox = None


# Modifies the date of a file at a given file_path
# to mimic the birthdate of the source_message given.
def change_file_date(source_message, file_path):
    # Retrieve the date of the source_message
    date = source_message.date[5:]
    date_formatted = datetime.strptime(date, "%d %b %Y %H:%M:%S %z")  # Given format
    new_date_string = date_formatted.strftime("%Y.%m.%d %H:%M:%S")  # ISO Format

    # Change the date on the file object
    file = filedate.File(file_path)
    file.set(
        modified=new_date_string,
        created=new_date_string,
        accessed=new_date_string
    )

    # Write the new date to the file
    filedate.File(file_path)


# Grab the email's login details from login.json
# and make the export directory if need be.
def fetch_login():

    global username
    global password
    global directory

    # Load login file into memory
    login_file = open('login.json')
    login_json = json.load(login_file)

    # Parse login file and exit if fails
    try:
        username = login_json['username']
        password = login_json['password']

        # If the directory doesn't exist, create it
        directory = login_json['directory_raw']
        if not os.path.isdir(directory):
            os.makedirs(directory, exist_ok=True)
    except KeyError as e:
        print(f'Error loading username, password, or directory; please provide all fields in login.json')
        sys.exit()


# Attempt to log in to Gmail's servers with
# the fetched email address and password
def attempt_login(login_username, login_password):

    global account

    # Login to email address with credentials
    account = Imbox(
        "imap.gmail.com",
        username=login_username,
        password=login_password,
        ssl=True,
        ssl_context=None,
        starttls=False
    )


if __name__ == "__main__":

    fetch_login()
    attempt_login(username, password)

    # Fetch all messages that have attachments
    messages = account.messages(folder='all', raw='from:message@inbound.efax.com has:attachment')
    num_messages = messages.__len__()

    print(f'Found {num_messages} messages in your inbox.')
    print('Searching for attachments...')

    # Reset counters
    attachment_num_global = 0

    # Iterate over every message found
    for uid, message in messages:
        # Basic message info
        subject_raw: str = message.subject
        # Capitalize subject & fix odd spacing
        subject = subject_raw.strip().upper().replace("  ", " ")
        # Remove all non-alphanumeric characters
        subject = re.sub(r'[^A-Za-z0-9 ]+', '', subject)
        # Remove redundant tags and prefixes
        subject = subject[10:].replace("CALLERID", "").replace("PAGES", "")
        # Replace remaining spaces with _ for better corruption protection
        subject = subject.replace(" ", "_")

        sender_data = message.sent_from[0]
        sender = sender_data['email']  # Extract from retrieved name/email list

        # Iterate over every attachment in the current message
        attachments: list = message.attachments
        num_attachments_message = len(attachments)
        for idx, attachment in enumerate(attachments):

            # Reset counters per message
            attachment_num_global += 1

            try:
                # Basic attachment info
                attachment_name: str = attachment.get('filename')

                # Alert the user of the download
                file_extension = attachment_name.split('.').pop(1)

                # Build subdirectory to download to
                subdirectory = f'{ directory }/{ int(uid) }'
                if not os.path.isdir(subdirectory):
                    os.mkdir(subdirectory)

                final_file_path = f'{subdirectory}/{subject}_{num_attachments_message}.{file_extension}'

                # If the file already exists, don't re-download it.
                if os.path.isfile(final_file_path):
                    # !! Shorter message to separate from errors in terminal
                    print(f'({attachment_num_global}/{num_attachments_message}) Done.')
                    continue

                # Download/write the file
                with open(final_file_path, "wb") as fp:
                    fp.write(attachment.get('content').read())

                change_file_date(message, final_file_path)

                # Increment counters
                num_attachments_message += 1

                # If it's the first line, print a newline for better formatting
                if attachment_num_global == 1:
                    print()

                # Alert the user of the download completion
                print(f'({attachment_num_global}/{num_messages}) Successfully downloaded "{final_file_path}" '
                      f'from {sender}... ')
            except Exception as e:
                # Alert the user of the download error
                print(f'({attachment_num_global}/{num_messages}) Failed to download from {sender}; {str(e)}')

    account.logout()

    print()
    print('Complete!')
    print(f'Successfully downloaded {attachment_num_global} new attachments.')

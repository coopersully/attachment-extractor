import os
import re
from datetime import datetime

import filedate
from imbox import Imbox
import imbox.vendors as vendors

import sqlite_manager

account: Imbox


# Modifies the date of a file at a given file_path
# to mimic the birthdate of the source_message given.
def change_file_date(source_message, file_path) -> None:
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


# Attempt to log in to Gmail's servers with
# the fetched email address and password
def attempt_login(login_username, login_password) -> None:

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


def get_uid(message) -> int:
    return int(message.uid)


def download_attachments(directory: str, starting_uid: int = 0):

    # Fetch all messages that have attachments
    messages: vendors.GmailMessages = account.messages(
        folder='all',
        raw='from:message@inbound.efax.com has:attachment',
        uid__range=f'{ starting_uid + 1 }:*'
    )
    num_messages = messages.__len__()

    print(f'Found { num_messages } new messages in your inbox.')
    print('Searching messages for attachments...')
    print()

    # Reset counters
    attachment_num_global = 0

    # Iterate over every message found
    for uid, message in messages:

        # If the message is already exported, continue
        if sqlite_manager.is_exported(uid):
            attachment_num_global += 1
            print(f'({attachment_num_global}/{num_messages}) Done.')
            continue

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

        sqlite_manager.export(uid)  # Log message as exported

    account.logout()

    print()
    print('Complete!')
    print(f'Successfully downloaded {attachment_num_global} new attachments.')

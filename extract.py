import json
import os
import re
import sys
from imbox import Imbox

host = "imap.gmail.com"

# Load login file into memory
login_file = open('login.json')
login_json = json.load(login_file)

# Parse login file and exit if fails
try:
    username = login_json['username']
    password = login_json['password']
    directory = login_json['directory_raw']
    if not os.path.isdir(directory):
        os.makedirs(directory, exist_ok=True)
except KeyError as e:
    print('Error loading username, password, or directory')
    print('Please provide all fields in login.json')
    sys.exit()

# Login to email address with credentials
mail = Imbox(
    host,
    username=username,
    password=password,
    ssl=True,
    ssl_context=None,
    starttls=False
)
messages = mail.messages(sent_from='message@inbound.efax.com')  # Fetch messages, defaults to "Inbox" inbox
num_messages = messages.__len__()

print(f'Found { num_messages } messages in your inbox.')
print('Searching for attachments...')

# Reset counters
total_attachments = 0
attachment_num_global = 0

# Iterate over every message found
for (uid, message) in messages:

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
    total_attachments = len(attachments)
    for idx, attachment in enumerate(attachments):

        # Reset counters per message
        attachment_num_global += 1
        attachment_num_message = 0

        try:
            # Basic attachment info
            attachment_name: str = attachment.get('filename')

            # Alert the user of the download
            file_extension = attachment_name.split('.').pop(1)

            # Build subdirectory to download to
            final_file_path = f'{ directory }/"{ subject }_{ attachment_num_message }.{ file_extension }'

            # If the file already exists, don't re-download it.
            if os.path.isfile(final_file_path):
                print(f'({attachment_num_global}/{total_attachments}) Done.')  # Shorter message to separate from errors in terminal
                continue

            # Download/write the file
            with open(final_file_path, "wb") as fp:
                fp.write(attachment.get('content').read())

            # Increment counters
            attachment_num_message += 1

            # If it's the first line, print a newline for better formatting
            if attachment_num_global == 1:
                print()

            # Alert the user of the download completion
            print(f'({ attachment_num_global }/{ total_attachments }) Successfully downloaded "{ attachment_name }" from "{sender}"... ')
        except Exception as e:
            # Alert the user of the download error
            print(f'({ attachment_num_global }/{ total_attachments }) Failed to download from "{ sender }"; { str(e) }')

mail.logout()

print()
print('Complete!')
print(f'Successfully downloaded { total_attachments } new attachments.')
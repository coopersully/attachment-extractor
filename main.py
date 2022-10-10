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
    directory = login_json['directory']
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

print(f'Found { messages.__len__() } messages in your inbox.')
print('Searching for attachments...')

# Iterate over every message found
total_attachments = 0
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

    sender_data: list = message.sent_from[0]
    sender = sender_data['email']  # Extract from retrieved name/email list

    # Iterate over every attachment in the current message
    for idx, attachment in enumerate(message.attachments):

        attachment_num = 0
        try:

            # Basic attachment info
            attachment_name: str = attachment.get('filename')

            # Build subdirectory to download to
            final_file_path = f"{directory}/"
            if not os.path.isdir(final_file_path):
                # Create the subdirectory if it doesn't exist
                os.makedirs(final_file_path, exist_ok=True)

            # Alert the user of the download
            file_extension = attachment_name.split('.').pop(1)
            final_file_path += f'{ subject }_{ attachment_num }.{ file_extension }'
            print(final_file_path)

            print()
            print(f'Downloading "{ attachment_name }" from "{ sender }"... ')

            # Download/write the file
            with open(final_file_path, "wb") as fp:
                fp.write(attachment.get('content').read())

            # Increment counters
            attachment_num += 1
            total_attachments += 1
        except Exception as e:
            print(e)

mail.logout()

print()
print('Complete!')
print(f'Successfully downloaded { total_attachments } new attachments.')
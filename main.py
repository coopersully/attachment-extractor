import json
import os
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
messages = mail.messages()  # Fetch messages, defaults to "Inbox" inbox

print(f'Found { messages.__len__() } messages in your inbox.')
print('Searching for attachments...')

# Iterate over every message found
total_attachments = 0
for (uid, message) in messages:

    # Basic message info
    subject = message.subject
    sender_data: list = message.sent_from[0]
    sender = sender_data['email']  # Extract from retrieved name/email list

    # Iterate over every attachment in the current message
    for idx, attachment in enumerate(message.attachments):

        try:

            # Basic attachment info
            attachment_name = attachment.get('filename')

            # Build subdirectory to download to
            subdir = f"{ directory }/{ sender }/{ subject }"
            if not os.path.isdir(subdir):
                # Create the subdirectory if it doesn't exist.
                # !! It should NOT already exist beforehand.
                os.makedirs(subdir, exist_ok=True)
            else:
                # If the subdirectory already exists locally, the file
                # already exists as well. Don't re-download and overwrite,
                # just keep going to the next file.
                continue

            # Increment counter
            total_attachments += 1

            # Alert the user of the download
            download_path = f"{ subdir }/{ attachment_name }"
            print()
            print(f'Downloading "{ attachment_name }" from "{ sender }"... ')

            # Download/write the file
            with open(download_path, "wb") as fp:
                fp.write(attachment.get('content').read())

        except Exception as e:
            print(e)

mail.logout()

print()
print('Complete!')
print(f'Successfully downloaded { total_attachments } new attachments.')
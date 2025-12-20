import os
import paramiko
from datetime import datetime

# Replace these values with your actual paths and server information
# Local directory where images are stored
local_directory = 'C:/apps/foo/media_root/categories_images'

# Remote server details
remote_server = '157.245.74.156'
remote_user = 'yurey'
remote_directory = '/home/yurey/myprojectdir/media_root/categories_images'

# SSH connection details
ssh_password = 'gadwad123'

# Calculate the date for today
today = datetime.now().date()

# Filter images created today
today_images = [f for f in os.listdir(local_directory) if os.path.isfile(os.path.join(local_directory, f))]
today_images = [f for f in today_images if os.path.getctime(os.path.join(local_directory, f)) > datetime(today.year, today.month, today.day).timestamp()]
print(today_images)
# Create an SSH client
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    # Connect to the remote server
    ssh.connect(remote_server, port=22, username=remote_user, password=ssh_password)

    # Create an SFTP session
    sftp = ssh.open_sftp()

    # Upload each image to the remote server
    for image_file in today_images:
        local_path = os.path.join(local_directory, image_file)
        remote_path = os.path.join(remote_directory, image_file).replace('\\', '/')
        print('sending', local_path, remote_path)
        # Upload the file
        sftp.put(local_path, remote_path)

    print("Images uploaded successfully.")
except Exception as e:
    print(f"Error: {e}")
finally:
    # Close the SSH connection
    if ssh:
        ssh.close()

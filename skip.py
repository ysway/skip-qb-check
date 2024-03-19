import os
import shutil
import glob
import libtorrent as lt
from tqdm import tqdm

qbittorrent_backup_path = os.path.join(
    os.getenv("LOCALAPPDATA"), "qBittorrent", "BT_backup"
)

if os.path.exists(qbittorrent_backup_path) and os.path.isdir(qbittorrent_backup_path):
    print(f"The folder '{qbittorrent_backup_path}' exists.")
else:
    print("Cannot find qbittorrent backup folder, aborting...")
    exit(1)

print("Backing up the folder to Desktop...")
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
backup_folder_name = "BT_backup"
destination_folder = os.path.join(desktop_path, backup_folder_name)

try:
    shutil.copytree(qbittorrent_backup_path, destination_folder)
    print(f"Backup completed successfully. Folder copied to {destination_folder}")
except Exception as e:
    print(f"An error occurred during the backup process: {e}")
    print("Stopping job, cannot guarantee not damaging existing fastresume files")
    exit(2)

print("Globbing fastresume files and torrents...")
torrent_files = glob.glob(os.path.join(qbittorrent_backup_path, "*.torrent"))
fastresume_files = glob.glob(os.path.join(qbittorrent_backup_path, "*.fastresume"))

# Strip the extensions and keep the base names for comparison
torrent_basenames = set(os.path.splitext(os.path.basename(f))[0] for f in torrent_files)
fastresume_basenames = set(
    os.path.splitext(os.path.basename(f))[0] for f in fastresume_files
)

# Find the intersection of basenames to identify matches
matching_basenames = torrent_basenames.intersection(fastresume_basenames)

print("Skipping checking for torrents...")
os.chdir(qbittorrent_backup_path)
errors = []
for name in tqdm(matching_basenames):
    try:
        # binary format dict
        data_bin_dict_dump = lt.bdecode(open(f"{name}.fastresume", mode="rb").read())

        # NOT used, qbittorrent has unique keys that the lib doesn't support.
        # add_torrent_params
        # data_dict = lt.read_resume_data(open(f"{name}.fastresume", mode="rb").read())

        # Display available keys and their values
        # for key in data_bin_dict_dump.keys():
        #     print(str(key)+": "+str(data_bin_dict_dump.get(key)))

        # Only process paused files
        if data_bin_dict_dump.get(b"paused") != 0:
            torrent_info = lt.torrent_info(f"{name}.torrent")
            num_of_pieces = torrent_info.num_pieces()
            data_bin_dict_dump.update({b"pieces": b"\x01" * num_of_pieces})

            # Write back to the file
            with open(f"{name}.fastresume", "wb") as f:
                f.write(lt.bencode(data_bin_dict_dump))
    except Exception as e:
        errors.append(f"An error occurred during the process: {e}, file: {name}")

for error in errors:
    print(error)

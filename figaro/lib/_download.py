"""Module for downloading files and folders from Box."""

# Standard libraries
import os
import math

# Specialized libraries
import dill
import psutil
import joblib
import tqdm

# Internal imports
from figaro import lib


def filedownload_to_path(client, config, filemap, foldermap, file_path):
    """
    Downloads a file from Box to the specified local path.

    Arguments
    ---------
    client    : boxsdk client object
    config    : configuration dictionary
    file_path : local file path where the file should be downloaded
    """
    client = dill.loads(client)

    path_from_root = os.path.abspath(file_path).replace(
        config["folder"]["local_path"] + os.sep, ""
    )

    if path_from_root in filemap.keys():
        file_id = filemap[path_from_root]
        box_file = client.file(file_id).get()

        if lib.is_file_changed(file_path, box_file, download=True):
            with open(file_path, "wb") as download_stream:
                box_file.download_to(download_stream)
            message = (f'    -File "{box_file.name}" has been downloaded.')
        else:
            message = (f'    -File "{box_file.name}" is up to date. Skipping download.')

    else:
        raise ValueError(f"{file_path} not found in filemap.")

    return message


def filedownload_from_list(client, config, filemap, foldermap, filelist):
    """
    Downloads a list of files from Box to the local directory.

    Arguments
    ---------
    client   : boxsdk client object
    config   : configuration dictionary
    filelist : list of local file paths to download
    """
    cpu_avail = max(
        1,
        psutil.cpu_count()
        - math.floor(psutil.cpu_percent() * psutil.cpu_count() / 100),
    )

    num_procs = min(cpu_avail, len(filelist))

    if num_procs in [0, 1]:
        messages = [
            filedownload_to_path(
                dill.dumps(client), config, filemap, foldermap, file_path
            )
            for file_path in tqdm.tqdm(filelist, position=0)
        ]
    else:
        with joblib.parallel_backend(n_jobs=num_procs, backend="loky"):
            messages = joblib.Parallel(batch_size="auto")(
                joblib.delayed(filedownload_to_path)(
                    dill.dumps(client), config, filemap, foldermap, file_path
                )
                for file_path in tqdm.tqdm(filelist, position=0)
            )

    lib.write_boxmap(config, filemap, foldermap)
    [print(f"{message}") for message in messages]

def folderdownload_recursive(client, config, filemap, foldermap, local_folder_path):
    """
    Recursively downloads a folder and its contents from Box, creating local folders as needed.

    Arguments
    ---------
    client              : boxsdk client object
    config              : configuration dictionary
    filemap             : file mapping dictionary
    foldermap           : folder mapping dictionary
    folder_id           : Box folder ID to download from
    local_folder_path   : Local path where files should be downloaded
    """
    path_from_root = os.path.abspath(local_folder_path).replace(
        config["folder"]["local_path"] + os.sep, ""
    )

    folder_id = str(foldermap[path_from_root])

    # Get the Box folder object using the folder_id
    box_folder = client.folder(folder_id)

    print(f'Downloading box folder "{path_from_root}"')

    # Create the local folder if it doesn't exist
    if not os.path.exists(local_folder_path):
        os.makedirs(local_folder_path)
        print(f'Created local folder "{path_from_root}"')

    # Get the folder items (both files and subfolders)
    folder_items = box_folder.get_items()

    filelist = []
    folderlist = []

    for item in folder_items:
        if item.type == "file":
            filelist.append(os.path.join(os.path.abspath(local_folder_path), item.name))
        elif item.type == "folder":
            folderlist.append(
                os.path.join(os.path.abspath(local_folder_path), item.name)
            )

    filedownload_from_list(client, config, filemap, foldermap, filelist)

    for item in folderlist:
        # Recursively download subfolder
        new_local_folder_path = os.path.join(local_folder_path, item)
        folderdownload_recursive(
            client, config, filemap, foldermap, new_local_folder_path
        )

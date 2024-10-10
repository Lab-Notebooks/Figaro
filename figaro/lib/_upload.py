"""Module for library"""

# Standard libraries
import os
import math

# Specialized libraries
import dill
import psutil
import joblib

# Internal imports
from figaro import lib


def fileupload_from_path(client, config, filemap, foldermap, file_path):
    """
    Arguments
    ---------
    client	: boxsdk client object
    config	: configuration dictionary
    file_path	: path to file from working directory
    """
    client = dill.loads(client)

    if not os.path.isfile(file_path):
        raise ValueError(f"{file_path} is not a valid file.")

    path_from_root = os.path.abspath(file_path).replace(
        config["folder"]["local_path"] + os.sep, ""
    )

    upload_size = os.stat(file_path).st_size
    upload_id = None
    upload_obj = client.folder(config["folder"]["box_id"])
    upload_name = path_from_root.split(os.sep)[-1]

    if path_from_root in filemap.keys():
        upload_id = str(filemap[path_from_root])
        upload_obj = client.file(upload_id)

        # Check if the file has changed before uploading
        box_file = upload_obj.get()
        if not lib.is_file_changed(file_path, box_file):
            print(f'File "{box_file.name}" is up to date. Skipping upload.')
            return

    elif os.sep.join(path_from_root.split(os.sep)[:-1]) in foldermap.keys():
        upload_id = None
        upload_obj = client.folder(
            str(foldermap[os.sep.join(path_from_root.split(os.sep)[:-1])])
        )

    elif not os.sep.join(path_from_root.split(os.sep)[:-1]):
        pass
    else:
        raise ValueError(f"{path_from_root} is not found in filemap or foldermap.")

    if upload_id:
        if upload_size < 20000000:
            updated_file = upload_obj.update_contents(file_path)
            print(f'File "{updated_file.name}" has been updated')

        else:
            # uploads new large file version
            chunked_uploader = upload_obj.get_chunked_uploader(file_path)
            uploaded_file = chunked_uploader.start()
            print(
                f'File "{uploaded_file.name}" uploaded to Box with file ID {uploaded_file.id}'
            )

    else:
        if upload_size < 20000000:
            new_file = upload_obj.upload(file_path)
            print(f'File "{new_file.name}" uploaded to Box with file ID {new_file.id}')
            filemap[path_from_root] = new_file.id

        else:
            # uploads large file to a root folder
            chunked_uploader = upload_obj.get_chunked_uploader(
                file_path=file_path, file_name=upload_name
            )
            uploaded_file = chunked_uploader.start()
            print(
                f'File "{uploaded_file.name}" uploaded to Box with file ID {uploaded_file.id}'
            )
            filemap[path_from_root] = uploaded_file.id


def fileupload_from_list(client, config, filemap, foldermap, filelist):
    """
    Arguments
    ---------
    client	: boxsdk client object
    config	: configuration dictionary
    filelist	: list of file paths to upload
    """
    cpu_avail = max(
        1,
        psutil.cpu_count()
        - math.floor(psutil.cpu_percent() * psutil.cpu_count() / 100),
    )

    num_procs = min(cpu_avail, len(filelist))

    if num_procs in [0, 1]:
        [
            fileupload_from_path(
                dill.dumps(client), config, filemap, foldermap, file_path
            )
            for file_path in filelist
        ]
    else:
        with joblib.parallel_backend(n_jobs=num_procs, backend="loky"):
            joblib.Parallel(batch_size="auto")(
                joblib.delayed(fileupload_from_path)(
                    dill.dumps(client), config, filemap, foldermap, file_path
                )
                for file_path in filelist
            )

    lib.write_boxmap(config, filemap, foldermap)


def folderupload_recursive(client, config, filemap, foldermap, folder_path):
    """
    Recursively uploads a folder and its contents to Box.

    Arguments
    ---------
    client      : boxsdk client object
    config      : configuration dictionary
    filemap     : file mapping dictionary
    foldermap   : folder mapping dictionary
    folder_path : local path to the folder that needs to be uploaded
    """
    # Traverse the folder structure recursively
    for root, dirs, files in os.walk(folder_path):
        # Calculate the path relative to the root directory
        relative_path = os.path.abspath(root).replace(
            config["folder"]["local_path"] + os.sep, ""
        )

        # Check if the folder exists in the foldermap
        if relative_path in foldermap.keys():
            folder_id = foldermap[relative_path]
            box_folder = client.folder(folder_id)
        else:
            # Create the folder in Box if it doesn't exist
            parent_relative_path = os.sep.join(relative_path.split(os.sep)[:-1])
            if parent_relative_path in foldermap.keys():
                parent_folder_id = foldermap[parent_relative_path]
                parent_folder = client.folder(parent_folder_id)
            else:
                parent_folder = client.folder(config["folder"]["box_id"])

            # Create the new folder in Box
            new_folder = parent_folder.create_subfolder(os.path.basename(root))
            print(
                f'Created folder "{new_folder.name}" in Box with folder ID {new_folder.id}'
            )
            foldermap[relative_path] = new_folder.id
            box_folder = new_folder

        # Upload each file in the current folder
        fileupload_from_list(
            client,
            config,
            filemap,
            foldermap,
            [os.path.join(root, sfile) for sfile in files],
        )

    # Write updated file and folder mappings back to disk
    lib.write_boxmap(config, filemap, foldermap)

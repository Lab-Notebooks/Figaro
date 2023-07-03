"""Module for library"""

# Standard libraries
import os
import itertools
import multiprocessing
import toml

# Specialized libraries
import dill
import joblib
import boxsdk


def load_config():
    """
    \b
    Load configuration from .figaro file
    by search backwards along a directory
    tree.

    Arguments
    ---------
    None

    Returns
    -------
    config	: dictionary representation of .figaro
    """
    search_path = os.getcwd().split("/")

    for node in search_path[::-1]:

        config_file = os.path.join("/".join(search_path), ".figaro")

        if os.path.isfile(config_file):
            config = toml.load(config_file)
            config["folder"]["local_path"] = "/".join(search_path)
            break

        search_path.remove(node)

    return config


def validate_credentials(config):
    """
    \b
    Validate user credentials for Oauth
    or JWT authentication.

    Arguments
    ---------
    config	: configuration dictionary

    Returns
    client	: boxsdk client object
    """
    oauth = boxsdk.OAuth2(
        client_id=config["credentials"]["client_id"],
        client_secret=config["credentials"]["client_secret"],
        access_token=config["credentials"]["access_token"],
    )

    client = boxsdk.Client(oauth)

    return client


def filelist_from_item(item, path_from_root):
    """
    Arguments
    ---------
    folder		: boxsdk folder/item object
    path_from_root	: path from root
    """
    item = dill.loads(item)

    if hasattr(item, "get_items"):
        return filelist_from_folder(item, os.path.join(path_from_root, item.name))

    return (path_from_root, item.name, item.object_id)


def filelist_from_folder(folder, path_from_root):
    """
    \b
    Get a list of files from a box folder

    Arguments
    ---------
    folder		: boxsdk folder/item object
    path_from_root	: path_from_root
    """

    itemlist = list(folder.get_items())
    num_procs = min(multiprocessing.cpu_count(), len(itemlist))

    if num_procs == 1:

        filelist = [
            filelist_from_item(dill.dumps(item), path_from_root) for item in itemlist
        ]

    else:

        with joblib.parallel_backend(n_jobs=num_procs, backend="loky"):
            filelist = joblib.Parallel(batch_size="auto")(
                joblib.delayed(filelist_from_item)(dill.dumps(item), path_from_root)
                for item in itemlist
            )

    filelist = list(itertools.chain.from_iterable(filelist))
    return filelist


def filelist_from_root(client, config):
    """
    \b
    Get a list of files from a box folder

    Arguments
    ---------
    client	: boxsdk client object
    config	: configuration dictionary
    """
    folder = client.folder(config["folder"]["box_id"])
    path_from_root = ""

    filelist = filelist_from_folder(folder, path_from_root)
    filelist = [filelist[i : i + 3] for i in range(0, len(filelist), 3)]

    return filelist


def fileupload_from_path(client, config, file_path):
    """
    Arguments
    ---------
    client	: boxsdk client object
    config	: configuration dictionary
    file_path	: path to file from working directory
    """
    if not os.path.isfile(file_path):
        raise ValueError

    path_from_root = os.path.abspath(file_path).replace(
        config["folder"]["local_path"] + "/", ""
    )

    upload_size = os.stat(file_path).st_size
    upload_id = None
    upload_obj = client.folder(config["folder"]["box_id"])
    upload_name = path_from_root.split("/")[-1]

    for node in path_from_root.split("/"):

        itemlist = upload_obj.get_items(fields=["id,name"])

        for item in itemlist:
            if item.name == node:
                upload_obj = item
                if not hasattr(item, "get_items"):
                    upload_id = item.id
                continue

        continue

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
            # the uploaded_file.id will be the same as 'existing_big_file_id'

    else:
        if upload_size < 20000000:
            new_file = upload_obj.upload(file_path)
            print(f'File "{new_file.name}" uploaded to Box with file ID {new_file.id}')

        else:
            # uploads large file to a root folder
            chunked_uploader = upload_obj.get_chunked_uploader(
                file_path=file_path, file_name=upload_name
            )
            uploaded_file = chunked_uploader.start()
            print(
                f'File "{uploaded_file.name}" uploaded to Box with file ID {uploaded_file.id}'
            )

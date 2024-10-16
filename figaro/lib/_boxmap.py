"""Module for library"""

# Standard libraries
import os
import math
import multiprocessing

# Specialized libraries
import dill
import yaml
import psutil
import joblib
import time
import pytz
from datetime import datetime
import hashlib


class YamlLoader(yaml.SafeLoader):
    """
    Class YamlLoader for YAML
    """

    def __init__(self, stream):
        """
        Constructor
        """
        super().__init__(stream)
        self._stream = stream

    def construct_mapping(self, node, deep=False):
        """
        Mapping function
        """
        mapping = set()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in mapping:
                print(f"ERROR:   Duplicate {key!r} key found in {self._stream.name!r}.")
                raise ValueError()
            mapping.add(key)
        return super().construct_mapping(node, deep)


def calculate_file_hash(file_path, chunk_size=65536):
    """
    Calculates the SHA-1 hash of a file in chunks to avoid memory issues with large files.

    Arguments
    ---------
    file_path : str
        Path to the file.
    chunk_size : int
        Size of each chunk to read from the file. Default is 64KB.

    Returns
    -------
    str : The SHA-1 hash of the file.
    """
    sha1 = hashlib.sha1()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            sha1.update(chunk)
    return sha1.hexdigest()


def is_file_changed(local_path, box_file, upload=False, download=False):
    """
    Checks if the file has changed between local and cloud.

    Arguments
    ---------
    local_path : str
        Local path to the file.
    box_file   : boxsdk.file.File
        Box file object to compare.

    Returns
    -------
    bool : True if the file has changed, False otherwise.
    """
    if upload and download:
        raise ValueError(f"upload and download are mutually exclusive options")

    elif not upload and not download:
        raise ValueError(f"Need either upload or download to be true")

    if not os.path.exists(local_path):
        return True

    # Get local file modification time (in seconds since the epoch)
    local_mtime = os.path.getmtime(local_path)
    local_time_utc = datetime.utcfromtimestamp(local_mtime).replace(tzinfo=pytz.UTC)

    # Get Box file modification time (converted to seconds since the epoch)
    box_mtime = datetime.strptime(box_file.modified_at, "%Y-%m-%dT%H:%M:%S%z")
    box_time_utc = box_mtime.astimezone(pytz.UTC)

    # Get local file size
    local_size = os.path.getsize(local_path)

    # Compare file times and hashes for upload or download
    if upload:
        # Check if cloud file is older than the local file
        if box_time_utc < local_time_utc:
            #
            # Get SHA-1 has for local and box file
            local_hash = calculate_file_hash(local_path)
            box_hash = box_file.sha1.lower()
            #
            # Check if hashes are inconsistent
            if local_hash[:40] != box_hash:
                return True

    if download:
        # Check if local file is older than the cloud file
        if box_time_utc > local_time_utc:
            #
            # Get SHA-1 has for local and box file
            local_hash = calculate_file_hash(local_path)
            box_hash = box_file.sha1.lower()
            #
            # Check if hashes are inconsistent
            if local_hash[:40] != box_hash:
                return True

    return False


def load_boxmap(config):
    """
    \b
    Load boxmap from .figaro/boxmap
    """
    filemap = multiprocessing.Manager().dict()
    foldermap = multiprocessing.Manager().dict()

    filemap_path = os.path.join(config["folder"]["local_path"], ".figaro", "filemap")
    foldermap_path = os.path.join(
        config["folder"]["local_path"], ".figaro", "foldermap"
    )

    if os.stat(filemap_path).st_size != 0:
        with open(filemap_path, "r") as stream:
            try:
                filemap.update(yaml.load(stream, Loader=YamlLoader))
            except yaml.YAMLError as exc:
                print(exc)

    if os.stat(foldermap_path).st_size != 0:
        with open(foldermap_path, "r") as stream:
            try:
                foldermap.update(yaml.load(stream, Loader=YamlLoader))
            except yaml.YAMLError as exc:
                print(exc)

    return filemap, foldermap


def write_boxmap(config, filemap, foldermap):
    """
    \b
    Write boxmap to .figaro/boxmap
    """
    with open(
        os.path.join(config["folder"]["local_path"], ".figaro", "filemap"), "w"
    ) as mapfile:
        for key, value in filemap.items():
            mapfile.write(f"{key}: {value}\n")

    with open(
        os.path.join(config["folder"]["local_path"], ".figaro", "foldermap"), "w"
    ) as mapfile:
        for key, value in foldermap.items():
            mapfile.write(f"{key}: {value}\n")


def boxmap_from_item(item, path_from_root, filemap, foldermap):
    """
    Arguments
    ---------
    folder		: boxsdk folder/item object
    path_from_root	: path from root
    boxmap		: multiprocessing manager dictionary
    """
    item = dill.loads(item)

    if hasattr(item, "get_items"):
        boxmap_from_folder(
            item, os.path.join(path_from_root, item.name), filemap, foldermap
        )
        foldermap.update({os.path.join(path_from_root, item.name): item.object_id})
    else:
        filemap.update({os.path.join(path_from_root, item.name): item.object_id})


def boxmap_from_folder(folder, path_from_root, filemap, foldermap):
    """
    \b
    Get a list of files from a box folder

    Arguments
    ---------
    folder		: boxsdk folder/item object
    path_from_root	: path_from_root
    """
    itemlist = list(folder.get_items())
    cpu_avail = max(
        1,
        psutil.cpu_count()
        - math.floor(psutil.cpu_percent() * psutil.cpu_count() / 100),
    )

    num_procs = min(cpu_avail, len(itemlist))

    if num_procs in [0, 1]:

        [
            boxmap_from_item(dill.dumps(item), path_from_root, filemap, foldermap)
            for item in itemlist
        ]

    else:

        with joblib.parallel_backend(n_jobs=num_procs, backend="loky"):
            joblib.Parallel(batch_size="auto")(
                joblib.delayed(boxmap_from_item)(
                    dill.dumps(item), path_from_root, filemap, foldermap
                )
                for item in itemlist
            )


def boxmap_from_root(client, config):
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

    filemap = multiprocessing.Manager().dict()
    foldermap = multiprocessing.Manager().dict()

    boxmap_from_folder(folder, path_from_root, filemap, foldermap)

    return filemap, foldermap

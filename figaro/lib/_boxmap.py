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

"""Module for library"""

import os
import sys
import dill
import itertools
import joblib
import tqdm
import multiprocessing


def filelist_from_item(item, path_from_root):
    """
    Arguments
    ---------
    item		: boxsdk item object
    path_from_root	: path from folder root
    """
    item = dill.loads(item)

    if hasattr(item, "get_items"):
        return filelist_from_folder(item, os.path.join(path_from_root, item.name))
    else:
        return (path_from_root, item.name, item.object_id)


def filelist_from_folder(folder, path_from_root=""):
    """
    Arguments
    ---------
    folder		: boxsdk folder object
    path_from_root	: path from folder root
    """

    itemlist = [item for item in folder.get_items()]

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


def fileupload_from_path(folder, path_from_root):
    """
    Arguments
    ---------
    folder		: boxsdk folder object
    path_from_root	: path from folder root
    """
    if not os.path.isfile(path_from_root):
        raise ValueError

    upload_size = os.stat(path_from_root).st_size
    upload_id = None
    upload_obj = folder

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
            updated_file = upload_obj.update_contents(path_from_root)
            print(f'File "{updated_file.name}" has been updated')

        else:
            # uploads new large file version
            chunked_uploader = upload_obj.get_chunked_uploader(path_from_root)
            uploaded_file = chunked_uploader.start()
            print(
                f'File "{uploaded_file.name}" uploaded to Box with file ID {uploaded_file.id}'
            )
            # the uploaded_file.id will be the same as 'existing_big_file_id'

    else:
        if upload_size < 20000000:
            new_file = upload_obj.upload(path_from_root)
            print(f'File "{new_file.name}" uploaded to Box with file ID {new_file.id}')

        else:
            # uploads large file to a root folder
            chunked_uploader = upload_obj.get_chunked_uploader(
                file_path=path_from_root, file_name=node
            )
            uploaded_file = chunked_uploader.start()
            print(
                f'File "{uploaded_file.name}" uploaded to Box with file ID {uploaded_file.id}'
            )

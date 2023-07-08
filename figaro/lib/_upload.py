"""Module for library"""

# Standard libraries
import os
import math

# Specialized libraries
import dill
import psutil
import joblib


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
        raise ValueError

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

    elif os.sep.join(path_from_root.split(os.sep)[:-1]) in foldermap.keys():
        upload_id = None
        upload_obj = client.folder(
            str(foldermap[os.sep.join(path_from_root.split(os.sep)[:-1])])
        )

    else:
        raise ValueError

    # for node in path_from_root.split(os.sep):
    #
    #    itemlist = upload_obj.get_items(fields=["id,name"])
    #
    #    for item in itemlist:
    #        if item.name == node:
    #            upload_obj = item
    #            if not hasattr(item, "get_items"):
    #                upload_id = item.id
    #            continue
    #
    #    continue

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


def fileupload_from_list(client, config, filemap, foldermap, filelist):
    """
    Arguments
    ---------
    client	: boxsdk client object
    config	: configuration dictionary
    file_path	: path to file from working directory
    """
    cpu_avail = max(
        1,
        psutil.cpu_count()
        - math.floor(psutil.cpu_percent() * psutil.cpu_count() / 100),
    )

    num_procs = min(cpu_avail, len(filelist))

    if num_procs == 1:

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

"""Command line interface for Jobrunner"""

# Standard libraries
import os
import toml

# Feature libraries
import click
import boxsdk

from figaro.cli import figaro
from figaro import lib


@figaro.command("download")
def download():

    config = lib.load_config()

    oauth = boxsdk.OAuth2(
        client_id=config["credentials"]["client_id"],
        client_secret=config["credentials"]["client_secret"],
        access_token=config["credentials"]["access_token"],
    )

    client = boxsdk.Client(oauth)

    remote_folder = client.folder(config["folder"]["box_id"])
    local_folder = config["folder"]["local_path"]

    filelist = lib.filelist_from_folder(remote_folder)
    filelist = [filelist[i : i + 3] for i in range(0, len(filelist), 3)]
    print(filelist)


@figaro.command("file-upload")
@click.argument("sourcelist", nargs=-1)
def file_upload(sourcelist):

    config = lib.load_config()

    oauth = boxsdk.OAuth2(
        client_id=config["credentials"]["client_id"],
        client_secret=config["credentials"]["client_secret"],
        access_token=config["credentials"]["access_token"],
    )

    client = boxsdk.Client(oauth)

    remote_folder = client.folder(config["folder"]["box_id"])
    local_folder = config["folder"]["local_path"]

    for source in sourcelist:
        lib.fileupload_from_path(
            remote_folder,
            os.path.abspath(source).replace(local_folder + "/", ""),
            source,
        )

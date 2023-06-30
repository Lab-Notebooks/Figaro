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

    config = toml.load(".figaro")

    oauth = boxsdk.OAuth2(
        client_id=config["credentials"]["client_id"],
        client_secret=config["credentials"]["client_secret"],
        access_token=config["credentials"]["access_token"],
    )

    client = boxsdk.Client(oauth)
    folder = client.folder(config["folder"]["box_id"])

    filelist = lib.filelist_from_folder(folder)
    filelist = [filelist[i : i + 3] for i in range(0, len(filelist), 3)]
    print(filelist)


@figaro.command("file-upload")
@click.argument("source")
def file_upload(source):

    config = toml.load(".figaro")

    oauth = boxsdk.OAuth2(
        client_id=config["credentials"]["client_id"],
        client_secret=config["credentials"]["client_secret"],
        access_token=config["credentials"]["access_token"],
    )

    client = boxsdk.Client(oauth)
    folder = client.folder(config["folder"]["box_id"])

    lib.fileupload_from_path(folder, source)

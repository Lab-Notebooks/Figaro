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
@click.argument("source")
def download(source):

    config = toml.load(".figaro")

    oauth = boxsdk.OAuth2(
        client_id=config["client_id"],
        client_secret=config["client_secret"],
        access_token=config["access_token"],
    )

    client = boxsdk.Client(oauth)
    folder = client.folder(source)

    filelist = lib.filelist_from_folder(folder)
    filelist = [filelist[i:i+3] for i in range(0,len(filelist),3)]
    print(filelist)

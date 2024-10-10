"""Command line interface for Jobrunner"""

import time
import click

from figaro.cli import figaro
from figaro import lib


@figaro.command("map-items")
def map_items():
    """
    \b
    Write project directory map from Box cloud storage
    """

    config = lib.load_config()
    client = lib.validate_credentials(config)

    filemap, foldermap = lib.boxmap_from_root(client, config)
    lib.write_boxmap(config, filemap, foldermap)


@figaro.command("upload-files")
@click.argument("sourcelist", nargs=-1)
def upload_files(sourcelist):
    """
    \b
    Upload files to Box cloud storage
    """

    config = lib.load_config()
    filemap, foldermap = lib.load_boxmap(config)
    client = lib.validate_credentials(config)

    lib.fileupload_from_list(client, config, filemap, foldermap, sourcelist)


@figaro.command("upload-folder")
@click.argument("folderpath", type=click.Path(exists=True))
def upload_folder(folderpath):
    """
    \b
    Upload a folder and its contents to Box cloud storage
    """
    config = lib.load_config()
    filemap, foldermap = lib.load_boxmap(config)
    client = lib.validate_credentials(config)

    lib.folderupload_recursive(client, config, filemap, foldermap, folderpath)


@figaro.command("download-files")
@click.argument("sourcelist", nargs=-1)
def download_files(sourcelist):
    """
    \b
    Download files from Box cloud storage
    """

    config = lib.load_config()
    filemap, foldermap = lib.load_boxmap(config)
    client = lib.validate_credentials(config)

    lib.filedownload_from_list(client, config, filemap, foldermap, sourcelist)


@figaro.command("download-folder")
@click.argument("folderpath", type=click.Path(exists=True))
def download_folder(folderpath):
    """
    \b
    Download a folder and its contents from Box cloud storage
    """
    config = lib.load_config()
    filemap, foldermap = lib.load_boxmap(config)
    client = lib.validate_credentials(config)

    lib.folderdownload_recursive(client, config, filemap, foldermap, folderpath)

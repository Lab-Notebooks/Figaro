"""Command line interface for Jobrunner"""

import time
import click

from figaro.cli import figaro
from figaro import lib


@figaro.command("map-files")
def map_files():
    """
    \b
    Write boxmap from cloud storage
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
    Upload files to a box cloud storage
    """

    config = lib.load_config()
    filemap, foldermap = lib.load_boxmap(config)
    client = lib.validate_credentials(config)

    lib.fileupload_from_list(client, config, filemap, foldermap, sourcelist)

@figaro.command("upload-folder")
@click.argument("folder_path", type=click.Path(exists=True))
def upload_folder(folder_path):
    """
    \b
    Upload a folder and its contents to Box cloud storage.
    
    Arguments:
    folder_path: Path to the local folder to upload.
    """
    config = lib.load_config()
    filemap, foldermap = lib.load_boxmap(config)
    client = lib.validate_credentials(config)

    # Call the recursive upload function
    lib.folderupload_recursive(client, config, filemap, foldermap, folder_path)

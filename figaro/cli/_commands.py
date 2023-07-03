"""Command line interface for Jobrunner"""

import click

from figaro.cli import figaro
from figaro import lib


@figaro.command("file-list")
def file_list():
    """
    \b
    Get file-list from cloud storage
    """

    config = lib.load_config()
    client = lib.validate_credentials(config)

    filelist = lib.filelist_from_root(client, config)
    print(filelist)


@figaro.command("file-upload")
@click.argument("sourcelist", nargs=-1)
def file_upload(sourcelist):
    """
    \b
    Upload files to a box cloud storage
    """

    config = lib.load_config()
    client = lib.validate_credentials(config)

    for source in sourcelist:
        lib.fileupload_from_path(client, config, source)

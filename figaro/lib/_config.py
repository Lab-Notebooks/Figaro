"""Module for library"""

# Standard libraries
import os
import toml

# Specialized libraries
import boxsdk


def load_config():
    """
    \b
    Load configuration from .figaro file
    by search backwards along a directory
    tree.

    Arguments
    ---------
    None

    Returns
    -------
    config	: dictionary representation of .figaro
    """
    search_path = os.getcwd().split(os.sep)

    for node in search_path[::-1]:

        config_file = os.path.join(os.sep.join(search_path), ".figaro", "config")

        if os.path.isfile(config_file):
            config = toml.load(config_file)
            config["folder"]["local_path"] = os.sep.join(search_path)
            break

        search_path.remove(node)

    return config


def validate_credentials(config):
    """
    \b
    Validate user credentials for Oauth
    or JWT authentication.

    Arguments
    ---------
    config	: configuration dictionary

    Returns
    client	: boxsdk client object
    """
    oauth = boxsdk.OAuth2(
        client_id=config["credentials"]["client_id"],
        client_secret=config["credentials"]["client_secret"],
        access_token=config["credentials"]["access_token"],
    )

    client = boxsdk.Client(oauth)

    return client

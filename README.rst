.. |icon| image:: ./media/icon.svg
   :width: 20

###############
 |icon| Figaro
###############

|Code style: black|

**********
 Overview
**********

Figaro is a tool designed to simplify the management of data
synchronization between local supercomputing environments and Box cloud
storage. It serves as a wrapper over the Box Python SDK, aiding in the
process of uploading files and folders to Box, and creating maps of
cloud storage items. Figaro is tailored for use on Linux platforms via
command line, making it an essential tool for handling data
synchronization for high-performance computing (HPC) workloads.

**************
 Key Features
**************

-  **Cloud Storage Mapping:** Figaro can generate a map of items stored
   in your Box cloud storage, which helps manage and track file
   locations.

-  **Efficient Uploads:** Upload files or entire folders to Box cloud
   storage directly from the command line, ensuring quick and efficient
   synchronization of large datasets or project files.

*******************
 Statement of Need
*******************

In scientific computing and supercomputing, managing large amounts of
data and synchronizing it between local environments and cloud storage
is crucial for maintaining workflows across HPC platforms. Box cloud
storage is widely used for its scalability and accessibility, but its
direct integration with supercomputing environments requires interface
with Box SDK. Figaro aids this process, allowing users to seamlessly
interact with Box from using a wrapper API, reducing the time and effort
needed for manual file transfers and organization.

**************
 Installation
**************

To install Figaro, we recommend using the following steps:

.. code::

   ./setup develop

This installs Figaro in development mode, which is ideal for testing
features and debugging the software. The installation relies on the
`click` library, which can be installed using:

.. code::

   pip install click

After installation, the ``figaro`` script is added to the
`$HOME/.local/bin` directory, so be sure to update your `PATH`
environment variable to use it from the command line.

Additionally, you need to create a ``.figaro`` folder in your project
directory, which will contain a configuration file called ``config``.
This file stores your Box developer credentials and folder information.
The configuration file should be populated as follows:

.. code:: toml

   [credentials]
   client_id = "<box-developer-app-id>"
   client_secret = "<box-developer-app-secret>"
   access_token = "<box-developer-app-access-token>"

   [folder]
   box_id = "<box-folder-id>"

Replace the placeholder values with your Box developer credentials. The
`box_id` is the ID of the folder in Box where files will be uploaded.

*******
 Usage
*******

You can use the `--help` option with each command to better understand
its functionality:

.. code::

   ▶ figaro --help
   Usage: figaro [OPTIONS] COMMAND [ARGS]...

     Figaro is a wrapper over Box (https://box.com)
     Python SDK to manage data syncronization requirements
     for supercomputing workloads on linux platforms.

   Options:
     -v, --version
     --help         Show this message and exit.

   Commands:
     download-files   Download files from Box cloud storage
     download-folder  Download a folder and its contents from Box cloud storage
     map-items        Write project directory map from Box cloud storage
     upload-files     Upload files to Box cloud storage
     upload-folder    Upload a folder and its contents to Box cloud storage

Here is an overview of the commands:

#. ``figaro map-items`` - This command creates a map of all items in
   your Box cloud storage and writes the output to a specified files.
   The map includes the structure of folders and files, helping you keep
   track of stored data.

#. ``figaro upload-files <file_list>`` - Use this command to upload a
   list of files to your project Box cloud storage. Figaro handles
   folder heiarchary implicitly using file and folder map

#. ``figaro upload-folder <local_folder>`` - This command uploads an
   entire folder from your local system to a destination folder in Box
   cloud storage. It recursively uploads all files and subfolders,
   providing an easy way to sync large datasets or project directories.

#. ``figaro download-files <file_list>`` - Use this command to download
   a list of files from your project Box cloud storage. Figaro handles
   folder heiarchary implicitly using file and folder map

#. ``figaro download-folder <cloud_folder>`` - This command downloads an
   entire folder from Box cloud storage to the corresponding destination
   on local system. It recursively downloads all files and subfolders,
   providing an easy way to sync large datasets or project directories.

**********
 Citation
**********

.. code::

   @software{Figaro,
      author       = {Akash Dhruv},
      title        = {{akashdhruv/Figaro: 0.dev}},
      month        = oct,
      year         = 2024,
      publisher    = {Zenodo},
      version      = {0.dev},
      doi          = {10.5281/zenodo.13910702},
      url          = {https://doi.org/10.5281/zenodo.13910702}
   }

.. |Code style: black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black

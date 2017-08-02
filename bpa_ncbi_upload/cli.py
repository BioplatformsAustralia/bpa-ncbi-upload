from __future__ import print_function

import argparse
import sys

from .util import make_logger, make_ckan_api
from .upload import upload_data


logger = make_logger(__name__)


def version():
    import pkg_resources
    version = pkg_resources.require("bpa_ncbi_upload")[0].version
    print('''\
bpa-ncbi-upload, version %s

Copyright 2017 CCG, Murdoch University
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.''' % (version))
    sys.exit(0)


def usage(parser):
    parser.print_usage()
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='store_true', help='print version and exit')
    parser.add_argument('-k', '--api-key', required=True, help='CKAN API Key')
    parser.add_argument('-u', '--ckan-url', required=True, help='CKAN base url')
    parser.add_argument('--ftp-url', required=True, help='FTP base URL')
    parser.add_argument('--ftp-folder', required=True, help='Folder to upload to')
    parser.add_argument('sra_tsv', help='SRA subtemplate to upload')
    parser.add_argument('state_file', help='path to a JSON file, in which the current upload state will be written')

    args = parser.parse_args()
    if args.version:
        version()
    ckan = make_ckan_api(args)
    upload_data(ckan, args)

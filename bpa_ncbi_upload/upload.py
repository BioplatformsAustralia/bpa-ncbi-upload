
import os
import csv
import json
from .util import make_logger


logger = make_logger(__name__)


def discover_ckan_urls(ckan, file_info):
    logger.info('Querying CKAN for file URLS (will take some time)')
    for filename, info in file_info.items():
        resource_obj = ckan.action.resource_show(id=info['md5'])
        url = resource_obj['url']
        assert(url.rsplit('/', 1)[-1] == filename)
        info['url'] = resource_obj['url']


def build_file_info(ckan, filename):
    file_info = {}
    with open(filename) as fd:
        reader = csv.reader(fd, dialect='excel-tab')
        header = next(reader)
        # assumption: columns starting with 'filename' are immediately followed by an MD5 checksum column
        filename_indexes = [idx for idx, col in enumerate(header) if col.startswith('filename')]
        for row in reader:
            for idx in filename_indexes:
                fastq_filename, fastq_md5 = row[idx], row[idx + 1]
                if fastq_filename:
                    assert(fastq_filename not in file_info)
                    file_info[fastq_filename] = {
                        'md5': fastq_md5,
                        'submitted': False,
                    }
    logger.info('%d files to submit to NCBI' % len(file_info))
    discover_ckan_urls(ckan, file_info)


def get_state(filename):
    try:
        with open(filename) as fd:
            state = json.load(fd)
    except FileNotFoundError:
        return None


def write_state(state, filename):
    new_filename = filename + '_tmp'
    with open(new_filename, 'w') as fd:
        json.dump(state, fd)
    os.rename(new_filename, filename)


def upload_data(ckan, args):
    state = get_state(args.state_file)
    if state is None:
        logger.info('First run: building initial upload state')
        state = build_file_info(ckan, args.sra_tsv)
        write_state(state, args.state_file)

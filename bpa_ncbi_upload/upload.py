
import os
import csv
import json
import tempfile
import subprocess
from .util import make_logger, authenticated_ckan_session


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
        filename_indexes = [idx for idx, col in enumerate(
            header) if col.startswith('filename')]
        for row in reader:
            for idx in filename_indexes:
                # skip if filename index is greater
                if idx > len(row):
                    break
                fastq_filename, fastq_md5 = row[idx], row[idx + 1]
                if fastq_filename:
                    assert(fastq_filename not in file_info)
                    file_info[fastq_filename] = {
                        'md5': fastq_md5,
                        'submitted': False,
                    }
    logger.info('%d files to submit to NCBI' % len(file_info))
    discover_ckan_urls(ckan, file_info)
    return file_info


def get_state(filename):
    try:
        with open(filename) as fd:
            return json.load(fd)
    except FileNotFoundError:
        return None


def write_state(state, filename):
    new_filename = filename + '_tmp'
    with open(new_filename, 'w') as fd:
        json.dump(state, fd)
    os.rename(new_filename, filename)


def get_auth_tkt(ckan):
    session = authenticated_ckan_session(ckan)
    cookie = [t for t in session.cookies if t.name == 'auth_tkt'][0]
    return cookie.value


def download_ckan_file(url, auth_tkt):
    basename = url.rsplit('/', 1)[-1]
    tempdir = tempfile.mkdtemp(prefix='bpa-ncbi-upload-data-')
    path = os.path.join(tempdir, basename)
    # mirrors that sometimes close connections. ugly, but pragmatic.
    wget_args = ['wget', '-q', '-c', '-t', '3',
                 '--header=Cookie: auth_tkt=%s' % auth_tkt, '-O', path, url]
    status = subprocess.call(wget_args)
    if status != 0:
        try:
            os.unlink(path)
        except OSError:
            pass
        try:
            os.rmdir(tempdir)
        except OSError:
            pass
        return None, None
    return tempdir, path


def calculate_md5sum(file_path):
    output = subprocess.check_output(['md5sum', file_path]).decode('utf8')
    return output.split()[0]


def ascp_upload(ascp_url, ascp_keyfile, file_path):
    cmd = [
        'ascp',
        '-d',  # make target directory if not there
        '-i', ascp_keyfile,
        file_path,
        ascp_url
    ]
    status = subprocess.call(cmd)
    if status != 0:
        logger.error('Upload to NCBI of %s failed. Status=%d.' %
                     (file_path, status))
        raise Exception("Upload failed.")


def upload_data(ckan, args):
    state = get_state(args.state_file)
    if state is None:
        logger.info('First run: building initial upload state')
        state = build_file_info(ckan, args.sra_tsv)
        write_state(state, args.state_file)

    auth_tkt = get_auth_tkt(ckan)
    for filename, info in state.items():
        if info['submitted']:
            continue
        logger.info('downloading %s from CKAN' % (filename))
        tempdir, ckan_path = download_ckan_file(info['url'], auth_tkt)
        try:
            md5sum = calculate_md5sum(ckan_path)
            assert(md5sum == info['md5'])
            logger.info('file checksum OK: %s' % (filename))
            # upload to NCBI
            ascp_upload(args.ascp_url, args.ascp_keyfile, ckan_path)
            logger.info('file uploaded successfully to NCBI: %s' % (filename))
            # done
            info['submitted'] = True
            write_state(state, args.state_file)
        finally:
            os.unlink(ckan_path)
            os.rmdir(tempdir)

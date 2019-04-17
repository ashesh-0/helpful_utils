"""
Google drive utils. Mainly to work with colab.
Adapted from https://colab.research.google.com/drive/1P2AmVHPmDccstO0BiGu2uGAG0vTx444b#scrollTo=qn79wv8fuwHF
"""
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.client import GoogleCredentials
import zipfile
import os

ModelDirectory = 'Code_models'


def install():
    print('Run following in the cell: "!pip install -U -q PyDrive"')


def get_drive():
    from google.colab import auth
    # 1. Authenticate and create the PyDrive client.
    auth.authenticate_user()
    gauth = GoogleAuth()
    gauth.credentials = GoogleCredentials.get_application_default()
    drive_obj = GoogleDrive(gauth)

    if not os.path.exists(ModelDirectory):
        os.makedirs(ModelDirectory)

    return drive_obj


def upload_file(drive_obj, filename):
    f = drive_obj.CreateFile()
    f.SetContentFile(filename)
    f.Upload()


def download_file(drive_obj, file_id, output_fname=None):
    gfile = drive_obj.CreateFile({'id': file_id})
    if output_fname is None:
        output_fname = file_id
    gfile.GetContentFile(output_fname)

    return output_fname


def mount_drive():
    from google.colab import drive
    drive.mount('/content/gdrive', force_remount=True)


def zipfolder(foldername, target_dir):
    """
    Args:
        foldername: Name of the output folder. Actual name will be `foldername`.zip
        target_dir: Directory whose contents need to be zipped
    Returns:
        name of the zipped file.
    """
    zip_fname = foldername + '.zip'
    zipobj = zipfile.ZipFile(zip_fname, 'w', zipfile.ZIP_DEFLATED)
    rootlen = len(target_dir) + 1
    for base, dirs, files in os.walk(target_dir):
        for fname in files:
            fn = os.path.join(base, fname)
            zipobj.write(fn, fn[rootlen:])

    return zip_fname


class GdriveUtils:
    def __init__(self, temp_folder='/home/ashesh/Documents/initiatives/helpful_utils/temp/'):
        self._drive_obj = get_drive()
        # self._temp_folder = 'drive_utils_temp/'
        self._temp_folder = temp_folder

    def _new_folder(self):
        i = -1

        if not os.path.exists(self._temp_folder):
            os.mkdir(self._temp_folder)

        while True:
            i += 1
            foldername = self._temp_folder + str(i) + '/'
            if os.path.exists(foldername):
                continue

            os.mkdir(foldername)
            return foldername

    def upload_folder(self, target_dir: str):

        if target_dir[-1] == '/':
            target_dir = target_dir[:-1]

        zip_fname = zipfolder(os.path.basename(target_dir), target_dir)
        self.upload_file(zip_fname, compress=False)

    def download_folder(self, file_id):
        zip_fname = download_file(self._drive_obj, file_id)
        assert zip_fname[-4:] == '.zip'
        with zipfile.ZipFile(zip_fname, 'r') as zip_ref:
            output_folder = self._new_folder()
            zip_ref.extractall(output_folder)
        return output_folder

    def upload_file(self, fname, compress=True):
        if compress:
            zip_fname = self.compress(fname)
            fname = zip_fname

        upload_file(self._drive_obj, fname)

    def compress(self, fname):
        zip_fname = fname + '.zip'
        with zipfile.ZipFile(zip_fname, 'w', zipfile.ZIP_DEFLATED) as zipobj:
            zipobj.write(fname, os.path.basename(fname))

        return zip_fname

    def decompress_one_file(self, zip_fname):
        with zipfile.ZipFile(zip_fname, 'r') as zip_ref:
            output_folder = self._new_folder()
            zip_ref.extractall(output_folder)
            r, d, f = list(os.walk(output_folder))[0]
            assert r == output_folder
            files = list(f)
            assert len(files) == 1
            parent_dir = os.path.abspath(r + '/..')
            new_location = os.path.join(parent_dir, files[0])
            print('new location', new_location)
            os.rename(os.path.join(r, files[0]), new_location)
            os.rmdir(output_folder)
        return new_location

    def download_file(self, file_id, output_fname=None, decompress=True):
        output_fname = download_file(self._drive_obj, file_id, output_fname=output_fname)
        if output_fname[-4:] == '.zip' and decompress:
            unzipped_fname = self.decompress_one_file(output_fname)

            if unzipped_fname != output_fname:
                os.remove(output_fname)

            return unzipped_fname

        return output_fname

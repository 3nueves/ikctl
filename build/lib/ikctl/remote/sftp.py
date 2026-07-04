class Sftp:
    """ Class to management files and folders on remote servers """

    def __init__(self)-> None:
        pass

    def upload_file(self, client, scripts, remote_path):
        sftp = client
        sftp.put(scripts, remote_path)

    def create_folder(self, client, folder):
        sftp = client
        sftp.mkdir(folder)

    def remove_folder(self, client):
        sftp = client
        sftp.rmdir(".ikctl")

    def remove_files(self, client):
        sftp = client
        sftp.remove(".ikctl")

    def change_current_directory(self, client):
        sftp = client
        sftp.chdir(".ikctl")

    def change_permisions(self, client, file):
        sftp = client
        sftp.chmod(file, 755)

    def list_dir(self, client, folder=None):
        sftp = client
        if folder is not None:
            folder = sftp.listdir(folder)
        else:
            folder = sftp.listdir()
        return folder

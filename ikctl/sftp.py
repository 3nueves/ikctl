class Sftp:

    def __init__(self)-> None:
        pass

    def upload_file(self, client, scripts, remote_path):
        sftp = client
        sftp.put(scripts, remote_path)

    def create_folder(self, client):
        sftp = client
        sftp.mkdir(".ikctl")

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

    def list_dir(self, client, user):
        sftp = client
        if user != "root": 
            folder = sftp.listdir("/home/"+user)
        else:
            folder = sftp.listdir("/root")
        return folder
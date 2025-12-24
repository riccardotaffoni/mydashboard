from io import BytesIO
import paramiko
import pandas as pd

def read_from_ftp(
    filename,
    path="opt/veostrading/veos_ita_automation/",
):
    # SSH connection details
    hostname = "poet.veos.digital"
    port = 4022
    username = "riccardo.taffoni"
    password = "VeosGroup2024!"  # lascia vuoto se usi solo la chiave

    remote_filepath = f"../../{path}{filename}"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=hostname,
        port=port,
        username=username,
        password=password,
    )

    sftp = ssh.open_sftp()

    try:
        file_bytes = BytesIO()
        with sftp.open(remote_filepath, 'rb') as remote_file:
            file_bytes.write(remote_file.read())

        file_bytes.seek(0)
        df = pd.read_feather(file_bytes)

        print(f"📥 File {filename} letto con successo")

    finally:
        sftp.close()
        ssh.close()

    return df

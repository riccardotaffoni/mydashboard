from io import BytesIO
import paramiko
import pandas as pd
import streamlit as st
def read_from_ftp(
    filename,
    path="opt/veostrading/veos_ita_automation/",
    return_mtime=True
):
    # SSH connection details
    hostname = st.secrets["FTP_HOST"]
    port = 4022
    username = st.secrets["username"]
    password = st.secrets["password"]  # lascia vuoto se usi solo la chiave

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
        # 🔹 mtime remoto
        stat = sftp.stat(remote_filepath)
        remote_mtime = stat.st_mtime

        # 🔹 lettura file
        buffer = BytesIO()
        with sftp.open(remote_filepath, 'rb') as f:
            buffer.write(f.read())
        buffer.seek(0)

        df = pd.read_feather(buffer)

        print(f"📥 File {filename} letto correttamente")

    finally:
        sftp.close()
        ssh.close()

    if return_mtime:
        return df, remote_mtime
    else:
        return df

def get_remote_mtime(
    filename,
    path,
):
    hostname = st.secrets["FTP_HOST"]
    port = 4022
    username = st.secrets["username"]
    password = st.secrets["password"]  # lascia vuoto se usi solo la chiave

    remote_filepath = f"../../{path}{filename}"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=hostname,
        port=port,
        username=username,
        password=password
    )

    sftp = ssh.open_sftp()

    try:
        stat = sftp.stat(remote_filepath)
        return stat.st_mtime
    finally:
        sftp.close()
        ssh.close()

from io import BytesIO
import paramiko
import pandas as pd
import streamlit as st
def read_from_ftp(
    filename,
    path="opt/veostrading/veos_ita_automation/",
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

import paramiko
from pathlib import Path


class Remote:

    def __init__(self, user, remote, venv=None):
        self.user = user
        self.remote = remote
        self.venv = venv

    def execute_script(self, script, venv=None) -> str:
        """ Execute script and return stdout

        :param script: Python code to execute
        :param venv:  Path to venv, which takes precedence over self.venv
        :return: stdout string
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.remote, username=self.user)

        # Python expects stream input from stdin
        cmd = "python3 -"

        if self.venv is not None:
            pathlib_venv = Path(self.venv) / "bin" / "activate"
            cmd = f"bash -lc 'source {pathlib_venv.as_posix()} && python3 -'"

        if venv is not None:
            pathlib_venv = Path(venv) / "bin" / "activate"
            cmd = f"bash -c 'source {pathlib_venv.as_posix()} && python3 -'"

        stdin, stdout, stderr = ssh.exec_command(cmd)
        # Pass code to stream
        stdin.write(script)
        # Send end of file (EOF)
        stdin.channel.shutdown_write()

        out = stdout.read().decode()
        _err = stderr.read().decode()

        ssh.close()
        _exit_status = stdout.channel.recv_exit_status()

        # if exit_status != 0:
        #     raise RuntimeError(
        #         f"Remote exit code: {exit_status}\n"
        #         f"--- STDERR ---\n{err or '<empty>'}\n"
        #         f"--- STDOUT (truncated) ---\n{out[:2000]}"
        #     )
        return out

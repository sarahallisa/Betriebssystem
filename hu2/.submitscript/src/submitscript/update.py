import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory

import semver

from submitscript.data import DataDirectory
from submitscript.execute_subprocess import execute_subprocess
from submitscript.output import interface_print
from submitscript.util.prompt import YesNoParser, prompt


def get_current_version() -> semver.VersionInfo:
    with open("version", "r") as file:
        return semver.VersionInfo.parse(file.read())


def update(data: DataDirectory) -> None:
    backend = data.get_backend().client

    current = get_current_version()
    available = backend.get_current_version()

    if current < available:
        interface_print("Update available")

        if prompt("Do you want to view the changelog?", YesNoParser(True)):
            changelogs = backend.get_changelogs()

            for key in sorted(changelogs.keys()):
                interface_print("=== Changes in version %s ===" % str(key))
                interface_print(changelogs[key])
                interface_print()

        if prompt("Do you want to download the update now?", YesNoParser(True)):
            with TemporaryDirectory() as temp_dir:
                path = Path(temp_dir) / "client.tgz"

                with path.open("wb") as f:
                    f.write(backend.get())

                with tarfile.open(str(path)) as f:
                    f.extractall(str(Path.cwd().parent))

                interface_print("Update complete. Restarting script.")
                execute_subprocess(["./main.sh"], capture_output=False)
                exit(0)

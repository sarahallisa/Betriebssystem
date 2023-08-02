from pathlib import Path

import requests

from submitscript.data.data_directory import DataDirectory
from submitscript.output import interface_print, set_global_log_file, global_log_file
from submitscript.submit import check_for_new_results, submit
from submitscript.team import ensure_team_existence
from submitscript.update import update
from submitscript.util.prompt import YesNoParser, prompt


def main():
    root_directory = Path.cwd().parent.parent
    data_directory = DataDirectory(Path.cwd().parent / "data")

    set_global_log_file(data_directory.create_logfile())

    bootstrap_log_path = Path("bootstrap.log")
    if bootstrap_log_path.is_file():
        global_log_file.log("Bootstrap log:\n%s" % bootstrap_log_path.open().read())

    interface_print("=== Welcome ===")

    update(data_directory)

    check_for_new_results(data_directory)
    ensure_team_existence(data_directory)

    def start_submission():
        interface_print()
        success = submit(root_directory, data_directory)
        interface_print()

        if success:
            if prompt("Do you want to submit another solution?", YesNoParser(True)):
                start_submission()
        else:
            if prompt("Do you want to try again?", YesNoParser(True)):
                start_submission()

    if prompt("Do you want to submit a solution now?", YesNoParser(True)):
        start_submission()


if __name__ == '__main__':
    try:
        main()
    except requests.exceptions.ConnectionError as e:
        interface_print("The server can not be reached. You may need to be logged in to the VPN.")
        interface_print("Aborting.")
        exit(1)
    except KeyboardInterrupt:
        interface_print()  # Print a single linefeed to avoid having the new command prompt dangle in the same line as the last output line
        exit(0)

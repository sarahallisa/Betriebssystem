import shutil
import tarfile
import tempfile
import traceback
import sys
from pathlib import Path
from typing import List, Optional

from submitscript.data.assignment import Assignment
from submitscript.data.config import SkeletonVariant
from submitscript.data.data_directory import DataDirectory
from submitscript.data.submission import SubmissionStatus
from submitscript.execute_subprocess import execute_subprocess
from submitscript.output import interface_print, global_log_file
from submitscript.util.prompt import prompt, YesNoParser, SelectionParser


def check_for_new_results(data_directory: DataDirectory):
    # Check every submission for new results
    try:
        for assignment in data_directory.get_assignments():
            for submission in assignment.get_submissions():
                if not submission.bookkeeping_data.get().status == SubmissionStatus.accepted:
                    continue

                if submission.check_for_evaluation_results():
                    submission.print_evaluation_results()
                    continue

                # Check if the submission still exists (may have been removed) and if it is eligible for result subscription
                if submission.bookkeeping_data.get().status == SubmissionStatus.accepted and submission.submission_response.get().immediate_evaluation:
                    if prompt("Do you want to subscribe to the results of submission %s?" % submission.submission_data.get().submission_id, YesNoParser(True)):
                        submission.wait_for_evaluation_results()
    except Exception as e:
        global_log_file.error("".join(traceback.format_exception(*sys.exc_info())))

        # Errors when checking for new results should never prevent students from submitting, so we are a fault tolerant.
        interface_print("Error while checking for new results: %s" % str(e))
        interface_print("Please report this issue. You will still be able to submit a solution.")


def select_assignment(options: List[Assignment]) -> Optional[Assignment]:
    if len(options) == 0:
        return None

    if len(options) == 1:
        return options[0]

    return prompt("Please choose the assignment you want to submit.", SelectionParser([(a.assignment_id, a) for a in options], None))


def select_variant(root_directory: Path, data: DataDirectory) -> Optional[SkeletonVariant]:
    found_options = [v for v in data.config.get().skeleton_variants if (root_directory / v.root).is_dir()]

    if len(found_options) == 0:
        interface_print("No skeleton variant found! Did you delete all of them?")
        return None

    if len(found_options) == 1:
        return found_options[0]

    return prompt("Please choose the variant you want to submit.", SelectionParser([(a.name, a) for a in found_options], None))


def build_solution(directory: Path, selected_variant: SkeletonVariant) -> bool:
    interface_print("=== Building submission ===")
    interface_print("Running '%s'." % selected_variant.build)
    interface_print("=== Building submission finished ===")

    build_result = execute_subprocess([selected_variant.build], cwd=directory, is_shell_command=True, merge_stdout_stderr=True)

    if not build_result.is_success():
        interface_print("Building your solution failed!")
        if prompt("Do you want to view the build log?", YesNoParser(True)):
            interface_print("=== BEGIN Build Log ===")
            interface_print(build_result.stdout, end='')
            interface_print("=== END Build Log ===")

        if not prompt("Do you want to submit your solution anyway, despite the failing build?", YesNoParser(False)):
            interface_print("Aborting submission.")
            return False

    return True


def clean_directory(directory: Path, selected_variant: SkeletonVariant):
    def clean_helper(path: Path):
        if path.is_file():
            str(path.relative_to(directory))

            if not selected_variant.is_filename_allowed(str(path.relative_to(directory))):
                path.unlink()
        elif path.is_dir():
            for child in path.iterdir():
                clean_helper(child)
            if not any(path.iterdir()):
                path.rmdir()

    interface_print("=== Cleaning directory for submission ===")
    clean_helper(directory)
    interface_print("=== Cleaning directory finished ===")


def submit(root_directory: Path, data: DataDirectory) -> bool:
    """
    :returns Whether a solution was submitted.
    """
    interface_print("=== Submitting ===")

    submission = None
    try:
        selected_assignment = select_assignment(data.get_assignments())
        interface_print()
        if selected_assignment is None:
            return False

        selected_variant = select_variant(root_directory, data)
        interface_print()

        if selected_variant is None:
            return False

        interface_print("Selected variant '%s' for assignment '%s'." % (selected_variant.name, selected_assignment.assignment_id))

        submission = selected_assignment.create_submission()

        submission.team.set(data.team.get())
        submission.variant.set(selected_variant.variant_data)

        # Create temporary directory to build submission.
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_solution_root = Path(tmpdir) / selected_variant.root
            shutil.copytree(root_directory / selected_variant.root, tmp_solution_root)

            if not build_solution(tmp_solution_root, selected_variant):
                return False

            clean_directory(tmp_solution_root, selected_variant)

            with tempfile.TemporaryFile() as temp_file:
                with tarfile.open(fileobj=temp_file, mode='w:gz', format=tarfile.GNU_FORMAT) as tar:
                    tar.add(tmp_solution_root, recursive=True, arcname="/%s" % selected_variant.root)

                submission.set_upload_file(temp_file)

        return submission.submit()
    except KeyboardInterrupt:
        interface_print("=== Aborted Submitting ===")
        if submission is not None:
            submission.delete()
        return False

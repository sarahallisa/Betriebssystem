from submitscript.data import Team
from submitscript.data.data_directory import DataDirectory
from submitscript.data.student import Student
from submitscript.output import interface_print
from submitscript.util.prompt import prompt, YesNoParser, NameParser, MatriculationNumberParser


def prompt_student(member_number: int) -> Student:
    while True:
        interface_print("Please enter details of team member %d." % member_number)

        lastname = prompt("Last Name:", NameParser())
        firstname = prompt("First Name:", NameParser())
        matriculation_number = prompt("Matriculation number:", MatriculationNumberParser())

        member = Student(lastname, firstname, matriculation_number)

        interface_print()
        interface_print("First name: %s; Last name: %s; Matriculation number: %s" % (member.first_name, member.last_name, member.matriculation_number))

        if prompt("Is this correct?", YesNoParser(False)):
            return member


def create_team_json(data: DataDirectory) -> None:
    members = []
    interface_print("A new team.json will now be created.\n")

    while True:
        members.append(prompt_student(len(members) + 1))

        if len(members) >= data.config.get().max_team_size or not prompt("Another?", YesNoParser(True)):
            break

    data.team.set(Team(members))

    interface_print("team.json successfully created.\n")


def ensure_team_existence(data: DataDirectory, can_be_skipped: bool = False) -> None:
    if not data.team.has_value():
        interface_print("There is no team.json saved yet. You will need to provide information about your team before you can submit solutions.")
        if not can_be_skipped or prompt("Do you want to create a team.json now?", YesNoParser(True)):
            create_team_json(data)
    else:
        interface_print("Please review the currently saved information about your team:")

        i = 1
        for member in data.team.get().members:
            interface_print(" %d - First name: %s; Last name: %s; Matriculation number: %s" % (i, member.first_name, member.last_name, member.matriculation_number))
            i += 1

        if not prompt("Is this information up to date?", YesNoParser(True)):
            create_team_json(data)

        interface_print()

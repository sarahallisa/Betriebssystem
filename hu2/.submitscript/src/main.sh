#!/usr/bin/env bash

{

  function is_macos() {
    [[ "$OSTYPE" == "darwin"* ]]
    return $?
  }

  function resolve_absolute_path() {
    if is_macos; then
      if which greadlink >/dev/null; then
        # Use greadlink if defined because we know for sure this works
        greadlink -f "$*"
      else
        # If greadlink is not available we can hack our way there with this.
        # https://stackoverflow.com/a/5756763
        ABSPATH="$(cd "$(dirname "$*")"; pwd -P)/$(basename "$*")"
        echo "$ABSPATH"
      fi
    else readlink -f "$*"; fi
  }

  SCRIPT=$(resolve_absolute_path "$0")
  SCRIPTPATH=$(dirname "$SCRIPT")

  exec &> >(tee "$SCRIPTPATH/bootstrap.log")

  PYTHON3_INTERPRETER=""
  PYTHON3_PIP=""
  PIPENV=""
  PACKAGE_MANAGER=""

  # In certain misconfigured environments running python <= 3.6 the command line parse 'click' raises an exception
  # To mitigate this we can manually set the environment variables LC_ALL and LANG
  export LC_ALL=C.UTF-8
  export LANG=C.UTF-8

  # prepend_sudo: Prepends 'sudo' to a command if necessary.
  #               This is included to allow the script to run in docker-containers where sudo does not exist
  function prepend_sudo() {
    if [ -x "$(command -v sudo)" ]; then
      echo "sudo $*"
    else
      echo "$*"
    fi
  }

  # run_command: Asks for permission to run a command given via it's arguments.
  #              If permission is given the command is run.
  #              If permission is denied the script ends.
  function run_command() {
    log "I want to run the command '$*'."
    read -p "[Bootstrap] Do you want to run this command now? [yN]" -n 1 -r
    echo # move to a new line
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      log "Permission to run a command refused."
      log "You need to install the missing dependencies manually or give permission to the script to do it for you."
      give_up
    fi

    log "Running '$*'"
    if [[ $* == *"sudo"* ]]; then log "You may be asked for your root password."; fi
    eval "$*"
  }

  # log: Utility function that prints a line with the prefix "[Bootstrap] "
  function log() {
    echo "[Bootstrap] $*"
  }

  # give_up: Prints a resigning message and exits
  function give_up() {
    log "I'm giving up." && exit 1
  }

  # identify_python3_and_pip: Tries to identify the python3 command and its associated pip.
  #                           Returns 0 if both were identified, 1 otherwise.
  #                           Identified commands are placed in the globals PYTHON3_INTERPRETER and $PYTHON3_PIP
  function identify_python3_and_pip() {
    function identify_python3() {
      function check_python3_interpreter_version() {
        PYTHON3_INTERPRETER=$(resolve_absolute_path "$*")
        regex="Python ([0-9]+)\.([0-9]+)\.([0-9]+)"

        v=$(eval "$PYTHON3_INTERPRETER" --version 2>/dev/null)

        if [[ "$v" =~ $regex ]]; then
          major=${BASH_REMATCH[1]}
          minor=${BASH_REMATCH[2]}
          # patch=${BASH_REMATCH[3]}

          if [ "$major" -ge 3 ] && [ "$minor" -ge 6 ]; then
            echo "Identified" "$("$PYTHON3_INTERPRETER" --version)" "at" "$PYTHON3_INTERPRETER"
            return 0
          fi
        fi

        return 1
      }

      check_python3_interpreter_version "$(which python3.10)" && return 0
      check_python3_interpreter_version "$(which python3.9)" && return 0
      check_python3_interpreter_version "$(which python3.8)" && return 0
      check_python3_interpreter_version "$(which python3.7)" && return 0
      check_python3_interpreter_version "$(which python3.6)" && return 0
      check_python3_interpreter_version "$(which python3)" && return 0

      log "No suitable python3 interpreter identified. I require at least Python 3.6"
      return 1
    }

    function identify_pip() {
      cmd="$PYTHON3_INTERPRETER -m pip"
      id=$(eval "$cmd --version" 2>/dev/null)
      res=$?
      if [ "$res" -eq 0 ]; then
        PYTHON3_PIP=$cmd
        log "Identified $id' at $cmd"
        return 0
      fi
      return 1
    }

    identify_python3 && identify_pip

    return $?
  }

  # identify_pipenv: Tries to identify the pipenv command associated with the existing PYTHON3_INTERPRETER
  #                  Returns 0 if it was identified, 1 otherwise.
  #                  The identified command is placed in the global PIPENV
  function identify_pipenv() {
    cmd="$PYTHON3_INTERPRETER -m pipenv"
    id=$(eval "$cmd --version" 2>/dev/null)
    res=$?
    if [ "$res" -eq 0 ]; then
      PIPENV=$cmd
      log "Identified '$id' at $cmd"
      return 0
    fi
    return 1
  }

  # ensure_python3_and_pip: Tries to identify python3 and its associated pip.
  #                         If it fails this function tries to install them.
  #                         If the installation or the subsequent repeated identifation fail, this function exits the script.
  function ensure_python3_and_pip() {
    function identify_package_manager() {
      function check_package_manager() {
        PACKAGE_MANAGER="$*"

        if [ ! -x "$(command -v "$PACKAGE_MANAGER")" ]; then return 1; fi

        log "Identified package manager '$PACKAGE_MANAGER'."
        return 0
      }

      if check_package_manager apt; then return 0; fi

      return 1
    }

    function install_python3_and_pip() {
      function try_to_remedy_failing_package_installation() {
        local COMMAND
        case $PACKAGE_MANAGER in
        "apt")
          COMMAND=$(prepend_sudo "apt update")
          ;;
        esac

        log "Trying to fix installation issues for you."
        if ! run_command "$COMMAND"; then
          log "Trying to fix installation issues failed."
          give_up
        fi
      }

      log "Trying installation of 'python3' and 'pip3' with the system package manager."

      if ! identify_package_manager; then
        log "I can't help you further because I do not recognize your package manager."
        log "You need to install a python3 interpreter and pip3!"
        give_up
      fi

      local COMMAND
      case $PACKAGE_MANAGER in
      "apt")
        COMMAND=$(prepend_sudo "apt install -y python3 python3-pip")
        ;;
      esac

      if ! run_command "$COMMAND"; then
        log "Automated package installation failed."
        try_to_remedy_failing_package_installation

        if ! run_command "$COMMAND"; then
          log "Automated package installation failed again. I'm giving up."
          log "You may need to install dependencies manually."
          give_up
        fi
      fi

      log "Automated package installation successful."
    }

    if ! identify_python3_and_pip; then
      install_python3_and_pip

      if ! identify_python3_and_pip; then
        log "Even after an apparently successful python3 installation no interpreter could be found."
        log "I'm giving up." && exit 1
      fi
    fi
  }

  # ensure_pipenv: Tries to identify 'pipenv'. If it does not exist, pipenv is installed via pip.
  #                This function REQUIRES the variables PYTHON3_INTERPRETER and PYTHON3_PIP to contain values.
  function ensure_pipenv() {
    function install_pipenv() {
      log "python3 module 'pipenv' is missing."
      log "Attempting automated installation of the missing package."
      local COMMAND="$PYTHON3_PIP install pipenv"

      if ! run_command "$COMMAND"; then
        log "Automated python package installation failed."
        log "You may need to install dependencies manually."
        give_up
      fi

      log "Automated python package installation successful."
    }

    if ! identify_pipenv; then
      install_pipenv

      if ! identify_pipenv; then
        log "Even after an apparently successful pipenv installation the module could not be found."
        log "I'm giving up." && exit 1
      fi
    fi
  }

  # Ensure the working directory exists
  cd "$SCRIPTPATH" || (log "There's an issue with your folder structure" && give_up)

  # Ensure the existence of all necessary executables/python modules
  ensure_python3_and_pip
  ensure_pipenv

  function pipenv_install() {
    cmd="$PIPENV install --python $major.$minor"
    log "Running '$cmd' to ensure the existence of a virtual environment."
    log "This may take a moment."
    eval "$cmd"
    return $?
  }

  if ! pipenv_install; then
    log "Installing script dependencies failed."
    log "I will now try to remove and recreate a potentially existing virtual environment."

    if ! (eval "$PIPENV --rm"); then
      log "I could not remove the virtual environment."
      give_up
    fi

    if ! pipenv_install; then
      log "Installing script dependencies failed again."
      log "There is nothing more I can do about this. Please get help from your teacher."
      give_up
    fi
  fi

  log "Running the script in a virtual environment."
  echo "$PIPENV run python3 ./main.py"
  eval "$PIPENV run python3 ./main.py"

  exit 0
}

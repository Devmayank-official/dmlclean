# bash completion for dmlclean
# Generated for DMLClean v0.1.0
# Place in: /etc/bash_completion.d/ or ~/.bash_completion.d/

_dmlclean_completion() {
    local IFS=$'\n'
    local response

    response=$(env COMP_WORDS="${COMP_WORDS[*]}" COMP_CWORD=$COMP_CWORD _DMLCLEAN_COMPLETE=bash_complete $1)

    for completion in $response; do
        IFS=',' read type value <<< "$completion"

        if [[ $type == 'dir' ]]; then
            COMPREPLY=()
            compopt -o dirnames
        elif [[ $type == 'file' ]]; then
            COMPREPLY=()
            compopt -o default
        elif [[ $type == 'plain' ]]; then
            COMPREPLY+=($value)
        fi
    done

    return 0
}

_dmlclean_completion_setup() {
    complete -o nosort -F _dmlclean_completion dmlclean
}

_dmlclean_completion_setup

# Main command completions
complete -W "scan clean schedule config protect history report doctor profile plugin storage trends system version --help --version --verbose --quiet" dmlclean

# Scan command completions
complete -W "fast deep custom --mode --categories --path --json --quiet --help" -P "scan " dmlclean

# Clean command completions
complete -W "dry-run trash permanent --mode --profile --categories --min-age --min-size --force --yes --path --help" -P "clean " dmlclean

# Schedule command completions
complete -W "list add remove enable disable run install uninstall --help" -P "schedule " dmlclean

# Config command completions
complete -W "show set get export --help" -P "config " dmlclean

# Protect command completions
complete -W "add remove list check --help" -P "protect " dmlclean

# History command completions
complete -W "list undo export clear --help" -P "history " dmlclean

# Profile completions
complete -W "developer designer system-admin gamer minimal" -P "clean --profile " dmlclean
complete -W "developer designer system-admin gamer minimal" -P "--profile " dmlclean

# Mode completions
complete -W "fast deep custom" -P "scan --mode " dmlclean
complete -W "dry-run trash permanent" -P "clean --mode " dmlclean

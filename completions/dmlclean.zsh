# zsh completion for dmlclean
# Generated for DMLClean v0.1.0
# Place in: ~/.zsh/completions/ or /usr/local/share/zsh/site-functions/

#compdef dmlclean

autoload -U is-at-least

_dmlclean() {
    typeset -A opt_args
    typeset -a _arguments_options
    local ret=1

    if is-at-least 5.2; then
        _arguments_options=(-s -S -C)
    else
        _arguments_options=(-s -C)
    fi

    local context curcontext="$curcontext" state line

    local -a subcommands
    subcommands=(
        "scan:Scan for cleanable files"
        "clean:Execute cleaning operation"
        "schedule:Manage scheduled cleaning"
        "config:Manage configuration"
        "protect:Manage Protected Zone"
        "history:View/undo cleaning history"
        "report:Generate reports"
        "doctor:System diagnostics"
        "profile:Profile management"
        "plugin:Plugin management"
        "storage:Storage management"
        "trends:Disk usage trends"
        "system:System commands"
        "version:Show version"
    )

    _arguments "${_arguments_options[@]}" \
        '--help[Show help message]' \
        '--version[Show version]' \
        '-v[Show version]' \
        '--verbose[Enable debug logging]' \
        '-V[Enable debug logging]' \
        '--quiet[Suppress all output except errors]' \
        '-q[Suppress all output except errors]' \
        "(- *)":(-: :->subcommands) \
        "(- *):{ _describe 'command' subcommands }" \
        && ret=0

    case $state in
        subcommands)
            local -a subcommand_actions
            subcommand_actions=(
                'scan:_dmlclean_scan'
                'clean:_dmlclean_clean'
                'schedule:_dmlclean_schedule'
                'config:_dmlclean_config'
                'protect:_dmlclean_protect'
                'history:_dmlclean_history'
                'report:_dmlclean_report'
                'doctor:_dmlclean_doctor'
                'profile:_dmlclean_profile'
                'plugin:_dmlclean_plugin'
                'storage:_dmlclean_storage'
                'trends:_dmlclean_trends'
                'system:_dmlclean_system'
                'version:_dmlclean_version'
            )

            local subcommand
            read -r subcommand _ <<< "$words[1]"
            _describe -t commands 'command' subcommand_actions && ret=0
            ;;
    esac

    return ret
}

_dmlclean_scan() {
    _arguments "${_arguments_options[@]}" \
        '--mode=[Scan mode: fast, deep, or custom]:MODE:(fast deep custom)' \
        '-m=[Scan mode: fast, deep, or custom]:MODE:(fast deep custom)' \
        '--categories=[Comma-separated list of categories]:CATEGORIES: ' \
        '-c=[Comma-separated list of categories]:CATEGORIES: ' \
        '*--path=[Paths to scan]:PATH:_files -/' \
        '*-p=[Paths to scan]:PATH:_files -/' \
        '--json[Output in JSON format]' \
        '--quiet[Suppress output]' \
        '-q[Suppress output]' \
        '--help[Show help]' \
        && return 0
}

_dmlclean_clean() {
    _arguments "${_arguments_options[@]}" \
        '--mode=[Clean mode: dry-run, trash, or permanent]:MODE:(dry-run trash permanent)' \
        '-m=[Clean mode: dry-run, trash, or permanent]:MODE:(dry-run trash permanent)' \
        '--profile=[Cleaning profile]:PROFILE:(developer designer system-admin gamer minimal)' \
        '-p=[Cleaning profile]:PROFILE:(developer designer system-admin gamer minimal)' \
        '--categories=[Comma-separated list of categories]:CATEGORIES: ' \
        '-c=[Comma-separated list of categories]:CATEGORIES: ' \
        '--min-age=[Only clean files older than N days]:DAYS: ' \
        '--min-size=[Only clean files larger than N MB]:MB: ' \
        '--force[Required for permanent mode]' \
        '-f[Required for permanent mode]' \
        '--yes[Skip confirmation prompts]' \
        '-y[Skip confirmation prompts]' \
        '*--path=[Paths to clean]:PATH:_files -/' \
        '--help[Show help]' \
        && return 0
}

_dmlclean_schedule() {
    local -a subcommands
    subcommands=(
        "list:List scheduled jobs"
        "add:Add new schedule"
        "remove:Remove schedule"
        "enable:Enable schedule"
        "disable:Disable schedule"
        "run:Run schedule immediately"
        "install:Install as native OS task"
        "uninstall:Remove native OS task"
    )

    _arguments "${_arguments_options[@]}" \
        '--help[Show help]' \
        "(- *)":(-: :->subcommands) \
        "(- *):{ _describe 'command' subcommands }" \
        && return 0

    case $state in
        subcommands)
            case $words[1] in
                list)
                    _arguments \
                        '--limit=[Maximum entries]:LIMIT: ' \
                        '--enabled[Only enabled]' \
                        '--disabled[Only disabled]' \
                        && return 0
                    ;;
                add)
                    _arguments \
                        '--name=[Job name]:NAME: ' \
                        '--cron=[Cron expression]:CRON: ' \
                        '--profile=[Profile]:PROFILE:(developer designer system-admin gamer minimal)' \
                        '--mode=[Mode]:MODE:(dry-run trash permanent)' \
                        '--enabled[Enable immediately]' \
                        && return 0
                    ;;
                remove|enable|disable|run)
                    _arguments \
                        '--id=[Job ID]:ID: ' \
                        && return 0
                    ;;
            esac
            ;;
    esac
}

_dmlclean_config() {
    local -a subcommands
    subcommands=(
        "show:Show current configuration"
        "set:Set configuration value"
        "get:Get configuration value"
        "export:Export configuration"
    )

    _arguments "${_arguments_options[@]}" \
        '--help[Show help]' \
        "(- *)":(-: :->subcommands) \
        "(- *):{ _describe 'command' subcommands }" \
        && return 0

    case $state in
        subcommands)
            case $words[1] in
                show)
                    _arguments '--json[JSON output]' && return 0
                    ;;
                get|set)
                    _arguments \
                        '--section=[Config section]:SECTION: ' \
                        '--key=[Config key]:KEY: ' \
                        && return 0
                    ;;
                export)
                    _arguments '--output=[Output file]:FILE:_files' && return 0
                    ;;
            esac
            ;;
    esac
}

_dmlclean_protect() {
    local -a subcommands
    subcommands=(
        "add:Add protected path"
        "remove:Remove protected path"
        "list:List protected paths"
        "check:Check if path is protected"
    )

    _arguments "${_arguments_options[@]}" \
        '--help[Show help]' \
        "(- *)":(-: :->subcommands) \
        "(- *):{ _describe 'command' subcommands }" \
        && return 0

    case $state in
        subcommands)
            case $words[1] in
                add)
                    _arguments \
                        '--description=[Description]:DESC: ' \
                        '--glob[Is glob pattern]' \
                        ':path:_files -/' \
                        && return 0
                    ;;
                remove)
                    _arguments '--id=[Entry ID]:ID: ' && return 0
                    ;;
                check)
                    _arguments ':path:_files -/' && return 0
                    ;;
            esac
            ;;
    esac
}

_dmlclean_history() {
    local -a subcommands
    subcommands=(
        "list:List cleaning history"
        "undo:Undo operation"
        "export:Export history"
        "clear:Clear history"
    )

    _arguments "${_arguments_options[@]}" \
        '--help[Show help]' \
        "(- *)":(-: :->subcommands) \
        "(- *):{ _describe 'command' subcommands }" \
        && return 0

    case $state in
        subcommands)
            case $words[1] in
                list)
                    _arguments \
                        '--limit=[Maximum entries]:LIMIT: ' \
                        '--profile=[Filter by profile]:PROFILE: ' \
                        '--status=[Filter by status]:STATUS:(complete partial failed)' \
                        '--mode=[Filter by mode]:MODE:(dry-run trash permanent)' \
                        && return 0
                    ;;
                undo)
                    _arguments '--id=[Entry ID]:ID: ' && return 0
                    ;;
                export)
                    _arguments '--output=[Output file]:FILE:_files' && return 0
                    ;;
            esac
            ;;
    esac
}

_dmlclean_report() {
    _arguments "${_arguments_options[@]}" \
        '--format=[Output format]:FORMAT:(terminal json csv html)' \
        '--output=[Output file]:FILE:_files' \
        '--days=[Days to include]:DAYS: ' \
        '--profile=[Filter by profile]:PROFILE: ' \
        '--help[Show help]' \
        && return 0
}

_dmlclean_doctor() {
    _arguments "${_arguments_options[@]}" \
        '--json[JSON output]' \
        '--help[Show help]' \
        && return 0
}

_dmlclean_profile() {
    local -a subcommands
    subcommands=(
        "list:List available profiles"
        "show:Show profile details"
    )

    _arguments "${_arguments_options[@]}" \
        '--help[Show help]' \
        "(- *)":(-: :->subcommands) \
        "(- *):{ _describe 'command' subcommands }" \
        && return 0

    case $state in
        subcommands)
            case $words[1] in
                list)
                    _arguments '--json[JSON output]' && return 0
                    ;;
                show)
                    _arguments ':name:(developer designer system-admin gamer minimal)' && return 0
                    ;;
            esac
            ;;
    esac
}

_dmlclean_plugin() {
    local -a subcommands
    subcommands=(
        "list:List available plugins"
        "search:Search plugins"
        "install:Install plugin"
        "remove:Remove plugin"
        "update:Update plugins"
    )

    _arguments "${_arguments_options[@]}" \
        '--help[Show help]' \
        "(- *)":(-: :->subcommands) \
        "(- *):{ _describe 'command' subcommands }" \
        && return 0

    case $state in
        subcommands)
            case $words[1] in
                list)
                    _arguments '--installed[List installed only]' && return 0
                    ;;
                search)
                    _arguments ':query: ' && return 0
                    ;;
                install)
                    _arguments \
                        '--version=[Specific version]:VERSION: ' \
                        '--upgrade[Upgrade if installed]' \
                        ':name: ' \
                        && return 0
                    ;;
                remove)
                    _arguments ':name: ' && return 0
                    ;;
                update)
                    _arguments ':name: ' && return 0
                    ;;
            esac
            ;;
    esac
}

_dmlclean_storage() {
    local -a subcommands
    subcommands=(
        "info:Show storage information"
        "paths:Show storage paths"
        "cleanup:Cleanup storage"
    )

    _arguments "${_arguments_options[@]}" \
        '--help[Show help]' \
        "(- *)":(-: :->subcommands) \
        "(- *):{ _describe 'command' subcommands }" \
        && return 0
}

_dmlclean_trends() {
    _arguments "${_arguments_options[@]}" \
        '--days=[Days to show]:DAYS: ' \
        '--json[JSON output]' \
        '--help[Show help]' \
        && return 0
}

_dmlclean_system() {
    local -a subcommands
    subcommands=(
        "version:Show version info"
        "self-update:Update DMLClean"
        "doctor:System diagnostics"
    )

    _arguments "${_arguments_options[@]}" \
        '--help[Show help]' \
        "(- *)":(-: :->subcommands) \
        "(- *):{ _describe 'command' subcommands }" \
        && return 0

    case $state in
        subcommands)
            case $words[1] in
                self-update)
                    _arguments '--force[Force update]' && return 0
                    ;;
            esac
            ;;
    esac
}

_dmlclean_version() {
    _arguments "${_arguments_options[@]}" \
        '--help[Show help]' \
        && return 0
}

_dmlclean "$@"

# Local Variables:
# mode: Shell-Script
# sh-indentation: 4
# indent-tabs-mode: nil
# sh-basic-offset: 4
# End:
# vim: ft=zsh sw=4 ts=4 et

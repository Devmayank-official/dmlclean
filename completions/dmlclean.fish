# fish completion for dmlclean
# Generated for DMLClean v0.1.0
# Place in: ~/.config/fish/completions/dmlclean.fish

# Main command
complete -c dmlclean -f

# Top-level commands
complete -c dmlclean -n __fish_use_subcommand -a scan -d 'Scan for cleanable files'
complete -c dmlclean -n __fish_use_subcommand -a clean -d 'Execute cleaning operation'
complete -c dmlclean -n __fish_use_subcommand -a schedule -d 'Manage scheduled cleaning'
complete -c dmlclean -n __fish_use_subcommand -a config -d 'Manage configuration'
complete -c dmlclean -n __fish_use_subcommand -a protect -d 'Manage Protected Zone'
complete -c dmlclean -n __fish_use_subcommand -a history -d 'View/undo cleaning history'
complete -c dmlclean -n __fish_use_subcommand -a report -d 'Generate reports'
complete -c dmlclean -n __fish_use_subcommand -a doctor -d 'System diagnostics'
complete -c dmlclean -n __fish_use_subcommand -a profile -d 'Profile management'
complete -c dmlclean -n __fish_use_subcommand -a plugin -d 'Plugin management'
complete -c dmlclean -n __fish_use_subcommand -a storage -d 'Storage management'
complete -c dmlclean -n __fish_use_subcommand -a trends -d 'Disk usage trends'
complete -c dmlclean -n __fish_use_subcommand -a system -d 'System commands'
complete -c dmlclean -n __fish_use_subcommand -a version -d 'Show version'

# Global options
complete -c dmlclean -n __fish_use_subcommand -l help -s h -d 'Show help'
complete -c dmlclean -n __fish_use_subcommand -l version -s v -d 'Show version'
complete -c dmlclean -n __fish_use_subcommand -l verbose -s V -d 'Enable debug logging'
complete -c dmlclean -n __fish_use_subcommand -l quiet -s q -d 'Suppress output'

# Scan command options
complete -c dmlclean -n '__fish_seen_subcommand_from scan' -l mode -s m -d 'Scan mode' -r -f -a "fast\t'Fast scan (default)' deep\t'Deep scan' custom\t'Custom scan'"
complete -c dmlclean -n '__fish_seen_subcommand_from scan' -l categories -s c -d 'Categories to scan'
complete -c dmlclean -n '__fish_seen_subcommand_from scan' -l path -s p -d 'Paths to scan' -r -F
complete -c dmlclean -n '__fish_seen_subcommand_from scan' -l json -d 'JSON output'
complete -c dmlclean -n '__fish_seen_subcommand_from scan' -l quiet -s q -d 'Quiet mode'
complete -c dmlclean -n '__fish_seen_subcommand_from scan' -l help -s h -d 'Show help'

# Clean command options
complete -c dmlclean -n '__fish_seen_subcommand_from clean' -l mode -s m -d 'Clean mode' -r -f -a "dry-run\t'Preview only' trash\t'Move to trash' permanent\t'Permanently delete'"
complete -c dmlclean -n '__fish_seen_subcommand_from clean' -l profile -s p -d 'Cleaning profile' -r -f -a "developer\t'Developer profile' designer\t'Designer profile' system-admin\t'System admin profile' gamer\t'Gamer profile' minimal\t'Minimal profile'"
complete -c dmlclean -n '__fish_seen_subcommand_from clean' -l categories -s c -d 'Categories to clean'
complete -c dmlclean -n '__fish_seen_subcommand_from clean' -l min-age -d 'Minimum file age in days'
complete -c dmlclean -n '__fish_seen_subcommand_from clean' -l min-size -d 'Minimum file size in MB'
complete -c dmlclean -n '__fish_seen_subcommand_from clean' -l force -s f -d 'Force permanent deletion'
complete -c dmlclean -n '__fish_seen_subcommand_from clean' -l yes -s y -d 'Skip confirmation'
complete -c dmlclean -n '__fish_seen_subcommand_from clean' -l path -d 'Paths to clean' -r -F
complete -c dmlclean -n '__fish_seen_subcommand_from clean' -l help -s h -d 'Show help'

# Schedule command options
complete -c dmlclean -n '__fish_seen_subcommand_from schedule' -l help -s h -d 'Show help'
complete -c dmlclean -n '__fish_seen_subcommand_from schedule list' -l limit -d 'Limit results'
complete -c dmlclean -n '__fish_seen_subcommand_from schedule add' -l name -d 'Job name'
complete -c dmlclean -n '__fish_seen_subcommand_from schedule add' -l cron -d 'Cron expression'
complete -c dmlclean -n '__fish_seen_subcommand_from schedule remove' -l id -d 'Job ID'
complete -c dmlclean -n '__fish_seen_subcommand_from schedule enable' -l id -d 'Job ID'
complete -c dmlclean -n '__fish_seen_subcommand_from schedule disable' -l id -d 'Job ID'

# Config command options
complete -c dmlclean -n '__fish_seen_subcommand_from config' -l help -s h -d 'Show help'
complete -c dmlclean -n '__fish_seen_subcommand_from config show' -l json -d 'JSON output'
complete -c dmlclean -n '__fish_seen_subcommand_from config get' -l section -d 'Config section'
complete -c dmlclean -n '__fish_seen_subcommand_from config set' -l section -d 'Config section'
complete -c dmlclean -n '__fish_seen_subcommand_from config export' -l output -d 'Output file' -r -F

# Protect command options
complete -c dmlclean -n '__fish_seen_subcommand_from protect' -l help -s h -d 'Show help'
complete -c dmlclean -n '__fish_seen_subcommand_from protect add' -l description -d 'Description'
complete -c dmlclean -n '__fish_seen_subcommand_from protect add' -l glob -d 'Glob pattern'
complete -c dmlclean -n '__fish_seen_subcommand_from protect remove' -l id -d 'Entry ID'
complete -c dmlclean -n '__fish_seen_subcommand_from protect check' -l path -d 'Path to check' -r -F

# History command options
complete -c dmlclean -n '__fish_seen_subcommand_from history' -l help -s h -d 'Show help'
complete -c dmlclean -n '__fish_seen_subcommand_from history list' -l limit -d 'Limit results'
complete -c dmlclean -n '__fish_seen_subcommand_from history list' -l profile -d 'Filter by profile'
complete -c dmlclean -n '__fish_seen_subcommand_from history undo' -l id -d 'Entry ID'
complete -c dmlclean -n '__fish_seen_subcommand_from history export' -l output -d 'Output file' -r -F

# Profile command options
complete -c dmlclean -n '__fish_seen_subcommand_from profile' -l help -s h -d 'Show help'
complete -c dmlclean -n '__fish_seen_subcommand_from profile list' -l json -d 'JSON output'
complete -c dmlclean -n '__fish_seen_subcommand_from profile show' -l name -d 'Profile name' -r -f -a "developer designer system-admin gamer minimal"

# Plugin command options
complete -c dmlclean -n '__fish_seen_subcommand_from plugin' -l help -s h -d 'Show help'
complete -c dmlclean -n '__fish_seen_subcommand_from plugin list' -l installed -d 'List installed only'
complete -c dmlclean -n '__fish_seen_subcommand_from plugin install' -l version -d 'Specific version'
complete -c dmlclean -n '__fish_seen_subcommand_from plugin install' -l upgrade -d 'Upgrade if installed'
complete -c dmlclean -n '__fish_seen_subcommand_from plugin remove' -l name -d 'Plugin name' -r

# System command options
complete -c dmlclean -n '__fish_seen_subcommand_from system' -l help -s h -d 'Show help'
complete -c dmlclean -n '__fish_seen_subcommand_from system self-update' -l force -d 'Force update'
complete -c dmlclean -n '__fish_seen_subcommand_from system doctor' -l json -d 'JSON output'

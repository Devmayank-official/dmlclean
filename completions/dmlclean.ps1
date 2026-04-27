# PowerShell completion for dmlclean
# Generated for DMLClean v0.1.0
# Place in: $PROFILE or run: . .\dmlclean.ps1

using namespace System.Management.Automation
using namespace System.Management.Automation.Language

Register-ArgumentCompleter -Native -CommandName 'dmlclean' -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)

    $commandElements = $commandAst.CommandElements
    $command = @(
        'dmlclean'
        for ($i = 1; $i -lt $commandElements.Count; $i++) {
            $element = $commandElements[$i]
            if ($null -ne $element) {
                $element.ToString()
            }
        }
    ) -join ';'

    $completions = @(switch ($command) {
        'dmlclean' {
            [CompletionResult]::new('--help', '--help', [CompletionResultType]::ParameterName, 'Show help')
            [CompletionResult]::new('--version', '--version', [CompletionResultType]::ParameterName, 'Show version')
            [CompletionResult]::new('--verbose', '--verbose', [CompletionResultType]::ParameterName, 'Enable debug logging')
            [CompletionResult]::new('--quiet', '--quiet', [CompletionResultType]::ParameterName, 'Suppress output')
            [CompletionResult]::new('scan', 'scan', [CompletionResultType]::ParameterValue, 'Scan for cleanable files')
            [CompletionResult]::new('clean', 'clean', [CompletionResultType]::ParameterValue, 'Execute cleaning operation')
            [CompletionResult]::new('schedule', 'schedule', [CompletionResultType]::ParameterValue, 'Manage scheduled cleaning')
            [CompletionResult]::new('config', 'config', [CompletionResultType]::ParameterValue, 'Manage configuration')
            [CompletionResult]::new('protect', 'protect', [CompletionResultType]::ParameterValue, 'Manage Protected Zone')
            [CompletionResult]::new('history', 'history', [CompletionResultType]::ParameterValue, 'View/undo cleaning history')
            [CompletionResult]::new('report', 'report', [CompletionResultType]::ParameterValue, 'Generate reports')
            [CompletionResult]::new('doctor', 'doctor', [CompletionResultType]::ParameterValue, 'System diagnostics')
            [CompletionResult]::new('profile', 'profile', [CompletionResultType]::ParameterValue, 'Profile management')
            [CompletionResult]::new('plugin', 'plugin', [CompletionResultType]::ParameterValue, 'Plugin management')
            [CompletionResult]::new('storage', 'storage', [CompletionResultType]::ParameterValue, 'Storage management')
            [CompletionResult]::new('trends', 'trends', [CompletionResultType]::ParameterValue, 'Disk usage trends')
            [CompletionResult]::new('system', 'system', [CompletionResultType]::ParameterValue, 'System commands')
            [CompletionResult]::new('version', 'version', [CompletionResultType]::ParameterValue, 'Show version')
        }

        'dmlclean;scan' {
            [CompletionResult]::new('--mode', '--mode', [CompletionResultType]::ParameterName, 'Scan mode')
            [CompletionResult]::new('-m', '-m', [CompletionResultType]::ParameterAlias, 'Scan mode')
            [CompletionResult]::new('--categories', '--categories', [CompletionResultType]::ParameterName, 'Categories to scan')
            [CompletionResult]::new('-c', '-c', [CompletionResultType]::ParameterAlias, 'Categories to scan')
            [CompletionResult]::new('--path', '--path', [CompletionResultType]::ParameterName, 'Paths to scan')
            [CompletionResult]::new('-p', '-p', [CompletionResultType]::ParameterAlias, 'Paths to scan')
            [CompletionResult]::new('--json', '--json', [CompletionResultType]::ParameterName, 'JSON output')
            [CompletionResult]::new('--quiet', '--quiet', [CompletionResultType]::ParameterName, 'Quiet mode')
            [CompletionResult]::new('--help', '--help', [CompletionResultType]::ParameterName, 'Show help')
            [CompletionResult]::new('fast', 'fast', [CompletionResultType]::ParameterValue, 'Fast scan')
            [CompletionResult]::new('deep', 'deep', [CompletionResultType]::ParameterValue, 'Deep scan')
            [CompletionResult]::new('custom', 'custom', [CompletionResultType]::ParameterValue, 'Custom scan')
        }

        'dmlclean;clean' {
            [CompletionResult]::new('--mode', '--mode', [CompletionResultType]::ParameterName, 'Clean mode')
            [CompletionResult]::new('-m', '-m', [CompletionResultType]::ParameterAlias, 'Clean mode')
            [CompletionResult]::new('--profile', '--profile', [CompletionResultType]::ParameterName, 'Cleaning profile')
            [CompletionResult]::new('-p', '-p', [CompletionResultType]::ParameterAlias, 'Cleaning profile')
            [CompletionResult]::new('--categories', '--categories', [CompletionResultType]::ParameterName, 'Categories to clean')
            [CompletionResult]::new('--min-age', '--min-age', [CompletionResultType]::ParameterName, 'Minimum file age')
            [CompletionResult]::new('--min-size', '--min-size', [CompletionResultType]::ParameterName, 'Minimum file size')
            [CompletionResult]::new('--force', '--force', [CompletionResultType]::ParameterName, 'Force permanent deletion')
            [CompletionResult]::new('-f', '-f', [CompletionResultType]::ParameterAlias, 'Force permanent deletion')
            [CompletionResult]::new('--yes', '--yes', [CompletionResultType]::ParameterName, 'Skip confirmation')
            [CompletionResult]::new('-y', '-y', [CompletionResultType]::ParameterAlias, 'Skip confirmation')
            [CompletionResult]::new('--path', '--path', [CompletionResultType]::ParameterName, 'Paths to clean')
            [CompletionResult]::new('--help', '--help', [CompletionResultType]::ParameterName, 'Show help')
            [CompletionResult]::new('dry-run', 'dry-run', [CompletionResultType]::ParameterValue, 'Preview only')
            [CompletionResult]::new('trash', 'trash', [CompletionResultType]::ParameterValue, 'Move to trash')
            [CompletionResult]::new('permanent', 'permanent', [CompletionResultType]::ParameterValue, 'Permanently delete')
            [CompletionResult]::new('developer', 'developer', [CompletionResultType]::ParameterValue, 'Developer profile')
            [CompletionResult]::new('designer', 'designer', [CompletionResultType]::ParameterValue, 'Designer profile')
            [CompletionResult]::new('system-admin', 'system-admin', [CompletionResultType]::ParameterValue, 'System admin profile')
            [CompletionResult]::new('gamer', 'gamer', [CompletionResultType]::ParameterValue, 'Gamer profile')
            [CompletionResult]::new('minimal', 'minimal', [CompletionResultType]::ParameterValue, 'Minimal profile')
        }

        'dmlclean;schedule' {
            [CompletionResult]::new('list', 'list', [CompletionResultType]::ParameterValue, 'List schedules')
            [CompletionResult]::new('add', 'add', [CompletionResultType]::ParameterValue, 'Add schedule')
            [CompletionResult]::new('remove', 'remove', [CompletionResultType]::ParameterValue, 'Remove schedule')
            [CompletionResult]::new('enable', 'enable', [CompletionResultType]::ParameterValue, 'Enable schedule')
            [CompletionResult]::new('disable', 'disable', [CompletionResultType]::ParameterValue, 'Disable schedule')
            [CompletionResult]::new('run', 'run', [CompletionResultType]::ParameterValue, 'Run schedule now')
            [CompletionResult]::new('install', 'install', [CompletionResultType]::ParameterValue, 'Install native task')
            [CompletionResult]::new('uninstall', 'uninstall', [CompletionResultType]::ParameterValue, 'Uninstall native task')
            [CompletionResult]::new('--help', '--help', [CompletionResultType]::ParameterName, 'Show help')
        }

        'dmlclean;config' {
            [CompletionResult]::new('show', 'show', [CompletionResultType]::ParameterValue, 'Show config')
            [CompletionResult]::new('set', 'set', [CompletionResultType]::ParameterValue, 'Set config value')
            [CompletionResult]::new('get', 'get', [CompletionResultType]::ParameterValue, 'Get config value')
            [CompletionResult]::new('export', 'export', [CompletionResultType]::ParameterValue, 'Export config')
            [CompletionResult]::new('--help', '--help', [CompletionResultType]::ParameterName, 'Show help')
        }

        'dmlclean;protect' {
            [CompletionResult]::new('add', 'add', [CompletionResultType]::ParameterValue, 'Add protected path')
            [CompletionResult]::new('remove', 'remove', [CompletionResultType]::ParameterValue, 'Remove protected path')
            [CompletionResult]::new('list', 'list', [CompletionResultType]::ParameterValue, 'List protected paths')
            [CompletionResult]::new('check', 'check', [CompletionResultType]::ParameterValue, 'Check if path protected')
            [CompletionResult]::new('--help', '--help', [CompletionResultType]::ParameterName, 'Show help')
        }

        'dmlclean;history' {
            [CompletionResult]::new('list', 'list', [CompletionResultType]::ParameterValue, 'List history')
            [CompletionResult]::new('undo', 'undo', [CompletionResultType]::ParameterValue, 'Undo operation')
            [CompletionResult]::new('export', 'export', [CompletionResultType]::ParameterValue, 'Export history')
            [CompletionResult]::new('clear', 'clear', [CompletionResultType]::ParameterValue, 'Clear history')
            [CompletionResult]::new('--help', '--help', [CompletionResultType]::ParameterName, 'Show help')
        }

        'dmlclean;profile' {
            [CompletionResult]::new('list', 'list', [CompletionResultType]::ParameterValue, 'List profiles')
            [CompletionResult]::new('show', 'show', [CompletionResultType]::ParameterValue, 'Show profile')
            [CompletionResult]::new('--help', '--help', [CompletionResultType]::ParameterName, 'Show help')
        }

        'dmlclean;plugin' {
            [CompletionResult]::new('list', 'list', [CompletionResultType]::ParameterValue, 'List plugins')
            [CompletionResult]::new('search', 'search', [CompletionResultType]::ParameterValue, 'Search plugins')
            [CompletionResult]::new('install', 'install', [CompletionResultType]::ParameterValue, 'Install plugin')
            [CompletionResult]::new('remove', 'remove', [CompletionResultType]::ParameterValue, 'Remove plugin')
            [CompletionResult]::new('update', 'update', [CompletionResultType]::ParameterValue, 'Update plugins')
            [CompletionResult]::new('--help', '--help', [CompletionResultType]::ParameterName, 'Show help')
        }

        'dmlclean;system' {
            [CompletionResult]::new('version', 'version', [CompletionResultType]::ParameterValue, 'Show version')
            [CompletionResult]::new('self-update', 'self-update', [CompletionResultType]::ParameterValue, 'Self-update')
            [CompletionResult]::new('doctor', 'doctor', [CompletionResultType]::ParameterValue, 'System diagnostics')
            [CompletionResult]::new('--help', '--help', [CompletionResultType]::ParameterName, 'Show help')
        }
    })

    $completions.Where{ $_.CompletionText -like "$wordToComplete*" } |
        Sort-Object -Property ListItemText
}

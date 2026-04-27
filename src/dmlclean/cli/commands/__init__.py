"""
CLI commands package for DMLClean.

All CLI command modules are organized in this subpackage.
"""

from dmlclean.cli.commands.clean import app as clean_app
from dmlclean.cli.commands.config import app as config_app
from dmlclean.cli.commands.doctor import app as doctor_app
from dmlclean.cli.commands.history import app as history_app
from dmlclean.cli.commands.notification import app as notification_app
from dmlclean.cli.commands.plugin_cmd import app as plugin_app
from dmlclean.cli.commands.profile import app as profile_app
from dmlclean.cli.commands.protect import app as protect_app
from dmlclean.cli.commands.report import app as report_app
from dmlclean.cli.commands.scan import app as scan_app
from dmlclean.cli.commands.schedule import app as schedule_app
from dmlclean.cli.commands.storage_cmd import app as storage_app
from dmlclean.cli.commands.system import app as system_app
from dmlclean.cli.commands.trends import app as trends_app

__all__ = [
    "clean_app",
    "config_app",
    "doctor_app",
    "history_app",
    "notification_app",
    "plugin_app",
    "profile_app",
    "protect_app",
    "report_app",
    "scan_app",
    "schedule_app",
    "storage_app",
    "system_app",
    "trends_app",
]

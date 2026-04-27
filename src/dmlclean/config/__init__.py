"""
Configuration management for DMLClean.

This package provides:
- TOML-based configuration loading and validation
- Environment variable overrides
- Named profiles (developer, designer, system-admin)
- Default values for all configuration options
"""

from dmlclean.config.defaults import get_defaults
from dmlclean.config.loader import ConfigLoader
from dmlclean.config.profiles import Profile, get_profile
from dmlclean.config.schema import ConfigSchema

__all__ = [
    "ConfigLoader",
    "ConfigSchema",
    "Profile",
    "get_defaults",
    "get_profile",
]

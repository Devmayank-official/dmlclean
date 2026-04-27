"""
Configuration loader for DMLClean.

Handles loading, merging, and validating configuration from:
1. Default values (lowest priority)
2. TOML config file
3. Environment variables (highest priority)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import tomli_w
from loguru import logger

from dmlclean.config.defaults import get_defaults
from dmlclean.config.schema import ConfigSchema


class ConfigLoader:
    """
    Configuration loader with layered merging and validation.

    The configuration is loaded in layers:
    1. Default values from defaults.py
    2. TOML file from platform-specific location
    3. Environment variables (DMLCLEAN_<SECTION>_<KEY>)

    Attributes:
        config_path: Path to the configuration file.
        schema: Validated Pydantic schema instance.
    """

    def __init__(self, config_path: Path | str | None = None) -> None:
        """
        Initialize the configuration loader.

        Args:
            config_path: Optional path to config file. If None, uses
                platform-specific default location.
        """
        if config_path is None:
            self.config_path = self._get_default_config_path()
        else:
            self.config_path = Path(config_path)

        self._raw_config: dict[str, Any] = {}
        self._schema: ConfigSchema | None = None
        logger.debug(f"ConfigLoader initialized with path: {self.config_path}")

    @staticmethod
    def _get_default_config_path() -> Path:
        """
        Get the platform-specific default config path.

        Uses unified storage paths for cross-platform compatibility.

        Returns:
            Path: Default configuration file path.
        """
        # Use unified storage path: ~/DML Labs/DML Clean/config/
        from dmlclean.storage.paths import get_config_dir

        config_dir = get_config_dir()
        config_file = config_dir / "config.toml"
        logger.debug(f"Default config path: {config_file}")
        return config_file

    def load(self) -> ConfigLoader:
        """
        Load configuration from all sources and merge.

        Returns:
            ConfigLoader: Self for method chaining.

        Raises:
            FileNotFoundError: If config file doesn't exist and isn't created.
            ValueError: If configuration is invalid.
        """
        # Layer 1: Defaults
        self._raw_config = get_defaults()
        logger.debug("Loaded default configuration")

        # Layer 2: TOML file (if exists)
        if self.config_path.exists():
            file_config = self._load_toml()
            self._raw_config = self._deep_merge(self._raw_config, file_config)
            logger.info(f"Loaded configuration from: {self.config_path}")
        else:
            logger.debug(f"Config file not found, will use defaults: {self.config_path}")

        # Layer 3: Environment variables
        env_config = self._load_env_vars()
        if env_config:
            self._raw_config = self._deep_merge(self._raw_config, env_config)
            logger.debug(f"Merged {len(env_config)} environment variable overrides")

        # Validate and create schema
        self._schema = ConfigSchema(**self._raw_config)
        logger.info("Configuration validated successfully")

        return self

    def _load_toml(self) -> dict[str, Any]:
        """
        Load configuration from TOML file.

        Returns:
            dict[str, Any]: Parsed TOML configuration.

        Raises:
            ValueError: If TOML parsing fails.
        """
        # Use stdlib tomllib for Python 3.11+
        import tomllib

        try:
            with self.config_path.open("rb") as f:
                data = tomllib.load(f)
            logger.debug(f"Successfully parsed TOML from {self.config_path}")
            return data
        except tomllib.TOMLDecodeError as e:
            raise ValueError(f"Invalid TOML in {self.config_path}: {e}") from e
        except OSError as e:
            raise ValueError(f"Cannot read {self.config_path}: {e}") from e

    def _load_env_vars(self) -> dict[str, Any]:
        """
        Load configuration from environment variables.

        Environment variables follow the pattern:
        DMLCLEAN_<SECTION>_<KEY> = value

        Examples:
            DMLCLEAN_GENERAL_DEFAULT_SCAN_MODE=deep
            DMLCLEAN_SCANNER_FOLLOW_SYMLINKS=true

        Returns:
            dict[str, Any]: Configuration from environment variables.
        """
        env_config: dict[str, Any] = {}
        prefix = "DMLCLEAN_"

        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue

            # Remove prefix and parse
            remainder = key[len(prefix) :]
            parts = remainder.split("_", 1)

            if len(parts) != 2:
                continue

            section, config_key = parts
            section_lower = section.lower()

            # Convert value to appropriate type
            typed_value = self._parse_env_value(value)

            # Build nested dict structure
            if section_lower not in env_config:
                env_config[section_lower] = {}
            env_config[section_lower][config_key.lower()] = typed_value

        return env_config

    @staticmethod
    def _parse_env_value(value: str) -> Any:
        """
        Parse an environment variable value to appropriate Python type.

        Args:
            value: Raw string value from environment.

        Returns:
            Any: Parsed value (bool, int, float, or str).
        """
        # Boolean
        if value.lower() in ("true", "yes", "1", "on"):
            return True
        if value.lower() in ("false", "no", "0", "off"):
            return False

        # Integer
        try:
            return int(value)
        except ValueError:
            pass

        # Float
        try:
            return float(value)
        except ValueError:
            pass

        # String (default)
        return value

    @staticmethod
    def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """
        Deep merge two dictionaries.

        Args:
            base: Base dictionary.
            override: Dictionary to merge on top of base.

        Returns:
            dict[str, Any]: Merged dictionary.
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigLoader._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def save(self) -> None:
        """
        Save current configuration to the config file.

        Creates parent directories if they don't exist.
        Sets file permissions to 0o600 on Unix systems.
        """
        if self._schema is None:
            raise ValueError("No configuration loaded. Call load() first.")

        # Ensure parent directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write TOML
        with self.config_path.open("wb") as f:
            tomli_w.dump(self._raw_config, f)

        # Set permissions on Unix
        if os.name != "nt":
            self.config_path.chmod(0o600)

        logger.info(f"Configuration saved to: {self.config_path}")

    @property
    def schema(self) -> ConfigSchema:
        """
        Get the validated configuration schema.

        Returns:
            ConfigSchema: Validated Pydantic schema instance.

        Raises:
            ValueError: If configuration hasn't been loaded.
        """
        if self._schema is None:
            raise ValueError("No configuration loaded. Call load() first.")
        return self._schema

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by section and key.

        Args:
            section: Configuration section name.
            key: Configuration key within the section.
            default: Default value if key doesn't exist.

        Returns:
            Any: Configuration value or default.
        """
        if self._schema is None:
            return default

        try:
            section_obj = getattr(self._schema, section)
            return getattr(section_obj, key, default)
        except AttributeError:
            return default

    def set(self, section: str, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            section: Configuration section name.
            key: Configuration key within the section.
            value: Value to set.

        Raises:
            ValueError: If configuration hasn't been loaded or section/key invalid.
        """
        if self._schema is None:
            raise ValueError("No configuration loaded. Call load() first.")

        # Update raw config
        if section not in self._raw_config:
            self._raw_config[section] = {}
        self._raw_config[section][key] = value

        # Re-validate schema
        self._schema = ConfigSchema(**self._raw_config)
        logger.debug(f"Set config: {section}.{key} = {value}")

    def to_dict(self) -> dict[str, Any]:
        """
        Get the full configuration as a dictionary.

        Returns:
            dict[str, Any]: Configuration dictionary.
        """
        if self._schema is None:
            return get_defaults()
        return self._schema.to_dict()

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate the current configuration.

        Returns:
            tuple[bool, list[str]]: (is_valid, list of error messages)
        """
        if self._schema is None:
            try:
                self._schema = ConfigSchema(**self._raw_config)
                return True, []
            except Exception as e:
                return False, [str(e)]

        # Schema is already valid if we got here
        return True, []

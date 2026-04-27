"""
Unit tests for DMLClean configuration system.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from dmlclean.config.loader import ConfigLoader
from dmlclean.config.schema import CleanMode, ConfigSchema, ScanMode


class TestConfigSchema:
    """Tests for ConfigSchema validation."""

    def test_default_schema(self) -> None:
        """Test default schema creation."""
        schema = ConfigSchema()
        assert schema.general.default_scan_mode == ScanMode.FAST
        assert schema.general.default_clean_mode == CleanMode.DRY_RUN

    def test_schema_with_custom_values(self) -> None:
        """Test schema with custom values."""
        schema = ConfigSchema(
            general={
                "default_scan_mode": "deep",
                "default_clean_mode": "trash",
            }
        )
        assert schema.general.default_scan_mode == ScanMode.DEEP
        assert schema.general.default_clean_mode == CleanMode.TRASH

    def test_invalid_scan_mode(self) -> None:
        """Test that invalid scan mode raises error."""
        with pytest.raises(ValueError):
            ConfigSchema(general={"default_scan_mode": "invalid"})


class TestConfigLoader:
    """Tests for ConfigLoader."""

    def test_load_defaults(self, fake_fs: FakeFilesystem) -> None:
        """Test loading default configuration."""
        loader = ConfigLoader()
        loader.load()

        assert loader.get("general", "default_scan_mode") == "fast"
        assert loader.get("scanner", "follow_symlinks") is False

    def test_load_from_file(self, fake_fs: FakeFilesystem, config_path: Path) -> None:
        """Test loading configuration from TOML file."""
        import io

        import tomli_w

        config_data = {
            "general": {
                "default_scan_mode": "deep",
            },
            "scanner": {
                "follow_symlinks": True,
            },
        }

        # Write TOML file properly (tomli_w.dump needs binary mode)
        output = io.BytesIO()
        tomli_w.dump(config_data, output)
        fake_fs.create_file(config_path, contents=output.getvalue().decode("utf-8"))

        loader = ConfigLoader(config_path=config_path)
        loader.load()

        assert loader.get("general", "default_scan_mode") == "deep"
        assert loader.get("scanner", "follow_symlinks") is True

    def test_env_var_override(
        self, fake_fs: FakeFilesystem, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test environment variable overrides."""
        monkeypatch.setenv("DMLCLEAN_GENERAL_DEFAULT_SCAN_MODE", "deep")

        loader = ConfigLoader()
        loader.load()

        # Environment variables should override defaults
        assert loader.get("general", "default_scan_mode") == "deep"

    def test_save_config(self, fake_fs: FakeFilesystem, config_path: Path) -> None:
        """Test saving configuration to file."""
        import tomllib

        loader = ConfigLoader(config_path=config_path)
        loader.load()
        loader.set("general", "default_scan_mode", "deep")
        loader.save()

        # Verify file was created
        assert config_path.exists()

        # Verify content by reading and parsing
        with config_path.open("rb") as f:
            saved_data = tomllib.load(f)

        assert saved_data["general"]["default_scan_mode"] == "deep"

    def test_validate_config(self, fake_fs: FakeFilesystem) -> None:
        """Test configuration validation."""
        loader = ConfigLoader()
        loader.load()

        is_valid, errors = loader.validate()
        assert is_valid
        assert len(errors) == 0

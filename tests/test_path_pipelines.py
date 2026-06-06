"""Tests for _resolve_pipeline_path in main.py."""
from __future__ import annotations

import os
import tempfile

import pytest

from ikctl.config.exceptions import ConfigError
from ikctl.main import _resolve_pipeline_path


class TestResolvePipelinePath:
    """Tests for the _resolve_pipeline_path helper."""

    def test_resolve_absolute_path_directly(self):
        """An existing file path is returned unchanged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline_file = os.path.join(tmpdir, "my-pipeline.yaml")
            with open(pipeline_file, "w", encoding="utf-8") as f:
                f.write("name: test\nsteps: []\n")

            result = _resolve_pipeline_path(pipeline_file, None)
            assert result == pipeline_file

    def test_resolve_by_name_with_path_pipelines(self):
        """A pipeline name without extension is resolved via path_pipelines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline_file = os.path.join(tmpdir, "install-docker.yaml")
            with open(pipeline_file, "w", encoding="utf-8") as f:
                f.write("name: install-docker\nsteps: []\n")

            result = _resolve_pipeline_path("install-docker", tmpdir)
            assert result == pipeline_file

    def test_resolve_by_name_with_yaml_extension(self):
        """A pipeline name with .yaml extension is resolved via path_pipelines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline_file = os.path.join(tmpdir, "install-docker.yaml")
            with open(pipeline_file, "w", encoding="utf-8") as f:
                f.write("name: install-docker\nsteps: []\n")

            result = _resolve_pipeline_path("install-docker.yaml", tmpdir)
            assert result == pipeline_file

    def test_resolve_raises_when_not_found(self):
        """Raises ConfigError when neither a file path nor path_pipelines resolves."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ConfigError) as exc_info:
                _resolve_pipeline_path("nonexistent-pipeline", tmpdir)

            assert "nonexistent-pipeline" in str(exc_info.value)
            assert "path_pipelines" in str(exc_info.value)

    def test_resolve_raises_when_path_pipelines_none(self):
        """Raises ConfigError when path_pipelines is None and name is not a file."""
        with pytest.raises(ConfigError) as exc_info:
            _resolve_pipeline_path("install-docker", None)

        assert "install-docker" in str(exc_info.value)
        assert "path_pipelines" in str(exc_info.value)

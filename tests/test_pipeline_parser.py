"""Tests for ikctl.orchestration.parser."""
from __future__ import annotations

import textwrap

import pytest

from ikctl.exceptions import ConfigError
from ikctl.orchestration.parser import PipelineParser, PipelineDef


@pytest.fixture
def parser() -> PipelineParser:
    return PipelineParser()


@pytest.fixture
def valid_yaml(tmp_path) -> str:
    content = textwrap.dedent("""\
        name: test-pipeline
        steps:
          - id: step1
            kit: packages
            servers: all-nodes
            sudo: true
            params:
              - curl
              - wget
          - id: step2
            kit: docker
            servers: all-nodes
            needs:
              - step1
    """)
    path = tmp_path / "pipeline.yaml"
    path.write_text(content, encoding="utf-8")
    return str(path)


def test_parse_valid_yaml(parser, valid_yaml):
    result = parser.parse(valid_yaml)
    assert isinstance(result, PipelineDef)
    assert result.name == "test-pipeline"
    assert len(result.steps) == 2


def test_parse_first_step_fields(parser, valid_yaml):
    result = parser.parse(valid_yaml)
    step1 = result.steps[0]
    assert step1.id == "step1"
    assert step1.kit == "packages"
    assert step1.servers == "all-nodes"
    assert step1.sudo is True
    assert step1.params == ["curl", "wget"]
    assert step1.needs == []


def test_parse_second_step_has_needs(parser, valid_yaml):
    result = parser.parse(valid_yaml)
    step2 = result.steps[1]
    assert step2.needs == ["step1"]
    assert step2.sudo is False
    assert step2.params == []


def test_parse_step_defaults(tmp_path, parser):
    content = textwrap.dedent("""\
        name: minimal
        steps:
          - id: only-step
            kit: mykut
            servers: myservers
    """)
    path = tmp_path / "minimal.yaml"
    path.write_text(content, encoding="utf-8")
    result = parser.parse(str(path))
    step = result.steps[0]
    assert step.sudo is False
    assert step.params == []
    assert step.needs == []


def test_parse_missing_name_raises(tmp_path, parser):
    content = textwrap.dedent("""\
        steps:
          - id: step1
            kit: k
            servers: s
    """)
    path = tmp_path / "no_name.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ConfigError, match="missing required field: name"):
        parser.parse(str(path))


def test_parse_missing_steps_raises(tmp_path, parser):
    content = "name: mypipeline\n"
    path = tmp_path / "no_steps.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ConfigError, match="missing required field: steps"):
        parser.parse(str(path))


def test_parse_step_missing_id_raises(tmp_path, parser):
    content = textwrap.dedent("""\
        name: mypipeline
        steps:
          - kit: k
            servers: s
    """)
    path = tmp_path / "no_id.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ConfigError, match="missing required field: id"):
        parser.parse(str(path))


def test_parse_step_missing_kit_raises(tmp_path, parser):
    content = textwrap.dedent("""\
        name: mypipeline
        steps:
          - id: step1
            servers: s
    """)
    path = tmp_path / "no_kit.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ConfigError, match="missing required field: kit"):
        parser.parse(str(path))


def test_parse_step_missing_servers_raises(tmp_path, parser):
    content = textwrap.dedent("""\
        name: mypipeline
        steps:
          - id: step1
            kit: k
    """)
    path = tmp_path / "no_servers.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ConfigError, match="missing required field: servers"):
        parser.parse(str(path))


def test_parse_invalid_yaml_raises(tmp_path, parser):
    content = "name: [\nbad yaml"
    path = tmp_path / "bad.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ConfigError, match="Invalid YAML"):
        parser.parse(str(path))


def test_parse_file_not_found_raises(parser):
    with pytest.raises(ConfigError, match="not found"):
        parser.parse("/nonexistent/path/pipeline.yaml")


def test_parse_non_mapping_raises(tmp_path, parser):
    content = "- just a list\n"
    path = tmp_path / "list.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ConfigError, match="must be a YAML mapping"):
        parser.parse(str(path))

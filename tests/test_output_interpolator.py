"""Tests for ikctl.orchestration.interpolator."""
from __future__ import annotations

import pytest

from ikctl.config.exceptions import ConfigError
from ikctl.orchestration.interpolator import OutputInterpolator


@pytest.fixture
def interpolator() -> OutputInterpolator:
    return OutputInterpolator()


# --- extract() tests ---

def test_extract_simple_kv(interpolator):
    stdout = "KEY=value\n"
    result = interpolator.extract(stdout)
    assert result == {"KEY": "value"}


def test_extract_multiple_kv(interpolator):
    stdout = "JOIN_TOKEN=abc123\nJOIN_ENDPOINT=10.0.0.1:6443\n"
    result = interpolator.extract(stdout)
    assert result == {"JOIN_TOKEN": "abc123", "JOIN_ENDPOINT": "10.0.0.1:6443"}


def test_extract_ignores_non_kv_lines(interpolator):
    stdout = "This is normal output\nKEY=val\nSome other line\n"
    result = interpolator.extract(stdout)
    assert result == {"KEY": "val"}


def test_extract_empty_value(interpolator):
    stdout = "EMPTY=\n"
    result = interpolator.extract(stdout)
    assert result == {"EMPTY": ""}


def test_extract_value_with_equals(interpolator):
    stdout = "URL=http://example.com/?a=b\n"
    result = interpolator.extract(stdout)
    assert result == {"URL": "http://example.com/?a=b"}


def test_extract_ignores_line_starting_with_number(interpolator):
    stdout = "1KEY=val\n"
    result = interpolator.extract(stdout)
    assert result == {}


def test_extract_empty_stdout(interpolator):
    result = interpolator.extract("")
    assert result == {}


def test_extract_underscore_in_key(interpolator):
    stdout = "MY_LONG_KEY=some_value\n"
    result = interpolator.extract(stdout)
    assert result == {"MY_LONG_KEY": "some_value"}


# --- interpolate() tests ---

def test_interpolate_single_reference(interpolator):
    step_outputs = {"init-master": {"JOIN_TOKEN": "secret123"}}
    params = ["{{ steps.init-master.JOIN_TOKEN }}"]
    result = interpolator.interpolate(params, step_outputs)
    assert result == ["secret123"]


def test_interpolate_multiple_references_in_one_param(interpolator):
    step_outputs = {"s1": {"A": "hello", "B": "world"}}
    params = ["{{ steps.s1.A }}-{{ steps.s1.B }}"]
    result = interpolator.interpolate(params, step_outputs)
    assert result == ["hello-world"]


def test_interpolate_no_references(interpolator):
    params = ["--flag", "--option=value"]
    result = interpolator.interpolate(params, {})
    assert result == ["--flag", "--option=value"]


def test_interpolate_multiple_params(interpolator):
    step_outputs = {"step1": {"TOKEN": "abc", "ENDPOINT": "1.2.3.4:6443"}}
    params = ["{{ steps.step1.TOKEN }}", "{{ steps.step1.ENDPOINT }}"]
    result = interpolator.interpolate(params, step_outputs)
    assert result == ["abc", "1.2.3.4:6443"]


def test_interpolate_unknown_step_raises(interpolator):
    step_outputs = {}
    params = ["{{ steps.nonexistent.KEY }}"]
    with pytest.raises(ConfigError, match="unknown step"):
        interpolator.interpolate(params, step_outputs)


def test_interpolate_unknown_key_raises(interpolator):
    step_outputs = {"step1": {"OTHER": "val"}}
    params = ["{{ steps.step1.MISSING_KEY }}"]
    with pytest.raises(ConfigError, match="no output key"):
        interpolator.interpolate(params, step_outputs)


def test_interpolate_empty_params(interpolator):
    result = interpolator.interpolate([], {"step1": {"K": "v"}})
    assert result == []


def test_interpolate_spaces_in_template(interpolator):
    step_outputs = {"s": {"K": "v"}}
    params = ["{{  steps.s.K  }}"]
    result = interpolator.interpolate(params, step_outputs)
    assert result == ["v"]


# --- pipeline_params tests ---

def test_interpolate_params_key(interpolator):
    """{{ params.TOKEN }} is resolved when pipeline_params contains TOKEN."""
    params = ["{{ params.TOKEN }}"]
    result = interpolator.interpolate(params, {}, pipeline_params={"TOKEN": "abc"})
    assert result == ["abc"]


def test_interpolate_params_key_missing(interpolator):
    """{{ params.TOKEN }} raises ConfigError when TOKEN is not in pipeline_params."""
    params = ["{{ params.TOKEN }}"]
    with pytest.raises(ConfigError, match="TOKEN"):
        interpolator.interpolate(params, {}, pipeline_params={})


def test_interpolate_mixed_steps_and_params(interpolator):
    """{{ steps.init.KEY }} and {{ params.ENV }} in the same step are both resolved."""
    step_outputs = {"init": {"KEY": "step-value"}}
    params = ["{{ steps.init.KEY }}", "{{ params.ENV }}"]
    result = interpolator.interpolate(params, step_outputs, pipeline_params={"ENV": "production"})
    assert result == ["step-value", "production"]


def test_interpolate_params_none_raises_on_reference(interpolator):
    """{{ params.KEY }} raises ConfigError when pipeline_params is None."""
    params = ["{{ params.KEY }}"]
    with pytest.raises(ConfigError, match="KEY"):
        interpolator.interpolate(params, {}, pipeline_params=None)

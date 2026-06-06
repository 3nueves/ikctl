"""Tests for ikctl.orchestration.dag."""
from __future__ import annotations

import pytest

from ikctl.config.exceptions import ConfigError
from ikctl.orchestration.dag import DAGResolver
from ikctl.orchestration.parser import StepDef


def make_step(step_id: str, needs: list[str] | None = None) -> StepDef:
    return StepDef(id=step_id, kit="k", servers="s", needs=needs or [])


@pytest.fixture
def resolver() -> DAGResolver:
    return DAGResolver()


def test_no_dependencies_produces_single_wave(resolver):
    steps = [make_step("a"), make_step("b"), make_step("c")]
    waves = resolver.resolve(steps)
    assert len(waves) == 1
    assert {s.id for s in waves[0]} == {"a", "b", "c"}


def test_chain_produces_n_waves(resolver):
    steps = [
        make_step("a"),
        make_step("b", needs=["a"]),
        make_step("c", needs=["b"]),
    ]
    waves = resolver.resolve(steps)
    assert len(waves) == 3
    assert [s.id for s in waves[0]] == ["a"]
    assert [s.id for s in waves[1]] == ["b"]
    assert [s.id for s in waves[2]] == ["c"]


def test_parallel_steps_in_same_wave(resolver):
    steps = [
        make_step("a"),
        make_step("b"),
        make_step("c", needs=["a", "b"]),
    ]
    waves = resolver.resolve(steps)
    assert len(waves) == 2
    assert {s.id for s in waves[0]} == {"a", "b"}
    assert {s.id for s in waves[1]} == {"c"}


def test_diamond_dag(resolver):
    # a -> b, a -> c, b -> d, c -> d
    steps = [
        make_step("a"),
        make_step("b", needs=["a"]),
        make_step("c", needs=["a"]),
        make_step("d", needs=["b", "c"]),
    ]
    waves = resolver.resolve(steps)
    assert len(waves) == 3
    assert {s.id for s in waves[0]} == {"a"}
    assert {s.id for s in waves[1]} == {"b", "c"}
    assert {s.id for s in waves[2]} == {"d"}


def test_single_step_no_deps(resolver):
    steps = [make_step("only")]
    waves = resolver.resolve(steps)
    assert len(waves) == 1
    assert waves[0][0].id == "only"


def test_cycle_raises_config_error(resolver):
    steps = [
        make_step("a", needs=["b"]),
        make_step("b", needs=["a"]),
    ]
    with pytest.raises(ConfigError, match="cycle"):
        resolver.resolve(steps)


def test_self_cycle_raises_config_error(resolver):
    steps = [make_step("a", needs=["a"])]
    with pytest.raises(ConfigError):
        resolver.resolve(steps)


def test_unknown_need_raises_config_error(resolver):
    steps = [make_step("a", needs=["nonexistent"])]
    with pytest.raises(ConfigError, match="unknown dependency"):
        resolver.resolve(steps)


def test_three_step_cycle_raises(resolver):
    steps = [
        make_step("a", needs=["c"]),
        make_step("b", needs=["a"]),
        make_step("c", needs=["b"]),
    ]
    with pytest.raises(ConfigError, match="cycle"):
        resolver.resolve(steps)


def test_empty_steps_returns_empty_waves(resolver):
    waves = resolver.resolve([])
    assert waves == []


def test_mixed_deps_correct_waves(resolver):
    # step1 (no deps), step2 (needs step1), step3 (no deps), step4 (needs step2, step3)
    steps = [
        make_step("step1"),
        make_step("step2", needs=["step1"]),
        make_step("step3"),
        make_step("step4", needs=["step2", "step3"]),
    ]
    waves = resolver.resolve(steps)
    assert len(waves) == 3
    assert {s.id for s in waves[0]} == {"step1", "step3"}
    assert {s.id for s in waves[1]} == {"step2"}
    assert {s.id for s in waves[2]} == {"step4"}

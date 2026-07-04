"""Tests for ikctl.orchestration.runner."""
from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import pytest

from ikctl.config.models import IkctlConfig, Context, KitPipeline, ServerGroup
from ikctl.orchestration.parser import PipelineDef, StepDef
from ikctl.orchestration.runner import OrchestrationRunner, StepResult
from ikctl.runner.base import RunResult


def make_context(name: str = "default") -> Context:
    return Context(
        name=name,
        path_kits="/kits",
        path_servers="/servers",
        path_secrets="/secrets",
        mode="remote",
    )


def make_ikctl_config() -> IkctlConfig:
    ctx = make_context()
    return IkctlConfig(context="default", contexts={"default": ctx})


def make_step(step_id: str, kit: str = "mykut", servers: str = "myservers", needs: list[str] | None = None) -> StepDef:
    return StepDef(id=step_id, kit=kit, servers=servers, needs=needs or [])


def make_pipeline(*steps: StepDef) -> PipelineDef:
    return PipelineDef(name="test-pipeline", steps=list(steps))


def make_base_options() -> argparse.Namespace:
    return argparse.Namespace(dry_run=False, parallel_workers=1, mode="remote")


def fake_kit() -> KitPipeline:
    return KitPipeline(uploads=[], pipeline=["/kits/mykut/install.sh"])


def fake_servers() -> ServerGroup:
    return ServerGroup(user="root", port=22, hosts=["localhost"])


@pytest.fixture
def config() -> IkctlConfig:
    return make_ikctl_config()


@pytest.fixture
def connection_factory():
    return MagicMock()


def _make_runner(config, connection_factory):
    return OrchestrationRunner(
        config=config,
        connection_factory=connection_factory,
        max_workers=1,
        mode="remote",
        timeout_exec=30.0,
    )


class TestStepResultDataclass:
    def test_default_outputs_is_empty_dict(self):
        r = StepResult(id="x", status="ok")
        assert r.outputs == {}
        assert r.stdout == ""
        assert r.stderr == ""


class TestOrchestrationRunnerBasic:
    def test_single_step_ok(self, config, connection_factory):
        runner = _make_runner(config, connection_factory)
        pipeline = make_pipeline(make_step("a"))

        mock_run_results = [RunResult(host="localhost", success=True, stdout="KEY=value", stderr="")]

        with patch("ikctl.orchestration.runner.KitRepository") as MockKitRepo, \
             patch("ikctl.orchestration.runner.ServerRepository") as MockServerRepo, \
             patch("ikctl.orchestration.runner.RemoteRunner") as MockRemoteRunner:

            MockKitRepo.return_value.resolve.return_value = fake_kit()
            MockServerRepo.return_value.resolve.return_value = fake_servers()
            MockRemoteRunner.return_value.run.return_value = mock_run_results

            results = runner.run(pipeline, make_base_options())

        assert len(results) == 1
        assert results[0].id == "a"
        assert results[0].status == "ok"

    def test_single_step_failure(self, config, connection_factory):
        runner = _make_runner(config, connection_factory)
        pipeline = make_pipeline(make_step("a"))

        mock_run_results = [RunResult(host="localhost", success=False, stdout="", stderr="oops")]

        with patch("ikctl.orchestration.runner.KitRepository") as MockKitRepo, \
             patch("ikctl.orchestration.runner.ServerRepository") as MockServerRepo, \
             patch("ikctl.orchestration.runner.RemoteRunner") as MockRemoteRunner:

            MockKitRepo.return_value.resolve.return_value = fake_kit()
            MockServerRepo.return_value.resolve.return_value = fake_servers()
            MockRemoteRunner.return_value.run.return_value = mock_run_results

            results = runner.run(pipeline, make_base_options())

        assert results[0].status == "failed"


class TestOrchestrationRunnerSkip:
    def test_dependent_skipped_when_need_fails(self, config, connection_factory):
        runner = _make_runner(config, connection_factory)
        pipeline = make_pipeline(
            make_step("a"),
            make_step("b", needs=["a"]),
        )

        fail_results = [RunResult(host="localhost", success=False, stdout="", stderr="fail")]

        with patch("ikctl.orchestration.runner.KitRepository") as MockKitRepo, \
             patch("ikctl.orchestration.runner.ServerRepository") as MockServerRepo, \
             patch("ikctl.orchestration.runner.RemoteRunner") as MockRemoteRunner:

            MockKitRepo.return_value.resolve.return_value = fake_kit()
            MockServerRepo.return_value.resolve.return_value = fake_servers()
            MockRemoteRunner.return_value.run.return_value = fail_results

            results = runner.run(pipeline, make_base_options())

        assert len(results) == 2
        a_result = next(r for r in results if r.id == "a")
        b_result = next(r for r in results if r.id == "b")
        assert a_result.status == "failed"
        assert b_result.status == "skipped"

    def test_multiple_dependents_all_skipped(self, config, connection_factory):
        runner = _make_runner(config, connection_factory)
        pipeline = make_pipeline(
            make_step("a"),
            make_step("b", needs=["a"]),
            make_step("c", needs=["a"]),
        )

        fail_results = [RunResult(host="localhost", success=False, stdout="", stderr="fail")]

        with patch("ikctl.orchestration.runner.KitRepository") as MockKitRepo, \
             patch("ikctl.orchestration.runner.ServerRepository") as MockServerRepo, \
             patch("ikctl.orchestration.runner.RemoteRunner") as MockRemoteRunner:

            MockKitRepo.return_value.resolve.return_value = fake_kit()
            MockServerRepo.return_value.resolve.return_value = fake_servers()
            MockRemoteRunner.return_value.run.return_value = fail_results

            results = runner.run(pipeline, make_base_options())

        statuses = {r.id: r.status for r in results}
        assert statuses["a"] == "failed"
        assert statuses["b"] == "skipped"
        assert statuses["c"] == "skipped"

    def test_independent_step_still_runs_when_other_fails(self, config, connection_factory):
        runner = _make_runner(config, connection_factory)
        pipeline = make_pipeline(
            make_step("a"),
            make_step("b"),  # no dependency on a
        )

        def run_side_effect(kit, servers, options):
            # a fails, b succeeds — but since they run in same wave we track by call order
            return [RunResult(host="localhost", success=False, stdout="", stderr="fail")]

        with patch("ikctl.orchestration.runner.KitRepository") as MockKitRepo, \
             patch("ikctl.orchestration.runner.ServerRepository") as MockServerRepo, \
             patch("ikctl.orchestration.runner.RemoteRunner") as MockRemoteRunner:

            MockKitRepo.return_value.resolve.return_value = fake_kit()
            MockServerRepo.return_value.resolve.return_value = fake_servers()
            MockRemoteRunner.return_value.run.side_effect = [
                [RunResult(host="localhost", success=False, stdout="", stderr="fail")],
                [RunResult(host="localhost", success=True, stdout="", stderr="")],
            ]

            results = runner.run(pipeline, make_base_options())

        # Both should have been attempted (they're in wave 0, no deps)
        assert len(results) == 2


class TestOrchestrationRunnerOutputPropagation:
    def test_outputs_from_step_available_for_next(self, config, connection_factory):
        runner = _make_runner(config, connection_factory)
        pipeline = make_pipeline(
            make_step("a"),
            StepDef(
                id="b",
                kit="mykut",
                servers="myservers",
                params=["{{ steps.a.TOKEN }}"],
                needs=["a"],
            ),
        )

        call_args_capture = {}

        def run_side_effect(kit, servers, options):
            call_args_capture[id(options)] = getattr(options, "parameter", None)
            return [RunResult(host="localhost", success=True, stdout="TOKEN=abc123", stderr="")]

        with patch("ikctl.orchestration.runner.KitRepository") as MockKitRepo, \
             patch("ikctl.orchestration.runner.ServerRepository") as MockServerRepo, \
             patch("ikctl.orchestration.runner.RemoteRunner") as MockRemoteRunner:

            MockKitRepo.return_value.resolve.return_value = fake_kit()
            MockServerRepo.return_value.resolve.return_value = fake_servers()
            MockRemoteRunner.return_value.run.side_effect = run_side_effect

            results = runner.run(pipeline, make_base_options())

        # Step a should have extracted TOKEN=abc123
        a_result = next(r for r in results if r.id == "a")
        assert a_result.outputs == {"TOKEN": "abc123"}
        assert a_result.status == "ok"

        # Step b should have run (not skipped)
        b_result = next(r for r in results if r.id == "b")
        assert b_result.status == "ok"

    def test_step_outputs_extracted_from_stdout(self, config, connection_factory):
        runner = _make_runner(config, connection_factory)
        pipeline = make_pipeline(make_step("a"))

        mock_run_results = [RunResult(
            host="localhost", success=True,
            stdout="JOIN_TOKEN=secret\nJOIN_ENDPOINT=10.0.0.1:6443\nSome other output",
            stderr="",
        )]

        with patch("ikctl.orchestration.runner.KitRepository") as MockKitRepo, \
             patch("ikctl.orchestration.runner.ServerRepository") as MockServerRepo, \
             patch("ikctl.orchestration.runner.RemoteRunner") as MockRemoteRunner:

            MockKitRepo.return_value.resolve.return_value = fake_kit()
            MockServerRepo.return_value.resolve.return_value = fake_servers()
            MockRemoteRunner.return_value.run.return_value = mock_run_results

            results = runner.run(pipeline, make_base_options())

        assert results[0].outputs["JOIN_TOKEN"] == "secret"
        assert results[0].outputs["JOIN_ENDPOINT"] == "10.0.0.1:6443"


class TestOrchestrationRunnerErrors:
    def test_kit_not_found_marks_step_failed(self, config, connection_factory):
        from ikctl.exceptions import KitNotFoundError
        runner = _make_runner(config, connection_factory)
        pipeline = make_pipeline(make_step("a"))

        with patch("ikctl.orchestration.runner.KitRepository") as MockKitRepo:
            MockKitRepo.return_value.resolve.side_effect = KitNotFoundError("Kit 'mykut' not found")
            results = runner.run(pipeline, make_base_options())

        assert results[0].status == "failed"
        assert "mykut" in results[0].stderr

    def test_server_not_found_marks_step_failed(self, config, connection_factory):
        from ikctl.exceptions import ServerNotFoundError
        runner = _make_runner(config, connection_factory)
        pipeline = make_pipeline(make_step("a"))

        with patch("ikctl.orchestration.runner.KitRepository") as MockKitRepo, \
             patch("ikctl.orchestration.runner.ServerRepository") as MockServerRepo:

            MockKitRepo.return_value.resolve.return_value = fake_kit()
            MockServerRepo.return_value.resolve.side_effect = ServerNotFoundError("Server 'myservers' not found")

            results = runner.run(pipeline, make_base_options())

        assert results[0].status == "failed"
        assert "myservers" in results[0].stderr

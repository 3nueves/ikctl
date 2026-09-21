# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.12.2] - 2026-09-21

### Fixed

- `--stdout` crashed on every streamed line with `rich.errors.MarkupError: closing tag '[/]' at position N has nothing to close`, aborting the remote run. The stdout stream printer's prefix pre-closed its `[cyan]` tag while the printer itself appended a second, unmatched `[/]`.

## [1.12.1] - 2026-09-15

### Fixed

- Deadlock over SSH when a remote command produced more output than paramiko's receive window: `recv_exit_status()` was called before the channel buffers were drained. Output is now streamed incrementally via `recv_ready()`/`recv_stderr_ready()`.
- Pipeline step options were not applied correctly by the orchestration runner.

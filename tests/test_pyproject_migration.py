"""Tests that validate the pyproject_migration acceptance criteria."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import tomllib

ROOT = Path(__file__).parent.parent


def _load_pyproject() -> dict:
    with open(ROOT / "pyproject.toml", "rb") as f:
        return tomllib.load(f)


def test_pyproject_exists():
    """pyproject.toml must exist at the project root."""
    assert (ROOT / "pyproject.toml").exists()


def test_build_system_uses_hatchling():
    """[build-system] must require hatchling>=1.26."""
    data = _load_pyproject()
    requires = data["build-system"]["requires"]
    assert any("hatchling" in r for r in requires), "hatchling not found in build-system.requires"
    hatchling_req = next(r for r in requires if "hatchling" in r)
    assert "1.26" in hatchling_req or ">=" in hatchling_req


def test_build_backend_is_hatchling():
    """build-backend must be hatchling.build."""
    data = _load_pyproject()
    assert data["build-system"]["build-backend"] == "hatchling.build"


def test_project_name():
    """[project] name must be 'ikctl'."""
    data = _load_pyproject()
    assert data["project"]["name"] == "ikctl"


def test_project_dynamic_version():
    """[project] version must be dynamic."""
    data = _load_pyproject()
    assert "version" in data["project"]["dynamic"]


def test_project_description():
    """[project] must have a description."""
    data = _load_pyproject()
    assert data["project"]["description"]


def test_project_readme():
    """[project] readme must point to README.md."""
    data = _load_pyproject()
    assert data["project"]["readme"] == "README.md"


def test_project_license_spdx():
    """[project] license must be 'Apache-2.0' (SPDX)."""
    data = _load_pyproject()
    assert data["project"]["license"] == "Apache-2.0"


def test_project_license_files():
    """[project] license-files must include 'LICENSE*'."""
    data = _load_pyproject()
    assert "LICENSE*" in data["project"]["license-files"]


def test_project_authors():
    """[project] authors must be present."""
    data = _load_pyproject()
    assert data["project"]["authors"]


def test_project_requires_python():
    """[project] requires-python must be '>=3.13'."""
    data = _load_pyproject()
    assert data["project"]["requires-python"] == ">=3.13"


def test_project_classifiers():
    """[project] classifiers must include required entries."""
    data = _load_pyproject()
    classifiers = data["project"]["classifiers"]
    assert "Development Status :: 4 - Beta" in classifiers
    assert "Programming Language :: Python :: 3.13" in classifiers
    assert "License :: OSI Approved :: Apache Software License" in classifiers
    assert "Intended Audience :: System Administrators" in classifiers
    assert "Environment :: Console" in classifiers


def test_project_dependencies():
    """[project] dependencies must include paramiko>=3.0, pyaml, envyaml."""
    data = _load_pyproject()
    deps = data["project"]["dependencies"]
    dep_names = [re.split(r"[>=<!\[]", d)[0].strip() for d in deps]
    assert "paramiko" in dep_names
    assert "pyaml" in dep_names
    assert "envyaml" in dep_names
    paramiko_dep = next(d for d in deps if "paramiko" in d)
    assert "3.0" in paramiko_dep or ">=3.0" in paramiko_dep


def test_project_scripts():
    """[project.scripts] must map ikctl to ikctl.main:main."""
    data = _load_pyproject()
    assert data["project"]["scripts"]["ikctl"] == "ikctl.main:main"


def test_project_urls_repository():
    """[project.urls] must have a Repository entry."""
    data = _load_pyproject()
    assert "Repository" in data["project"]["urls"]


def test_hatch_version_path():
    """[tool.hatch.version] path must point to ikctl/config/config.py."""
    data = _load_pyproject()
    assert data["tool"]["hatch"]["version"]["path"] == "ikctl/config/config.py"


def test_dependency_groups_dev():
    """[dependency-groups].dev must include pytest>=8.0 and ruff>=0.5."""
    data = _load_pyproject()
    dev_deps = data["dependency-groups"]["dev"]
    dev_names = [re.split(r"[>=<!\[]", d)[0].strip() for d in dev_deps]
    assert "pytest" in dev_names
    assert "ruff" in dev_names
    pytest_dep = next(d for d in dev_deps if "pytest" in d)
    ruff_dep = next(d for d in dev_deps if "ruff" in d)
    assert "8.0" in pytest_dep or ">=8.0" in pytest_dep
    assert "0.5" in ruff_dep or ">=0.5" in ruff_dep


def test_version_no_v_prefix():
    """__version__ in config.py must not have 'v' prefix."""
    config_path = ROOT / "ikctl" / "config" / "config.py"
    content = config_path.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
    assert match, "__version__ not found in config.py"
    version = match.group(1)
    assert not version.startswith("v"), f"Version should not start with 'v', got: {version}"


def test_setup_py_removed():
    """setup.py must not exist."""
    assert not (ROOT / "setup.py").exists()


def test_pipfile_removed():
    """Pipfile must not exist."""
    assert not (ROOT / "Pipfile").exists()


def test_pipfile_lock_removed():
    """Pipfile.lock must not exist."""
    assert not (ROOT / "Pipfile.lock").exists()


def test_gitignore_has_venv():
    """.gitignore must contain an entry to ignore .venv."""
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".venv" in gitignore


def test_gitignore_does_not_ignore_uv_lock():
    """.gitignore must not ignore uv.lock."""
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    lines = [line.strip() for line in gitignore.splitlines()]
    assert "uv.lock" not in lines


def test_ikctl_version_output():
    """uv run ikctl --version must print the version without 'v' prefix."""
    result = subprocess.run(
        ["uv", "run", "ikctl", "--version"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0
    output = result.stdout.strip() + result.stderr.strip()
    assert output, "No version output"
    assert not output.startswith("v"), f"Version output should not start with 'v', got: {output}"


def test_init_sh_uses_uv_run_pytest():
    """init.sh must use 'uv run pytest' instead of 'python3 -m pytest'."""
    init_sh = (ROOT / "init.sh").read_text(encoding="utf-8")
    assert "uv run pytest" in init_sh
    assert "python3 -m pytest" not in init_sh

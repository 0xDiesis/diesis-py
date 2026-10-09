from pathlib import Path

import tomllib

PROJECT_ROOT = Path(__file__).parents[1]


def test_distribution_name_does_not_claim_unrelated_pypi_project() -> None:
    config = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())

    assert config["project"]["name"] == "diesis-sdk"
    assert config["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == ["src/diesis"]


def test_readme_documents_pinned_git_installation() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text()

    assert "pip install diesis\n" not in readme
    assert "'diesis-sdk @ git+https://github.com/0xDiesis/diesis-py.git@<commit>'" in readme
    assert "not on PyPI" in readme

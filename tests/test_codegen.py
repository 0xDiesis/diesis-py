"""Fail-closed generator input and non-mutating drift checks."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "codegen.py"
spec = importlib.util.spec_from_file_location("diesis_codegen", SCRIPT)
assert spec and spec.loader
codegen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codegen)


def fixture(tmp_path):
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    artifact = artifacts / "A.json"
    artifact.write_text(json.dumps({"abi": []}))
    entry = {
        "contract": "A",
        "source": "src/A.sol",
        "path": "A.json",
        "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
    }
    return artifacts, {"contractsRevision": codegen.CONTRACTS_REVISION, "selectedArtifacts": [entry]}


def test_rejects_stale_artifact_before_generator(tmp_path):
    artifacts, manifest = fixture(tmp_path)
    (artifacts / "A.json").write_text('{"abi":[{"type":"fallback"}]}')
    with pytest.raises(ValueError, match="Artifact hash"):
        codegen.artifact_contract_names(manifest, artifacts)


def test_rejects_escaping_and_duplicate_artifact_identity(tmp_path):
    artifacts, manifest = fixture(tmp_path)
    manifest["selectedArtifacts"].append(dict(manifest["selectedArtifacts"][0]))
    with pytest.raises(ValueError, match="Duplicate"):
        codegen.artifact_contract_names(manifest, artifacts)
    manifest["selectedArtifacts"] = [manifest["selectedArtifacts"][0]]
    manifest["selectedArtifacts"][0]["path"] = "../outside.json"
    with pytest.raises(ValueError, match="Escaping"):
        codegen.artifact_contract_names(manifest, artifacts)


def test_rejects_wrong_accepted_source(tmp_path):
    artifacts, manifest = fixture(tmp_path)
    manifest["contractsRevision"] = "0" * 40
    with pytest.raises(ValueError, match="contracts revision"):
        codegen.artifact_contract_names(manifest, artifacts)


def test_drift_detection_does_not_write_existing_generated_files(tmp_path):
    expected, actual = tmp_path / "expected", tmp_path / "actual"
    expected.mkdir()
    actual.mkdir()
    (expected / "A.py").write_text("new output\n")
    (actual / "A.py").write_text("old output\n")
    (actual / "extra.py").write_text("preserve during check\n")
    assert codegen.drift(expected, actual) == ["A.py", "extra.py"]
    assert (actual / "A.py").read_text() == "old output\n"
    assert (actual / "extra.py").is_file()


def test_generator_source_must_match_published_commit():
    with pytest.raises(ValueError, match="Generator source"):
        codegen.validate_generator_identity({"version": "abi-typegen 0.7.0", "sourceCommit": "0" * 40})
    codegen.validate_generator_identity(
        {"version": "abi-typegen 0.7.0", "sourceCommit": "e7e56176a4be4dd104ec3a05020fbacee414f88e"}
    )


def test_qualified_input_path_cannot_be_relative(monkeypatch):
    monkeypatch.setenv("DIESIS_ARTIFACTS_DIR", "contracts/out")
    with pytest.raises(ValueError, match="absolute path"):
        codegen.required_path("DIESIS_ARTIFACTS_DIR")


def test_generator_path_must_be_explicit_absolute(monkeypatch):
    monkeypatch.delenv("ABI_TYPEGEN", raising=False)
    with pytest.raises(ValueError, match="ABI_TYPEGEN is required"):
        codegen.required_path("ABI_TYPEGEN")
    monkeypatch.setenv("ABI_TYPEGEN", "node_modules/.bin/abi-typegen")
    with pytest.raises(ValueError, match="absolute path"):
        codegen.required_path("ABI_TYPEGEN")

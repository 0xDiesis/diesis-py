"""Generate Python bindings only from verified artifacts; check mode never writes source."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

CONTRACTS_REVISION = "e905d65c6a52df39f1d73906e9f5e91bd69011e9"
ROOT = Path(__file__).resolve().parents[1]


def artifact_contract_names(manifest: dict[str, Any], artifacts: Path) -> list[str]:
    if manifest.get("contractsRevision") != CONTRACTS_REVISION:
        raise ValueError("Unsupported contracts revision")
    names: list[str] = []
    identities: set[tuple[str, str]] = set()
    for entry in manifest["selectedArtifacts"]:
        name, source = entry["contract"], entry["source"]
        if name in names or (source, name) in identities:
            raise ValueError("Duplicate artifact identity")
        relative = Path(entry["path"])
        candidate = artifacts / relative
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or not candidate.resolve().is_relative_to(artifacts.resolve())
        ):
            raise ValueError("Escaping artifact path")
        if candidate.is_symlink() or hashlib.sha256(candidate.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError("Artifact hash mismatch")
        names.append(name)
        identities.add((source, name))
    if not names:
        raise ValueError("Qualified artifacts required")
    return names


def drift(expected: Path, actual: Path) -> list[str]:
    def files(root: Path) -> dict[str, bytes]:
        return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*.py") if p.is_file()}

    left, right = files(expected), files(actual)
    return sorted(name for name in left.keys() | right.keys() if left.get(name) != right.get(name))


def required_path(name: str) -> Path:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"{name} is required; contracts checkout outputs are never an implicit input")
    if not Path(value).is_absolute():
        raise ValueError(f"{name} must be an absolute path")
    return Path(value).resolve(strict=True)


def validate_generator_identity(generator: dict[str, Any]) -> None:
    if generator.get("sourceCommit") != "e7e56176a4be4dd104ec3a05020fbacee414f88e":
        raise ValueError("Generator source differs from published input")
    if generator.get("version") != "abi-typegen 0.7.0":
        raise ValueError("Exact abi-typegen 0.7.0 required")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    options = parser.parse_args()
    preflight = required_path("DIESIS_ARTIFACT_PREFLIGHT")
    manifest_path = required_path("DIESIS_ARTIFACT_MANIFEST")
    artifacts = required_path("DIESIS_ARTIFACTS_DIR")
    generator = required_path("ABI_TYPEGEN")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/verify-contract-artifacts.py"),
            "--preflight",
            str(preflight),
            "--check",
            str(manifest_path),
        ],
        check=True,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if artifacts != Path(manifest["artifactRoot"]).resolve(strict=True):
        raise ValueError("Artifact root differs from the qualified manifest")
    names = artifact_contract_names(manifest, artifacts)
    canonical = (ROOT / "scripts/abi-contracts.txt").read_text(encoding="utf-8").splitlines()
    if len(canonical) != 45 or len(set(canonical)) != 45 or set(names) != set(canonical):
        raise ValueError("Complete accepted contract selection required")
    validate_generator_identity(manifest["generator"])
    if hashlib.sha256(generator.read_bytes()).hexdigest() != manifest["generator"]["binarySha256"]:
        raise ValueError("Generator binary differs from qualified input")
    version = subprocess.check_output([str(generator), "--version"], text=True).strip()
    if version != "abi-typegen 0.7.0":
        raise ValueError("Exact abi-typegen 0.7.0 required")
    destination = ROOT / "src/diesis/abi/generated"
    with TemporaryDirectory(prefix="diesis-python-codegen-") as temporary:
        generated = Path(temporary) / "generated"
        subprocess.run(
            [
                str(generator),
                "generate",
                "--artifacts",
                str(artifacts),
                "--out",
                str(generated),
                "--target",
                "python",
                "--contracts",
                ",".join(names),
                "--clean",
            ],
            cwd=ROOT,
            check=True,
        )
        from generate_abi_exports import generate_exports

        generate_exports(generated)
        if set(p.stem for p in generated.glob("*.py")) - {"__init__"} != set(names):
            raise ValueError("Generator omitted or added contracts")
        changes = drift(generated, destination)
        if options.check:
            if changes:
                raise ValueError("Generated binding drift: " + ", ".join(changes))
            print("Python bindings reproduce byte for byte from qualified inputs")
        elif changes:
            if destination.is_symlink():
                raise ValueError("Generated source directory may not be a symlink")
            for existing in destination.glob("*.py"):
                existing.unlink()
            destination.mkdir(parents=True, exist_ok=True)
            for source in generated.glob("*.py"):
                shutil.copyfile(source, destination / source.name)


if __name__ == "__main__":
    main()

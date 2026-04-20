#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "release" / "darkoffice-skill-bundle"

INCLUDE_PATHS = [
    "skill/adapter.ts",
    "skill/darkoffice-persistent-skill.md",
    "runtime/__init__.py",
    "runtime/content.py",
    "runtime/db.py",
    "runtime/engine.py",
    "scripts/game_state_cli.py",
    "scripts/simulate_balance.py",
    "scripts/check_env.sh",
    "deploy/manifests/openclaw.skill.json",
    "deploy/manifests/workbuddy.skill.json",
    "deploy/manifests/qclaw.skill.json",
    "deploy/templates/DEPLOYMENT.md",
    "package.json",
    "package-lock.json",
    "tsconfig.json",
]


def copy_path(rel_path: str) -> None:
    src = ROOT / rel_path
    dst = BUNDLE / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)


def main() -> None:
    if BUNDLE.exists():
        shutil.rmtree(BUNDLE)
    BUNDLE.mkdir(parents=True, exist_ok=True)

    copied = []
    for rel in INCLUDE_PATHS:
        copy_path(rel)
        copied.append(rel)

    manifest = {
        "name": "darkoffice-skill-bundle",
        "version": "1.0.0",
        "files": copied,
        "entrypoint": "npx tsx skill/adapter.ts <command>",
        "healthcheck": "./scripts/check_env.sh",
    }
    (BUNDLE / "bundle-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "ok": True,
                "bundle_path": str(BUNDLE),
                "file_count": len(copied),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

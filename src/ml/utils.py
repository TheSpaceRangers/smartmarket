from datetime import UTC, datetime
from json import dump, loads
from pathlib import Path
from typing import Any

from django.conf import settings


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def artifacts_dir() -> Path:
    p = Path(settings.ML_ARTIFACTS_DIR)
    ensure_dir(p)
    return p


def write_manifest(name: str, manifest: dict[str, Any]) -> Path:
    manifest = {**manifest, "name": name, "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z")}
    path = artifacts_dir() / f"{name}_manifest.json"
    with path.open("w", encoding="utf-8") as f:
        dump(manifest, f, ensure_ascii=False, indent=2)
    return path


def read_manifest(name: str) -> dict[str, Any] | None:
    path = artifacts_dir() / f"{name}_manifest.json"
    if not path.exists():
        return None
    return loads(path.read_text(encoding="utf-8"))

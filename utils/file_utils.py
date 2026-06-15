from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Mapping, Any


def slugify(value: str, fallback: str = "requirement") -> str:
    safe_name = re.sub(r"[^a-z0-9]+", "_", (value or "").lower()).strip("_")
    safe_name = re.sub(r"_+", "_", safe_name)
    return safe_name[:100] or fallback


def save_script(requirement_or_feature: Mapping[str, Any] | str, script: str) -> str:
    os.makedirs("generated_tests", exist_ok=True)
    if isinstance(requirement_or_feature, Mapping):
        prefix = slugify(str(requirement_or_feature.get("id", "req")), "req")
        feature = slugify(str(requirement_or_feature.get("feature", "requirement")), "requirement")
        filename = f"{prefix}_{feature}.spec.ts"
    else:
        filename = f"{slugify(str(requirement_or_feature))}.spec.ts"
    path = Path("generated_tests") / filename
    path.write_text(script, encoding="utf-8")
    return str(path)


def clean_generated_outputs() -> None:
    for folder in [Path("generated_tests"), Path("reports")]:
        folder.mkdir(exist_ok=True)
    for spec in Path("generated_tests").glob("*.spec.ts"):
        spec.unlink()

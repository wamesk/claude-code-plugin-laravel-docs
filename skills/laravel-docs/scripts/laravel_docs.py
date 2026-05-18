#!/usr/bin/env python3
"""
laravel-docs — orchestration script for the laravel-docs Claude Code plugin.

This script does the deterministic work:
- Detect project type (modular vs flat)
- Scan models
- Load per-project config
- Resolve targets, output paths and prompts
- Emit a JSON plan for Claude to execute

Claude (via SKILL.md) then reads the JSON plan and performs the AI work
(reading models, applying prompts, writing markdown).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

PLUGIN_SLUG = "laravel-docs-wamesk"
DATA_ROOT = Path.home() / ".claude" / "plugins" / "data" / PLUGIN_SLUG
DEFAULT_TYPES = ("technical", "business", "admin")
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_PROMPTS_DIR = SKILL_DIR / "prompts"
DEFAULT_CONFIG_TEMPLATE = SKILL_DIR.parent.parent / "config.example.json"


# ---------- Config ----------------------------------------------------------

def project_config_dir(project_root: Path) -> Path:
    """Per-project persistent config directory."""
    project_hash = hashlib.md5(str(project_root.resolve()).encode()).hexdigest()[:12]
    return DATA_ROOT / project_hash


def default_config() -> dict:
    if DEFAULT_CONFIG_TEMPLATE.exists():
        return json.loads(DEFAULT_CONFIG_TEMPLATE.read_text(encoding="utf-8"))
    return {
        "types": {
            "technical": {"enabled": True, "output_path": "docs/technical", "prompt_path": None},
            "business": {"enabled": True, "output_path": "docs/business", "prompt_path": None},
            "admin": {"enabled": True, "output_path": "docs/admin", "prompt_path": None},
        },
        "modular_strategy": "per_module_with_root_index",
        "model_search_paths": [
            "app/Models",
            "wamesk/*/src/Models",
            "Modules/*/Models",
            "Modules/*/app/Models",
        ],
        "excluded_models": [],
        "language": "auto",
        "overwrite_existing": False,
        "generate_index_threshold": 2,
    }


def load_config(project_root: Path) -> dict:
    cfg_dir = project_config_dir(project_root)
    cfg_file = cfg_dir / "config.json"
    base = default_config()
    if cfg_file.exists():
        try:
            user_cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
            # Deep merge for types
            merged = {**base, **user_cfg}
            if "types" in user_cfg:
                merged_types = {**base.get("types", {})}
                for key, val in user_cfg["types"].items():
                    if isinstance(val, dict) and key in merged_types:
                        merged_types[key] = {**merged_types[key], **val}
                    else:
                        merged_types[key] = val
                merged["types"] = merged_types
            return merged
        except json.JSONDecodeError as exc:
            print(f"warn: config.json is invalid JSON ({exc}); using defaults", file=sys.stderr)
    return base


def init_config(project_root: Path) -> Path:
    cfg_dir = project_config_dir(project_root)
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_file = cfg_dir / "config.json"
    if cfg_file.exists():
        return cfg_file
    if DEFAULT_CONFIG_TEMPLATE.exists():
        shutil.copyfile(DEFAULT_CONFIG_TEMPLATE, cfg_file)
    else:
        cfg_file.write_text(json.dumps(default_config(), indent=2), encoding="utf-8")
    return cfg_file


# ---------- Project detection ----------------------------------------------

@dataclass
class ModelInfo:
    name: str
    file_path: str
    module: Optional[str] = None
    module_root: Optional[str] = None


def is_laravel_project(project_root: Path) -> bool:
    """Heuristic: composer.json contains laravel/framework."""
    composer = project_root / "composer.json"
    if not composer.exists():
        return False
    try:
        data = json.loads(composer.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    deps = {**data.get("require", {}), **data.get("require-dev", {})}
    return "laravel/framework" in deps or "laravel/laravel" in deps


def detect_modules(project_root: Path) -> list[dict]:
    """Detect wamesk-style or Modules/ style modules.

    Returns a list of dicts with: name, root, src_dir.
    """
    modules: list[dict] = []
    # wamesk/* style
    wamesk_dir = project_root / "wamesk"
    if wamesk_dir.is_dir():
        for child in sorted(wamesk_dir.iterdir()):
            if not child.is_dir():
                continue
            if (child / "src").is_dir() and (child / "composer.json").exists():
                modules.append({
                    "name": child.name,
                    "root": str(child.relative_to(project_root)),
                    "src_dir": "src",
                    "style": "wamesk",
                })
    # nwidart Modules/ style
    nwidart_dir = project_root / "Modules"
    if nwidart_dir.is_dir():
        for child in sorted(nwidart_dir.iterdir()):
            if not child.is_dir():
                continue
            # nwidart can place models in Models/ or app/Models/
            if (child / "Models").is_dir() or (child / "app" / "Models").is_dir():
                modules.append({
                    "name": child.name,
                    "root": str(child.relative_to(project_root)),
                    "src_dir": "app" if (child / "app").is_dir() else "",
                    "style": "nwidart",
                })
    return modules


def detect_project_type(project_root: Path) -> dict:
    laravel = is_laravel_project(project_root)
    modules = detect_modules(project_root)
    has_app_models = (project_root / "app" / "Models").is_dir()
    if modules:
        project_type = "modular"
    elif has_app_models:
        project_type = "flat"
    else:
        project_type = "unknown"
    locale = detect_locale(project_root)
    return {
        "project_type": project_type,
        "is_laravel": laravel,
        "modules": modules,
        "locale": locale,
        "project_root": str(project_root.resolve()),
    }


# ---------- Locale ----------------------------------------------------------

LOCALE_ENV_RE = re.compile(r"^\s*APP_LOCALE\s*=\s*['\"]?([a-zA-Z_]+)['\"]?\s*$", re.MULTILINE)
LOCALE_PHP_RE = re.compile(r"['\"]locale['\"]\s*=>\s*env\(['\"]APP_LOCALE['\"]\s*,\s*['\"]([a-zA-Z_]+)['\"]\)")
LOCALE_PHP_DIRECT_RE = re.compile(r"['\"]locale['\"]\s*=>\s*['\"]([a-zA-Z_]+)['\"]")


def detect_locale(project_root: Path) -> str:
    env_file = project_root / ".env"
    if env_file.exists():
        try:
            content = env_file.read_text(encoding="utf-8", errors="ignore")
            match = LOCALE_ENV_RE.search(content)
            if match:
                return match.group(1)
        except OSError:
            pass
    app_php = project_root / "config" / "app.php"
    if app_php.exists():
        try:
            content = app_php.read_text(encoding="utf-8", errors="ignore")
            match = LOCALE_PHP_RE.search(content) or LOCALE_PHP_DIRECT_RE.search(content)
            if match:
                return match.group(1)
        except OSError:
            pass
    return "en"


# ---------- Model scanning --------------------------------------------------

CLASS_RE = re.compile(r"^\s*(?:final\s+|abstract\s+)?class\s+([A-Z][A-Za-z0-9_]*)\b", re.MULTILINE)


def looks_like_model(php_text: str) -> bool:
    """Heuristic: extends Model / Authenticatable / Pivot / uses Eloquent."""
    return bool(re.search(
        r"\bextends\s+(?:Model|Authenticatable|Pivot|MorphPivot|Eloquent\\\\Model|Illuminate\\\\Database\\\\Eloquent\\\\Model)\b",
        php_text,
    ))


def extract_class_name(php_text: str, file_path: Path) -> Optional[str]:
    match = CLASS_RE.search(php_text)
    if match:
        return match.group(1)
    return file_path.stem


def scan_models(project_root: Path, config: dict, project_info: dict) -> list[ModelInfo]:
    search_paths = config.get("model_search_paths", []) or []
    excluded = set(config.get("excluded_models", []) or [])
    found: dict[str, ModelInfo] = {}

    # Build a quick lookup of module roots to map a model to a module
    module_lookup: list[tuple[Path, str]] = []
    for module in project_info.get("modules", []):
        module_lookup.append((project_root / module["root"], module["name"]))

    for raw_pattern in search_paths:
        pattern = raw_pattern.strip()
        if not pattern:
            continue
        # Resolve glob relative to project root
        for path in project_root.glob(pattern):
            if not path.is_dir():
                continue
            for php_file in path.rglob("*.php"):
                try:
                    text = php_file.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                if not looks_like_model(text):
                    continue
                name = extract_class_name(text, php_file)
                if not name or name in excluded:
                    continue
                if name in found:
                    continue  # first match wins
                module_name = None
                module_root = None
                for mod_root, mod_name in module_lookup:
                    try:
                        php_file.relative_to(mod_root)
                        module_name = mod_name
                        module_root = str(mod_root.relative_to(project_root))
                        break
                    except ValueError:
                        continue
                found[name] = ModelInfo(
                    name=name,
                    file_path=str(php_file.relative_to(project_root)),
                    module=module_name,
                    module_root=module_root,
                )
    return sorted(found.values(), key=lambda m: m.name)


# ---------- Path & prompt resolution ---------------------------------------

def kebab_to_snake(name: str) -> str:
    """Order → order, OrderItem → order_item"""
    out = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    return out


def compute_output_path(
    project_root: Path,
    model: ModelInfo,
    type_name: str,
    type_cfg: dict,
    project_type: str,
    modular_strategy: str,
) -> dict:
    """Return dict with file output info."""
    type_output = type_cfg.get("output_path") or f"docs/{type_name}"

    # Modular strategies
    if project_type == "modular" and model.module:
        if modular_strategy == "per_module_with_root_index":
            module_dir = Path(model.module_root) / "docs" / type_name
            output_dir = project_root / module_dir
            relative_dir = str(module_dir)
            root_index_dir = project_root / type_output
            root_index_rel = type_output
        elif modular_strategy == "module_only":
            module_dir = Path(model.module_root) / "docs" / type_name
            output_dir = project_root / module_dir
            relative_dir = str(module_dir)
            root_index_dir = None
            root_index_rel = None
        else:  # central_only
            output_dir = project_root / type_output / model.module
            relative_dir = f"{type_output}/{model.module}"
            root_index_dir = project_root / type_output
            root_index_rel = type_output
    else:
        # flat layout
        output_dir = project_root / type_output
        relative_dir = type_output
        root_index_dir = project_root / type_output
        root_index_rel = type_output

    file_name = f"{model.name}.md"
    file_path = output_dir / file_name
    return {
        "file": str(file_path),
        "file_relative": f"{relative_dir}/{file_name}",
        "directory": str(output_dir),
        "directory_relative": relative_dir,
        "root_index_dir": str(root_index_dir) if root_index_dir else None,
        "root_index_dir_relative": root_index_rel,
        "exists": file_path.exists(),
    }


def resolve_prompt_path(project_root: Path, type_name: str, type_cfg: dict) -> str:
    custom = type_cfg.get("prompt_path")
    if custom:
        candidate = Path(custom)
        if not candidate.is_absolute():
            candidate = project_root / candidate
        if candidate.exists():
            return str(candidate)
        # Fall through to default if custom path is missing
        print(
            f"warn: custom prompt_path '{custom}' not found for type '{type_name}'; "
            f"falling back to default",
            file=sys.stderr,
        )
    default = DEFAULT_PROMPTS_DIR / f"{type_name}.md"
    return str(default)


# ---------- Plan ------------------------------------------------------------

def resolve_types(
    config: dict,
    cli_types: Optional[list[str]],
) -> list[str]:
    """CLI types override config.enabled — explicit user request always wins."""
    if cli_types:
        return cli_types
    enabled: list[str] = []
    for type_name, type_cfg in (config.get("types") or {}).items():
        if type_cfg.get("enabled", True):
            enabled.append(type_name)
    return enabled


def resolve_language(
    cli_lang: Optional[str],
    config: dict,
    project_locale: str,
) -> str:
    if cli_lang:
        return cli_lang
    cfg_lang = config.get("language", "auto")
    if cfg_lang and cfg_lang != "auto":
        return cfg_lang
    return project_locale or "en"


def filter_targets(
    models: list[ModelInfo],
    model_arg: Optional[str],
    module_arg: Optional[str],
) -> list[ModelInfo]:
    if model_arg:
        filtered = [m for m in models if m.name.lower() == model_arg.lower()]
        return filtered
    if module_arg:
        return [m for m in models if (m.module or "").lower() == module_arg.lower()]
    return models


def build_plan(args: argparse.Namespace) -> dict:
    project_root = Path(args.project_root).resolve() if args.project_root else Path.cwd()
    project_info = detect_project_type(project_root)
    config = load_config(project_root)

    cli_types = None
    if args.type:
        cli_types = [t.strip() for t in args.type.split(",") if t.strip()]

    language = resolve_language(args.lang, config, project_info["locale"])
    types = resolve_types(config, cli_types)

    models = scan_models(project_root, config, project_info)
    targets = filter_targets(models, args.model, args.module)

    modular_strategy = config.get("modular_strategy", "per_module_with_root_index")
    overwrite = args.overwrite or bool(config.get("overwrite_existing", False))

    items = []
    type_to_dirs: dict[str, set[str]] = {}

    for model in targets:
        for type_name in types:
            type_cfg = (config.get("types") or {}).get(type_name) or {}
            paths = compute_output_path(
                project_root, model, type_name, type_cfg, project_info["project_type"], modular_strategy,
            )
            prompt_path = resolve_prompt_path(project_root, type_name, type_cfg)
            item = {
                "model": asdict(model),
                "type": type_name,
                "prompt_path": prompt_path,
                "output": paths,
                "skip": paths["exists"] and not overwrite,
            }
            items.append(item)
            root_dir = paths.get("root_index_dir_relative")
            if root_dir:
                type_to_dirs.setdefault(type_name, set()).add(root_dir)

    indexes = []
    threshold = int(config.get("generate_index_threshold", 2))
    for type_name, dirs in type_to_dirs.items():
        for relative_dir in sorted(dirs):
            indexes.append({
                "type": type_name,
                "directory_relative": relative_dir,
                "directory": str(project_root / relative_dir),
                "threshold": threshold,
            })

    plan = {
        "project": project_info,
        "language": language,
        "modular_strategy": modular_strategy,
        "config_path": str(project_config_dir(project_root) / "config.json"),
        "overwrite": overwrite,
        "filters": {
            "model": args.model,
            "module": args.module,
            "all": args.all,
            "types_cli_override": cli_types is not None,
        },
        "types": types,
        "models_found": len(models),
        "targets_count": len(targets),
        "items": items,
        "indexes": indexes,
        "default_prompts_dir": str(DEFAULT_PROMPTS_DIR),
    }

    if not models:
        plan["warning"] = (
            "No models found. Check `model_search_paths` in config (run --init "
            "to create per-project config) or `--project-root`."
        )
    elif not targets:
        plan["warning"] = (
            f"Model/module filter matched zero models out of {len(models)} discovered. "
            f"Available models: {', '.join(m.name for m in models[:25])}"
            + ("…" if len(models) > 25 else "")
        )

    return plan


# ---------- CLI -------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="laravel-docs",
        description="Orchestration helper for the laravel-docs Claude Code plugin.",
    )
    parser.add_argument("--init", action="store_true", help="Create per-project config.json")
    parser.add_argument("--detect", action="store_true", help="Detect project type and exit")
    parser.add_argument("--plan", action="store_true", help="Emit JSON execution plan (default)")
    parser.add_argument("--model", help="Filter to a specific model name (e.g. Order)")
    parser.add_argument("--module", help="Filter to a specific module name (e.g. order)")
    parser.add_argument("--all", action="store_true", help="Include all models (default if no filter given)")
    parser.add_argument("--type", help="Comma-separated list of doc types (technical,business,admin). Overrides config.enabled.")
    parser.add_argument("--lang", help="Force documentation language (e.g. sk, en, cs)")
    parser.add_argument("--project-root", help="Override project root (defaults to CWD)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve() if args.project_root else Path.cwd()

    if args.init:
        cfg = init_config(project_root)
        print(json.dumps({"status": "ok", "config_path": str(cfg)}, indent=2 if args.pretty else None))
        return 0

    if args.detect:
        info = detect_project_type(project_root)
        print(json.dumps(info, indent=2 if args.pretty else None))
        return 0

    plan = build_plan(args)
    print(json.dumps(plan, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    sys.exit(main())

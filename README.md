# laravel-docs — Claude Code plugin

Generate **technical**, **business**, and **admin-navigation** documentation
for any Laravel project — model by model, module by module, or all at once.

Auto-detects modular (`wamesk/*`, `Modules/*`) vs flat (`app/Models`) layout.
Per-project config, overridable output paths, and replaceable prompts per
documentation type.

## Installation

```bash
# inside Claude Code
/plugin marketplace add wamesk/claude-code     # one-time
/plugin install laravel-docs@wamesk
```

## Quick start

In the root of your Laravel project:

```
/laravel-docs --init               # create per-project config (optional)
/laravel-docs Order                # docs for the Order model — all enabled types
/laravel-docs --module=order       # docs for every model in the order module
/laravel-docs --all                # docs for every model in the project
/laravel-docs Order --type=admin   # only the admin navigation guide
/laravel-docs Order --lang=cs      # force Czech output
```

If no arguments are given, `/laravel-docs` generates **all enabled types for
all discovered models**.

## What it generates

By default three document types per model:

| Type | Audience | Style |
|------|----------|-------|
| **technical** | Developers, analysts | Full business-technical spec — fields, validations, lifecycle, Observer, Services, Jobs |
| **business** | Client, product owner, account manager | Plain language — no code, no SQL, no framework jargon |
| **admin** | Nova admin end-users | Click-by-click navigation, every button, every filter, workflows |

Output location depends on project layout and `modular_strategy`:

- **Modular** + `per_module_with_root_index` (default):
  - Files: `wamesk/{module}/docs/{type}/{Label} ({Model}).md`
  - Root index (if ≥ 2 files): `docs/{type}/index.md`
- **Flat**: `docs/{type}/{Model}.md`

## Configuration

Per-project config is stored at:

```
~/.claude/plugins/data/laravel-docs-wamesk/<project-hash>/config.json
```

This location survives plugin updates. The config path is also printed in
the JSON plan (visible in verbose runs).

Example (`config.example.json`):

```json
{
  "types": {
    "technical": { "enabled": true,  "output_path": "docs/technical", "prompt_path": null },
    "business":  { "enabled": true,  "output_path": "docs/business",  "prompt_path": null },
    "admin":     { "enabled": true,  "output_path": "docs/admin",     "prompt_path": null }
  },
  "modular_strategy": "per_module_with_root_index",
  "model_search_paths": ["app/Models", "wamesk/*/src/Models", "Modules/*/Models", "Modules/*/app/Models"],
  "excluded_models": [],
  "language": "auto",
  "overwrite_existing": false,
  "generate_index_threshold": 2
}
```

### CLI override behavior

- **Type enabled/disabled:** CLI `--type=X` **always** wins. Even if
  `types.X.enabled` is `false` in the config, `--type=X` will generate it.
- **Language priority:** `--lang` > `config.language` > `APP_LOCALE` > `en`.
- **Overwrite:** `--overwrite` flag > `config.overwrite_existing` > `false`
  (existing files are skipped by default with a `⏭️` line).

### Custom prompts

Replace any built-in prompt with your own — point `types.X.prompt_path`
at a markdown file in your project:

```json
"types": {
  "technical": {
    "enabled": true,
    "output_path": "docs/technical",
    "prompt_path": ".claude/prompts/my-tech-spec.md"
  }
}
```

The custom prompt receives the same placeholders as built-in prompts
(`{model_name}`, `{model_file}`, `{module_root}`, `{locale}`, `{output_file}`, …).
See [`skills/laravel-docs/prompts/technical.md`](skills/laravel-docs/prompts/technical.md)
for the full list and an example structure.

### Custom doc types

Add a brand-new type by inserting an entry under `types` and supplying a
prompt:

```json
"types": {
  "api-spec": {
    "enabled": true,
    "output_path": "docs/api",
    "prompt_path": ".claude/prompts/api-spec.md"
  }
}
```

Then invoke with `/laravel-docs --type=api-spec`.

## How it works

The plugin combines a deterministic Python orchestrator with Claude's AI
generation:

1. **`scripts/laravel_docs.py`** — detects project type, scans models,
   loads config, computes output paths, and emits a JSON execution plan.
2. **`SKILL.md`** — Claude reads the plan, applies each prompt, writes the
   markdown files, and maintains the per-type `index.md`.

Run the script directly for debugging:

```bash
python3 ~/.claude/plugins/.../laravel_docs.py --detect --pretty
python3 ~/.claude/plugins/.../laravel_docs.py --plan --model=Order --pretty
```

## Supported project layouts

- **Flat Laravel** — models in `app/Models`
- **wamesk/internachi modular** — `wamesk/{module}/src/Models`
- **nwidart/laravel-modules** — `Modules/{Module}/Models` or `Modules/{Module}/app/Models`
- **Custom** — add globs to `model_search_paths` in config

## Languages

Documentation is generated in the project's primary language. Detection
priority:

1. `--lang` CLI flag
2. `language` field in config (not `auto`)
3. `APP_LOCALE` from `.env` / `config/app.php`
4. Fallback: `en`

Slovak, Czech, English are explicitly tested. Other languages work as long
as Claude can write in them — proper diacritics are enforced.

## FAQ

**Q: My model wasn't picked up.**
A: Check `model_search_paths` in your config — the default covers wamesk
and nwidart layouts plus `app/Models`. For custom locations add a glob,
e.g. `"src/Domain/*/Models"`. Run `python3 .../laravel_docs.py --plan --pretty`
to see which models are detected.

**Q: I want all three types in one PDF.**
A: Out of scope for v1. Consider running `pandoc` over the generated
markdown afterwards — the layout (`docs/{type}/`) is friendly to bulk
conversion.

**Q: Can I disable a type just once?**
A: Yes — `--type=technical,business` only generates those two and skips
`admin` for that run.

**Q: Why does CLI override the disabled flag?**
A: Explicit user intent beats stored preferences. If you typed
`--type=admin`, you wanted admin docs.

## License

MIT — see [LICENSE](LICENSE).

## Contributing

Plugin lives at <https://github.com/wamesk/claude-code-plugin-laravel-docs>.
Marketplace registration is in <https://github.com/wamesk/claude-code>.

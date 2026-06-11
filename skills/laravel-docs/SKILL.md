---
name: laravel-docs
description: "Use when the user asks to 'generate Laravel documentation', 'create model specification', 'vytvor špecifikáciu', 'generuj dokumentáciu pre Laravel projekt', '/laravel-docs', or wants technical/business/admin docs for a Laravel model or module. Auto-detects modular (wamesk/*) vs flat (app/Models) project layout. Invoked as /laravel-docs with optional model name, --module, --type, --lang, --all flags."
argument-hint: "[Model | --module=name | --all] [--type=technical,business,admin] [--lang=sk|en|cs]"
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep]
---

# Laravel Docs Generator

Generate **technical**, **business**, and **admin-navigation** documentation
for one or more models in a Laravel project. Auto-detects modular (wamesk/*,
Modules/*) vs flat (`app/Models`) layout. Per-project config with overridable
output paths and custom prompts.

## Arguments

User invoked this with: `$ARGUMENTS`

Supported forms:
- `/laravel-docs` — all models × all enabled doc types
- `/laravel-docs Order` — single model, all enabled types
- `/laravel-docs --module=order` — all models from a module
- `/laravel-docs --all` — explicitly: all models
- `/laravel-docs --type=technical,business` — restrict doc types
- `/laravel-docs Order --type=admin` — single type for single model (CLI overrides `enabled:false` in config)
- `/laravel-docs Order --lang=cs` — force language (overrides APP_LOCALE)
- `/laravel-docs --init` — create per-project config.json
- `/laravel-docs --overwrite` — regenerate even if files exist

## Step-by-step instructions

### Step 1 — Locate the orchestration script

The Python script is bundled with the plugin. Find it once and reuse:

```bash
SCRIPT=$(find ~/.claude/plugins -path "*/laravel-docs/skills/laravel-docs/scripts/laravel_docs.py" -print -quit 2>/dev/null | head -1)
```

If empty, the plugin is not installed correctly — tell the user to run
`/plugin install laravel-docs@wamesk` (or check their `~/.claude/plugins`
path manually).

### Step 2 — Handle `--init`

If the user passed `--init`, run:

```bash
python3 "$SCRIPT" --init
```

Print the resulting `config_path`, then **stop**. The user will edit the
config and re-invoke without `--init`.

### Step 3 — Build the execution plan

Pass through the user's arguments to the script with `--plan`:

```bash
python3 "$SCRIPT" --plan [user arguments] --pretty
```

The script returns a JSON plan. Parse it. Key fields:

- `project.project_type` — `modular`, `flat`, or `unknown`
- `project.is_laravel` — must be `true`; if false, **abort** with a friendly error
- `language` — output language for the docs
- `models_found`, `targets_count`
- `items[]` — list of `(model × type)` work items
- `indexes[]` — per-type root index directories (only build if ≥ threshold files exist after run)
- `warning` — present when no matches; relay it to the user and stop

If `targets_count == 0` show the warning and **stop**.

### Step 4 — Confirm before large runs

If `len(items) > 10`, show the user a summary:

> Going to generate **N documents** across **M models** and **K types**.
> Language: `{language}`. Continue?

Use natural language confirmation — do **not** spawn AskUserQuestion for
small runs (≤ 10 items).

### Step 5 — Execute each item

For each item where `skip == false`:

1. **Read the prompt** at `item.prompt_path`
2. **Substitute placeholders** with values from the plan:
   - `{model_name}` ← `item.model.name`
   - `{model_file}` ← `item.model.file_path`
   - `{module_name}` ← `item.model.module` (empty if flat)
   - `{module_root}` ← `item.model.module_root` (empty if flat)
   - `{project_type}` ← `project.project_type`
   - `{locale}` ← `language`
   - `{output_file}` ← `item.output.file`
3. **Follow the prompt** — read the model, translations, related files;
   build the markdown content; write to `item.output.file` (create
   directories if needed).
4. **Rename the file** if the prompt requested a translated label
   (e.g. `Order.md` → `Objednávky (Order).md`)
5. After each item, print **only**:
   ```
   ✅ Created: <relative path>
   ```
   Do **not** echo the file contents.

For items where `skip == true` (file exists, no `--overwrite`):

```
⏭️  Skipped (already exists): <relative path>
```

### Step 6 — Generate root index files

For every entry in `indexes[]`:

1. Count `.md` files in `directory` (exclude `index.md` itself).
2. If count `>= threshold`:
   - List all `.md` files (excluding `index.md`)
   - Write `<directory>/index.md` with:
     - Heading `# {Type capitalized} documentation`
     - Bulleted list with relative links sorted alphabetically by file name
     - If modular project + `per_module_with_root_index`: group by module
       (extract module from each file's path by reading the file's location
       on disk after writing)

Because every file is named `{Label} ({Model}).md` (spaces **and**
parentheses in the name), the link destination must be wrapped in angle
brackets `<...>` — the CommonMark angle-bracket form. Without it the literal
`)` truncates the destination and the spaces break the link, so the generated
index links do not resolve. Always emit the destination as `<...>`.

The index list should look like (for modular):

```markdown
# Technical documentation

## Module: order
- [Objednávky (Order)](<../../wamesk/order/docs/technical/Objednávky (Order).md>)
- [Položka objednávky (OrderItem)](<../../wamesk/order/docs/technical/Položka objednávky (OrderItem).md>)

## Module: ticket
- [Lístok (Ticket)](<../../wamesk/ticket/docs/technical/Lístok (Ticket).md>)
```

For flat layout, just one ungrouped list (still using the angle-bracket form,
since the file names contain spaces and parentheses too):

```markdown
# Technical documentation

- [Order](<Order.md>)
- [Invoice](<Invoice.md>)
```

### Step 7 — Final summary

Print a compact summary at the end:

```
Generated N file(s), skipped M, indexed K type(s).
Output language: {language}
```

Do not enumerate files again (already printed during the loop).

## Error handling

- **No models found** → show the `warning` from the plan; suggest
  `/laravel-docs --init` and editing `model_search_paths`.
- **Custom prompt not found** → script already falls back to default and
  emits a warning on stderr; surface it to the user.
- **Output directory not writable** → tell the user the failing path.
- **No translations** → fall back to the model class name for the file
  name and headings; do not fail.

## Configuration reference

Per-project config lives at:
```
~/.claude/plugins/data/laravel-docs-wamesk/<project-hash>/config.json
```

Run `/laravel-docs --init` to create it from the bundled `config.example.json`.
The path is also printed in the plan JSON (`config_path`).

Key options:

- `types.{name}.enabled` — set `false` to disable a type by default. **CLI
  `--type=X` always overrides this.**
- `types.{name}.output_path` — where docs of this type go (project-relative).
  In modular projects with `per_module_with_root_index`, this path is used
  only for the **root index**; individual files go to `{module_root}/docs/{type}/`.
- `types.{name}.prompt_path` — path to a custom prompt (project-relative or
  absolute). `null` = use bundled default.
- `modular_strategy` — `per_module_with_root_index` (default), `central_only`,
  or `module_only`.
- `model_search_paths` — glob list; defaults cover wamesk/*, Modules/*, and
  flat `app/Models`.
- `language` — `auto` (detect from `APP_LOCALE`), or explicit code (`sk`,
  `en`, `cs`, …). **CLI `--lang` overrides.**
- `excluded_models` — names to skip (e.g. `["BaseModel", "User"]`).
- `overwrite_existing` — default behavior; `--overwrite` flag overrides.
- `generate_index_threshold` — min files before an `index.md` is created.

## Custom doc types

Add a new entry under `types` in config.json:

```json
"types": {
  "api-spec": {
    "enabled": true,
    "output_path": "docs/api",
    "prompt_path": ".claude/prompts/my-api-spec.md"
  }
}
```

The custom prompt receives the same placeholders as built-in prompts.
Invoke with `/laravel-docs --type=api-spec`.

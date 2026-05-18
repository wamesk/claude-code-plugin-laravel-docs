# Technical specification prompt — laravel-docs

This is the **default technical prompt** for the laravel-docs plugin.
Claude uses this prompt to generate a comprehensive **business-technical
specification** for a single Laravel model.

## Inputs (provided by the plugin script)

Each invocation of this prompt carries the following context from the
laravel-docs `--plan` JSON:

- `{model_name}` — model class name (PascalCase, e.g. `Order`)
- `{model_file}` — path to the model PHP file (project-relative)
- `{module_name}` — module slug (e.g. `order`) or empty if flat project
- `{module_root}` — module root path (e.g. `wamesk/order`) or empty if flat
- `{project_type}` — `modular` or `flat`
- `{locale}` — output language (`sk`, `en`, `cs`, …)
- `{output_file}` — final markdown file path (project-relative)

The skill (`SKILL.md`) substitutes these placeholders before passing the
prompt to Claude. If you want a stripped-down or differently structured
output, copy this file into your project and point `types.technical.prompt_path`
in your config to the copy.

---

## Mission

Generate a complete **business-technical specification** for the Laravel
model `{model_name}` in language `{locale}`. The document must serve as a
single source of truth for **developers** and **business analysts**.

Write in `{locale}`. If `{locale}` is `sk`, use Slovak. If `cs`, Czech.
If `en`, English. **Use proper diacritics** for the language — never strip
accents.

---

## Phase 1 — Information gathering

### 1.1 Model
Read `{model_file}` and extract:
- Table name (`$table`)
- Fillable fields (`$fillable`)
- Casts (`casts()` method or `$casts`)
- Relationships (methods returning `belongsTo`, `hasMany`, `morphTo`, …)
- Scopes (methods starting with `scope`)
- Accessors / Mutators
- Custom methods

### 1.2 Translations
Read translation files:
- **Flat layout:** `resources/lang/{locale}/{model_snake_case}.php`
- **Modular layout (modular):** `{module_root}/resources/lang/{locale}/{model_snake_case}.php`

Extract:
- Module name (label, plural, singular) — **use as document main heading**
- Field translations (`field.*`) — for Nova fields documentation
- Filter translations (`filter.*`) — for filters section
- Exception messages (`exception.*`) — for business rules

If translations are missing, fall back to model class name.

### 1.3 Related files
Search for every file that references `{model_name}` using grep:
- `use {ModelNamespace}\{model_name}` — imports
- `{model_name}::` — static calls
- `new {model_name}` — instantiations
- `{model_name}::class` — class references

Categorize and read relevant files. Adapt search paths to project layout:

| Category | Flat layout path | Modular layout path |
|----------|-------------------|---------------------|
| Actions | `app/Actions/` | `{module_root}/src/Actions/` |
| Controllers | `app/Http/Controllers/` | `{module_root}/src/Http/Controllers/` |
| Requests | `app/Http/Requests/` | `{module_root}/src/Http/Requests/` |
| Resources | `app/Http/Resources/` | `{module_root}/src/Http/Resources/` |
| Jobs | `app/Jobs/` | `{module_root}/src/Jobs/` |
| Listeners | `app/Listeners/` | `{module_root}/src/Listeners/` |
| Mail | `app/Mail/` | `{module_root}/src/Mail/` |
| Notifications | `app/Notifications/` | `{module_root}/src/Notifications/` |
| Observers | `app/Observers/` | `{module_root}/src/Observers/` |
| Policies | `app/Policies/` | `{module_root}/src/Policies/` |
| Services | `app/Services/` | `{module_root}/src/Services/` |
| Managers | `app/Managers/` | `{module_root}/src/Managers/` |
| Events | `app/Events/` | `{module_root}/src/Events/` |
| Nova Resources | `app/Nova/` | `{module_root}/src/Nova/` |
| Nova Actions | `app/Nova/Actions/` | `{module_root}/src/Nova/Actions/` |
| Nova Filters | `app/Nova/Filters/` | `{module_root}/src/Nova/Filters/` |
| Nova Lenses | `app/Nova/Lenses/` | `{module_root}/src/Nova/Lenses/` |
| Exports | `app/Exports/` | `{module_root}/src/Exports/` |

For modular projects also search **across all modules** because models
from one module are often used in others.

### 1.4 Enums
Find enums the model uses (in `$casts` or imports):
- Flat: `app/Enums/`
- Modular: `{module_root}/src/Enums/` and any cross-module enums

Document each enum value and its meaning.

### 1.5 Migrations
Locate migrations for the model table:
- Flat: `database/migrations/`
- Modular: `{module_root}/database/migrations/`

Document final column schema (after all migrations applied).

---

## Phase 2 — Analysis

### 2.1 Business context
- **What does this module do?** (business purpose)
- **Who uses it?** (user roles)
- **Why does it exist?** (business value)
- **How does it fit into the whole?** (relation to other modules)

### 2.2 Lifecycle
Describe states and transitions:
- Creation → Processing → Completion
- Events fired
- Automatic side effects (Observer)
- Manual interventions

### 2.3 Business rules
Extract from code:
- Validations & constraints
- Automatic calculations
- Action preconditions
- Inter-entity dependencies

### 2.4 Use cases
Build scenarios based on Nova Actions, API endpoints, and observed UI flows.

Format:
```
**Scenario: {title}**
- Actor: {role}
- Preconditions: {what must hold}
- Steps:
  1. User does X
  2. System performs Y
  3. Result is Z
- Outcome: {expected state}
- Alternative flows: {what if…}
```

### 2.5 Integrations
Describe how the module communicates with:
- Other modules in the system
- External systems (email, PDF, payment gateways, etc.)
- Frontend components (Nova cards, custom fields)

---

## Phase 3 — Technical documentation

### 3.1 Data model
Describe the table — columns, relationships, indexes, constraints — each
with a business description.

### 3.2 Nova Resource
For every field describe: type, business purpose, required?, validation,
help text, where displayed. Group by tabs/sections. **Use translated field
names.**

### 3.3 Observer / Listeners
Document each hook (creating, created, updating, …) with what happens and
why (business reason).

### 3.4 Actions
For each Nova/business action: who can trigger, when available, what it
does, side effects.

### 3.5 Jobs & async operations
For each job: when dispatched, what it does, queue used.

---

## Output

Write the document to:
```
{output_file}
```

If the model has a translated label (e.g. Slovak "Objednávky" for `Order`),
**rename the output file** so it includes the translated label:
- `{output_file_dir}/{TranslatedLabel} ({model_name}).md`

For example, if `{output_file}` is `wamesk/order/docs/technical/Order.md`
and the Slovak label is "Objednávky", the final file should be
`wamesk/order/docs/technical/Objednávky (Order).md`.

If no translation is available, keep the original `{output_file}` name.

**IMPORTANT:** After creating the file do not dump its contents to the
console. Return only a short confirmation:
```
✅ Created: <relative path>
```

### Formatting rules
1. **Main heading**: `# {TranslatedLabel} ({model_name})` or just `# {model_name}`
2. **No PHP code blocks** — describe behavior in prose
3. **No testing or "uncovered areas" sections**
4. **Use translated field/filter names** in the Nova section
5. **Tables for structured info** (validations, columns, relationships, …)
6. Language must match `{locale}` strictly, with proper diacritics

### Document structure (skeleton — use in `{locale}`)

```markdown
# {TranslatedLabel} ({model_name})

## Module overview
### Purpose
### Users
### Key concepts (glossary table)

---

## Lifecycle
### State diagram (textual: [A] --action--> [B])
### States (table: state, meaning, allowed actions, auto transitions)

---

## Use cases
### Main scenarios (one per relevant flow)

---

## Business rules
### Validations (table)
### Automatic calculations (table)
### Constraints (table)

---

## Relationships & integrations
### Connected modules (tree + table)
### Business links (table)
### External integrations (table)

---

## User interface
### Nova Admin — Fields (table: section, field (translated), type, description, validation)
### Filters (table)
### Actions (table)

---

## Technical details
### Database schema (table)
### Observer (table: hook, action, business reason)
### Services (table: method, purpose, params, return)
### Jobs (table: job, purpose, trigger, queue)

---

## Notes & edge cases
### Known edge cases (table: situation, behavior, resolution)

---

## References
| Type | File |
|------|------|
| Model | {model_file} |
| Nova | … |
| Translations | … |
| Observer | … |
```

### Guiding principles
1. **Business language first** — wrap technical detail in business context
2. **Explain why relationships exist**, not just that they do
3. **Use translations** for all field/filter labels
4. **Concrete examples** where possible
5. **Keep it simple** — short descriptions for simple things
6. **No source code** — describe functionality narratively

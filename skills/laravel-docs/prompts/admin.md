# Admin navigation prompt — laravel-docs

This is the **default admin-navigation prompt** for the laravel-docs plugin.
Generates a **step-by-step guide for administrators** who use the Laravel
Nova admin panel — what each screen does, how to navigate, what every
button and filter is for.

## Inputs (provided by the plugin script)

- `{model_name}` — model class name (PascalCase, e.g. `Order`)
- `{model_file}` — path to the model PHP file
- `{module_name}` — module slug (or empty for flat)
- `{module_root}` — module root path (or empty for flat)
- `{project_type}` — `modular` or `flat`
- `{locale}` — output language
- `{output_file}` — final markdown file path

---

## Mission

Produce a **practical Nova admin guide** for `{model_name}` in `{locale}`.
The reader is an **end user of the admin panel** — operations team, support
staff, content manager. They do not write code; they click buttons.

Write in `{locale}` with **proper diacritics**.

---

## What to read

1. **Nova resource**:
   - Flat: `app/Nova/{model_name}.php`
   - Modular: `{module_root}/src/Nova/{model_name}.php`
2. **Nova actions**: `…/Nova/Actions/`
3. **Nova filters**: `…/Nova/Filters/`
4. **Nova lenses**: `…/Nova/Lenses/`
5. **Nova cards / metrics**: `…/Nova/Cards/` or `…/Nova/Metrics/`
6. **Translations** for screen titles and labels:
   - Flat: `resources/lang/{locale}/{model_snake_case}.php`
   - Modular: `{module_root}/resources/lang/{locale}/{model_snake_case}.php`
7. **Policies**: who can do what

Then build the navigation guide using **translated labels** wherever
available — admins see the translated UI, not the English class names.

---

## What this document MUST include

- **Where to find the screen** (menu path, URL pattern)
- **What every screen shows** (index, detail, create, edit)
- **What every filter does** (in plain language)
- **What every action button does** — including confirmation behavior and
  side effects
- **Permission requirements** if not everyone can use a feature
- **Workflow scenarios** — "How do I do X" walkthroughs
- **Screenshot placeholders** for future visuals

## What this document MUST avoid

- No PHP code blocks
- No Nova internal class names (`Boolean::make`, `BelongsTo`, …) in the text
- No HTTP / API talk
- No mention of "Eloquent", "Observer", "Job" — just describe the user-visible effect

---

## Document structure (in `{locale}`)

```markdown
# {TranslatedLabel} ({model_name}) — Admin guide

## Overview
A short paragraph: what this section of the admin is for, who uses it.

---

## Navigation
- **Menu**: Sidebar → {TranslatedLabel}
- **URL**: `/nova/resources/{resource_uri_key}`
- **Required permission**: {policy ability if any}

---

## Screens

### 1. List of {TranslatedLabel} (Index)
> ![Screenshot placeholder](TODO-screenshot-index.png)

**What you see:**
- Table with columns: {list translated column labels visible on index}
- Pagination at the bottom
- Search box at the top right
- Filters sidebar (see below)

**What you can do here:**
- Click **{TranslatedLabel}** in a row to open detail
- Click **Create** (top right) to add a new entry
- Tick checkboxes to select multiple rows → batch actions appear at the top

### 2. Detail
> ![Screenshot placeholder](TODO-screenshot-detail.png)

**What you see:**
Sections / tabs:
- **{Tab name}** — {what's in this tab, plain language}
- **{Tab name}** — …

**What you can do here:**
- **Edit** — change the entry (top right)
- **Delete** — remove the entry (with confirmation)
- Run **actions** (see Actions section below)

### 3. Create / Edit form
> ![Screenshot placeholder](TODO-screenshot-form.png)

**Fields you fill in:**
| Field (translated) | What to enter | Required? | Notes |
|--------------------|----------------|-----------|-------|
| Customer name | Full name of the customer | Yes | Used on the invoice |
| … | … | … | … |

**Buttons:**
- **Save** — saves the entry and returns to detail
- **Save & Add Another** — saves and opens a fresh form
- **Cancel** — discards changes

---

## Filters
Each filter narrows down the index list.

| Filter (translated) | What it does | When to use |
|---------------------|---------------|-------------|
| Status | Show only entries in a specific status | "Show me only paid orders" |
| Date range | Show entries created in a range | Monthly reports |
| … | … | … |

---

## Actions
Buttons that perform an operation on one or more entries.

### {Translated action name}
- **Where**: detail page / index batch / both
- **When available**: e.g. only when status is "New"
- **What it does**: plain language description
- **After running**: what changes (status update, email sent, file generated…)
- **Permissions**: who can run it
- **Confirmation**: does it ask before running?

### {Translated action name}
…

---

## Lenses (special views)
> Lenses are alternative pre-filtered views of the same data.

### {Lens name}
- **What it shows**: e.g. "Only overdue invoices"
- **When to use**: e.g. for daily collection follow-up

---

## Workflows
Step-by-step guides for common tasks. Use only **translated labels** and
**user-visible buttons**.

### Workflow: How to create a new {TranslatedLabel}
1. Click **{TranslatedLabel}** in the sidebar.
2. Click **Create {TranslatedSingular}** in the top-right corner.
3. Fill in the form (see Create form above).
4. Click **Save**.
5. You'll be redirected to the detail page of the new entry.

### Workflow: How to cancel a {TranslatedSingular}
1. Open the entry detail.
2. Click the **Cancel** action button.
3. Confirm in the dialog.
4. The status changes to "Cancelled" and the customer receives an
   automatic notification email.

### Workflow: …

---

## Tips & gotchas
- {Translated label}: this filter combines with text search — if results
  are empty, check both filters
- Some actions are only available for specific statuses; check the Actions
  section above
- Bulk actions: select checkboxes first, then choose the action from the
  dropdown at the top
- …

---

## Permissions overview
| Role | Can view | Can create | Can edit | Can delete | Can run actions |
|------|----------|-------------|----------|-------------|------------------|
| Admin | ✓ | ✓ | ✓ | ✓ | ✓ |
| Operator | ✓ | ✓ | ✓ |  | limited (see Actions) |
| Viewer | ✓ |  |  |  |  |

(Adjust to actual policies found.)
```

---

## Output

Write the document to:
```
{output_file}
```

If a translated label is available, rename to:
`{output_file_dir}/{TranslatedLabel} ({model_name}).md`

**Return only:**
```
✅ Created: <relative path>
```

---

## Tone & style
- **You-form** ("You'll see…", "You can…") — instructional
- **Concrete UI labels** — quote button names exactly as the admin sees them
- **Step-by-step** for any multi-action task
- **Plain language** — no developer jargon

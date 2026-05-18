# Business specification prompt — laravel-docs

This is the **default business prompt** for the laravel-docs plugin.
It generates documentation aimed at a **client / business stakeholder** —
the person who pays for the system but does not read code.

## Inputs (provided by the plugin script)

- `{model_name}` — model class name (PascalCase, e.g. `Order`)
- `{model_file}` — path to the model PHP file
- `{module_name}` — module slug (or empty for flat)
- `{module_root}` — module root path (or empty for flat)
- `{project_type}` — `modular` or `flat`
- `{locale}` — output language (`sk`, `en`, `cs`, …)
- `{output_file}` — final markdown file path

---

## Mission

Write a **business-friendly description** of the `{model_name}` module in
language `{locale}`. The reader is a **product owner, account manager, or
end client** — they understand the business, **not** the code.

Write in `{locale}` with **proper diacritics** (Slovak: áčďéíĺľňóôŕšťúýž).
Never strip accents.

---

## What this document MUST avoid

- **Zero code blocks** (no PHP, SQL, JSON, YAML)
- **Zero database / migration / column / SQL talk**
- **No "Observer", "Service", "Job", "Listener", "Controller", "Resource"** terminology
- **No HTTP / API endpoint references** ("POST", "endpoint", "route")
- **No PHP class names** unless they are domain terms the client already uses
- **No mention of Laravel, Nova, Eloquent, ORM, framework**

If the underlying behavior matters, **translate it into product language**:
| ❌ Technical | ✅ Business |
|------------|-------------|
| "Observer fires `OrderCreated` event" | "When an order is created, the system automatically sends a confirmation email" |
| "API endpoint POST /api/v1/orders" | "Customer submits the order form" |
| "Cancels via `OrderCancelUnpaidJob`" | "Unpaid orders are automatically cancelled after 30 minutes" |
| "Validation: required\|numeric\|min:1" | "The customer must enter a positive number" |

---

## Phase 1 — Understand the module

To write good business prose you still need to read the code, but you
**never expose it**. Read:

1. The model (`{model_file}`) — for fields and relations
2. Translations — for human-readable field names
3. Nova resource, actions, filters — for what users can do in the admin
4. Observer / Listeners / Jobs — for automatic behavior
5. Migrations — for what data we keep

Then map everything to **business concepts** the client understands.

---

## Phase 2 — Document structure

Use this skeleton (in `{locale}`). Adjust sections to fit the module —
not every module has external integrations, etc.

```markdown
# {TranslatedLabel} ({model_name})

## What this is
A 2-4 sentence plain-language description of the module's purpose.
What does it represent in the business world? Why does it exist?

---

## Who works with it
| Role | What they do |
|------|--------------|
| (e.g. Customer) | Creates a new order on the website |
| (e.g. Operator) | Confirms order, prints ticket |
| (e.g. Manager) | Reviews monthly reports |

---

## What information we track
Plain language list of the data we keep about each entity. **No technical
column names** — use translated field labels. Group logically.

**Basic information**
- Customer name and contact (email, phone)
- Address for delivery / pickup
- …

**Order details**
- Items ordered (with quantity and price)
- Total amount
- …

**Status**
- Current state (e.g. New, Paid, Cancelled, Completed)
- When created / last updated

---

## How it works — main scenarios
Describe each scenario in **plain English/Slovak/Czech**. No code, no
internal events. Just: who does what, what happens next.

### Scenario 1: {plain title, e.g. "Customer places an order"}
1. Customer fills the order form on the website.
2. System checks availability and calculates the price (including discounts).
3. Customer receives an order confirmation email with a payment link.
4. After payment, the order is marked Paid and a ticket is generated.
5. The customer receives the ticket as a PDF attachment.

**Alternative flow** — if payment is not received within 30 minutes, the
order is automatically cancelled and the seat is released.

### Scenario 2: {…}

---

## Rules and limits
Plain-language list of what the system enforces. Examples:
- Each order must contain at least one item.
- The customer must provide a valid email and phone number.
- An order can be cancelled only while it is in the New or Pending state.
- Discount codes expire after the configured date.

---

## How this connects to other parts of the system
Describe relationships in business terms — **not** "has_many" / "belongs_to".

- Each order belongs to a **customer** (we keep their history of orders).
- An order contains one or more **tickets** — printed and sent to the customer.
- Payments are processed through **{payment gateway name}**.
- After payment the order generates an **invoice**.

---

## Automatic actions
Plain-language list of things the system does **without manual input**.
- New orders confirmed by email immediately.
- Unpaid orders cancelled after 30 minutes.
- Daily summary of new orders sent to the operations team.
- …

---

## Frequently asked situations
Edge cases written as Q&A.

**Q: What happens if a customer pays twice?**
A: The system detects the duplicate payment and refunds the second one
automatically. Operations team is notified.

**Q: …**

---

## Glossary
| Term | Meaning |
|------|---------|
| Order | A request from a customer to buy goods or services |
| Status | Current stage of the order (New, Paid, Completed, Cancelled) |
| … | … |
```

---

## Output

Write the document to:
```
{output_file}
```

If a translated label is available, rename the file to include it:
`{output_file_dir}/{TranslatedLabel} ({model_name}).md`

**Return only a short confirmation:**
```
✅ Created: <relative path>
```

---

## Tone & style
- **Plain language** — like explaining to a smart non-developer at lunch
- **Short sentences** — one idea per sentence
- **Concrete examples** — "Cancelled after 30 minutes" is better than "Cancelled after a timeout"
- **Active voice** — "The system sends an email" not "An email is sent"
- **No jargon** — if the client wouldn't use the word, find a different one

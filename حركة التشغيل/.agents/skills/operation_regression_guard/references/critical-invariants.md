# Critical Invariants

## Source of truth

- `templates/base.html`: shared `window.OperationPrint` implementation for table printing, margin controls, row density, header and footer notes, and page options.
- `operation_app.py`: printable routes, `/api/settings`, and report context wiring.
- `operation_storage.py`: database initialization, mojibake repair, date normalization, and settings persistence.
- `static/print.css`: global print defaults for RTL tables and signatures.

## Existing guarded templates

- `templates/payment_receipt.html`
- `templates/accounting_statement_receipt.html`
- `templates/statement_report.html`
- `templates/manufacturer_accounts.html`

These templates already contain `GUARD:` comments around signature or print-sensitive blocks. Prefer surgical edits inside those blocks.

## Settings contract

- Shared database-backed keys:
  - `statement_header_note`
  - `statement_footer_note`
- Shared browser keys:
  - `print_show_time`
  - `print_show_page_numbers`
  - `print_landscape`
  - `global_print_row_padding_pt`
  - `print_margin_top_mm`
  - `print_margin_right_mm`
  - `print_margin_bottom_mm`
  - `print_margin_left_mm`

If one side changes, update every reader, writer, default, and printed output that depends on it.

## Layout consistency contract

- Good visual coordination is a requirement, not a cosmetic extra.
- If two cards live in the same row and belong to the same visual level, compare them as a pair:
  - header height
  - top and bottom padding
  - title baseline
  - action-group alignment
  - fold or toggle hit-area height
- Differences between adjacent cards should be intentional and explainable, not accidental side effects of content length or button count.
- When a consistency fix is needed, prefer one shared rule that normalizes siblings together.
- Use page-scoped rules when the adjustment is local to one screen; use shared styles only when the pattern is truly global.

## Regression checklist

### After `templates/base.html` or table-print changes

- Open a page that uses `OperationPrint.initPrintSettings(...)`.
- Toggle printed columns and confirm columns with `data-print="no"` stay excluded.
- Change row height and margins, then confirm the printed output reflects them.
- If privacy mode is enabled, confirm protected price columns stay hidden.

### After new page design or card-header alignment changes

- Check adjacent cards in the same row at a glance before focusing on details.
- Confirm peer cards have a consistent visual rhythm even if their internal content differs.
- Confirm foldable headers feel like equally sized click targets when they sit beside each other.
- Confirm the alignment fix did not change unrelated card body, print, or behavior logic.

### After printable template changes

- Open `/print-payment/<id>` and confirm both signature lines are visible, centered, and solid black.
- Open `/accounting-statement/<id>?pwd=<admin-password>` and confirm footer note, totals, and signatures render correctly.
- Confirm muted or semantic Bootstrap colors do not appear faded in print output.

### After storage or encoding changes

- Verify Arabic names and statuses loaded from SQLite display correctly in the UI.
- Confirm old mojibake values still recover through `_decode_mojibake_text`.
- If a new date field was added, confirm it is normalized consistently with existing date columns.

---
name: Operation Regression Guard
description: Guardrails for the operation tracking project to prevent reintroducing solved regressions in the unified print engine, Arabic text and encoding repair, accounting and receipt reports, settings synchronization, and visual layout consistency. Use when modifying `templates/base.html`, `templates/manufacturer_accounts.html`, `templates/payment_receipt.html`, `templates/accounting_statement_receipt.html`, `templates/statement_report.html`, `static/print.css`, `operation_app.py`, or `operation_storage.py`, or when designing a new page that should match the existing card and foldable-header rhythm.
---

# Operation Regression Guard

Treat the existing print, report, and Arabic-data paths as protected behavior. Reuse current helpers before adding local replacements.

## Protect the unified print engine

- Treat `window.OperationPrint` in `templates/base.html` as the source of truth for table printing.
- Keep these keys aligned wherever they are read or written: `print_show_time`, `print_show_page_numbers`, `print_landscape`, `global_print_row_padding_pt`, `print_margin_top_mm`, `print_margin_right_mm`, `print_margin_bottom_mm`, `print_margin_left_mm`, `statement_header_note`, `statement_footer_note`.
- Preserve `data-print="no"` handling, `enforcePrivacy`, `priceColumnMapping`, width sync from `colgroup` or header widths, and the shared row-padding behavior.
- Use `OperationPrint.initPrintSettings(...)` and `OperationPrint.printTable(...)` for new table print features instead of cloning inline print logic.

## Protect printable reports

- Keep signature areas self-contained inside printable templates. Do not depend on external CSS variables for signature visibility in popup or print windows.
- Preserve the current signature standard: flex column layout, centered solid black line, and enough vertical room for manual signing.
- Keep printed text and borders forced to black. Do not rely on Bootstrap semantic colors in printed output.
- Avoid duplicating date or time inside the report body when the shared print engine already renders it in the header or footer.

## Protect layout consistency

- Favor a good, unified layout over one-off visual fixes.
- When two or more cards appear in the same row and play comparable roles, align their header height, title baseline, action alignment, and fold-toggle hit area unless a different size is intentionally required.
- Treat the card header as a deliberate click surface. If adjacent foldable cards share the same visual tier, their clickable header area should feel equal in height and rhythm.
- Prefer a shared selector, shared class, or page-scoped rule for sibling alignment instead of ad hoc per-element styling scattered across the page.
- For new pages, establish consistent spacing, button sizing, card header density, and collapse behavior first; only then add exceptions.

## Protect Arabic text integrity

- Keep `_repair_text_encodings(...)` in both `initialize_database()` and `initialize_factories_table()`.
- Do not remove the CP1256 to UTF-8 mojibake recovery path in `_decode_mojibake_text` unless the replacement covers the same cases.
- When adding a new persisted Arabic text column, decide whether it belongs in `_repair_text_encodings(...)` or `_normalize_date_columns(...)`.

## Protect routes and settings

- Keep `operation_app.py` routes and template field names synchronized for printable pages.
- Keep `/api/settings` compatible with every frontend reader and writer of `statement_header_note` and `statement_footer_note`.
- Do not remove imports such as `get_factory_balance`, `get_accounting_statement_details`, `get_payment_receipt_data`, `get_setting`, or `set_setting` without checking every report or receipt flow that uses them.

## Work safely

1. Search for an existing helper or setting key before introducing new logic.
2. Edit the smallest safe block instead of replacing large print or template sections.
3. Keep or add `GUARD:` comments around critical print and signature blocks.
4. Read `references/critical-invariants.md` before large refactors or new page layout work in these files.
5. Run the matching regression checklist after edits.

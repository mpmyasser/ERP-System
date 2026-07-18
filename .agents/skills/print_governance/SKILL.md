---
name: Print Governance Skill
description: Instructions for maintaining and protecting the smart print system in DataTables.
---

# Print Governance Skill (مهارة حوكمة نظام الطباعة)

This skill defines the rules for modifying `app/static/js/datatables_init.js`, specifically the `customize` function inside the print button configuration.

## 🛡️ Protected Logic (الأجزاء المحمية)

The following logic blocks MUST NOT be replaced by generic code:

1.  **Smart Grouping Detection**: The code that uses `groupKeywords` to find the grouping column.
2.  **Sectional Printing**: The logic that splits data into `groups` and iterates over them.
3.  **Variable Initialization**: Always ensure `settings`, `$printBody`, `marginTop`, `marginBottom`, and `orientation` are defined at the very top of `customize`.
4.  **Subtotals and Grand Totals**: The footer calculation logic inside each group loop and the final grand total table.
5.  **Paper Saving (Continuous Flow)**: The use of `$groupWrapper` with `page-break-inside: avoid` instead of forced page breaks.
6.  **Column Width Sync**: The use of `_capturedWidths` to apply on-screen widths to print cells.

## ⚠️ Common Pitfalls (أخطاء شائعة يجب تجنبها)

> [!IMPORTANT]
> - DO NOT use `$(win.document.body).empty()` unless you immediately follow it with `.append($wrapper)`.
> - ALWAYS check that `settings` is parsed from `localStorage` before using any settings variable.
> - When adding new features, use `multi_replace_file_content` to surgically edit specific lines instead of replacing the whole `customize` block.

## 🖋️ Global Signature Standard (معيار التوقيعات الموحد)

Any report or document requiring signatures (Receipts, Statements, Vouchers, etc.) MUST adhere to the following global standard:

1.  **Strict Vertical Centering**: Signature lines MUST be perfectly centered between the label (e.g., "Receiver Signature") and the bottom edge of their container.
2.  **Container Height**: Signature boxes/containers MUST have a minimum height of `85px` to ensure adequate space for centering and manual signing.
3.  **Self-Containment (العزل التام)**: DO NOT rely on external CSS variables (like `var(--sig-line-style)`). Hardcode the style directly in the template's style block to ensure visibility in independent print windows.
4.  **High-Contrast Lines**: Use `border-bottom: 2px solid #000 !important;` for all signature lines. They should have a width of `180px` and be centered horizontally within their box.
5.  **Layout**: Use `flexbox` with `flex-direction: column` and `justify-content: space-between` to push the label to the top and the line to the bottom of the container.
6.  **Zero Timestamp Redundancy (منع التكرار)**: DO NOT include date/time inside the report body if it exists in the header. The "Show Time" toggle must control both Date and Time together to optimize vertical space.
7.  **Reference Integrity (سلامة المراجع)**: Always re-initialize critical DOM references (e.g., Balance, Deduction, Totals) locally inside the click/print handler. This prevents data loss if global pointers are shadowed or lost during refactoring.
8.  **Smart Advance Hiding (الإخفاء الذكي)**: Advance/Balance cards in "Quick Reports" should ONLY be hidden if ALL three values (Previous Balance, Deduction, Balance After) are exactly zero. This logic must be preserved to maintain financial transparency.
9.  **Backend Connectivity Integrity (سلامة الاتصال بالخلفية)**: Core financial functions (especially `get_factory_balance`) are the heart of the system. NEVER remove or modify their imports in `operation_app.py` without verifying that all accounting modules (Summary Bar, Reports, Archives) still function.
10. **Print Contrast & Formatting (جودة التباين والخطوط)**: All financial values in printed reports MUST be forced to deep black (`#000 !important`). NEVER use Bootstrap color classes (`text-success`, `text-warning`) in printed output as they appear faded. Signature lines MUST be solid (`1.5px solid #000`), never dotted or light gray.
11. **Flexible Row Height (التحكم في ارتفاع الصفوف)**: Users can control vertical density for printing via a slider. This is implemented globally using the `global_print_row_padding_pt` key in `localStorage`, the `--table-row-padding-pt` CSS variable, and the `rowPadding` configuration in `printTable`. NEVER hardcode fixed vertical padding in table styles that might override this universal user preference.
## ⚡ Token Efficiency Mode (وضع ترشيد التوكينات)

When working on this project, prioritize token efficiency without sacrificing correctness.

### Context Usage
1. Read the minimum number of files required.
2. Avoid scanning unrelated directories.
3. Prefer targeted searches over full project analysis.
4. Reuse already discovered context whenever possible.

### Code Modification Strategy
1. Modify the smallest possible code region.
2. Prefer surgical edits over full-block replacements.
3. Preserve existing architecture and naming conventions.
4. Do not refactor unrelated code.

### Response Policy
1. Do not explain completed changes unless requested.
2. Do not generate implementation plans unless the task is ambiguous.
3. Do not repeat user requirements.
4. Keep status updates under 30 words.
5. Prefer action over discussion.

### File Access Policy
1. Open only files directly related to the requested task.
2. Avoid reading backup files unless explicitly required.
3. Avoid re-reading files already analyzed.

### Print System Exception
Token optimization MUST NEVER justify bypassing or simplifying:

- Smart Grouping Detection
- Sectional Printing
- Subtotals / Grand Totals
- Column Width Sync
- Signature Standards
- Financial Calculations
- Backend Connectivity Integrity

Protected print logic always takes priority over token savings.

### Completion Format

Success:
DONE

Blocked:
BLOCKED: <reason>
## 🛠️ How to Add a Feature (كيفية إضافة ميزة جديدة)

If you need to add a new print option:
1.  Update the settings panel to add the UI element.
2.  Update the event handler to save the value to `localStorage`.
3.  In the print logic, read the value and apply it surgically.
4.  **GUARD COMMENTS**: When editing critical print blocks, wrap them in comments:
    `/* GUARD: CRITICAL PRINT LOGIC - DO NOT REMOVE */`
5.  **REGRESSION CHECK**: Always compare the new output with `manufacturer_accounts.html.before_compact_print.bak` to ensure no original logic was lost.

---
*Created: 2026-03-24*

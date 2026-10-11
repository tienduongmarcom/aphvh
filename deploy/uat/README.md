# APH–VH–MK–TL candidate UAT

This branch is an opt-in candidate, not a production release. Base source was verified against the UAT export recorded in candidate-20261011.json. The later credit bypass patch has separately verified runtime SHA256 values recorded there. Native ERPNext/Frappe DocType dumps are evidence only and must not overwrite core schemas.

The approved new coordinator creates company-specific Sales Orders. Dispatch posts a submitted receivable SI without a second stock posting. Global warnings use receivable GL across APH/VH/MK/TL and already include verified-customer unallocated receipts. High-risk customer shipments require a matching, unrevoked chief approval.

## Explicit setup in a fresh, isolated UAT clone

Use only site aphvh-web-uat, Administrator, the exact candidate code, and a restored blank baseline. No after_install/after_migrate enables these features. No automatic production schema installer is added. Feature flags must be explicitly set in the UAT site's private config:

- kh_aph_server_cost_guard = 1
- kh_aph_post_receivable_on_delivery = 1
- kh_aph_shared_sales_order = 1
- kh_aph_global_credit_warning = 1
- kh_aph_high_risk_credit_guard = 1

Then run from the bench directory:

```sh
bench --site aphvh-web-uat execute kh_aph.uat_candidate_setup.setup_uat
bench --site aphvh-web-uat clear-cache
```

Reload only the isolated UAT workers. The explicit setup preserves native permissions, installs 13 candidate custom fields and the approval audit DocType, and adds only Delivery Note read at level0 for Accounts Manager. The production frontend is explicitly rejected.

Fresh-image/site verification succeeded: 152 kh_aph + 48 lab9x tests, candidate setup with idempotent repeat, 46 HTTP business cases and database/series restoration. Evidence: https://github.com/tienduongmarcom/aphvh/actions/runs/38134304280 . This run also generated a four-company PDF; the later A4 style refinement is checked separately.

## Delivery and quantity slips

Warehouse users confirm handoff or pickup through the Delivery Note buttons. Handoff submits the native company DN and its accounting-only SI in the same request; pickup goes straight to received. Native submit defaults to in transit. Sales users who can read that DN may confirm receipt through the dedicated endpoint; this does not grant native write/submit permissions. The endpoint accepts only a name/action, loads the trusted document, stamps the three delivery fields, and preserves native read scope. Version history records state changes.

On a submitted shared order, select company delivery batches under Print to generate a quantity-only consolidated slip. Individual Delivery Notes retain their existing print formats. Consolidation checks permissions and shared-order membership for every selected DN, preserves source company/warehouse and makes no stock/accounting writes. A4 is specified by the print CSS.

HTTP evidence includes eight deliveries for APH/VH/MK/TL under the warehouse role, receipt by the read-only sales role, generic-write and unrelated-role denial, four-company stock/debt checks and consolidation under the warehouse role. Restore verification includes shared order/child tables, custom fields and Version counts. These are simulated UAT users, not actual Dung/chief identities.

## Remaining gates before release

Direct Sales Invoice bypass and unauthorized customer-control edits passed the specified HTTP cases. Other credit paths still require review. Actual Dung and chief-accountant identities, concurrent approve/revoke/dispatch behavior, and the user interface remain unverified. Shared-order bag conversion, delivery workflow/slips, pending valuation, manufacturing/byproducts and deposit allocation are not fully accepted. The complete 202 numbered decisions were not available for full reconciliation. Do not merge, tag or deploy automatically.

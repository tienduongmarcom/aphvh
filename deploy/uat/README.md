# APH–VH–MK–TL candidate UAT

This branch is an opt-in candidate, not a production release. Source hooks/coordinator/credit modules are byte-for-byte copies of the verified UAT export recorded in candidate-20261011.json. Native ERPNext/Frappe DocType dumps are evidence only and must not overwrite core schemas.

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

Reload only the isolated UAT workers. The explicit setup preserves native permissions, installs 10 new custom fields and the approval audit DocType, and adds only Delivery Note read at level0 for Accounts Manager. The production frontend is explicitly rejected.

The exported existing UAT candidate passed 23 business cases plus data/series restoration. This new consolidated setup has not yet been exercised in a fresh image/site; do not label clean-image reproduction PASS until that test runs.

## Remaining gates before release

Direct Sales Invoice/other credit paths and unauthorized customer-control edits must be tested. Actual Dung and chief-accountant identities, concurrent approve/revoke/dispatch behavior, and the user interface remain unverified. Shared-order bag conversion, delivery workflow/slips, pending valuation, manufacturing/byproducts and deposit allocation are not fully accepted. The complete 202 numbered decisions were not available for full reconciliation. Do not merge, tag or deploy automatically.

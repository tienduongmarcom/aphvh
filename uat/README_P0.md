# P0 UAT candidate — not released

Base: kh_aph v0.9.1, a140661e343f5efc114b7cf402ddc24e10c2ff27.
Observed runtime: Frappe16.35.0/ERPNext16.36.1. Target Frappe16.36.1 not yet verified.

## Changes

- Opt-in site config kh_aph_post_receivable_on_delivery defaults off. DN on_submit uses an accounting SI submitted within the dispatch transaction, update_stock=0; errors propagate, so the request must roll back. No MISA call or historical auto-submit. Partial/mixed prior billing fails closed pending reconciliation. A return requires exactly one posted original; legacy flow unchanged when flag off.
- Opt-in kh_aph_server_cost_guard defaults off. Controller mixin masks cost on apply_fieldlevel_read_permissions used by client.get, Desk load and REST read. Site-local explicit apply_query_field_permissions raises cost fields to level9 and preserves level0 Custom DocPerm before adding authorized role permissions. No migration/install hook automatically applies it.
- Role overrides remain the existing policy: Accounts/Stock/Purchase Managers etc may see cost even with a hidden role. Dũng's actual account/role has not been verified. Do not declare Dũng secured until approved role/identity tests pass.

## Local validation

113 kh_aph tests +48 lab9x tests OK; 12 new behaviour tests cover masks/quantity/sales price/admin/flags, posting failure/retries/draft safety/return ambiguity. These mocks do not replace Frappe integration.

## Isolated runtime test

APHVH_P0_UAT.py embeds the candidate modules. Run it only through the supplied docker exec on aphvh-uat. It replaces modules/controllers in that short-lived Python process, not shared app files, and prohibits DB commit. All fixture/Property Setter/Custom DocPerm writes rollback. It compares 16 table counts and naming series before/after. Emails muted; no password is created.

The process-local runner tests document reads, child-cost query, admin cost access, dispatch GL vs expected amount, unchanged stock count, repeat-hook idempotency and intentional invoice-posting failure. Hook binding/mixin loaded by actual deployed hooks, web request transaction, cross-worker races, returns/cancel and broad API/export/report routes still require an isolated candidate image before release.

## Open gates

Runtime tests not yet executed for candidate. Existing v0.9.1 showed FAIL on cost read and debt0 vs80000 after DN.
Raw SQL reports, report/export aliases/filters, purchase-price/OPEX exceptions, Stock Ledger/Bin direct queries, Version/history/attachments and custom endpoints are not fully secured by this scoped patch. These remain P0 validation/remediation gates; do not say full cost protection is complete.
Do not upgrade shared backend source or run migrate against frontend. No release tag, production deploy or automatic historical invoice submission is included.

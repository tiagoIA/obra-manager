# Material photo coverage target

Target set: 2026-10-08.
Status: OPEN — the target is not yet achieved.

## Acceptance criterion

Every active material must have a relevant, readable photo. Inactive/deleted materials are excluded from this target. Do not deactivate records merely to improve the photo coverage metric.

Verified current inventory (read-only audit run 37861255934):
- 524 catalog records.
- 468 active material records.
- 322 active records with a photo.
- 146 active material records without a photo.
- 45 inactive records without a photo, excluded from the target.

## Work sequence

1. Recheck the current Firestore record before preparing each update.
2. Prioritize exact model/part matches from manufacturer or supplier sources.
3. For a generic family record, a representative real product photo may be used only with an explicit English family-reference note; do not assert that it identifies a particular model, package, gauge or compatibility.
4. Keep ambiguous names/codes as identification blockers until resolved; do not insert unrelated images, logos, placeholders or generated product photographs.
5. Back up before writing, use optimistic document preconditions, update only photo/provenance fields, and preserve stock, IDs, codes and history.
6. Validate image downloads, file formats and meaningful dimensions; inspect the candidate image and record the source and hash.
7. After each batch, re-read the catalog, check all updated photos, and report the actual active backlog. The target is complete only when the active backlog is zero.

## Identification issues already visible

Names such as "Febwfbew", "Switch 6 normal", "Outlet 24 unid", "uninstructed clamp" and "Pipe Lines for Smoke 120V" do not identify an exact product. The MAT records HP362N, K2A250, RG36 and QA1154FC also require careful part-code reconciliation rather than substitution based on similar model numbers.

No photo or status changes were made by the target-setting audit.

# Material photo coverage target

Target set: 2026-10-08.
Status: OPEN — the target is not yet achieved.

## Acceptance criterion

Every active material must have a relevant, readable photo. Inactive/deleted materials are excluded from this target. Do not deactivate records merely to improve the photo coverage metric.

Initial inventory (read-only audit run 37861255934):
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

## Current verified coverage — 2026-10-09

Read-only audit [37877300976](https://github.com/tiagoIA/obra-manager/actions/runs/37877300976):
- 524 catalog records; 468 active materials.
- 462 active materials have readable photos; 6 remain without photos.
- 140 photos added since the initial audit; 0 failed image downloads in this audit.
- No records were deactivated to improve coverage.
- Representative images are marked as family references and do not verify exact models, sizes or compatibility.

### Identification blockers

| SKU | Material ID | Existing name | Information required |
| --- | --- | --- | --- |
| ELEC-196 | 6Slgo0bUln1R3rBe8RY5 | uninstructed clamp | Correct clamp type, manufacturer or part number |
| ELEC-027 | AvymoHXdWiMfhrcGMqMm | point of attachment | Actual hardware type and model |
| FIRE-045 | HAvsU3Xkf359Tkbs5kwO | Pipe Lines for Smoke 120V | Whether this is a physical material or a work item; actual product name |
| ELEC-068 | ih7gJ4TXKQSd5MN3h8KH | Pipe lines for smoke’s 120volt | Whether this is a physical material or a work item; actual product name |
| ELEC-070 | rwX7nGbTG9yI2RDM1YkO | Febwfbew | Correct product name |
| FIRE-015 | vkIv9XEz6Az7A7x3mM7m | B300-16 white | Manufacturer and exact part number/product type |

Do not infer identity from previously generated descriptions. These records remain active and unchanged pending identification.

## Earlier identification issues

Names such as "Febwfbew", "Switch 6 normal", "Outlet 24 unid", "uninstructed clamp" and "Pipe Lines for Smoke 120V" do not identify an exact product. The MAT records HP362N, K2A250, RG36 and QA1154FC also require careful part-code reconciliation rather than substitution based on similar model numbers.

The initial target-setting audit made no photo or status changes. Subsequent approved batches applied photo-only updates with backups and protected-field verification; the target remains open until all six blockers are resolved.

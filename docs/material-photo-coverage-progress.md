# Material photo coverage progress — 2026-10-09

Status: OPEN — six active materials require identification.

## Verified work

140 previously missing photos were added. Of 468 active materials, 462 have readable photos and six remain without photos. All 524 catalog records remain present.

Four existing wrong-family images were corrected:
- MAT-56D354B6E3C0: replaced a jacketed multiconductor cable image with a THHN wire family reference; pictured 12 AWG example is explicitly distinguished from the 14 AWG record.
- ELEC-038: replaced an EMT image with a PVC conduit family reference.
- FIRE-091: replaced a battery image with a power supply board family reference; pictured 2.5 A example is explicitly distinguished from the 12 V 6 A record.
- ELEC-040: replaced a metal LB image with a manufacturer specification photograph of Carlon E986D PVC Type LB conduit body.

MAT-8EBCE853D091 retained its existing NM-B family image, with an explicit note distinguishing the pictured 12/2 cable from the 4/3 125-ft record.

Family references are not exact-model verification. Product identity, manufacturer part fields, stock, status, IDs and history were preserved.

## Verification and backups

| Operation | Verified run | Backup folder in private project bucket |
| --- | --- | --- |
| Three wrong-family replacements | [37877695432](https://github.com/tiagoIA/obra-manager/actions/runs/37877695432) | backups/photo-coverage/37877695432/ |
| NM-B family annotation | [37877752328](https://github.com/tiagoIA/obra-manager/actions/runs/37877752328) | backups/photo-coverage/37877752328/ |
| PVC LB replacement | [37877783716](https://github.com/tiagoIA/obra-manager/actions/runs/37877783716) | backups/photo-coverage/37877783716/ |

Each operation backed up materials, shoppingLists, shoppingItems, tasks, productDB, invoices and invoiceItems. Original image SHA-256 guards reject stale replacements; Firestore update-time preconditions reject concurrent document changes. Post-write comparisons validated all 524 material records outside the photo/provenance/update-time fields.

See [material-photo-coverage-target.md](material-photo-coverage-target.md) for the six unresolved records and required identification. No record was deactivated solely to improve coverage.

## Final asset audit

Read-only audit [37877815178](https://github.com/tiagoIA/obra-manager/actions/runs/37877815178) completed successfully after all corrections: 524 catalog records, 468 active materials, 462 readable photo assets, 6 missing photos and 0 failed assets. Coverage is 98.72%; the target remains open pending identification of the six records.

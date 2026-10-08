# English catalog and material lifecycle release

Published and verified: 2026-10-08 (UTC).
Site: https://obra-manager-4ecc7.web.app/
Verified release: https://github.com/tiagoIA/obra-manager/actions/runs/37860645847
Source branch: `feature/lista-guiada-v1`.
Hosting version: `sites/obra-manager-4ecc7/versions/6f8d5702a91dd019`.

## Completed implementation stages

1. English material, guided shopping and catalog interface copy; reviewed catalog descriptions/specification labels and built-in starter templates. Internal IDs, SKUs and manufacturer codes remain unchanged. Existing user-authored history and custom text are retained.
2. Active/inactive lifecycle with Active, Inactive and All materials filters. Owner-only deactivation/reactivation. Inactive material IDs are retained in existing purchases, tasks and exports, but excluded from new material selections.
3. Generic record review with stock protection and explicit identification warnings. Candidate products are review choices, not equivalence mappings. No automatic inventory transfer or history relinking.
4. Reviewed supplier variants: 23 breaker candidates and 8 hardware candidates. 29 new products and 2 existing product matches; no skipped candidates.
5. Verified source references and photo hashes for this batch. Dottie family reference photographs are labeled; unknown photos or product identities are not invented.
6. Shared catalog integration for guided lists, custom lists, manual entry, task selection, shopping search and purchase PDFs. Existing customized lists and historical references are preserved.
7. Browser, mobile layout, edit/status/search, historical references, PDF, duplicate identity, syntax and migration guard checks passed before publication. The four deployed assets were fetched and byte-verified after release. All 74 hosting assets were retained.

## Verified results

| Measure | Result |
|---|---:|
| Catalog records before | 495 |
| Catalog records after | 524 |
| New specific products | 29 |
| Existing product matches | 2 |
| Generic records reviewed | 131 |
| Generic records deactivated | 56 |
| English material record updates | 145 |
| English built-in templates updated | 12 |
| Active material records | 468 |
| Inactive material records | 56 |
| Records with photos | 333 |
| Records without photos | 191 |

The 191 records without photos remain open identification/enrichment work. This release does not claim complete coverage of every supplier, product family or market variant. Reviewed generics without suitable candidates, or with physical stock requiring identification, remain available with review warnings.

## Supplier coverage and remaining work

Electric Supply Center appears on 33 historical supplier rows; its public site presented an additional security check, so its full live catalog was not collected. Granite City Electric has 82 existing supplier catalog references retained in the library. This batch uses Electrical Wholesalers NE as a supplemental public source, not evidence that it is the user's primary purchasing supplier.

Reviewed batch parts:
- Siemens: Q115, Q120, Q230, Q240, Q250, Q260, QA115AFC, QA115AFCN, QA120AFC, QF120A, QF220A, QF240A, QF260A.
- Eaton: BR115, BR115CAFA, BR120, BR230, BR240, BR250, BR250H, BR260, BR260H, BR260ST.
- Dottie: PHSMSS8114, PMS6321, LWBZ58, FWBZ38, FWBZ12, HNBZ38, SA38300, SA14138.

Compatibility, package/order units and actual physical generic stock must be confirmed before selecting replacements. Manufacturer or supplier descriptions do not make candidate parts universally interchangeable.

## Preservation, backups and release recovery

All 495 existing material IDs were retained. Existing stock and fields outside the reviewed update masks were checked after the transaction. No purchase/task history was reassigned. Owner reactivation is available in the Inactive filter.

Private Firebase Storage backup paths:
- Data: `backups/catalog-lifecycle/37860645847/`
- Hosting: `backups/lifecycle-hosting/37860645847/`

Data backups cover materials, shopping lists/items, tasks, productDB and invoice records, plus prepared writes, commit results, receipt and pending identification report. Hosting backups retain the prior file map, configuration and four changed assets.

The initial run 37860329265 detected a Firestore serialization representation difference and automatically rolled back all 317 writes; rollback was verified. The verification was corrected to compare decoded values while still rejecting missing fields, then all tests and the migration/publication succeeded in run 37860645847.

## Deactivated records

These records retain their IDs and historical links. They had zero stock and specific product candidates in the relevant family; candidates are not automatic replacements.

| SKU | Material | Historical reference count |
|---|---|---:|
| ELEC-164 | Grounding Bushing 1/2" | 0 |
| ELEC-102 | 3-Gang Old Work Box | 0 |
| ELEC-149 | Emergency Light Twin Head | 0 |
| ELEC-148 | Exit Sign LED | 0 |
| ELEC-185 | Breaker AFCI 15 Amps  Siemens | 0 |
| ELEC-126 | EV Charger Outlet NEMA 14-50 | 0 |
| ELEC-145 | Recessed Can Light 4" | 0 |
| ELEC-123 | Dimmer Switch Single Pole | 0 |
| ELEC-172 | Concrete Screws 3in | 0 |
| ELEC-134 | Double Pole Breaker 50A | 0 |
| ELEC-188 | 4 in” Metal Pancakes box 1/2 k’Os 5.9 cu. in | 0 |
| ELEC-124 | Dryer Outlet 30A 240V | 0 |
| FIRE-079 | POE Switch 8-Port | 0 |
| ELEC-116 | GFCI Outlet 20A | 0 |
| ELEC-122 | 4-Way Switch 15A | 0 |
| ELEC-118 | USB Outlet Type A+C | 0 |
| ELEC-131 | Single Pole Breaker 15A | 0 |
| ELEC-189 | 4 in” round Fan box 1-1/2  in. Deep 15.3 | 0 |
| ELEC-147 | LED Shop Light 4ft | 0 |
| ELEC-125 | Range Outlet 50A 240V | 0 |
| ELEC-136 | AFCI Breaker Single Pole 20A | 0 |
| ELEC-156 | Cable Staples 3/4" | 1 |
| ELEC-154 | Wire Nut Red 16-10 AWG | 0 |
| ELEC-106 | 4" Square Box 1-1/2" Deep | 0 |
| ELEC-111 | Handy Box | 0 |
| ELEC-194 | Nut 3/8 | 0 |
| ELEC-152 | Wire Nut Orange 22-14 AWG | 0 |
| ELEC-180 | Dinner room outlet | 0 |
| ELEC-114 | Outlet Duplex 20A 125V | 0 |
| ELEC-117 | AFCI Outlet 15A | 0 |
| ELEC-105 | 3-Gang New Work Box | 0 |
| ELEC-107 | 4" Square Box 2-1/8" Deep | 0 |
| ELEC-120 | Single Pole Switch 15A | 0 |
| ELEC-186 | Breaker 20A GFCI Siemens | 1 |
| ELEC-175 | Lock Breaker | 0 |
| ELEC-109 | Weatherproof Box 1-Gang | 0 |
| ELEC-192 | SELF NAILING PLATE 1 1/2" X 5" 18GA | 0 |
| ELEC-153 | Wire Nut Yellow 18-10 AWG | 0 |
| ELEC-110 | Junction Box 4"x4" | 0 |
| ELEC-119 | Tamper Resistant Outlet 15A | 0 |
| ELEC-176 | Outlet 24-Pack | 0 |
| ELEC-150 | Outdoor Motion Sensor Light | 0 |
| ELEC-112 | PVC Device Box 1-Gang | 0 |
| ELEC-144 | Recessed Can Light 6" | 0 |
| ELEC-113 | Outlet Duplex 15A 125V | 0 |
| ELEC-115 | GFCI Outlet 15A | 0 |
| ELEC-138 | Dual Function AFCI/GFCI Breaker | 0 |
| ELEC-146 | LED Troffer 2x4 5000K | 0 |
| ELEC-137 | GFCI Breaker 2P 20A | 0 |
| ELEC-108 | 4" Octagon Box | 0 |
| ELEC-132 | Single Pole Breaker 20A | 0 |
| ELEC-195 | strut channel (Unistrut) | 0 |
| ELEC-133 | Double Pole Breaker 30A | 0 |
| ELEC-151 | Vapor Tight Fixture 4ft | 0 |
| ELEC-141 | Transfer Switch 30A Manual | 0 |
| ELEC-191 | 3/8” threaded rod | 0 |

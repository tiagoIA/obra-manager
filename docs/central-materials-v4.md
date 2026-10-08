# Central materials and purchasing v4

The existing Firestore `materials` collection remains the product catalog. Tasks link `materialId`; purchases link `matId`. Invoice vendor observations in `productDB` remain historical records and keep their existing material associations.

The central editor separates internal `sku`, manufacturer `brand`/`manufacturerPart`, UPC, and an extensible `suppliers[]` array (name, retailer code, URL, order unit, optional reference price/date). Existing IDs, stock quantities, supplier metadata, installation notes and old internal codes are retained. New products receive independent internal codes. Unknown store codes are not inferred.

The owner can create or edit products from Materials. Technical/installation tabs remain available through the editor. Guided lists show the same catalog photos and IDs, with editable service tags, manual items and custom reusable templates. Data/Cat6 and Solar presets supplement the existing ten presets.

Shopping PDF resolves photos/codes from current linked products. Consolidation keeps differing units and observations separate; a group is purchased only when all its lines are purchased. Modes remain store, by room and full. Supplier selection exposes missing codes clearly. Copy, WhatsApp and email open a text draft; saved PDFs can be attached manually.

## Import and release

`catalog-products-v1.json` contains 136 reviewed candidate references from public EW NE, Leviton Store and Platt catalogs. Placeholder images, mismatched brands and unrelated query results were removed. Classification is editorial; catalog presence is not confirmation of suitability or availability. No vendor prices, stock or automatic circuit sizing are imported.

The release verifies each reviewed image hash, uploads photos, deduplicates UPC/manufacturer/supplier identities, preserves existing stock/history, and performs one Firestore commit using existence/update-time preconditions. Unit/identity conflicts are skipped and recorded in a private receipt. Existing GCE references receive supplier metadata without renumbering IDs or internal codes.

Before mutation, Firebase Storage receives private backups of Hosting configuration/assets, index, materials, shopping lists/items, tasks, invoice observations and invoices under `backups/central-catalog/<run>/`. Hosting preserves all pre-existing asset paths and configuration. A live-index hash guard prevents overwriting a changed app. Published file bytes and preserved data are checked. Failure triggers Hosting rollback and optimistic database rollback, without overwriting later user edits.

## Validation

`tests/guided-shopping.cjs`: twelve presets, service filtering, photos, linked IDs, manual items, reusable models, existing purchase state, mobile layout.

`tests/central-catalog.cjs`: supplier metadata, role guards, duplicate internal/UPC/model keys, live photo/code resolution, quantity/unit/note and room/status preservation, safe markup, mobile layout and printable PDF.

Full application script syntax is checked before publishing. Research collectors are read-only and run separately from production deployment.

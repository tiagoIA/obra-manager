# Catalog expansion: staged discovery

Target: at least 3,000 distinct usable products in the existing library. Live count remains unverified. No live material writes in this stage.

Leviton official store discovery: 1,462 source products; 2,318 raw variants; 2,307 candidates after source-SKU deduplication. 94 candidates lack SKU; 16 lack an acceptable image after variant isolation. 708 candidates have two image references. Second photo is optional and never a blocking requirement. Images explicitly tied to a different variant are excluded. Shared images require review.

Source data: https://store.leviton.com/products.json?limit=250&page=1 through page=6. Retailer category maps: https://www.homedepot.com/b/Electrical/N-5yc1vZarcd and https://www.lowes.com/c/Electrical . Product candidates are gzip JSON; generator is scripts/stage_manufacturer_catalog.py.

Source SKU remains separate from confirmed manufacturer part. Purchase units, packages, category, dimensions and manufacturer part require source review. No guessed compatibility or dimensions. Before import, match existing products by verified manufacturer/model or barcode; supplier codes belong to separate store references. Preserve invoice price history and company permissions.

Continue with wire/cable, conduit, fittings, boxes/covers, breakers/panels, devices/plates, grounding/supports, lighting and job supplies, across manufacturers. Do not fill the target with colors or patch-cord variants from one manufacturer. Final count must exclude duplicates, unverified candidates and existing records.

Photo handling: retain existing primary photo; secondary reference optional, up to two distinct URLs per candidate. No image binary belongs in material documents. Gallery UI and live imports have not been changed in this branch.

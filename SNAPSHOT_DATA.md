# Snapshot data and integrity

The original review archive contains three complete catalogue JSON files (~15.6 MB each). They are intentionally not committed to this Git repository so that the review surface stays focused on the patches, implementation, evidence metadata, report, and verification logs.

Exact files from the 10 September 2026 archive:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `evidence/metadata.original.json` | 15,642,382 | `2551bb522f9462d001462243baa46739442899cf14d10c1405708e0f898f667f` |
| `metadata.six.corrected.json` | 15,641,994 | `8064bdef324d9a595c2d203a65563fe644ec6c222108c9784929145bdfb2b75b` |
| `metadata.seven.proposed.json` | 15,641,994 | `e765645dff297a24bcd648410605674965764897c52992f613e55d70fbdd8fbd` |

The uploaded source archive used for this publication was:

`Vesuvius_Catalogue_Repair_2026-09-10(4).zip`

SHA-256: `2807de7198d9dc4dc30d6aaa988a5389f6a5dc0888ca95f6ad55b42715682cce`

The captured source URL, retrieval time, ETag, response hash, decoded hash, and the four Zarr metadata sources are recorded in `evidence/manifest.json`.

## Refresh from the public source

To review against the current public catalogue rather than the historical snapshot:

```sh
python3 repair_catalogue.py snapshot --out fresh_evidence
python3 repair_catalogue.py apply \
  --evidence fresh_evidence \
  --catalogue fresh_evidence/metadata.original.json \
  --out reviewed.six.json \
  --patch reviewed.six.patch.json
```

The public source can change. A fresh download should not be described as byte-identical to the 10 September 2026 snapshot unless its SHA-256 matches the value above.

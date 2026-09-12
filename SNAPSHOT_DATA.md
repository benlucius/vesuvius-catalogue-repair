# Snapshot data and integrity

The full v1.0.0 release archive contains three complete catalogue JSON files (~15.6 MB each). They are intentionally not committed as plain files to the Git repository so the review surface stays focused on the patches, implementation, evidence metadata, report and verification results.

Full release archive:

`Vesuvius_Catalogue_Repair_v1.0.0.zip`

Direct asset URL (after the v1.0.0 GitHub Release is published):

`https://github.com/benlucius/vesuvius-catalogue-repair/releases/download/v1.0.0/Vesuvius_Catalogue_Repair_v1.0.0.zip`

SHA-256 of the final release ZIP prepared on 12 September 2026:

`89111968a070ce9bacfb6f3223c8335bab844fed894e4947dfa135e41ff14875`

Exact large files inside that archive:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `evidence/metadata.original.json` | 15,642,382 | `2551bb522f9462d001462243baa46739442899cf14d10c1405708e0f898f667f` |
| `metadata.six.corrected.json` | 15,641,994 | `8064bdef324d9a595c2d203a65563fe644ec6c222108c9784929145bdfb2b75b` |
| `metadata.seven.proposed.json` | 15,641,994 | `e765645dff297a24bcd648410605674965764897c52992f613e55d70fbdd8fbd` |

The original user-supplied archive used as the publication source was `Vesuvius_Catalogue_Repair_2026-09-10(4).zip`, SHA-256 `2807de7198d9dc4dc30d6aaa988a5389f6a5dc0888ca95f6ad55b42715682cce`.

The captured catalogue source URL, retrieval time, ETag, response hash and decoded hash are recorded in `evidence/manifest.json`. The four Zarr metadata sources are recorded there as well.

For exact regression-test reproduction, download and unpack the full v1.0.0 archive; a repository checkout alone intentionally omits the three large plain JSON snapshots.

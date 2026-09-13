# Snapshot data and integrity

[Download the published v1.0.0 ZIP](https://github.com/benlucius/vesuvius-catalogue-repair/releases/download/v1.0.0/Vesuvius_Catalogue_Repair_v1.0.0.zip).

Filename: `Vesuvius_Catalogue_Repair_v1.0.0.zip`  
Size: 3,605,910 bytes  
SHA-256: `3c65e001d54accba3d29c612635b00dab8f31466826f352a449f88e9b354068c`

This identifies the cleaned, published release asset. A GitHub-generated source archive is a different file and omits the complete catalogue snapshots. Extract the attached release ZIP and run from its top-level directory for offline reproduction.

| File inside the release | Bytes | SHA-256 |
| --- | ---: | --- |
| `evidence/metadata.original.json` | 15,642,382 | `2551bb522f9462d001462243baa46739442899cf14d10c1405708e0f898f667f` |
| `metadata.six.corrected.json` | 15,641,994 | `8064bdef324d9a595c2d203a65563fe644ec6c222108c9784929145bdfb2b75b` |
| `metadata.seven.proposed.json` | 15,641,994 | `e765645dff297a24bcd648410605674965764897c52992f613e55d70fbdd8fbd` |

Use `SHA256SUMS.txt` inside the ZIP to verify all other files in that same ZIP. Source URLs, capture timestamps and response metadata are recorded in `evidence/manifest.json`. The three full JSON snapshots are intentionally omitted from this Git repository.

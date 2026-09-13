# Vesuvius catalogue repair for issues #1504 and #1516

Based on the public catalogue snapshot captured on 10 September 2026. This package contains six directly supported metadata corrections and one separately marked segment provenance proposal. It does not claim discovery of the reported defects.

The four missing volume shapes are copied, in their published array order, from the corresponding level-0 Zarr metadata. Two volume parent references retain their IDs and change their type from `volume` to `scan`; their `scan_id` fields independently agree. The seventh record is a segment: its proposed parent is its declared `original_volume_id`, preserving the catalogue's volume-parent convention. A maintainer must confirm that provenance choice.

## Download v1.0.0

[Download the full release archive](https://github.com/benlucius/vesuvius-catalogue-repair/releases/download/v1.0.0/Vesuvius_Catalogue_Repair_v1.0.0.zip) · [Release page](https://github.com/benlucius/vesuvius-catalogue-repair/releases/tag/v1.0.0)

Download and extract `Vesuvius_Catalogue_Repair_v1.0.0.zip` for exact offline reproduction. The attached archive contains all three complete catalogue snapshots; GitHub's automatically generated source archives and a repository checkout do not.

Archive size: 3,605,910 bytes. SHA-256:

```text
3c65e001d54accba3d29c612635b00dab8f31466826f352a449f88e9b354068c
```

## Start here

Use `catalogue.six.patch.json` or `metadata.six.corrected.json` for the six directly supported corrections. `metadata.seven.proposed.json` and `catalogue.seven.proposed.patch.json` additionally include the segment proposal and are explicitly for review.

The following inventory describes the release ZIP. Follow the README inside that ZIP when reproducing its contents.

| File | Purpose |
| --- | --- |
| `repair_catalogue.py` | Standard-library snapshot, audit, guarded repair and verification commands |
| `catalogue.six.patch.json` | RFC 6902 tests and six directly supported replacements |
| `metadata.six.corrected.json` | Complete local catalogue with those six corrections |
| `catalogue.seven.proposed.patch.json` | Six corrections plus the proposed segment parent ID correction |
| `metadata.seven.proposed.json` | Complete local catalogue including that proposal |
| `evidence/` | Unmodified decoded public responses, source URLs, timestamps, headers and hashes |
| `validation.six.json`, `validation.seven.proposed.json` | Full-document semantic comparison and consumer audit results |
| `verification.log` | Actual commands, exit statuses and regression test output |
| `test_repair.py` | 12 regression tests using the complete real catalogue fixture |
| `SHA256SUMS.txt` | Checksums of all other files inside the release ZIP (use the copy inside that ZIP) |

## Reproduce offline

Python 3.9 or later; no installation, account, credentials, GPU or third-party Python dependency is required. Run from the extracted release directory. The captured run used the Python version recorded in `verification.log`.

```sh
python3 repair_catalogue.py check --catalogue evidence/metadata.original.json
```

The original snapshot returns exit code 1, as expected: none of the four selected shapes matches its Zarr metadata and none of the three selected typed references resolves. This exit code reports the known defects; it is not a script failure.

```sh
python3 repair_catalogue.py verify --catalogue evidence/metadata.original.json --after metadata.six.corrected.json
python3 repair_catalogue.py verify --catalogue evidence/metadata.original.json --after metadata.seven.proposed.json --include-segment-proposal
python3 -m unittest -v test_repair
```

All three commands should exit 0. Verification compares the entire document semantically, allows only the expected six or seven replacements, and checks that a second repair makes no changes. The tests also check stale/conflicting values, input preservation, independent JSON Patch application, corrupted evidence and refusal to overwrite existing output files.

To create new output files, choose paths that do not already exist:

```sh
python3 repair_catalogue.py apply --catalogue evidence/metadata.original.json --out reviewed.six.json --patch reviewed.six.patch.json
```

Only after confirming the segment's intended provenance, add `--include-segment-proposal` to generate the seventh correction. The default deliberately leaves that record untouched.

## Refresh against the public source

```sh
python3 repair_catalogue.py snapshot --out fresh_evidence
python3 repair_catalogue.py apply --evidence fresh_evidence --catalogue fresh_evidence/metadata.original.json --out fresh.six.json --patch fresh.six.patch.json
```

The snapshot command makes five public HTTP GET requests: one catalogue and four small `.zarray` metadata objects. No CT chunks are downloaded. All other commands are offline. A failed download may leave a partial evidence directory; use a new output directory for a retry. Snapshotting is not an atomic server-side transaction. The saved response metadata documents when each object was retrieved.

The utility validates the targeted record IDs, array paths, evidence hashes, current field values and scan relationships before writing outputs. It aborts on conflicts. Already corrected values are accepted. Evidence hashes detect local corruption, not malicious replacement of both the manifest and its files. The public source may change after capture.

The generated JSON Patch files target the captured snapshot. Check its SHA-256 in `evidence/manifest.json` before applying a patch with another tool. To work with newer catalogues, regenerate evidence and use the guarded utility. Apply the full patch in memory and persist only after all tests succeed. Output whitespace may differ; unrelated JSON values are preserved.

## Maintainer integration

1. Review the six direct corrections and, separately, the segment proposal.
2. Make the corresponding changes in the authoritative metadata source records or export process, and regenerate the published catalogue. This standalone package does not locate or modify that upstream system.
3. Compare the regenerated targeted fields with the Zarr metadata and verify their typed parent references. Preserve unrelated records and run the project's normal validation before publication.

A local corrected snapshot is not a deployed fix. Patching only a generated output may be undone by a later export. This package neither publishes data nor changes the project's servers.

## Verification on 13 September 2026

The published asset digest matches the locally tested archive. A fresh download of the official catalogue and four Zarr metadata objects matched the release evidence byte for byte. All 12 regression tests passed from an extracted copy of the archive. Independent application of both packaged JSON patches reproduced their corresponding full catalogue outputs. The default output changes exactly six fields; the optional proposal changes seven. Repeated repair makes no further changes.

## Evidence and limits

Measured: selected shape lookups improve from 0/4 to 4/4; selected parent lookups improve from 0/3 to 2/3 with the direct corrections, or 3/3 including the proposal. These are metadata consumer checks on actual published records, not scroll-reading accuracy or runtime benchmarks. There is no demonstrated change to VC3D rendering, segmentation, ink detection or recovered text, and no evidence of community adoption yet. Regression fault-injection tests supplement, rather than replace, the real-data check.

The original reports are by [@nerln in #1504](https://github.com/ScrollPrize/villa/issues/1504) and [#1516](https://github.com/ScrollPrize/villa/issues/1516). Issue #1516 also credits @Bullo27 with independent shape verification and an audit check. This package provides a guarded repair implementation, captured evidence, reproducible outputs, regression checks and separate treatment of the segment's ambiguous provenance.

Implementation, tests and documentation were prepared with assistance from OpenAI Codex.

## Licence and attribution

The original code in this package is offered under the MIT licence in `LICENSE`. Third-party catalogue and Zarr metadata are attributed to Vesuvius Challenge / Scroll Prize and remain subject to their original terms. Dataset licence fields are preserved. See `NOTICE.txt` and the source URLs in `evidence/manifest.json`.


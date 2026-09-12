# Vesuvius catalogue repair for issues #1504 and #1516

Prepared for technical review and published at:

- Repository: https://github.com/benlucius/vesuvius-catalogue-repair
- Full v1.0.0 archive: https://github.com/benlucius/vesuvius-catalogue-repair/releases/download/v1.0.0/Vesuvius_Catalogue_Repair_v1.0.0.zip

This package contains six directly supported metadata corrections and one separately marked segment-provenance proposal. It does not claim discovery of the reported defects.

The four missing volume shapes are copied, in their published array order, from the corresponding level-0 Zarr metadata. Two volume parent references retain their IDs and change their type from `volume` to `scan`; their `scan_id` fields independently agree. The seventh record is a segment: its proposed parent is its declared `original_volume_id`, preserving the catalogue's volume-parent convention. A maintainer must confirm that provenance choice.

## Start here

Read `Catalogue_Repair_Report.pdf`, then use the six-correction patch by default. `metadata.seven.proposed.json` and `catalogue.seven.proposed.patch.json` additionally include the segment proposal and are explicitly for review.

For the exact historical reproduction, **download and unpack the full release archive**. It contains the original ~15.6 MB catalogue snapshot and both complete corrected catalogue variants. Those three large plain JSON files are intentionally not committed to the Git repository.

| File | Purpose |
| --- | --- |
| `repair_catalogue.py` | Standard-library snapshot, audit, guarded repair and verification commands |
| `catalogue.six.patch.json` | RFC 6902 tests and six directly supported replacements |
| `metadata.six.corrected.json` | Complete local catalogue with those six corrections (full release archive) |
| `catalogue.seven.proposed.patch.json` | Six corrections plus the proposed segment parent ID correction |
| `metadata.seven.proposed.json` | Complete local catalogue including that proposal (full release archive) |
| `evidence/` | Captured source manifest, source-status record and the four small Zarr metadata objects in Git; the full release archive additionally contains `metadata.original.json` |
| `validation.six.json`, `validation.seven.proposed.json` | Full-document semantic comparison and consumer-audit results |
| `verification.log` | Recorded verification and regression-test output |
| `test_repair.py` | 12 regression tests using the captured real catalogue fixture |
| `build_report.py` | Optional PDF rebuild; requires ReportLab and the DejaVu system fonts |
| `SHA256SUMS.txt` | Checksums of all other files in the full release archive |
| `submission_email.txt` | Draft email for technical review and an eligibility enquiry |
| `progress_prize_form.txt` | Draft technical answers for the monthly form |
| `START_HERE_RU.txt` | Short instructions in Russian |

## Exact reproduction from the v1.0.0 archive

Python 3.9 or later is sufficient for the repair utility itself. Download and unpack the release ZIP, then run from the unpacked directory:

```sh
python3 repair_catalogue.py check --evidence evidence --catalogue evidence/metadata.original.json
```

The original snapshot returns exit code 1, as expected: none of the four selected shapes matches its Zarr metadata and none of the three selected typed references resolves. This exit code reports the known defects; it is not a script failure.

```sh
python3 repair_catalogue.py verify --catalogue evidence/metadata.original.json --after metadata.six.corrected.json
python3 repair_catalogue.py verify --catalogue evidence/metadata.original.json --after metadata.seven.proposed.json --include-segment-proposal
python3 -m unittest -v test_repair
```

The two `verify` commands and the test suite should exit 0. Verification compares the entire document semantically, allows only the expected six or seven replacements, and checks that a second repair makes no changes. The tests also check stale/conflicting values, input preservation, independent JSON Patch application, corrupted evidence and refusal to overwrite existing output files.

To create a new six-correction output file, choose paths that do not already exist:

```sh
python3 repair_catalogue.py apply --evidence evidence --catalogue evidence/metadata.original.json --out reviewed.six.json --patch reviewed.six.patch.json
```

Only after confirming the segment's intended provenance, add `--include-segment-proposal` to generate the seventh correction. The default deliberately leaves that record untouched.

## Repository checkout vs full release

The Git repository intentionally omits the three complete ~15.6 MB catalogue JSON snapshots. **For repeating the exact regression tests, download and unpack the v1.0.0 archive linked above.** The repository still publishes the patches, utility, report, evidence manifest and small Zarr evidence, validation outputs and verification log.

## Refresh against the current public source

```sh
python3 repair_catalogue.py snapshot --out fresh_evidence
python3 repair_catalogue.py check --evidence fresh_evidence --catalogue fresh_evidence/metadata.original.json
python3 repair_catalogue.py apply --evidence fresh_evidence --catalogue fresh_evidence/metadata.original.json --out fresh.six.json --patch fresh.six.patch.json
```

The snapshot command makes five public HTTP GET requests: one catalogue and four small `.zarray` metadata objects. No CT chunks are downloaded. All other commands are offline. A failed download may leave a partial evidence directory; use a new output directory for a retry. Snapshotting is not an atomic server-side transaction. The saved response metadata documents when each object was retrieved.

The utility validates the targeted record IDs, array paths, evidence hashes, current field values and scan relationships before writing outputs. It aborts on conflicts. Already corrected values are accepted. Evidence hashes detect local corruption, not malicious replacement of both the manifest and its files. The public source may change after capture.

The generated JSON Patch files target the captured snapshot. Check its SHA-256 in `evidence/manifest.json` before applying a patch with another tool. To work with newer catalogues, regenerate evidence and use the guarded utility. Apply the full patch in memory and persist only after all tests succeed. Output whitespace may differ; unrelated JSON values are preserved.

## Maintainer integration

1. Review the six direct corrections and, separately, the segment proposal.
2. Make the corresponding changes in the authoritative metadata source records or export process, and regenerate the published catalogue. This standalone package does not locate or modify that upstream system.
3. Compare the regenerated targeted fields with the Zarr metadata and verify their typed parent references. Preserve unrelated records and run the project's normal validation before publication.

A local corrected snapshot is not a deployed fix. Patching only a generated output may be undone by a later export. This package does not change the project's servers.

## Evidence and limits

Measured on the captured snapshot: selected shape lookups improve from 0/4 to 4/4; selected typed parent-reference lookups improve from 0/3 to 2/3 with the direct corrections, or 3/3 including the proposal. These are metadata-consumer checks on published records, not scroll-reading accuracy or runtime benchmarks. There is no demonstrated change to VC3D rendering, segmentation, ink detection or recovered text, and no evidence of community adoption yet. Regression fault-injection tests supplement, rather than replace, the real-data check.

The original reports are by [@nerln in #1504](https://github.com/ScrollPrize/villa/issues/1504) and [#1516](https://github.com/ScrollPrize/villa/issues/1516). Issue #1516 also credits @Bullo27 with independent shape verification and an audit check. The added contribution here is the guarded repair implementation, fresh evidence capture, reproducible outputs, regression checks and the separate treatment of the segment's ambiguous provenance.

The implementation, testing and documentation were prepared with OpenAI Codex at the submitter's request. Do not describe the submitter as the original discoverer, or claim personal code review or hands-on VC3D use that has not occurred. The project's [contribution guidelines](https://github.com/ScrollPrize/villa/blob/main/CONTRIBUTING.md) require actual human use, human-written motivation and code review for AI-assisted PRs. This is a technical review package, not a representation that those PR requirements have already been fulfilled.

## Submission and award status

The package now has a public contribution URL: https://github.com/benlucius/vesuvius-catalogue-repair . The v1.0.0 release archive is the reproducibility artifact linked at the top of this README. Emailing the draft in `submission_email.txt` does not itself constitute a completed monthly Progress Prize entry; identity/contact details and acceptance of any current terms remain the submitter's responsibility.

This is a small maintenance contribution to previously reported issues. It has no assigned bounty or guaranteed payment. The project alone decides eligibility and awards.

## Licence and attribution

The original code in this package is offered under the MIT licence in `LICENSE`. Third-party catalogue and Zarr metadata are attributed to Vesuvius Challenge / Scroll Prize and remain subject to their original terms. Dataset licence fields are preserved. See `NOTICE.txt` and the source URLs in `evidence/manifest.json`.

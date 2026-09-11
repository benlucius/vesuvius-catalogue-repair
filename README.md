# Vesuvius catalogue repair for issues #1504 and #1516

Public technical-review repository for a small catalogue repair prepared on 10 September 2026. It contains **six directly supported metadata corrections** and **one separately marked segment-provenance proposal**. It does not claim discovery of the reported defects.

The four missing volume shapes are copied, in published array order, from the corresponding level-0 Zarr metadata. Two volume parent references keep their IDs and change their type from `volume` to `scan`; the records' `scan_id` fields independently agree. The seventh record is a segment: its proposed parent is its declared `original_volume_id`, preserving the catalogue's volume-parent convention. That provenance choice still needs maintainer confirmation.

## Files to review

- `catalogue.six.patch.json` — the default six directly supported corrections.
- `catalogue.seven.proposed.patch.json` — the same six corrections plus the separately flagged segment-parent proposal.
- `repair_catalogue.py` — standard-library snapshot, audit, guarded repair, and verification utility.
- `test_repair.py` — regression tests used against the captured full catalogue fixture.
- `SNAPSHOT_DATA.md` — exact sizes and SHA-256 values for the full historical catalogue snapshots and the original review ZIP.
- `START_HERE_RU.txt` — short Russian handoff notes.
- `progress_prize_form.txt` and `submission_email.txt` — draft submission materials with the public repository URL filled in.

The original archive also contains three complete catalogue JSON files of about 15.6 MB each plus a generated PDF report and recorded validation logs. Those bulky historical outputs are not committed here. Their exact hashes and sizes are preserved in `SNAPSHOT_DATA.md`, and the source archive SHA-256 is recorded there as well.

## What the repair changes

Measured on the captured 10 September 2026 catalogue snapshot:

- selected shape lookups: **0/4 → 4/4**;
- selected typed parent-reference lookups: **0/3 → 2/3** with the six direct corrections;
- parent-reference lookups: **0/3 → 3/3** only when the separate segment proposal is included;
- semantic changes: exactly **6** or **7**, respectively;
- second repair pass: no changes;
- regression suite: **12/12 tests passed**.

The six-correction patch is the conservative default. The seventh change should not be treated as confirmed historical provenance until a maintainer verifies the intended parent of segment `20250910185200`.

## Refresh against the current public catalogue

Python 3.9+ is sufficient for the repair utility itself.

```sh
python3 repair_catalogue.py snapshot --out fresh_evidence
python3 repair_catalogue.py check --catalogue fresh_evidence/metadata.original.json
python3 repair_catalogue.py apply \
  --evidence fresh_evidence \
  --catalogue fresh_evidence/metadata.original.json \
  --out reviewed.six.json \
  --patch reviewed.six.patch.json
```

The public source may have changed since the captured September snapshot. A new download should not be described as byte-identical unless its SHA-256 matches the historical value in `SNAPSHOT_DATA.md`.

To generate the seventh proposal, add `--include-segment-proposal` only after reviewing the provenance question.

## Attribution and scope

The original reports are by [@nerln in ScrollPrize/villa#1504](https://github.com/ScrollPrize/villa/issues/1504) and [#1516](https://github.com/ScrollPrize/villa/issues/1516). Issue #1516 also credits @Bullo27 with independent shape verification and an audit check. The added contribution here is the guarded repair implementation, reproducible patches, regression checks, and separate handling of the segment's ambiguous provenance.

Implementation, testing, and documentation were prepared with OpenAI Codex at the submitter's request. This repository does **not** represent that the submitter discovered the original defects, personally reviewed every generated line, or performed hands-on VC3D testing.

This work demonstrates metadata-consumer consistency fixes only. It does not demonstrate improved segmentation, ink detection, recovered text, or scroll-reading accuracy, and it carries no guaranteed bounty or award.

## Public contribution URL

https://github.com/benlucius/vesuvius-catalogue-repair

## Licence

Original code in this repository is offered under the MIT licence in `LICENSE`. Third-party catalogue and Zarr metadata remain subject to their original terms; see `NOTICE.txt`.

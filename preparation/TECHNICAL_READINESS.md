# Technical readiness and integration handoff

Assessment date: 13 September 2026. This document supplements the published v1.0.0 ZIP; it does not alter that release or its checksums.

## Confirmed consumer effect

The unmodified `lasagna.manager.cli` from Villa commit `be09a85035059fd83471b1632b5898c62f2c65b1` was executed against the full original catalogue and the six-correction output, using separate local fixture caches. Its `volume ls` table displayed `-` for four volume shapes before repair and the correct dimensions afterward. Its JSON output contained three-dimensional shapes for 67 of 71 volumes before repair and all 71 after repair. Both commands exit successfully before and after: this is a catalogue completeness/display improvement, not a demonstrated crash fix.

| Sample | Volume | Before | After, Z/Y/X |
| --- | --- | --- | --- |
| PHerc0343P | 20250521134555 | Missing | 5398 / 5057 / 5057 |
| PHerc0500P2 | 20250526151718 | Missing | 28096 / 18209 / 18209 |
| PHerc0500P2 | 20250528085330 | Missing | 15838 / 9423 / 9423 |
| PHerc0500P2 | 20250820143440 | Missing | 7057 / 4196 / 4196 |

Evidence: [actual command output](results/consumer-before-after.log), [machine-readable results](results/consumer-result.json), [reproduction script](reproduce_consumer.py), [pinned source hashes](source-lock.json).

A negative control executed the website's unmodified `buildIndex` function on both complete catalogues with the same empty optional overlays. Outputs were identical. No improvement to the website index is claimed. VC3D source inspection confirms that its manifest parser reads volume shapes, but the VC3D application was not built or run. No inference, segmentation, recovered-text, speed, adoption, or human-use improvement was measured.

The two parent-type fixes remain supported by record identity, `scan_id`, and typed-reference resolution checks. The consumer experiment above demonstrates the four shape fixes; it does not independently demonstrate a downstream benefit of the two reference fixes.

## Reproduce

Requirements for this supplemental experiment: Python 3.11+ and Node.js 18+ on Linux or macOS. The main release utility still requires only Python 3.9+. No package installation, model weights, GPU, or CT chunks are needed. The imported upstream cache module uses Unix `fcntl`; Windows was not tested.

1. Download and extract the attached v1.0.0 release ZIP.
2. Obtain this repository's `preparation` directory (script and source-lock file).
3. Run from the repository root, substituting the extracted release directory:

```sh
python3 preparation/reproduce_consumer.py \
  --release-dir /path/to/vesuvius-catalogue-repair-2026-09-10 \
  --upstream-dir ./villa-consumer-source \
  --fetch-upstream \
  --out ./consumer-reproduction
```

The optional fetch flag downloads 13 source files pinned to one Villa commit, verifies their Git blob hashes, and never installs packages. Files already present must match their hashes. Without the flag, all files must already be present. The script verifies the ZIP's internal file checksums, runs the original CLI using disposable local catalogue caches, and compares the outputs. It writes two result files to a new output directory. Local fixture cache metadata is explicitly labelled as a fixture; it is not claimed to be a network fetch by Lasagna.

Recorded runtime: Python 3.12.14, Node.js v24.19.0. Source modules match the upstream Git blobs byte for byte. The repair code and published ZIP were not modified for this experiment.

## Official integration: prepared, not deployed

[Villa's manager documentation](https://github.com/ScrollPrize/villa/blob/be09a85035059fd83471b1632b5898c62f2c65b1/lasagna/docs/manager.md) identifies a separate Atlas checkout, metadata review/merge, and operator-controlled publication/export. The website generator consumes the public S3 catalogue; it does not generate the authoritative volume records. The official Atlas source records and publication credentials were not available in this session. Consequently there is no verified Atlas source patch or upstream deployment to report.

The exact changes below are specified at the exported catalogue level. An Atlas maintainer must map them to authoritative source fields; source filenames and exporter commands must not be guessed.

| Sample / volume | Exported field | Required change |
| --- | --- | --- |
| PHerc0343P / 20250521134555 | properties.shape | null to [5398, 5057, 5057] |
| PHerc0500P2 / 20250526151718 | properties.shape | null to [28096, 18209, 18209] |
| PHerc0500P2 / 20250528085330 | properties.shape | null to [15838, 9423, 9423] |
| PHerc0500P2 / 20250820143440 | properties.shape | null to [7057, 4196, 4196] |
| PHerc0009B / 20250521125136 | creation.derived_from.type | volume to scan; retain ID 20250509053741 |
| PHerc0009B / 20250820154339 | creation.derived_from.type | volume to scan; retain ID 20250718080859 |

Review sequence for the maintainer:

1. Confirm the six changes against current source records and published Zarr metadata. Use `catalogue.six.patch.json` as the reviewable exported-field specification.
2. Update the authoritative Atlas records or export logic, preserving IDs, unrelated metadata, licences and access rules. Run Atlas's own validation. The source edit is intentionally not fabricated here because its schema and repository were unavailable.
3. Generate a local catalogue export before publishing. Compare it with a corresponding unmodified export; account for any independent changes. Check the four shapes and two typed references. Use the existing release verification only when the baseline is the captured snapshot; it deliberately rejects unrelated changes.
4. Re-run the Lasagna listing against the exported data. Then have the authorised Atlas operator publish through the project's normal mechanism and refresh consumer caches.
5. Retrieve the public catalogue again to confirm that the deployed values persist through regeneration. Record the upstream commit, publication timestamp, catalogue hash and before/after results.

Do not apply the seventh segment proposal by default. A resolvable parent ID does not prove historical provenance. The segment's intended parent must be confirmed by the data maintainer.

## Human participation and submission status

[Villa's contribution policy](https://github.com/ScrollPrize/villa/blob/be09a85035059fd83471b1632b5898c62f2c65b1/CONTRIBUTING.md) requires human use of the tool on real scroll data, human-written motivation and personal code review for AI-assisted bugfix PRs. It also asks for before/after evidence, including screenshots for bugfix PRs. Agent-executed commands and an AI-written document do not fulfil the personal-use or human-writing requirements.

The source-policy scope is Villa PRs. It must not automatically be asserted as Atlas's policy without reading Atlas's own rules. No exemption or permission from either project's maintainers has been obtained.

To complete a Villa PR honestly, a human must actually use the relevant tool, understand/review the proposed changes, and write their own account of the real task and benefit. Simply signing or copying AI-generated commentary is not a substitute. If the maintainer chooses to integrate these data corrections independently, record that outcome and the actual attribution rather than claiming the submitter personally met the PR requirements.

Current status:

- Release integrity, six corrections, regression tests, and actual catalogue-listing improvement: demonstrated.
- Maintainer handoff: prepared as exact exported-field changes and acceptance checks.
- Authoritative Atlas source patch, merge and public deployment: not completed; source/operator access required.
- Seventh segment provenance: unresolved.
- Human-use and personal-review requirements for a Villa PR: not fulfilled by the agent.
- Community adoption and improved scroll-reading outcomes: not demonstrated.
- Contest form: not submitted; it will be handled separately.

This is a reproducible metadata-maintenance contribution to issues [#1504](https://github.com/ScrollPrize/villa/issues/1504) and [#1516](https://github.com/ScrollPrize/villa/issues/1516), originally reported by nerln, with independent shape verification credited to Bullo27. Preparation and the supplemental experiment used OpenAI Codex. No endorsement by the original reporters or project maintainers is claimed.

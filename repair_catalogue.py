#!/usr/bin/env python3
"""Narrow, offline-first repair of Vesuvius catalogue issues #1504 and #1516.

Python 3.9+, standard library only. Network access is limited to `snapshot`.
The segment provenance proposal is opt-in and needs maintainer review.
"""
import argparse
import copy
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

ROOT = "https://vesuvius-challenge-open-data.s3.amazonaws.com/"
SHAPES = (
    ("PHerc0500P2", "20250526151718", "20250526151718-2.215um-0.4m-111keV-masked.zarr"),
    ("PHerc0500P2", "20250528085330", "20250528085330-4.317um-1.2m-111keV-masked.zarr"),
    ("PHerc0500P2", "20250820143440", "20250820143440-9.362um-1.2m-113keV-masked.zarr"),
    ("PHerc0343P", "20250521134555", "20250521134555-8.640um-1.2m-116keV-masked.zarr"),
)
REFERENCES = (
    ("20250521125136", "20250509053741"),
    ("20250820154339", "20250718080859"),
)
SEGMENT = "20250910185200"
SEGMENT_VOLUME = "20250820154339"
SEGMENT_SCAN = "20250718080859"


class RepairError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise RepairError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def read_json(path):
    return json.loads(Path(path).read_bytes())


def write_new(path, data):
    """Exclusive creation; never overwrite an input or an earlier output."""
    with Path(path).open("xb") as stream:
        stream.write(data)


def shape_file(sample, volume):
    return sample + "_" + volume + ".zarray.json"


def shape_url(sample, long_id):
    return ROOT + sample + "/volumes/" + long_id + "/0/.zarray"


def snapshot(directory):
    """Preserve decoded HTTP payloads, their hashes and response provenance."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    sources = [("metadata.original.json", ROOT + "metadata.json")]
    sources.extend((shape_file(s, v), shape_url(s, long_id)) for s, v, long_id in SHAPES)
    manifest = {"format": 1, "sources": {}}
    for filename, url in sources:
        request = urllib.request.Request(url, headers={"User-Agent": "VesuviusCatalogueRepair/1.0"})
        with urllib.request.urlopen(request, timeout=40) as response:
            wire = response.read()
            payload = gzip.decompress(wire) if wire[:2] == b"\x1f\x8b" else wire
            json.loads(payload)
            manifest["sources"][filename] = {
                "url": url,
                "retrieved_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"),
                "content_encoding": response.headers.get("Content-Encoding"),
                "response_bytes": len(wire),
                "response_sha256": sha(wire),
                "decoded_bytes": len(payload),
                "decoded_sha256": sha(payload),
            }
        write_new(directory / filename, payload)
        print("Saved " + filename, flush=True)
    write_new(directory / "manifest.json", encoded(manifest))


def load_evidence(directory):
    directory = Path(directory)
    manifest = read_json(directory / "manifest.json")
    require(manifest.get("format") == 1, "Unsupported evidence manifest")
    expected = {"metadata.original.json": ROOT + "metadata.json"}
    expected.update({shape_file(s, v): shape_url(s, long_id) for s, v, long_id in SHAPES})
    arrays = {}
    for filename, url in expected.items():
        source = manifest["sources"][filename]
        payload = (directory / filename).read_bytes()
        require(source["url"] == url, "Unexpected evidence URL: " + filename)
        require(sha(payload) == source["decoded_sha256"], "Evidence hash mismatch: " + filename)
        require(len(payload) == source["decoded_bytes"], "Evidence size mismatch: " + filename)
        value = json.loads(payload)
        if filename != "metadata.original.json":
            dims = value.get("shape")
            require(value.get("zarr_format") == 2, "Expected Zarr v2 metadata: " + filename)
            require(isinstance(dims, list) and len(dims) == 3 and
                    all(type(n) is int and n > 0 for n in dims), "Invalid array shape: " + filename)
            arrays[filename] = dims
    return arrays


def pointer(parts):
    return "/" + "/".join(str(p).replace("~", "~0").replace("/", "~1") for p in parts)


def at(document, parts):
    for part in parts:
        document = document[part]
    return document


def same(a, b):
    # JSON numbers and booleans must not be confused by Python's True == 1.
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def repair(catalogue, arrays, include_segment=False):
    """Return a new document and a guarded RFC 6902 patch. Input is untouched."""
    result = copy.deepcopy(catalogue)
    guards, replacements = [], []

    def guard(parts, expected):
        require(same(at(catalogue, parts), expected), "Guard failed: " + pointer(parts))
        guards.append({"op": "test", "path": pointer(parts), "value": copy.deepcopy(expected)})

    def replace(parts, before, after):
        current = at(catalogue, parts)
        if same(current, after):
            return
        require(same(current, before), "Unexpected current value: " + pointer(parts))
        guard(parts, before)
        replacements.append({"op": "replace", "path": pointer(parts), "value": copy.deepcopy(after)})
        at(result, parts[:-1])[parts[-1]] = copy.deepcopy(after)

    for sample, volume, long_id in SHAPES:
        base = ("samples", sample, "volumes", volume)
        guard(base + ("id",), volume)
        guard(base + ("sample_id",), sample)
        guard(base + ("long_id",), long_id)
        volume_record = at(catalogue, base)
        expected_path = sample + "/volumes/" + long_id + "/"
        matched = False
        for i, data in enumerate(volume_record.get("data") or []):
            if data.get("type") != "ome-zarr":
                continue
            for j, origin in enumerate(data.get("origins") or []):
                if origin.get("path") == expected_path:
                    guard(base + ("data", i, "type"), "ome-zarr")
                    guard(base + ("data", i, "origins", j, "path"), expected_path)
                    matched = True
        require(matched, "Array path no longer matches: " + volume)
        replace(base + ("properties", "shape"), None, arrays[shape_file(sample, volume)])

    sample = catalogue["samples"]["PHerc0009B"]
    for volume, scan in REFERENCES:
        base = ("samples", "PHerc0009B", "volumes", volume)
        guard(base + ("id",), volume)
        guard(base + ("sample_id",), "PHerc0009B")
        guard(base + ("scan_id",), scan)
        require(scan not in sample["volumes"], "Ambiguous scan/volume identifier: " + scan)
        guard(("samples", "PHerc0009B", "scans", scan, "id"), scan)
        guard(base + ("creation", "derived_from", "id"), scan)
        replace(base + ("creation", "derived_from", "type"), "volume", "scan")

    if include_segment:
        # Proposal: retain the volume parent convention and use the explicitly
        # declared original_volume_id. This is not historical provenance proof.
        base = ("samples", "PHerc0009B", "segments", SEGMENT)
        guard(base + ("id",), SEGMENT)
        guard(base + ("sample_id",), "PHerc0009B")
        guard(base + ("original_volume_id",), SEGMENT_VOLUME)
        guard(base + ("creation", "derived_from", "type"), "volume")
        guard(("samples", "PHerc0009B", "volumes", SEGMENT_VOLUME, "scan_id"), SEGMENT_SCAN)
        guard(("samples", "PHerc0009B", "volumes", SEGMENT_VOLUME, "id"), SEGMENT_VOLUME)
        replace(base + ("creation", "derived_from", "id"), SEGMENT_SCAN, SEGMENT_VOLUME)

    # Tests precede every mutation, for review and implementations that apply
    # a patch in memory. Persist the document only after the entire patch passes.
    return result, (guards + replacements if replacements else [])


def audit(catalogue, arrays):
    """Exercise catalogue consumers on the seven selected records."""
    shapes, refs = [], []
    for sample, volume, unused in SHAPES:
        current = catalogue["samples"][sample]["volumes"][volume]["properties"]["shape"]
        expected = arrays[shape_file(sample, volume)]
        shapes.append({"sample": sample, "volume": volume, "catalogue_shape": current,
                       "array_shape": expected,
                       "matches_array": isinstance(current, list) and
                       all(type(n) is int for n in current) and current == expected})
    sample = catalogue["samples"]["PHerc0009B"]
    for kind, rid in [("volumes", v) for v, s in REFERENCES] + [("segments", SEGMENT)]:
        ref = sample[kind][rid]["creation"]["derived_from"]
        collection = {"scan": "scans", "volume": "volumes"}.get(ref.get("type"))
        refs.append({"kind": kind, "id": rid, "reference": ref,
                     "resolves": bool(collection and ref.get("id") in (sample.get(collection) or {}))})
    all_volumes = [v for s in catalogue["samples"].values() for v in (s.get("volumes") or {}).values()]
    return {"selected_shapes_matching_arrays": sum(r["matches_array"] for r in shapes),
            "selected_references_resolving": sum(r["resolves"] for r in refs),
            "catalogue_volume_count": len(all_volumes),
            "catalogue_null_volume_shapes": sum((v.get("properties") or {}).get("shape", "missing") is None for v in all_volumes),
            "shapes": shapes, "references": refs}


def differences(before, after, path=()):
    """Return semantic differences; unchanged formatting is not required."""
    if type(before) is not type(after):
        return [pointer(path)]
    if isinstance(before, dict):
        paths = []
        for key in sorted(before.keys() | after.keys()):
            if key not in before or key not in after:
                paths.append(pointer(path + (key,)))
            else:
                paths.extend(differences(before[key], after[key], path + (key,)))
        return paths
    if isinstance(before, list):
        if len(before) != len(after):
            return [pointer(path)]
        paths = []
        for i, (left, right) in enumerate(zip(before, after)):
            paths.extend(differences(left, right, path + (i,)))
        return paths
    return [] if before == after else [pointer(path)]


def verify(before, after, arrays, include_segment=False):
    expected, patch = repair(before, arrays, include_segment)
    require(not differences(expected, after), "Output differs from the complete expected document")
    changes = differences(before, after)
    allowed = sorted(p["path"] for p in patch if p["op"] == "replace")
    require(sorted(changes) == allowed, "Unexpected changed paths")
    again, repeat_patch = repair(after, arrays, include_segment)
    require(not repeat_patch and not differences(after, again), "Repair is not idempotent")
    return {"verified": True, "segment_proposal_included": include_segment,
            "semantic_change_count": len(changes), "changed_paths": changes,
            "idempotent": True, "before": audit(before, arrays), "after": audit(after, arrays)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("snapshot").add_argument("--out", required=True)
    for command in ("check", "apply", "verify"):
        sub = commands.add_parser(command)
        sub.add_argument("--evidence", default="evidence")
        sub.add_argument("--catalogue", required=True)
        if command != "check":
            sub.add_argument("--include-segment-proposal", action="store_true")
        if command == "apply":
            sub.add_argument("--out", required=True)
            sub.add_argument("--patch", required=True)
        if command == "verify":
            sub.add_argument("--after", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "snapshot":
            snapshot(args.out)
            return 0
        arrays = load_evidence(args.evidence)
        catalogue = read_json(args.catalogue)
        if args.command == "check":
            value = audit(catalogue, arrays)
            print(encoded(value).decode(), end="")
            return 0 if value["selected_shapes_matching_arrays"] == 4 and value["selected_references_resolving"] == 3 else 1
        if args.command == "apply":
            destinations = [Path(args.out), Path(args.patch)]
            require(len({p.resolve() for p in destinations}) == 2, "Outputs must be distinct")
            require(all(not p.exists() for p in destinations), "Output already exists; choose new paths")
            corrected, patch = repair(catalogue, arrays, args.include_segment_proposal)
            verify(catalogue, corrected, arrays, args.include_segment_proposal)
            # Serialise all content before creating any output file.
            payloads = [encoded(corrected), encoded(patch)]
            for path, payload in zip(destinations, payloads):
                write_new(path, payload)
            print(json.dumps({"replacements": sum(p["op"] == "replace" for p in patch),
                              "segment_proposal_included": args.include_segment_proposal}))
        else:
            print(encoded(verify(catalogue, read_json(args.after), arrays, args.include_segment_proposal)).decode(), end="")
        return 0
    except (RepairError, KeyError, TypeError, OSError, json.JSONDecodeError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

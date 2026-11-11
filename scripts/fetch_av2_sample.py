#!/usr/bin/env python3
"""Download a small, explicitly nonrandom AV2 validation sample from the official public bucket."""

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = "https://argoverse.s3.amazonaws.com/"
PREFIX = "datasets/av2/motion-forecasting/val/"
LICENSE = "https://www.argoverse.org/av2.html"


def fetch_bytes(url: str) -> bytes:
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 3:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 3:
                raise
        time.sleep(2**attempt)
    raise RuntimeError("download retries exhausted")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=128)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.count <= 500:
        parser.error("count must be 1..500")
    if args.out.exists():
        parser.error("output already exists; choose a new directory")
    keys, token = [], None
    ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
    while len(keys) < args.count:
        query = {"list-type": "2", "prefix": PREFIX, "max-keys": "1000"}
        if token:
            query["continuation-token"] = token
        tree = ET.fromstring(fetch_bytes(ROOT + "?" + urllib.parse.urlencode(query)))
        keys.extend(
            k.text
            for k in tree.findall("s3:Contents/s3:Key", ns)
            if k.text and k.text.endswith(".parquet")
        )
        token = tree.findtext("s3:NextContinuationToken", namespaces=ns)
        if not token:
            break
    keys = sorted(keys)[: args.count]
    if len(keys) < args.count:
        raise ValueError("not enough scenario objects in official validation prefix")
    args.out.mkdir(parents=True)

    def download(key: str) -> dict:
        # Key is validated before constructing a local filename.
        parts = key.split("/")
        if not key.startswith(PREFIX) or ".." in parts:
            raise ValueError("unexpected bucket key")
        url = ROOT + urllib.parse.quote(key, safe="/")
        data = fetch_bytes(url)
        path = args.out / Path(key).name
        path.write_bytes(data)
        return {
            "key": key,
            "url": url,
            "file": path.name,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }

    with ThreadPoolExecutor(max_workers=4) as executor:
        items = list(executor.map(download, keys))
    manifest = {
        "dataset": "Argoverse 2 Motion Forecasting",
        "split": "val",
        "selection": "first N parquet keys in lexicographic S3 order; not random or representative",
        "requested": args.count,
        "downloaded": len(items),
        "license": "CC-BY-NC-SA-4.0; see full dataset terms",
        "terms": LICENSE,
        "credit": "Argo AI / Argoverse 2 contributors (Wilson et al., 2023)",
        "files": items,
    }
    (args.out / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps(
            {
                "downloaded": len(items),
                "bytes": sum(i["bytes"] for i in items),
                "manifest": str(args.out / "source_manifest.json"),
            }
        )
    )


if __name__ == "__main__":
    main()

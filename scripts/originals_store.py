#!/usr/bin/env python3
"""Store downloaded originals (documents/<id>/original.*) in an S3 bucket.

Originals are not committed to git. When ORIGINALS_S3_BUCKET is set, fetch.py
uploads each original it saves, and convert.py --from-s3 downloads originals
that are missing locally before converting.

Environment:
    ORIGINALS_S3_BUCKET   bucket name; S3 storage is off when unset
    ORIGINALS_S3_PREFIX   key prefix, default "originals/"
    AWS credentials and region are read by boto3 in the usual way
    (AWS_PROFILE, AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY, AWS_REGION, instance role).

Object key: <prefix><id>/original.<ext>, with the file's SHA-256 in the
object metadata (x-amz-meta-sha256).

Usage:
    python scripts/originals_store.py push [ids...]   # upload local originals not yet in the bucket
    python scripts/originals_store.py pull [ids...]   # download originals missing locally
    python scripts/originals_store.py list            # list stored originals
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "documents"

CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".html": "text/html; charset=utf-8",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".odt": "application/vnd.oasis.opendocument.text",
    ".rtf": "application/rtf",
}


def bucket() -> str | None:
    return os.environ.get("ORIGINALS_S3_BUCKET") or None


def prefix() -> str:
    p = os.environ.get("ORIGINALS_S3_PREFIX", "originals/")
    return p if not p or p.endswith("/") else p + "/"


def enabled() -> bool:
    return bucket() is not None


def _client():
    try:
        import boto3
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise SystemExit("ORIGINALS_S3_BUCKET is set but boto3 is not installed: pip install boto3") from exc
    return boto3.client("s3")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def key_for(doc_id: str, filename: str) -> str:
    return f"{prefix()}{doc_id}/{filename}"


def s3_uri(doc_id: str, filename: str) -> str:
    return f"s3://{bucket()}/{key_for(doc_id, filename)}"


def remote_originals(client=None) -> dict[str, dict]:
    """Map doc id -> {"key", "size", "filename"} for every original in the bucket."""
    client = client or _client()
    out: dict[str, dict] = {}
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket(), Prefix=prefix()):
        for obj in page.get("Contents", []):
            rest = obj["Key"][len(prefix()):]
            doc_id, _, filename = rest.partition("/")
            if filename.startswith("original."):
                out[doc_id] = {"key": obj["Key"], "size": obj["Size"], "filename": filename}
    return out


def upload(doc_id: str, path: Path, client=None) -> str:
    """Upload one original unless the bucket already holds the same bytes. Returns its s3:// URI."""
    client = client or _client()
    key = key_for(doc_id, path.name)
    digest = _sha256(path)
    try:
        head = client.head_object(Bucket=bucket(), Key=key)
        if head.get("Metadata", {}).get("sha256") == digest:
            return s3_uri(doc_id, path.name)
    except client.exceptions.ClientError as exc:
        if exc.response.get("Error", {}).get("Code") not in {"404", "NoSuchKey", "NotFound"}:
            raise
    # Remove an original with another extension (e.g. HTML replaced by PDF).
    for other in client.list_objects_v2(Bucket=bucket(), Prefix=key_for(doc_id, "original.")).get("Contents", []):
        if other["Key"] != key:
            client.delete_object(Bucket=bucket(), Key=other["Key"])
    client.upload_file(
        str(path),
        bucket(),
        key,
        ExtraArgs={
            "ContentType": CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream"),
            "Metadata": {"sha256": digest},
        },
    )
    return s3_uri(doc_id, path.name)


def download(doc_id: str, client=None, remote: dict | None = None) -> Path | None:
    """Download the original for doc_id into documents/<id>/ if it is missing locally."""
    client = client or _client()
    out_dir = DOCS / doc_id
    local = sorted(out_dir.glob("original.*"))
    if local:
        return local[0]
    if remote is None:
        remote = remote_originals(client)
    obj = remote.get(doc_id)
    if obj is None:
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / obj["filename"]
    client.download_file(bucket(), obj["key"], str(target))
    return target


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["push", "pull", "list"])
    parser.add_argument("ids", nargs="*", help="only these catalog ids")
    args = parser.parse_args(argv)
    if not enabled():
        print("ORIGINALS_S3_BUCKET is not set")
        return 1
    client = _client()
    ids = set(args.ids)
    if args.command == "list":
        for doc_id, obj in sorted(remote_originals(client).items()):
            print(f"{doc_id:50s} {obj['filename']:16s} {obj['size']:>12,}")
        return 0
    if args.command == "push":
        count = 0
        for path in sorted(DOCS.glob("*/original.*")):
            doc_id = path.parent.name
            if ids and doc_id not in ids:
                continue
            print(f"{doc_id:50s} {upload(doc_id, path, client)}")
            count += 1
        print(f"done; {count} original(s) checked")
        return 0
    remote = remote_originals(client)
    count = 0
    for doc_id in sorted(ids or remote):
        path = download(doc_id, client, remote)
        print(f"{doc_id:50s} {path.relative_to(ROOT) if path else 'not in bucket'}")
        count += bool(path)
    print(f"done; {count} original(s) present locally")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

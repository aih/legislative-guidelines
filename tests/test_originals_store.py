"""S3 storage of originals, against a mocked S3 (skipped when moto is not installed)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

moto = pytest.importorskip("moto")
boto3 = pytest.importorskip("boto3")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import originals_store  # noqa: E402


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("ORIGINALS_S3_BUCKET", "test-originals")
    monkeypatch.setenv("ORIGINALS_S3_PREFIX", "originals")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setattr(originals_store, "DOCS", tmp_path / "documents")
    monkeypatch.setattr(originals_store, "ROOT", tmp_path)
    with moto.mock_aws():
        client = boto3.client("s3")
        client.create_bucket(Bucket="test-originals")
        yield client, tmp_path / "documents"


def _original(docs: Path, doc_id: str, name: str, data: bytes) -> Path:
    path = docs / doc_id / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def test_upload_and_download_round_trip(store):
    client, docs = store
    path = _original(docs, "xx-guide", "original.pdf", b"%PDF-1.7 test")
    uri = originals_store.upload("xx-guide", path, client)
    assert uri == "s3://test-originals/originals/xx-guide/original.pdf"
    head = client.head_object(Bucket="test-originals", Key="originals/xx-guide/original.pdf")
    assert head["ContentType"] == "application/pdf"
    assert head["Metadata"]["sha256"] == originals_store._sha256(path)

    path.unlink()
    restored = originals_store.download("xx-guide", client)
    assert restored == path
    assert restored.read_bytes() == b"%PDF-1.7 test"


def test_upload_replaces_original_with_other_extension(store):
    client, docs = store
    html = _original(docs, "xx-guide", "original.html", b"<html>old</html>")
    originals_store.upload("xx-guide", html, client)
    html.unlink()
    pdf = _original(docs, "xx-guide", "original.pdf", b"%PDF-1.7 new")
    originals_store.upload("xx-guide", pdf, client)
    remote = originals_store.remote_originals(client)
    assert remote["xx-guide"]["filename"] == "original.pdf"
    keys = [o["Key"] for o in client.list_objects_v2(Bucket="test-originals")["Contents"]]
    assert keys == ["originals/xx-guide/original.pdf"]


def test_download_missing_returns_none(store):
    client, _ = store
    assert originals_store.download("not-there", client) is None


def test_project_specific_variables(monkeypatch):
    for name in ("ORIGINALS_S3_BUCKET", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION", "AWS_REGION"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("S3_BUCKET_LEGDRAFT", "legdraft-bucket")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID_LEGDRAFT", "AKIALEGDRAFT")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY_LEGDRAFT", "secret")
    monkeypatch.setenv("AWS_REGION_LEGDRAFT", "eu-west-2")
    assert originals_store.bucket() == "legdraft-bucket"
    client = originals_store._client()
    assert client.meta.region_name == "eu-west-2"
    assert client._request_signer._credentials.access_key == "AKIALEGDRAFT"

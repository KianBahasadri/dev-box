"""Characterization tests locking in the docs/bind-mounts.md table.

The "Current mounts" table in docs/bind-mounts.md documents exactly the disk
bind-mount devices declared in node-dev.tf, with matching host and container
paths, and an access column that says "Read-only" precisely when the device
sets `readonly = "true"`. These tests assert that current behavior so the two
files cannot silently drift apart.
"""

import re
from pathlib import Path

import hcl2

REPO_ROOT = Path(__file__).resolve().parents[1]
TF_FILE = REPO_ROOT / "node-dev.tf"
DOCS_FILE = REPO_ROOT / "docs" / "bind-mounts.md"

TABLE_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|$")


def _unquote(value):
    # python-hcl2 keeps the surrounding double quotes of HCL string literals
    # and of quoted labels/keys.
    return value.strip('"')


def tf_disk_mounts():
    """Disk bind mounts declared in node-dev.tf.

    Returns a set of (source, path, readonly) tuples, where readonly is the
    string "true" or "false". A disk device without both a source and a path
    (e.g. a future root disk) is not a bind mount and is excluded, matching
    what the docs table documents.
    """
    with TF_FILE.open() as f:
        tf = hcl2.load(f)
    mounts = set()
    for resource in tf["resource"]:
        for instances in resource.values():
            for instance in instances.values():
                for device in instance.get("device", []):
                    if _unquote(device["type"]) != "disk":
                        continue
                    props = device.get("properties", {})
                    if "source" not in props or "path" not in props:
                        continue
                    mounts.add(
                        (
                            _unquote(props["source"]),
                            _unquote(props["path"]),
                            _unquote(props.get("readonly", "false")),
                        )
                    )
    return mounts


def docs_table_rows():
    """Rows of the "Current mounts" table in docs/bind-mounts.md.

    Returns a dict mapping (host path, container path) -> access string.
    """
    rows = {}
    for line in DOCS_FILE.read_text().splitlines():
        match = TABLE_ROW.match(line)
        if match:
            rows[(match.group(1), match.group(2))] = match.group(3)
    return rows


def test_table_lists_exactly_the_tf_disk_mounts():
    tf_paths = {(source, path) for source, path, _ in tf_disk_mounts()}
    doc_paths = set(docs_table_rows())
    assert tf_paths == doc_paths, (
        f"in node-dev.tf but missing from docs/bind-mounts.md: "
        f"{sorted(tf_paths - doc_paths)}; "
        f"in docs/bind-mounts.md but not a disk mount in node-dev.tf: "
        f"{sorted(doc_paths - tf_paths)}"
    )


def test_access_column_matches_readonly_flag():
    docs = docs_table_rows()
    for source, path, readonly in tf_disk_mounts():
        expected = "Read-only" if readonly == "true" else "Read/write"
        assert (source, path) in docs, (
            f"mount {source} -> {path} is missing from docs/bind-mounts.md"
        )
        assert docs[(source, path)] == expected, (
            f"docs/bind-mounts.md says {docs[(source, path)]!r} for "
            f"{source} (readonly={readonly!r} in node-dev.tf), expected {expected!r}"
        )

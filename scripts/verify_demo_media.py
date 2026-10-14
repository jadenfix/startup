"""Verify demo provenance, artifact bytes, complete decode, and repository cleanliness."""
import hashlib
import json
import struct
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "docs" / "demo"


def run(*args):
    return subprocess.run(args, cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    manifest = json.loads((DEMO / "manifest.json").read_text())
    source = manifest["captured_source_commit"]
    assert run("git", "cat-file", "-t", source) == "commit"
    assert run("git", "rev-parse", f"{source}^{{tree}}") == manifest["captured_source_tree"]
    for relative, expected_blob in manifest["source_files"].items():
        path = ROOT / relative
        assert path.is_file(), f"captured source file missing: {relative}"
        assert run("git", "hash-object", str(path)) == expected_blob, f"source changed: {relative}"
    for name, expected in manifest["artifacts"].items():
        path = DEMO / name
        assert path.is_file(), f"artifact missing: {name}"
        assert sha256(path) == expected["sha256"], f"SHA-256 mismatch: {name}"
        assert run("git", "hash-object", str(path)) == expected["git_blob"], f"blob mismatch: {name}"
        if path.suffix in {".gif", ".mp4"}:
            subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"], check=True)
            probe = json.loads(run("ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                "-show_entries", "stream=width,height,nb_read_frames:format=duration", "-of", "json", str(path)))
            stream = probe["streams"][0]
            assert int(stream["width"]) >= 960 and int(stream["height"]) >= 540
            assert int(stream["nb_read_frames"]) > 50
            assert float(probe["format"]["duration"]) >= 10
        elif path.suffix == ".png":
            with path.open("rb") as stream:
                header = stream.read(24)
            assert header[:8] == b"\x89PNG\r\n\x1a\n"
            assert struct.unpack(">II", header[16:24]) == (1280, 720)
    assert not run("git", "status", "--porcelain"), "verification must leave a clean checkout"
    print(f"PASS: source {source} and {len(manifest['artifacts'])} media artifacts verified")


if __name__ == "__main__":
    main()

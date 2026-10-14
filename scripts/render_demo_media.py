"""Render the actual local HTTP smoke output as source-pinned demo media."""
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ANSI = re.compile(r"\x1b\[[0-9;]*m")
WIDTH, HEIGHT = 1280, 720


def run(*args, **kwargs):
    return subprocess.run(args, cwd=ROOT, check=True, text=True, **kwargs)


def one(prefix, lines, occurrence=0):
    found = [line for line in lines if line.startswith(prefix)]
    if len(found) <= occurrence:
        raise RuntimeError(f"Smoke output did not contain {prefix!r}")
    return found[occurrence]


def font(size, bold=False):
    name = "DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)


def frame(path, source, tree, heading, lines, footer):
    image = Image.new("RGB", (WIDTH, HEIGHT), "#09111f")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((45, 35, 1235, 685), 22, fill="#101b2d", outline="#334866", width=2)
    draw.ellipse((75, 67, 91, 83), fill="#ff5f57")
    draw.ellipse((101, 67, 117, 83), fill="#febc2e")
    draw.ellipse((127, 67, 143, 83), fill="#28c840")
    draw.rounded_rectangle((898, 57, 1198, 93), 18, fill="#254d3d")
    draw.text((927, 65), "FICTIONAL LOCAL DEMO", font=font(18, True), fill="#a9f5d0")
    draw.text((75, 120), heading, font=font(34, True), fill="#f4f7fb")
    draw.text((75, 172), f"source {source[:12]}  tree {tree[:12]}", font=font(17), fill="#91a7c4")
    y = 225
    for label, value, color in lines:
        draw.text((82, y), label, font=font(20, True), fill=color)
        y += 35
        for chunk in [value[i:i + 94] for i in range(0, len(value), 94)] or [""]:
            draw.text((82, y), chunk, font=font(18), fill="#d7e2ef")
            y += 29
        y += 18
    draw.line((75, 625, 1205, 625), fill="#334866", width=2)
    draw.text((82, 644), footer, font=font(17), fill="#91a7c4")
    image.save(path)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def probe(path):
    result = subprocess.run([
        "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,nb_read_frames:format=duration",
        "-of", "json", str(path),
    ], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="docs/demo")
    args = parser.parse_args()
    out = ROOT / args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    source = run("git", "rev-parse", "HEAD", capture_output=True).stdout.strip()
    tree = run("git", "rev-parse", "HEAD^{tree}", capture_output=True).stdout.strip()
    smoke = subprocess.run(
        [str(Path(__import__("sys").executable)), "scripts/smoke_delivery.py"],
        cwd=ROOT, check=True, capture_output=True, text=True)
    lines = [ANSI.sub("", line) for line in (smoke.stdout + smoke.stderr).splitlines()]
    pricing = one("/pricing ", lines)
    order = one("/orders ", lines)
    assigned = one("/drivers/assign/", lines)
    repeated = one("/drivers/assign/", lines, 1)
    guard = one("Region guard:", lines)
    delivered = one("Delivered:", lines)
    restarted = one("Restarted API:", lines)
    passed = one("PASS:", lines)
    cards = [
        ("Local delivery workflow", [("SCOPE", one("FICTIONAL LOCAL DEMO", lines), "#a9f5d0")],
         "Disposable SQLite + real localhost HTTP; no paid or live service"),
        ("Price and create", [("HTTP", pricing, "#7dd3fc"), ("HTTP", order, "#7dd3fc")],
         "Responses are captured from scripts/smoke_delivery.py"),
        ("Keep dispatch inside the order region", [("HTTP", assigned, "#7dd3fc"),
         ("CHECK", guard, "#a9f5d0")], "Closer OAK capacity stays available for OAK"),
        ("Repeat safely, then deliver", [("REPEAT", repeated, "#fbcf77"),
         ("STATUS", delivered, "#a9f5d0")], "Repeated assignment returns the existing reservation"),
        ("Restart and read persisted state", [("SQLITE", restarted, "#7dd3fc")],
         "A new server and SQLAlchemy engine reopen the same database"),
        ("Verified workflow complete", [("RESULT", passed, "#a9f5d0")],
         "No routing, payment, authentication, performance, or deployment claim"),
    ]
    durations = [1.6, 1.8, 2.2, 1.8, 2.0, 2.3]
    with tempfile.TemporaryDirectory() as directory:
        temp = Path(directory)
        pngs = []
        for index, card in enumerate(cards):
            path = temp / f"frame-{index:02}.png"
            frame(path, source, tree, *card)
            pngs.append(path)
        concat = temp / "frames.txt"
        concat.write_text("".join(
            f"file '{path}'\nduration {duration}\n" for path, duration in zip(pngs, durations)
        ) + f"file '{pngs[-1]}'\n")
        mp4 = out / "region-safe-delivery.mp4"
        run("ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
            "-i", str(concat), "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(mp4))
        gif = out / "region-safe-delivery.gif"
        palette = temp / "palette.png"
        run("ffmpeg", "-y", "-loglevel", "error", "-i", str(mp4), "-vf",
            "fps=10,scale=960:-1:flags=lanczos,palettegen=stats_mode=diff", str(palette))
        run("ffmpeg", "-y", "-loglevel", "error", "-i", str(mp4), "-i", str(palette),
            "-lavfi", "fps=10,scale=960:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer",
            "-loop", "0", str(gif))
        poster = out / "region-safe-delivery.png"
        pngs[-1].replace(poster)
    artifacts = {}
    for path in (gif, mp4, poster):
        artifacts[path.name] = {
            "sha256": sha256(path),
            "git_blob": run("git", "hash-object", str(path), capture_output=True).stdout.strip(),
            "probe": probe(path) if path.suffix in {".gif", ".mp4"} else {"width": WIDTH, "height": HEIGHT},
        }
    tracked = run("git", "ls-tree", "-r", source, capture_output=True).stdout.splitlines()
    source_files = {line.split("\t", 1)[1]: line.split()[2] for line in tracked}
    manifest = {
        "captured_source_commit": source,
        "captured_source_tree": tree,
        "capture_command": "python scripts/render_demo_media.py",
        "workflow_command": "python scripts/smoke_delivery.py",
        "scope": "fictional local SQLite and localhost HTTP only; no live dispatch, routing, payment, provider, deployment, or performance claim",
        "source_files": source_files,
        "observed_output": [pricing, order, assigned, guard, repeated, delivered, restarted, passed],
        "artifacts": artifacts,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()

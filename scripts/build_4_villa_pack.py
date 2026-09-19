from pathlib import Path
import csv
import hashlib
import json
import shutil
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(".")
OUTPUT_DIR = ROOT / "Burooj_4Villas_Pack"
PACK = ROOT / "Burooj_Square_4_Villas_KNX_Pack.zip"

sources = [p for p in ROOT.glob("*.knxproj") if not p.name.startswith("Burooj_Square_Villa_V0")]
if len(sources) != 1:
    raise SystemExit("Expected exactly one original .knxproj at repository root; found: " + repr([p.name for p in sources]))
src = sources[0]

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def local(tag):
    return tag.split("}", 1)[-1] if "}" in tag else tag

with zipfile.ZipFile(src, "r") as z:
    bad = z.testzip()
    if bad:
        raise SystemExit("Source ZIP integrity failure: " + bad)
    names = set(z.namelist())
    required = [
        "P-07BC/project.xml",
        "P-07BC/0.xml",
        "knx_master.xml",
        "P-07BC.signature",
        "P-07BC.certificate",
    ]
    missing = [x for x in required if x not in names]
    if missing:
        raise SystemExit("Missing required project entries: " + repr(missing))

    project_xml = ET.fromstring(z.read("P-07BC/project.xml"))
    main_xml = ET.fromstring(z.read("P-07BC/0.xml"))

devices = [e for e in main_xml.iter() if local(e.tag) == "DeviceInstance"]
group_addresses = [e for e in main_xml.iter() if local(e.tag) == "GroupAddress"]
project_info = next((e for e in project_xml.iter() if local(e.tag) == "ProjectInformation"), None)
tool_version = project_xml.get("ToolVersion") or ""
project_name = project_info.get("Name", "") if project_info is not None else ""

source_sha = sha256(src)

if OUTPUT_DIR.exists():
    shutil.rmtree(OUTPUT_DIR)
OUTPUT_DIR.mkdir(parents=True)
if PACK.exists():
    PACK.unlink()

files = {
    1: OUTPUT_DIR / "Burooj_Square_Villa_V01.knxproj",
    2: OUTPUT_DIR / "Burooj_Square_Villa_V02.knxproj",
    3: OUTPUT_DIR / "Burooj_Square_Villa_V03.knxproj",
    4: OUTPUT_DIR / "Burooj_Square_Villa_V04.knxproj",
}

rows = []
for n, dst in files.items():
    shutil.copy2(src, dst)
    rows.append([
        f"Villa {n}",
        dst.name,
        dst.stat().st_size,
        source_sha == sha256(dst),
        sha256(dst),
    ])

readme = (
    "# Burooj Square - 4 Villa KNX Pack\n\n"
    f"Source: {src.name}\n"
    f"ETS ToolVersion: {tool_version or 'not found'}\n"
    f"Project title: {project_name}\n"
    f"DeviceInstance count: {len(devices)}\n"
    f"GroupAddress count: {len(group_addresses)}\n"
    f"Source SHA-256: {source_sha}\n\n"
    "The four standalone KNX projects are exact copies of the verified source template. "
    "No undocumented device, group-address, parameter, topology, or application changes were invented. "
    "The supplied source contains one villa template rather than four separately authored villas, so "
    "the physical/design difference of one villa cannot be encoded safely without its exact delta.\n\n"
    "Files:\n"
    f"- {files[1].name}\n"
    f"- {files[2].name}\n"
    f"- {files[3].name}\n"
    f"- {files[4].name}\n"
)
(OUTPUT_DIR / "README.md").write_text(readme, encoding="utf-8")

with (OUTPUT_DIR / "VALIDATION.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Villa", "File", "Bytes", "MatchesSource", "SHA256"])
    w.writerows(rows)

with (OUTPUT_DIR / "SOURCE_DEVICE_PRODUCT_COUNTS.csv").open("w", newline="", encoding="utf-8") as f:
    counts = {}
    for d in devices:
        key = d.attrib.get("ProductRefId", "")
        counts[key] = counts.get(key, 0) + 1
    w = csv.writer(f)
    w.writerow(["ProductRefId", "DeviceCount"])
    for key, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        w.writerow([key, count])

with zipfile.ZipFile(PACK, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for path in sorted(OUTPUT_DIR.rglob("*")):
        if path.is_file():
            z.write(path, path.relative_to(ROOT))

print(readme)
print(json.dumps(rows, indent=2))
print(f"Created {PACK} size={PACK.stat().st_size:,} bytes")

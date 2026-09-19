from pathlib import Path
import csv, json, re, shutil, zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

ROOT = Path(".")
SOURCE = next((p for p in ROOT.glob("*.knxproj") if not p.name.startswith("Burooj_Square_Villa_V0")), None)
if SOURCE is None:
    raise SystemExit("No source .knxproj found")

OUT = ROOT / "Burooj_Simulation_Test_Pack"
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir()

with zipfile.ZipFile(SOURCE) as z:
    root = ET.fromstring(z.read("P-07BC/0.xml"))
    project = ET.fromstring(z.read("P-07BC/project.xml"))

def local(tag):
    return tag.split("}",1)[-1] if "}" in tag else tag

def attrs(e):
    return {local(k): v for k,v in e.attrib.items()}

parent = {}
for p in root.iter():
    for c in list(p):
        parent[c] = p

def nearest_device(e):
    p = parent.get(e)
    while p is not None:
        if local(p.tag) == "DeviceInstance":
            return p
        p = parent.get(p)
    return None

devices = {}
for e in root.iter():
    if local(e.tag) == "DeviceInstance":
        a = attrs(e)
        devices[a.get("Id","")] = a

groups = {}
for e in root.iter():
    if local(e.tag) == "GroupAddress":
        a = attrs(e)
        groups[a.get("Id","")] = a

device_ga = defaultdict(set)
ga_devices = defaultdict(set)

for e in root.iter():
    if local(e.tag) not in {"ComObjectInstanceRef","GroupObjectInstance"}:
        continue
    d = nearest_device(e)
    if d is None:
        continue
    did = attrs(d).get("Id","")
    blob = json.dumps(attrs(e), ensure_ascii=False)
    refs = re.findall(r"GA-\d+", blob)
    for short in sorted(set(refs)):
        gid = "P-07BC-0_" + short
        if gid in groups:
            device_ga[did].add(gid)
            ga_devices[gid].add(did)

def classify(name, dpt):
    n = (name or "").strip().lower()
    d = (dpt or "").strip().upper()
    info = any(x in n for x in ["info", "status", "feedback", "state"])
    if "error" in n:
        role = "feedback/error"
    elif info:
        role = "feedback"
    else:
        role = "command/value"

    if d == "DPST-1-1":
        kind = "switch"; values = "0,1"
    elif d == "DPST-1-6":
        kind = "1-bit control"; values = "0,1"
    elif d == "DPST-1-8":
        kind = "move/up-down"; values = "0,1"
    elif d == "DPST-1-17":
        kind = "stop"; values = "0,1"
    elif d == "DPST-3-7":
        kind = "relative dimming"; values = "dim telegrams"
    elif d == "DPST-5-1":
        kind = "8-bit scaling"; values = "0,50,100"
    elif d == "DPST-7-7":
        kind = "2-byte unsigned value"; values = "use application range"
    elif d == "DPST-9-1":
        kind = "2-byte float / temperature-style value"; values = "18.0,22.0,25.0"
    elif d == "DPST-16-0":
        kind = "text/string"; values = "read/observe first"
    elif d == "DPST-20-105":
        kind = "HVAC mode enum"; values = "cycle valid mode values"
    elif d:
        kind = "other DPT"; values = "use exact DPT domain"
    else:
        kind = "unknown DPT"; values = "inspect before writing"
    return role, kind, values

ga_rows = []
for gid, a in sorted(groups.items(), key=lambda kv: (int(kv[1].get("Address","-1")) if kv[1].get("Address","").isdigit() else 10**9, kv[0])):
    role, kind, values = classify(a.get("Name",""), a.get("DatapointType",""))
    linked = sorted(ga_devices.get(gid, set()))
    linked_names = []
    for did in linked:
        da = devices.get(did, {})
        label = da.get("Name","").strip() or da.get("ProductRefId","").strip() or did
        linked_names.append(f"{did}:{label}")

    if role == "feedback":
        action = "READ/OBSERVE"
        expected = "Observe telegram/value; do not force-write unless explicitly writable."
    elif kind == "switch":
        action = "WRITE 0 THEN 1"
        expected = "Command accepted; linked status should change."
    elif kind == "8-bit scaling":
        action = "WRITE 0,50,100"
        expected = "Linked value changes low/mid/high."
    elif kind == "2-byte float / temperature-style value":
        action = "WRITE 18.0,22.0,25.0"
        expected = "Linked temperature/setpoint/value updates."
    elif kind in {"move/up-down","stop","1-bit control"}:
        action = "WRITE 0 THEN 1"
        expected = "Linked function reacts; verify corresponding feedback."
    elif kind == "relative dimming":
        action = "SEND DIM TELEGRAMS"
        expected = "Linked dimmer changes according to configured semantics."
    elif kind == "HVAC mode enum":
        action = "CYCLE VALID MODES"
        expected = "Mode changes and feedback updates."
    else:
        action = "READ FIRST"
        expected = "Verify exact DPT/object semantics before writing."

    ga_rows.append([
        gid, a.get("Address",""), a.get("Name","").strip(), a.get("DatapointType",""),
        role, kind, action, values, " | ".join(linked_names), len(linked), expected
    ])

with (OUT/"GROUP_TEST_MATRIX.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["GroupAddressId","RawAddress","Name","DatapointType","Role","Kind","RecommendedAction","TestValues","LinkedDevices","LinkedDeviceCount","ExpectedObservation"])
    w.writerows(ga_rows)

with (OUT/"DEVICE_GA_MATRIX.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["DeviceId","IndividualAddress","DeviceName","ProductRefId","Hardware2ProgramRefId","GroupAddressId","RawAddress","GroupName","DatapointType","Role","Kind"])
    for did, ga_ids in sorted(device_ga.items()):
        da = devices.get(did,{})
        for gid in sorted(ga_ids, key=lambda x:int(groups[x].get("Address","-1")) if groups[x].get("Address","").isdigit() else 10**9):
            ga = groups[gid]
            role, kind, _ = classify(ga.get("Name",""), ga.get("DatapointType",""))
            w.writerow([
                did, da.get("Address",""), da.get("Name","").strip(), da.get("ProductRefId",""),
                da.get("Hardware2ProgramRefId",""), gid, ga.get("Address",""),
                ga.get("Name","").strip(), ga.get("DatapointType",""), role, kind
            ])

counts = Counter(r[5] for r in ga_rows)
roles = Counter(r[4] for r in ga_rows)
dpt_counts = Counter(r[3] for r in ga_rows)
linked_ga = sum(1 for r in ga_rows if r[9] > 0)

project_info = next((e for e in project.iter() if local(e.tag)=="ProjectInformation"), None)
tool_version = project.get("ToolVersion","")
project_name = project_info.get("Name","") if project_info is not None else ""

summary = [
    "# Burooj Square — KNX Simulation Test Pack",
    "",
    f"Source project: {SOURCE.name}",
    f"ETS project title: {project_name}",
    f"ETS ToolVersion in source: {tool_version or 'not found'}",
    "",
    "## Source coverage",
    f"- Group addresses: {len(groups)}",
    f"- Device instances: {len(devices)}",
    f"- Group addresses linked to at least one DeviceInstance: {linked_ga}",
    f"- Device-to-Group Address links found: {sum(len(v) for v in device_ga.values())}",
    "",
    "## What this pack does",
    "Turns the real ETS project database into a simulation-oriented test matrix. "
    "It does not rewrite the source project or invent missing device behavior. "
    "Use it with KNX Virtual and ETS Group Monitor to exercise Group Addresses and observe telegrams.",
    "",
    "## Important limitation",
    "The source project contains manufacturer-specific Zennio devices. KNX Virtual simulates its own virtual device set, "
    "not every Zennio application in this project. Therefore use this pack for telegram/DPT/Group Address validation and "
    "for end-to-end behavior on the subset that can be mapped to KNX Virtual virtual devices. "
    "A Zennio-specific application parameter cannot be declared fully simulated unless a matching virtual device exists.",
    "",
    "## Files",
    "- GROUP_TEST_MATRIX.csv — one row per Group Address with DPT, role, links and suggested test.",
    "- DEVICE_GA_MATRIX.csv — device-to-Group Address relationships extracted from the actual project.",
    "- SIMULATION_SETUP.md — step-by-step setup and testing workflow.",
    "- OPERATOR_CHECKLIST.md — quick operator checklist.",
    "",
    "## Role counts",
]
summary += [f"- {k}: {v}" for k,v in sorted(roles.items())]
summary += ["", "## Test-kind counts"]
summary += [f"- {k}: {v}" for k,v in counts.most_common()]
summary += ["", "## DPT counts"]
summary += [f"- {k or '(blank)'}: {v}" for k,v in dpt_counts.most_common()]

(OUT/"SUMMARY.md").write_text("\n".join(summary), encoding="utf-8")

setup = """# Simulation setup — Burooj Square

## 1. Install the simulator

Install the current ETS and KNX Virtual on the same Windows PC. KNX Association states that KNX Virtual is a PC-based simulator that behaves like a real KNX installation and can be used with ETS without physical KNX hardware.

Use only the official KNX download from MyKNX. Do not use third-party copies.

## 2. Keep the original project safe

Work from Burooj_Square_Villa_V01.knxproj or another copy. Do not overwrite the verified original backup.

## 3. Connect ETS to KNX Virtual

Start KNX Virtual, then start ETS and select the KNX Virtual connection/interface in the connection settings.

## 4. Test the real project's Group Addresses

Open GROUP_TEST_MATRIX.csv.

For every row whose Role is command/value:
1. Open ETS Group Monitor.
2. Send the RecommendedAction/TestValues from the row.
3. Watch the returned telegrams and any matching feedback/status Group Address.
4. Record a result outside this pack.

For feedback/status rows, use READ/OBSERVE and do not force-write unless the application explicitly defines that object as writable.

## 5. Start with these functional groups

Test these first because they are represented clearly by their DPT/name:
- DPST-1-1 switching
- DPST-5-1 scaling
- DPST-3-7 relative dimming
- DPST-1-8 move/up-down
- DPST-1-17 stop
- DPST-9-1 temperature/setpoint-style values
- DPST-20-105 HVAC mode

Then continue through the remaining rows using the exact DPT from the CSV.

## 6. What counts as verified

Mark a function verified only when:
- ETS accepts the telegram without a DPT mismatch;
- the compatible KNX Virtual device/load reacts when one is configured;
- feedback/status returns on the expected Group Address;
- no unexpected linked object changes are seen.

## 7. Important boundary

A KNX Virtual pass verifies the KNX telegram path and the virtual function under test. It does not prove every Zennio-specific parameter in the final hardware. Those require final-device commissioning and functional testing.
"""
(OUT/"SIMULATION_SETUP.md").write_text(setup, encoding="utf-8")

checklist = """# Operator checklist

- [ ] Install current ETS + KNX Virtual on Windows
- [ ] Open a copy of Villa 01
- [ ] Connect ETS to KNX Virtual
- [ ] Test switching
- [ ] Test scaling/dimming
- [ ] Test move/stop
- [ ] Test temperature/setpoint values
- [ ] Test HVAC modes
- [ ] Observe feedback/status telegrams
- [ ] Record DPT/object mismatches
- [ ] Keep simulator results separate from final hardware commissioning
"""
(OUT/"OPERATOR_CHECKLIST.md").write_text(checklist, encoding="utf-8")

print("\n".join(summary))

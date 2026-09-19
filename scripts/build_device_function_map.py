from pathlib import Path
import csv
import json
import re
import shutil
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict

ROOT = Path(".")
srcs = list(ROOT.glob("*.knxproj"))
srcs = [p for p in srcs if not p.name.startswith("Burooj_Square_Villa_V0")]
if len(srcs) != 1:
    raise SystemExit("Expected one source .knxproj, found: " + repr([p.name for p in srcs]))
src = srcs[0]

OUT = ROOT / "knx-device-map"
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir()

def local(tag):
    return tag.split("}",1)[-1] if "}" in tag else tag

def clean_attrs(e):
    return {local(k): v for k,v in e.attrib.items()}

with zipfile.ZipFile(src) as z:
    names = z.namelist()
    xml_blobs = {}
    for n in names:
        if n.lower().endswith(".xml"):
            try:
                xml_blobs[n] = z.read(n)
            except Exception:
                pass

main = ET.fromstring(xml_blobs["P-07BC/0.xml"])

# Global index of useful definition/reference elements from every XML.
by_id = defaultdict(list)
for filename, blob in xml_blobs.items():
    try:
        r = ET.fromstring(blob)
    except Exception:
        continue
    for e in r.iter():
        a = clean_attrs(e)
        for key in ("Id","RefId","Code"):
            v = a.get(key)
            if v:
                by_id[v].append((filename, local(e.tag), a))

# Device and hierarchy maps.
parent = {}
for p in main.iter():
    for c in list(p):
        parent[c] = p

devices = {}
for e in main.iter():
    if local(e.tag) == "DeviceInstance":
        a = clean_attrs(e)
        devices[a.get("Id","")] = e

groups = {}
for e in main.iter():
    if local(e.tag) == "GroupAddress":
        a = clean_attrs(e)
        groups[a.get("Id","")] = a

def nearest_device(e):
    p = parent.get(e)
    while p is not None:
        if local(p.tag) == "DeviceInstance":
            return p
        p = parent.get(p)
    return None

def device_path(d):
    out = []
    p = parent.get(d)
    while p is not None:
        t = local(p.tag)
        a = clean_attrs(p)
        if t in {"Space","BuildingPart","Floor","Room","DistributionBoard","Node","Installation","Line","Area","Segment"}:
            label = a.get("Name","").strip() or a.get("Id","")
            if label:
                out.append(f"{t}:{label}")
        p = parent.get(p)
    return " > ".join(reversed(out))

# Build actual device object/channel map.
rows = []
for did, d in sorted(devices.items(), key=lambda kv: (int(clean_attrs(kv[1]).get("Address","9999")) if clean_attrs(kv[1]).get("Address","").isdigit() else 9999, kv[0])):
    da = clean_attrs(d)
    object_rows = []
    channel_ids = set()

    for e in d.iter():
        t = local(e.tag)
        if t not in {"ComObjectInstanceRef","GroupObjectInstance","Channel"}:
            continue
        a = clean_attrs(e)
        cid = a.get("ChannelId","")
        if t == "Channel" and cid == "":
            cid = a.get("Id","")
        if cid:
            channel_ids.add(cid)
        if t in {"ComObjectInstanceRef","GroupObjectInstance"}:
            # KNX project stores GAs in Links="GA-xxx".
            links = a.get("Links","")
            ga_ids = []
            for short in re.findall(r"GA-\d+", links):
                gid = "P-07BC-0_" + short
                if gid in groups:
                    ga_ids.append(gid)
            if not ga_ids:
                ga_ids = [g for g in re.findall(r"P-07BC-0_GA-\d+", json.dumps(a)) if g in groups]
            refs = []
            for refkey in ("RefId","Id"):
                v = a.get(refkey,"")
                if v:
                    refs.extend(by_id.get(v, []))
                    if "_" in v:
                        refs.extend(by_id.get(v.split("_",1)[0], []))
            # Keep a compact unique definition summary.
            defs = []
            seen = set()
            for fn, tag, attrs in refs:
                sig = (fn, tag, tuple(sorted(attrs.items())))
                if sig in seen:
                    continue
                seen.add(sig)
                defs.append({
                    "file": fn,
                    "tag": tag,
                    "attrs": {k:v for k,v in attrs.items() if k in {
                        "Id","RefId","Name","Description","Function","Number","NumberOfChannels","Type",
                        "Text","ChannelId","ComObjectNumber","ObjectNumber","Flags","DatapointType"
                    }}
                })
            object_rows.append({
                "tag": t,
                "ref_id": a.get("RefId",""),
                "links": ga_ids,
                "channel_id": a.get("ChannelId",""),
                "instance_attrs": a,
                "definitions": defs[:8]
            })

    # Also attach definitions for each channel ID.
    channels = []
    for cid in sorted(channel_ids):
        defs = []
        seen = set()
        keys = [cid]
        if "_" in cid:
            keys.append(cid.split("_",1)[0])
        for key in keys:
            for item in by_id.get(key, []):
                sig = (item[0],item[1],tuple(sorted(item[2].items())))
                if sig in seen:
                    continue
                seen.add(sig)
                defs.append({
                    "file":item[0],"tag":item[1],
                    "attrs":{k:v for k,v in item[2].items() if k in {
                        "Id","RefId","Name","Description","Function","Number","Type","ChannelId"
                    }}
                })
        channels.append({"channel_id":cid,"definitions":defs[:10]})

    rows.append({
        "device_id": did,
        "address": da.get("Address",""),
        "name": da.get("Name",""),
        "product_ref": da.get("ProductRefId",""),
        "hardware_program": da.get("Hardware2ProgramRefId",""),
        "puid": da.get("Puid",""),
        "path": device_path(d),
        "channels": channels,
        "objects": object_rows
    })

# Human-friendly logical family classification, explicitly from product IDs/names.
def family(product):
    p=(product or "").upper()
    if "ZIOMB8V4" in p: return "Relay actuator 8-channel"
    if "ZIOMB16V4" in p: return "Relay actuator 16-channel"
    if "ZIOMB24V2" in p: return "Relay actuator 24-channel"
    if "ZIOMBSH8V3" in p: return "Shutter actuator 8-channel"
    if "ZDID64V3" in p: return "DALI gateway/driver"
    if "ZPSU640" in p: return "KNX power supply"
    if "ZSYKIPISC" in p: return "KIPI SC / communication gateway"
    if "ZCL.2DLG1" in p: return "Universal logic controller / actuator"
    if "ZVIT55X4" in p: return "Tecla 55 X4 keypad"
    if "ZVIT55X6" in p: return "Tecla 55 X6 keypad"
    if "ZVI.2DTMDP4" in p: return "Touch-MyDesign Plus 4"
    if "ZVI.2DTMDP6" in p: return "Touch-MyDesign Plus 6"
    if "ZVI.2DTMDP8" in p: return "Touch-MyDesign Plus 8"
    if "ZVIZ35V2" in p: return "Z35 v2 touch panel"
    if "ZVIZ100" in p: return "Z100 touch panel"
    if "ZPDEZTPV2" in p: return "Presence/occupancy detector"
    if "ZN1CL.2DIRSC" in p: return "IRSC infrared remote interface"
    return "Other / inspect"

# Device schedule.
with (OUT/"DEVICE_SCHEDULE.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w=csv.writer(f)
    w.writerow([
        "DeviceId","IndividualAddress","Name","ProductRefId","Hardware2ProgramRefId","Puid",
        "ModelFamily","LogicalPath","ChannelIds","ObjectInstanceCount","LinkedGroupAddressCount"
    ])
    for d in rows:
        linked = set()
        for o in d["objects"]:
            linked.update(o["links"])
        w.writerow([
            d["device_id"],d["address"],d["name"].strip(),d["product_ref"],d["hardware_program"],d["puid"],
            family(d["product_ref"]),d["path"]," | ".join(c["channel_id"] for c in d["channels"]),
            len(d["objects"]),len(linked)
        ])

# Detailed per-object schedule, with definition text when available.
with (OUT/"DEVICE_FUNCTION_SCHEDULE.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w=csv.writer(f)
    w.writerow([
        "DeviceId","IndividualAddress","DeviceName","ProductRefId","ModelFamily",
        "ChannelId","ObjectRefId","GroupAddressId","RawAddress","GroupName","GroupDPT",
        "DefinitionFile","DefinitionTag","DefinitionId","DefinitionName","DefinitionDescription",
        "DefinitionFunction","InstanceAttributes"
    ])
    for d in rows:
        for o in d["objects"]:
            for gid in o["links"] or [""]:
                ga=groups.get(gid,{})
                defs=o["definitions"] or [{}]
                for de in defs:
                    a=de.get("attrs",{})
                    w.writerow([
                        d["device_id"],d["address"],d["name"].strip(),d["product_ref"],family(d["product_ref"]),
                        o["channel_id"],o["ref_id"],gid,ga.get("Address",""),ga.get("Name","").strip(),ga.get("DatapointType",""),
                        de.get("file",""),de.get("tag",""),a.get("Id",a.get("RefId","")),
                        a.get("Name",""),a.get("Description",""),a.get("Function",""),
                        json.dumps(o["instance_attrs"],ensure_ascii=False)
                    ])

# Human-oriented "what this device is for" summary based on linked GA names plus product family.
with (OUT/"DEVICE_USAGE_SUMMARY.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w=csv.writer(f)
    w.writerow(["DeviceId","Address","DeviceName","ModelFamily","ProductRefId","LikelyFunctionalDomains","EvidenceGroupNames"])
    domain_keywords = {
        "Lighting":["light","lamp","dimm","on/off","scene","led","downlight","lighting"],
        "Blinds/Shutters":["blind","curtain","shutter","move","stop"],
        "DALI":["dali"],
        "HVAC":["mode","fan","set point","setpoint","temp","temperature","hvac","clim"],
        "Garage":["garage"],
        "Intercom":["intercom","door","entry"],
        "Sensors":["presence","occupancy","motion","lux"],
        "Security":["alarm","security","lock"],
        "General IO":["input","output","switch","relay"]
    }
    for d in rows:
        names=[]
        for o in d["objects"]:
            for gid in o["links"]:
                if gid in groups:
                    names.append(groups[gid].get("Name","").strip())
        domains=set()
        alltext=" | ".join(names).lower()
        for dom, keys in domain_keywords.items():
            if any(k in alltext for k in keys):
                domains.add(dom)
        w.writerow([
            d["device_id"],d["address"],d["name"].strip(),family(d["product_ref"]),d["product_ref"],
            "; ".join(sorted(domains)) if domains else "Not inferable from GA names",
            " | ".join(sorted(set(n for n in names if n)))
        ])

# Global GA schedule including linked device/object refs.
with (OUT/"GROUP_ADDRESS_SCHEDULE.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w=csv.writer(f)
    w.writerow(["GroupAddressId","RawAddress","Name","DatapointType","LinkedDeviceCount","LinkedDevices","SuggestedLogicalDomain"])
    for gid,a in sorted(groups.items(), key=lambda kv: (int(kv[1].get("Address","999999")) if kv[1].get("Address","").isdigit() else 999999, kv[0])):
        dlist=[]
        for d in rows:
            if any(gid in o["links"] for o in d["objects"]):
                dlist.append(f'{d["device_id"]}({d["address"]}) {family(d["product_ref"])}')
        nm=a.get("Name","").lower()
        domains=[]
        for dom,keys in domain_keywords.items():
            if any(k in nm for k in keys):
                domains.append(dom)
        w.writerow([gid,a.get("Address",""),a.get("Name","").strip(),a.get("DatapointType",""),len(dlist)," | ".join(dlist),"; ".join(domains)])

# Compact JSON for future analysis.
(OUT/"DEVICE_MAP.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

summary = [
    "# KNX device/function map",
    "",
    f"Source: {src.name}",
    f"Devices: {len(rows)}",
    f"Group addresses: {len(groups)}",
    "",
    "Files:",
    "- DEVICE_SCHEDULE.csv",
    "- DEVICE_FUNCTION_SCHEDULE.csv",
    "- DEVICE_USAGE_SUMMARY.csv",
    "- GROUP_ADDRESS_SCHEDULE.csv",
    "- DEVICE_MAP.json",
]
(OUT/"SUMMARY.md").write_text("\n".join(summary),encoding="utf-8")
print("\n".join(summary))

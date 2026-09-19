from pathlib import Path
import csv, re, zipfile, xml.etree.ElementTree as ET
from collections import defaultdict

ROOT = Path(".")
srcs=[p for p in ROOT.glob("*.knxproj") if not p.name.startswith("Burooj_Square_Villa_V0")]
if len(srcs)!=1: raise SystemExit("Expected one source KNX project")
src=srcs[0]

with zipfile.ZipFile(src) as z:
    root=ET.fromstring(z.read("P-07BC/0.xml"))
    project=ET.fromstring(z.read("P-07BC/project.xml"))

def local(tag): return tag.split("}",1)[-1] if "}" in tag else tag
def attrs(e): return {local(k):v for k,v in e.attrib.items()}

parent={}
for p in root.iter():
    for c in list(p): parent[c]=p

devices={}
for e in root.iter():
    if local(e.tag)=="DeviceInstance":
        devices[attrs(e).get("Id","")]=e

groups={}
for e in root.iter():
    if local(e.tag)=="GroupAddress":
        groups[attrs(e).get("Id","")]=attrs(e)

def nearest_device(e):
    p=parent.get(e)
    while p is not None:
        if local(p.tag)=="DeviceInstance": return p
        p=parent.get(p)
    return None

device_gas=defaultdict(list)
for e in root.iter():
    if local(e.tag) not in {"ComObjectInstanceRef","GroupObjectInstance"}: continue
    d=nearest_device(e)
    if d is None: continue
    did=attrs(d).get("Id","")
    for short in re.findall(r"GA-\d+", attrs(e).get("Links","")):
        gid="P-07BC-0_"+short
        if gid in groups and gid not in device_gas[did]:
            device_gas[did].append(gid)

def family(prod):
    p=(prod or "").upper()
    if "ZIOMB8V4" in p: return "MAXinBOX 8 v4 — 8 relay outputs"
    if "ZIOMB16V4" in p: return "MAXinBOX 16 v4 — 16 relay outputs"
    if "ZIOMB24V2" in p: return "MAXinBOX 24 v2 — 24 relay outputs"
    if "ZIOMBSH8V3" in p: return "MAXinBOX SHUTTER 8CH v3 — 8 shutter channels"
    if "ZDID64V3" in p: return "DALI BOX Interface 64 v3 — up to 64 DALI ballasts"
    if "ZPSU640" in p: return "KUPSupply 640 mA KNX power supply"
    if "ZSYKIPISC" in p: return "KIPI SC — KNX-IP interface"
    if "ZCL.2DLG1" in p: return "Logic controller (project exposes HVAC blocks)"
    if "ZVIT55X4" in p: return "Tecla 55 X4 — capacitive keypad"
    if "ZVIT55X6" in p: return "Tecla 55 X6 — capacitive keypad"
    if "ZVI.2DTMDP4" in p: return "Touch-MyDesign Plus 4"
    if "ZVI.2DTMDP6" in p: return "Touch-MyDesign Plus 6"
    if "ZVI.2DTMDP8" in p: return "Touch-MyDesign Plus 8"
    if "ZVIZ35V2" in p: return "Z35 v2 — touch panel / thermostat"
    if "ZVIZ100" in p: return "Z100 — 10-inch touch panel"
    if "ZPDEZTPV2" in p: return "EyeZen TP v2 — motion/lux sensor"
    if "ZN1111-4" in p or "ZN1CL.2DIRSC" in p: return "IRSC — A/C infrared controller"
    return "Other"

def ga_names(did):
    out=[]
    for gid in device_gas.get(did,[]):
        a=groups[gid]
        out.append((a.get("Address",""),a.get("Name","").strip(),a.get("DatapointType",""),gid))
    return out

wiring=[]
for did,d in sorted(devices.items(), key=lambda kv:int(attrs(kv[1]).get("Address","9999")) if attrs(kv[1]).get("Address","").isdigit() else 9999):
    da=attrs(d); prod=da.get("ProductRefId",""); fam=family(prod); addr=da.get("Address",""); dns=ga_names(did)

    if "ZIOMB8V4" in prod:
        cmd=[x for x in dns if x[1].startswith("On/Off ") and not x[1].endswith("Info")]
        assignments=[(1,"Relay 1","Move Garage","Garage motor command","Inferred from 8-output capacity + project GA sequence"),
                     (2,"Relay 2","Stop Garage","Garage stop","Inferred; verify physical terminal on electrical schedule")]
        for i in range(6):
            n=3+i; gname=f"On/Off {n}"
            assignments.append((n,f"Relay {n}",gname,"Lighting output","Inferred from project GA sequence"))
        for ch,label,gname,domain,evidence in assignments:
            ga=next((x for x in dns if x[1]==gname),None)
            wiring.append([did,addr,fam,ch,label,gname,ga[2] if ga else "",domain,evidence])

    elif "ZIOMB16V4" in prod:
        cmd=[x for x in dns if x[1].startswith("On/Off ") and not x[1].endswith("Info")]
        for ch in range(1,17):
            n=16+ch; gname=f"On/Off {n}"
            ga=next((x for x in cmd if x[1]==gname),None)
            wiring.append([did,addr,fam,ch,f"Relay {ch}",gname,ga[2] if ga else "","Lighting output","Sequential GA mapping; verify terminal assignment on electrical schedule"])

    elif "ZIOMB24V2" in prod:
        cmd=[x for x in dns if x[1].startswith("On/Off ") and not x[1].endswith("Info")]
        for ch in range(1,25):
            n=48+ch; gname=f"On/Off {n}"
            ga=next((x for x in cmd if x[1]==gname),None)
            wiring.append([did,addr,fam,ch,f"Relay {ch}",gname,ga[2] if ga else "","Lighting output","Sequential GA mapping; verify terminal assignment on electrical schedule"])

    elif "ZIOMBSH8V3" in prod:
        base=0 if int(addr)==9 else 8 if int(addr)==10 else 16
        for ch in range(1,9):
            n=base+ch
            gname=f"{n} Move"
            ga=next((x for x in dns if x[1]==gname),None)
            present = bool(ga)
            wiring.append([did,addr,fam,ch,f"Shutter channel {ch}",gname,ga[2] if ga else "","Blind/shutter motor",
                           "Channel range follows GA naming; channels 3-8 on address 11 have no linked GAs" if int(addr)==11 and ch>=3 else "GA sequence mapping; verify physical motor wiring"])

    elif "ZCL.2DLG1" in prod:
        seen=set()
        for x in dns:
            gname=x[1]
            m=re.match(r"^(\d+) ",gname)
            if not m or gname in seen: continue
            if any(token in gname for token in ["Mode","ON/Off","Fan","Set Point","Temp.","Error Code"]):
                seen.add(gname)
                n=int(m.group(1))
                wiring.append([did,addr,fam,n,f"HVAC logical block {n}",gname,x[2],"HVAC logic","Logical/software function from project; not a physical HVAC power output"])

    elif "ZN1111-4" in prod or "ZN1CL.2DIRSC" in prod:
        wiring.append([did,addr,fam,"","IR emitter/controller","","","Air-conditioner IR","Device type is explicit; no linked GAs in current DeviceInstance"])

    elif "ZDID64V3" in prod:
        wiring.append([did,addr,fam,"","DALI bus","","","DALI lighting","Device type is explicit; exact ballast/group mapping is not visible from the DeviceInstance links"])

    elif "ZPDEZTPV2" in prod:
        wiring.append([did,addr,fam,"","Ceiling presence/lux sensor","","","Sensors","Device type is explicit; no linked GAs in current DeviceInstance"])

    elif "ZVIZ100" in prod:
        for dom, words in {
            "Lighting":["On/Off","Dimming"],
            "Blinds":["Move","Stop","Status"],
            "Garage":["Garage"],
            "HVAC":["Mode","Fan","Set Point","Temp."]
        }.items():
            matched=[x for x in dns if any(w.lower() in x[1].lower() for w in words)]
            if matched:
                wiring.append([did,addr,fam,dom,f"{len(matched)} linked objects",", ".join(sorted(set(x[1] for x in matched))),"","Control / visualization","Project links show this panel as a control point; it is not a load output"])

    else:
        wiring.append([did,addr,fam,"","","","","Control/device","No physical terminal-to-load mapping is encoded in the project instance"])

with (ROOT/"INSTALLER_WIRING_SCHEDULE.csv").open("w",newline="",encoding="utf-8-sig") as f:
    w=csv.writer(f)
    w.writerow(["DeviceId","IndividualAddress","Device","ChannelOrDomain","OutputOrObject","ProjectGroupName","DPT","PhysicalDomain","EvidenceLevel"])
    w.writerows(wiring)

overview=[]
for did,d in sorted(devices.items(), key=lambda kv:int(attrs(kv[1]).get("Address","9999")) if attrs(kv[1]).get("Address","").isdigit() else 9999):
    a=attrs(d)
    overview.append([did,a.get("Address",""),a.get("Name","").strip(),family(a.get("ProductRefId","")),len(set(device_gas.get(did,[])))])
with (ROOT/"INSTALLER_DEVICE_OVERVIEW.csv").open("w",newline="",encoding="utf-8-sig") as f:
    w=csv.writer(f); w.writerow(["DeviceId","IndividualAddress","Name","DeviceType","LinkedGroupAddressCount"]); w.writerows(overview)

keyword_groups=[
    ("Lighting",["light","lamp","dimm","on/off","dali"]),
    ("HVAC",["mode","fan","set point","temp.","error code","hvac"]),
    ("Blinds/Shutters",["move","stop","status"]),
    ("Garage",["garage"]),
    ("Intercom/Access",["intercom","door","lock","entry","access"]),
    ("Security/Alarm",["alarm","security"]),
]
keyword_hits=defaultdict(list)
for a in groups.values():
    nm=a.get("Name","").strip(); low=nm.lower()
    for dom,keys in keyword_groups:
        if any(k in low for k in keys):
            keyword_hits[dom].append(f"{a.get('Address','')} — {nm}")

md=[]
md += [
    "# Burooj Square — Installer Device & Wiring Guide",
    "",
    f"Source project: {src.name}",
    "",
    "## كيف تستخدم هذا الملف",
    "هذا الدليل يفرق بين المعلومة الموجودة فعلياً داخل مشروع ETS وبين الاستنتاج المنطقي من اسم الـGroup Address ونوع الجهاز. "
    "أي شيء مكتوب عليه Inferred أو Sequential GA mapping ليس بديلاً عن المخطط الكهربائي أو ترقيم الأسلاك في الموقع.",
    "",
    "## ما يثبته مشروع ETS حالياً",
    "- المشروع يحتوي على قالب فيلا واحد.",
    "- الأجهزة المادية/الوظيفية الموجودة تشمل ريليات، تحكم ستائر، DALI، لوحات لمس، لوحات مفاتيح، حساسات حضور، واجهات IR للمكيفات، وواجهة KNX-IP.",
    "- مشروع ETS لا يسجل لي بشكل موثوق رقم الكابل الميداني أو اسم الحمل الكهربائي النهائي لكل طرف ريليه.",
    "",
    "## أهم الأجهزة وطريقة التوصيل الفيزيائي المتوقعة",
    "",
    "| Device | عنوان KNX | الجهاز | يتصل عادةً بـ | ما يثبته المشروع |",
    "|---|---:|---|---|---|",
    "| DI-10 | — | KUPSupply 640 | تغذية KNX/لوحة التوزيع | موجود في المشروع |",
    "| DI-11 | 1 | KIPI SC | KNX TP + Ethernet | موجود؛ لا GAs مباشرة في الـInstance |",
    "| DI-12/13 | 2/3 | DALI BOX Interface 64 v3 | KNX TP + DALI bus | موجودان؛ ballast mapping غير مثبت في الـInstance |",
    "| DI-14 | 4 | MAXinBOX 8 v4 | KNX TP + 8 relay outputs | Garage + On/Off 3..8 |",
    "| DI-15 | 5 | MAXinBOX 8 v4 | KNX TP + 8 relay outputs | On/Off 9..16 |",
    "| DI-16 | 6 | MAXinBOX 16 v4 | KNX TP + 16 relay outputs | On/Off 17..32 |",
    "| DI-17 | 7 | MAXinBOX 16 v4 | KNX TP + 16 relay outputs | On/Off 33..48 |",
    "| DI-18 | 8 | MAXinBOX 24 v2 | KNX TP + 24 relay outputs | On/Off 49..72 |",
    "| DI-19/20/21 | 9/10/11 | MAXinBOX SHUTTER 8CH v3 | KNX TP + shutter motor outputs | shutter groups 1..18 |",
    "| DI-22..30 | 12..20 | Logic controller | KNX TP; logic only | HVAC blocks are visible in GAs |",
    "| DI-43..46 | 23..26 | IRSC | KNX + IR emitter to indoor A/C | four devices present; no linked GAs in instances |",
    "| DI-57..62 | 27..32 | Tecla 55 X4 | KNX TP | devices present |",
    "| DI-63/64/72/73 | 33/34/35/36 | Tecla 55 X6 | KNX TP | devices present |",
    "| DI-65/66 | 37/38 | TMD Plus 4 | KNX TP | control panel, no load output |",
    "| DI-70/74 | 39/40 | TMD Plus 6 | KNX TP | names include Majlis & Dining |",
    "| DI-71 | 41 | TMD Plus 8 | KNX TP | name includes G.F Living Areas |",
    "| DI-85..92/98 | 43..50 | Z35 v2 | KNX TP; touch panel/thermostat/sensors per configuration | several room names are explicit |",
    "| DI-99 | 51 | Z100 | KNX + 24VDC power + Ethernet | large set of links for lighting/blinds/HVAC/Garage |",
    "| DI-100..103 | 52..55 | EyeZen TP v2 | KNX TP at ceiling | four devices present; no linked GAs in instances |",
    "",
    "## توزيع مخارج الريليه — استنتاج منطقي من المشروع",
    "",
    "DI-14 / address 4 / MAXinBOX 8 v4:",
    "1. Relay 1 → Move Garage",
    "2. Relay 2 → Stop Garage",
    "3. Relay 3 → On/Off 3",
    "4. Relay 4 → On/Off 4",
    "5. Relay 5 → On/Off 5",
    "6. Relay 6 → On/Off 6",
    "7. Relay 7 → On/Off 7",
    "8. Relay 8 → On/Off 8",
    "",
    "DI-15 / address 5: Relay 1..8 → On/Off 9..16.",
    "DI-16 / address 6: Relay 1..16 → On/Off 17..32.",
    "DI-17 / address 7: Relay 1..16 → On/Off 33..48.",
    "DI-18 / address 8: Relay 1..24 → On/Off 49..72.",
    "",
    "**تحذير تنفيذ:** هذه المطابقة من تسلسل Group Addresses وعدد المخارج. لا تعتمد عليها لترقيم الأسلاك على الأطراف قبل مقارنتها مع electrical schedule / panel termination schedule.",
    "",
    "## الستائر",
    "DI-19: channels 1..8 → blinds 1..8",
    "DI-20: channels 1..8 → blinds 9..16",
    "DI-21: channels 1..2 → blinds 17..18",
    "القنوات 3..8 في DI-21 لا تظهر لها Group Address links في الـInstance الحالي.",
    "",
    "## المكيفات",
    "مشروع ETS يحتوي طبقة HVAC واضحة من مجموعات Mode / Fan / ON/Off / Set Point / Temp. / Error Code. "
    "كما يحتوي أربع وحدات IRSC عند العناوين 23–26. نوع IRSC مخصص للتحكم بوحدات A/C عبر الأشعة تحت الحمراء، لكن المشروع الحالي لا يحدد أي IRSC مرتبط بأي غرفة أو وحدة داخلية. "
    "لذلك لا أنسب مكيفاً معيناً إلى IRSC معين بدون HVAC schedule أو room schedule.",
    "",
    "## الكراج",
    "يوجد Move Garage وStop Garage وحقول Info/Status. الـMove مرتبط بالـMAXinBOX عند العنوان 4، وبعض Info/Status مرتبطة أيضاً بـZ100. "
    "هذا يثبت منطق الكراج في KNX، لكنه لا يحدد terminal/cable ميدانياً.",
    "",
    "## الإنتركم / الأبواب",
    "لم تظهر تسمية صريحة لـIntercom أو Door أو Lock أو Entry أو Access ضمن Group Address names الحالية. "
    "لذلك لا يمكن تحديد جهاز إنتركم أو قفل باب من ملف ETS وحده. جهاز Z100 لديه قدرة تكامل Video Intercom حسب صفحة Zennio، لكن هذا لا يثبت أن التكامل مفعّل في هذا المشروع.",
    "",
    "## الحساسات",
    "يوجد 4 أجهزة EyeZen TP v2 على العناوين 52–55. هي حساسات حركة/إضاءة سقفية حسب مواصفات Zennio، لكن الـDeviceInstance الحالي لا يربطها مباشرةً بزوج Group Address واضح لكل دائرة إنارة.",
    "",
    "## الملفات الجاهزة",
    "- INSTALLER_WIRING_SCHEDULE.csv — جدول device/channel/GA/domain مع مستوى الدليل.",
    "- INSTALLER_DEVICE_OVERVIEW.csv — جميع الأجهزة وعناوينها وعدد روابط GA.",
    "- knx-device-map/GROUP_ADDRESS_SCHEDULE.csv — جميع الـ618 GA مع الأجهزة المرتبطة.",
    "",
    "## تدقيق الكلمات المهمة",
    ""
]
for dom,_ in keyword_groups:
    hits=keyword_hits.get(dom,[])
    md.append(f"### {dom}")
    if hits:
        md.extend([f"- {h}" for h in hits[:100]])
    else:
        md.append("- لا توجد تسمية صريحة مطابقة في أسماء Group Addresses الحالية.")
    md.append("")

(ROOT/"INSTALLER_DEVICE_WIRING_GUIDE.md").write_text("\n".join(md),encoding="utf-8")
print("Created installer guide", len(wiring), "wiring rows", len(overview), "devices")

#!/usr/bin/env python3
"""Upstream's 256 factory presets as this port's presets (tools/gen_presets.cpp does the conversion with the DSP's own code).

    tools/presets.py json            -> vst/presets.json (the wrapper's PRESET menu) and vst/presets/factory.json (every
                                        parameter, for the .xpl files); needs g++ on the host
    tools/presets.py xpl <skin dir>  -> <skin dir>/Presets/NNNN-<name>.xpl (MPC's own preset files, one per preset)

A preset sets the patch (what upstream's presets set), not the live controls (arpeggiator, hold, portamento, tuning,
volume, bender depths) or the voice settings; the .xpl files carry the defaults for those, since they hold a whole state."""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
VST = os.path.join(ROOT, "vst")


def params():
    return json.load(open(os.path.join(VST, "params.json")))["params"]


def converted():
    exe = os.path.join(tempfile.mkdtemp(), "gen_presets")
    src = os.path.join(ROOT, "src")
    subprocess.run(["g++", "-std=gnu++17", "-O1", "-I" + src, "-I" + os.path.join(src, "dsp"),
                    os.path.join(HERE, "gen_presets.cpp"), "-o", exe], check=True)
    return json.loads(subprocess.run([exe], check=True, capture_output=True, text=True).stdout)


def short(name):
    return name if len(name) <= 23 else name[:22] + "."   # the wrapper's preset names are 23 characters


def write_json():
    ps = {p["key"]: p for p in params()}
    rows, full = [], []
    for pr in converted():
        vals = {}
        for k, x in pr["values"].items():
            if k not in ps:
                sys.exit("preset %r: unknown key %r" % (pr["name"], k))
            vals[k] = ps[k]["options"][int(x)] if "options" in ps[k] else round(x, 6)
        rows.append({"name": short(pr["name"]), "values": vals})
        v = {p["key"]: (p["options"].index(p["default"]) if "options" in p else p["default"]) for p in ps.values()}
        v.update({k: x for k, x in pr["values"].items()})
        full.append([pr["name"], v])
    json.dump({"presets": rows}, open(os.path.join(VST, "presets.json"), "w"), indent=1)
    os.makedirs(os.path.join(VST, "presets"), exist_ok=True)
    json.dump(full, open(os.path.join(VST, "presets", "factory.json"), "w"), indent=1)
    print(len(rows), "presets")


def write_xpl(skin):
    sys.path.insert(0, os.environ.get("MPC_VST_TOOLS", os.path.join(ROOT, "..", "mpc-vst-plugins", "tools")))
    import xpl
    cfg = json.load(open(os.path.join(VST, "vst.json")))
    so_path = "%%payload-path%%/%s - VST - %s/%s" % (cfg["vendor"], cfg["name"], cfg["so"])
    uid = int.from_bytes(cfg["uid"].encode(), "big")
    os.makedirs(os.path.join(skin, "Presets"), exist_ok=True)
    for i, (name, v) in enumerate(json.load(open(os.path.join(VST, "presets", "factory.json"))), 1):
        state = ";".join("%s=%s" % (k, x) for k, x in v.items() if k != "chorus_off").encode() + b"\0"
        fn = os.path.join(skin, "Presets", "%04d-%s.xpl" % (i, name.replace("/", "-")))
        with open(fn, "w", encoding="utf-8") as f:
            f.write(xpl.xpl(cfg["name"], cfg["vendor"], so_path, uid, cfg.get("version", 1000), state, preset=name))


if __name__ == "__main__":
    if sys.argv[1:2] == ["json"]:
        write_json()
    elif sys.argv[1:2] == ["xpl"] and len(sys.argv) == 3:
        write_xpl(sys.argv[2])
    else:
        sys.exit(__doc__)

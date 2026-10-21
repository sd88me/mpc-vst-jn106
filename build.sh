#!/usr/bin/env bash
# Build the plugin: parameters, presets and skin art, then tools/build_port.sh from a checkout of mpc-vst-plugins
# (MPC_VST, default ~/mpc-vst-plugins): the skin folder and kr106.so for armv7 and aarch64 in vst/build/.
#   ./build.sh [armv7|aarch64|all]          the skin drawn from upstream's panel art (skin/make_skin.py)
#   SKIN=real ./build.sh [armv7|aarch64]    the realistic panel drawn from scratch (skin/make_real_skin.py)
set -euo pipefail
cd "$(dirname "$0")"
MPC_VST="${MPC_VST:-$HOME/mpc-vst-plugins}"
python3 tools/gen_params.py
python3 tools/presets.py json
if [ "${SKIN:-}" = real ]; then
  python3 skin/make_real_skin.py
  # build_port.sh reads <port>/vst.json: point its layout at the realistic one for this build, then put it back
  cp vst/vst.json vst/vst.json.keep
  trap 'mv vst/vst.json.keep vst/vst.json' EXIT
  python3 - <<'PY'
import json
d = json.load(open("vst/vst.json"))
d["layout"] = "layout.real.conf"
json.dump(d, open("vst/vst.json", "w"), indent=2)
PY
else
  python3 -c "import sys; sys.path.insert(0, 'skin'); import make_skin; make_skin.build('vst')"
fi
"$MPC_VST/tools/build_port.sh" vst/vst.json "${1:-all}"

#!/usr/bin/env bash
# Build the plugin: skin art (skin/make_skin.py) and presets (tools/presets.py json), then tools/build_port.sh from a checkout
# of mpc-vst-plugins (MPC_VST, default ../mpc-vst-plugins): skin folder, kr106.so for armv7 and aarch64 in vst/build/.
set -euo pipefail
cd "$(dirname "$0")"
MPC_VST="${MPC_VST:-$HOME/mpc-vst-plugins}"
python3 tools/gen_params.py
python3 tools/presets.py json
python3 -c "import sys; sys.path.insert(0, 'skin'); import make_skin; make_skin.build('vst')"
"$MPC_VST/tools/build_port.sh" vst/vst.json "${1:-all}"

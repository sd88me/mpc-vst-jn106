# KR-106 for MPC

A six-voice (optionally 8 or 10) polyphonic Juno-style synth plugin for Akai MPC OS standalone devices (MPC Live/One/X/Key,
Force): the DSP of [Ultramaster KR-106](https://github.com/kayrockscreenprinting/ultramaster_kr106) by Karl LaRocca, with its
panel artwork cut into five MPC screens and its 256 factory presets (128 Juno-60 and 128 Juno-106 patches) as native presets.

**Status: offline only.** Host test (ASan) passes, the skin has been previewed offline, and both zips pass `catalog_check.py`.
It has not been loaded on a device and has not been benched (`tools/bench.sh`).

## Screens
LFO / DCO / HPF, VCF / VCA / ENV / chorus, ARP (with TRANS and HOLD), PERFORM (volume, portamento, bender depths, tuning) and
SETTINGS (voices, VCF oversampling, wavetable or PolyBLEP oscillators, ignore velocity, arp limit, mono retrigger). The keybed
and scope are left out. Each screen has its own Q-Link page.

## Presets
All 256 factory presets are in MPC's PRESET menu (`vst/presets.json`) and as `.xpl` files for the instruments browser. A preset
sets the patch and the model (JUNO-60 or 106 mode: bank 1 is the 60 mode); live controls (arpeggiator, hold, portamento, tuning,
volume, bender depths) and voice settings stay as they are. Names are upstream's; one is cut to 23 characters by the wrapper.

## MIDI
Notes, pitch bend, mod wheel (the LFO trigger), sustain pedal (HOLD), CC 120/123, and upstream's CC map (3, 5, 7, 9, 11-13, 70-82).
CC 20-35 and NRPN are the wrapper's (first page's Q-Links, any parameter). Master volume defaults to 0.3 (upstream's 0.5 clips).

## Build
`./build.sh` (Docker; needs a checkout of https://github.com/sd88me/mpc-vst-plugins at `$MPC_VST`, default `~/mpc-vst-plugins`):
parameters, presets, skin art, `kr106.so` for armv7 and aarch64. `tools/test_port.sh vst/vst.json` for the host test.
Release: `docs/RELEASING.md` in mpc-vst-plugins, with `--repo sd88me/mpc-vst-kr106 --license GPL-3.0-only --id kr-106`.

## Layout of this repo
`src/` vendored upstream (`src/VENDORED.md`), `vst/engine.cpp` the engine, `tools/gen_params.py` the parameter list,
`tools/presets.py` + `gen_presets.cpp` the presets, `skin/make_skin.py` the skin (draws the controls as upstream's editor does).

## Licence
GPL-3.0-only, as upstream. The skin contains no maker's name or logo.

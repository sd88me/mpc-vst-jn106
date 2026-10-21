# JN-106 for MPC

A six-voice polyphonic Juno-style synth plugin for Akai MPC OS standalone devices (MPC Live/One/X/Key, Force): the DSP of
[Ultramaster KR-106](https://github.com/kayrockscreenprinting/ultramaster_kr106) by Karl LaRocca, on a realistic panel skin
drawn for the MPC screen, with its 256 factory presets (128 Juno-60 and 128 Juno-106 patches) as native presets.

![LFO / DCO / HPF screen](docs/img/screenshot-lfo-dco.png)

**Status:** loads, plays and loads presets on a Force (MPC OS 3.9.1, armv7). The aarch64 build (Gen2 MPCs) has not
been run on a device. CPU on the Force (`tools/bench.sh`, six held notes): 2x oversampling about 31% of a block (WARN),
1x about 20%; a fast Q-Link sweep peaks near 47% at p99 (FAIL class). Use 1x on a busy project.

## Screens
LFO / DCO / HPF, FILTER / AMP / ENV (with chorus), ARP (with TRANS and HOLD), PERFORM (volume, portamento, bender depths,
tuning) and SETTINGS (VCF oversampling 1x/2x, wavetable or PolyBLEP oscillators, ignore velocity, arp limit, mono
retrigger). The keybed and scope are left out. Each screen except SETTINGS has its own Q-Link page.

## Presets
All 256 factory presets are in the instruments browser (Sounds > Instruments > JN-106) and in MPC's PRESET list
(`vst/presets.json`). A preset sets the patch and the model (JUNO-60 or 106 mode: bank A is the 60 mode); live controls
(arpeggiator, hold, portamento, tuning, volume, bender depths) stay as they are. Names are upstream's; one is cut to 23
characters by the wrapper. The PRESET dropdown in the plugin header does not open on the Force; use the browser.

## Changes to the upstream DSP
Listed in `src/VENDORED.md`. From the Roland service notes and schematics:
- 106 mode: the DCO pitch moves in 4.2 ms steps (the CPU's control loop) and each note is rounded to an 8253 counter
  value, so the top notes can sit a few cents off, as on the hardware.
- 60 mode: attack, decay and release use the 60's linear slider wiring instead of copying the Juno-6 taper (the Juno-6
  has a 39K pull-up across each slider). Both ends of each slider are unchanged; the middle is faster.

## MIDI
Notes, pitch bend, mod wheel (the LFO trigger), sustain pedal (HOLD), CC 120/123, and upstream's CC map (3, 5, 7, 9, 11-13, 70-82).
CC 20-35 and NRPN are the wrapper's (first page's Q-Links, any parameter). Master volume defaults to 0.3 (upstream's 0.5 clips).

## Install
Download the zip for your MPC from the releases page (armv7 for Gen1, aarch64 for Gen2) and follow its `INSTALL.md`, or
install it from the mpc-vst-plugins catalog. The installer restarts MPC.

## Build
`SKIN=real ./build.sh` (Docker; needs a checkout of https://github.com/sd88me/mpc-vst-plugins at `$MPC_VST`, default
`~/mpc-vst-plugins`): parameters, presets, skin art, `kr106.so` for armv7 and aarch64. `tools/test_port.sh vst/vst.json`
for the host test. Release: `docs/RELEASING.md` in mpc-vst-plugins, with
`--repo sd88me/mpc-vst-jn106 --license GPL-3.0-only --id j106`.

## Layout of this repo
`src/` vendored upstream (`src/VENDORED.md`), `vst/engine.cpp` the engine, `tools/gen_params.py` the parameter list,
`tools/presets.py` + `gen_presets.cpp` the presets, `skin/make_real_skin.py` the realistic skin (`skin/make_skin.py`, the
older skin cut from upstream's panel art, is kept but not shipped).

## Licence
GPL-3.0-only, as upstream. The skin contains no maker's name or logo. Michroma font: SIL OFL (`skin/assets/OFL-Michroma.txt`).

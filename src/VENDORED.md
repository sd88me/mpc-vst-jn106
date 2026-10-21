# Vendored from Ultramaster KR-106

- Upstream: https://github.com/kayrockscreenprinting/ultramaster_kr106 (GPL-3.0, Karl LaRocca; see `../UPSTREAM-AUTHORS`)
- Commit: `bc15caee5843ab238a25d0969e68d57db2b1615f` (2026-05-07, "Bump version to 2.5.13")
- `src/dsp/*.h`: upstream `Source/DSP/*.h`, unchanged (the DSP has no JUCE dependency). `KR106SysEx.h` and `KR106ParamValue.h` are
  carried but not used by this port.
- `src/KR106_Presets_JUCE.h`: upstream `Source/KR106_Presets_JUCE.h`, unchanged (the 256 factory presets); read by `tools/gen_presets.cpp`.
- `skin/assets/*.png`: upstream `resources/img/` (`kr106_background@2x`, `smallknob@2x`, `switch_3way@2x`,
  `switch_3way_horizontal@2x`, `led_red@2x`, `slider_handle@2x`), unchanged.

Not taken: the JUCE processor/editor, preset manager, MIDI learn, SysEx, scope, keybed and host sync. `vst/engine.cpp` redoes
what the processor does around the DSP (parameter push, MIDI decode, master volume, denormal flush).

## Local changes to the vendored DSP

- `dsp/KR106_DSP.h`: idle voices are skipped (`KR106_SKIP_IDLE_VOICES`, CPU on Gen1 MPCs).
- `dsp/KR106Voice.h`: in J106 mode the DCO pitch is held between firmware ticks (4.2 ms) and rounded to an 8253
  counter value at 8 MHz / 2, 4 or 8 (RANGE 4', 8', 16'), per the Juno-106 Service Notes ("OSC, DCO" and the D/A
  timing chart): the slave CPU writes divide data once per main loop. `mDcoStepped` switches it off.

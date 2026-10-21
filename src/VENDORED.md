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

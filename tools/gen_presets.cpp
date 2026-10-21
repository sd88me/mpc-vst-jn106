// Upstream's 256 factory presets (src/KR106_Presets_JUCE.h: 128 Juno-60 tape-dump patches, then 128 Juno-106 patches) as this
// port's presets, with the same conversion PluginProcessor.cpp's constructor does (raw 7-bit values to 0-1 sliders, the
// 106 bank's DCO LFO depth back through the DSP's own inverse taper). Prints JSON on stdout:
//   [{"name": ..., "values": {key: number}}, ...]   values in params.json's units (an option as its index)
// Built and run by tools/presets.py (host g++, -Isrc/dsp not needed: only KR106Voice.h's static function is used).
#include <stdio.h>
#include "dsp/KR106Voice.h"
#include "KR106_Presets_JUCE.h"

// upstream parameter number -> this port's key (nullptr: a live-performance control or one the panel doesn't have, which
// presets never set: upstream's sExcludeMask / the processor's own "live" list)
static const char *KEYS[44] = {
    "bender_dco", "bender_vcf", "arp_rate", "lfo_rate", "lfo_delay",
    "dco_lfo", "dco_pwm", "dco_sub", "dco_noise", "hpf",
    "vcf_freq", "vcf_res", "vcf_env", "vcf_lfo", "vcf_kbd",
    "vca_level", "env_a", "env_d", "env_s", "env_r",
    nullptr, nullptr, nullptr, "pulse", "saw", "sub_sw",
    nullptr, "chorus_i", "chorus_ii",
    "octave", nullptr, nullptr, "lfo_mode", "pwm_mode",
    "vcf_env_inv", "vca_mode",
    nullptr, nullptr, nullptr, nullptr, nullptr, nullptr, nullptr, nullptr,
};

int main() {
    printf("[\n");
    for (int j = 0; j < kNumFactoryPresets; j++) {
        const KR106FactoryPreset &p = kFactoryPresets[j];
        printf("%s {\"name\": \"%s\", \"values\": {", j ? ",\n" : "", p.name);
        printf("\"adsr_mode\": %d", j >= 128 ? 1 : 0);   // the bank is the model: 0 = Juno-60 tape dump, 1 = Juno-106
        for (int i = 0; i < 44; i++) {
            if (!KEYS[i]) continue;
            // upstream's live-performance parameters (kArpRate, bender sensitivities) are excluded from preset loads
            if (i == 0 || i == 1 || i == 2) continue;
            int raw = p.values[i];
            double v;
            if (i == 9 || i == 29 || i == 32 || i == 33 || i == 34 || i == 35 || (i >= 23 && i <= 28)) v = raw;   // switches, buttons, the 4-step HPF
            else {
                v = raw / 127.0;
                if (i == 5 && j >= 128) v = kr106::Voice<float>::dcoLfoDepth106_inverseTaper((float)v);
            }
            printf(", \"%s\": %.9g", KEYS[i], v);
        }
        printf("}}");
    }
    printf("\n]\n");
    return 0;
}

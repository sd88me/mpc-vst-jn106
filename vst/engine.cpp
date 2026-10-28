/* The KR-106 DSP (src/dsp/, Ultramaster KR-106 by Karl LaRocca, GPL-3.0) as mpc-vst-plugins' mpc_engine()
 * (wrapper/engine.h). The synth's own JUCE processor does three things around the DSP that this file redoes:
 * it pushes every parameter in with KR106DSP::SetParam(), decodes MIDI into NoteOn/NoteOff/ControlChange, and
 * applies the master volume (a squared taper) before ProcessBlock(). Parameter keys and order are params.json's.
 * The JUCE-only parts (editor, preset manager, MIDI learn, SysEx, scope, host sync) are not here. */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <string>

extern "C" {
#include "engine.h"
}
#ifndef KR106_OS_DEFAULT
#define KR106_OS_DEFAULT 1   /* option index; bench builds override */
#endif
#include "dsp/KR106_DSP.h"

namespace {

/* The DSP's own parameter numbers (KR106_DSP_SetParam.h's enum, PluginProcessor.h's EParams). */
enum {
    kBenderDco = 0, kBenderVcf, kArpRate, kLfoRate, kLfoDelay,
    kDcoLfo, kDcoPwm, kDcoSub, kDcoNoise, kHpfFreq,
    kVcfFreq, kVcfRes, kVcfEnv, kVcfLfo, kVcfKbd,
    kVcaLevel, kEnvA, kEnvD, kEnvS, kEnvR,
    kTranspose, kHold, kArpeggio, kDcoPulse, kDcoSaw, kDcoSubSw,
    kChorusOff, kChorusI, kChorusII,
    kOctTranspose, kArpMode, kArpRange, kLfoMode, kPwmMode,
    kVcfEnvInv, kVcaMode,
    kBender, kTuning, kPower,
    kPortaMode, kPortaRate,
    kTransposeOffset, kBenderLfo,
    kAdsrMode,
    kMasterVol,
    kNumDsp,
    /* settings the processor keeps outside the DSP's SetParam */
    kSetVoices = 100, kSetOversample, kSetIgnoreVel, kSetArpLimitKbd, kSetMonoRetrig, kSetOscMode,
    kSetChorusOff, kSetArpSync, kSetArpDiv,
};

struct P { const char *key; int id; float def; };

/* params.json's order. `def` is the value the engine starts with (the same as params.json's default). */
const P PARAMS[] = {
    {"tuning", kTuning, 0},          {"master_vol", kMasterVol, 0.3f}, {"porta_rate", kPortaRate, 0},
    {"bender_dco", kBenderDco, 0},   {"bender_vcf", kBenderVcf, 0},    {"bender_lfo", kBenderLfo, 0},
    {"porta_mode", kPortaMode, 1},
    {"transpose", kTranspose, 0},    {"hold", kHold, 0},               {"arpeggio", kArpeggio, 0},
    {"arp_mode", kArpMode, 0},       {"arp_range", kArpRange, 0},      {"arp_rate", kArpRate, 30.f / 128},
    {"lfo_rate", kLfoRate, 0.24f},   {"lfo_delay", kLfoDelay, 0},      {"lfo_mode", kLfoMode, 0},
    {"dco_lfo", kDcoLfo, 0},         {"dco_pwm", kDcoPwm, 0.5f},       {"pwm_mode", kPwmMode, 1},
    {"pulse", kDcoPulse, 1},         {"saw", kDcoSaw, 1},              {"sub_sw", kDcoSubSw, 1},
    {"octave", kOctTranspose, 1},    {"dco_sub", kDcoSub, 1},          {"dco_noise", kDcoNoise, 0},
    {"hpf", kHpfFreq, 1},
    {"vcf_freq", kVcfFreq, 1},       {"vcf_res", kVcfRes, 0},          {"vcf_env_inv", kVcfEnvInv, 0},
    {"vcf_env", kVcfEnv, 0},         {"vcf_lfo", kVcfLfo, 0},          {"vcf_kbd", kVcfKbd, 0},
    {"vca_mode", kVcaMode, 1},       {"vca_level", kVcaLevel, 0.5f},
    {"env_a", kEnvA, 0.25f},         {"env_d", kEnvD, 0.25f},          {"env_s", kEnvS, 0.9f},
    {"env_r", kEnvR, 0.25f},         {"adsr_mode", kAdsrMode, 1},
    {"chorus_off", kSetChorusOff, 0}, {"chorus_i", kChorusI, 1},       {"chorus_ii", kChorusII, 0},
    {"oversample", kSetOversample, KR106_OS_DEFAULT}, {"osc_mode", kSetOscMode, 1},
    {"ignore_vel", kSetIgnoreVel, 1}, {"arp_limit_kbd", kSetArpLimitKbd, 1}, {"mono_retrig", kSetMonoRetrig, 1},
    {"arp_sync", kSetArpSync, 0},    {"arp_div", kSetArpDiv, 6},
};
const int NP = (int)(sizeof PARAMS / sizeof PARAMS[0]);

/* MIDI CC -> parameter key, as the synth's own table (PluginProcessor.cpp kCCtoParam) for the parameters exposed here. */
const struct { int cc; const char *key; } CC_MAP[] = {
    {3, "dco_lfo"}, {5, "porta_rate"}, {7, "master_vol"}, {9, "dco_sub"}, {11, "vca_level"}, {12, "hpf"}, {13, "dco_noise"},
    {70, "env_s"}, {71, "vcf_res"}, {72, "env_r"}, {73, "env_a"}, {74, "vcf_freq"}, {75, "env_d"}, {76, "vcf_env"},
    {77, "vcf_lfo"}, {78, "vcf_kbd"}, {79, "dco_pwm"}, {80, "lfo_rate"}, {81, "lfo_delay"}, {82, "arp_rate"},
};

struct Inst {
    KR106DSP<float> dsp;
    float val[64];                 /* current value of every PARAMS[] entry, in its own units */
    float master_vol;              /* squared taper, as the processor sets mDSP.mMasterVol each block */
    int os_opt;                    /* option index of "oversample" (1x/2x; 4x costs 53% of a block with 6 voices on a Force) */
    bool transpose_mode;
    bool arp_sync, host_ok;        /* ARP SYNC on; the host gave a tempo this block */
    int changed[16], nchanged;     /* keys the engine moved itself (CC, chorus off): mpc_engine_changed() */
    float *ch[2];
    float lbuf[128], rbuf[128];

    Inst() : dsp(6), master_vol(0.09f), os_opt(0), transpose_mode(false), arp_sync(false), host_ok(false), nchanged(0) {
        ch[0] = lbuf; ch[1] = rbuf;
        dsp.Reset(44100.0, 128);
        dsp.SetDriftAmount(0.25f);   /* the synth's default ("recently calibrated") */
        for (int i = 0; i < NP; i++) apply(i, PARAMS[i].def);
        dsp.mMasterVolSmooth = dsp.mMasterVol;   /* no ramp from the constructor's value at the first block */
        dsp.mVcaLevelSmooth = dsp.mVcaLevel;
    }

    int find(const char *key) const {
        for (int i = 0; i < NP; i++) if (!strcmp(PARAMS[i].key, key)) return i;
        return -1;
    }

    void note_changed(int i) {
        for (int k = 0; k < nchanged; k++) if (changed[k] == i) return;
        if (nchanged < 16) changed[nchanged++] = i;
    }

    /* Put value v into parameter i and into the DSP. */
    void apply(int i, float v) {
        val[i] = v;
        int id = PARAMS[i].id;
        switch (id) {
        case kMasterVol:
            master_vol = v * v;
            dsp.mMasterVol = master_vol;
            break;
        case kSetOversample: {
            int o = (int)lroundf(v);
            os_opt = o < 0 ? 0 : o > 1 ? 1 : o;
            dsp.SetOversample(1 << os_opt);
            break;
        }
        case kSetIgnoreVel: dsp.mIgnoreVelocity = v > 0.5f; break;
        case kSetArpLimitKbd: dsp.mArp.mLimitToKeyboard = v > 0.5f; break;
        case kSetArpSync: arp_sync = v > 0.5f; dsp.mArp.mSyncToHost = arp_sync && host_ok; break;
        case kSetArpDiv: { int d = (int)lroundf(v); dsp.mArp.mDivision = d < 0 ? 0 : d > 8 ? 8 : d; break; }
        case kSetMonoRetrig: dsp.mMonoRetrigger = v > 0.5f; break;
        case kSetOscMode: {
            int m = (int)lroundf(v);
            dsp.ForEachVoice([m](kr106::Voice<float> &vo) { vo.mOscMode = m; });
            break;
        }
        case kSetChorusOff:
            if (v > 0.5f) {   /* the OFF key: both chorus keys up */
                for (const char *k : {"chorus_i", "chorus_ii"}) {
                    int j = find(k);
                    if (val[j] > 0.5f) { apply(j, 0); note_changed(j); }
                }
            }
            break;
        case kTranspose:
            transpose_mode = v > 0.5f;
            dsp.SetParam(id, v);
            break;
        case kChorusI: case kChorusII:
            dsp.SetParam(id, v);
            break;
        default:
            dsp.SetParam(id, v);
            break;
        }
    }

    void set(int i, float v) {
        if (PARAMS[i].id == kSetChorusOff) { apply(i, v); val[i] = 0; return; }   /* a trigger: nothing to hold */
        apply(i, v);
    }

    void cc_set(const char *key, int cc_val) {
        int i = find(key);
        if (i < 0) return;
        float v;
        if (!strcmp(key, "hpf")) { v = (float)(cc_val / 32 > 3 ? 3 : cc_val / 32); }
        else if (!strcmp(key, "dco_pwm")) { v = cc_val > 105 ? 1.f : cc_val / 105.f; }   /* the 106's PWM slider stops at byte 105 */
        else v = cc_val / 127.f;
        if (v == val[i]) return;
        apply(i, v);
        note_changed(i);
    }
};

/* Flush denormals to zero for the block, as the synth's own processBlock does with juce::ScopedNoDenormals. */
struct NoDenormals {
#if defined(__SSE__)
    unsigned old;
    NoDenormals() { old = __builtin_ia32_stmxcsr(); __builtin_ia32_ldmxcsr(old | 0x8040); }
    ~NoDenormals() { __builtin_ia32_ldmxcsr(old); }
#elif defined(__aarch64__)
    unsigned long old;
    NoDenormals() { asm volatile("mrs %0, fpcr" : "=r"(old)); asm volatile("msr fpcr, %0" :: "r"(old | (1ul << 24))); }
    ~NoDenormals() { asm volatile("msr fpcr, %0" :: "r"(old)); }
#elif defined(__arm__)
    unsigned old;
    NoDenormals() { asm volatile("vmrs %0, fpscr" : "=r"(old)); unsigned n = old | (1u << 24); asm volatile("vmsr fpscr, %0" :: "r"(n)); }
    ~NoDenormals() { asm volatile("vmsr fpscr, %0" :: "r"(old)); }
#else
    NoDenormals() {}
#endif
};

void *create(const char *) { return new Inst(); }
void destroy(void *p) { delete (Inst *)p; }

void midi(void *p, const uint8_t *m, int len) {
    Inst *e = (Inst *)p;
    if (len < 2) return;
    int st = m[0] & 0xF0, d1 = m[1], d2 = len > 2 ? m[2] : 0;
    if (st == 0x90 && d2 > 0) {
        if (e->transpose_mode) e->dsp.SetKeyTranspose(d1 - 60);   /* TRANS held: the key names the transposition */
        else e->dsp.NoteOn(d1, d2);
    } else if (st == 0x80 || st == 0x90) {
        e->dsp.NoteOff(d1);
    } else if (st == 0xE0) {
        e->dsp.SetParam(kBender, ((d1 | (d2 << 7)) - 8192) / 8192.0);
    } else if (st == 0xB0) {
        if (d1 == 120 || d1 == 123) {
            e->dsp.AllNotesOff();
        } else if (d1 == 64) {   /* sustain pedal = HOLD */
            int i = e->find("hold");
            float v = d2 >= 64 ? 1.f : 0.f;
            if (v != e->val[i]) { e->apply(i, v); e->note_changed(i); }
        } else if (d1 == 1) {    /* mod wheel = the bender lever's LFO trigger */
            e->dsp.ControlChange(1, d2 / 127.f);
        } else {
            for (const auto &c : CC_MAP) if (c.cc == d1) { e->cc_set(c.key, d2); break; }
        }
    }
}

void set_param(void *p, const char *key, const char *v) {
    Inst *e = (Inst *)p;
    if (!strcmp(key, "state")) {   /* "key=value;key=value;..." */
        const char *s = v;
        while (*s) {
            const char *eq = strchr(s, '=');
            const char *end = strchr(s, ';');
            if (!eq || (end && eq > end)) break;
            std::string k(s, eq - s);
            int i = e->find(k.c_str());
            if (i >= 0) e->set(i, (float)atof(eq + 1));
            if (!end) break;
            s = end + 1;
        }
        return;
    }
    int i = e->find(key);
    if (i >= 0) e->set(i, (float)atof(v));
}

int get_param(void *p, const char *key, char *buf, int len) {
    Inst *e = (Inst *)p;
    if (!strcmp(key, "state")) {
        std::string s;
        char t[64];
        for (int i = 0; i < NP; i++) {
            if (PARAMS[i].id == kSetChorusOff) continue;
            snprintf(t, sizeof t, "%s=%g;", PARAMS[i].key, e->val[i]);
            s += t;
        }
        snprintf(buf, len, "%s", s.c_str());
        return (int)strlen(buf);
    }
    int i = e->find(key);
    if (i < 0) return -1;
    return snprintf(buf, len, "%g", e->val[i]);
}

void render(void *p, int16_t *out, int frames) {
    Inst *e = (Inst *)p;
    NoDenormals nd;
    e->dsp.mMasterVol = e->master_vol;
    e->dsp.ProcessBlock(nullptr, e->ch, 2, frames);
    for (int i = 0; i < frames; i++) {
        for (int c = 0; c < 2; c++) {
            float x = e->ch[c][i] * 32767.f;
            out[2 * i + c] = (int16_t)(x > 32767.f ? 32767 : x < -32768.f ? -32768 : x);
        }
    }
}

/* Once per host block, before render(): the arpeggiator follows the host's tempo and beat grid while ARP SYNC is on (and free-runs
 * at the tempo when the transport is stopped), else the RATE slider. No tempo from the host (bpm 0) means the slider. */
void song_pos(void *p, double ppq, double bpm, int playing, int) {
    Inst *e = (Inst *)p;
    e->host_ok = bpm > 0 && ppq >= 0;
    kr106::Arpeggiator &a = e->dsp.mArp;
    a.mSyncToHost = e->arp_sync && e->host_ok;
    if (e->host_ok) {
        a.mHostBPM = bpm;
        a.mHostBeatPos = ppq;
        a.mHostPlaying = playing != 0;
    }
}

const mpc_engine_t api = {create, destroy, midi, set_param, get_param, render, nullptr, song_pos};

}  // namespace

extern "C" const mpc_engine_t *mpc_engine(void) { return &api; }

/* The keys the engine moved itself since the host last asked (a CC, the sustain pedal, the chorus OFF key), one per call. */
extern "C" int mpc_engine_changed(void *p, char *key, int len) {
    Inst *e = (Inst *)p;
    if (e->nchanged == 0) return 0;
    int i = e->changed[--e->nchanged];
    snprintf(key, len, "%s", PARAMS[i].key);
    return 1;
}

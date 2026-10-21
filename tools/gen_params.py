#!/usr/bin/env python3
"""vst/params.json: the KR-106 panel's controls in VST index order (append only once released).
Keys match the PARAMS table in vst/engine.cpp (which has the DSP's own parameter numbers); the host test checks
that every key here is known to the engine. Run from anywhere: tools/gen_params.py"""
import json
import os

ONOFF = ["Off", "On"]


def f(key, name, default=0.0, lo=0.0, hi=1.0):
    return {"key": key, "name": name, "min": lo, "max": hi, "default": default}


def o(key, name, options, default):
    return {"key": key, "name": name, "options": options, "default": default}


PARAMS = [
    f("tuning", "Tuning", 0.0, -1.0, 1.0),
    f("master_vol", "Volume", 0.3),
    f("porta_rate", "Portamento", 0.0),
    f("bender_dco", "Bender DCO"),
    f("bender_vcf", "Bender VCF"),
    f("bender_lfo", "Bender LFO"),
    o("porta_mode", "Porta Mode", ["Mono", "Poly I", "Poly II"], "Poly I"),
    o("transpose", "Transpose", ONOFF, "Off"),
    o("hold", "Hold", ONOFF, "Off"),
    o("arpeggio", "Arpeggio", ONOFF, "Off"),
    o("arp_mode", "Arp Mode", ["Up", "Up/Down", "Down"], "Up"),
    o("arp_range", "Arp Range", ["1 Oct", "2 Oct", "3 Oct"], "1 Oct"),
    f("arp_rate", "Arp Rate", 30 / 128),
    f("lfo_rate", "LFO Rate", 0.24),
    f("lfo_delay", "LFO Delay"),
    o("lfo_mode", "LFO Mode", ["Auto", "Manual"], "Auto"),
    f("dco_lfo", "DCO LFO"),
    f("dco_pwm", "DCO PWM", 0.5),
    o("pwm_mode", "PWM Mode", ["LFO", "Manual", "Env"], "Manual"),
    o("pulse", "Pulse", ONOFF, "On"),
    o("saw", "Saw", ONOFF, "On"),
    o("sub_sw", "Sub", ONOFF, "On"),
    o("octave", "Octave", ["16'", "8'", "4'"], "8'"),
    f("dco_sub", "Sub Level", 1.0),
    f("dco_noise", "Noise"),
    o("hpf", "HPF", ["0", "1", "2", "3"], "1"),
    f("vcf_freq", "VCF Freq", 1.0),
    f("vcf_res", "VCF Res"),
    o("vcf_env_inv", "VCF Env Polarity", ["Normal", "Inverted"], "Normal"),
    f("vcf_env", "VCF Env"),
    f("vcf_lfo", "VCF LFO"),
    f("vcf_kbd", "VCF Kbd"),
    o("vca_mode", "VCA Mode", ["Env", "Gate"], "Gate"),
    f("vca_level", "VCA Level", 0.5),
    f("env_a", "Attack", 0.25),
    f("env_d", "Decay", 0.25),
    f("env_s", "Sustain", 0.9),
    f("env_r", "Release", 0.25),
    o("adsr_mode", "Model", ["J60", "J106"], "J106"),
    dict(o("chorus_off", "Chorus Off", ONOFF, "Off"), momentary=True),
    o("chorus_i", "Chorus I", ONOFF, "On"),
    o("chorus_ii", "Chorus II", ONOFF, "Off"),
    o("voices", "Voices", ["6", "8", "10"], "6"),
    o("oversample", "VCF Oversample", ["1x", "2x", "4x"], "2x"),
    o("osc_mode", "Oscillators", ["Wavetable", "PolyBLEP"], "PolyBLEP"),
    o("ignore_vel", "Ignore Velocity", ONOFF, "On"),
    o("arp_limit_kbd", "Arp Limit Keyboard", ONOFF, "On"),
    o("mono_retrig", "Mono Retrigger", ONOFF, "On"),
]

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vst", "params.json")
    json.dump({"name": "KR-106", "params": PARAMS}, open(out, "w"), indent=1)
    print(len(PARAMS), "parameters")

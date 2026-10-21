#!/usr/bin/env python3
"""Draw the realistic JN-106 skin: a panel and controls drawn from scratch (no upstream art, no maker's name or logo) in the
style of a late-1980s polyphonic synth: charcoal panel, red section headers, black fader caps with a white line, bevelled colour
keys with LEDs, rocker switches, black knobs. Five 1280 x 628 screens (the same split as skin/make_skin.py, and the same
parameters and Q-Link pages). Everything is drawn at 2x and cut down, each control as a filmstrip or an on/off pair cropped from
its tab with the control in each position, so a frame sits exactly over its place.

    make_real_skin.build("vst")   -> vst/art_real/*.png, vst/layout.real.conf, vst/preview_real/*.png

Coordinates here are plugin pixels (0..1280 x 0..628); the layout gets +86 on y (Force Shadow's header), as skin/make_skin.py."""
import math
import os
import random
import re

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_B = FONT_S = os.path.join(HERE, "assets", "Michroma-Regular.ttf")
FONT_SCALE = 0.72   # Michroma is a wide face: same labels at the old sizes would not fit
W, H, Y_OFF, SS = 1280, 628, 86, 2

PANEL = (54, 55, 58)
RED, RED_D = (206, 24, 30), (132, 12, 18)
BLUE, BLUE_D = (28, 70, 205), (14, 36, 120)
WHITE, DIM = (238, 238, 232), (168, 168, 164)
CREAM, YELLOW, ORANGE = (222, 222, 178), (230, 228, 90), (240, 173, 56)


def S(v):
    return int(round(v * SS))


def font(size, bold=True):
    return ImageFont.truetype(FONT_B if bold else FONT_S, S(size * FONT_SCALE))


def text(im, x, y, s, size, fill=WHITE, anchor="mm", italic=False, bold=True, stroke=0):
    """Text at plugin pixel (x, y); italic=True skews it."""
    f = font(size, bold)
    l, t, r, b = f.getbbox(s, anchor="ls")
    pad = S(size)
    layer = Image.new("RGBA", (r - l + 2 * pad, S(size) * 2 + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((pad, S(size) + pad), s, font=f, fill=fill + (255,), anchor="ls",
                                  stroke_width=S(stroke), stroke_fill=fill + (255,))   # stroke fakes a bold weight: Michroma has one
    if italic:
        k = 0.2
        layer = layer.transform(layer.size, Image.AFFINE, (1, k, -k * (S(size) + pad), 0, 1, 0), Image.BICUBIC)
    w = r - l
    ox = {"l": 0, "m": w / 2, "r": w}[anchor[0]]
    oy = {"m": S(size) * 0.35, "s": 0, "t": S(size) * 0.7}[anchor[1]]
    im.alpha_composite(layer, (int(S(x) - pad - ox), int(S(y) - pad - S(size) + oy)))


def vgrad(w, h, top, bottom):
    g = Image.linear_gradient("L").resize((w, h))
    return ImageOps.colorize(g, top, bottom).convert("RGBA")


def rrect(im, box, r, fill=None, outline=None, width=1, grad=None):
    x0, y0, x1, y1 = [S(v) for v in box]
    if grad:
        mask = Image.new("L", im.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle([x0, y0, x1, y1], S(r), fill=255)
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        layer.paste(vgrad(x1 - x0 + 1, y1 - y0 + 1, grad[0], grad[1]), (x0, y0))
        im.alpha_composite(Image.composite(layer, Image.new("RGBA", im.size, (0, 0, 0, 0)), mask))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x0, y0, x1, y1], S(r), fill=None if grad else fill, outline=outline, width=S(width) if outline else 0)


def glow(im, cx, cy, r, colour, alpha):
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse([S(cx - r), S(cy - r), S(cx + r), S(cy + r)], fill=colour + (alpha,))
    im.alpha_composite(layer.filter(ImageFilter.GaussianBlur(S(r) * 0.5)))


# ---- the moving parts: each draws one control in one state onto a tab (plugin pixel coordinates) ----

def cap(im, cx, cy):
    """A fader cap: black, rounded, with a white line across the middle."""
    w, h = 68, 40
    glow(im, cx + 2, cy + 6, 26, (0, 0, 0), 150)
    rrect(im, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), 7, grad=((104, 104, 108), (22, 22, 24)))
    rrect(im, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), 7, outline=(6, 6, 6), width=2)
    d = ImageDraw.Draw(im)
    d.line([S(cx - w / 2 + 7), S(cy - h / 2 + 5), S(cx + w / 2 - 7), S(cy - h / 2 + 5)], fill=(150, 150, 154), width=S(2))
    for dy in (-6, 6):
        d.line([S(cx - w / 2 + 4), S(cy + dy), S(cx + w / 2 - 4), S(cy + dy)], fill=(8, 8, 8), width=S(2))
    d.line([S(cx - w / 2 + 4), S(cy), S(cx + w / 2 - 4), S(cy)], fill=(244, 244, 240), width=S(3))


def key(im, cx, cy, w, h, colour):
    """A bevelled square key."""
    hi = (253, 247, 203)
    lo = tuple(int(c * 0.8) for c in colour)
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    glow(im, cx + 2, cy + 5, w * 0.5, (0, 0, 0), 140)
    d = ImageDraw.Draw(im)
    d.rectangle([S(x0), S(y0), S(x1), S(y1)], fill=(0, 0, 0))
    d.rectangle([S(x0 + 3), S(y0 + 3), S(x1 - 3), S(y1 - 3)], fill=colour)
    d.rectangle([S(x0 + 3), S(y0 + 3), S(x1 - 3), S(y0 + 6)], fill=hi)
    d.rectangle([S(x0 + 3), S(y0 + 3), S(x0 + 6), S(y1 - 3)], fill=hi)
    d.rectangle([S(x0 + 4), S(y1 - 6), S(x1 - 3), S(y1 - 3)], fill=lo)
    d.rectangle([S(x1 - 6), S(y0 + 4), S(x1 - 3), S(y1 - 3)], fill=lo)


def led(im, cx, cy, on):
    r = 9
    if on:
        glow(im, cx, cy, 20, (255, 40, 40), 190)
    d = ImageDraw.Draw(im)
    d.ellipse([S(cx - r - 2), S(cy - r - 2), S(cx + r + 2), S(cy + r + 2)], fill=(14, 10, 10))
    d.ellipse([S(cx - r), S(cy - r), S(cx + r), S(cy + r)], fill=(255, 64, 54) if on else (92, 24, 24))
    d.ellipse([S(cx - r * 0.5), S(cy - r * 0.7), S(cx + r * 0.1), S(cy - r * 0.2)], fill=(255, 215, 205) if on else (150, 70, 70))


def knob(im, cx, cy, r, v):
    """A black knob with a white pointer, turning 270 degrees."""
    a = math.radians(-135 + 270 * v)
    glow(im, cx + 2, cy + 8, r, (0, 0, 0), 150)
    d = ImageDraw.Draw(im)
    d.ellipse([S(cx - r), S(cy - r), S(cx + r), S(cy + r)], fill=(10, 10, 10))
    body = Image.new("RGBA", im.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(body)
    rr = r - 4
    for i in range(14):   # a domed top: lighter toward the upper left
        t = i / 13
        c = int(70 - 48 * t)
        bd.ellipse([S(cx - rr * (1 - t * 0.55) - 5 * (1 - t)), S(cy - rr * (1 - t * 0.55) - 6 * (1 - t)),
                    S(cx + rr * (1 - t * 0.55) - 5 * (1 - t)), S(cy + rr * (1 - t * 0.55) - 6 * (1 - t))], fill=(c, c, c + 2, 255))
    im.alpha_composite(body)
    d = ImageDraw.Draw(im)
    d.line([S(cx + math.sin(a) * r * 0.25), S(cy - math.cos(a) * r * 0.25), S(cx + math.sin(a) * r * 0.86), S(cy - math.cos(a) * r * 0.86)],
           fill=(246, 246, 242), width=S(4))


def rocker(im, cx, cy, pos, n, horizontal=False, length=92):
    """A rocker: a black slot with a pale lever at one of n places."""
    w = 40
    if horizontal:
        rrect(im, (cx - length / 2, cy - w / 2, cx + length / 2, cy + w / 2), 14, fill=(12, 12, 12), outline=(60, 60, 62), width=2)
        pitch = (length - 44) / max(1, n - 1)
        px_, py_ = cx - length / 2 + 22 + pos * pitch, cy
        rrect(im, (px_ - 20, py_ - 15, px_ + 20, py_ + 15), 9, grad=((236, 236, 232), (130, 130, 128)))
    else:
        rrect(im, (cx - w / 2, cy - length / 2, cx + w / 2, cy + length / 2), 14, fill=(12, 12, 12), outline=(60, 60, 62), width=2)
        pitch = (length - 44) / max(1, n - 1)
        px_, py_ = cx, cy - length / 2 + 22 + pos * pitch
        rrect(im, (px_ - 15, py_ - 20, px_ + 15, py_ + 20), 9, grad=((236, 236, 232), (130, 130, 128)))


# ---- the panel: static art ----

class Tab:
    def __init__(self, name, title_note=""):
        self.name = name
        self.im = Image.new("RGBA", (S(W), S(H)), PANEL + (255,))
        noise = Image.effect_noise((S(W), S(H)), 18).convert("RGBA")
        noise.putalpha(30)
        self.im.alpha_composite(noise)
        d = ImageDraw.Draw(self.im)
        d.rectangle([0, 0, S(W), S(12)], fill=(8, 8, 8))
        d.rectangle([0, S(H - 12), S(W), S(H)], fill=(8, 8, 8))
        d.rectangle([0, S(12), S(W), S(14)], fill=(86, 87, 90))
        self.controls = []
        self.lines = []
        text(self.im, 36, 592, "JN-106", 40, WHITE, "lm", stroke=1.6)
        text(self.im, 250, 596, "SIX-VOICE POLYPHONIC SYNTHESIZER", 15, DIM, "lm", bold=False)

    def section(self, x0, x1, label, colour=RED, dark=RED_D):
        rrect(self.im, (x0, 26, x1, 66), 2, grad=(colour, dark))
        text(self.im, (x0 + x1) / 2, 46, label, 26, WHITE)
        d = ImageDraw.Draw(self.im)
        d.rectangle([S(x0), S(548), S(x1), S(555)], fill=colour)
        d.line([S(x1 + 6), S(70), S(x1 + 6), S(548)], fill=(206, 206, 202), width=S(2))

    def label(self, x, y, s, size=17, fill=WHITE, anchor="mm"):
        text(self.im, x, y, s, size, fill, anchor)

    def slot(self, cx, y0, y1, ticks=11, numbers=True, labels=None, side=26):
        """A fader slot with scale ticks (and 0 / 5 / 10 numerals) either side; the cap is drawn per frame."""
        d = ImageDraw.Draw(self.im)
        rrect(self.im, (cx - 7, y0 - 8, cx + 7, y1 + 8), 4, fill=(10, 10, 10), outline=(30, 30, 32), width=1)
        d.line([S(cx), S(y0 - 5), S(cx), S(y1 + 5)], fill=(0, 0, 0), width=S(3))
        for i in range(ticks):
            y = y1 - i * (y1 - y0) / (ticks - 1)
            major = (ticks == 11 and i in (0, 5, 10)) or ticks != 11
            ln = side if major else side * 0.55
            col = (236, 236, 232) if major else (150, 150, 148)
            d.line([S(cx - 12 - ln), S(y), S(cx - 12), S(y)], fill=col, width=S(2))
            d.line([S(cx + 12), S(y), S(cx + 12 + ln), S(y)], fill=col, width=S(2))
        if numbers and ticks == 11:
            for i, n in ((0, "0"), (5, "5"), (10, "10")):
                y = y1 - i * (y1 - y0) / 10
                text(self.im, cx - 12 - side - 12, y, n, 14, DIM, "rm", italic=False)
        for i, s in (labels or {}).items():
            y = y1 - i * (y1 - y0) / (ticks - 1)
            text(self.im, cx + 12 + side + 8, y, s, 15, WHITE, "lm")

    def add(self, **c):
        self.controls.append(c)


Y0, Y1 = 150, 450          # a fader's travel (plugin pixels)


def slider_at(t, key, cx, name, labels=None, ticks=11, frames=33, vals=None, y0=Y0, y1=Y1, nums=False, side=22):
    t.slot(cx, y0, y1, ticks=ticks, labels=labels, numbers=nums and ticks == 11, side=side)
    t.label(cx, y0 - 36, name, 15)
    t.add(kind="slider", key=key, cx=cx, y0=y0, y1=y1, frames=frames, vals=vals)


def keyed(t, key, cx, cy, name, colour, w=84, h=70):
    t.label(cx, cy - h / 2 - 50, name, 17)
    t.add(kind="key", key=key, cx=cx, cy=cy, w=w, h=h, colour=colour)


def rocker_at(t, key, cx, cy, labels, n, horizontal=False, name=None, length=96, ends=False):
    if name:
        t.label(cx, cy - (length / 2 if not horizontal else 40) - 30, name, 17)
    pitch = (length - 44) / max(1, n - 1)
    for i, s in enumerate(labels):
        if horizontal and ends:   # the two labels outside the ends of the slot
            t.label(cx - length / 2 - 16 if i == 0 else cx + length / 2 + 16, cy, s, 13, anchor="rm" if i == 0 else "lm")
        elif horizontal:
            t.label(cx - length / 2 + 22 + i * pitch, cy + 46, s, 13)
        else:
            t.label(cx + 34, cy - length / 2 + 22 + i * pitch, s, 13, anchor="lm")
    t.add(kind="rocker", key=key, cx=cx, cy=cy, n=n, horizontal=horizontal, length=length)


def knob_at(t, key, cx, cy, r, name, scale=True):
    t.label(cx, cy - r - 52, name, 19)
    d = ImageDraw.Draw(t.im)
    for i in range(11):
        a = math.radians(-135 + 270 * i / 10)
        r0, r1 = r + 10, r + (22 if i in (0, 5, 10) else 17)
        d.line([S(cx + math.sin(a) * r0), S(cy - math.cos(a) * r0), S(cx + math.sin(a) * r1), S(cy - math.cos(a) * r1)],
               fill=(220, 220, 216), width=S(2))
    t.add(kind="knob", key=key, cx=cx, cy=cy, r=r)


# ---- the five tabs ----

def tab_lfo_dco():
    t = Tab("LFO DCO")
    t.section(20, 372, "LFO")
    slider_at(t, "lfo_rate", 90, "RATE", nums=True)
    slider_at(t, "lfo_delay", 190, "DELAY")
    rocker_at(t, "lfo_mode", 282, 300, ["AUTO", "MAN"], 2, name="MODE")
    t.section(384, 1096, "DCO")
    slider_at(t, "dco_lfo", 446, "LFO", nums=True)
    slider_at(t, "dco_pwm", 536, "PWM")
    rocker_at(t, "pwm_mode", 626, 300, ["LFO", "MAN", "ENV"], 3, name="PWM MODE")
    for key_, cx, nm, col in (("pulse", 740, "PULSE", YELLOW), ("saw", 820, "SAW", YELLOW), ("sub_sw", 900, "SUB", ORANGE)):
        t.add(kind="keyled", key=key_, cx=cx, cy=300, w=70, h=70, colour=col)
        t.label(cx, 300 - 35 - 52, nm, 17)
    rocker_at(t, "octave", 820, 450, ["16'", "8'", "4'"], 3, horizontal=True, name="RANGE", length=130)
    slider_at(t, "dco_sub", 996, "SUB", side=14)
    slider_at(t, "dco_noise", 1074, "NOISE", side=14)
    t.section(1108, 1260, "HPF")
    slider_at(t, "hpf", 1184, "FREQ", ticks=4, frames=4, vals=[0, 1 / 3, 2 / 3, 1], labels={0: "0", 1: "1", 2: "2", 3: "3"})
    return t


def tab_filter():
    t = Tab("FILTER AMP ENV")
    t.section(20, 556, "VCF")
    slider_at(t, "vcf_freq", 80, "FREQ", nums=True)
    slider_at(t, "vcf_res", 160, "RES")
    rocker_at(t, "vcf_env_inv", 240, 300, ["", ""], 2, name="POLARITY")
    t.label(274, 254, "NORM", 15, anchor="lm")
    t.label(274, 346, "INV", 15, anchor="lm")
    slider_at(t, "vcf_env", 380, "ENV")
    slider_at(t, "vcf_lfo", 454, "LFO")
    slider_at(t, "vcf_kbd", 528, "KYBD")
    t.section(568, 770, "VCA")
    rocker_at(t, "vca_mode", 604, 300, ["ENV", "GATE"], 2, name="MODE")
    slider_at(t, "vca_level", 734, "LEVEL", ticks=3, frames=33)
    t.label(694, 150, "+5", 14, DIM, "rm")
    t.label(694, 300, "0", 14, DIM, "rm")
    t.label(694, 450, "-5", 14, DIM, "rm")
    t.section(782, 1098, "ENV")
    for key_, cx, nm in (("env_a", 834, "A"), ("env_d", 908, "D"), ("env_s", 982, "S"), ("env_r", 1056, "R")):
        slider_at(t, key_, cx, nm, nums=False, side=18, y0=140, y1=400)
    rocker_at(t, "adsr_mode", 940, 510, ["60", "106"], 2, horizontal=True, length=110, ends=True)
    t.section(1110, 1262, "CHORUS", BLUE, BLUE_D)
    for key_, cx, nm, col, kind in (("chorus_off", 1138, "OFF", CREAM, "button"), ("chorus_i", 1186, "I", YELLOW, "keyled"),
                                    ("chorus_ii", 1234, "II", ORANGE, "keyled")):
        t.add(kind=kind, key=key_, cx=cx, cy=300, w=44, h=56, colour=col)
        t.label(cx, 300 - 28 - 52, nm, 16)
    return t


def tab_arp():
    t = Tab("ARP")
    t.section(20, 330, "KEYS")
    t.add(kind="keyled", key="transpose", cx=110, cy=300, w=96, h=84, colour=YELLOW)
    t.label(110, 300 - 42 - 52, "TRANSPOSE", 19)
    t.add(kind="keyled", key="hold", cx=240, cy=300, w=96, h=84, colour=YELLOW)
    t.label(240, 300 - 42 - 52, "HOLD", 19)
    t.section(342, 1260, "ARPEGGIO", BLUE, BLUE_D)
    t.add(kind="keyled", key="arpeggio", cx=440, cy=300, w=96, h=84, colour=YELLOW)
    t.label(440, 300 - 42 - 52, "ON / OFF", 19)
    rocker_at(t, "arp_mode", 640, 300, ["UP", "UP / DOWN", "DOWN"], 3, name="MODE", length=150)
    rocker_at(t, "arp_range", 860, 300, ["1", "2", "3"], 3, name="RANGE", length=150)
    slider_at(t, "arp_rate", 1100, "RATE", nums=True)
    return t


def tab_perform():
    t = Tab("PERFORM")
    t.section(20, 700, "PERFORMANCE")
    knob_at(t, "tuning", 140, 300, 58, "TUNING")
    knob_at(t, "master_vol", 340, 300, 58, "VOLUME")
    knob_at(t, "porta_rate", 540, 300, 58, "PORTAMENTO")
    t.section(712, 1260, "BENDER")
    slider_at(t, "bender_dco", 780, "DCO", nums=True)
    slider_at(t, "bender_vcf", 860, "VCF")
    slider_at(t, "bender_lfo", 940, "LFO")
    rocker_at(t, "porta_mode", 1130, 300, ["MONO", "POLY I", "POLY II"], 3, name="MODE", length=150)
    return t


# SETTINGS: a 3 x 2 grid of cards, each a Michroma label (baked into tab5) over a two-option segment row. enum_h's cy is
# the row's centre plus the 86 px header offset, and label="" leaves the labelling to the art.
CARD_W, CARD_H = 380, 150
CARD_X = (213, 640, 1067)
CARD_Y = (125, 315)
SETTING_CARDS = [("VCF OVERSAMPLE", "oversample"), ("OSCILLATORS", "osc_mode"), ("IGNORE VELOCITY", "ignore_vel"),
                 ("ARP LIMIT TO KEYBOARD", "arp_limit_kbd"), ("MONO RETRIGGER", "mono_retrig")]


def settings_art(t):
    for i, (name, _) in enumerate(SETTING_CARDS + [("ENGINE", None)]):
        cx, y = CARD_X[i % 3], CARD_Y[i // 3]
        rrect(t.im, (cx - CARD_W / 2, y, cx + CARD_W / 2, y + CARD_H), 8, fill=(54, 55, 58), outline=(88, 89, 92), width=2)
        t.label(cx, y + 32, name, 17)
    cx, y = CARD_X[2], CARD_Y[1]
    for k, line in enumerate(("DSP: ULTRAMASTER KR-106", "BY KARL LAROCCA, GPL-3.0", "SIX VOICES, FIXED")):
        t.label(cx, y + 78 + k * 26, line, 13, DIM)


def settings_layout():
    out = ["[tab SETTINGS]", "art file=art_real/tab5.png fit=stretch"]
    for i, (_, key) in enumerate(SETTING_CARDS):
        cx, y = CARD_X[i % 3], CARD_Y[i // 3]
        out.append('enum_h cx=%d cy=%d label="" key=%s sw=150 sh=56' % (cx, y + 95 + Y_OFF, key))
    return "\n".join(out) + "\n"



HEADER = """# generated by skin/make_real_skin.py: the KR-106's realistic panel, drawn for the MPC's 1280x628 plugin area.
theme_bg=2a2b2e
theme_panel=36373a
theme_ink=eeeee8
theme_ink_dim=a8a8a4
theme_accent=ce181e
theme_accent_hi=ff4a4a
theme_lcd=1b1a1a
theme_seg_active=ce181e
theme_seg_inactive=2a2b2e
theme_seg_active_tx=ffffff
theme_box=36373a
"""

QLINKS = {
    "LFO DCO": "lfo_rate,lfo_delay,dco_lfo,dco_pwm,dco_sub,dco_noise,hpf,octave,pwm_mode,pulse,saw,sub_sw,lfo_mode",
    "FILTER AMP ENV": "vcf_freq,vcf_res,vcf_env,vcf_lfo,vcf_kbd,vca_level,env_a,env_d,env_s,env_r,vcf_env_inv,vca_mode,adsr_mode,chorus_i,chorus_ii",
    "ARP": "arp_rate,arp_mode,arp_range,arpeggio,hold,transpose",
    "PERFORM": "master_vol,tuning,porta_rate,porta_mode,bender_dco,bender_vcf,bender_lfo",
}


# ---- render: strips and pairs cropped from the tab, and the layout lines ----

class Renderer:
    def __init__(self, out):
        self.out = out
        self.dir = os.path.join(out, "art_real")
        os.makedirs(self.dir, exist_ok=True)

    def save(self, im, name):
        im.convert("RGB").save(os.path.join(self.dir, name + ".png"))

    def frame(self, tab, rect, draw):
        """rect = (x, y, w, h) plugin pixels: that part of the tab with draw(canvas, ox, oy) applied (ox, oy = rect's corner,
        subtracted from the control's coordinates), cut to screen size."""
        x, y, w, h = rect
        base = tab.im.crop((S(x), S(y), S(x + w), S(y + h)))
        draw(base, x, y)
        return base.resize((w, h), Image.LANCZOS)

    def tab(self, i, tab):
        L = [("art", "art file=art_real/tab%d.png fit=stretch" % i)]
        for c in tab.controls:
            k, key_ = c["kind"], c["key"]
            if k == "slider":
                cx, y0, y1, n = c["cx"], c["y0"], c["y1"], c["frames"]
                vals = c["vals"] or [j / (n - 1) for j in range(n)]
                w, h = 70, (y1 - y0) + 72
                cy = (y0 + y1) // 2
                rect = (cx - w // 2, cy - h // 2, w, h)
                strip = Image.new("RGB", (w, h * len(vals)))
                for j, v in enumerate(vals):
                    strip.paste(self.frame(tab, rect, lambda b, ox, oy, v=v: cap(b, cx - ox, y1 - v * (y1 - y0) - oy)), (0, j * h))
                self.save(strip, key_)
                L.append(("slider_v", 'slider_v cx=%d cy=%d w=%d h=%d label="" key=%s strip=art_real/%s.png frames=%d ns=0 vs=0 bw=%d'
                          % (cx, cy, w, h, key_, key_, len(vals), w)))
            elif k == "knob":
                cx, cy, r = c["cx"], c["cy"], c["r"]
                s = 2 * r + 10
                n = 64
                rect = (cx - s // 2, cy - s // 2, s, s)
                strip = Image.new("RGB", (s, s * n))
                for j in range(n):
                    strip.paste(self.frame(tab, rect, lambda b, ox, oy, j=j: knob(b, cx - ox, cy - oy, r, j / (n - 1))), (0, j * s))
                self.save(strip, key_)
                L.append(("knob", 'knob cx=%d cy=%d r=%d label="" key=%s strip=art_real/%s.png frames=%d ns=0 vs=0 bw=%d'
                          % (cx, cy, r, key_, key_, n, s)))
            elif k in ("key", "keyled", "button"):
                cx, cy, w, h, col = c["cx"], c["cy"], c["w"], c["h"], c["colour"]
                top = 30 if k == "keyled" else 6
                rect = (cx - w // 2 - 5, cy - h // 2 - top - 14, w + 10, h + top + 28)
                for on in (0, 1):
                    def d(b, ox, oy, on=on):
                        key(b, cx - ox, cy - oy, w, h, col)
                        if k == "keyled":
                            led(b, cx - ox, cy - oy - h // 2 - 22, on)
                    self.save(self.frame(tab, rect, d), "%s_%s" % (key_, "on" if on else "off"))
                rw, rh = rect[2], rect[3]
                rcx, rcy = rect[0] + rw // 2, rect[1] + rh // 2
                if k == "button":
                    L.append(("button", 'button cx=%d cy=%d label="" key=%s img=art_real/%s_off.png img_on=art_real/%s_on.png w=%d h=%d'
                              % (rcx, rcy, key_, key_, key_, rw, rh)))
                else:
                    L.append(("toggle", 'toggle cx=%d cy=%d label="" key=%s img=art_real/%s_off.png img_on=art_real/%s_on.png w=%d h=%d ns=0'
                              % (rcx, rcy, key_, key_, key_, rw, rh)))
            elif k == "rocker":
                cx, cy, n, hz, ln = c["cx"], c["cy"], c["n"], c["horizontal"], c["length"]
                pw, ph = (ln + 24, 76) if hz else (76, ln + 24)
                rect = (cx - pw // 2, cy - ph // 2, pw, ph)
                files = []
                for p in range(n):
                    nm = "%s_%d" % (key_, p)
                    self.save(self.frame(tab, rect, lambda b, ox, oy, p=p: rocker(b, cx - ox, cy - oy, p, n, hz, ln)), nm)
                    files.append("art_real/%s.png" % nm)
                if n == 2:
                    L.append(("toggle", 'toggle cx=%d cy=%d label="" key=%s img=%s img_on=%s w=%d h=%d ns=0'
                              % (cx, cy, key_, files[0], files[1], pw, ph)))
                else:
                    L.append(("picture", 'picture x=%d y=%d w=%d h=%d key=%s files="%s"' % (rect[0], rect[1], pw, ph, key_, ",".join(files))))
                    if hz:
                        L.append(("enum", 'enum_h cx=%d cy=%d label="" key=%s options="%s" sw=%d sh=%d img=art_real/clear.png img_on=art_real/clear.png'
                                  % (cx, cy, key_, ",".join([" "] * n), pw // n, ph)))
                    else:
                        L.append(("enum", 'enum_v cx=%d cy=%d label="" key=%s options="%s" sw=%d sh=%d img=art_real/clear.png img_on=art_real/clear.png'
                                  % (cx, cy, key_, ",".join([" "] * n), pw, ph // n)))
        return L

    def preview(self, tab, i, defaults):
        im = tab.im.copy()
        for c in tab.controls:
            v = defaults.get(c["key"], 0)
            k = c["kind"]
            if k == "slider":
                cap(im, c["cx"], c["y1"] - v * (c["y1"] - c["y0"]))
            elif k == "knob":
                knob(im, c["cx"], c["cy"], c["r"], v)
            elif k in ("key", "keyled", "button"):
                key(im, c["cx"], c["cy"], c["w"], c["h"], c["colour"])
                if k == "keyled":
                    led(im, c["cx"], c["cy"] - c["h"] // 2 - 22, v > 0.5)
            elif k == "rocker":
                rocker(im, c["cx"], c["cy"], round(v * (c["n"] - 1)), c["n"], c["horizontal"], c["length"])
        os.makedirs(os.path.join(self.out, "preview_real"), exist_ok=True)
        im.convert("RGB").resize((W, H), Image.LANCZOS).save(os.path.join(self.out, "preview_real", "tab%d.png" % i))


def shift(line):
    if line.startswith("art "):
        return line
    return re.sub(r"\b(cy|y)=(\d+)", lambda m: "%s=%d" % (m.group(1), int(m.group(2)) + Y_OFF), line)


def build(out):
    import json
    ps = {p["key"]: p for p in json.load(open(os.path.join(out, "params.json")))["params"]}

    def norm(k):
        p = ps[k]
        if "options" in p:
            return p["options"].index(p["default"]) / max(1, len(p["options"]) - 1)
        return (p["default"] - p["min"]) / (p["max"] - p["min"])

    defaults = {k: norm(k) for k in ps}
    r = Renderer(out)
    Image.new("RGBA", (4, 4), (0, 0, 0, 0)).save(os.path.join(r.dir, "clear.png"))
    tabs = [tab_lfo_dco(), tab_filter(), tab_arp(), tab_perform()]
    lines = [HEADER]
    rank = {"art": 0, "knob": 1, "slider_v": 2}
    for i, t in enumerate(tabs, 1):
        r.save(t.im, "tab%d" % i)
        got = r.tab(i, t)
        r.preview(t, i, defaults)
        lines.append("[tab %s]" % t.name)
        lines += [shift(l) for _, l in sorted(got, key=lambda g: rank.get(g[0], 3))]
        lines.append('qlinks "%s" = %s' % (t.name, QLINKS[t.name]))
        lines.append("")
    t5 = Tab("SETTINGS")
    t5.section(20, 1260, "SETTINGS")
    settings_art(t5)
    r.save(t5.im, "tab5")
    r.preview(t5, 5, defaults)
    lines.append(settings_layout())
    open(os.path.join(out, "layout.real.conf"), "w").write("\n".join(lines))


if __name__ == "__main__":
    build(os.path.join(HERE, "..", "vst"))

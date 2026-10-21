#!/usr/bin/env python3
"""Draw the KR-106 skin for the MPC's 1280 x 628 plugin area from the synth's own @2x artwork (skin/assets, GPL-3.0, from
Ultramaster KR-106 resources/img): the panel background cut into two rows plus the performance block, and every control
drawn the way upstream's editor draws it (Source/Controls/KR106Slider.h, KR106Button.h, KR106Switch.h, KR106Knob.h), as a
filmstrip or an on/off pair cropped from the panel so each frame sits exactly over its place.  No keybed and no scope.

    make_skin.build("vst")   -> vst/art/*.png, vst/layout.conf, vst/preview/panel.png (all controls at their defaults)

Coordinates: `c` = the 2x canvas (upstream's @2x pixels, editor base coordinates x 2); `m` = MPC screen pixels."""
import math
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "assets")
W, H = 1280, 628
Y_OFF = 86   # layout y = plugin y + 86 (Force Shadow's); art files stay in plugin coordinates
PAGE = (27, 26, 26)


def img(name):
    return Image.open(os.path.join(A, name)).convert("RGBA")


class Region:
    """A box of the canvas shown at (X0, Y0) on the screen, k times bigger."""
    def __init__(self, box, X0, Y0, k):
        self.box, self.X0, self.Y0, self.k = box, X0, Y0, k
        self.w, self.h = round((box[2] - box[0]) * k), round((box[3] - box[1]) * k)

    @property
    def kx(self):
        return self.w / (self.box[2] - self.box[0])

    @property
    def ky(self):
        return self.h / (self.box[3] - self.box[1])

    def has(self, x, y):
        return self.box[0] <= x < self.box[2] and self.box[1] <= y < self.box[3]

    def to_m(self, x, y):
        return self.X0 + (x - self.box[0]) * self.kx, self.Y0 + (y - self.box[1]) * self.ky

    def to_c(self, X, Y):
        return self.box[0] + (X - self.X0) / self.kx, self.box[1] + (Y - self.Y0) / self.ky


def fit(box, k, X0=None, Y0=None):
    r = Region(box, 0, 0, k)
    return Region(box, (W - r.w) // 2 if X0 is None else X0, (H - r.h) // 2 if Y0 is None else Y0, k)


# The upstream panel (1880 x 448 canvas pixels) cut by section, one tab each; the power block and the keybed are not used.
PERF = Region((38, 218, 260, 436), 0, 96, 2.0)
TUNE = Region((38, 96, 174, 190), 0, 96 + (PERF.h - round(94 * 2.0)) // 2, 2.0)
_total = TUNE.w + 40 + PERF.w
TUNE.X0, PERF.X0 = (W - _total) // 2, (W - _total) // 2 + TUNE.w + 40
TABS = [
    ("LFO DCO", [fit((495, 6, 988, 212), 1260 / 493.0)]),
    ("FILTER AMP ENV", [fit((987, 6, 1578, 212), 1260 / 591.0)]),
    ("ARP", [fit((176, 6, 495, 212), 2.8)]),
    ("PERFORM", [TUNE, PERF]),
]


def find(cx, cy):
    for name, regs in TABS:
        for r in regs:
            if r.has(cx, cy):
                return name, r
    raise SystemExit("control at canvas (%d, %d) is on no tab" % (cx, cy))


# ---- drawing in canvas pixels (one base pixel = 2) ----

def px(d, ox, oy, x, y, w, h, col):
    """A rectangle in base pixels (x, y, w, h) relative to the control's origin (ox, oy in canvas pixels)."""
    d.rectangle([ox + round(x * 2), oy + round(y * 2), ox + round((x + w) * 2) - 1, oy + round((y + h) * 2) - 1], fill=col)


BRIGHT, DIM = (219, 219, 219), (126, 126, 126)
HANDLE = None


def slider(cv, ox, oy, val, extra=0, ticks=None):
    """KR106Slider::paint: the ticks, the well and the handle, in a 19 x 49 base-pixel cell."""
    d = ImageDraw.Draw(cv)
    tw = 17 + extra
    if ticks is None:
        ticks = [(round(44 - i * 4), BRIGHT if i in (0, 5, 10) else DIM) for i in range(11)]
    for y, col in ticks:
        px(d, ox, oy, 1, y, tw, 1, col)
    dark, black = (34, 34, 34), (0, 0, 0)
    px(d, ox, oy, 7, 1, 5, 47, dark)
    px(d, ox, oy, 8, 0, 3, 1, dark)
    px(d, ox, oy, 8, 48, 3, 1, dark)
    px(d, ox, oy, 9, 2, 1, 45, black)
    fy = round(44 - val * 40)
    hx = math.floor((19 - 13) / 2)
    cv.paste(HANDLE, (ox + hx * 2, oy + round((fy - 4 + 1) * 2)), HANDLE)


COLORS = [((253, 247, 203), (220, 220, 178), (178, 179, 144)),   # cream
          ((253, 247, 203), (228, 229, 88), (180, 179, 69)),     # yellow
          ((253, 247, 203), (240, 173, 56), (180, 126, 41))]     # orange


def button(cv, ox, oy, l, t, r, b, kind):
    """DrawKR106Button: a bevelled key, l..r x t..b in base pixels."""
    hi, face, lo = COLORS[kind]
    d = ImageDraw.Draw(cv)
    px(d, ox, oy, l + 2, t + 2, r - l - 4, b - t - 4, face)
    px(d, ox, oy, l + 1, t + 1, r - l - 2, 1, hi)
    px(d, ox, oy, l + 1, t + 1, 1, b - t - 2, hi)
    px(d, ox, oy, l + 2, b - 2, r - l - 3, 1, lo)
    px(d, ox, oy, r - 2, t + 2, 1, b - t - 3, lo)
    for rect in ((l, t, r - l, 1), (l, b - 1, r - l, 1), (l, t, 1, b - t), (r - 1, t, 1, b - t)):
        px(d, ox, oy, *rect, (0, 0, 0))


def button_led(cv, ox, oy, kind, on):
    """KR106ButtonLED: the LED (9 x 9 at x 4) over a 17 x 19 key, 17 x 28 in all."""
    frame = LED.crop((0, 18 if on else 0, 18, 36 if on else 18))
    cv.paste(frame, (ox + 8, oy), frame)
    button(cv, ox, oy, 0, 9, 17, 28, kind)


def sprite(cv, ox, oy, sheet, frame, vertical_frames=True):
    """KR106Switch / KR106HorizontalSwitch: one of the sheet's three frames stacked down."""
    fh = sheet.height // 3
    f = sheet.crop((0, frame * fh, sheet.width, (frame + 1) * fh))
    cv.paste(f, (ox, oy), f)


def knob(cv, ox, oy, val):
    """KR106Knob with the small knob's sheet: 32 frames of 56 x 54."""
    n = KNOB.width // 56
    f = KNOB.crop((round(val * (n - 1)) * 56, 0, round(val * (n - 1)) * 56 + 56, 54))
    cv.paste(f, (ox, oy), f)


# ---- the controls: key, kind, base rect (x, y, w, h) as upstream's PluginEditor.cpp places them ----

SLIDERS = [  # key, x, y, extraRight
    ("bender_dco", 34, 147, 1), ("bender_vcf", 52, 147, 1), ("bender_lfo", 70, 147, 0),
    ("arp_rate", 227, 33, 0), ("lfo_rate", 249, 33, 1), ("lfo_delay", 267, 33, 0),
    ("dco_lfo", 313, 33, 1), ("dco_pwm", 331, 33, 0), ("dco_sub", 427, 33, 1), ("dco_noise", 445, 33, 0),
    ("vcf_freq", 495, 33, 1), ("vcf_res", 513, 33, 0), ("vcf_env", 549, 33, 1), ("vcf_lfo", 567, 33, 1), ("vcf_kbd", 585, 33, 0),
    ("vca_level", 634, 33, 0),
    ("env_a", 656, 33, 1), ("env_d", 674, 33, 1), ("env_s", 692, 33, 1), ("env_r", 710, 33, 0),
]
HPF = ("hpf", 470, 33)
KNOBS = [("tuning", 40, 64), ("master_vol", 30, 118), ("porta_rate", 66, 118)]
SW3V = [("porta_mode", 92, 161), ("arp_mode", 175, 46), ("arp_range", 210, 46), ("pwm_mode", 351, 46)]
SW3H = [("octave", 389, 84)]
SW2V = [("lfo_mode", 294, 46), ("vcf_env_inv", 536, 46), ("vca_mode", 614, 45)]
SW2H = [("adsr_mode", 680, 84)]
LEDS = [("transpose", 95, 43, 1), ("hold", 122, 43, 1), ("arpeggio", 154, 43, 1),
        ("pulse", 377, 43, 1), ("saw", 393, 43, 1), ("sub_sw", 409, 43, 2),
        ("chorus_i", 751, 43, 1), ("chorus_ii", 767, 43, 2)]
CHORUS_OFF = ("chorus_off", 735, 52)

HEADER = """# generated by skin/make_skin.py: Ultramaster KR-106's panel artwork and controls, drawn for the MPC's 1280x628 plugin area.
theme_bg=1b1a1a
theme_panel=3e3e3e
theme_ink=dbdbdb
theme_ink_dim=7e7e7e
theme_accent=c60a0a
theme_accent_hi=ff4040
theme_lcd=1b1a1a
theme_seg_active=c60a0a
theme_seg_inactive=2a2a2a
theme_seg_active_tx=ffffff
theme_box=3e3e3e
"""

QLINKS = {
    "LFO DCO": "lfo_rate,lfo_delay,dco_lfo,dco_pwm,dco_sub,dco_noise,hpf,octave,pwm_mode,pulse,saw,sub_sw,lfo_mode",
    "FILTER AMP ENV": "vcf_freq,vcf_res,vcf_env,vcf_lfo,vcf_kbd,vca_level,env_a,env_d,env_s,env_r,vcf_env_inv,vca_mode,adsr_mode,chorus_i,chorus_ii",
    "ARP": "arp_rate,arp_mode,arp_range,arpeggio,hold,transpose",
    "PERFORM": "master_vol,tuning,porta_rate,porta_mode,bender_dco,bender_vcf,bender_lfo",
}

SETTINGS = """[tab SETTINGS]
enum_h cx=380 cy=230 label="VOICES" key=voices sw=140 sh=56
enum_h cx=900 cy=230 label="VCF OVERSAMPLE" key=oversample sw=140 sh=56
enum_h cx=380 cy=390 label="OSCILLATORS" key=osc_mode sw=190 sh=56
enum_h cx=900 cy=390 label="IGNORE VELOCITY" key=ignore_vel sw=140 sh=56
enum_h cx=380 cy=550 label="ARP LIMIT TO KEYBOARD" key=arp_limit_kbd sw=140 sh=56
enum_h cx=900 cy=550 label="MONO RETRIGGER" key=mono_retrig sw=140 sh=56
qlinks "SETTINGS" = voices,oversample,osc_mode,ignore_vel,arp_limit_kbd,mono_retrig
"""


def shift(line):
    """A layout line with its y (cy= or picture's y=) moved down by Y_OFF; art lines are unchanged."""
    import re
    if line.startswith("art "):
        return line
    return re.sub(r"\b(cy|y)=(\d+)", lambda m: "%s=%d" % (m.group(1), int(m.group(2)) + Y_OFF), line)


class Skin:
    def __init__(self, out):
        self.out = out
        os.makedirs(os.path.join(out, "art"), exist_ok=True)
        self.canvas = img("kr106_background@2x.png").convert("RGB")
        self.lines = {name: [] for name, _ in TABS}

    def save(self, im, name):
        im.convert("RGB").save(os.path.join(self.out, "art", name + ".png"))

    def crop(self, reg, rect, draw):
        """The screen rectangle rect = (X, Y, w, h) of the panel with draw(canvas_crop, ox, oy) applied, at screen size."""
        X, Y, w, h = rect
        c0, c1 = reg.to_c(X, Y), reg.to_c(X + w, Y + h)
        ix0, iy0, ix1, iy1 = math.floor(c0[0]) - 2, math.floor(c0[1]) - 2, math.ceil(c1[0]) + 2, math.ceil(c1[1]) + 2
        cv = self.canvas.crop((ix0, iy0, ix1, iy1))
        if draw:
            draw(cv, ix0, iy0)
        return cv.resize((w, h), Image.LANCZOS, box=(c0[0] - ix0, c0[1] - iy0, c1[0] - ix0, c1[1] - iy0))

    def place(self, base, cw, ch):
        """Control at base (x, y), cw x ch canvas pixels: its tab, region, canvas origin and screen centre."""
        ox, oy = base[0] * 2, base[1] * 2
        tab, reg = find(ox + cw / 2, oy + ch / 2)
        cxm, cym = reg.to_m(ox + cw / 2, oy + ch / 2)
        return tab, reg, ox, oy, round(cxm), round(cym)

    def background(self):
        for i, (name, regs) in enumerate(TABS, 1):
            bg = Image.new("RGB", (W, H), PAGE)
            for reg in regs:
                bg.paste(self.canvas.resize((reg.w, reg.h), Image.LANCZOS, box=reg.box), (reg.X0, reg.Y0))
            self.save(bg, "tab%d" % i)
            self.lines[name].append("art file=art/tab%d.png fit=stretch" % i)

    def slider_strip(self, key, x, y, extra, frames=33, ticks=None, vals=None):
        tab, reg, ox, oy, cxm, cym = self.place((x, y), 38, 98)
        w, h = round(36 * reg.kx) // 2 * 2, round(98 * reg.ky) // 2 * 2
        rect = (cxm - w // 2, cym - h // 2, w, h)
        vals = vals or [i / (frames - 1) for i in range(frames)]
        strip = Image.new("RGB", (w, h * len(vals)))
        for i, v in enumerate(vals):
            strip.paste(self.crop(reg, rect, lambda cv, a, b, v=v: slider(cv, ox - a, oy - b, v, extra, ticks)), (0, i * h))
        self.save(strip, key)
        self.lines[tab].append('slider_v cx=%d cy=%d w=%d h=%d label="" key=%s strip=art/%s.png frames=%d ns=0 vs=0 bw=%d'
                               % (cxm, cym, w, h, key, key, len(vals), w))

    def build(self):
        global HANDLE, LED, KNOB
        HANDLE, LED, KNOB = img("slider_handle@2x.png"), img("led_red@2x.png"), img("smallknob@2x.png")
        sw3v, sw3h = img("switch_3way@2x.png"), img("switch_3way_horizontal@2x.png")
        self.background()
        for key, x, y, extra in SLIDERS:
            self.slider_strip(key, x, y, extra)
        hp = [(round(44 - i * 40 / 3), BRIGHT) for i in range(4)]
        self.slider_strip(HPF[0], HPF[1], HPF[2], 0, ticks=hp, vals=[0, 1 / 3, 2 / 3, 1])
        for key, x, y in KNOBS:
            tab, reg, ox, oy, cxm, cym = self.place((x, y), 56, 54)
            r = min(59, int(56 * reg.kx / 2) + 2)
            s = 2 * r + 10
            rect = (cxm - s // 2, cym - s // 2, s, s)
            frames = KNOB.width // 56
            strip = Image.new("RGB", (s, s * frames))
            for i in range(frames):
                strip.paste(self.crop(reg, rect, lambda cv, a, b, i=i: knob(cv, ox - a, oy - b, i / (frames - 1))), (0, i * s))
            self.save(strip, key)
            self.lines[tab].append('knob cx=%d cy=%d r=%d label="" key=%s strip=art/%s.png frames=%d ns=0 vs=0 bw=%d'
                                   % (cxm, cym, r, key, key, frames, s))
        # three-way switches: one picture per position under clear touch zones
        for kind, group, sheet, cw, ch in (("v", SW3V, sw3v, 18, 48), ("h", SW3H, sw3h, 48, 18)):
            for key, x, y in group:
                tab, reg, ox, oy, cxm, cym = self.place((x, y), cw, ch)
                pw, ph = round(cw * reg.kx) + 16, round(ch * reg.ky) + 16
                rect = (cxm - pw // 2, cym - ph // 2, pw, ph)
                files = []
                for i in range(3):
                    self.save(self.crop(reg, rect, lambda cv, a, b, i=i: sprite(cv, ox - a, oy - b, sheet, i)), "%s_%d" % (key, i))
                    files.append("art/%s_%d.png" % (key, i))
                L = self.lines[tab]
                L.append('picture x=%d y=%d w=%d h=%d key=%s files="%s"' % (rect[0], rect[1], pw, ph, key, ",".join(files)))
                if kind == "v":
                    L.append('enum_v cx=%d cy=%d label="" key=%s options=" , , " sw=%d sh=%d img=art/clear.png img_on=art/clear.png'
                             % (cxm, cym, key, pw, (ph - 4) // 3))
                else:
                    L.append('enum_h cx=%d cy=%d label="" key=%s options=" , , " sw=%d sh=%d img=art/clear.png img_on=art/clear.png'
                             % (cxm, cym, key, pw // 3, ph))
        # two-way switches: frames 0 and 2 of the same sheet
        for group, sheet, cw, ch in ((SW2V, sw3v, 18, 48), (SW2H, sw3h, 48, 18)):
            for key, x, y in group:
                tab, reg, ox, oy, cxm, cym = self.place((x, y), cw, ch)
                pw, ph = round(cw * reg.kx) + 16, round(ch * reg.ky) + 16
                rect = (cxm - pw // 2, cym - ph // 2, pw, ph)
                for i, nm in ((0, "off"), (2, "on")):
                    self.save(self.crop(reg, rect, lambda cv, a, b, i=i: sprite(cv, ox - a, oy - b, sheet, i)), "%s_%s" % (key, nm))
                self.lines[tab].append('toggle cx=%d cy=%d label="" key=%s img=art/%s_off.png img_on=art/%s_on.png w=%d h=%d ns=0'
                                       % (cxm, cym, key, key, key, pw, ph))
        # the lit keys: LED over a key, on/off pictures as wide as the spacing of upstream's keys allows
        for key, x, y, kind in LEDS:
            tab, reg, ox, oy, cxm, cym = self.place((x, y), 34, 56)
            pw, ph = round(32 * reg.kx), round(58 * reg.ky)   # upstream's keys of one group sit 16 base pixels apart
            rect = (cxm - pw // 2, cym - ph // 2, pw, ph)
            for on in (0, 1):
                self.save(self.crop(reg, rect, lambda cv, a, b, on=on: button_led(cv, ox - a, oy - b, kind, on)), "%s_%s" % (key, "on" if on else "off"))
            self.lines[tab].append('toggle cx=%d cy=%d label="" key=%s img=art/%s_off.png img_on=art/%s_on.png w=%d h=%d ns=0'
                                   % (cxm, cym, key, key, key, pw, ph))
        key, x, y = CHORUS_OFF
        tab, reg, ox, oy, cxm, cym = self.place((x, y), 34, 38)
        pw, ph = round(32 * reg.kx), round(40 * reg.ky)
        rect = (cxm - pw // 2, cym - ph // 2, pw, ph)
        im = self.crop(reg, rect, lambda cv, a, b: button(cv, ox - a, oy - b, 0, 0, 17, 19, 0))
        self.save(im, "chorus_off_off")
        self.save(im, "chorus_off_on")
        self.lines[tab].append('button cx=%d cy=%d label="" key=chorus_off img=art/chorus_off_off.png img_on=art/chorus_off_on.png w=%d h=%d'
                               % (cxm, cym, pw, ph))
        Image.new("RGBA", (4, 4), (0, 0, 0, 0)).save(os.path.join(self.out, "art", "clear.png"))
        out = [HEADER]
        for name, _ in TABS:
            out.append("[tab %s]" % name)
            # later lines sit on top: knobs, then sliders (whose hidden label area reaches into what is below), then the rest
            rank = {"art": 0, "knob": 1, "slider_v": 2}
            out += [shift(l) for l in sorted(self.lines[name], key=lambda l: rank.get(l.split()[0], 3))]
            out.append('qlinks "%s" = %s' % (name, QLINKS[name]))
            out.append("")
        out.append(SETTINGS)
        open(os.path.join(self.out, "layout.conf"), "w").write("\n".join(out))


def preview(out):
    """vst/preview/tabN.png: every control drawn at the parameter's default, the tabs as they sit on the screen."""
    import json
    ps = {p["key"]: p for p in json.load(open(os.path.join(out, "params.json")))["params"]}

    def norm(key):
        p = ps[key]
        if "options" in p:
            return p["options"].index(p["default"]) / max(1, len(p["options"]) - 1)
        return (p["default"] - p["min"]) / (p["max"] - p["min"])

    sk = Skin(out)
    global HANDLE, LED, KNOB
    HANDLE, LED, KNOB = img("slider_handle@2x.png"), img("led_red@2x.png"), img("smallknob@2x.png")
    sw3v, sw3h = img("switch_3way@2x.png"), img("switch_3way_horizontal@2x.png")
    cv = sk.canvas
    for key, x, y, extra in SLIDERS:
        slider(cv, x * 2, y * 2, norm(key), extra)
    hp = [(round(44 - i * 40 / 3), BRIGHT) for i in range(4)]
    slider(cv, HPF[1] * 2, HPF[2] * 2, norm("hpf"), 0, hp)
    for key, x, y in KNOBS:
        knob(cv, x * 2, y * 2, norm(key))
    for key, x, y in SW3V:
        sprite(cv, x * 2, y * 2, sw3v, round(norm(key) * 2))
    for key, x, y in SW3H:
        sprite(cv, x * 2, y * 2, sw3h, round(norm(key) * 2))
    for key, x, y in SW2V:
        sprite(cv, x * 2, y * 2, sw3v, 2 if norm(key) > 0.5 else 0)
    for key, x, y in SW2H:
        sprite(cv, x * 2, y * 2, sw3h, 2 if norm(key) > 0.5 else 0)
    for key, x, y, kind in LEDS:
        button_led(cv, x * 2, y * 2, kind, norm(key) > 0.5)
    button(cv, CHORUS_OFF[1] * 2, CHORUS_OFF[2] * 2, 0, 0, 17, 19, 0)
    os.makedirs(os.path.join(out, "preview"), exist_ok=True)
    for i, (name, regs) in enumerate(TABS, 1):
        bg = Image.new("RGB", (W, H), PAGE)
        for reg in regs:
            bg.paste(cv.resize((reg.w, reg.h), Image.LANCZOS, box=reg.box), (reg.X0, reg.Y0))
        bg.save(os.path.join(out, "preview", "tab%d.png" % i))


def build(out):
    sk = Skin(out)
    sk.build()
    preview(out)
    return sk


if __name__ == "__main__":
    build(os.path.join(HERE, "..", "vst"))

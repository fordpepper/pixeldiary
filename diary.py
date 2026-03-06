#!/usr/bin/env python3
"""
Pixel Diary  -  run with:  python3 diary.py
Uses only tkinter (built into Python 3).
If missing on Ubuntu run:  sudo apt install python3-tk
"""

import tkinter as tk
from tkinter import PhotoImage
import os, sys, calendar
from datetime import date

# ─── Paths ─────────────────────────────────────────────────────────────────────
# When frozen by PyInstaller assets live in sys._MEIPASS.
# diary.txt and start.txt always sit next to the executable.
if getattr(sys, 'frozen', False):
    _BUNDLE_DIR = sys._MEIPASS
    BASE_DIR    = os.path.dirname(sys.executable)
else:
    _BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR    = _BUNDLE_DIR

ASSETS_DIR = os.path.join(_BUNDLE_DIR, 'assets')
DIARY_FILE = os.path.join(BASE_DIR, 'diary.txt')
START_FILE = os.path.join(BASE_DIR, 'start.txt')

# ─── Canvas ────────────────────────────────────────────────────────────────────
CW, CH         = 98, 49
DEFAULT_SCALE  = 8
ICON_W, ICON_H = 12, 7
BG_COLOR       = '#999999'

# ─── Layout ────────────────────────────────────────────────────────────────────
def row_y(r): return 1 + r * 8
def col_x(d): return 1 + d * 13

DATE_X  = 92
DIGIT_Y = [1, 9, 33, 41]

# ─── Picker popup ──────────────────────────────────────────────────────────────
PK_X, PK_Y, PK_W, PK_H = 5, 17, 88, 15
PK_ICON_Y  = 21
PK_X_BTN_X = 9
PK_O_BTN_X = 82
PK_MOOD_X  = [17, 30, 43, 56, 69]


# ══════════════════════════════════════════════════════════════════════════════
#  Data helpers
# ══════════════════════════════════════════════════════════════════════════════

def load_start_date():
    if not os.path.exists(START_FILE):
        return date.today()
    try:
        dd, mm, yy = open(START_FILE).read().strip().split('.')
        return date(2000 + int(yy), int(mm), int(dd))
    except Exception:
        return date.today()

def load_diary():
    if not os.path.exists(DIARY_FILE):
        return ''
    return open(DIARY_FILE).read().strip()

def save_diary(data):
    with open(DIARY_FILE, 'w') as f:
        f.write(data)

def get_mood(data, start, d):
    idx = (d - start).days
    if idx < 0:         return '9'
    if idx < len(data): return data[idx]
    return '9'

def set_mood(data, start, d, mood):
    idx = (d - start).days
    if idx < 0: return data
    lst = list(data)
    while len(lst) <= idx:
        lst.append('9')
    lst[idx] = mood
    return ''.join(lst)


# ══════════════════════════════════════════════════════════════════════════════
#  App
# ══════════════════════════════════════════════════════════════════════════════

class PixelDiary:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Pixel Diary')
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(True, True)
        self.root.minsize(CW, CH)

        self.scale = DEFAULT_SCALE

        self.canvas = tk.Canvas(
            self.root,
            width=CW * self.scale,
            height=CH * self.scale,
            bg=BG_COLOR,
            highlightthickness=0,
            cursor='arrow',
        )
        self.canvas.pack(expand=True, fill='both')

        sprite_names = (
            ['mood1','mood2','mood3','mood4','mood5','mood9','today','O','X']
            + [str(i) for i in range(10)]
        )
        self._raw   = {
            n: PhotoImage(file=os.path.join(ASSETS_DIR, f'{n}.png'))
            for n in sprite_names
        }
        self._cache = {}

        self.start_date = load_start_date()
        self.diary_data = load_diary()
        today           = date.today()
        self.view       = today.replace(day=1)
        self.start_mon  = self.start_date.replace(day=1)

        self.picker_open     = False
        self.picker_selected = None
        self.picker_target   = None

        self.canvas.bind('<Button-1>',   self.on_click)
        self.canvas.bind('<Button-4>',   self.on_scroll_up)
        self.canvas.bind('<Button-5>',   self.on_scroll_down)
        self.canvas.bind('<MouseWheel>', self.on_mousewheel)

        self._resize_job = None
        self.root.bind('<Configure>', self._schedule_resize)

        self.draw()
        self.root.mainloop()

    # ── Sprites ─────────────────────────────────────────────────────────────────

    def sprite(self, name):
        key = (name, self.scale)
        if key not in self._cache:
            self._cache[key] = self._raw[name].zoom(self.scale)
        return self._cache[key]

    # ── Coordinates ─────────────────────────────────────────────────────────────

    def _get_scale(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 2 or h < 2:
            return DEFAULT_SCALE
        return max(1, min(w // CW, h // CH))

    def _snap_window(self, s):
        self.root.geometry(f'{CW * s}x{CH * s}')

    def screen_to_canvas(self, sx, sy):
        s  = self.scale
        cx = sx // s
        cy = sy // s
        if 0 <= cx < CW and 0 <= cy < CH:
            return cx, cy
        return None, None

    # ── Drawing ─────────────────────────────────────────────────────────────────

    def draw(self):
        s = self._get_scale()
        c = self.canvas
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 2 or h < 2:
            self.root.after(20, self.draw)
            return

        if s != self.scale or w != CW * s or h != CH * s:
            self.scale = s
            self._snap_window(s)
            return

        c.delete('all')
        c.create_rectangle(0, 0, CW*s, CH*s, fill=BG_COLOR, outline='')

        def blit(name, px, py):
            c.create_image(px*s, py*s, image=self.sprite(name), anchor='nw')

        today     = date.today()
        year, mon = self.view.year, self.view.month

        # Date digits
        mm = f'{mon:02d}'
        yy = f'{year % 100:02d}'
        for ch, dy in zip(mm[0] + mm[1] + yy[0] + yy[1], DIGIT_Y):
            blit(ch, DATE_X, dy)

        # Mood grid
        first_dow   = date(year, mon, 1).weekday()
        days_in_mon = calendar.monthrange(year, mon)[1]

        for day_num in range(1, days_in_mon + 1):
            d      = date(year, mon, day_num)
            offset = (day_num - 1) + first_dow
            ri     = offset // 7
            ci     = offset % 7
            px     = col_x(ci)
            py     = row_y(ri)

            mood = get_mood(self.diary_data, self.start_date, d)
            blit(f'mood{mood}', px, py)

            if d == today:
                blit('today', px, py)

        # Picker popup
        if self.picker_open:
            c.create_rectangle(
                PK_X*s,         PK_Y*s,
                (PK_X+PK_W)*s,  (PK_Y+PK_H)*s,
                fill='black', outline='')
            c.create_rectangle(
                (PK_X+1)*s,       (PK_Y+1)*s,
                (PK_X+PK_W-1)*s,  (PK_Y+PK_H-1)*s,
                fill='white', outline='')
            c.create_rectangle(
                (PK_X+2)*s,       (PK_Y+2)*s,
                (PK_X+PK_W-2)*s,  (PK_Y+PK_H-2)*s,
                fill='black', outline='')
            c.create_rectangle(
                (PK_X+3)*s,       (PK_Y+3)*s,
                (PK_X+PK_W-3)*s,  (PK_Y+PK_H-3)*s,
                fill=BG_COLOR, outline='')

            blit('X', PK_X_BTN_X, PK_ICON_Y)
            blit('O', PK_O_BTN_X, PK_ICON_Y)

            for i, ax in enumerate(PK_MOOD_X):
                blit(f'mood{i+1}', ax, PK_ICON_Y)
                if self.picker_selected == str(i + 1):
                    blit('today', ax, PK_ICON_Y)

    # ── Resize ──────────────────────────────────────────────────────────────────

    def _schedule_resize(self, event=None):
        if self._resize_job:
            self.root.after_cancel(self._resize_job)
        self._resize_job = self.root.after(40, self.draw)

    # ── Click ───────────────────────────────────────────────────────────────────

    def on_click(self, event):
        cx, cy = self.screen_to_canvas(event.x, event.y)
        if cx is None:
            return

        if self.picker_open:
            hit = self._picker_hit(cx, cy)
            if hit in ('outside', 'x_btn'):
                self.picker_open     = False
                self.picker_selected = None
                self.picker_target   = None
            elif hit == 'o_btn':
                if self.picker_selected and self.picker_target:
                    self.diary_data = set_mood(
                        self.diary_data, self.start_date,
                        self.picker_target, self.picker_selected)
                    save_diary(self.diary_data)
                self.picker_open     = False
                self.picker_selected = None
                self.picker_target   = None
            elif hit in ('1', '2', '3', '4', '5'):
                self.picker_selected = hit
        else:
            today   = date.today()
            clicked = self._day_at(cx, cy, self.view.year, self.view.month, today)
            if clicked:
                self.picker_open   = True
                self.picker_target = clicked
                existing = get_mood(self.diary_data, self.start_date, clicked)
                self.picker_selected = existing if existing != '9' else None

        self.draw()

    # ── Scroll ──────────────────────────────────────────────────────────────────

    def on_scroll_up(self, event=None):
        if self.picker_open: return
        m, y = self.view.month - 1, self.view.year
        if m == 0: m, y = 12, y - 1
        candidate = date(y, m, 1)
        if candidate >= self.start_mon:
            self.view = candidate
            self.draw()

    def on_scroll_down(self, event=None):
        if self.picker_open: return
        m, y = self.view.month + 1, self.view.year
        if m == 13: m, y = 1, y + 1
        candidate = date(y, m, 1)
        if candidate <= date.today().replace(day=1):
            self.view = candidate
            self.draw()

    def on_mousewheel(self, event):
        if event.delta > 0: self.on_scroll_up()
        else:                self.on_scroll_down()

    # ── Hit testing ─────────────────────────────────────────────────────────────

    def _picker_hit(self, cx, cy):
        if not (PK_X <= cx < PK_X + PK_W and PK_Y <= cy < PK_Y + PK_H):
            return 'outside'
        if PK_X_BTN_X <= cx < PK_X_BTN_X+7 and PK_ICON_Y <= cy < PK_ICON_Y+7:
            return 'x_btn'
        if PK_O_BTN_X <= cx < PK_O_BTN_X+7 and PK_ICON_Y <= cy < PK_ICON_Y+7:
            return 'o_btn'
        for i, ax in enumerate(PK_MOOD_X):
            if ax <= cx < ax + ICON_W and PK_ICON_Y <= cy < PK_ICON_Y + ICON_H:
                return str(i + 1)
        return 'other'

    def _day_at(self, cx, cy, year, mon, today):
        first_dow   = date(year, mon, 1).weekday()
        days_in_mon = calendar.monthrange(year, mon)[1]
        for day_num in range(1, days_in_mon + 1):
            d = date(year, mon, day_num)
            if d > today: continue
            offset = (day_num - 1) + first_dow
            ri     = offset // 7
            ci     = offset % 7
            px     = col_x(ci)
            py     = row_y(ri)
            if px <= cx < px + ICON_W and py <= cy < py + ICON_H:
                return d
        return None


if __name__ == '__main__':
    PixelDiary()

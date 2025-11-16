"""
Directional / Spatial Stroop — Reverse Arrow version (with 4 directions).

Updates:
 - Directions now include LEFT, RIGHT, UP, DOWN.
 - Arrow always points to the OPPOSITE direction of the correct answer.
 - Four response buttons placed on ONE single horizontal line.
 - Stimulus duration changed to EXACTLY 1.0 second.
"""

import pygame
import random
import time
import sys

# -------------------- Config --------------------
FPS = 60
SCREEN_SIZE = (1000, 650)
TRIALS = 40
STIMULUS_DURATION = 1.0     # <-- Updated from 1.2 to 1.0 sec
FEEDBACK_DURATION = 0.6
FIXATION_DURATION = 0.5
SHOW_ARROW = True
FONT_NAME = None

# Colors
BG_TOP = (16, 24, 40)
BG_BOTTOM = (12, 78, 120)
CARD_COLOR = (240, 248, 255)
TEXT_COLOR = (20, 20, 30)
ACCENT = (255, 180, 85)
CORRECT_GREEN = (20, 160, 80)
WRONG_RED = (220, 60, 60)
BUTTON_COLOR = (30, 40, 60)
BUTTON_HOVER = (50, 70, 100)

# ------------------------------------------------

pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption("Reverse Arrow Stroop — 4-Direction Version")
clock = pygame.time.Clock()

# Fonts
def font(size, bold=False):
    return pygame.font.SysFont(FONT_NAME, size, bold=bold)

TITLE_FONT = font(36, True)
SMALL_FONT = font(22)
BUTTON_FONT = font(28, True)


# ---------------- BUTTON CLASS ----------------
class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.hot = False

    def draw(self, surf):
        color = BUTTON_HOVER if self.hot else BUTTON_COLOR
        pygame.draw.rect(surf, color, self.rect, border_radius=12)
        inner = self.rect.inflate(-6, -6)
        pygame.draw.rect(surf, CARD_COLOR, inner, border_radius=10)
        txt = BUTTON_FONT.render(self.text, True, TEXT_COLOR)
        surf.blit(txt, txt.get_rect(center=self.rect.center))

    def update(self, mpos):
        self.hot = self.rect.collidepoint(mpos)

    def clicked(self, mpos):
        return self.rect.collidepoint(mpos)


# ------------- DRAW GRADIENT BG ---------------
def draw_gradient(surf, top_color, bottom_color):
    w, h = surf.get_size()
    for y in range(h):
        t = y / (h - 1)
        color = (
            int(top_color[0] * (1 - t) + bottom_color[0] * t),
            int(top_color[1] * (1 - t) + bottom_color[1] * t),
            int(top_color[2] * (1 - t) + bottom_color[2] * t),
        )
        pygame.draw.line(surf, color, (0, y), (w, y))


# ------------- DRAW ARROW FOR 4 DIRECTIONS -------------
def draw_arrow(surface, center, size, direction, color=TEXT_COLOR, outline=True):
    cx, cy = center
    w = size * 1.6
    h = size

    if direction == "RIGHT":
        points = [
            (cx - w/2, cy - h/2),
            (cx, cy - h/2),
            (cx + w/2, cy),
            (cx, cy + h/2),
            (cx - w/2, cy + h/2),
        ]

    elif direction == "LEFT":
        points = [
            (cx + w/2, cy - h/2),
            (cx, cy - h/2),
            (cx - w/2, cy),
            (cx, cy + h/2),
            (cx + w/2, cy + h/2),
        ]

    elif direction == "UP":
        points = [
            (cx - h/2, cy + w/2),
            (cx - h/2, cy),
            (cx, cy - w/2),
            (cx + h/2, cy),
            (cx + h/2, cy + w/2),
        ]

    elif direction == "DOWN":
        points = [
            (cx - h/2, cy - w/2),
            (cx - h/2, cy),
            (cx, cy + w/2),
            (cx + h/2, cy),
            (cx + h/2, cy - w/2),
        ]

    pygame.draw.polygon(surface, color, points)
    if outline:
        pygame.draw.polygon(surface, (0,0,0), points, 2)


# Opposite direction
def opposite_dir(direction):
    return {
        "LEFT": "RIGHT",
        "RIGHT": "LEFT",
        "UP": "DOWN",
        "DOWN": "UP"
    }[direction]


# Make trials with 4 directions
def make_trials(n):
    options = ["LEFT", "RIGHT", "UP", "DOWN"]
    trials = []
    for _ in range(n):
        correct = random.choice(options)
        displayed = opposite_dir(correct)
        trials.append((correct, displayed))
    random.shuffle(trials)
    return trials


# ------------------ FEEDBACK OVERLAY -------------------
def draw_feedback(surf, text, correct):
    overlay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    overlay.fill((0,0,0,110))
    surf.blit(overlay, (0,0))
    big = TITLE_FONT.render(text, True, CORRECT_GREEN if correct else WRONG_RED)
    surf.blit(big, big.get_rect(center=(SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2)))


# ---------------- CREATE 4 BUTTONS IN ONE LINE ----------------
button_y = SCREEN_SIZE[1] - 110
gap = 40
btn_w = 150
btn_h = 70
start_x = (SCREEN_SIZE[0] - (btn_w * 4 + gap * 3)) // 2

left_button  = Button((start_x,               button_y, btn_w, btn_h), "LEFT")
right_button = Button((start_x + (btn_w+gap), button_y, btn_w, btn_h), "RIGHT")
up_button    = Button((start_x + 2*(btn_w+gap), button_y, btn_w, btn_h), "UP")
down_button  = Button((start_x + 3*(btn_w+gap), button_y, btn_h, btn_h), "DOWN")


# ---------------- STATE VARIABLES ----------------
trials = make_trials(TRIALS)
trial_index = 0
score = 0
results = []
state = "start"
state_time = 0.0
stim_onset = None


# ---------------- HELPER: AVG RT ----------------
def calc_avg_rt():
    rts = [r['rt'] for r in results if r['correct'] and r['rt']]
    return sum(rts) / len(rts) if rts else 0.0


# ---------------- DRAW START SCREEN ----------------
def draw_start(surf):
    draw_gradient(surf, BG_TOP, BG_BOTTOM)
    title = TITLE_FONT.render("Reverse Arrow Stroop — 4 Directions", True, CARD_COLOR)
    subtitle = SMALL_FONT.render("Arrow always points OPPOSITE of the correct direction.", True, CARD_COLOR)
    surf.blit(title, title.get_rect(center=(SCREEN_SIZE[0]//2, 120)))
    surf.blit(subtitle, subtitle.get_rect(center=(SCREEN_SIZE[0]//2, 170)))
    card = pygame.Rect(120, 220, SCREEN_SIZE[0]-240, 260)
    pygame.draw.rect(surf, CARD_COLOR, card, border_radius=16)
    lines = [
        f"Trials: {TRIALS}    Stimulus Time: {STIMULUS_DURATION}s",
        "Directions: LEFT, RIGHT, UP, DOWN.",
        "Arrow shows the OPPOSITE direction — respond to the TRUE hidden direction.",
        "Press SPACE or click anywhere to start."
    ]
    for i, line in enumerate(lines):
        surf.blit(SMALL_FONT.render(line, True, TEXT_COLOR), (card.x + 28, card.y + 28 + i * 42))


# ---------------- DRAW PROGRESS HUD ----------------
def draw_hud(surf, idx, total, score):
    bar_w = SCREEN_SIZE[0] - 260
    bar_h = 14
    x = 130
    y = 40
    bg = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
    bg.fill((255,255,255,30))
    surf.blit(bg, (x, y))
    fill = int(bar_w * (idx / total))
    pygame.draw.rect(surf, ACCENT, (x, y, fill, bar_h), border_radius=8)
    txt = SMALL_FONT.render(f"Trial {idx}/{total}    Score: {score}", True, CARD_COLOR)
    surf.blit(txt, (x, y - 28))


# ---------------- DRAW FIXATION ----------------
def draw_fixation(surf):
    draw_gradient(surf, BG_TOP, BG_BOTTOM)
    draw_hud(surf, trial_index + 1, TRIALS, score)
    cx, cy = SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2
    pygame.draw.line(surf, CARD_COLOR, (cx-14, cy), (cx+14, cy), 5)
    pygame.draw.line(surf, CARD_COLOR, (cx, cy-14), (cx, cy+14), 5)


# ---------------- DRAW STIMULUS ----------------
def draw_stimulus_screen(surf, displayed_arrow, time_left):
    draw_gradient(surf, BG_TOP, BG_BOTTOM)
    draw_hud(surf, trial_index + 1, TRIALS, score)

    card = pygame.Rect(140, 120, SCREEN_SIZE[0]-280, 360)
    pygame.draw.rect(surf, CARD_COLOR, card, border_radius=18)

    if SHOW_ARROW:
        draw_arrow(surf, (SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2), 90, displayed_arrow, color=(60,60,80))

    # update and draw buttons
    mpos = pygame.mouse.get_pos()
    for b in [left_button, right_button, up_button, down_button]:
        b.update(mpos)
        b.draw(surf)

    # timer
    ttxt = SMALL_FONT.render(f"{time_left:.2f}s left", True, TEXT_COLOR)
    surf.blit(ttxt, (SCREEN_SIZE[0]//2 - 40, SCREEN_SIZE[1]-40))


# ---------------- DRAW FEEDBACK ----------------
def draw_feedback_screen(surf, displayed_arrow, last_correct):
    draw_gradient(surf, BG_TOP, BG_BOTTOM)
    draw_hud(surf, trial_index + 1, TRIALS, score)

    card = pygame.Rect(140, 120, SCREEN_SIZE[0]-280, 360)
    pygame.draw.rect(surf, CARD_COLOR, card, border_radius=18)

    draw_arrow(surf, (SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2), 90, displayed_arrow, color=(140,140,150), outline=False)
    draw_feedback(surf, "Correct!" if last_correct else "Wrong!", last_correct)


# ---------------- MAIN LOOP ----------------
running = True
while running:
    dt = clock.tick(FPS) / 1000.0
    t = time.time()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # ---------- START SCREEN ----------
        if state == "start":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                trial_index = 0
                score = 0
                results = []
                trials = make_trials(TRIALS)
                state = "fixation"
                state_time = t
            if event.type == pygame.MOUSEBUTTONDOWN:
                trial_index = 0
                score = 0
                results = []
                trials = make_trials(TRIALS)
                state = "fixation"
                state_time = t

        # ---------- FIXATION ----------
        elif state == "fixation":
            if t - state_time >= FIXATION_DURATION:
                state = "stimulus"
                state_time = t
                stim_onset = t
                current_correct, current_display = trials[trial_index]

        # ---------- STIMULUS ----------
        elif state == "stimulus":
            response = None

            # keyboard
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:  response = "LEFT"
                if event.key == pygame.K_RIGHT: response = "RIGHT"
                if event.key == pygame.K_UP:    response = "UP"
                if event.key == pygame.K_DOWN:  response = "DOWN"

            # mouse
            if event.type == pygame.MOUSEBUTTONDOWN:
                m = event.pos
                if left_button.clicked(m):  response = "LEFT"
                if right_button.clicked(m): response = "RIGHT"
                if up_button.clicked(m):    response = "UP"
                if down_button.clicked(m):  response = "DOWN"

            # if player responded
            if response:
                rt = t - stim_onset
                correct = (response == current_correct)
                if correct: score += 1
                results.append({
                    'trial': trial_index+1,
                    'correct_direction': current_correct,
                    'displayed_arrow': current_display,
                    'response': response,
                    'correct': correct,
                    'rt': rt
                })
                state = "feedback"
                state_time = t

            # timeout
            if t - stim_onset >= STIMULUS_DURATION and state == "stimulus":
                results.append({
                    'trial': trial_index+1,
                    'correct_direction': current_correct,
                    'displayed_arrow': current_display,
                    'response': None,
                    'correct': False,
                    'rt': None
                })
                state = "feedback"
                state_time = t

        # ---------- FEEDBACK ----------
        elif state == "feedback":
            if t - state_time >= FEEDBACK_DURATION:
                trial_index += 1
                state = "finished" if trial_index >= TRIALS else "fixation"
                state_time = t

        # ---------- FINISHED ----------
        elif state == "finished":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    state = "start"
                if event.key == pygame.K_q:
                    running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                state = "start"

    # -------- DRAW SCREEN --------
    if state == "start":
        draw_start(screen)

    elif state == "fixation":
        draw_fixation(screen)

    elif state == "stimulus":
        elapsed = t - stim_onset
        time_left = max(0.0, STIMULUS_DURATION - elapsed)
        draw_stimulus_screen(screen, current_display, time_left)

    elif state == "feedback":
        last = results[-1]
        draw_feedback_screen(screen, last['displayed_arrow'], last['correct'])

    elif state == "finished":
        draw_gradient(screen, BG_TOP, BG_BOTTOM)
        title = TITLE_FONT.render("Session Complete!", True, CARD_COLOR)
        screen.blit(title, title.get_rect(center=(SCREEN_SIZE[0]//2, 120)))
        score_txt = SMALL_FONT.render(f"Score: {score}/{TRIALS}", True, CARD_COLOR)
        screen.blit(score_txt, score_txt.get_rect(center=(SCREEN_SIZE[0]//2, 180)))
        avg = calc_avg_rt()
        line = SMALL_FONT.render(f"Average RT: {avg:.3f}s", True, CARD_COLOR)
        screen.blit(line, (SCREEN_SIZE[0]//2 - 140, 240))
        tip = SMALL_FONT.render("Press R to Restart or Q to Quit", True, CARD_COLOR)
        screen.blit(tip, (SCREEN_SIZE[0]//2 - 140, 280))

    pygame.display.flip()

pygame.quit()
sys.exit()

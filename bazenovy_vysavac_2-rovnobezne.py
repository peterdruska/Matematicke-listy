import pygame
import random
import math
import time
from collections import defaultdict

# ---------------- PARAMETRE SIMULÁCIE ----------------
REAL_POOL_WIDTH_M = 20
REAL_POOL_HEIGHT_M = 15
PIXEL_WIDTH = 800
PIXEL_HEIGHT = 600
METER_TO_PIXEL = PIXEL_WIDTH / REAL_POOL_WIDTH_M  # 40 px/m

VACUUM_WIDTH_M = 0.5
VACUUM_WIDTH_PX = VACUUM_WIDTH_M * METER_TO_PIXEL

SPEED_M_S = 0.2
DEFAULT_SIMULATED_SECONDS = 2 * 60 * 60     # 2 hodiny
DEFAULT_SIM_DURATION_REALTIME = 2           # 2 sekundy

STEP_DISTANCE_M = SPEED_M_S * 1
STEP_DISTANCE_PX = STEP_DISTANCE_M * METER_TO_PIXEL

GRID_SIZE_PX = 40  # veľkosť bunky mriežky (1 meter)
GRID_COLS = PIXEL_WIDTH // GRID_SIZE_PX
GRID_ROWS = PIXEL_HEIGHT // GRID_SIZE_PX

PRUNE_RADIUS = 10  # rozšírený polomer na zistenie "blízkosti" pre existujúce prieniky

# -------------------- INIT ---------------------------
pygame.init()
screen = pygame.display.set_mode((PIXEL_WIDTH, PIXEL_HEIGHT + 100))
pygame.display.set_caption("Bazénový vysávač – s mriežkou")
clock = pygame.time.Clock()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE  = (0, 128, 255)
LINE_COLOR = (255, 0, 0, 50)
RED = (255, 0, 0)

FONT = pygame.font.SysFont(None, 24)
line_surface = pygame.Surface((PIXEL_WIDTH, PIXEL_HEIGHT), pygame.SRCALPHA)
RECT = pygame.Rect(0, 0, PIXEL_WIDTH, PIXEL_HEIGHT)

input_active = False
input_text = ""
input_box = pygame.Rect(10, PIXEL_HEIGHT + 10, 300, 32)
info_text = "Zadaj: cas_prace_vysavaca_hodiny,cas_beh_simulacie_sekundy"

# ---------------- POMOCNÉ FUNKCIE --------------------
def segment_intersect(p1, p2, q1, q2):
    def ccw(a, b, c):
        return (c[1]-a[1])*(b[0]-a[0]) > (b[1]-a[1])*(c[0]-a[0])
    return (ccw(p1, q1, q2) != ccw(p2, q1, q2)) and (ccw(p1, p2, q1) != ccw(p1, p2, q2))

def grid_coords(x, y):
    return int(x // GRID_SIZE_PX), int(y // GRID_SIZE_PX)

# ---------------- SIMULÁCIA --------------------------
def run_simulation(sim_seconds, sim_duration):
    total_steps = int(sim_seconds)
    # Začiatočná pozícia v ľavom hornom rohu bazéna
    x, y = 0, 0
    dx, dy = 1, 0  # najskôr pôjde vodorovne doprava (pozri poznámky nižšie)
    step_px = STEP_DISTANCE_PX

    trajectory = [(x, y)]
    intersections = defaultdict(int)
    grid = defaultdict(list)
    line_surface.fill((0, 0, 0, 0))
    drawn_steps = 0
    simulation_done = False
    start_time = time.time()

    total_distance_px = 0.0

    direction_along_width = True  # začína ísť rovnobežne s kratšou stranou (šírka bazéna)
    vacuum_width_px = VACUUM_WIDTH_PX

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

        if not simulation_done:
            elapsed = time.time() - start_time
            progress_ratio = min(1.0, elapsed / sim_duration)
            target_steps = int(progress_ratio * total_steps)

            while drawn_steps < target_steps:
                prev_x, prev_y = x, y

                # Posun o krok
                x += dx * step_px
                y += dy * step_px

                # Kontrola hraníc
                if x < 0 or x > PIXEL_WIDTH or y < 0 or y > PIXEL_HEIGHT:
                    # Ak dosiahne koniec riadku (alebo steny bazéna), posuň sa o šírku vysávača kolmo na aktuálny smer
                    if direction_along_width:
                        # Ak chodil po šírke bazéna (horizontálne), posuň sa vertikálne dole
                        y += vacuum_width_px
                        # otoč smer o 180°, aby išiel naspäť (doľava)
                        dx = -dx
                        dy = 0
                    else:
                        # Ak chodil po výške bazéna (vertikálne), posuň sa horizontálne doprava
                        x += vacuum_width_px
                        # otoč smer o 180°, aby išiel naspäť (hore/dole)
                        dx = 0
                        dy = -dy

                    # Ak vysávač dosiahol koniec povrchu v tomto smere, prepnúť smer chodenia
                    if direction_along_width and y > PIXEL_HEIGHT:
                        # prepni na chodenie po výške
                        direction_along_width = False
                        x, y = 0, 0
                        dx, dy = 0, 1
                    elif not direction_along_width and x > PIXEL_WIDTH:
                        # prepni na chodenie po šírke
                        direction_along_width = True
                        x, y = 0, 0
                        dx, dy = 1, 0

                    # Aktualizuj pozíciu v rámci hraníc
                    x = max(0, min(x, PIXEL_WIDTH))
                    y = max(0, min(y, PIXEL_HEIGHT))

                new_point = (x, y)
                trajectory.append(new_point)
                pygame.draw.line(line_surface, LINE_COLOR, (prev_x, prev_y), new_point)

                total_distance_px += math.hypot(x - prev_x, y - prev_y)

                gx, gy = grid_coords(x, y)
                current_cell = (gx, gy)

                # Prieniky segmentov + blízkosť existujúcich prienikov
                found = False
                for dxg in [-1, 0, 1]:
                    for dyg in [-1, 0, 1]:
                        neighbor = (gx + dxg, gy + dyg)
                        for seg in grid.get(neighbor, []):
                            A1, A2 = seg
                            if segment_intersect((prev_x, prev_y), new_point, A1, A2):
                                px = int((prev_x + x + A1[0] + A2[0]) / 4)
                                py = int((prev_y + y + A1[1] + A2[1]) / 4)
                                intersections[(px, py)] += 1
                                found = True

                if not found:
                    for pos in list(intersections.keys()):
                        dxp = pos[0] - x
                        dyp = pos[1] - y
                        if dxp*dxp + dyp*dyp <= PRUNE_RADIUS * PRUNE_RADIUS:
                            intersections[pos] += 1
                            found = True
                            break

                if not found:
                    grid[current_cell].append(((prev_x, prev_y), new_point))

                drawn_steps += 1

            if drawn_steps >= total_steps:
                simulation_done = True

        screen.fill(BLACK)
        pygame.draw.rect(screen, WHITE, RECT)
        screen.blit(line_surface, (0, 0))

        if not simulation_done:
            pygame.draw.circle(screen, BLUE, (int(x), int(y)), 6)

        for pos, count in intersections.items():
            radius = 3 + count
            pygame.draw.circle(screen, RED, pos, radius, 0)

        # Vypíš dĺžku dráhy v metroch
        distance_m = total_distance_px / METER_TO_PIXEL
        distance_text = FONT.render(f"Dĺžka dráhy: {distance_m:.1f} m", True, WHITE)
        screen.blit(distance_text, (320, PIXEL_HEIGHT + 20))

        pygame.display.flip()
        clock.tick(60)

        if simulation_done:
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return "quit"
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                        return "done"
                pygame.time.wait(100)

# ---------------- Hlavný cyklus ----------------------
running = True
state = "input"
sim_seconds = DEFAULT_SIMULATED_SECONDS
sim_duration = DEFAULT_SIM_DURATION_REALTIME

while running:
    if state == "input":
        screen.fill(BLACK)
        pygame.draw.rect(screen, (255, 255, 255), input_box, 2)
        txt_surface = FONT.render(input_text, True, WHITE)
        info_surface = FONT.render(info_text, True, WHITE)
        screen.blit(txt_surface, (input_box.x+5, input_box.y+5))
        screen.blit(info_surface, (10, PIXEL_HEIGHT + 50))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    try:
                        h, s = input_text.strip().split(",")
                        sim_seconds = int(float(h) * 3600)
                        sim_duration = int(float(s))
                        input_text = ""
                        state = "sim"
                    except:
                        input_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode

    elif state == "sim":
        result = run_simulation(sim_seconds, sim_duration)
        if result == "quit":
            running = False
        elif result == "done":
            state = "input"

pygame.quit()

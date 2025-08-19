import pygame
import sys
import os
import time
import random


# --- Initialization ---
pygame.init()

# --- DYNAMIC SCREEN SCALING ---
BASE_WIDTH, BASE_HEIGHT = 600, 700
try:
    info = pygame.display.Info()
    real_screen_width, real_screen_height = info.current_w, info.current_h
except pygame.error:
    real_screen_width, real_screen_height = 800, 1200 # Fallback

scale_w = real_screen_width / BASE_WIDTH; scale_h = real_screen_height / BASE_HEIGHT
scale_factor = min(scale_w, scale_h)
SCALED_WIDTH = int(BASE_WIDTH * scale_factor); SCALED_HEIGHT = int(BASE_HEIGHT * scale_factor)

screen = pygame.display.set_mode((SCALED_WIDTH, SCALED_HEIGHT))
virtual_screen = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
pygame.display.set_caption("Ludo")

# --- PERFECTED COORDINATES & PATH LOGIC ---
HOME_POSITIONS = {
    "red":    [(85, 85), (155, 85), (85, 155), (155, 155)],
    "green":  [(445, 85), (515, 85), (445, 155), (515, 155)],
    "blue":   [(85, 445), (155, 445), (85, 515), (155, 515)],
    "yellow": [(445, 445), (515, 445), (445, 515), (515, 515)]
}
MAIN_PATH = [
    (60, 260), (100, 260), (140, 260), (180, 260), (220, 260), (260, 220), (260, 180),
    (260, 140), (260, 100), (260, 60), (260, 20), (300, 20), (340, 20), (340, 60),
    (340, 100), (340, 140), (340, 180), (340, 220), (380, 260), (420, 260), (460, 260),
    (500, 260), (540, 260), (580, 260), (580, 300), (580, 340), (540, 340), (500, 340),
    (460, 340), (420, 340), (380, 340), (340, 380), (340, 420), (340, 460), (340, 500),
    (340, 540), (340, 580), (300, 580), (260, 580), (260, 540), (260, 500), (260, 460),
    (260, 420), (260, 380), (220, 340), (180, 340), (140, 340), (100, 340), (60, 340),
    (20, 340), (20, 300)
]
HOME_PATH = {
    "red":    [(60, 300), (100, 300), (140, 300), (180, 300), (220, 300), (260, 300)],
    "green":  [(300, 60), (300, 100), (300, 140), (300, 180), (300, 220), (300, 260)],
    "yellow":   [(540, 300), (500, 300), (460, 300), (420, 300), (380, 300), (340, 300)],
    "blue": [(300, 540), (300, 500), (300, 460), (300, 420), (300, 380), (300, 340)]
}
PATH_START_INDICES = {"red": 0, "green": 13, "yellow": 26, "blue": 39}
SAFE_SQUARES = [MAIN_PATH[0], MAIN_PATH[8], MAIN_PATH[13], MAIN_PATH[21], MAIN_PATH[26], MAIN_PATH[34], MAIN_PATH[39], MAIN_PATH[47]]

# --- Asset Loading and Scaling ---
script_dir = os.path.dirname(os.path.abspath(__file__)); assets_dir = os.path.join(script_dir, 'assets')
try:
    board_img = pygame.transform.scale(pygame.image.load(os.path.join(assets_dir, 'ludo_board.png')), (600, 600))
    dice_images = [pygame.transform.scale(pygame.image.load(os.path.join(assets_dir, f'dice{i}.png')), (64, 64)) for i in range(1, 7)]
    pawn_images = { "red": pygame.transform.scale(pygame.image.load(os.path.join(assets_dir, 'red_pawn.png')), (34, 34)), "green": pygame.transform.scale(pygame.image.load(os.path.join(assets_dir, 'green_pawn.png')), (34, 34)), "yellow": pygame.transform.scale(pygame.image.load(os.path.join(assets_dir, 'yellow_pawn.png')), (34, 34)), "blue": pygame.transform.scale(pygame.image.load(os.path.join(assets_dir, 'blue_pawn.png')), (34, 34)) }
except Exception as e:
    print(f"Error loading assets: {e}. Check 'assets' folder."); sys.exit()

# --- Colors and Fonts ---
WHITE=(255,255,255); BLACK=(0,0,0); GREY=(220,220,220); YELLOW_HIGHLIGHT=(255,255,0,150)
PLAYER_COLORS = {"red":(215,0,0), "green":(0,165,0), "yellow":(225,205,0), "blue":(0,0,225)}
font = pygame.font.Font(None, 40); small_font = pygame.font.Font(None, 32)

# --- Game State ---
game_state="menu"; num_players=0; players_setup=[]; current_player_index=0; dice_value=0
winner=None; turn_state="roll"; movable_pawns=[]; pawns={}; message=""

def reset_game(players_count):
    global game_state, num_players, players_setup, current_player_index, dice_value, winner, turn_state, pawns, message
    game_state = "playing"; num_players = players_count
    if num_players == 2: players_setup = ["red", "yellow"]
    else: players_setup = ["red", "green", "yellow", "blue"]
    current_player_index=0; dice_value=0; winner=None; turn_state="roll"
    message = f"{players_setup[0].title()}'s turn. Roll the dice!"
    pawns = {color: [[0, -1] for _ in range(4)] for color in ["red", "green", "yellow", "blue"]}

def get_pawn_screen_pos(color, pawn_index):
    state, path_idx = pawns[color][pawn_index]
    if state == 0: return HOME_POSITIONS[color][pawn_index]
    elif state == 1:
        if path_idx >= 52:
            home_run_idx = path_idx - 52
            if home_run_idx < len(HOME_PATH[color]): return HOME_PATH[color][home_run_idx]
        else:
            entry_idx = PATH_START_INDICES[color]; actual_path_index = (entry_idx + path_idx) % 52
            return MAIN_PATH[actual_path_index]
    return None

def draw_text(text, font, color, surface, center_pos):
    text_obj = font.render(text, True, color); text_rect = text_obj.get_rect(center=center_pos)
    surface.blit(text_obj, text_rect)

def draw_all():
    virtual_screen.fill((240, 240, 240))
    if game_state == "menu":
        draw_text("LUDO", pygame.font.Font(None, 100), BLACK, virtual_screen, (BASE_WIDTH // 2, 150))
        btn_2p = pygame.Rect(BASE_WIDTH//2-125, 280, 250, 60); btn_4p = pygame.Rect(BASE_WIDTH//2-125, 360, 250, 60)
        pygame.draw.rect(virtual_screen, PLAYER_COLORS["red"], btn_2p, border_radius=15); draw_text("2 Players", font, BLACK, virtual_screen, btn_2p.center)
        pygame.draw.rect(virtual_screen, PLAYER_COLORS["yellow"], btn_4p, border_radius=15); draw_text("4 Players", font, BLACK, virtual_screen, btn_4p.center)
    elif game_state == "playing":
        virtual_screen.blit(board_img, (0, 0))
        for color in players_setup:
            for i in range(4):
                pos = get_pawn_screen_pos(color, i)
                if pos: pawn_img=pawn_images[color]; virtual_screen.blit(pawn_img, (pos[0]-17, pos[1]-17))
        highlight_movable_pawns(); draw_ui()
    elif game_state == "game_over":
        virtual_screen.blit(board_img, (0, 0))
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)); virtual_screen.blit(overlay, (0,0))
        winner_color = PLAYER_COLORS.get(winner, BLACK)
        draw_text(f"{winner.title()} Wins!", pygame.font.Font(None, 90), winner_color, virtual_screen, (BASE_WIDTH//2, BASE_HEIGHT//2-50))
        draw_text("Click to return to menu", font, WHITE, virtual_screen, (BASE_WIDTH//2, BASE_HEIGHT//2+50))

    scaled_surface = pygame.transform.scale(virtual_screen, (SCALED_WIDTH, SCALED_HEIGHT))
    screen.blit(scaled_surface, (0, 0)); pygame.display.flip()

def draw_ui():
    pygame.draw.rect(virtual_screen, GREY, (0, 600, 600, 100))
    current_player_color_name = players_setup[current_player_index]
    draw_text("Turn:", small_font, BLACK, virtual_screen, (70, 625))
    pygame.draw.circle(virtual_screen, PLAYER_COLORS[current_player_color_name], (70, 665), 25)
    dice_rect = pygame.Rect(268, 615, 64, 64)
    if dice_value > 0: virtual_screen.blit(dice_images[dice_value - 1], dice_rect.topleft)
    else: pygame.draw.rect(virtual_screen, (200,200,200), dice_rect, border_radius=10)
    draw_text(message, small_font, BLACK, virtual_screen, (470, 650))

def highlight_movable_pawns():
    if turn_state == "move":
        for pawn_index in movable_pawns:
            color = players_setup[current_player_index]
            pos = get_pawn_screen_pos(color, pawn_index)
            if pos:
                s = pygame.Surface((44, 44), pygame.SRCALPHA)
                pygame.draw.circle(s, YELLOW_HIGHLIGHT, (22, 22), 22); virtual_screen.blit(s, (pos[0] - 22, pos[1] - 22))

def find_movable_pawns():
    global movable_pawns; movable_pawns = []
    color = players_setup[current_player_index]
    for i, (state, path_idx) in enumerate(pawns[color]):
        if state == 0 and dice_value == 6: movable_pawns.append(i)
        elif state == 1 and path_idx + dice_value < 58: movable_pawns.append(i)

def next_turn():
    global current_player_index, turn_state, dice_value, message
    if dice_value != 6: current_player_index = (current_player_index + 1) % len(players_setup)
    turn_state = "roll"; dice_value = 0
    message = f"{players_setup[current_player_index].title()}'s turn. Roll!"

def check_for_capture(move_color, move_pawn_idx):
    final_pos = get_pawn_screen_pos(move_color, move_pawn_idx)
    if not final_pos or final_pos in SAFE_SQUARES: return False
    for color in players_setup:
        if color != move_color:
            for i in range(4):
                if pawns[color][i][0] == 1 and get_pawn_screen_pos(color, i) == final_pos:
                    pawns[color][i] = [0, -1]; return True
    return False

def check_for_win():
    global winner, game_state; color = players_setup[current_player_index]
    if all(p[0] == 2 for p in pawns[color]): winner = color; game_state = "game_over"

# --- Main Game Loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos; virtual_mx = int(mx / scale_factor); virtual_my = int(my / scale_factor)
            if game_state == "menu":
                btn_2p = pygame.Rect(BASE_WIDTH//2-125, 280, 250, 60); btn_4p = pygame.Rect(BASE_WIDTH//2-125, 360, 250, 60)
                if btn_2p.collidepoint(virtual_mx, virtual_my): reset_game(2)
                elif btn_4p.collidepoint(virtual_mx, virtual_my): reset_game(4)
            elif game_state == "playing":
                dice_rect = pygame.Rect(268, 615, 64, 64)
                if turn_state == "roll" and dice_rect.collidepoint(virtual_mx, virtual_my):
                    dice_value = random.randint(1, 6); find_movable_pawns()
                    if movable_pawns: turn_state = "move"; message = "Click a highlighted pawn."
                    else: message = f"Rolled {dice_value}. No moves."; draw_all(); time.sleep(1.2); next_turn()
                elif turn_state == "move":
                    color = players_setup[current_player_index]
                    for pawn_idx in movable_pawns:
                        pos = get_pawn_screen_pos(color, pawn_idx)
                        if pos and pygame.Rect(pos[0]-17, pos[1]-17, 34, 34).collidepoint(virtual_mx, virtual_my):
                            state, path_idx = pawns[color][pawn_idx]
                            if state == 0 and dice_value == 6: pawns[color][pawn_idx] = [1, 0]
                            elif state == 1:
                                new_idx = path_idx + dice_value
                                if new_idx == 57: pawns[color][pawn_idx] = [2, -1] # Reached home
                                else: pawns[color][pawn_idx][1] = new_idx
                            capture = check_for_capture(color, pawn_idx); check_for_win()
                            if game_state != "game_over":
                                if capture or dice_value == 6:
                                    turn_state = "roll"; dice_value = 0; message = f"{color.title()} gets another turn!"
                                else: next_turn()
                            break
            elif game_state == "game_over": game_state = "menu"
    draw_all()
pygame.quit()
sys.exit()

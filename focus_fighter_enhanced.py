import pygame
import random
import os
import missions

# ------window & Display Setup------
is_fullscreen = False
screen = pygame.display.set_mode((0, 0), pygame.RESIZABLE | pygame.SHOWN)
WIDTH, HEIGHT = screen.get_size()

os.environ['SDL_VIDEO_CENTERED'] = '1'
screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE | pygame.SHOWN)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("Focus Fighter")

pygame.init()
pygame.mixer.init()
display_info = pygame.display.Info()
WIDTH, HEIGHT = display_info.current_w, display_info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE | pygame.SHOWN)
pygame.display.set_caption("Focus Fighter")

# ───── Handle Esc to minimize properly ─────
def update_ui_rects():
    global minus_rect, plus_rect
    minus_rect = pygame.Rect(WIDTH - 160, HEIGHT - 60, 30, 30)
    plus_rect = pygame.Rect(WIDTH - 100, HEIGHT - 60, 30, 30)

def scale_background():
    global bg_image
    original_bg = pygame.image.load("assets/images/bg_image.jpg").convert()
    screen_width, screen_height = screen.get_size()
    bg_image = pygame.transform.scale(original_bg, (screen_width, screen_height))

update_ui_rects()
scale_background()

screen.blit(bg_image, (0, 0))
pygame.display.update()
# ───── Gamepad Setup ─────
pygame.joystick.init()
joystick = None
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print("Joystick connected:", joystick.get_name())
else:
    print()

# ──────── Sound Setup ────────
sound_path = "assets/sounds/"
fire_sound = pygame.mixer.Sound(os.path.join(sound_path, "fire.wav"))
enemy_kill_sound = pygame.mixer.Sound(os.path.join(sound_path, "enemy_kill.wav"))
boss_defeated_sound = pygame.mixer.Sound(os.path.join(sound_path, "boss_defeated.wav"))
powerup_sound = pygame.mixer.Sound(os.path.join(sound_path, "powerup.wav"))
gameover_sound = pygame.mixer.Sound(os.path.join(sound_path, "game_over.mp3"))

music_tracks = [f for f in os.listdir(sound_path) if f.startswith("bg_music") and (f.endswith(".mp3") or f.endswith(".wav"))]
current_track_index = 0
volume_level = 0.4
is_muted = False
enemy_fire_sound = pygame.mixer.Sound(os.path.join(sound_path, "enemy_fire.wav"))
enemy_fire_sound.set_volume(volume_level)

# --- collect all sound objects so we can set volumes in one place ---
all_sounds = [
    fire_sound,
    enemy_kill_sound,
    boss_defeated_sound,
    powerup_sound,
    gameover_sound,
    enemy_fire_sound,
]

# ───── Boss & Enemy Types Setup ─────
boss_types = [
    {"type": "fast", "speed": 4},
    {"type": "teleport", "teleport_interval": 2000},
    {"type": "shielded", "shield": True}
]

enemy_bullets = []
ENEMY_FIRE_INTERVAL = 2000  # milliseconds
last_enemy_fire_time = 0

boss_bullets = []
last_boss_shot = pygame.time.get_ticks()
last_teleport = pygame.time.get_ticks()

game_mode = "normal"  # Can be 'normal', 'training', 'endless', 'time_attack'
bg_x = 0
game_over_time = None

# ──────── LEVELS SETUP ────────
levels = [
    {"duration": 60000, "enemy_speed": 3, "spawn_rate": 90},
    {"duration": 70000, "enemy_speed": 4, "spawn_rate": 70},
    {"duration": 80000, "enemy_speed": 5, "spawn_rate": 50},
]
current_level = 0

def play_music(index):
    pygame.mixer.music.load(os.path.join(sound_path, music_tracks[index]))
    pygame.mixer.music.set_volume(volume_level)
    pygame.mixer.music.play(-1)

play_music(current_track_index)

# ──────── Game Setup ────────
update_ui_rects()
pygame.display.set_caption("Focus Fighter")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 36)
WHITE, BLUE, GREEN, GRAY = (255, 255, 255), (50, 150, 255), (0, 255, 0), (60, 60, 60)
ORANGE, RED, PURPLE, CYAN = (255, 100, 0), (200, 50, 50), (180, 50, 255), (0, 255, 255)
YELLOW, MAGENTA = (255, 255, 0), (255, 0, 255)

# Load and scale background image
screen_width, screen_height = screen.get_size()
WIDTH, HEIGHT = screen_width, screen_height
update_ui_rects()

bg_image = pygame.image.load("assets/images/bg_image.jpg").convert()
bg_image = pygame.transform.scale(bg_image, (screen_width, screen_height))

# ──────── Game State ────────
HISTORY_FILE = "score_history.txt"

def save_score_history(p1_score, p2_score=0):
    with open(HISTORY_FILE, "a") as f:
        if is_multiplayer:
            f.write(f"P1: {p1_score}, P2: {p2_score}\n")
        else:
            f.write(f"P1 (Solo): {p1_score}\n")

HIGH_SCORE_FILE = "highscore.txt"
POWER_TYPES = ['shield', 'slow', 'double']
POWER_COLORS = {'shield': CYAN, 'slow': YELLOW, 'double': MAGENTA}
FIRE_DELAY = 15
is_paused = False
is_multiplayer = False  # By default, single-player

# Volume buttons
minus_rect = pygame.Rect(WIDTH - 160, HEIGHT - 60, 30, 30)
plus_rect = pygame.Rect(WIDTH - 100, HEIGHT - 60, 30, 30)

def load_high_score():
    return int(open(HIGH_SCORE_FILE).read()) if os.path.exists(HIGH_SCORE_FILE) else 0

def save_high_score(score):
    with open(HIGH_SCORE_FILE, "w") as f:
        f.write(str(score))

def apply_volume():
    """Apply current volume_level or mute to music and all SFX."""
    if is_muted:
        pygame.mixer.music.set_volume(0)
        for s in all_sounds:
            s.set_volume(0)
    else:
        pygame.mixer.music.set_volume(volume_level)
        for s in all_sounds:
            s.set_volume(volume_level)

def set_volume(vol=None):
    """Set volume_level (0.0–1.0). Call without arg to re-apply current volume."""
    global volume_level
    if vol is not None:
        volume_level = max(0.0, min(vol, 1.0))
    apply_volume()

def toggle_mute():
    """Toggle mute on/off and apply volumes."""
    global is_muted
    is_muted = not is_muted
    apply_volume()

# show time attack duration to choose
def show_time_attack_duration():
    selecting = True
    while selecting:
        screen.blit(bg_image, (0, 0))
        title = font.render("SELECT TIME ATTACK DURATION", True, RED)
        one_min = font.render("1. 1 Minute", True, WHITE)
        two_min = font.render("2. 2 Minutes", True, WHITE)
        three_min = font.render("3. 3 Minutes", True, WHITE)

        screen.blit(title, (WIDTH // 2 - 200, HEIGHT // 2 - 100))
        screen.blit(one_min, (WIDTH // 2 - 120, HEIGHT // 2 - 40))
        screen.blit(two_min, (WIDTH // 2 - 120, HEIGHT // 2))
        screen.blit(three_min, (WIDTH // 2 - 120, HEIGHT // 2 + 40))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return 60000     # 1 min
                elif event.key == pygame.K_2:
                    return 120000    # 2 min
                elif event.key == pygame.K_3:
                    return 180000    # 3 min

# Mode Selection Screen
def show_mode_selection():
    selecting = True
    global game_mode
    while selecting:
        screen.blit(bg_image, (0, 0))
        title = font.render("CHOOSE MODE", True, WHITE)
        solo = font.render("1. Solo Mode (Press 1)", True, GREEN)
        multi = font.render("2. Multiplayer Mode (Press 2)", True, CYAN)
        train = font.render("3. Training Mode (Press 3)", True, MAGENTA)
        endless = font.render("4. Endless Mode (Press 4)", True, YELLOW)
        timeattack = font.render("5. Time Attack (Press 5)", True, RED)

        screen.blit(title, (WIDTH//2 - 100, HEIGHT//2 - 120))
        screen.blit(solo, (WIDTH//2 - 140, HEIGHT//2 - 50))
        screen.blit(multi, (WIDTH//2 - 140, HEIGHT//2 - 10))
        screen.blit(train, (WIDTH//2 - 140, HEIGHT//2 + 30))
        screen.blit(endless, (WIDTH//2 - 140, HEIGHT//2 + 70))
        screen.blit(timeattack, (WIDTH//2 - 140, HEIGHT//2 + 110))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    game_mode = "normal"
                    return False, None
                elif event.key == pygame.K_2:
                    game_mode = "normal"
                    return True, None
                elif event.key == pygame.K_3:
                    game_mode = "training"
                    return False, None
                elif event.key == pygame.K_4:
                    game_mode = "endless"
                    return False, None
                elif event.key == pygame.K_5:
                    game_mode = "time_attack"
                    duration = show_time_attack_duration()
                    return False, duration
                
is_multiplayer, selected_duration = show_mode_selection()
WIDTH, HEIGHT = screen.get_size()
update_ui_rects()
scale_background()
pygame.display.update()

def reset_game():
    global score_saved, selected_duration
    global player, focus, lives, max_focus, score, total_attacks, successful_hits, fire_cooldown
    global player2, player2_lives, player2_focus, player2_score, player2_active
    global fireballs, enemies, enemy_timer, enemy_spawn_time
    global game_over, high_score, boss_enemy, boss_health, boss_active
    global power_ups, active_power, power_timer, shield_active
    global level_start_time, level_duration, level_completed, current_level
    global boss_bullets, last_boss_shot, last_teleport, bg_x, game_over_time
    global enemy_bullets, last_enemy_fire_time

    player = pygame.Rect(100, 450, 50, 50)
    if is_multiplayer:
        player2 = pygame.Rect(100, 300, 50, 50)

    focus, max_focus, lives = 100, 100, 3 if game_mode != "training" else 9999
    score, total_attacks, successful_hits = 0, 0, 0
    fire_cooldown = 0
    fireballs, enemies, power_ups, boss_bullets = [], [], [], []
    enemy_bullets = []
    last_enemy_fire_time = pygame.time.get_ticks()
    enemy_timer, enemy_spawn_time = 0, 90
    game_over, boss_active, shield_active = False, False, False
    boss_enemy, boss_health = None, 0
    active_power, power_timer = None, 0
    high_score = load_high_score()
    game_over_time = None

    player2_lives = 3 if game_mode != "training" else 9999
    player2_focus = 100
    player2_score = 0
    player2_active = False

    current_level = 0
    level_start_time = pygame.time.get_ticks()
    level_duration = selected_duration if game_mode == "time_attack" else levels[current_level]["duration"]
    level_completed = False

    last_boss_shot = pygame.time.get_ticks()
    last_teleport = pygame.time.get_ticks()
    bg_x = 0

    if is_multiplayer:
        player2 = pygame.Rect(100, 300, 50, 50)
    import missions
    if not is_multiplayer and game_mode == "normal":
        missions.reset_mission()
        missions.start_random_mission()

def draw_focus_bar(x, y, w, h):
    pygame.draw.rect(screen, GRAY, (x, y, w, h))
    if focus > 0:
        fill_width = max(1, int((focus / max_focus) * w))
        pygame.draw.rect(screen, GREEN, (x, y, fill_width, h))

def draw_volume_controls():
    pygame.draw.rect(screen, WHITE, minus_rect)
    pygame.draw.rect(screen, WHITE, plus_rect)
    screen.blit(font.render("-", True, (0, 0, 0)), minus_rect.move(10, 0))
    screen.blit(font.render("+", True, (0, 0, 0)), plus_rect.move(10, 0))
    pygame.draw.rect(screen, WHITE, (WIDTH - 200, HEIGHT - 25, 150, 10))
    fill_rect = pygame.Rect(WIDTH - 200, HEIGHT - 25, int(150 * volume_level), 10)
    pygame.draw.rect(screen, GREEN, fill_rect)
    vol_text = font.render("Volume", True, WHITE)
    screen.blit(vol_text, (WIDTH - 270, HEIGHT - 60))

def draw_ui():
    # Use focus to calculate accuracy (since green bar is based on focus)
    acc = max(0, min(100, int((focus / max_focus) * 100)))  # Assuming max_focus = 100

    # Accuracy % Text
    accuracy_text = font.render(f"Accuracy: {acc}%", True, WHITE)
    screen.blit(accuracy_text, (20, 100))

    # Main Stats Texts (excluding accuracy again)
    texts = [
        f"Focus: {int(focus)}",
        f"Lives: {max(0, lives)}",
        f"Score: {score}",
        f"High Score: {high_score}"
    ]
    for i, txt in enumerate(texts):
        render = font.render(txt, True, WHITE)
        if i < 2:
            screen.blit(render, (20, 20 + i * 40))
        else:
            screen.blit(render, (WIDTH - 200, 20 + (i - 2) * 40))

    # Power-Up UI
    if active_power:
        power_text = font.render(f"Power-Up: {active_power.upper()}", True, POWER_COLORS[active_power])
        screen.blit(power_text, (WIDTH // 2 - 100, 20))

    # Timer for non-ended levels
    if not game_over and not level_completed and game_mode == "time_attack":
        remaining = max(0, (level_duration - (pygame.time.get_ticks() - level_start_time)) // 1000)
        timer = font.render(f"Time Left: {remaining}s", True, WHITE)
        screen.blit(timer, (WIDTH // 2 - 70, 60))

    # Multiplayer Stats
    if is_multiplayer:
        p1_stat = font.render(f"P1 Lives: {lives}  Score: {score}", True, BLUE)
        p2_stat = font.render(f"P2 Lives: {player2_lives}  Score: {player2_score}", True, GREEN)
        screen.blit(p1_stat, (20, HEIGHT - 100))
        screen.blit(p2_stat, (20, HEIGHT - 70))

        mp_ui = [
            f"P2 Lives: {player2_lives}",
            f"P2 Focus: {int(player2_focus)}",
            f"P2 Score: {player2_score}"
        ]
        for i, txt in enumerate(mp_ui):
            render = font.render(txt, True, CYAN)
            screen.blit(render, (20, 300 + i * 40))
    if not is_multiplayer and game_mode == "normal":
        draw_mission_ui()
        
    # Volume Control Buttons
    draw_volume_controls()


def draw_mission_ui():
    mission = missions.get_selected_mission()
    window_width, window_height = screen.get_size()
            
    # Show active mission
    if missions.is_mission_active() and mission:
        title = font.render(f"Mission: {mission['description']}", True, YELLOW)
        screen.blit(title, (window_width // 2 - 150, window_height - 120))

        if mission["type"] == "defeat_enemies":
            progress = font.render(
                f"Progress: {missions.get_mission_progress()}/{mission['goal']}", True, WHITE
            )
            screen.blit(progress, (window_width // 2 - 150, window_height - 90))

        elif mission["type"] == "accuracy":
            progress = font.render(
                f"Maintain ≥{mission['goal']}% accuracy for {mission['time'] // 1000}s", True, WHITE
            )
            screen.blit(progress, (window_width // 2 - 150, window_height - 90))

    # Show mission success for 3 seconds
    elif missions.mission_success() and missions.get_mission_success_time() != 0 and pygame.time.get_ticks() - missions.get_mission_success_time() < 5000:
        done = font.render("✅ Mission Completed!", True, GREEN)
        screen.blit(done, (window_width // 2 - 150, window_height - 100))

    # Show mission failure for 3 seconds
    elif missions.mission_failed() and missions.get_mission_success_time() != 0 and pygame.time.get_ticks() - missions.get_mission_success_time() < 3000:
        fail = font.render("❌ Mission Failed!", True, RED)
        screen.blit(fail, (window_width // 2 - 150, window_height - 100))

def draw_all():
    screen.blit(bg_image, (0, 0))  # ✅ Background

    pygame.draw.rect(screen, BLUE, player)
    for fb in fireballs:
        pygame.draw.rect(screen, ORANGE, fb["rect"])
    for en in enemies:
        pygame.draw.rect(screen, RED, en)
    for eb in enemy_bullets:
        pygame.draw.rect(screen, YELLOW, eb["rect"])
    for p in power_ups:
        pygame.draw.rect(screen, POWER_COLORS[p["type"]], p["rect"])

    if boss_enemy:
        pygame.draw.rect(screen, PURPLE, boss_enemy)
        ratio = boss_health / 5
        pygame.draw.rect(screen, RED, (boss_enemy.x, boss_enemy.y - 15, boss_enemy.width, 10))
        pygame.draw.rect(screen, GREEN, (boss_enemy.x, boss_enemy.y - 15, boss_enemy.width * ratio, 10))
    
    if is_multiplayer:
        pygame.draw.rect(screen, GREEN, player2)

    draw_focus_bar(20, 140, 300, 20)
    draw_ui()
    pause_status = font.render("PAUSE: P | Mute: M | Change Track: B", True, WHITE)
    screen.blit(pause_status, (20, HEIGHT - 35))

reset_game()

def handle_collisions():
    global fireballs, enemies, score, successful_hits, focus
    global power_ups, active_power, power_timer, lives, shield_active

    for fb in fireballs[:]:
        for en in enemies[:]:
            if fb["rect"].colliderect(en):
                fireballs.remove(fb)
                enemies.remove(en)
                score += 10
                successful_hits += 1
                focus = min(max_focus, focus + 2)
                break

    for p in power_ups[:]:
        if player.colliderect(p["rect"]):
            active_power = random.choice(["shield", "boost", "extra_life"])
            power_timer = pygame.time.get_ticks()
            if active_power == "extra_life":
                lives += 1
            elif active_power == "shield":
                shield_active = True
            power_ups.remove(p)

def update_enemies():
    global enemy_timer, enemy_spawn_time, enemies

    enemy_timer += 1
    if enemy_timer >= enemy_spawn_time:
        x = random.randint(50, WIDTH - 50)
        y = -50
        enemy = pygame.Rect(x, y, 40, 40)
        enemies.append(enemy)
        enemy_timer = 0

    for en in enemies:
        en.y += 2  # Adjust speed as needed

def update_powerups():

    global shield_active, power_ups, player, active_power, power_timer

    for p in power_ups[:]:
        if player.colliderect(p["rect"]):
            active_power = p["type"]
            power_timer = pygame.time.get_ticks()
            if active_power == "shield":
                shield_active = True
            powerup_sound.play()
            power_ups.remove(p)

# ──────── Game Loop ────────
WIDTH, HEIGHT = screen.get_size()
game_over_time = None
score_saved = None
running = True
while running:
    clock.tick(60)
    # 🧠 Input handling
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            update_ui_rects()
            scale_background()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
            # Escape minimizes the window (not pause or quit)
                pygame.display.iconify()
            elif event.key == pygame.K_p:
                is_paused = not is_paused
            elif event.key == pygame.K_b:
                current_track_index = (current_track_index + 1) % len(music_tracks)
                play_music(current_track_index)
            elif event.key == pygame.K_m:
                toggle_mute()
            elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                set_volume(volume_level + 0.1)
            elif event.key == pygame.K_MINUS:
                set_volume(volume_level - 0.1)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if minus_rect.collidepoint(event.pos):
                set_volume(volume_level - 0.1)
            elif plus_rect.collidepoint(event.pos):
                set_volume(volume_level + 0.1)

    # Pause check
    if is_paused:
        screen.blit(bg_image, (0, 0))
        pause_text = font.render("PAUSED - Press P to Resume", True, WHITE)
        screen.blit(pause_text, pause_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        pygame.display.update()
        continue

    # 🎨 Draw Background
    screen.blit(bg_image, (0, 0))

    # Game logic
    if not game_over:
        if not is_multiplayer and game_mode == "normal":
            missions.update_mission(total_attacks, successful_hits)
        # 🕹 Gamepad Movement
        if joystick:
            axis_x = joystick.get_axis(0)
            axis_y = joystick.get_axis(1)
            if abs(axis_x) > 0.2:
                player.x += int(axis_x * 5)
            if abs(axis_y) > 0.2:
                player.y += int(axis_y * 5)

        # ⌨️ Keyboard Movement
        if is_multiplayer:
            if keys[pygame.K_a]: player2.x -= 5
            if keys[pygame.K_d]: player2.x += 5
            if keys[pygame.K_w]: player2.y -= 5
            if keys[pygame.K_s]: player2.y += 5

            player2.x = max(0, min(player2.x, WIDTH - player2.width))
            player2.y = max(0, min(player2.y, HEIGHT - player2.height))
        
        handle_collisions()
        update_powerups()
        if not is_multiplayer and game_mode == "normal":
            if missions.is_mission_active() and missions.get_mission_success_time() != 0:
                if pygame.time.get_ticks() - missions.get_mission_success_time() > 5000:
                    missions.reset_mission()
                    missions.start_random_mission()

        draw_all()
        
        if keys[pygame.K_LEFT]:
            player.x -= 5
        if keys[pygame.K_RIGHT]:
            player.x += 5
        if keys[pygame.K_UP]:
            player.y -= 5
        if keys[pygame.K_DOWN]:
            player.y += 5

        # Constrain player in bounds
        player.x = max(0, min(player.x, WIDTH - player.width))
        player.y = max(0, min(player.y, HEIGHT - player.height))

        # 🔫 Gamepad or keyboard fire
        if (joystick and joystick.get_button(0)) or keys[pygame.K_SPACE]:
            if fire_cooldown == 0:
                fireballs.append({"rect": pygame.Rect(player.x + player.width, player.y + 20, 20, 10), "owner": "P1"})
                total_attacks += 1
                fire_cooldown = FIRE_DELAY
                fire_sound.play()
        
        # 🔫 Player 2 fire (Multiplayer only)
        if is_multiplayer and keys[pygame.K_f] and fire_cooldown == 0:
            fireballs.append({"rect": pygame.Rect(player2.x + player2.width, player2.y + 20, 20, 10), "owner": "P2"})
            total_attacks += 1
            fire_cooldown = FIRE_DELAY
            fire_sound.play()

        if fire_cooldown > 0:
            fire_cooldown -= 1

        # 🕒 Timer-based level challenge
        if not level_completed:
            elapsed = pygame.time.get_ticks() - level_start_time
            if elapsed >= level_duration:
                level_completed = True

        if level_completed:
            if game_mode == "time_attack":
                game_over = True
            else:
                current_level += 1
                if current_level < len(levels):
                    level_start_time = pygame.time.get_ticks()
                    level_duration = levels[current_level]["duration"]
                    enemy_spawn_time = levels[current_level]["spawn_rate"]
                    level_completed = False
                else:
                    game_over = True

        # 👾 Spawn enemies and power-ups
        enemy_timer += 1
        spawn_delay = int(enemy_spawn_time * 1.5) if active_power == "slow" else enemy_spawn_time
        if enemy_timer >= spawn_delay:
            enemy_timer = 0
            enemies.append(pygame.Rect(WIDTH, random.randint(100, HEIGHT - 50), 40, 40))

        if (score >= 100 or player2_score >= 100) and not boss_active:
            boss_enemy = pygame.Rect(WIDTH, HEIGHT // 2 - 40, 80, 80)
            boss_health = 5
            boss_active = True

        if random.randint(1, 500) == 1 and len(power_ups) < 1:
            ptype = random.choice(POWER_TYPES)
            rect = pygame.Rect(random.randint(100, WIDTH - 100), random.randint(150, HEIGHT - 60), 30, 30)
            power_ups.append({"type": ptype, "rect": rect})

        # 🔄 Update fireballs and enemies
        for fb in fireballs:
            fb["rect"].x += 10
        fireballs = [fb for fb in fireballs if fb["rect"].x < WIDTH]

        for eb in enemy_bullets:
            eb["rect"].x += eb["vel"][0]
            eb["rect"].y += eb["vel"][1]
        enemy_bullets = [eb for eb in enemy_bullets if 0 <= eb["rect"].x <= WIDTH and 0 <= eb["rect"].y <= HEIGHT]
        # 👊 Enemy bullets hitting the player
        for eb in enemy_bullets[:]:
            if eb["rect"].colliderect(player):
                enemy_bullets.remove(eb)
                if shield_active:
                    shield_active = False
                else:
                    lives -= 1
                    focus = max(0, focus - 20)
                    if lives <= 0 and focus == 0:
                        gameover_sound.play()
                        game_over = True
        if is_multiplayer:
            for eb in enemy_bullets[:]:
                if eb["rect"].colliderect(player2):
                    enemy_bullets.remove(eb)
                    if shield_active:
                        shield_active = False
                    else:
                        player2_lives -= 1
                        player2_focus = max(0, player2_focus - 20)
                        if player2_lives <= 0:
                            gameover_sound.play()
                            game_over = True
                    
        enemy_speed = levels[current_level]["enemy_speed"]
        for en in enemies:
            en.x -= 1 if active_power == "slow" else enemy_speed
            # 🔫 Enemy Firing (bullets towards player)
            current_time = pygame.time.get_ticks()
            if current_time - last_enemy_fire_time > ENEMY_FIRE_INTERVAL:
                for en in enemies:
                    # Choose target if needed (for future logic like multiplayer scores), but shoot horizontally
                    bullet = {
                        "rect": pygame.Rect(en.left, en.centery - 5, 10, 10),  # Spawn bullet at enemy's left center
                        "vel": (-5, 0)  # Always move left horizontally
                    }
                    enemy_bullets.append(bullet)
                    enemy_fire_sound.play()
                last_enemy_fire_time = current_time

        if boss_enemy:
            boss_enemy.x -= 1 if active_power == "slow" else 2
            if boss_enemy.right < 0:
                boss_enemy = None
                boss_active = False

        # 🎯 Collisions: Fireballs vs enemies
        for fb in fireballs[:]:
            for en in enemies[:]:
                if fb["rect"].colliderect(en):
                    fireballs.remove(fb)
                    enemies.remove(en)
                    if not is_multiplayer and game_mode == "normal":
                        if missions.is_mission_active():
                            mission = missions.get_selected_mission()
                            if mission and mission["type"] == "defeat_enemies":
                                missions.increment_mission_progress()
                    successful_hits += 1
                    if fb["owner"] == "P1":
                        score += 20 if active_power == "double" else 10
                        focus = min(100, focus + 15)
                    else:
                        player2_score += 20 if active_power == "double" else 10 
                        focus = min(100, player2_score + 15)
                    enemy_kill_sound.play()
                    break

        if boss_enemy:
            for fb in fireballs[:]:
                if fb["rect"].colliderect(boss_enemy):
                    fireballs.remove(fb)
                    boss_health -= 1
                    successful_hits += 1
                    if boss_health <= 0:
                        if fb["owner"] == "player2":
                            player2_score += 50
                            player2_focus = min(100, player2_focus + 30)
                        else:
                            score += 50
                            focus = min(100, focus + 30)
                        boss_enemy = None
                        boss_active = False
                        boss_defeated_sound.play()
                    break

        for en in enemies[:]:
            if en.colliderect(player):
                enemies.remove(en)
                for eb in enemy_bullets[:]:
                    if eb["rect"].colliderect(player):
                        enemy_bullets.remove(eb)

                if shield_active:
                    shield_active = False
                else:
                    if lives > 0:
                        lives -= 1
                        if lives <= 0 or focus == 0:
                            gameover_sound.play()
                            game_over = True
                    focus = max(0, focus - 20)

        if boss_enemy and boss_enemy.colliderect(player):
            if shield_active:
                shield_active = False
            else:
                lives -= 1
                focus = max(0, focus - 30)
                if lives <= 0 or focus == 0:
                    gameover_sound.play()
                    game_over = True
            boss_enemy = None
            boss_active = False

        for p in power_ups[:]:
            if not is_multiplayer and game_mode == "normal":
                mission = missions.get_selected_mission()
            if p["rect"].colliderect(player):
                if not is_multiplayer and game_mode == "normal":
                    if mission and mission["type"] == "no_powerups":
                        missions.mark_powerup_used()
                active_power = p["type"]
                power_timer = pygame.time.get_ticks()
                if active_power == "shield":
                    shield_active = True
                powerup_sound.play()
                power_ups.remove(p)
                
            # Player 2 collision
            elif is_multiplayer and p["rect"].colliderect(player2):
                active_power = p["type"]
                power_timer = pygame.time.get_ticks()
                if active_power == "shield":
                    shield_active = True
                powerup_sound.play()
                power_ups.remove(p)

        if active_power and active_power != "shield":
            if pygame.time.get_ticks() - power_timer > 5000:
                active_power = None

        focus = max(0, focus - 0.1)
        if focus == 0 or lives <= 0:
            focus = 0
            lives = 0
            gameover_sound.play()
            game_over = True

        if score % 50 == 0 and score != 0 and enemy_spawn_time > 30:
            enemy_spawn_time -= 1

        if is_multiplayer:
            for en in enemies[:]:
                if en.colliderect(player2):
                    enemies.remove(en)
                    if shield_active:
                        shield_active = False
                    else:
                        player2_lives -= 1
                        player2_focus = max(0, player2_focus - 20)
                        if player2_lives <= 0:
                            gameover_sound.play()
                            game_over = True

        if boss_enemy and is_multiplayer and boss_enemy.colliderect(player2):
            if shield_active:
                shield_active = False
            else:
                player2_lives -= 1
                player2_focus = max(0, player2_focus - 30)
                if player2_lives <= 0:
                    gameover_sound.play()
                    game_over = True
            boss_enemy = None
            boss_active = False

        # 🎨 Draw all elements (player, enemies, UI, etc.)
        draw_all()
        if not missions.is_mission_active() and missions.get_mission_success_time() != 0:
            if pygame.time.get_ticks() - missions.get_mission_success_time() > 5000:
                missions.reset_mission()
                missions.start_random_mission()
        # ✅ FINAL game over enforcement — STRONG version
        if not game_over:
            if (lives <= 0 or focus <= 0):
                focus = 0
                lives = 0
                game_over = True
                if not score_saved:
                    gameover_sound.play()
                game_over_time = pygame.time.get_ticks()
                continue
            
    else:
        if not score_saved:
            current_high = load_high_score()
            if is_multiplayer:
                top_score = max(score, player2_score)
            else:
                top_score = score
            
            if top_score > current_high:
                save_high_score(top_score)
            
            save_score_history(score, player2_score)
            score_saved = True

        if score > high_score:
            high_score = score
            save_high_score(high_score)
        
        if player2_score > high_score:
            high_score = player2_score
            save_high_score(high_score)
        if player2_score > high_score:
            high_score = player2_score
            save_high_score(high_score)

        if game_mode == "time_attack" and level_completed:
            message = "⏰ TIME'S UP!"
            sub_message = "🎉 Congratulations! You survived!"
        else:
            message = "GAME OVER!"
            if is_multiplayer:
                if score > player2_score:
                    sub_message = "Player 1 Wins!"
                elif player2_score > score:
                    sub_message = "Player 2 Wins!"
                else:
                    sub_message = "It's a Tie!"
            else:
                sub_message = f"Your Score: {score}"
        # Display messages
        go_text = font.render(message, True, RED)
        go_rect = go_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 120))
        screen.blit(go_text, go_rect)

        # Subtext
        sub_text = font.render(sub_message, True, (0, 0, 0))
        sub_rect = sub_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80))
        screen.blit(sub_text, sub_rect)

        # Automatically return to mode selection after 5 seconds of Game Over
        if game_over_time is None:
            game_over_time = pygame.time.get_ticks()

        if game_over_time and pygame.time.get_ticks() - game_over_time > 5000:
            is_multiplayer, selected_duration = show_mode_selection()
            reset_game()
            game_over_time = None  # Reset the timer for next game over
            continue  # Skip drawing Game Over screen again

        # Optional: Keyboard shortcut (press R to restart in same mode)
        if keys[pygame.K_r]:
            reset_game()


    # 🔄 Update screen
    pygame.display.update()

pygame.quit() 

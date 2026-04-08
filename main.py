import turtle
import random
import time
import math

BG_COLOR = "#d9f7d9"
GRID_COLOR = "#184d2f"
HUD_FILL = "#f4fff4"
HUD_BORDER = "#184d2f"
STATUS_FILL = "#ecffec"
LEVEL_UP_SCORE = 10
MEGA_FOOD_SCORE = 15
MEGA_FOOD_DURATION = 5
WEAPON_UNLOCK_LEVEL = 3
WEAPON_SCORE_BONUS = 20
WEAPON_MAX_COUNT = 3
GUN_BULLETS_PER_PICKUP = 15
KILL_STREAK_WINDOW = 4
BASE_MOVE_SPEED = 6
BASE_ENEMY_SPEED = 0.8
GORILLA_SPEED_BONUS = 0.3
MIN_SPAWN_DISTANCE = 70
TERRAIN_THEMES = [
    {"bg": "#d9f7d9", "grid": "#184d2f", "accent": "#2d8a57", "label": "GRASSLAND"},
    {"bg": "#efe0b8", "grid": "#7a4a12", "accent": "#b06b1f", "label": "DUNES"},
    {"bg": "#dcecff", "grid": "#24507a", "accent": "#4f84ba", "label": "FROST"},
    {"bg": "#f0d8d8", "grid": "#7a1f1f", "accent": "#d14b4b", "label": "EMBER"},
    {"bg": "#e8dcff", "grid": "#4a2a78", "accent": "#7b50b2", "label": "AURORA"},
    {"bg": "#d6f0f9", "grid": "#1a5b6d", "accent": "#2ea2bf", "label": "TIDAL"},
]

# Screen setup
screen = turtle.Screen()
screen.title("Ultimate Collect Game")
screen.bgcolor(BG_COLOR)
screen.setup(width=600, height=600)
screen.tracer(0)

# Decorative background accents (light green + black)
bg_accent = turtle.Turtle()
bg_accent.hideturtle()
bg_accent.speed(0)
bg_accent.penup()
bg_accent.color(GRID_COLOR)

# Scenic graphics layer
bg_scene = turtle.Turtle()
bg_scene.hideturtle()
bg_scene.speed(0)
bg_scene.penup()

bg_accent.goto(-295, 295)
bg_accent.pendown()
bg_accent.pensize(4)
for _ in range(4):
    bg_accent.forward(590)
    bg_accent.right(90)

bg_accent.penup()
bg_accent.pensize(1)
for x in range(-260, 281, 80):
    bg_accent.goto(x, -295)
    bg_accent.setheading(90)
    bg_accent.pendown()
    bg_accent.forward(590)
    bg_accent.penup()

for y in range(-260, 281, 80):
    bg_accent.goto(-295, y)
    bg_accent.setheading(0)
    bg_accent.pendown()
    bg_accent.forward(590)
    bg_accent.penup()


def random_position(avoid_turtles=(), min_distance=MIN_SPAWN_DISTANCE, attempts=200):
    candidate = (0, 0)
    for _ in range(attempts):
        candidate = random.randint(-260, 260), random.randint(-260, 260)
        if all(math.hypot(candidate[0] - item.xcor(), candidate[1] - item.ycor()) >= min_distance for item in avoid_turtles):
            return candidate
    return candidate


def place_turtle_randomly(turtle_obj, avoid_turtles=()):
    turtle_obj.goto(random_position(avoid_turtles=avoid_turtles + (turtle_obj,), min_distance=MIN_SPAWN_DISTANCE))


def draw_terrain(level):
    theme = TERRAIN_THEMES[(level - 1) % len(TERRAIN_THEMES)]
    screen.bgcolor(theme["bg"])

    bg_accent.clear()
    bg_scene.clear()
    bg_accent.hideturtle()
    bg_scene.hideturtle()
    bg_accent.speed(0)
    bg_scene.speed(0)
    bg_accent.penup()
    bg_scene.penup()

    # Stable pseudo-random for repeatable level look.
    rng = random.Random(level * 97)
    label = theme["label"]

    # Scenic graphics layer.
    bg_scene.pensize(2)
    if level >= 5:
        # Universe stage.
        bg_scene.color("#ffffff")
        for _ in range(90):
            bg_scene.goto(rng.randint(-280, 280), rng.randint(-280, 280))
            bg_scene.dot(rng.randint(2, 4))

        bg_scene.color(theme["accent"])
        for radius in (55, 95, 140, 185):
            bg_scene.goto(0, -radius)
            bg_scene.setheading(0)
            bg_scene.pendown()
            bg_scene.circle(radius)
            bg_scene.penup()
    elif label == "DUNES":
        bg_scene.color(theme["accent"])
        for y_base in (-250, -220, -190, -160):
            bg_scene.goto(-300, y_base)
            bg_scene.pendown()
            for x in range(-300, 301, 10):
                y_wave = y_base + math.sin((x + level * 8) / 40) * 10
                bg_scene.goto(x, y_wave)
            bg_scene.penup()
    elif label == "GRASSLAND":
        bg_scene.color(theme["accent"])
        for x in (-260, -130, 10, 150):
            bg_scene.goto(x, -290)
            bg_scene.pendown()
            bg_scene.begin_fill()
            bg_scene.setheading(60)
            bg_scene.circle(95, 120)
            bg_scene.goto(x + 140, -290)
            bg_scene.goto(x, -290)
            bg_scene.end_fill()
            bg_scene.penup()
    elif label == "FROST":
        bg_scene.color(theme["accent"])
        for base_x in (-240, -80, 80):
            bg_scene.goto(base_x, -290)
            bg_scene.pendown()
            bg_scene.begin_fill()
            bg_scene.goto(base_x + 70, -120)
            bg_scene.goto(base_x + 140, -290)
            bg_scene.goto(base_x, -290)
            bg_scene.end_fill()
            bg_scene.penup()
        bg_scene.color("#ffffff")
        for _ in range(25):
            bg_scene.goto(rng.randint(-280, 280), rng.randint(-120, 270))
            bg_scene.dot(3)
    else:
        bg_scene.color(theme["accent"])
        for r in (35, 60, 90, 125):
            bg_scene.goto(-170 + r, 120)
            bg_scene.pendown()
            bg_scene.circle(r)
            bg_scene.penup()

    # Subtle patterned overlay.
    bg_accent.color(theme["grid"])
    bg_accent.pensize(1)

    if level == 1:
        # Keep level 1 intentionally minimal.
        for x in (-200, 0, 200):
            bg_accent.goto(x, -295)
            bg_accent.setheading(90)
            bg_accent.pendown()
            bg_accent.forward(590)
            bg_accent.penup()

        for y in (-200, 0, 200):
            bg_accent.goto(-295, y)
            bg_accent.setheading(0)
            bg_accent.pendown()
            bg_accent.forward(590)
            bg_accent.penup()

        bg_accent.color(theme["grid"])
        bg_accent.goto(-295, 295)
        bg_accent.setheading(0)
        bg_accent.pensize(4)
        bg_accent.pendown()
        for _ in range(4):
            bg_accent.forward(590)
            bg_accent.right(90)
        bg_accent.penup()
        return

    for x in range(-260, 281, 95):
        bg_accent.goto(x, -295)
        bg_accent.setheading(90)
        bg_accent.pendown()
        bg_accent.forward(590)
        bg_accent.penup()

    for y in range(-260, 281, 95):
        bg_accent.goto(-295, y)
        bg_accent.setheading(0)
        bg_accent.pendown()
        bg_accent.forward(590)
        bg_accent.penup()

    bg_accent.color(theme["accent"])
    for x in range(-240, 241, 120):
        for y in range(-240, 241, 120):
            bg_accent.goto(x, y)
            bg_accent.dot(7)

    # Fixed border.
    bg_accent.color(theme["grid"])
    bg_accent.goto(-295, 295)
    bg_accent.setheading(0)
    bg_accent.pensize(4)
    bg_accent.pendown()
    for _ in range(4):
        bg_accent.forward(590)
        bg_accent.right(90)
    bg_accent.penup()


draw_terrain(1)


def register_heart_shape():
    heart = []
    scale = 5
    for i in range(0, 360, 8):
        angle = i * 3.14159265 / 180.0
        x = scale * (16 * (math.sin(angle) ** 3))
        y = scale * (
            13 * math.cos(angle)
            - 5 * math.cos(2 * angle)
            - 2 * math.cos(3 * angle)
            - math.cos(4 * angle)
        )
        heart.append((x, y))
    screen.register_shape("heart", tuple(heart))


register_heart_shape()

# Player
player = turtle.Turtle()
player.shape("square")
player.color("blue")
player.penup()
player.goto(-240, -240)
player.hideturtle()

# Food
food = turtle.Turtle()
food.shape("circle")
food.color("#ffd166")
food.shapesize(1.8, 1.8)
food.penup()
food.goto(random_position())
food.showturtle()

# Enemy (Monster)
enemy = turtle.Turtle()
enemy.shape("triangle")
enemy.color("red")
enemy.penup()
enemy.goto(240, 240)
enemy.setheading(90)
enemy.hideturtle()

# Fierce enemy (appears after level 5)
gorilla_enemy = turtle.Turtle()
gorilla_enemy.shape("triangle")
gorilla_enemy.color("#5a3d2b")
gorilla_enemy.penup()
gorilla_enemy.goto(220, -220)
gorilla_enemy.hideturtle()

# Icon renderers for player/enemy
player_icon = turtle.Turtle()
player_icon.hideturtle()
player_icon.penup()

enemy_icon = turtle.Turtle()
enemy_icon.hideturtle()
enemy_icon.penup()

gorilla_icon = turtle.Turtle()
gorilla_icon.hideturtle()
gorilla_icon.penup()

fire_icon = turtle.Turtle()
fire_icon.hideturtle()
fire_icon.penup()

pothole_icon = turtle.Turtle()
pothole_icon.hideturtle()
pothole_icon.penup()

trap_icon = turtle.Turtle()
trap_icon.hideturtle()
trap_icon.penup()

food_icon = turtle.Turtle()
food_icon.hideturtle()
food_icon.penup()

mega_food_icon = turtle.Turtle()
mega_food_icon.hideturtle()
mega_food_icon.penup()

weapon_icon = turtle.Turtle()
weapon_icon.hideturtle()
weapon_icon.penup()

# Obstacles
# Fire
fire = turtle.Turtle()
fire.shape("circle")
fire.color("orange")
fire.penup()
fire.goto(random_position())
fire.hideturtle()

# Pothole
pothole = turtle.Turtle()
pothole.shape("square")
pothole.color("black")
pothole.penup()
pothole.goto(random_position())
pothole.hideturtle()

# Trap
trap = turtle.Turtle()
trap.shape("triangle")
trap.color("purple")
trap.penup()
trap.goto(random_position())
trap.hideturtle()

# Bonus life (heart)
life_bonus = turtle.Turtle()
life_bonus.shape("heart")
life_bonus.color("hot pink")
life_bonus.penup()
life_bonus.hideturtle()

# Mega food
mega_food = turtle.Turtle()
mega_food.shape("circle")
mega_food.shapesize(1.6, 1.6)
mega_food.color("gold")
mega_food.penup()
mega_food.hideturtle()

# Weapon drops (one per slot/type)
weapon_drop_arrow = turtle.Turtle()
weapon_drop_arrow.shape("circle")
weapon_drop_arrow.color("silver")
weapon_drop_arrow.penup()
weapon_drop_arrow.hideturtle()

weapon_drop_gun = turtle.Turtle()
weapon_drop_gun.shape("circle")
weapon_drop_gun.color("silver")
weapon_drop_gun.penup()
weapon_drop_gun.hideturtle()

weapon_drop_capture = turtle.Turtle()
weapon_drop_capture.shape("circle")
weapon_drop_capture.color("silver")
weapon_drop_capture.penup()
weapon_drop_capture.hideturtle()

# Score
score = 0
lives = 3
level = 1
game_over = False
paused = False
next_life_spawn_time = None
life_bonus_expire_time = None
mega_food_expire_time = None
weapon_respawn_time = None
weapon_slots = [False, False, False]
selected_weapon_slot = 0
gun_bullets = 0
capture_charges = 0
fire_requested = False
kill_streak = 0
last_kill_time = None
move_speed = BASE_MOVE_SPEED
enemy_speed = BASE_ENEMY_SPEED
keys_pressed = {"Up": False, "Down": False, "Left": False, "Right": False}
pickup_radius = 28
terrain_label = TERRAIN_THEMES[0]["label"]

# Score display
score_display = turtle.Turtle()
score_display.hideturtle()
score_display.penup()
score_display.goto(70, 255)

level_display = turtle.Turtle()
level_display.hideturtle()
level_display.penup()
level_display.goto(205, 255)

weapon_display = turtle.Turtle()
weapon_display.hideturtle()
weapon_display.penup()
weapon_display.goto(205, 236)

title_display = turtle.Turtle()
title_display.hideturtle()
title_display.penup()
title_display.color(HUD_BORDER)
title_display.goto(0, 289)
title_display.write("ULTIMATE COLLECT", align="center", font=("Segoe UI", 14, "bold"))

# Lives panel (top-left)
lives_panel = turtle.Turtle()
lives_panel.hideturtle()
lives_panel.speed(0)
lives_panel.penup()
lives_panel.color(HUD_BORDER, HUD_FILL)


def draw_panel(pen, x, y, width, height, border, fill):
    pen.penup()
    pen.goto(x, y)
    pen.color(border, fill)
    pen.pensize(2)
    pen.pendown()
    pen.begin_fill()
    for _ in range(2):
        pen.forward(width)
        pen.right(90)
        pen.forward(height)
        pen.right(90)
    pen.end_fill()
    pen.penup()


draw_panel(lives_panel, -292, 286, 220, 46, HUD_BORDER, HUD_FILL)
draw_panel(lives_panel, 72, 286, 220, 46, HUD_BORDER, HUD_FILL)

lives_display = turtle.Turtle()
lives_display.hideturtle()
lives_display.penup()
lives_display.goto(-278, 255)

status_display = turtle.Turtle()
status_display.hideturtle()
status_display.penup()
status_display.color(HUD_BORDER)
status_display.goto(0, 222)

game_over_display = turtle.Turtle()
game_over_display.hideturtle()
game_over_display.penup()
game_over_display.color("#8b0000")

event_display = turtle.Turtle()
event_display.hideturtle()
event_display.penup()
event_display.color("#b30000")

event_expire_time = None


def update_lives_display():
    hearts = " ".join(["❤"] * lives)
    if not hearts:
        hearts = "None"
    lives_display.clear()
    lives_display.write(f"Lives: {hearts}", align="left", font=("Segoe UI", 14, "bold"))


def update_score_display():
    score_display.clear()
    score_display.write(f"Score: {score:03d}", align="left", font=("Segoe UI", 14, "bold"))


def update_level_display():
    level_display.clear()
    level_display.write(f"Level: {level}", align="left", font=("Segoe UI", 14, "bold"))


def update_weapon_display():
    total_weapons = get_loaded_weapon_count()
    selected_label = weapon_name(selected_weapon_slot)
    drop_visible = weapon_drop_arrow.isvisible() or weapon_drop_gun.isvisible() or weapon_drop_capture.isvisible()
    weapon_display.clear()
    if level < WEAPON_UNLOCK_LEVEL:
        weapon_display.write("Weapon: Locked", align="left", font=("Segoe UI", 10, "normal"))
    elif total_weapons >= WEAPON_MAX_COUNT:
        weapon_display.write(f"Weapons {total_weapons}/{WEAPON_MAX_COUNT} | {selected_label}", align="left", font=("Segoe UI", 10, "bold"))
    elif drop_visible:
        weapon_display.write(f"Weapons {total_weapons}/{WEAPON_MAX_COUNT} | {selected_label} | Z pick", align="left", font=("Segoe UI", 10, "normal"))
    else:
        weapon_display.write(f"Weapons {total_weapons}/{WEAPON_MAX_COUNT} | {selected_label}", align="left", font=("Segoe UI", 10, "normal"))


def weapon_name(slot_index):
    if slot_index == 0:
        return "1: Arrow"
    if slot_index == 1:
        return f"2: Gun[{gun_bullets}]"
    return f"3: Capture[{capture_charges}]"


def get_loaded_weapon_count():
    return sum(1 for slot_index in range(WEAPON_MAX_COUNT) if weapon_slots[slot_index])


def update_hud():
    update_score_display()
    update_level_display()
    update_weapon_display()


def set_status(text):
    status_display.clear()
    status_display.write(text, align="center", font=("Segoe UI", 9, "normal"))


def show_big_event(text, duration=1.8):
    global event_expire_time
    event_display.clear()
    event_display.goto(0, 40)
    event_display.write(text, align="center", font=("Segoe UI", 22, "bold"))
    event_expire_time = time.time() + duration


def register_kill_event(target_enemy):
    global kill_streak, last_kill_time

    now = time.time()
    if last_kill_time is not None and now - last_kill_time <= KILL_STREAK_WINDOW:
        kill_streak += 1
    else:
        kill_streak = 1
    last_kill_time = now

    notes = []
    if target_enemy is gorilla_enemy:
        notes.append("GORILLA KILLED, END OF THE BEAST")

    if kill_streak >= 2:
        notes.append("EPIC!!!")
        kill_streak = 0
        last_kill_time = None

    return " | ".join(notes)


def update_terrain_from_level():
    global terrain_label
    terrain = TERRAIN_THEMES[(level - 1) % len(TERRAIN_THEMES)]
    terrain_label = terrain["label"]
    draw_terrain(level)


def spawn_mega_food():
    global mega_food_expire_time
    mega_food.goto(random_position(avoid_turtles=(player, enemy, gorilla_enemy, food, fire, pothole, trap, life_bonus, weapon_drop_arrow, weapon_drop_gun, weapon_drop_capture)))
    mega_food.showturtle()
    mega_food_expire_time = time.time() + MEGA_FOOD_DURATION


def spawn_weapon_drop(slot_index):
    if slot_index == 0:
        drop = weapon_drop_arrow
    elif slot_index == 1:
        drop = weapon_drop_gun
    else:
        drop = weapon_drop_capture

    drop.goto(random_position(avoid_turtles=(player, enemy, gorilla_enemy, food, fire, pothole, trap, life_bonus, mega_food, weapon_drop_arrow, weapon_drop_gun, weapon_drop_capture)))
    drop.showturtle()


def reset_player_position():
    player.goto(-240, -240)
    enemy.goto(240, 240)
    if level >= 5:
        gorilla_enemy.goto(-240, 240)


def active_enemies():
    enemies = [enemy]
    if level >= 5:
        enemies.append(gorilla_enemy)
    return enemies


def relocate_traps():
    place_turtle_randomly(fire, avoid_turtles=(player, enemy, food, pothole, trap, life_bonus, mega_food, gorilla_enemy, weapon_drop_arrow, weapon_drop_gun, weapon_drop_capture))
    place_turtle_randomly(pothole, avoid_turtles=(player, enemy, food, fire, trap, life_bonus, mega_food, gorilla_enemy, weapon_drop_arrow, weapon_drop_gun, weapon_drop_capture))
    place_turtle_randomly(trap, avoid_turtles=(player, enemy, food, fire, pothole, life_bonus, mega_food, gorilla_enemy, weapon_drop_arrow, weapon_drop_gun, weapon_drop_capture))


def move_enemy_towards_target(chaser, target, speed):
    if chaser.xcor() < target.xcor():
        chaser.setx(chaser.xcor() + speed)
    if chaser.xcor() > target.xcor():
        chaser.setx(chaser.xcor() - speed)
    if chaser.ycor() < target.ycor():
        chaser.sety(chaser.ycor() + speed)
    if chaser.ycor() > target.ycor():
        chaser.sety(chaser.ycor() - speed)


def draw_icons():
    player_icon.clear()
    enemy_icon.clear()
    gorilla_icon.clear()
    fire_icon.clear()
    pothole_icon.clear()
    trap_icon.clear()
    food_icon.clear()
    mega_food_icon.clear()
    weapon_icon.clear()

    player_icon.goto(player.xcor(), player.ycor())
    player_icon.write("😀", align="center", font=("Segoe UI Emoji", 20, "normal"))

    enemy_icon.goto(enemy.xcor(), enemy.ycor())
    enemy_icon.write("😈", align="center", font=("Segoe UI Emoji", 22, "normal"))

    if level >= 5:
        gorilla_icon.goto(gorilla_enemy.xcor(), gorilla_enemy.ycor())
        gorilla_icon.write("🦍", align="center", font=("Segoe UI Emoji", 22, "normal"))

    fire_icon.goto(fire.xcor(), fire.ycor())
    fire_icon.write("🔥", align="center", font=("Segoe UI Emoji", 20, "normal"))

    pothole_icon.goto(pothole.xcor(), pothole.ycor())
    pothole_icon.write("🕳", align="center", font=("Segoe UI Emoji", 20, "normal"))

    trap_icon.goto(trap.xcor(), trap.ycor())
    trap_icon.write("⚠", align="center", font=("Segoe UI Emoji", 20, "normal"))

    food_icon.goto(food.xcor(), food.ycor())
    food_icon.write("🍪", align="center", font=("Segoe UI Emoji", 20, "normal"))

    if mega_food.isvisible():
        mega_food_icon.goto(mega_food.xcor(), mega_food.ycor())
        mega_food_icon.write("🌟", align="center", font=("Segoe UI Emoji", 24, "normal"))

    if weapon_drop_arrow.isvisible():
        weapon_icon.goto(weapon_drop_arrow.xcor(), weapon_drop_arrow.ycor())
        weapon_icon.write("🏹", align="center", font=("Segoe UI Emoji", 22, "normal"))
    if weapon_drop_gun.isvisible():
        weapon_icon.goto(weapon_drop_gun.xcor(), weapon_drop_gun.ycor())
        weapon_icon.write("🔫", align="center", font=("Segoe UI Emoji", 22, "normal"))
    if weapon_drop_capture.isvisible():
        weapon_icon.goto(weapon_drop_capture.xcor(), weapon_drop_capture.ycor())
        weapon_icon.write("🛸", align="center", font=("Segoe UI Emoji", 22, "normal"))


def lose_life(reason):
    global lives, game_over, next_life_spawn_time, life_bonus_expire_time, mega_food_expire_time, weapon_slots, selected_weapon_slot, weapon_respawn_time, gun_bullets, capture_charges, kill_streak, last_kill_time, event_expire_time

    lives -= 1
    update_lives_display()

    if lives <= 0:
        game_over_display.clear()
        game_over_display.goto(0, 0)
        game_over_display.write("GAME OVER", align="center", font=("Segoe UI", 28, "bold"))
        set_status("Press R or Space to play again")
        game_over = True
        return

    # Schedule a heart to appear 10 seconds after losing a life.
    next_life_spawn_time = time.time() + 10
    life_bonus_expire_time = None
    mega_food_expire_time = None
    life_bonus.hideturtle()
    mega_food.hideturtle()
    weapon_drop_arrow.hideturtle()
    weapon_drop_gun.hideturtle()
    weapon_drop_capture.hideturtle()
    weapon_slots = [False, False, False]
    selected_weapon_slot = 0
    gun_bullets = 0
    capture_charges = 0
    kill_streak = 0
    last_kill_time = None
    event_display.clear()
    event_expire_time = None
    if level >= WEAPON_UNLOCK_LEVEL:
        weapon_respawn_time = time.time() + 3
    reset_player_position()
    set_status("Life lost. A bonus heart appears in 10s for 5s.")
    update_weapon_display()


def restart_game():
    global score, lives, level, game_over, paused, next_life_spawn_time, life_bonus_expire_time, mega_food_expire_time, weapon_respawn_time, weapon_slots, selected_weapon_slot, gun_bullets, capture_charges, kill_streak, last_kill_time, event_expire_time, move_speed, enemy_speed

    score = 0
    lives = 3
    level = 1
    game_over = False
    paused = False
    next_life_spawn_time = None
    life_bonus_expire_time = None
    mega_food_expire_time = None
    weapon_respawn_time = None
    weapon_slots = [False, False, False]
    selected_weapon_slot = 0
    gun_bullets = 0
    capture_charges = 0
    kill_streak = 0
    last_kill_time = None
    event_expire_time = None
    move_speed = BASE_MOVE_SPEED
    enemy_speed = BASE_ENEMY_SPEED

    life_bonus.hideturtle()
    mega_food.hideturtle()
    weapon_drop_arrow.hideturtle()
    weapon_drop_gun.hideturtle()
    weapon_drop_capture.hideturtle()
    reset_player_position()
    update_terrain_from_level()

    player.goto(random_position())
    enemy.goto(random_position(avoid_turtles=(player,)))
    gorilla_enemy.goto(random_position(avoid_turtles=(player, enemy)))
    food.goto(random_position(avoid_turtles=(player, enemy, gorilla_enemy)))
    fire.goto(random_position(avoid_turtles=(player, enemy, gorilla_enemy, food)))
    pothole.goto(random_position(avoid_turtles=(player, enemy, gorilla_enemy, food, fire)))
    trap.goto(random_position(avoid_turtles=(player, enemy, gorilla_enemy, food, fire, pothole)))

    game_over_display.clear()
    event_display.clear()
    update_hud()
    update_lives_display()
    set_status("")
    draw_icons()


def toggle_pause():
    global paused
    if game_over:
        return
    paused = not paused
    if paused:
        set_status("Paused. Press P to resume")
    else:
        set_status("Resumed")


update_lives_display()
update_hud()
set_status("")
draw_icons()

# Movement functions
def move_up():
    if game_over or paused:
        return
    keys_pressed["Up"] = True

def move_down():
    if game_over or paused:
        return
    keys_pressed["Down"] = True

def move_left():
    if game_over or paused:
        return
    keys_pressed["Left"] = True

def move_right():
    if game_over or paused:
        return
    keys_pressed["Right"] = True


def pickup_weapon_action():
    global weapon_slots, gun_bullets, capture_charges

    if game_over or paused or level < WEAPON_UNLOCK_LEVEL:
        return

    picked = False

    if weapon_drop_arrow.isvisible() and player.distance(weapon_drop_arrow) < 26 and not weapon_slots[0]:
        weapon_slots[0] = True
        weapon_drop_arrow.hideturtle()
        set_status("Picked 1: Arrow")
        picked = True

    if weapon_drop_gun.isvisible() and player.distance(weapon_drop_gun) < 26 and not weapon_slots[1]:
        weapon_slots[1] = True
        gun_bullets = GUN_BULLETS_PER_PICKUP
        weapon_drop_gun.hideturtle()
        set_status(f"Picked 2: Gun ({GUN_BULLETS_PER_PICKUP} bullets)")
        picked = True

    if weapon_drop_capture.isvisible() and player.distance(weapon_drop_capture) < 26 and not weapon_slots[2]:
        weapon_slots[2] = True
        capture_charges = 1
        weapon_drop_capture.hideturtle()
        set_status("Picked 3: Capture gun")
        picked = True

    if picked:
        update_weapon_display()


def select_weapon_slot(slot_index):
    global selected_weapon_slot

    if game_over or paused:
        return

    selected_weapon_slot = slot_index
    update_weapon_display()
    if weapon_slots[slot_index]:
        set_status(f"Selected {weapon_name(slot_index)}: READY")
    else:
        set_status(f"Selected {weapon_name(slot_index)}: EMPTY")


def select_weapon_1():
    select_weapon_slot(0)


def select_weapon_2():
    select_weapon_slot(1)


def select_weapon_3():
    select_weapon_slot(2)


def fire_weapon_action():
    global fire_requested
    if game_over or paused:
        return
    fire_requested = True


def stop_up():
    keys_pressed["Up"] = False


def stop_down():
    keys_pressed["Down"] = False


def stop_left():
    keys_pressed["Left"] = False


def stop_right():
    keys_pressed["Right"] = False

# Key bindings
screen.listen()
screen.onkeypress(move_up, "Up")
screen.onkeypress(move_down, "Down")
screen.onkeypress(move_left, "Left")
screen.onkeypress(move_right, "Right")
screen.onkeypress(move_up, "w")
screen.onkeypress(move_up, "W")
screen.onkeypress(move_down, "s")
screen.onkeypress(move_down, "S")
screen.onkeypress(move_left, "a")
screen.onkeypress(move_left, "A")
screen.onkeypress(move_right, "d")
screen.onkeypress(move_right, "D")
screen.onkeyrelease(stop_up, "Up")
screen.onkeyrelease(stop_down, "Down")
screen.onkeyrelease(stop_left, "Left")
screen.onkeyrelease(stop_right, "Right")
screen.onkeyrelease(stop_up, "w")
screen.onkeyrelease(stop_up, "W")
screen.onkeyrelease(stop_down, "s")
screen.onkeyrelease(stop_down, "S")
screen.onkeyrelease(stop_left, "a")
screen.onkeyrelease(stop_left, "A")
screen.onkeyrelease(stop_right, "d")
screen.onkeyrelease(stop_right, "D")
screen.onkey(toggle_pause, "p")
screen.onkey(toggle_pause, "P")
screen.onkey(restart_game, "r")
screen.onkey(restart_game, "R")
screen.onkey(restart_game, "space")
screen.onkey(pickup_weapon_action, "z")
screen.onkey(pickup_weapon_action, "Z")
screen.onkey(select_weapon_1, "1")
screen.onkey(select_weapon_2, "2")
screen.onkey(select_weapon_3, "3")
screen.onkeypress(fire_weapon_action, "x")
screen.onkeypress(fire_weapon_action, "X")

# Game loop
def game_loop():
    global score, game_over, next_life_spawn_time, life_bonus_expire_time, mega_food_expire_time, weapon_respawn_time, weapon_slots, selected_weapon_slot, gun_bullets, capture_charges, fire_requested, event_expire_time, lives, level, move_speed, enemy_speed

    if game_over:
        return

    if paused:
        draw_icons()
        screen.update()
        screen.ontimer(game_loop, 16)
        return

    screen.update()

    current_time = time.time()

    if keys_pressed["Up"]:
        player.sety(min(280, player.ycor() + move_speed))
    if keys_pressed["Down"]:
        player.sety(max(-280, player.ycor() - move_speed))
    if keys_pressed["Left"]:
        player.setx(max(-280, player.xcor() - move_speed))
    if keys_pressed["Right"]:
        player.setx(min(280, player.xcor() + move_speed))

    if event_expire_time is not None and current_time >= event_expire_time:
        event_display.clear()
        event_expire_time = None

    # Spawn heart 10 seconds after a life loss and keep it visible for 5 seconds.
    if next_life_spawn_time is not None and current_time >= next_life_spawn_time:
        life_bonus.goto(random_position(avoid_turtles=(player, enemy, gorilla_enemy, food, fire, pothole, trap, weapon_drop_arrow, weapon_drop_gun, weapon_drop_capture)))
        life_bonus.showturtle()
        life_bonus_expire_time = current_time + 5
        next_life_spawn_time = None

    if life_bonus.isvisible() and life_bonus_expire_time is not None and current_time >= life_bonus_expire_time:
        life_bonus.hideturtle()
        life_bonus_expire_time = None

    if mega_food.isvisible() and mega_food_expire_time is not None and current_time >= mega_food_expire_time:
        mega_food.hideturtle()
        mega_food_expire_time = None

    if level >= WEAPON_UNLOCK_LEVEL:
        for slot_index in range(WEAPON_MAX_COUNT):
            if not weapon_slots[slot_index]:
                if weapon_respawn_time is None:
                    weapon_respawn_time = current_time + 2
                elif current_time >= weapon_respawn_time:
                    if slot_index == 0 and not weapon_drop_arrow.isvisible():
                        spawn_weapon_drop(0)
                        weapon_respawn_time = None
                    if slot_index == 1 and not weapon_drop_gun.isvisible():
                        spawn_weapon_drop(1)
                        weapon_respawn_time = None
                    if slot_index == 2 and not weapon_drop_capture.isvisible():
                        spawn_weapon_drop(2)
                        weapon_respawn_time = None
        update_weapon_display()

    # Food collision
    if player.distance(food) < 20:
        place_turtle_randomly(food, avoid_turtles=(player, enemy, gorilla_enemy, fire, pothole, trap, life_bonus, weapon_drop_arrow, weapon_drop_gun, weapon_drop_capture))
        score += 1
        relocate_traps()
        if score % MEGA_FOOD_SCORE == 0:
            spawn_mega_food()
            set_status(f"Mega food is out for {MEGA_FOOD_DURATION} seconds")
        else:
            set_status("Yum! Traps switched places")

        new_level = score // LEVEL_UP_SCORE + 1
        if new_level != level:
            level = new_level
            move_speed = BASE_MOVE_SPEED
            enemy_speed = BASE_ENEMY_SPEED
            update_terrain_from_level()
            if level >= 5:
                set_status(f"Level {level}: {terrain_label} terrain | New fierce enemies unleashed")
            elif level >= WEAPON_UNLOCK_LEVEL:
                set_status(f"Level {level}: Weapon unlocked. Pick up ⚔ to slay enemies")
            else:
                set_status(f"Level {level}: {terrain_label} terrain")
        update_hud()

    if mega_food.isvisible() and player.distance(mega_food) < 24:
        mega_food.hideturtle()
        mega_food_expire_time = None
        score += 3
        update_hud()
        set_status("Mega food bonus collected")
        new_level = score // LEVEL_UP_SCORE + 1
        if new_level != level:
            level = new_level
            move_speed = BASE_MOVE_SPEED
            enemy_speed = BASE_ENEMY_SPEED
            update_terrain_from_level()
            set_status(f"Level {level}: {terrain_label} terrain")
            update_hud()

    # Enemy movement
    move_enemy_towards_target(enemy, player, enemy_speed)
    if level >= 5:
        move_enemy_towards_target(gorilla_enemy, player, enemy_speed + GORILLA_SPEED_BONUS)

    # Collect bonus life first so it is not lost to same-frame enemy/obstacle hits.
    if life_bonus.isvisible() and player.distance(life_bonus) < pickup_radius:
        life_bonus.hideturtle()
        life_bonus_expire_time = None
        next_life_spawn_time = None
        if lives < 3:
            lives += 1
            update_lives_display()
            set_status("Life regained")

    if fire_requested:
        fire_requested = False
        in_range_enemies = [current_enemy for current_enemy in active_enemies() if player.distance(current_enemy) < 260]
        target_enemy = min(in_range_enemies, key=lambda current_enemy: player.distance(current_enemy)) if in_range_enemies else None

        if target_enemy is None:
            set_status("No enemy in range to fire")
        elif selected_weapon_slot == 0 and weapon_slots[0]:
            weapon_slots[0] = False
            score += WEAPON_SCORE_BONUS
            place_turtle_randomly(target_enemy, avoid_turtles=(player, enemy, gorilla_enemy, food, fire, pothole, trap, life_bonus, mega_food, weapon_drop_arrow, weapon_drop_gun, weapon_drop_capture))
            update_hud()
            remaining_weapons = get_loaded_weapon_count()
            kill_note = register_kill_event(target_enemy)
            message = f"Arrow fired! +{WEAPON_SCORE_BONUS} points | Weapons left: {remaining_weapons}"
            if kill_note:
                message += f" | {kill_note}"
                show_big_event(kill_note.replace(" | ", "\n"))
            set_status(message)
            if level >= WEAPON_UNLOCK_LEVEL and remaining_weapons < WEAPON_MAX_COUNT:
                weapon_respawn_time = time.time() + 3
        elif selected_weapon_slot == 1 and weapon_slots[1] and gun_bullets > 0:
            gun_bullets -= 1
            score += WEAPON_SCORE_BONUS
            place_turtle_randomly(target_enemy, avoid_turtles=(player, enemy, gorilla_enemy, food, fire, pothole, trap, life_bonus, mega_food, weapon_drop_arrow, weapon_drop_gun, weapon_drop_capture))
            if gun_bullets <= 0:
                weapon_slots[1] = False
                gun_bullets = 0
            update_hud()
            remaining_weapons = get_loaded_weapon_count()
            kill_note = register_kill_event(target_enemy)
            message = f"Gun fired! +{WEAPON_SCORE_BONUS} points | Bullets: {gun_bullets}"
            if kill_note:
                message += f" | {kill_note}"
                show_big_event(kill_note.replace(" | ", "\n"))
            set_status(message)
            if level >= WEAPON_UNLOCK_LEVEL and remaining_weapons < WEAPON_MAX_COUNT:
                weapon_respawn_time = time.time() + 3
        elif selected_weapon_slot == 2 and weapon_slots[2] and capture_charges > 0:
            if target_enemy is enemy:
                capture_charges -= 1
                score += WEAPON_SCORE_BONUS
                place_turtle_randomly(enemy, avoid_turtles=(player, gorilla_enemy, food, fire, pothole, trap, life_bonus, mega_food, weapon_drop_arrow, weapon_drop_gun, weapon_drop_capture))
                if capture_charges <= 0:
                    weapon_slots[2] = False
                    capture_charges = 0
                update_hud()
                remaining_weapons = get_loaded_weapon_count()
                kill_note = register_kill_event(target_enemy)
                message = f"Ghost captured! +{WEAPON_SCORE_BONUS} points"
                if kill_note:
                    message += f" | {kill_note}"
                    show_big_event(kill_note.replace(" | ", "\n"))
                set_status(message)
                if level >= WEAPON_UNLOCK_LEVEL and remaining_weapons < WEAPON_MAX_COUNT:
                    weapon_respawn_time = time.time() + 3
            else:
                set_status("Capture gun works only on the devil ghost")
        else:
            set_status("Selected weapon slot is empty")

    draw_icons()

    # Enemy collision
    hit_enemy = next((current_enemy for current_enemy in active_enemies() if player.distance(current_enemy) < 20), None)
    if hit_enemy is not None:
        lose_life("Monster")
        if not game_over:
            draw_icons()
            screen.ontimer(game_loop, 16)
        return

    # Obstacle collision
    if (player.distance(fire) < 20 or 
        player.distance(pothole) < 20 or 
        player.distance(trap) < 20):

        lose_life("Obstacle")
        if not game_over:
            draw_icons()
            screen.ontimer(game_loop, 16)
        return

    screen.ontimer(game_loop, 16)

game_loop()
turtle.done()
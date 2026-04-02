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
BASE_MOVE_SPEED = 4
BASE_ENEMY_SPEED = 1
MIN_SPAWN_DISTANCE = 70
TERRAIN_THEMES = [
    {"bg": "#d9f7d9", "grid": "#184d2f", "accent": "#2d8a57", "label": "GRASSLAND"},
    {"bg": "#efe0b8", "grid": "#7a4a12", "accent": "#b06b1f", "label": "DUNES"},
    {"bg": "#dcecff", "grid": "#24507a", "accent": "#4f84ba", "label": "FROST"},
    {"bg": "#f0d8d8", "grid": "#7a1f1f", "accent": "#d14b4b", "label": "EMBER"},
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
    bg_accent.hideturtle()
    bg_accent.speed(0)
    bg_accent.penup()
    bg_accent.color(theme["grid"])

    bg_accent.goto(-295, 295)
    bg_accent.pendown()
    bg_accent.pensize(4)
    for _ in range(4):
        bg_accent.forward(590)
        bg_accent.right(90)

    bg_accent.penup()
    bg_accent.pensize(1)

    if level % 2 == 1:
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
    else:
        for offset in range(-320, 321, 80):
            bg_accent.goto(-295, offset)
            bg_accent.setheading(20)
            bg_accent.pendown()
            bg_accent.forward(690)
            bg_accent.penup()

            bg_accent.goto(295, offset)
            bg_accent.setheading(200)
            bg_accent.pendown()
            bg_accent.forward(690)
            bg_accent.penup()

    bg_accent.color(theme["accent"])
    for x in range(-220, 221, 110):
        for y in range(-220, 221, 110):
            bg_accent.goto(x, y)
            bg_accent.dot(10)


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
food.color("tan")
food.penup()
food.goto(random_position())
food.hideturtle()

# Enemy (Monster)
enemy = turtle.Turtle()
enemy.shape("triangle")
enemy.color("red")
enemy.penup()
enemy.goto(240, 240)
enemy.setheading(90)
enemy.hideturtle()

# Icon renderers for player/enemy
player_icon = turtle.Turtle()
player_icon.hideturtle()
player_icon.penup()

enemy_icon = turtle.Turtle()
enemy_icon.hideturtle()
enemy_icon.penup()

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

# Score
score = 0
lives = 3
level = 1
game_over = False
paused = False
next_life_spawn_time = None
life_bonus_expire_time = None
mega_food_expire_time = None
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
status_display.goto(0, -284)

game_over_display = turtle.Turtle()
game_over_display.hideturtle()
game_over_display.penup()
game_over_display.color("#8b0000")


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


def update_hud():
    update_score_display()
    update_level_display()


def set_status(text):
    status_display.clear()
    status_display.write(text, align="center", font=("Segoe UI", 10, "normal"))


def update_terrain_from_level():
    global terrain_label
    terrain = TERRAIN_THEMES[(level - 1) % len(TERRAIN_THEMES)]
    terrain_label = terrain["label"]
    draw_terrain(level)


def spawn_mega_food():
    global mega_food_expire_time
    mega_food.goto(random_position(avoid_turtles=(player, enemy, food, fire, pothole, trap, life_bonus)))
    mega_food.showturtle()
    mega_food_expire_time = time.time() + MEGA_FOOD_DURATION


def reset_player_position():
    player.goto(-240, -240)
    enemy.goto(240, 240)


def draw_icons():
    player_icon.clear()
    enemy_icon.clear()
    fire_icon.clear()
    pothole_icon.clear()
    trap_icon.clear()
    food_icon.clear()
    mega_food_icon.clear()

    player_icon.goto(player.xcor(), player.ycor())
    player_icon.write("😀", align="center", font=("Segoe UI Emoji", 20, "normal"))

    enemy_icon.goto(enemy.xcor(), enemy.ycor())
    enemy_icon.write("👻", align="center", font=("Segoe UI Emoji", 20, "normal"))

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


def lose_life(reason):
    global lives, game_over, next_life_spawn_time, life_bonus_expire_time, mega_food_expire_time

    lives -= 1
    update_lives_display()

    if lives <= 0:
        game_over_display.clear()
        game_over_display.goto(0, 0)
        game_over_display.write(f"💀 GAME OVER ({reason})", align="center", font=("Segoe UI", 24, "bold"))
        set_status("Press R to restart")
        game_over = True
        return

    # Schedule a heart to appear 10 seconds after losing a life.
    next_life_spawn_time = time.time() + 10
    life_bonus_expire_time = None
    mega_food_expire_time = None
    life_bonus.hideturtle()
    mega_food.hideturtle()
    reset_player_position()
    set_status("Life lost. A bonus heart appears in 10s for 5s.")


def restart_game():
    global score, lives, level, game_over, paused, next_life_spawn_time, life_bonus_expire_time, mega_food_expire_time, move_speed, enemy_speed

    score = 0
    lives = 3
    level = 1
    game_over = False
    paused = False
    next_life_spawn_time = None
    life_bonus_expire_time = None
    mega_food_expire_time = None
    move_speed = BASE_MOVE_SPEED
    enemy_speed = BASE_ENEMY_SPEED

    life_bonus.hideturtle()
    mega_food.hideturtle()
    reset_player_position()
    update_terrain_from_level()

    player.goto(random_position())
    enemy.goto(random_position(avoid_turtles=(player,)))
    food.goto(random_position(avoid_turtles=(player, enemy)))
    fire.goto(random_position(avoid_turtles=(player, enemy, food)))
    pothole.goto(random_position(avoid_turtles=(player, enemy, food, fire)))
    trap.goto(random_position(avoid_turtles=(player, enemy, food, fire, pothole)))

    game_over_display.clear()
    update_hud()
    update_lives_display()
    set_status("Arrows move | P pause/resume | R restart | Collect hearts to regain life")
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
set_status("Arrows move | P pause/resume | R restart | Collect hearts to regain life")
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
screen.onkeyrelease(stop_up, "Up")
screen.onkeyrelease(stop_down, "Down")
screen.onkeyrelease(stop_left, "Left")
screen.onkeyrelease(stop_right, "Right")
screen.onkey(toggle_pause, "p")
screen.onkey(toggle_pause, "P")
screen.onkey(restart_game, "r")
screen.onkey(restart_game, "R")

# Game loop
def game_loop():
    global score, game_over, next_life_spawn_time, life_bonus_expire_time, mega_food_expire_time, lives, level, move_speed, enemy_speed

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

    # Spawn heart 10 seconds after a life loss and keep it visible for 5 seconds.
    if next_life_spawn_time is not None and current_time >= next_life_spawn_time:
        life_bonus.goto(random_position(avoid_turtles=(player, enemy, food, fire, pothole, trap)))
        life_bonus.showturtle()
        life_bonus_expire_time = current_time + 5
        next_life_spawn_time = None

    if life_bonus.isvisible() and life_bonus_expire_time is not None and current_time >= life_bonus_expire_time:
        life_bonus.hideturtle()
        life_bonus_expire_time = None

    if mega_food.isvisible() and mega_food_expire_time is not None and current_time >= mega_food_expire_time:
        mega_food.hideturtle()
        mega_food_expire_time = None

    # Food collision
    if player.distance(food) < 20:
        place_turtle_randomly(food, avoid_turtles=(player, enemy, fire, pothole, trap, life_bonus))
        score += 1
        if score % MEGA_FOOD_SCORE == 0:
            spawn_mega_food()
            set_status(f"Mega food is out for {MEGA_FOOD_DURATION} seconds")
        else:
            set_status("Yum! Keep collecting")

        new_level = score // LEVEL_UP_SCORE + 1
        if new_level != level:
            level = new_level
            move_speed = BASE_MOVE_SPEED + (level - 1) // 2
            enemy_speed = BASE_ENEMY_SPEED + (level - 1) // 2
            update_terrain_from_level()
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
            move_speed = BASE_MOVE_SPEED + (level - 1) // 2
            enemy_speed = BASE_ENEMY_SPEED + (level - 1) // 2
            update_terrain_from_level()
            set_status(f"Level {level}: {terrain_label} terrain")
            update_hud()

    # Enemy movement (slow chasing)
    if enemy.xcor() < player.xcor():
        enemy.setx(enemy.xcor() + enemy_speed)
    if enemy.xcor() > player.xcor():
        enemy.setx(enemy.xcor() - enemy_speed)

    if enemy.ycor() < player.ycor():
        enemy.sety(enemy.ycor() + enemy_speed)
    if enemy.ycor() > player.ycor():
        enemy.sety(enemy.ycor() - enemy_speed)

    # Collect bonus life first so it is not lost to same-frame enemy/obstacle hits.
    if life_bonus.isvisible() and player.distance(life_bonus) < pickup_radius:
        life_bonus.hideturtle()
        life_bonus_expire_time = None
        next_life_spawn_time = None
        if lives < 3:
            lives += 1
            update_lives_display()
            set_status("Life regained")

    draw_icons()

    # Enemy collision
    if player.distance(enemy) < 20:
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
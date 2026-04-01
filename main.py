import turtle
import random
import time
import math

BG_COLOR = "#d9f7d9"
GRID_COLOR = "#184d2f"
HUD_FILL = "#f4fff4"
HUD_BORDER = "#184d2f"
STATUS_FILL = "#ecffec"

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


def random_position():
    return random.randint(-260, 260), random.randint(-260, 260)


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

# Score
score = 0
lives = 3
game_over = False
paused = False
next_life_spawn_time = None
life_bonus_expire_time = None
move_speed = 4
keys_pressed = {"Up": False, "Down": False, "Left": False, "Right": False}
pickup_radius = 28

# Score display
score_display = turtle.Turtle()
score_display.hideturtle()
score_display.penup()
score_display.goto(95, 252)

title_display = turtle.Turtle()
title_display.hideturtle()
title_display.penup()
title_display.color(HUD_BORDER)
title_display.goto(0, 272)
title_display.write("ULTIMATE COLLECT", align="center", font=("Segoe UI", 16, "bold"))

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
draw_panel(lives_panel, -292, -252, 584, 40, HUD_BORDER, STATUS_FILL)

lives_display = turtle.Turtle()
lives_display.hideturtle()
lives_display.penup()
lives_display.goto(-280, 252)

status_display = turtle.Turtle()
status_display.hideturtle()
status_display.penup()
status_display.color(HUD_BORDER)
status_display.goto(0, -244)

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


def set_status(text):
    status_display.clear()
    status_display.write(text, align="center", font=("Segoe UI", 12, "normal"))


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


def lose_life(reason):
    global lives, game_over, next_life_spawn_time, life_bonus_expire_time

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
    life_bonus.hideturtle()
    reset_player_position()
    set_status("Life lost. A bonus heart appears in 10s for 5s.")


def restart_game():
    global score, lives, game_over, paused, next_life_spawn_time, life_bonus_expire_time

    score = 0
    lives = 3
    game_over = False
    paused = False
    next_life_spawn_time = None
    life_bonus_expire_time = None

    life_bonus.hideturtle()
    food.goto(random_position())
    fire.goto(random_position())
    pothole.goto(random_position())
    trap.goto(random_position())
    reset_player_position()

    game_over_display.clear()
    update_score_display()
    update_lives_display()
    set_status("Hold arrow keys to move | P pause/resume | Collect hearts to regain life")
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
update_score_display()
set_status("Hold arrow keys to move | P pause/resume | Collect hearts to regain life")
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
    global score, game_over, next_life_spawn_time, life_bonus_expire_time, lives

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
        life_bonus.goto(random_position())
        life_bonus.showturtle()
        life_bonus_expire_time = current_time + 5
        next_life_spawn_time = None

    if life_bonus.isvisible() and life_bonus_expire_time is not None and current_time >= life_bonus_expire_time:
        life_bonus.hideturtle()
        life_bonus_expire_time = None

    # Food collision
    if player.distance(food) < 20:
        food.goto(random_position())
        score += 1
        update_score_display()
        set_status("Yum! Keep collecting")

        # Optional: increase difficulty
        if score % 5 == 0:
            enemy.setx(enemy.xcor() + 2)
            set_status("Enemy speed increased")

    # Enemy movement (slow chasing)
    if enemy.xcor() < player.xcor():
        enemy.setx(enemy.xcor() + 1)
    if enemy.xcor() > player.xcor():
        enemy.setx(enemy.xcor() - 1)

    if enemy.ycor() < player.ycor():
        enemy.sety(enemy.ycor() + 1)
    if enemy.ycor() > player.ycor():
        enemy.sety(enemy.ycor() - 1)

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
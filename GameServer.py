import threading
import pygame
import socket
import sys
import random
import time
import math

# Game variables
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BORDER_WIDTH = SCREEN_WIDTH // 6  # 1/6 of screen width for each border
GAME_AREA_WIDTH = SCREEN_WIDTH - (2 * BORDER_WIDTH)  # 4/6 of screen width for game area
BUCKET_WIDTH = 80
BUCKET_HEIGHT = 60
OBJECT_SIZE = 30
INITIAL_OBJECT_SPEED = 2
INITIAL_BUCKET_SPEED = 8
DIFFICULTY_INCREASE_RATE = 0.1  # Speed increase per second
MAX_LIVES = 3

# Upgrade variables
upgrade_points = 0
bucket_size_level = 1
bucket_speed_level = 1
lives_level = 1
catch_value_level = 1

# Shared game state variables
bucket_x = BORDER_WIDTH + (GAME_AREA_WIDTH // 2) - (BUCKET_WIDTH // 2)  # Center in game area
bucket_y = SCREEN_HEIGHT - 100
target_bucket_x = bucket_x  # For smooth lerp movement
target_bucket_y = bucket_y
game_score = 0
prv_score = 0
high_score = 0
game_over = False
objects = []  # List to store falling objects (x, y, speed)
object_speed_multiplier = 1.0
bucket_speed_multiplier = 1.0
lives = MAX_LIVES
last_spawn_time = 0
game_start_time = 0

restart_requested = False
paused = False

# Lock for thread-safe access to shared variables
game_lock = threading.Lock()

def reset_game():
    # """Reset the game state for a new game."""
    global bucket_x, bucket_y, target_bucket_x, target_bucket_y, game_score, game_over, objects
    global object_speed_multiplier, bucket_speed_multiplier, lives
    global last_spawn_time, game_start_time, restart_requested
    
    with game_lock:
        bucket_x = BORDER_WIDTH + (GAME_AREA_WIDTH // 2) - (BUCKET_WIDTH // 2)  # Center in game area
        bucket_y = SCREEN_HEIGHT - 100
        target_bucket_x = bucket_x
        target_bucket_y = bucket_y
        game_score = 0
        game_over = False
        objects = []
        object_speed_multiplier = 1.0
        bucket_speed_multiplier = 1.0
        lives = MAX_LIVES + (lives_level - 1)
        last_spawn_time = pygame.time.get_ticks()
        game_start_time = pygame.time.get_ticks()
        restart_requested = False

def spawn_object():
    # """Spawn a new falling object at a random x position, avoiding corners."""
    with game_lock:
        margin = BUCKET_WIDTH // 2  # Prevent spawning too close to edges
        # Adjust x position to be within the game area
        x = random.randint(BORDER_WIDTH + OBJECT_SIZE + margin, BORDER_WIDTH + GAME_AREA_WIDTH - OBJECT_SIZE - margin)
        objects.append([x, 0, INITIAL_OBJECT_SPEED * object_speed_multiplier])

# Button class for UI elements
class Button:
    def __init__(self, x, y, width, height, text, color=(100, 100, 255), hover_color=(130, 130, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.animation_offset = 0
        
    def draw(self, screen, font):
        # Draw button with hover effect and gradient
        current_color = self.hover_color if self.is_hovered else self.color
        
        # Create gradient effect
        for i in range(self.rect.height):
            factor = i / self.rect.height
            r = int(current_color[0] * (1 - factor * 0.3))
            g = int(current_color[1] * (1 - factor * 0.3))
            b = int(current_color[2] * (1 - factor * 0.3))
            pygame.draw.line(screen, (r, g, b), 
                            (self.rect.left, self.rect.top + i), 
                            (self.rect.right, self.rect.top + i))
        
        # Add pulsing animation when hovered
        border_width = 3 if self.is_hovered else 2
        if self.is_hovered:
            self.animation_offset = (self.animation_offset + 0.05) % (2 * math.pi)
            border_width += int(math.sin(self.animation_offset) * 1.5)
        
        pygame.draw.rect(screen, (0, 0, 0), self.rect, border_width)  # Border
        
        # Render text
        text_surf = font.render(self.text, True, (0, 0, 0))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
        
    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered
        
    def is_clicked(self, mouse_pos, mouse_click):
        return self.rect.collidepoint(mouse_pos) and mouse_click

# Helper function to create gradient background for main game area
def draw_game_area_gradient(screen, border_width, time_value):
    # Draw gradient for game area only
    game_area_rect = pygame.Rect(border_width, 0, SCREEN_WIDTH - 2 * border_width, SCREEN_HEIGHT)
    
    # Create vertical gradient with subtle animation
    for y in range(SCREEN_HEIGHT):
        # Calculate color with slight wave effect
        factor = y / SCREEN_HEIGHT
        wave = (math.sin(time_value * 0.5 + factor * 2) + 1) / 8  # Subtle wave
        
        # Ensure RGB values are between 0 and 255
        r = min(255, max(0, int(135 - 20 * factor + 10 * wave)))  # Light blue to slightly darker
        g = min(255, max(0, int(206 - 20 * factor + 10 * wave)))
        b = min(255, max(0, int(250 - 10 * factor + 10 * wave)))
        
        pygame.draw.line(screen, (r, g, b), 
                        (border_width, y), 
                        (SCREEN_WIDTH - border_width, y))

# Helper function to create gradient borders
def draw_borders(screen, border_width):
    # Define border rectangles
    left_border_rect = pygame.Rect(0, 0, border_width, SCREEN_HEIGHT)
    right_border_rect = pygame.Rect(SCREEN_WIDTH - border_width, 0, border_width, SCREEN_HEIGHT)
    
    # Fill left border with solid color
    pygame.draw.rect(screen, (80, 80, 120), left_border_rect)
    
    # Fill right border with solid color
    pygame.draw.rect(screen, (80, 80, 120), right_border_rect)
    
    # Draw border outlines
    pygame.draw.rect(screen, (40, 40, 80), left_border_rect, 2)
    pygame.draw.rect(screen, (40, 40, 80), right_border_rect, 2)

# Helper function to create full screen gradient for menus
def draw_full_screen_gradient(screen, top_color, bottom_color, time_value=0):
    height = screen.get_height()
    for y in range(height):
        # Calculate color for this line
        factor = y / height
        wave = (math.sin(time_value * 0.5 + factor * 2) + 1) / 8  # Subtle wave
        
        # Ensure RGB values are between 0 and 255
        r = min(255, max(0, int(top_color[0] * (1 - factor) + bottom_color[0] * factor + 10 * wave)))
        g = min(255, max(0, int(top_color[1] * (1 - factor) + bottom_color[1] * factor + 10 * wave)))
        b = min(255, max(0, int(top_color[2] * (1 - factor) + bottom_color[2] * factor + 10 * wave)))
        
        pygame.draw.line(screen, (r, g, b), (0, y), (screen.get_width(), y))

#Start Screen
def play_screen(screen, font):
    global high_score, upgrade_points
    
    # Create buttons
    play_button = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, 200, 60, "Play")
    upgrade_button = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 30, 200, 60, "Upgrades")
    
    title_font = pygame.font.SysFont('Arial', 60, bold=True)
    start_time = pygame.time.get_ticks() / 1000.0  # For animations
    
    while True:
        current_time = pygame.time.get_ticks() / 1000.0
        animation_time = current_time - start_time
        
        # Handle events
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_clicked = True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                return  # Keep space key functionality
        
        # Check button interactions
        play_button.check_hover(mouse_pos)
        upgrade_button.check_hover(mouse_pos)
        
        if play_button.is_clicked(mouse_pos, mouse_clicked):
            return  # Start the game
        
        if upgrade_button.is_clicked(mouse_pos, mouse_clicked):
            upgrade_screen(screen, font)  # Go to upgrade screen
        
        # Draw the screen with full screen gradient (no borders)
        draw_full_screen_gradient(screen, (135, 206, 250), (100, 180, 255), animation_time)
        
        # Draw title with subtle animation
        title_text = title_font.render("Bucket Catch Game", True, (0, 0, 0))
        title_y_offset = math.sin(animation_time * 2) * 5  # Gentle floating effect
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 
                                SCREEN_HEIGHT // 4 + title_y_offset))
        
        # Draw score and upgrade points
        score_text = font.render(f"High Score: {high_score}   Upgrade Points: {upgrade_points}", True, (0, 0, 0))
        screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 3 + 20))
        
        # Draw buttons
        play_button.draw(screen, font)
        upgrade_button.draw(screen, font)
        
        # Add hint text
        hint_font = pygame.font.SysFont('Arial', 20)
        hint_text = hint_font.render("Press SPACE to start immediately", True, (80, 80, 80))
        screen.blit(hint_text, (SCREEN_WIDTH // 2 - hint_text.get_width() // 2, SCREEN_HEIGHT - 50))
        
        pygame.display.flip()
        pygame.time.delay(10)  # Small delay to reduce CPU usage

# Upgrade screen
def upgrade_screen(screen, font):
    global upgrade_points, bucket_size_level, bucket_speed_level, lives_level, catch_value_level
    global BUCKET_WIDTH, BUCKET_HEIGHT, INITIAL_BUCKET_SPEED, MAX_LIVES
    
    # Create upgrade buttons
    bucket_size_button = Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 120, 300, 50, f"Bucket Size (Level {bucket_size_level})")
    bucket_speed_button = Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 50, 300, 50, f"Bucket Speed (Level {bucket_speed_level})")
    lives_button = Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 20, 300, 50, f"Extra Lives (Level {lives_level})")
    catch_value_button = Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 90, 300, 50, f"Catch Value (Level {catch_value_level})")
    back_button = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 50, "Back to Menu")
    
    title_font = pygame.font.SysFont('Arial', 48, bold=True)
    info_font = pygame.font.SysFont('Arial', 20)
    
    start_time = pygame.time.get_ticks() / 1000.0  # For animations
    
    while True:
        current_time = pygame.time.get_ticks() / 1000.0
        animation_time = current_time - start_time
        
        # Handle events
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_clicked = True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return  # Return to main menu
        
        # Check button interactions
        bucket_size_button.check_hover(mouse_pos)
        bucket_speed_button.check_hover(mouse_pos)
        lives_button.check_hover(mouse_pos)
        catch_value_button.check_hover(mouse_pos)
        back_button.check_hover(mouse_pos)
        
        # Handle button clicks
        if bucket_size_button.is_clicked(mouse_pos, mouse_clicked) and upgrade_points > 0:
            upgrade_points -= 1
            bucket_size_level += 1
            BUCKET_WIDTH = 80 + (bucket_size_level - 1) * 10
            BUCKET_HEIGHT = 60 + (bucket_size_level - 1) * 5
            bucket_size_button.text = f"Bucket Size (Level {bucket_size_level})"
            
        if bucket_speed_button.is_clicked(mouse_pos, mouse_clicked) and upgrade_points > 0:
            upgrade_points -= 1
            bucket_speed_level += 1
            INITIAL_BUCKET_SPEED = 8 + (bucket_speed_level - 1) * 1
            bucket_speed_button.text = f"Bucket Speed (Level {bucket_speed_level})"
            
        if lives_button.is_clicked(mouse_pos, mouse_clicked) and upgrade_points > 0:
            upgrade_points -= 1
            lives_level += 1
            lives_button.text = f"Extra Lives (Level {lives_level})"
            
        if catch_value_button.is_clicked(mouse_pos, mouse_clicked) and upgrade_points > 0:
            upgrade_points -= 1
            catch_value_level += 1
            catch_value_button.text = f"Catch Value (Level {catch_value_level})"
            
        if back_button.is_clicked(mouse_pos, mouse_clicked):
            return  # Return to main menu
        
        # Draw the screen with full screen gradient (no borders)
        draw_full_screen_gradient(screen, (135, 206, 250), (100, 180, 255), animation_time)
        
        # Draw title
        title_text = title_font.render("Upgrades", True, (0, 0, 0))
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))
        
        # Draw points available
        points_text = font.render(f"Upgrade Points Available: {upgrade_points}", True, (0, 0, 0))
        screen.blit(points_text, (SCREEN_WIDTH // 2 - points_text.get_width() // 2, 120))
        
        # Draw upgrade buttons
        bucket_size_button.draw(screen, font)
        bucket_speed_button.draw(screen, font)
        lives_button.draw(screen, font)
        catch_value_button.draw(screen, font)
        back_button.draw(screen, font)
        
        # Draw upgrade descriptions
        descriptions = [
            f"Increases bucket width by 10 and height by 5",
            f"Increases bucket speed by 1",
            f"Adds 1 extra life (Current: {MAX_LIVES + (lives_level - 1)})",
            f"Increases points per catch by 1"
        ]
        
        y_pos = SCREEN_HEIGHT // 2 - 120
        for i, desc in enumerate(descriptions):
            desc_text = info_font.render(desc, True, (50, 50, 50))
            screen.blit(desc_text, (SCREEN_WIDTH // 2 + 160, y_pos + 15))
            y_pos += 70
        
        # Add hint text
        hint_text = info_font.render("Press ESC to return to menu", True, (80, 80, 80))
        screen.blit(hint_text, (SCREEN_WIDTH // 2 - hint_text.get_width() // 2, SCREEN_HEIGHT - 40))
        
        pygame.display.flip()
        pygame.time.delay(10)  # Small delay to reduce CPU usage

# Game over screen
def game_over_screen(screen, font, score):
    global high_score
    
    # Create buttons
    restart_button = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2, 200, 60, "Play Again")
    home_button = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 80, 200, 60, "Return to Menu")
    
    title_font = pygame.font.SysFont('Arial', 60, bold=True)
    start_time = pygame.time.get_ticks() / 1000.0  # For animations
    
    while True:
        current_time = pygame.time.get_ticks() / 1000.0
        animation_time = current_time - start_time
        
        # Handle events
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_clicked = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return "restart"  # Restart the game
                elif event.key == pygame.K_ESCAPE:
                    return "home"  # Return to home screen
        
        # Check button interactions
        restart_button.check_hover(mouse_pos)
        home_button.check_hover(mouse_pos)
        
        if restart_button.is_clicked(mouse_pos, mouse_clicked):
            return "restart"  # Restart the game
        
        if home_button.is_clicked(mouse_pos, mouse_clicked):
            return "home"  # Return to home screen
        
        # Draw the screen with full screen gradient (no borders)
        draw_full_screen_gradient(screen, (135, 206, 250), (100, 180, 255), animation_time)
        
        # Draw title
        title_text = title_font.render("Game Over", True, (255, 0, 0))
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 4 - 50))
        
        # Draw score
        score_text = font.render(f"Your Score: {score}", True, (0, 0, 0))
        screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 3))
        
        high_score_text = font.render(f"High Score: {high_score}", True, (0, 0, 0))
        screen.blit(high_score_text, (SCREEN_WIDTH // 2 - high_score_text.get_width() // 2, SCREEN_HEIGHT // 3 + 40))
        
        # Draw buttons
        restart_button.draw(screen, font)
        home_button.draw(screen, font)
        
        # Add hint text
        hint_font = pygame.font.SysFont('Arial', 20)
        hint_text = hint_font.render("Press R to restart or ESC to return to menu", True, (80, 80, 80))
        screen.blit(hint_text, (SCREEN_WIDTH // 2 - hint_text.get_width() // 2, SCREEN_HEIGHT - 50))
        
        pygame.display.flip()
        pygame.time.delay(10)  # Small delay to reduce CPU usage

#quit menu
def quit(screen, font):
    while True:
        screen.fill((135, 206, 235))
        font = pygame.font.SysFont('Arial', 48, bold=True)
        text = font.render("Are you sure you want to quit?", True, (0, 0, 0))
        screen.blit(text, (SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 - 200))

        #Yes or No
        yes = font.render("Press y for Yes", True, (0, 0, 0))
        screen.blit(yes, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 100))

        no = font.render("Press n for No", True, (0, 0, 0))
        screen.blit(no, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2))

        pygame.display.flip()

        #Game Loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "quit"

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:
                    print("User quiting")
                    return "restarting"
                elif event.key == pygame.K_n:
                    print("Resume game")
                    return "resume"

def GameThread():
    # """Main game thread that handles the pygame display and game logic."""
    global bucket_x, bucket_y, target_bucket_x, target_bucket_y, game_score, prv_score, high_score, game_over, objects
    global object_speed_multiplier, bucket_speed_multiplier, lives
    global last_spawn_time, game_start_time, restart_requested, paused
    global upgrade_points
    
    pygame.init()
    pygame.font.init()
    font = pygame.font.SysFont('Arial', 24)
    
    # Colors
    BLUE = (0, 120, 255)
    YELLOW = (255, 255, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    ORANGE = (255, 165, 0)
    BACKGROUND_TOP = (135, 206, 250)  # Light sky blue
    BACKGROUND_BOTTOM = (100, 180, 255)  # Slightly darker blue
    
    # Set up the display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Bucket Catch Game - Server')
    
    # Load or create game assets
    bucket_img = pygame.Surface((BUCKET_WIDTH, BUCKET_HEIGHT))
    bucket_img.fill(YELLOW)
    
    # Different colors for falling objects
    object_colors = [RED, GREEN, ORANGE, BLUE]
    
    # Game clock
    clock = pygame.time.Clock()
    
    # Animation variables
    animation_time = 0
    
    # Main game loop
    running = True
    while running:
        #play_screen
        play_screen(screen, font)
        
        # Initialize game variables
        reset_game()
        animation_start_time = pygame.time.get_ticks() / 1000.0
        
        # Game loop
        game_running = True
        while game_running and running:
            current_time = pygame.time.get_ticks()
            animation_time = pygame.time.get_ticks() / 1000.0 - animation_start_time
            
            # Handle pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    game_running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if not game_over:
                            # Return to main menu if ESC is pressed during gameplay
                            game_running = False
                        else:
                            # If game is over, ESC is handled in game_over_screen
                            pass
                
                elif paused:
                    action = quit(screen, font)
                    if action == "restarting":
                        reset_game()
                        paused = False
                    elif action == "resume":
                        paused = False
                    elif action == "quit":
                        running = False
                        game_running = False
            
            # Check for restart request
            if restart_requested:
                print("Restarting Game...")
                reset_game()
                restart_requested = False
                animation_start_time = pygame.time.get_ticks() / 1000.0
            
            # If game is not over, update game state
            if not game_over and not paused:
                # Spawn new objects periodically
                if current_time - last_spawn_time > 1000:  # Spawn every second
                    spawn_object()
                    with game_lock:
                        last_spawn_time = current_time
                
                # Increase difficulty over time
                elapsed_seconds = (current_time - game_start_time) / 1000
                with game_lock:
                    object_speed_multiplier = 1.0 + (elapsed_seconds * DIFFICULTY_INCREASE_RATE)
                    bucket_speed_multiplier = 1.0 + (elapsed_seconds * DIFFICULTY_INCREASE_RATE)
                
                # Update object positions and check for collisions
                with game_lock:
                    # Precompute bucket bounds for AABB collision
                    bucket_left = bucket_x
                    bucket_right = bucket_x + BUCKET_WIDTH
                    bucket_top = bucket_y
                    bucket_bottom = bucket_y + BUCKET_HEIGHT

                    updated_objects = []
                    for obj in objects:
                        obj_x, obj_y, obj_speed = obj
                        
                        # Move object down
                        obj_y += obj_speed
                        
                        # Calculate object bounds for AABB collision
                        obj_left = obj_x
                        obj_right = obj_x + OBJECT_SIZE
                        obj_top = obj_y
                        obj_bottom = obj_y + OBJECT_SIZE
                        
                        # Check if object is caught by bucket
                        if (obj_right > bucket_left and obj_left < bucket_right and
                            obj_bottom > bucket_top and obj_top < bucket_bottom):
                            game_score += 1 * catch_value_level
                            if game_score > high_score:
                                high_score = game_score
                            
                            # Every 10 points, award an upgrade point
                            if game_score % 10 == 0 and game_score > prv_score:
                                upgrade_points += 1
                                prv_score = game_score
                        else:
                            # Keep object if it's still in play
                            if obj_y < SCREEN_HEIGHT:
                                updated_objects.append([obj_x, obj_y, obj_speed])
                            else:
                                # Object reached bottom without being caught
                                lives -= 1
                                if lives <= 0:
                                    game_over = True
                    
                    # Update objects list
                    objects = updated_objects
                
                # Smoothly move bucket towards target position (lerp)
                with game_lock:
                    lerp_factor = 0.2  # Adjust for smoother or more responsive movement
                    bucket_x += (target_bucket_x - bucket_x) * lerp_factor
                    bucket_y += (target_bucket_y - bucket_y) * lerp_factor
                    
                    # Ensure bucket stays within screen bounds (adjusted for borders)
                    bucket_x = max(BORDER_WIDTH, min(bucket_x, BORDER_WIDTH + GAME_AREA_WIDTH - BUCKET_WIDTH))
                    bucket_y = max(0, min(bucket_y, SCREEN_HEIGHT - BUCKET_HEIGHT))
            
            # Draw solid color background first
            screen.fill((100, 100, 150))
            
            # Draw borders (solid color)
            draw_borders(screen, BORDER_WIDTH)
            
            # Draw game area with gradient
            draw_game_area_gradient(screen, BORDER_WIDTH, animation_time)
            
            # Draw bucket with subtle animation
            bucket_wobble = math.sin(animation_time * 5) * 2
            bucket_rect = pygame.Rect(bucket_x + bucket_wobble, bucket_y, BUCKET_WIDTH, BUCKET_HEIGHT)
            
            # Create gradient bucket
            for i in range(BUCKET_HEIGHT):
                factor = i / BUCKET_HEIGHT
                r = min(255, int(YELLOW[0] * (1 - factor * 0.3)))
                g = min(255, int(YELLOW[1] * (1 - factor * 0.3)))
                b = min(255, int(YELLOW[2] * (1 - factor * 0.3)))
                pygame.draw.line(screen, (r, g, b), 
                                (bucket_rect.left, bucket_rect.top + i), 
                                (bucket_rect.right, bucket_rect.top + i))
            
            # Draw bucket border
            pygame.draw.rect(screen, (0, 0, 0), bucket_rect, 2)
            
            # Draw falling objects with animation
            with game_lock:
                for i, obj in enumerate(objects):
                    obj_x, obj_y, _ = obj
                    
                    # Add slight horizontal movement based on sine wave
                    obj_wobble = math.sin((animation_time * 3) + (i * 1.5)) * 3
                    
                    # Draw object with gradient
                    obj_rect = pygame.Rect(obj_x + obj_wobble, obj_y, OBJECT_SIZE, OBJECT_SIZE)
                    for j in range(OBJECT_SIZE):
                        factor = j / OBJECT_SIZE
                        r = min(255, int(object_colors[i % len(object_colors)][0] * (1 - factor * 0.5)))
                        g = min(255, int(object_colors[i % len(object_colors)][1] * (1 - factor * 0.5)))
                        b = min(255, int(object_colors[i % len(object_colors)][2] * (1 - factor * 0.5)))
                        pygame.draw.line(screen, (r, g, b), 
                                        (obj_rect.left, obj_rect.top + j), 
                                        (obj_rect.right, obj_rect.top + j))
                    
                    # Draw object border
                    pygame.draw.rect(screen, (0, 0, 0), obj_rect, 1)
            
            # Draw score + High score (adjusted for border)
            score_text = font.render(f'Score: {game_score}', True, (0, 0, 0))
            screen.blit(score_text, (BORDER_WIDTH + 10, 10))
            high_text = font.render(f'High Score: {high_score}', True, (0, 0, 0))
            screen.blit(high_text, (BORDER_WIDTH + 10, 40))
            
            # Draw health label and boxes (adjusted for border)
            health_text = font.render("Health:", True, (0, 0, 0))
            screen.blit(health_text, (SCREEN_WIDTH - BORDER_WIDTH - 150, 10))
            
            # Draw lives as boxes with gradient
            for i in range(lives):
                health_box = pygame.Rect(SCREEN_WIDTH - BORDER_WIDTH - 30 * (i + 1), 40, 20, 20)
                
                # Create gradient health box
                for j in range(20):
                    factor = j / 20
                    r = min(255, int(RED[0] * (1 - factor * 0.3)))
                    g = min(255, int(RED[1] * (1 - factor * 0.3)))
                    b = min(255, int(RED[2] * (1 - factor * 0.3)))
                    pygame.draw.line(screen, (r, g, b), 
                                    (health_box.left, health_box.top + j), 
                                    (health_box.right, health_box.top + j))
                
                # Draw box border
                pygame.draw.rect(screen, (0, 0, 0), health_box, 1)
            
            # Draw game over message
            if game_over:
                # Show game over screen and get action
                action = game_over_screen(screen, font, game_score)
                if action == "restart":
                    reset_game()
                    animation_start_time = pygame.time.get_ticks() / 1000.0
                elif action == "home":
                    game_running = False  # Return to main menu
            
            # Update the display
            pygame.display.flip()
            
            # Cap the frame rate
            clock.tick(60)
    
    # Quit pygame when done
    pygame.quit()

def ServerThread():
    # """Server thread that handles client connections and processes input."""
    global bucket_x, bucket_y, target_bucket_x, target_bucket_y, game_over, restart_requested, paused
    
    # Get the hostname
    host = "127.0.0.1"  # Default to localhost
    
    # Try to get the actual IP address
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        host = s.getsockname()[0]
        s.close()
    except:
        print("Could not determine IP address, using localhost")
    
    port = 5000  # Port number above 1024
    
    print(f"Server starting on {host}:{port}")
    
    server_socket = socket.socket()  # Create socket instance
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow address reuse
    
    try:
        # Bind host address and port
        server_socket.bind((host, port))
        print("Server enabled...")
        
        # Configure how many clients the server can listen to simultaneously
        server_socket.listen(2)
        print("Waiting for client connection...")
        
        while True:
            conn, address = server_socket.accept()  # Accept new connection
            print(f"Connection from: {address}")
            
            try:
                # Process client input
                while True:
                    # Receive data stream
                    data = conn.recv(1024).decode()
                    if not data:
                        break
                    
                    # Process received command
                    print(f"From client: {data}")
                    
                    with game_lock:
                        bucket_speed = INITIAL_BUCKET_SPEED * bucket_speed_multiplier
                        
                        if data == 'w':  # Move up
                            target_bucket_y = max(SCREEN_HEIGHT // 2, target_bucket_y - bucket_speed)
                        elif data == 's':  # Move down
                            target_bucket_y = min(SCREEN_HEIGHT - BUCKET_HEIGHT, target_bucket_y + bucket_speed)
                        elif data == 'a':  # Move left
                            target_bucket_x = max(BORDER_WIDTH, target_bucket_x - bucket_speed)
                        elif data == 'd':  # Move right
                            target_bucket_x = min(BORDER_WIDTH + GAME_AREA_WIDTH - BUCKET_WIDTH, target_bucket_x + bucket_speed)
                        # Handle diagonal movement
                        elif data == 'ul':  # Up-left diagonal
                            target_bucket_y = max(SCREEN_HEIGHT // 2, target_bucket_y - bucket_speed)
                            target_bucket_x = max(BORDER_WIDTH, target_bucket_x - bucket_speed)
                        elif data == 'ur':  # Up-right diagonal
                            target_bucket_y = max(SCREEN_HEIGHT // 2, target_bucket_y - bucket_speed)
                            target_bucket_x = min(BORDER_WIDTH + GAME_AREA_WIDTH - BUCKET_WIDTH, target_bucket_x + bucket_speed)
                        elif data == 'dl':  # Down-left diagonal
                            target_bucket_y = min(SCREEN_HEIGHT - BUCKET_HEIGHT, target_bucket_y + bucket_speed)
                            target_bucket_x = max(BORDER_WIDTH, target_bucket_x - bucket_speed)
                        elif data == 'dr':  # Down-right diagonal
                            target_bucket_y = min(SCREEN_HEIGHT - BUCKET_HEIGHT, target_bucket_y + bucket_speed)
                            target_bucket_x = min(BORDER_WIDTH + GAME_AREA_WIDTH - BUCKET_WIDTH, target_bucket_x + bucket_speed)
                        elif data == 'r':  # Restart game
                            print(f"Restart requested: {restart_requested}")
                            restart_requested = True
                        elif data == 'q':  # Client quitting
                            print(f"Client {address} paused")
                            paused = True
            
            except ConnectionResetError:
                print(f"Connection with {address} was reset")
            except Exception as e:
                print(f"Error handling client {address}: {e}")
            finally:
                conn.close()
                print(f"Connection with {address} closed")
    
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server_socket.close()
        print("Server socket closed")

if __name__ == "__main__":
    # Start game and server threads
    game_thread = threading.Thread(target=GameThread)
    server_thread = threading.Thread(target=ServerThread)
    
    game_thread.daemon = True  # Allow program to exit even if thread is running
    server_thread.daemon = True
    
    game_thread.start()
    server_thread.start()
    
    try:
        # Keep main thread alive
        while game_thread.is_alive() and server_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server shutting down...")
    except Exception as e:
        print(f"Error in main thread: {e}")

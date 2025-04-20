import threading
import pygame
import socket
import sys
import random
import time

# Game variables
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BUCKET_WIDTH = 80
BUCKET_HEIGHT = 60
OBJECT_SIZE = 30
INITIAL_OBJECT_SPEED = 2
INITIAL_BUCKET_SPEED = 8
DIFFICULTY_INCREASE_RATE = 0.1  # Speed increase per second
MAX_LIVES = 3

# Shared game state variables
bucket_x = SCREEN_WIDTH // 2
bucket_y = SCREEN_HEIGHT - 100
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
    global bucket_x, bucket_y, game_score, game_over, objects
    global object_speed_multiplier, bucket_speed_multiplier, lives
    global last_spawn_time, game_start_time, restart_requested
    
    with game_lock:
        bucket_x = SCREEN_WIDTH // 2
        bucket_y = SCREEN_HEIGHT - 100
        game_score = 0
        game_over = False
        objects = []
        object_speed_multiplier = 1.0
        bucket_speed_multiplier = 1.0
        lives = MAX_LIVES
        last_spawn_time = pygame.time.get_ticks()
        game_start_time = pygame.time.get_ticks()
        restart_requested = False

def spawn_object():
    # """Spawn a new falling object at a random x position."""
    with game_lock:
        x = random.randint(OBJECT_SIZE, SCREEN_WIDTH - OBJECT_SIZE)
        objects.append([x, 0, INITIAL_OBJECT_SPEED * object_speed_multiplier])

#Start Screen
def play_screen(screen, font):
    while True:
        screen.fill((135, 206, 235))
        font = pygame.font.SysFont('Arial', 48, bold=True)
        text = font.render("Press SPACE to Start", True, (0, 0, 0))
        screen.blit(text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 30))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()  # Ensure proper exit
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                return  # Exit loop when SPACE is pressed

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
    global bucket_x, bucket_y, game_score, prv_score, high_score, game_over, objects
    global object_speed_multiplier, bucket_speed_multiplier, lives
    global last_spawn_time, game_start_time, restart_requested, paused
    
    pygame.init()
    pygame.font.init()
    font = pygame.font.SysFont('Arial', 24)
    
    # Colors
    BLUE = (0, 120, 255)
    YELLOW = (255, 255, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    ORANGE = (255, 165, 0)
    BACKGROUND = (135, 206, 235)  # Sky blue
    
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
    
    #play_screen
    play_screen(screen, font)

    # Initialize game variables
    reset_game()
    
    # Main game loop
    running = True
    while running:
        current_time = pygame.time.get_ticks()
        
        # Handle pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif paused:
               action = quit(screen, font)
               if action == "restarting":
                   reset_game()
                   play_screen(screen, font)
                   paused = False
               elif action == "resume":
                   paused = False
        
        # Check for restart request
            if restart_requested:
                print("Restarting Game...")
                reset_game()
                restart_requested = False
        
        # If game is not over, update game state
        if not game_over:
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
                # Create a copy of objects to safely modify during iteration
                updated_objects = []
                for obj in objects:
                    obj_x, obj_y, obj_speed = obj
                    
                    # Update object position
                    obj_y += obj_speed
                    
                    # Check if object hit the bottom
                    if obj_y > SCREEN_HEIGHT:
                        lives -= 1
                        if lives <= 0:
                            game_over = True
                    # Check if object collided with bucket
                    elif (bucket_x < obj_x < bucket_x + BUCKET_WIDTH and 
                          bucket_y < obj_y + OBJECT_SIZE < bucket_y + BUCKET_HEIGHT):
                        game_score += 1


                    else:
                        # Keep object if it's still in play
                        if obj_y < SCREEN_HEIGHT:
                            updated_objects.append([obj_x, obj_y, obj_speed])
                            
                
                # Update objects list
                objects = updated_objects
        
        # Draw everything
        screen.fill(BACKGROUND)
        
        # Draw bucket
        pygame.draw.rect(screen, YELLOW, (bucket_x, bucket_y, BUCKET_WIDTH, BUCKET_HEIGHT))
        
        # Draw falling objects
        with game_lock:
            for i, obj in enumerate(objects):
                obj_x, obj_y, _ = obj
                color = object_colors[i % len(object_colors)]
                pygame.draw.circle(screen, color, (obj_x, obj_y), OBJECT_SIZE)
        
        # Draw score + High score
        score_text = font.render(f'Score: {game_score}', True, (0, 0, 0))
        prv_score = game_score
        if game_score > high_score:
            high_score = game_score
        high_text = font.render(f'High Score: {high_score}', True, (0, 0, 0))
        screen.blit(score_text, (10, 10))
        screen.blit(high_text, (10, 40))
        
        # Draw lives
        for i in range(lives):
            pygame.draw.rect(screen, RED, (SCREEN_WIDTH - 30 * (i + 1), 10, 20, 20))
        
        # Draw game over message
        if game_over:
            game_over_text = font.render('GAME OVER! Press R to restart', True, (255, 0, 0))
            screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2))
        
        # Update display
        pygame.display.flip()
        
        # Cap the frame rate
        clock.tick(60)
    
    pygame.quit()

def ServerThread():
    # """Server thread that handles client connections and processes input."""
    global bucket_x, bucket_y, game_over, restart_requested, paused
    
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
                            bucket_y = max(SCREEN_HEIGHT // 2, bucket_y - bucket_speed)
                        elif data == 's':  # Move down
                            bucket_y = min(SCREEN_HEIGHT - BUCKET_HEIGHT, bucket_y + bucket_speed)
                        elif data == 'a':  # Move left
                            bucket_x = max(0, bucket_x - bucket_speed)
                        elif data == 'd':  # Move right
                            bucket_x = min(SCREEN_WIDTH - BUCKET_WIDTH, bucket_x + bucket_speed)
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

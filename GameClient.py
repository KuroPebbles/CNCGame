import keyboard
import socket
import time


def client_program():
    print("Bucket Catch Game - Client")
    print("Trying to connect to server...")
    host = "192.168.68.50"  # Updated to match server's IP
    port = 5000  # socket server port number

    client_socket = socket.socket()  # instantiate
    
    try:
        client_socket.connect((host, port))  # connect to the server
        print("Connected to server!")
        print("Controls: WASD to move bucket, Q to quit")
        
        while True:
            # Check for quit key
            if keyboard.is_pressed('q'):
                print("Quitting game...")
                client_socket.send('q'.encode())
                time.sleep(0.05)
                
            # Check for combined movement keys (diagonals)
            # Using a more efficient approach to handle diagonals
            up = keyboard.is_pressed('w')
            down = keyboard.is_pressed('s')
            left = keyboard.is_pressed('a')
            right = keyboard.is_pressed('d')
            
            # Send combined movement commands
            if up and left:
                client_socket.send('ul'.encode())  # up-left diagonal
            elif up and right:
                client_socket.send('ur'.encode())  # up-right diagonal
            elif down and left:
                client_socket.send('dl'.encode())  # down-left diagonal
            elif down and right:
                client_socket.send('dr'.encode())  # down-right diagonal
            # Single direction movements
            elif up:
                client_socket.send('w'.encode())  # move up
            elif down:
                client_socket.send('s'.encode())  # move down
            elif left:
                client_socket.send('a'.encode())  # move left
            elif right:
                client_socket.send('d'.encode())  # move right
                
            # Add a small delay after any movement command
            if up or down or left or right:
                time.sleep(0.05)

            # Check for restart key
            if keyboard.is_pressed('r'):
                client_socket.send('r'.encode())  # restart game
                time.sleep(0.05)  # Longer delay for restart to prevent multiple triggers
                
            # Small sleep to reduce CPU usage
            time.sleep(0.01)
            
    except ConnectionRefusedError:
        print("Could not connect to server. Make sure the server is running.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client_socket.close()  # close the connection
        print("Connection closed")


if __name__ == '__main__':
    client_program()
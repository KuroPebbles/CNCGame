import keyboard
import socket
import time


def client_program():
    print("Bucket Catch Game - Client")
    print("Trying to connect to server...")
    host = "10.12.51.41"  # Updated to match server's IP
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
                
            # Check for movement keys
            if keyboard.is_pressed('a'):
                client_socket.send('a'.encode())  # move left
                time.sleep(0.05)  # Small delay to prevent flooding
            if keyboard.is_pressed('d'):
                client_socket.send('d'.encode())  # move right
                time.sleep(0.05)
            if keyboard.is_pressed('w'):
                client_socket.send('w'.encode())  # move up
                time.sleep(0.05)
            if keyboard.is_pressed('s'):
                client_socket.send('s'.encode())  # move down
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
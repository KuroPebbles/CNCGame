# Bucket Catch Game

## Game Description

The objective of the game is to collect as many falling objects as possible using a bucket that can be moved sideways. The game follows these rules:

- One bucket moves sideways (and up/down) to collect falling objects
- Falling objects are generated at random locations from the top of the screen
- Objects and bucket speed increase as the game progresses
- Player loses when an object touches the bottom of the screen

## Requirements

- Python 3.x
- pygame
- keyboard

## Installation

Install the required packages:

```
pip install -r requirements.txt
```

## How to Run

1. Start the server first:

```
python GameServer.py
```

2. Then start the client in a separate terminal:

```
python GameClient.py
```

## Controls

- **W**: Move bucket up
- **A**: Move bucket left
- **S**: Move bucket down
- **D**: Move bucket right
- **R**: Restart game
- **Q**: Quit game

## Game Features

- Client-server architecture with socket programming
- Multithreaded server for handling game logic and client connections
- Increasing difficulty as the game progresses
- Score tracking
- Lives system
- Game restart functionality

## Project Structure

- `GameServer.py`: Server-side code that handles game logic and display
- `GameClient.py`: Client-side code that handles user input
- `requirements.txt`: List of required Python packages

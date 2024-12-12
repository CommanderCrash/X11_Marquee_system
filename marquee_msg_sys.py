#!/usr/bin/env python3

import os
import socket
import select
import queue
import threading
import pygame
import sys
import time
import stat
import uuid
import argparse
from dataclasses import dataclass
from typing import Optional, Tuple

def parse_arguments():
    parser = argparse.ArgumentParser(description='Notification Display Server')
    parser.add_argument('-t', '--tcp', action='store_true',
                      help='Enable TCP socket on port 5555 for network messages')
    return parser.parse_args()

# Set display environment variables for pygame
os.environ['SDL_VIDEODRIVER'] = 'x11'
os.environ['DISPLAY'] = ':0'
os.environ['SDL_VIDEO_WINDOW_POS'] = '0,0'

# Initialize Pygame and Pygame Mixer
pygame.init()
pygame.mixer.init()

# Paths and configurations
sock_path = "/mnt/ram/message_socket"
tcp_port = 5555        # For receiving messages

@dataclass
class Message:
    text: str
    priority: int
    color: str
    speed: float
    wav_path: str
    use_espeak: str
    id: str = ""
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

    def __lt__(self, other):
        return self.priority < other.priority

class MessageQueue:
    def __init__(self):
        self.queue = queue.PriorityQueue()
        self.queue_lock = threading.Lock()
        self.recent_messages = set()
        self.recent_messages_lock = threading.Lock()

    def add_message(self, msg: Message):
        with self.recent_messages_lock:
            message_key = f"{msg.text}_{msg.priority}"
            if message_key not in self.recent_messages:
                self.recent_messages.add(message_key)
                self.queue.put((msg.priority, msg))
                # Clear message from recent after 2 seconds
                threading.Timer(2.0, lambda: self.recent_messages.remove(message_key)).start()

    def get_message(self) -> Optional[Message]:
        try:
            with self.queue_lock:
                if not self.queue.empty():
                    _, msg = self.queue.get_nowait()
                    return msg
        except queue.Empty:
            pass
        return None

# Global variables
message_queue = MessageQueue()
current_message = None
message_visible = False
window_visible = False
screen = None

def get_screen_size():
    """Get the full screen width"""
    pygame.display.init()
    info = pygame.display.Info()
    return info.current_w, info.current_h

def create_window():
    global screen, window_visible
    try:
        if not window_visible:
            pygame.display.quit()
            pygame.display.init()
            
            # Get screen width
            screen_width, _ = get_screen_size()
            
            # Set window position at top of screen
            os.putenv('SDL_VIDEO_WINDOW_POS', '0,0')
            os.environ['SDL_VIDEO_WINDOW_POS'] = '0,0'
            pygame.display.set_mode((screen_width, 100), pygame.NOFRAME | pygame.SHOWN)
            
            # Create the window with full width
            screen = pygame.display.set_mode((screen_width, 100), pygame.NOFRAME | pygame.SHOWN)
            
            # X11 positioning (optional)
            try:
                import Xlib
                import Xlib.display
                from Xlib import X
                
                info = pygame.display.get_wm_info()
                if 'window' in info:
                    x11_display = Xlib.display.Display()
                    window = x11_display.create_resource_object('window', info['window'])
                    
                    # Window "stay on top" configuration
                    NET_WM_STATE = x11_display.intern_atom('_NET_WM_STATE')
                    NET_WM_STATE_ABOVE = x11_display.intern_atom('_NET_WM_STATE_ABOVE')
                    NET_WM_STATE_STAYS_ON_TOP = x11_display.intern_atom('_NET_WM_STATE_STAYS_ON_TOP')
                    window.change_property(NET_WM_STATE, Xlib.Xatom.ATOM, 32,
                                        [NET_WM_STATE_ABOVE, NET_WM_STATE_STAYS_ON_TOP],
                                        X.PropModeReplace)
                    
                    # Move to top of screen
                    window.configure(y=0, stack_mode=X.Above)
                    x11_display.sync()
            except Exception as e:
                print(f"X11 window positioning failed: {e}")
            
            window_visible = True
            time.sleep(0.1)
            return True
    except Exception as e:
        print(f"Error creating window: {e}")
        return False
    return False

def destroy_window():
    global screen, window_visible
    if window_visible:
        pygame.display.quit()
        window_visible = False
        screen = None
        time.sleep(0.1)

def play_audio(wav_path):
    """Plays the audio file if a valid path is provided."""
    if wav_path:
        try:
            print(f"Attempting to play audio: {wav_path}")
            if not os.path.isfile(wav_path):
                print(f"Audio file not found: {wav_path}")
                return

            def audio_thread():
                pygame.mixer.music.load(wav_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.delay(100)

            threading.Thread(target=audio_thread, daemon=True).start()

        except pygame.error as e:
            print(f"Failed to play audio: {e}")

def show_marquee(text, color, speed):
    global current_message, message_visible
    if create_window():
        current_message = (text, color, speed)
        message_visible = True

def update_marquee():
    global current_message, message_visible, screen
    if current_message is not None and screen is not None:
        try:
            text, color, speed = current_message
            font = pygame.font.Font(None, 74)
            rendered_text = font.render(text, True, pygame.Color(color))
            text_rect = rendered_text.get_rect()

            screen_height = text_rect.height + 20
            pygame.display.set_mode((screen.get_width(), screen_height), pygame.NOFRAME | pygame.SHOWN)

            for x in range(screen.get_width(), -text_rect.width, -5):
                if not window_visible:
                    break
                screen.fill((0, 0, 0))
                screen.blit(rendered_text, (x, 10))
                pygame.display.flip()
                pygame.time.delay(int(speed * 1000))

        except Exception as e:
            print(f"Error in update_marquee: {e}")
        finally:
            current_message = None
            message_visible = False
            destroy_window()

def socket_listener():
    try:
        # Add timeout to select
        read_sockets = [local_sock]
        if tcp_sock:
            read_sockets.append(tcp_sock)
        read_sockets, _, _ = select.select(read_sockets, [], [], 1.0)
        
        for sock in read_sockets:
            try:
                print(f"Accepting connection on socket {sock}")
                connection, client_address = sock.accept()
                print(f"Connection accepted from {client_address}")
                connection.settimeout(5.0)  # Set timeout for receiving data
                
                data = connection.recv(1024).decode().strip()
                print(f"Raw data received: {data}")
                
                if data:
                    parse_and_queue_message(data)
                connection.close()
            except Exception as e:
                print(f"Error handling connection: {e}")
                if 'connection' in locals():
                    connection.close()
    except select.error as e:
        print(f"Select error: {e}")
    except Exception as e:
        print(f"General error in socket listener: {e}")

def parse_and_queue_message(data):
    try:
        print(f"Parsing message: {data}")
        parts = data.split("|")
        if len(parts) != 6:
            print(f"Invalid message format. Expected 6 parts, got {len(parts)}")
            return
            
        priority, text, color, speed, wav_path, use_espeak = parts
        
        msg = Message(
            text=text,
            priority=int(priority),
            color=color,
            speed=float(speed),
            wav_path=wav_path,
            use_espeak=use_espeak
        )
        
        print(f"Created message object: {msg}")
        message_queue.add_message(msg)
        print("Message added to queue")
        
    except Exception as e:
        print(f"Failed to parse message: {e}")

def start_socket_listener():
    while True:
        try:
            socket_listener()
        except Exception as e:
            print(f"Error in socket listener: {e}")
            time.sleep(1)

def check_queue():
    msg = message_queue.get_message()
    if msg:
        print(f"Displaying message: {msg.text}")
        show_marquee(msg.text, msg.color, msg.speed)
        if msg.wav_path:
            play_audio(msg.wav_path)

if __name__ == "__main__":
    args = parse_arguments()
    
    print("\nServer Configuration:")
    print(f"Unix Socket: Enabled at {sock_path}")
    print(f"TCP Socket: {'Enabled' if args.tcp else 'Disabled'} (Port {tcp_port})")

    # Initialize sockets
    try:
        os.unlink(sock_path)
    except OSError:
        if os.path.exists(sock_path):
            raise

    # Create and bind the local Unix socket
    local_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    local_sock.bind(sock_path)
    local_sock.listen(1)
    os.chmod(sock_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    # Create and bind the network TCP socket
    tcp_sock = None
    if args.tcp:
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp_sock.bind(('0.0.0.0', tcp_port))
        tcp_sock.listen(5)

    print("Server started")
    print(f"Listening for display messages on {sock_path}")
    if args.tcp:
        print(f"Listening for network messages on port {tcp_port}")

    # Start the socket listener thread
    listener_thread = threading.Thread(target=start_socket_listener)
    listener_thread.daemon = True
    listener_thread.start()

    # Main loop
    try:
        while True:
            try:
                check_queue()
                if window_visible:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            raise SystemExit
                    if message_visible:
                        update_marquee()
                time.sleep(0.1)
            except pygame.error:
                destroy_window()
                time.sleep(0.1)

    except (KeyboardInterrupt, SystemExit):
        print("\nShutting down server...")
        destroy_window()
        pygame.quit()
        sys.exit()

# Cleanup
pygame.quit()

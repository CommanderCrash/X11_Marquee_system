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
import re
import os.path

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

# Font configurations
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]

EMOJI_FONT_PATHS = [
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
    "/usr/share/fonts/google-noto-emoji/NotoColorEmoji.ttf",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    None  # Fallback to default font
]


def get_emoji_font(size):
    """Get font for emojis"""
    # Force a very small fixed size for emojis
    emoji_size = 30  # Try a fixed small size regardless of input size
    
    emoji_paths = [
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
        "/usr/share/fonts/google-noto-emoji/NotoColorEmoji.ttf",
        None
    ]
    
    for font_path in emoji_paths:
        try:
            if font_path is None:
                return pygame.font.Font(None, emoji_size)
            if os.path.exists(font_path):
                font = pygame.font.Font(font_path, emoji_size)
                return font
        except Exception as e:
            print(f"Failed to load emoji font {font_path}: {e}")
            continue
    return pygame.font.Font(None, emoji_size)

def get_text_font(size):
    """Get font for regular text"""
    for font_path in FONT_PATHS:
        try:
            if os.path.exists(font_path):
                return pygame.font.Font(font_path, size)
        except Exception as e:
            print(f"Failed to load text font {font_path}: {e}")
            continue
    return pygame.font.Font(None, size)


def get_font_with_emoji_support(size):
    """Try to load a font that supports text and emoji"""
    # Try system fonts first
    for font_path in FONT_PATHS:
        try:
            if os.path.exists(font_path):
                print(f"Loading font: {font_path}")
                return pygame.font.Font(font_path, size)
        except Exception as e:
            print(f"Failed to load font {font_path}: {e}")
            continue
    
    # Fall back to emoji fonts
    for font_path in EMOJI_FONT_PATHS:
        try:
            if font_path is None:
                print("Using default pygame font")
                return pygame.font.Font(None, size)
            if os.path.exists(font_path):
                print(f"Loading emoji font: {font_path}")
                return pygame.font.Font(font_path, size)
        except Exception as e:
            print(f"Failed to load emoji font {font_path}: {e}")
            continue
            
    print("Using default pygame font as last resort")
    return pygame.font.Font(None, size)


def is_emoji(char):
    """Check if a character is an emoji"""
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return bool(emoji_pattern.match(char))

def render_mixed_text(text, size, color, bg_color=None):
    """Render text with mixed emoji and regular characters"""
    text_font = get_text_font(size)
    emoji_font = get_emoji_font(size)
    
    # First calculate total width
    total_width = 0
    heights = []
    
    # Split text into characters and measure each
    for char in text:
        if is_emoji(char):
            surf = emoji_font.render(char, True, color)
            # Adjust emoji vertical position
            heights.append(int(text_font.get_height() * 0.1))  # Slightly lower than text height
        else:
            surf = text_font.render(char, True, color)
            heights.append(surf.get_height())
        total_width += surf.get_width()
    
    # Create surface using text font height as reference
    max_height = text_font.get_height()
    surface = pygame.Surface((total_width, max_height), pygame.SRCALPHA)
    
    # Render each character
    x_pos = 0
    for char in text:
        if is_emoji(char):
            char_surf = emoji_font.render(char, True, color)
            # Center emoji vertically
            y_pos = (max_height - char_surf.get_height()) // 2
        else:
            char_surf = text_font.render(char, True, color)
            y_pos = 0  # Regular text aligned to top
            
        surface.blit(char_surf, (x_pos, y_pos))
        x_pos += char_surf.get_width()
    
    return surface

@dataclass
class Message:
    text: str
    priority: int
    blink_mode: int
    color: str
    bg_color: str
    speed: float
    wav_path: str
    use_espeak: str
    id: str = ""
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        self.text = self.convert_emoji_to_emoticon(self.text)

    def __lt__(self, other):
        return self.priority < other.priority

    def has_emoji(self):
        """Check for both Unicode emojis and text emoticons"""
        emoticon_pattern = r'(:-?\)|:-?\(|:-?D|:-?P|;-?\)|:-?\||>:-?\(|\^_\^|:3|<3|:o|:O|:v|:V|=\))'
        return bool(re.search(emoticon_pattern, self.text))

    def convert_emoji_to_emoticon(self, text):
        """Convert Unicode emoji to text emoticons"""
        emoji_to_emoticon = {
            '😊': ':)',
            '😃': ':D',
            '😄': ':D',
            '😆': 'XD',
            '🙂': ':)',
            '😉': ';)',
            '😢': ':(',
            '😭': ':\'(',
            '😎': '8)',
            '😍': '<3',
            '👍': '(y)',
            '❤️': '<3',
            '💙': '<3',
            '💚': '<3',
            '💛': '<3',
            '💜': '<3',
            '😀': ':D',
            '😁': ':D',
            '☹️': ':(',
            '🙁': ':(',
            '😮': ':O',
            '😯': ':o',
            '😕': ':/',
            '❓': '?',
            '❗': '!',
            '💪': 'flex',
            '👋': 'wave',
            '🎵': '♪',
            '🎶': '♫',
            '⭐': '*',
            '✨': '*',
            '🔥': 'fire',
            '💯': '100',
        }
        
        for emoji, emoticon in emoji_to_emoticon.items():
            text = text.replace(emoji, emoticon)
        return text

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
blink_state = True

def get_screen_size():
    pygame.display.init()
    info = pygame.display.Info()
    return info.current_w, info.current_h

def create_window():
    global screen, window_visible
    try:
        if not window_visible:
            pygame.display.quit()
            pygame.display.init()
            screen_width, _ = get_screen_size()
            os.putenv('SDL_VIDEO_WINDOW_POS', '0,0')
            os.environ['SDL_VIDEO_WINDOW_POS'] = '0,0'
            screen = pygame.display.set_mode((screen_width, 100), pygame.NOFRAME | pygame.SHOWN | pygame.SRCALPHA)
            pygame.display.set_caption('Transparent Message')
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

def show_marquee(message: Message):
    global current_message, message_visible
    if create_window():
        current_message = message
        message_visible = True

def render_text_with_blink(text: str, font_size: int, color: str, blink_mode: int, has_emoji: bool) -> pygame.Surface:
    """Render text with blinking support"""
    global blink_state
    
    # First render the complete text to get total dimensions
    full_text_surface = render_mixed_text(text, font_size, pygame.Color(color))
    total_width = full_text_surface.get_width()
    total_height = full_text_surface.get_height()
    
    # If not blinking or full text blink, return the appropriate surface
    if blink_mode == 0 or (blink_mode == 3 and blink_state):
        return full_text_surface
    
    if blink_mode == 3 and not blink_state:
        # Return empty surface of same size
        return pygame.Surface((total_width, total_height), pygame.SRCALPHA)
    
    # For modes 1 and 2 (partial blinking)
    final_surface = pygame.Surface((total_width, total_height), pygame.SRCALPHA)
    x_pos = 0
    
    for char in text:
        is_emoji_char = is_emoji(char)
        should_blink = (
            (blink_mode == 1 and not is_emoji_char) or
            (blink_mode == 2 and is_emoji_char)
        )
        
        # Render each character
        char_surface = render_mixed_text(char, font_size, pygame.Color(color))
        char_width = char_surface.get_width()
        
        if not should_blink or blink_state:
            # If character should be visible, blit it
            final_surface.blit(char_surface, (x_pos, 0))
        # If character should be invisible, skip blitting (space is already transparent)
        
        x_pos += char_width  # Always advance by character width
    
    return final_surface

def create_glass_panel(width, height):
    """Creates a glass panel effect surface with light reflection and borders"""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Main glass panel - semi-transparent white
    glass_color = (255, 255, 255, 25)  # Very light, mostly transparent white
    surface.fill(glass_color)
    
    # Add subtle gradient overlay for depth
    gradient = pygame.Surface((width, height), pygame.SRCALPHA)
    for i in range(height):
        alpha = int(25 * (1 - i/height))  # Fade from top to bottom
        pygame.draw.line(gradient, (255, 255, 255, alpha), (0, i), (width, i))
    surface.blit(gradient, (0, 0))
    
    # Add light border
    border_color = (255, 255, 255, 40)
    pygame.draw.rect(surface, border_color, (0, 0, width, height), 1)
    
    # Add highlight at the top
    highlight_color = (255, 255, 255, 30)
    pygame.draw.line(surface, highlight_color, (0, 1), (width, 1), 2)
    
    return surface

def update_marquee():
    global current_message, message_visible, screen, blink_state
    if current_message is not None and screen is not None:
        try:
            font_size = 100
            font = get_font_with_emoji_support(font_size)
            has_emoji = current_message.has_emoji()
            
            temp_text = font.render(current_message.text, True, pygame.Color(current_message.color))
            text_rect = temp_text.get_rect()
            screen_height = text_rect.height + 5
            
            # Set up window with alpha channel support
            pygame.display.set_mode((screen.get_width(), screen_height), pygame.NOFRAME | pygame.SHOWN | pygame.SRCALPHA)
            
            # Handle glass panel effect
            if current_message.bg_color.lower() == 'glass':
                glass_panel = create_glass_panel(screen.get_width(), screen_height)
            else:
                try:
                    bg_color = pygame.Color(current_message.bg_color)
                except (ValueError, TypeError):
                    bg_color = pygame.Color(0, 0, 0)
            
            x = screen.get_width()
            
            # Pre-render the text to get its full width
            full_text = render_text_with_blink(
                current_message.text,
                font_size,
                current_message.color,
                current_message.blink_mode,
                has_emoji
            )
            text_width = full_text.get_width()
            
            blink_counter = 0
            
            while x > -(text_width):
                if not window_visible:
                    break
                
                blink_counter += 1
                if blink_counter >= 30:
                    blink_state = not blink_state
                    blink_counter = 0
                
                rendered_text = render_text_with_blink(
                    current_message.text,
                    font_size,
                    current_message.color,
                    current_message.blink_mode,
                    has_emoji
                )
                
                # Clear screen with transparency
                screen.fill((0, 0, 0, 0))
                
                if current_message.bg_color.lower() == 'glass':
                    # Apply glass panel effect
                    screen.blit(glass_panel, (0, 0))
                    
                    # Add subtle shadow under text for better readability
                    shadow_offset = 2
                    shadow_text = render_text_with_blink(
                        current_message.text,
                        font_size,
                        "black",  # Shadow color
                        current_message.blink_mode,
                        has_emoji
                    )
                    # Set shadow transparency
                    shadow_text.set_alpha(50)
                    screen.blit(shadow_text, (x + shadow_offset, 10 + shadow_offset))
                else:
                    screen.fill(bg_color)
                
                screen.blit(rendered_text, (x, 10))
                pygame.display.flip()
                
                x -= 5
                pygame.time.delay(int(current_message.speed * 1000))

        except Exception as e:
            print(f"Error in update_marquee: {e}")
            print(f"Error details: {str(e)}")
        finally:
            current_message = None
            message_visible = False
            destroy_window()

def parse_and_queue_message(data):
    try:
        print(f"Parsing message: {data}")
        parts = data.split("|")
        if len(parts) < 8:
            print(f"Invalid message format. Expected 8 parts, got {len(parts)}")
            return
            
        priority, blink_mode, text, color, bg_color, speed, wav_path, use_espeak = parts[:8]
        
        # Fix empty background color
        if not bg_color.strip():
            bg_color = "black"
        
        msg = Message(
            text=text,
            priority=int(priority),
            blink_mode=int(blink_mode),
            color=color,
            bg_color=bg_color,
            speed=float(speed),
            wav_path=wav_path,
            use_espeak=use_espeak
        )
        
        print(f"Created message object: {msg}")
        message_queue.add_message(msg)
        print("Message added to queue")
        
    except Exception as e:
        print(f"Failed to parse message: {e}")

def socket_listener():
    try:
        read_sockets = [local_sock]
        if tcp_sock:
            read_sockets.append(tcp_sock)
        read_sockets, _, _ = select.select(read_sockets, [], [], 1.0)
        
        for sock in read_sockets:
            try:
                print(f"Accepting connection on socket {sock}")
                connection, client_address = sock.accept()
                print(f"Connection accepted from {client_address}")
                connection.settimeout(5.0)
                
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
        show_marquee(msg)
        if msg.wav_path:
            play_audio(msg.wav_path)

if __name__ == "__main__":
    args = parse_arguments()
    
    print("\nServer Configuration:")
    print(f"Unix Socket: Enabled at {sock_path}")
    print(f"TCP Socket: {'Enabled' if args.tcp else 'Disabled'} (Port {tcp_port})")

    try:
        os.unlink(sock_path)
    except OSError:
        if os.path.exists(sock_path):
            raise

    local_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    local_sock.bind(sock_path)
    local_sock.listen(1)
    os.chmod(sock_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

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

    listener_thread = threading.Thread(target=start_socket_listener)
    listener_thread.daemon = True
    listener_thread.start()

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

pygame.quit()

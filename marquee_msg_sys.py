#!/usr/bin/env python3

# By Commander Crash

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
import re
import json
import os.path
import traceback
from flask import Flask, request, send_from_directory, jsonify
import threading
from functools import partial
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial
from dataclasses import dataclass
from typing import Optional, Tuple
from datetime import datetime

# Create Flask app
app = Flask(__name__, static_folder='static')

# Global message log
message_history = []
ignored_messages = {}  # Dictionary to track ignored messages {message_content: expiry_time}


def parse_arguments():
    parser = argparse.ArgumentParser(description='Notification Display Server')
    parser.add_argument('-t', '--tcp', action='store_true',
                      help='Enable TCP socket on port 5555 for network messages')
    parser.add_argument('-w', '--webui', action='store_true',
                      help='Enable Web UI')
    parser.add_argument('-wp', '--webui-port', type=int, default=5501,
                      help='Web UI port (default: 5501)')
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
    "/usr/share/fonts/truetype/font-awesome/GreatAttraction-L1JW.ttf"
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
    emoji_size = 10  # Try a fixed small size regardless of input size

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
    """Check if a character is an emoji, including those with variation selectors"""
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F700-\U0001F77F"  # alchemical symbols
        u"\U0001F780-\U0001F7FF"  # Geometric Shapes
        u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        u"\U0001FA00-\U0001FA6F"  # Chess Symbols
        u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        u"\U00002600-\U000026FF"  # Miscellaneous Symbols
        u"\U00002700-\U000027BF"  # Dingbats
        u"\U0000FE00-\U0000FE0F"  # Variation Selectors
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002300-\U000023FF"  # Miscellaneous Technical
        u"\U000024C2-\U000024FF"  # Enclosed alphanumerics
        u"\U00002B50-\U00002B55"  # Star symbols
        u"\U00002600-\U000026FF"  # Miscellaneous Symbols
        u"\U00002702-\U000027B0"  # Dingbat symbols
        u"\U000026A0-\U000026AB"  # Warning sign and other symbols
        u"\U000026A1"             # High voltage
        u"\U0000203C"             # Double exclamation
        u"\U00002049"             # Exclamation question mark
        u"\U000020E3"             # Combining enclosing keycap
        u"\U00002122"             # Trade mark
        u"\U00002139"             # Information
        u"\U00002194-\U00002199"  # Arrows
        "]+", flags=re.UNICODE)

    # First check if the character is an emoji
    if emoji_pattern.match(char):
        return True

    # Also check for combined characters (emoji + variation selector)
    if len(char) > 1:
        # Check if any part of the character is a variation selector (U+FE0F)
        for c in char:
            if ord(c) == 0xFE0F:
                return True

    return False

def render_mixed_text(text, size, color, bg_color=None):
    """Render text with mixed emoji and regular characters"""
    text_font = get_text_font(size)
    emoji_font = get_emoji_font(size)

    # First calculate total width
    total_width = 0

    # Get reference height for the text
    ref_height = text_font.get_height()

    # Process text to handle emoji sequences properly
    processed_chars = []
    i = 0
    while i < len(text):
        current_char = text[i]

        # Check if this character plus the next one might form an emoji sequence
        if i + 1 < len(text) and ord(text[i+1]) == 0xFE0F:  # FE0F is variation selector
            processed_chars.append(text[i:i+2])
            i += 2
        else:
            processed_chars.append(current_char)
            i += 1

    # Split text into characters and measure each
    char_surfaces = []
    for char in processed_chars:
        if is_emoji(char):
            surf = emoji_font.render(char, True, color)
            # Scale emoji to fit the text height
            scale_factor = min(1.0, (ref_height * 0.9) / surf.get_height())
            scaled_width = int(surf.get_width() * scale_factor)
            scaled_height = int(surf.get_height() * scale_factor)
            if scaled_width > 0 and scaled_height > 0:
                surf = pygame.transform.scale(surf, (scaled_width, scaled_height))
        else:
            surf = text_font.render(char, True, color)

        char_surfaces.append(surf)
        total_width += surf.get_width()

    # Create surface with text height as reference
    surface = pygame.Surface((total_width, ref_height), pygame.SRCALPHA)

    # Render each character
    x_pos = 0
    for i, surf in enumerate(char_surfaces):
        char = processed_chars[i]
        if is_emoji(char):
            # Center emoji vertically
            y_pos = (ref_height - surf.get_height()) // 2
        else:
            # Regular text aligned to baseline
            y_pos = (ref_height - surf.get_height()) // 4

        surface.blit(surf, (x_pos, y_pos))
        x_pos += surf.get_width()

    return surface

def add_to_message_history(text, priority=1, color="#ffffff", bg_color="#000000"):
    """Centralized function to add messages to history"""
    message_entry = {
        'id': str(uuid.uuid4()),
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'message': text,
        'priority': priority,
        'color': color,
        'bg_color': bg_color
    }
    message_history.append(message_entry)
    return message_entry

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

    def __lt__(self, other):
        return self.priority < other.priority

    def has_emoji(self):
        """Check for both Unicode emojis and text emoticons"""
        emoticon_pattern = r'(:-?\)|:-?\(|:-?D|:-?P|;-?\)|:-?\||>:-?\(|\^_\^|:3|<3|:o|:O|:v|:V|=\))'
        return bool(re.search(emoticon_pattern, self.text))

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

class NotificationHandler(SimpleHTTPRequestHandler):
    def __init__(self, message_queue, *args, **kwargs):
        self.message_queue = message_queue
        super().__init__(*args, **kwargs)

    def translate_path(self, path):
        # Serve files from the static directory
        if path == '/':
            return os.path.join(os.path.dirname(__file__), 'static', 'index.html')
        return os.path.join(os.path.dirname(__file__), 'static', path.lstrip('/'))

    def do_POST(self):
        if self.path == '/api/send-message':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            # Convert hex colors to names or keep as hex
            color = data.get('color', '#ffffff')
            bg_color = data.get('bgColor', '#000000')

            # Create message string in the expected format
            message_str = (f"{data.get('priority', 1)}|"
                         f"{data.get('blinkMode', 0)}|"
                         f"{data.get('text', '')}|"
                         f"{color}|{bg_color}|"
                         f"{data.get('speed', 1.0)}||")

            parse_and_queue_message(message_str)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success'}).encode())
            return

        return super().do_POST()

# Global variables
message_queue = MessageQueue()
current_message = None
message_visible = False
window_visible = False
screen = None
blink_state = True

def start_webserver(port, message_queue=None):
    # Start cleanup thread for ignored messages
    def cleanup_ignored_messages():
        while True:
            current_time = datetime.now().timestamp()
            for key in list(ignored_messages.keys()):
                if ignored_messages[key] < current_time:
                    print(f"Removing expired ignore for message: {key}")
                    del ignored_messages[key]
            time.sleep(60)  # Check every minute

    cleanup_thread = threading.Thread(target=cleanup_ignored_messages, daemon=True)
    cleanup_thread.start()

    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

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
            screen = pygame.display.set_mode((screen_width, 100), pygame.NOFRAME | pygame.SHOWN)
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

    # Process text to handle emoji sequences properly
    processed_chars = []
    i = 0
    while i < len(text):
        current_char = text[i]

        # Check if this character plus the next one might form an emoji sequence
        if i + 1 < len(text) and ord(text[i+1]) == 0xFE0F:  # FE0F is variation selector
            processed_chars.append(text[i:i+2])
            i += 2
        else:
            processed_chars.append(current_char)
            i += 1

    # For partial blinking, render the full text again to ensure proper scaling
    if blink_mode in (1, 2):
        x_pos = 0
        for char in processed_chars:
            is_emoji_char = is_emoji(char)
            should_blink = (
                (blink_mode == 1 and not is_emoji_char) or
                (blink_mode == 2 and is_emoji_char)
            )

            # Render each character
            if is_emoji_char:
                emoji_font = get_emoji_font(font_size)
                char_surface = emoji_font.render(char, True, pygame.Color(color))

                # Scale emoji to fit within the height
                ref_height = get_text_font(font_size).get_height()
                scale_factor = min(1.0, (ref_height * 0.9) / char_surface.get_height())
                scaled_width = int(char_surface.get_width() * scale_factor)
                scaled_height = int(char_surface.get_height() * scale_factor)

                if scaled_width > 0 and scaled_height > 0:
                    char_surface = pygame.transform.scale(char_surface, (scaled_width, scaled_height))

                # Center emoji vertically
                y_pos = (total_height - char_surface.get_height()) // 2
            else:
                char_surface = get_text_font(font_size).render(char, True, pygame.Color(color))
                y_pos = (total_height - char_surface.get_height()) // 4

            if not should_blink or blink_state:
                final_surface.blit(char_surface, (x_pos, y_pos))

            x_pos += char_surface.get_width()

        return final_surface

    return full_text_surface

def update_marquee():
    global current_message, message_visible, screen, blink_state
    if current_message is not None and screen is not None:
        try:
            font_size = 70  # Define font size here if it works
            font = get_font_with_emoji_support(font_size)  # Get font for initial measurement only
            has_emoji = current_message.has_emoji()

            # Get initial text dimensions
            temp_text = font.render(current_message.text, True, pygame.Color(current_message.color))
            text_rect = temp_text.get_rect()
            screen_height = text_rect.height + 5

            # Set up the window size
            pygame.display.set_mode((screen.get_width(), screen_height), pygame.NOFRAME | pygame.SHOWN)

            # Parse background color
            try:
                bg_color = pygame.Color(current_message.bg_color)
            except (ValueError, TypeError):
                bg_color = pygame.Color(0, 0, 0)

            # For scrolling
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

            # Slow down the blinking
            blink_counter = 0

            # Continue until the entire text has scrolled off the left side of the screen
            while x > -(text_width):  # Changed condition to use actual text width
                if not window_visible:
                    break

                # Update blink state every 30 frames (slower blink)
                blink_counter += 1
                if blink_counter >= 30:
                    blink_state = not blink_state
                    blink_counter = 0

                # Render text with current blink state, passing font_size instead of font object
                rendered_text = render_text_with_blink(
                    current_message.text,
                    font_size,
                    current_message.color,
                    current_message.blink_mode,
                    has_emoji
                )

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

        # Check if message is ignored
        message_key = text.strip().lower()
        current_time = datetime.now().timestamp()

        # Clean up expired ignored messages
        for key in list(ignored_messages.keys()):
            if ignored_messages[key] < current_time:
                del ignored_messages[key]

        # Check if this message is currently ignored
        if message_key in ignored_messages:
            print(f"Message '{text}' is currently ignored. Expires at {datetime.fromtimestamp(ignored_messages[message_key])}")
            return

        # Add to message history BEFORE creating Message object
        message_id = str(uuid.uuid4())
        history_entry = {
            'id': message_id,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': text.strip(),
            'priority': int(priority),
            'color': color,
            'bg_color': bg_color
        }
        print(f"Adding to history: {history_entry}")  # Debug print
        message_history.append(history_entry)

        msg = Message(
            text=text,
            priority=int(priority),
            blink_mode=int(blink_mode),
            color=color,
            bg_color=bg_color,
            speed=float(speed),
            wav_path=wav_path,
            use_espeak=use_espeak,
            id=message_id
        )

        print(f"Created message object: {msg}")
        message_queue.add_message(msg)
        print("Message added to queue")

    except Exception as e:
        print(f"Failed to parse message: {e}")
        traceback.print_exc()  # Add this for better error tracking

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
                    # This will now log the message through parse_and_queue_message
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

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/sounds/<path:filename>')
def serve_sound(filename):
    return send_from_directory(os.path.join(app.static_folder, 'sounds'), filename)

@app.route('/api/send-message', methods=['POST'])
def send_message():
    try:
        data = request.get_json()

        # Convert hex colors to names or keep as hex
        color = data.get('color', '#ffffff')
        bg_color = data.get('bgColor', '#000000')

        # Create message string in the expected format
        message_str = (f"{data.get('priority', 1)}|"
                     f"{data.get('blinkMode', 0)}|"
                     f"{data.get('text', '')}|"
                     f"{color}|{bg_color}|"
                     f"{data.get('speed', 1.0)}||")

        parse_and_queue_message(message_str)

        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Error in send_message: {e}")  # Add error logging
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/message-history', methods=['GET'])
def get_message_history():
    print(f"Returning message history with {len(message_history)} entries")  # Debug print
    return jsonify(list(reversed(message_history)))  # Most recent first

@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    message_history.clear()
    return jsonify({'status': 'success'})

@app.route('/api/ignore_message', methods=['POST'])
def ignore_message():
    global message_history
    data = request.get_json()
    message_id = data.get('message_id')
    duration = data.get('duration', 5)  # Default 5 minutes

    # Find the message in history
    for msg in message_history:
        if msg.get('id') == message_id:
            message_content = msg['message'].strip().lower()
            expiry_time = datetime.now().timestamp() + (int(duration) * 60)
            ignored_messages[message_content] = expiry_time
            print(f"Ignoring message '{message_content}' until {datetime.fromtimestamp(expiry_time)}")
            break

    # Remove from history
    message_history = [msg for msg in message_history if msg.get('id') != message_id]

    return jsonify({'status': 'success'})

@app.route('/api/current_message', methods=['GET'])
def get_current_message():
    # Return empty response since we're not using this endpoint
    return jsonify({'message': None})


if __name__ == "__main__":
    args = parse_arguments()

    print("\nServer Configuration:")
    print(f"Unix Socket: Enabled at {sock_path}")
    print(f"TCP Socket: {'Enabled' if args.tcp else 'Disabled'} (Port {tcp_port})")
    print(f"Web UI: {'Enabled' if args.webui else 'Disabled'} (Port {args.webui_port})")

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

    # Start the socket listener thread
    listener_thread = threading.Thread(target=start_socket_listener)
    listener_thread.daemon = True
    listener_thread.start()

    # Start web UI if enabled
    if args.webui:
        webui_thread = threading.Thread(target=start_webserver, args=(args.webui_port,))
        webui_thread.daemon = True
        webui_thread.start()

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

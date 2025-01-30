# Notification Display Server

A versatile notification display system that shows scrolling messages on screen with support for custom colors, blinking effects, and web interface control.

## Features

- Scrolling text notifications with customizable colors and effects
- Multiple input methods:
  - Unix socket
  - TCP socket (optional)
  - Web interface (optional)
- Message priority system
- Message history tracking
- Configurable display options:
  - Text color
  - Background color
  - Scroll speed
  - Blinking effects
- Support for emoji and special characters
- Audio notification support (WAV files)

## Requirements

### System Requirements
- Python 3.8 or higher
- X11 display server
- System fonts (at least one of):
  - DejaVu Sans
  - Liberation Sans
  - Free Sans
  - Font Awesome (optional, for special characters)

### Python Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- Flask
- pygame
- typing
- dataclasses (for Python < 3.7)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/notification-display-server.git
cd notification-display-server
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Ensure you have X11 display server running:
```bash
echo $DISPLAY  # Should return something like :0
```

4. Make ram disk:
```bash
sudo mkdir -p /mnt/ram
echo "ramfs       /mnt/ram ramfs   nodev,nosuid,nodiratime,size=100M,mode=1777   0 0" | sudo tee -a /etc/fstab 
sudo mount -a
```
## Usage

### Starting the Server

Basic usage:
```bash
python3 notification_server.py
```

With all features enabled:
```bash
python3 notification_server.py --tcp --webui
```

Available command line options:
- `-t, --tcp`: Enable TCP socket on port 5555
- `-w, --webui`: Enable Web UI
- `-wp, --webui-port PORT`: Set Web UI port (default: 5501)

### Sending Messages

1. Via Unix Socket:
```bash
echo "1|0|Hello World!|#ffffff|#000000|1.0||" > /mnt/ram/message_socket
```

2. Via TCP (if enabled):
```bash
echo "1|0|Hello World!|#ffffff|#000000|1.0||" | nc localhost 5555
```

3. Via Web Interface (if enabled):
- Open http://localhost:5501 in your browser
- Use the web form to send messages

### Message Format

Messages should be formatted as:
```
priority|blink_mode|text|color|bg_color|speed|wav_path|use_espeak
```

Parameters:
- `priority`: Integer (1-9, lower = higher priority)
- `blink_mode`: Integer (0=none, 1=text only, 2=emoji only, 3=all)
- `text`: Message text
- `color`: Text color (hex code or color name)
- `bg_color`: Background color (hex code or color name)
- `speed`: Scroll speed (float, larger = slower)
- `wav_path`: Path to WAV file (optional)
- `use_espeak`: Espeak parameters (optional)

Example:
```
1|0|Important Message|#ff0000|#000000|1.0||
```

## Web Interface

If enabled, the web interface provides:
- Message submission form
- Message history
- Real-time message preview
- Color picker for text and background
- Speed adjustment slider
- Blink mode selection

Access at: http://localhost:5501 (or configured port)

## Troubleshooting

1. Display Issues:
- Ensure X11 is running: `echo $DISPLAY`
- Check font availability: `fc-list`
- Verify pygame installation: `python3 -c "import pygame"`

2. Socket Issues:
- Check socket permissions: `ls -l /mnt/ram/message_socket`
- Verify port availability: `netstat -an | grep 5555`

3. Web Interface Issues:
- Confirm Flask installation: `python3 -c "import flask"`
- Check port availability: `netstat -an | grep 5501`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

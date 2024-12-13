<h1 align="center">Marquee Message System</h1>
<hr />
<p>
  The <strong>Marquee Message System</strong> is a Python application designed to display scrolling text messages on multiple screens using the Pygame library. This can be useful for alert systems, announcements, or any application requiring visual notifications.
</p>
<hr />
<h2>Features</h2>
<ul>
  <li>Support for multiple displays.</li>
  <li>Customizable message attributes (color, speed, priority).</li>
  <li>Audio playback for accompanying alerts.</li>
  <li>Socket communication for receiving messages.</li>
  <li>Devimon Variant connects to android app to display notifications.</li>
  <li>Full emoji support with auto-conversion to text emoticons.</li>
  <li>Glass panel effect background option.</li>
  <li>Customizable blinking modes for text and emojis.</li>
  <li>TCP socket support for network messages.</li>
</ul>
<hr />
<h2>Requirements</h2>
<ul>
  <li>Python 3.x</li>
  <li>Pygame (version 2.0 or later)</li>
  <li>libSDL2, libSDL2_mixer, libSDL2_ttf</li>
  <li>Access to X11 display server</li>
  <li>Noto Color Emoji font (for emoji support)</li>
</ul>
<hr />
<h2>Installation</h2>
<pre><code>
# Install required libraries
sudo apt-get install libsdl2-dev libsdl2-mixer-dev libsdl2-ttf-dev fonts-noto-color-emoji
pip install pygame
</code></pre>
<hr />
<h2>Usage</h2>
<p>
  To run the Marquee Message System, use the following commands:
</p>
<pre><code>
# Run with local Unix socket only
python3 marquee_msg_sys.py

# Run with TCP socket enabled
python3 marquee_msg_sys.py -t
</code></pre>
<hr />
<h2>Sending Messages</h2>
<p>
  Messages can be sent to the system via a Unix socket or TCP connection. The message format is as follows:
</p>
<pre><code>
priority|blink_mode|text|color|bg_color|speed|audio_path|use_espeak
</code></pre>
<p>
  Parameters:
</p>
<ul>
  <li>priority: Message priority (lower numbers = higher priority)</li>
  <li>blink_mode: 0 = no blink, 1 = text blinks, 2 = emoji blinks, 3 = all blinks</li>
  <li>text: Message text (supports emojis)</li>
  <li>color: Text color (e.g., 'red', '#FF0000')</li>
  <li>bg_color: Background color or 'glass' for glass panel effect</li>
  <li>speed: Scroll speed (lower = faster)</li>
  <li>audio_path: Path to WAV file (optional)</li>
  <li>use_espeak: 0 or 1 for text-to-speech</li>
</ul>
<p>
  Examples:
</p>
<pre><code>
# Basic message with red text on black background
echo "1|0|Hello World|red|black|0.01||0" | nc -U /mnt/ram/message_socket

# Message with emojis and glass panel effect
echo "1|0|⛈📲☎📞📟📠🔋🔌|red|glass|0.01||0" | nc -U /mnt/ram/message_socket

# Message with blinking text
echo "1|1|ALERT MESSAGE|yellow|black|0.01||0" | nc -U /mnt/ram/message_socket

# Send message via TCP (if enabled)
echo "1|0|Network Message|blue|glass|0.01||0" | nc localhost 5555
</code></pre>
<hr />
<h2>Troubleshooting</h2>
<ul>
  <li>If you encounter issues with missing libraries, ensure that you have installed all the required SDL libraries.</li>
  <li>For emoji support, verify that the Noto Color Emoji font is installed.</li>
  <li>Check your display settings to ensure that your environment is set up to access the X11 display server.</li>
  <li>If messages aren't displayed, check that the Unix socket exists at /mnt/ram/message_socket.</li>
  <li>For TCP connections, ensure port 5555 is not blocked by firewall.</li>
</ul>
<hr />

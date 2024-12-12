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
</ul>

<hr />

<h2>Requirements</h2>
<ul>
  <li>Python 3.x</li>
  <li>Pygame (version 2.0 or later)</li>
  <li>libSDL2, libSDL2_mixer, libSDL2_ttf</li>
  <li>Access to X11 display server</li>
</ul>

<hr />

<h2>Installation</h2>
<pre><code>
# Install required libraries
sudo apt-get install libsdl2-dev libsdl2-mixer-dev libsdl2-ttf-dev
pip install pygame
</code></pre>

<hr />

<h2>Usage</h2>
<p>
  To run the Marquee Message System, use the following command:
</p>
<pre><code>
python3 marquee_msg_sys.py -d [display]
</code></pre>

<p>
  Replace <code>[display]</code> with the appropriate display number (e.g., <code>:0</code>) or use <code>all</code> to target all available displays.
</p>

<hr />

<h2>Sending Messages</h2>
<p>
  Messages can be sent to the system via a socket connection. The message format is as follows:
</p>
<pre><code>
priority|text|color|speed|audio_path|use_espeak
</code></pre>

<p>
  Example:
</p>
<pre><code>
4|TESTING ALERT SYSTEM...|purple|0.1|/PATH/TO/AUDIO/FILE/|0
</code></pre>

<hr />

<h2>Example Command</h2>
<pre><code>
python3 marquee_msg_sys.py -d all
</code></pre>

<hr />

<h2>Troubleshooting</h2>
<ul>
  <li>If you encounter issues with missing libraries, ensure that you have installed all the required SDL libraries.</li>
  <li>Check your display settings to ensure that your environment is set up to access the X11 display server.</li>
</ul>

<hr />

<h2>License</h2>
<p>
  This project is licensed under the MIT License. See the <a href="LICENSE">LICENSE</a> file for details.
</p>

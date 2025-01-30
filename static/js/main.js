// static/js/main.js

document.addEventListener('DOMContentLoaded', () => {
    // Initialize sound effects
    const sounds = {
        hover: document.getElementById('hoverSound'),
        click: document.getElementById('clickSound'),
        dropdown: document.getElementById('dropdownSound')
    };

    // Play sound function
    const playSound = (sound) => {
        sound.currentTime = 0;
        sound.play().catch(e => console.log('Sound play error:', e));
    };

    // Add hover sound to all buttons and menu items
    document.querySelectorAll('button, .menu-item').forEach(element => {
        element.addEventListener('mouseenter', () => playSound(sounds.hover));
    });

    // Message form handling
    const messageForm = document.getElementById('message-form');
    messageForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        playSound(sounds.click);

        const speedValue = parseFloat(document.getElementById('scroll-speed').value);
        console.log('Speed value:', speedValue); // Debug log

        const formData = {
            text: document.getElementById('message-text').value,
            priority: parseInt(document.getElementById('message-priority').value),
            color: document.getElementById('message-color').value,
            bgColor: document.getElementById('message-bg-color').value,
            blinkMode: parseInt(document.getElementById('blink-mode').value),
            speed: speedValue
        };

        console.log('Sending form data:', formData); // Debug log

        try {
            const response = await fetch('/api/send-message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            if (response.ok) {
                messageForm.reset();
                // Set default values after reset
                document.getElementById('message-color').value = '#ffffff';
                document.getElementById('message-bg-color').value = '#000000';
                document.getElementById('message-priority').value = '1';
                document.getElementById('scroll-speed').value = '0.05';
                document.getElementById('speed-value').textContent = '0.05';
            }
        } catch (error) {
            console.error('Error sending message:', error);
        }
    });

    // Context menu handling
    const contextMenu = document.getElementById('context-menu');
    const ignoreModal = document.getElementById('ignore-modal');
    let selectedMessageId = null;

    document.getElementById('message-log').addEventListener('contextmenu', (e) => {
        e.preventDefault();
        playSound(sounds.dropdown);
        
        const messageElement = e.target.closest('.log-entry');
        if (messageElement) {
            selectedMessageId = messageElement.dataset.id;
            contextMenu.style.display = 'block';
            contextMenu.style.left = `${e.pageX}px`;
            contextMenu.style.top = `${e.pageY}px`;
        }
    });

    // Hide context menu on click outside
    document.addEventListener('click', () => {
        contextMenu.style.display = 'none';
    });

    // Ignore menu item handling
    document.getElementById('ignore-message').addEventListener('click', () => {
        ignoreModal.style.display = 'flex';
        playSound(sounds.click);
    });

    document.getElementById('cancel-ignore').addEventListener('click', () => {
        ignoreModal.style.display = 'none';
        playSound(sounds.click);
    });

    document.getElementById('confirm-ignore').addEventListener('click', async () => {
        const duration = document.getElementById('ignore-duration').value;
        playSound(sounds.click);
        
        try {
            const response = await fetch('/api/ignore_message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message_id: selectedMessageId,
                    duration: parseInt(duration)
                })
            });
            if (response.ok) {
                ignoreModal.style.display = 'none';
                updateMessageLog();
            }
        } catch (error) {
            console.error('Error ignoring message:', error);
        }
    });

    // Clear log button
    document.getElementById('clear-log').addEventListener('click', async () => {
        try {
            const response = await fetch('/api/clear-history', {
                method: 'POST'
            });
            if (response.ok) {
                updateMessageLog();
            }
        } catch (error) {
            console.error('Error clearing history:', error);
        }
    });

    // Speed slider value display update
    const speedSlider = document.getElementById('scroll-speed');
    const speedValue = document.getElementById('speed-value');
    
    speedSlider.addEventListener('input', function(e) {
        const value = parseFloat(e.target.value).toFixed(3);
        speedValue.textContent = value;
        console.log('Speed changed to:', value); // Debug log
    });

    function updateMessageLog() {
        console.log('Fetching message history...'); // Debug log
        fetch('/api/message-history')
            .then(response => response.json())
            .then(messages => {
                console.log('Received messages:', messages); // Debug log
                const messageLog = document.getElementById('message-log');
                if (!messageLog) {
                    console.error('Message log element not found!');
                    return;
                }
                
                messageLog.innerHTML = ''; // Clear existing messages
                
                messages.forEach(msg => {
                    const logEntry = document.createElement('div');
                    logEntry.className = 'log-entry';
                    
                    // Create the HTML content
                    logEntry.innerHTML = `
                        <span class="timestamp">${msg.timestamp}</span>
                        <span class="message-text" style="color: ${msg.color || '#fff'}">${msg.message}</span>
                        ${msg.priority > 1 ? `<span class="priority">[Priority: ${msg.priority}]</span>` : ''}
                    `;
                    
                    messageLog.appendChild(logEntry);
                });
            })
            .catch(error => {
                console.error('Error fetching message history:', error);
            });
    }

    // Update message log every second
    setInterval(updateMessageLog, 1000);
    
    // Initial update
    updateMessageLog();
});

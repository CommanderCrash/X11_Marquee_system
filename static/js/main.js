// static/js/main.js

// Theme definitions
const themes = {
    matrix: {
        '--bg-primary': 'black',
        '--glass-bg': 'rgba(17, 25, 40, 0.75)',
        '--text-primary': '#fff',
        '--accent-color': '#d5ff76',
        '--border-color': 'rgba(255, 255, 255, 0.125)',
        '--shadow-color': 'rgba(0, 255, 0, 0.3)',
        '--input-bg': 'rgba(0, 0, 0, 0.3)',
        '--button-bg': 'rgba(0, 255, 0, 0.2)',
        '--button-hover': 'rgba(0, 255, 0, 0.4)',
        '--log-bg': 'rgba(0, 0, 0, 0.2)'
    },

office: {
    // Background and container colors
    '--bg-primary': '#3f4a55',           // Dark blue-gray background
    '--glass-bg': '#5be0ff8c',          // Semi-transparent light blue
    '--text-primary': '#252525',         // Dark text
    '--accent-color': '#0078d4',         // Microsoft Blue
    '--border-color': '#f701ffa6',       // Semi-transparent pink
    '--shadow-color': 'rgba(0, 0, 0, 0.08)', // Subtle shadows
    '--input-bg': '#ffffffd1',             // --input-bg: #ffffffd1
    '--button-bg': '#cce9ff',            // Light blue buttons
    '--button-hover': '#106ebe',         // Darker blue on hover
    '--log-bg': '#000000c2',             // Semi-transparent black
    '--error-color': '#d83b01',          // Red for errors
    '--success-color': '#107c10',        // Green for success
    '--warning-color': '#797673',        // Gray for warnings
    '--disabled-bg': '#f3f2f1',          // Light gray for disabled
    '--hover-bg': '#f3f9fd',             // Very light blue for hover
    '--selected-bg': '#e5f3ff'           // Light blue for selected
}
};


// Matrix animation setup and control
function setupMatrixAnimation() {
    const canvas = document.getElementById('matrix-canvas');
    const ctx = canvas.getContext('2d');
    let animationId = null;

    // Set canvas size
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    
    const characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*";
    const fontSize = 14;
    let drops = [];

    function initMatrix() {
        resizeCanvas();
        const columns = canvas.width / fontSize;
        drops = new Array(Math.floor(columns)).fill(1);
    }

    function drawMatrix() {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#0F0';
        ctx.font = fontSize + 'px monospace';

        for (let i = 0; i < drops.length; i++) {
            const text = characters[Math.floor(Math.random() * characters.length)];
            ctx.fillText(text, i * fontSize, drops[i] * fontSize);
            if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
                drops[i] = 0;
            }
            drops[i]++;
        }
        animationId = requestAnimationFrame(drawMatrix);
    }

    // Initialize
    initMatrix();
    window.addEventListener('resize', () => {
        initMatrix();
    });

    // Return control functions
    return {
        start: () => {
            if (!animationId) {
                drawMatrix();
            }
        },
        stop: () => {
            if (animationId) {
                cancelAnimationFrame(animationId);
                animationId = null;
                // Clear canvas
                ctx.clearRect(0, 0, canvas.width, canvas.height);
            }
        }
    };
}

// Theme handling function
const matrixController = setupMatrixAnimation();

function applyTheme(themeName) {
    const theme = themes[themeName];
    for (const [property, value] of Object.entries(theme)) {
        document.documentElement.style.setProperty(property, value);
    }

    // Add theme-specific class to body
    document.body.dataset.theme = themeName;

    // Toggle matrix canvas and animation
    const matrixCanvas = document.getElementById('matrix-canvas');
    if (matrixCanvas) {
        if (themeName === 'matrix') {
            matrixCanvas.style.display = 'block';
            matrixController.start();
        } else {
            matrixCanvas.style.display = 'none';
            matrixController.stop();
        }
    }

    // Update glass container styles
    document.querySelectorAll('.glass-container').forEach(container => {
        if (themeName === 'office') {
            container.style.boxShadow = '0 0 20px rgba(255, 255, 0, 0.3), 0 0 40px rgba(255, 255, 0, 0.3)';
            container.style.backdropFilter = 'none';
        } else {
            container.style.boxShadow = '0 0 20px var(--shadow-color), 0 0 40px var(--shadow-color)';
            container.style.backdropFilter = 'blur(10px) saturate(180%)';
        }
    });

    // Save theme preference
    localStorage.setItem('selectedTheme', themeName);
}

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

    // Theme initialization
    const savedTheme = localStorage.getItem('selectedTheme') || 'matrix';
    applyTheme(savedTheme);
    if (document.getElementById('theme-select')) {
        document.getElementById('theme-select').value = savedTheme;
    }

    // Theme switcher event listener
    document.getElementById('theme-select')?.addEventListener('change', (e) => {
        applyTheme(e.target.value);
        playSound(sounds.dropdown);
    });

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
        console.log('Speed value:', speedValue);

        const formData = {
            text: document.getElementById('message-text').value,
            priority: parseInt(document.getElementById('message-priority').value),
            color: document.getElementById('message-color').value,
            bgColor: document.getElementById('message-bg-color').value,
            blinkMode: parseInt(document.getElementById('blink-mode').value),
            speed: speedValue
        };

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
    });

    function updateMessageLog() {
        fetch('/api/message-history')
            .then(response => response.json())
            .then(messages => {
                const messageLog = document.getElementById('message-log');
                if (!messageLog) {
                    console.error('Message log element not found!');
                    return;
                }
                
                messageLog.innerHTML = '';
                
                messages.forEach(msg => {
                    const logEntry = document.createElement('div');
                    logEntry.className = 'log-entry';
                    
                    logEntry.innerHTML = `
                        <span class="timestamp">${msg.timestamp}</span>
                        <span class="message-text" style="color: ${msg.color || 'var(--text-primary)'}">${msg.message}</span>
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

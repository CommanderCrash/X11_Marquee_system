// static/js/main.js
// Theme definitions
const themes = {
  matrix: {
    "--bg-primary": "black",
    "--glass-bg": "rgba(17, 25, 40, 0.75)",
    "--text-primary": "#fff",
    "--accent-color": "#d5ff76",
    "--border-color": "rgba(255, 255, 255, 0.125)",
    "--shadow-color": "rgba(0, 255, 0, 0.3)",
    "--input-bg": "rgba(0, 0, 0, 0.3)",
    "--button-bg": "rgba(0, 255, 0, 0.2)",
    "--button-hover": "rgba(0, 255, 0, 0.4)",
    "--log-bg": "rgba(0, 0, 0, 0.2)",
    "--timestamp-color": "#aaffaa",
  },
  office: {
    // Background and container colors
    "--bg-primary": "#3f4a55", // Dark blue-gray background
    "--glass-bg": "#5be0ff8c", // Semi-transparent light blue
    "--text-primary": "#252525", // Dark text
    "--accent-color": "#0078d4", // Microsoft Blue
    "--border-color": "#f701ffa6", // Semi-transparent pink
    "--shadow-color": "rgba(0, 0, 0, 0.08)", // Subtle shadows
    "--input-bg": "#ffffffd1", // --input-bg: #ffffffd1
    "--button-bg": "#cce9ff", // Light blue buttons
    "--button-hover": "#106ebe", // Darker blue on hover
    "--log-bg": "#07232bb8", // Semi-transparent black
    "--error-color": "#d83b01", // Red for errors
    "--success-color": "#107c10", // Green for success
    "--warning-color": "#797673", // Gray for warnings
    "--disabled-bg": "#f3f2f1", // Light gray for disabled
    "--hover-bg": "#f3f9fd", // Very light blue for hover
    "--selected-bg": "#e5f3ff", // Light blue for selected
    "--timestamp-color": "#00b7eb", // Blue for timestamps
  },
  "cherry-blossom": {
    "--bg-primary": "#fff6f8",
    "--glass-bg": "rgba(255, 217, 228, 0.7)",
    "--text-primary": "#442c33",
    "--accent-color": "#ff758f",
    "--border-color": "rgba(255, 183, 197, 0.4)",
    "--shadow-color": "rgba(255, 166, 193, 0.3)",
    "--input-bg": "rgba(255, 246, 248, 0.7)",
    "--button-bg": "rgba(255, 182, 193, 0.6)",
    "--button-hover": "rgba(255, 105, 180, 0.7)",
    "--log-bg": "rgba(255, 240, 245, 0.6)",
    "--timestamp-color": "#e06377",
  },
  cyberpunk: {
    "--bg-primary": "#0a0a20",
    "--glass-bg": "rgba(10, 10, 32, 0.9)",
    "--text-primary": "#ffffff",
    "--accent-color": "#ff2a6d",
    "--border-color": "#00fff9",
    "--shadow-color": "rgba(0, 255, 249, 0.3)",
    "--input-bg": "#050510",
    "--button-bg": "transparent",
    "--button-hover": "#00fff9",
    "--log-bg": "rgba(5, 5, 16, 0.8)",
    "--timestamp-color": "#39ff14",
    "--neon-pink": "#ff2a6d",
    "--neon-blue": "#00fff9",
    "--neon-purple": "#8a2be2",
    "--dark-bg": "#0a0a20",
    "--darker-bg": "#050510",
    "--cyber-green": "#39ff14",
  },
};

// Matrix animation setup and control
function setupMatrixAnimation() {
  const canvas = document.getElementById("matrix-canvas");
  const ctx = canvas.getContext("2d");
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
    ctx.fillStyle = "rgba(0, 0, 0, 0.05)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#0F0";
    ctx.font = fontSize + "px monospace";
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
  window.addEventListener("resize", () => {
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
    },
  };
}

// Cherry Blossom animation setup and control
function setupCherryBlossomAnimation() {
  const canvas = document.getElementById("cherry-blossom-canvas");
  const ctx = canvas.getContext("2d");
  let animationId = null;

  // Set canvas size
  function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  // Petal configurations
  const petals = [];
  const petalColors = [
    "#FFD7E9",
    "#FFCCE1",
    "#FFC1D9",
    "#FFB6D1",
    "#FFABC9",
    "#FFA0C1",
    "#FF95B9",
    "#FF8AB1",
    "#FF7FA9",
    "#FF74A1",
  ];

  function createPetal() {
    const x = Math.random() * canvas.width;
    const y = Math.random() * canvas.height - canvas.height;
    const size = Math.random() * 10 + 5;
    const speed = Math.random() * 1 + 0.5;
    const angle = Math.random() * 360;
    const rotationSpeed = (Math.random() - 0.5) * 0.01;
    const color = petalColors[Math.floor(Math.random() * petalColors.length)];

    petals.push({ x, y, size, speed, angle, rotationSpeed, color });
  }

  function initCherryBlossom() {
    resizeCanvas();
    petals.length = 0;

    // Create initial petals
    for (let i = 0; i < 50; i++) {
      createPetal();
    }
  }

  function drawPetal(petal) {
    ctx.save();
    ctx.translate(petal.x, petal.y);
    ctx.rotate(petal.angle);

    // Draw petal shape
    ctx.beginPath();
    ctx.fillStyle = petal.color;
    ctx.moveTo(0, 0);
    ctx.bezierCurveTo(
      petal.size / 2,
      -petal.size,
      petal.size,
      -petal.size / 2,
      petal.size,
      0,
    );
    ctx.bezierCurveTo(
      petal.size,
      petal.size / 2,
      petal.size / 2,
      petal.size,
      0,
      0,
    );
    ctx.fill();
    ctx.restore();
  }

  function updateCherryBlossom() {
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw gradient background
    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    gradient.addColorStop(0, "#000000");
    gradient.addColorStop(1, "#111111");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Update and draw petals
    for (let i = 0; i < petals.length; i++) {
      const petal = petals[i];

      // Update position
      petal.y += petal.speed;
      petal.x += Math.sin(petal.y * 0.01) * 0.5;
      petal.angle += petal.rotationSpeed;

      // Draw the petal
      drawPetal(petal);

      // Reset if off screen
      if (petal.y > canvas.height + petal.size) {
        petal.y = -petal.size;
        petal.x = Math.random() * canvas.width;
      }
    }

    // Add new petals occasionally
    if (Math.random() < 0.02 && petals.length < 100) {
      createPetal();
    }

    animationId = requestAnimationFrame(updateCherryBlossom);
  }

  // Initialize
  initCherryBlossom();
  window.addEventListener("resize", () => {
    initCherryBlossom();
  });

  // Return control functions
  return {
    start: () => {
      if (!animationId) {
        updateCherryBlossom();
      }
    },
    stop: () => {
      if (animationId) {
        cancelAnimationFrame(animationId);
        animationId = null;
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    },
  };
}

// Theme handling function
const matrixController = setupMatrixAnimation();
const cherryBlossomController = setupCherryBlossomAnimation();

function applyTheme(themeName) {
  const theme = themes[themeName];
  for (const [property, value] of Object.entries(theme)) {
    document.documentElement.style.setProperty(property, value);
  }
  // Add theme-specific class to body
  document.body.dataset.theme = themeName;

  // Toggle animations based on theme
  const matrixCanvas = document.getElementById("matrix-canvas");
  const cherryBlossomCanvas = document.getElementById("cherry-blossom-canvas");

  // Stop all animations first
  matrixController.stop();
  cherryBlossomController.stop();

  if (matrixCanvas) matrixCanvas.style.display = "none";
  if (cherryBlossomCanvas) cherryBlossomCanvas.style.display = "none";

  // Start the appropriate animation
  if (themeName === "matrix") {
    if (matrixCanvas) {
      matrixCanvas.style.display = "block";
      matrixController.start();
    }
  } else if (themeName === "cherry-blossom") {
    if (cherryBlossomCanvas) {
      cherryBlossomCanvas.style.display = "block";
      cherryBlossomController.start();
    }
  }

  // Update glass container styles
  document.querySelectorAll(".glass-container").forEach((container) => {
    if (themeName === "office") {
      container.style.boxShadow =
        "0 0 20px rgba(255, 255, 0, 0.3), 0 0 40px rgba(255, 255, 0, 0.3)";
      container.style.backdropFilter = "none";
    } else if (themeName === "cherry-blossom") {
      container.style.boxShadow =
        "0 0 20px rgba(255, 166, 193, 0.3), 0 0 40px rgba(255, 166, 193, 0.3)";
      container.style.backdropFilter = "blur(10px) saturate(180%)";
    } else {
      container.style.boxShadow =
        "0 0 20px var(--shadow-color), 0 0 40px var(--shadow-color)";
      container.style.backdropFilter = "blur(10px) saturate(180%)";
    }
  });

  // Save theme preference
  localStorage.setItem("selectedTheme", themeName);
}

document.addEventListener("DOMContentLoaded", () => {
  // Initialize sound effects
  const sounds = {
    hover: document.getElementById("hoverSound"),
    click: document.getElementById("clickSound"),
    dropdown: document.getElementById("dropdownSound"),
  };
  // Play sound function
  const playSound = (sound) => {
    sound.currentTime = 0;
    sound.play().catch((e) => console.log("Sound play error:", e));
  };
  // Theme initialization
  const savedTheme = localStorage.getItem("selectedTheme") || "matrix";
  applyTheme(savedTheme);
  if (document.getElementById("theme-select")) {
    document.getElementById("theme-select").value = savedTheme;
  }
  // Theme switcher event listener
  document.getElementById("theme-select")?.addEventListener("change", (e) => {
    applyTheme(e.target.value);
    playSound(sounds.dropdown);
  });
  // Add hover sound to all buttons and menu items
  document.querySelectorAll("button, .menu-item").forEach((element) => {
    element.addEventListener("mouseenter", () => playSound(sounds.hover));
  });
  // Message form handling
  const messageForm = document.getElementById("message-form");
  messageForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    playSound(sounds.click);
    const speedValue = parseFloat(
      document.getElementById("scroll-speed").value,
    );
    console.log("Speed value:", speedValue);
    const formData = {
      text: document.getElementById("message-text").value,
      priority: parseInt(document.getElementById("message-priority").value),
      color: document.getElementById("message-color").value,
      bgColor: document.getElementById("message-bg-color").value,
      blinkMode: parseInt(document.getElementById("blink-mode").value),
      speed: speedValue,
    };
    try {
      const response = await fetch("/api/send-message", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });
      if (response.ok) {
        messageForm.reset();
        // Set default values after reset
        document.getElementById("message-color").value = "#ffffff";
        document.getElementById("message-bg-color").value = "#000000";
        document.getElementById("message-priority").value = "1";
        document.getElementById("scroll-speed").value = "0.05";
        document.getElementById("speed-value").textContent = "0.05";
      }
    } catch (error) {
      console.error("Error sending message:", error);
    }
  });
  // Context menu handling
  const contextMenu = document.getElementById("context-menu");
  const ignoreModal = document.getElementById("ignore-modal");
  let selectedMessageId = null;
  document
    .getElementById("message-log")
    .addEventListener("contextmenu", (e) => {
      e.preventDefault();
      playSound(sounds.dropdown);

      const messageElement = e.target.closest(".log-entry");
      if (messageElement) {
        selectedMessageId = messageElement.dataset.id;
        contextMenu.style.display = "block";
        contextMenu.style.left = `${e.pageX}px`;
        contextMenu.style.top = `${e.pageY}px`;
      }
    });
  // Hide context menu on click outside
  document.addEventListener("click", () => {
    contextMenu.style.display = "none";
  });
  // Ignore menu item handling
  document.getElementById("ignore-message").addEventListener("click", () => {
    ignoreModal.style.display = "flex";
    playSound(sounds.click);
  });
  document.getElementById("cancel-ignore").addEventListener("click", () => {
    ignoreModal.style.display = "none";
    playSound(sounds.click);
  });
  document
    .getElementById("confirm-ignore")
    .addEventListener("click", async () => {
      const duration = document.getElementById("ignore-duration").value;
      playSound(sounds.click);

      try {
        const response = await fetch("/api/ignore_message", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message_id: selectedMessageId,
            duration: parseInt(duration),
          }),
        });
        if (response.ok) {
          ignoreModal.style.display = "none";
          updateMessageLog();
        }
      } catch (error) {
        console.error("Error ignoring message:", error);
      }
    });
  // Clear log button
  document.getElementById("clear-log").addEventListener("click", async () => {
    try {
      const response = await fetch("/api/clear-history", {
        method: "POST",
      });
      if (response.ok) {
        updateMessageLog();
      }
    } catch (error) {
      console.error("Error clearing history:", error);
    }
  });
  // Speed slider value display update
  const speedSlider = document.getElementById("scroll-speed");
  const speedValue = document.getElementById("speed-value");

  speedSlider.addEventListener("input", function (e) {
    const value = parseFloat(e.target.value).toFixed(3);
    speedValue.textContent = value;
  });
  function updateMessageLog() {
    fetch("/api/message-history")
    .then((response) => response.json())
    .then((messages) => {
      const messageLog = document.getElementById("message-log");
      if (!messageLog) {
        console.error("Message log element not found!");
        return;
      }

      messageLog.innerHTML = "";

      messages.forEach((msg) => {
        const logEntry = document.createElement("div");
        logEntry.className = "log-entry";
        logEntry.dataset.id = msg.id; // Set the message ID

        logEntry.innerHTML = `
        <span class="timestamp">${msg.timestamp}</span>
        <span class="message-text" style="color: ${msg.color || "var(--text-primary)"}">${msg.message}</span>
        ${msg.priority > 1 ? `<span class="priority">[Priority: ${msg.priority}]</span>` : ""}
        `;

        messageLog.appendChild(logEntry);
      });
    })
    .catch((error) => {
      console.error("Error fetching message history:", error);
    });
  }

  // Update message log every second
  setInterval(updateMessageLog, 1000);

  // Initial update
  updateMessageLog();
});

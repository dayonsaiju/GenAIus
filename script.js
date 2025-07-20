// Drawer menu for mobile
const hamburger = document.getElementById("hamburger");
const drawer = document.getElementById("drawer");
const overlay = document.getElementById("drawerOverlay");
const closeBtn = document.getElementById("closeDrawer");
if (hamburger && drawer && overlay && closeBtn) {
  hamburger.addEventListener("click", () => {
    drawer.classList.add("active");
    overlay.classList.add("active");
  });
  overlay.addEventListener("click", () => {
    drawer.classList.remove("active");
    overlay.classList.remove("active");
  });
  closeBtn.addEventListener("click", () => {
    drawer.classList.remove("active");
    overlay.classList.remove("active");
  });
}

// Language Training Logic
if (document.getElementById("start-training")) {
  let language = "english";
  let level = "beginner";
  let unit = 0, step = 0, done = false;
  let recognition, recognizing = false;
  let lastUserInput = "", lastFeedback = "";

  // Level to unit/step mapping
  const levelMap = {
    "beginner": { unit: 0, step: 0 },
    "medium": { unit: 1, step: 0 },
    "expert": { unit: 3, step: 0 }
  };

  document.getElementById("start-training").onclick = function() {
    language = document.getElementById("language-select").value;
    level = document.getElementById("level-select").value;
    // Set unit/step based on level
    let mapping = levelMap[level] || { unit: 0, step: 0 };
    unit = mapping.unit;
    step = mapping.step;
    
    // Hide selection UI and show training UI
    document.getElementById("training-form").parentElement.style.display = "none";
    document.getElementById("unit-section").style.display = "block";
    
    // Show Hindi warning if Hindi is selected
    const hindiWarning = document.getElementById("hindi-warning");
    if (hindiWarning) {
      hindiWarning.style.display = language === "hindi" ? "block" : "none";
    }
    
    // Update text input placeholder for Hindi
    const textInput = document.getElementById("text-input");
    if (textInput) {
      textInput.placeholder = language === "hindi" ? "अपना जवाब टाइप करें..." : "Type your answer...";
    }
    
    fetchPrompt("", unit, step, true);
    // Hindi speech warning
    if (language === "hindi") {
      const warning = document.getElementById("speech-warning");
      if (!('webkitSpeechRecognition' in window)) {
        warning.textContent = "⚠️ Your browser does not support Hindi speech recognition. Please use Google Chrome on desktop.";
      } else {
        warning.textContent = "";
      }
    }
  };

  // On reset in free conversation mode, pass correct unit/step
  window.fetchPrompt = fetchPrompt; // expose for reset if needed

  function updateUI(data) {
    let unitNum = (typeof data.unit === 'number' ? data.unit + 1 : '')
    document.getElementById("unit-title").textContent = data.unit_title ? `Unit ${unitNum}: ${data.unit_title}` : "";
    document.getElementById("unit-prompt").textContent = data.prompt || "";
    document.getElementById("unit-progress").textContent = data.done ? "🎉 Training Complete!" : "";
    
    // Show last user input and feedback
    let userInputLi = document.getElementById("user-input-li");
    let feedbackLi = document.getElementById("feedback-li");
    
    if (!userInputLi) {
      userInputLi = document.createElement("div");
      userInputLi.id = "user-input-li";
      userInputLi.className = "user-input";
      document.querySelector("#unit-section .center-card").insertBefore(userInputLi, document.getElementById("unit-progress"));
    }
    
    if (!feedbackLi) {
      feedbackLi = document.createElement("div");
      feedbackLi.id = "feedback-li";
      feedbackLi.className = "feedback";
      document.querySelector("#unit-section .center-card").insertBefore(feedbackLi, document.getElementById("unit-progress"));
    }
    
    // Update user input display
    if (data.user_input) {
      userInputLi.textContent = language === "hindi" ? `आपने कहा: "${data.user_input}"` : `You said: "${data.user_input}"`;
      userInputLi.style.display = "block";
    } else {
      userInputLi.style.display = "none";
    }
    
    // Update AI feedback display
    if (data.feedback) {
      feedbackLi.textContent = language === "hindi" ? `AI: ${data.feedback}` : `AI: ${data.feedback}`;
      feedbackLi.style.display = "block";
    } else {
      feedbackLi.style.display = "none";
    }
    
    console.log("UI updated - Language:", language, "User input:", data.user_input, "Feedback:", data.feedback);
  }

  function fetchPrompt(user_input, customUnit, customStep, isFirst) {
    // Send custom unit/step only on first load after level select
    let payload = { language, user_input };
    if (isFirst) {
      payload.unit = customUnit;
      payload.step = customStep;
    }
    fetch("/language-training/api", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
      updateUI(data);
      playAudio(data.audio);
      done = data.done;
    });
  }

  function playAudio(url) {
    const audio = document.getElementById("audio-player");
    audio.src = url;
    audio.style.display = "block";
    audio.play();
  }

  // Mic button logic
  document.getElementById("mic-btn").onclick = function() {
    if (!('webkitSpeechRecognition' in window)) {
      alert("Speech recognition not supported in this browser.");
      return;
    }
    
    // Create new recognition instance for each language to avoid conflicts
    recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    
    // Set language based on current selection
    if (language === "hindi") {
      // Try Hindi first, but have fallback
      recognition.lang = "hi-IN";
      console.log("Setting Hindi speech recognition");
      
      // Add error handling for Hindi recognition
      recognition.onerror = function(event) {
        console.error("Hindi speech recognition error:", event.error);
        if (event.error === 'not-allowed' || event.error === 'no-speech') {
          // Fallback to English recognition for Hindi
          console.log("Falling back to English recognition for Hindi");
          recognition.lang = "en-US";
          document.getElementById("mic-status").textContent = "Hindi not supported, using English recognition";
          recognition.start();
        } else {
          document.getElementById("mic-status").textContent = language === "hindi" ? "त्रुटि: " + event.error : "Error: " + event.error;
        }
      };
    } else {
      recognition.lang = "en-US";
      console.log("Setting English speech recognition");
      
      recognition.onerror = function(event) {
        console.error("Speech recognition error:", event.error);
        document.getElementById("mic-status").textContent = "Error: " + event.error;
      };
    }
    
    recognition.onresult = function(event) {
      const transcript = event.results[0][0].transcript;
      console.log("Recognized speech:", transcript);
      console.log("Current language:", language);
      fetchPrompt(transcript);
    };
    
    recognition.onstart = function() {
      recognizing = true;
      document.getElementById("mic-status").textContent = language === "hindi" ? "सुन रहा हूं..." : "Listening...";
      console.log("Speech recognition started for language:", language);
    };
    
    recognition.onend = function() {
      recognizing = false;
      document.getElementById("mic-status").textContent = "";
      console.log("Speech recognition ended");
    };
    
    recognition.start();
  };

  // Text input logic
  document.getElementById("text-form").onsubmit = function(e) {
    e.preventDefault();
    const text = document.getElementById("text-input").value.trim();
    if (text) {
      fetchPrompt(text);
      document.getElementById("text-input").value = "";
    }
  };

  // Image upload logic
  document.getElementById("image-form").onsubmit = function(e) {
    e.preventDefault();
    const imageInput = document.getElementById("image-input");
    const file = imageInput.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("image", file);
    formData.append("language", language);
    fetch("/language-training/image", {
      method: "POST",
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      const resultDiv = document.getElementById("image-result");
      if (data.error) {
        resultDiv.textContent = data.error;
      } else {
        resultDiv.textContent = `Image: ${data.label || ''} | ${data.description}`;
        if (data.audio) {
          const audio = document.getElementById("audio-player");
          audio.src = data.audio;
          audio.style.display = "block";
          audio.play();
        }
      }
    });
  };
}

// Interview Section Logic
if (document.getElementById("mic-btn-interview")) {
  let recognition, recognizing = false;
  function fetchInterview(user_input) {
    fetch("/interview/api", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_input })
    })
    .then(res => res.json())
    .then(data => {
      document.getElementById("interview-prompt").textContent = data.prompt;
      playAudio(data.audio);
    });
  }
  function playAudio(url) {
    const audio = document.getElementById("audio-player-interview");
    audio.src = url;
    audio.style.display = "block";
    audio.play();
  }
  document.getElementById("mic-btn-interview").onclick = function() {
    if (!('webkitSpeechRecognition' in window)) {
      alert("Speech recognition not supported in this browser.");
      return;
    }
    if (!recognition) {
      recognition = new webkitSpeechRecognition();
      recognition.lang = "en-US";
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        fetchInterview(transcript);
      };
      recognition.onstart = function() {
        recognizing = true;
        document.getElementById("mic-status-interview").textContent = "Listening...";
      };
      recognition.onend = function() {
        recognizing = false;
        document.getElementById("mic-status-interview").textContent = "";
      };
    }
    recognition.start();
  };
  // Start with first prompt
  fetchInterview("");
}

// Theme toggle logic
function setTheme(light) {
  document.body.classList.toggle('light', light);
  
  // Handle header/navbar
  const header = document.querySelector('header');
  if (header) header.classList.toggle('light', light);
  
  const navbar = document.querySelector('.navbar');
  if (navbar) navbar.classList.toggle('light', light);
  
  // Handle main content areas
  const card = document.querySelector('.center-card');
  if (card) card.classList.toggle('light', light);
  
  const mainHero = document.querySelector('.main-hero');
  if (mainHero) mainHero.classList.toggle('light', light);
  
  // Handle buttons
  document.querySelectorAll('.btn.accent, .btn.primary').forEach(btn => btn.classList.toggle('light', light));
  document.querySelectorAll('.btn.secondary').forEach(btn => btn.classList.toggle('light', light));
  document.querySelectorAll('.hero-btn').forEach(btn => btn.classList.toggle('light', light));
}

// Initialize theme on page load
function initTheme() {
  const saved = localStorage.getItem('theme');
  const themeSwitch = document.getElementById('toggle-switch');
  
  if (themeSwitch) {
    if (saved === 'light') {
      themeSwitch.checked = true;
      setTheme(true);
    }
    
    themeSwitch.addEventListener('change', function() {
      setTheme(this.checked);
      localStorage.setItem('theme', this.checked ? 'light' : 'dark');
    });
  }
}

// Run theme initialization when DOM is loaded
document.addEventListener('DOMContentLoaded', initTheme); 
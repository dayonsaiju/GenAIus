function setupChatForm(endpoint, langCode) {
    const form = document.getElementById('chat-form');
    const input = document.getElementById('user_input');
    const chatHistory = document.getElementById('chat-history');
    const audioPlayer = document.getElementById('audio-player');
    const micBtn = document.getElementById('mic-btn');
    const micStatus = document.getElementById('mic-status');
    if (!form) return;
    input.style.display = 'none'; // Hide text input
    micBtn.style.display = 'inline-block';
    let recognizing = false;
    let recognition;
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.lang = langCode || 'en-US';
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.onstart = function() {
            recognizing = true;
            micStatus.textContent = 'Listening...';
        };
        recognition.onend = function() {
            recognizing = false;
            micStatus.textContent = '';
        };
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            // Send transcript to backend
            sendUserInput(transcript);
        };
        micBtn.onclick = function() {
            if (recognizing) {
                recognition.stop();
                return;
            }
            recognition.start();
        };
    } else {
        micBtn.disabled = true;
        micStatus.textContent = 'Speech recognition not supported.';
    }
    function sendUserInput(text) {
        const userMsg = document.createElement('div');
        userMsg.className = 'msg user';
        userMsg.textContent = 'User: ' + text;
        chatHistory.appendChild(userMsg);
        const formData = new FormData();
        formData.append('user_input', text);
        fetch(endpoint, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            const botMsg = document.createElement('div');
            botMsg.className = 'msg groq';
            botMsg.textContent = 'AI: ' + data.reply;
            chatHistory.appendChild(botMsg);
            if (data.audio) {
                audioPlayer.src = data.audio;
                audioPlayer.style.display = 'block';
                audioPlayer.play();
            }
            chatHistory.scrollTop = chatHistory.scrollHeight;
        });
    }
} 
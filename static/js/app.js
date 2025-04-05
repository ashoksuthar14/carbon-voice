document.addEventListener('DOMContentLoaded', function() {
    const voiceButton = document.getElementById('voice-input');
    const recordingStatus = document.getElementById('recording-status');
    const statusText = document.getElementById('status-text');
    const lastCommand = document.getElementById('last-command');
    const transcript = document.getElementById('transcript');
    
    let isRecording = false;
    let mediaRecorder = null;
    let audioChunks = [];
    
    // Speech recognition setup
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.continuous = true;
    recognition.interimResults = true;

    // Text-to-speech setup
    const synth = window.speechSynthesis;
    
    function speakResponse(text) {
        // Cancel any ongoing speech
        synth.cancel();

        // Create new utterance
        const utterance = new SpeechSynthesisUtterance(text);
        
        // Configure voice settings
        utterance.rate = 1.0;  // Normal speed
        utterance.pitch = 1.0; // Normal pitch
        utterance.volume = 1.0; // Full volume
        
        // Try to use a female voice if available
        const voices = synth.getVoices();
        const femaleVoice = voices.find(voice => 
            voice.name.toLowerCase().includes('female') || 
            voice.name.toLowerCase().includes('zira'));
        if (femaleVoice) {
            utterance.voice = femaleVoice;
        }
        
        // Speak the response
        synth.speak(utterance);
    }

    // Add transcript entry
    function addTranscriptEntry(text, isFinal = false) {
        const entry = document.createElement('div');
        entry.className = `p-3 ${isFinal ? 'bg-blue-50' : 'bg-gray-50'} rounded-lg mb-2`;
        entry.textContent = text;
        
        if (!isFinal) {
            entry.id = 'interim-transcript';
        } else {
            const existingInterim = document.getElementById('interim-transcript');
            if (existingInterim) {
                existingInterim.remove();
            }
        }
        
        transcript.appendChild(entry);
        transcript.scrollTop = transcript.scrollHeight;
        
        if (isFinal) {
            lastCommand.textContent = text;
        }
    }

    // Speech recognition event handlers
    recognition.onstart = () => {
        isRecording = true;
        recordingStatus.classList.remove('hidden');
        voiceButton.classList.add('bg-red-500');
        voiceButton.classList.remove('bg-blue-500');
        statusText.textContent = 'Listening...';
    };

    recognition.onend = () => {
        isRecording = false;
        recordingStatus.classList.add('hidden');
        voiceButton.classList.remove('bg-red-500');
        voiceButton.classList.add('bg-blue-500');
        statusText.textContent = 'Click the microphone to start speaking';
    };

    recognition.onresult = (event) => {
        const interimTranscript = Array.from(event.results)
            .map(result => result[0].transcript)
            .join('');

        addTranscriptEntry(interimTranscript, event.results[0].isFinal);

        if (event.results[0].isFinal) {
            sendTranscriptToServer(interimTranscript);
            // Stop recognition while processing to avoid feedback loop
            recognition.stop();
        }
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        statusText.textContent = `Error: ${event.error}`;
    };

    function sendTranscriptToServer(transcript) {
        statusText.textContent = 'Processing...';
        
        fetch('/process_command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ command: transcript })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Server response:', data);
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            if (data.response) {
                // Add the response to the transcript
                addTranscriptEntry(`🤖 ${data.response}`, true);
                statusText.textContent = 'Ready to listen';
                speakResponse(data.response);
            }

            // Restart recognition after response
            setTimeout(() => {
                if (!isRecording) {
                    try {
                        recognition.start();
                    } catch (e) {
                        console.warn('Could not restart recognition:', e);
                    }
                }
            }, 1000);
        })
        .catch(error => {
            console.error('Error:', error);
            const errorMessage = error.message || 'Error processing command. Please try again.';
            statusText.textContent = errorMessage;
            addTranscriptEntry(`❌ ${errorMessage}`, true);
            speakResponse('I encountered an error. Please try again.');
            
            // Restart recognition after error
            setTimeout(() => {
                if (!isRecording) {
                    try {
                        recognition.start();
                    } catch (e) {
                        console.warn('Could not restart recognition:', e);
                    }
                }
            }, 1000);
        });
    }

    function toggleRecording() {
        if (!isRecording) {
            recognition.start();
        } else {
            recognition.stop();
        }
    }

    // Event listener for voice button
    voiceButton.addEventListener('click', toggleRecording);
});

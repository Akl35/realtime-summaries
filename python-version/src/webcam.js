// Initialize the webcam and set event listeners
function initializeWebcam() {
    const video = document.getElementById('webcam');
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            video.srcObject = stream;
        })
        .catch(error => {
            console.error('getUserMedia error:', error);
            // You can update this to show an error message to the user in the UI.
        });
}

let imageInProcess = false;

// Send the image to the server for processing
async function processImage(base64Image) {
    // toggleLoader(true); // Show the loader
    if (imageInProcess) return;

    imageInProcess = true;

    // CHANGE THIS LINK! IF USING BLIP-2
    await fetch('https://834c-35-229-183-111.ngrok.io/summarize', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ image: base64Image })
    })
    .then(response => response.json())
    .then(handleResponse)
    .catch(handleError)
    .finally(() => { imageInProcess = false; });
}

// Function to send real-time webcam video to the backend
function sendVideoToBackend() {   
    
    // const socket = io.connect("https://a4e6-34-91-125-5.ngrok-free.app/");

    let frameInterval = null;
    const video = document.getElementById('webcam');
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');

    console.log("BEFORE CONNECTION");

    frameInterval = setInterval(async () => {
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        const base64Image = canvas.toDataURL('image/jpeg').split(',')[1];
        processImage(base64Image);
    }, 2000);

    console.log("FINISHED");
}

// CHANGE THIS
const socket = io.connect("http://127.0.0.1:5001");
var frameInterval2 = null;

function initializeSocket() {
    socket.on('connect', () => {
        console.log('WebSocket connection opened.');
    });
}

function disconnectSocket() {
    socket.disconnect();
    console.log("Web connection closed.")
    clearInterval(frameInterval2);
}

function createMessage(video, canvas) {

    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const base64Image = canvas.toDataURL('image/jpeg').split(',')[1];

    console.log(base64Image);
    socket.emit('summarize', {data: base64Image});

}

function getSummariesGPTV() {
    const video = document.getElementById('webcam');
    const canvas = document.createElement('canvas');

    // socket = io.connect("http://127.0.0.1:5001");

    // socket.on('connect', () => {
    //     console.log('WebSocket connection opened.');
    // });

    frameInterval2 = setInterval(() => {createMessage(video, canvas)}, 20000);

    socket.on("error", (error) => {
        console.log(error);
        console.log(socket.id);
    });

    socket.on('summary', event => {
        console.log('Message from server:', event.summary);
        appendToChatbox(event.summary);
    })
}

// Handle the server response
function handleResponse(data) {
    // toggleLoader(false); // Hide the loader
    console.log(data);
    if(data.error) {
        console.error(data.error);
        appendToChatbox(`Error: ${data.error}`, true);
        return;
    } else if (data.summary) {
        appendToChatbox(data.summary);
        return;
    } else {
        appendToChatbox(data);
        return;
    }
}
    

// Handle any errors during fetch
function handleError(error) {
    toggleLoader(false); // Hide the loader
    console.error('Fetch error:', error);
    appendToChatbox(`Error: ${error.message}`, true);
}

// Toggle the visibility of the loader
function toggleLoader(show) {
    document.querySelector('.loader').style.display = show ? 'block' : 'none';
}

// Append messages to the chatbox
function appendToChatbox(message, isUserMessage = false) {
    const chatbox = document.getElementById('chatbox');
    const messageElement = document.createElement('div');
    const timestamp = new Date().toLocaleTimeString(); // Get the current time as a string
    
    // Assign different classes based on the sender for CSS styling
    messageElement.className = isUserMessage ? 'user-message' : 'assistant-message';

    messageElement.innerHTML = `<div class="message-content">${message}</div>
                                <div class="timestamp">${timestamp}</div>`;
    if (chatbox.firstChild) {
        chatbox.insertBefore(messageElement, chatbox.firstChild);
    } else {
        chatbox.appendChild(messageElement);
    }
}

// Function to switch the camera source
function switchCamera() {
    const video = document.getElementById('webcam');
    let usingFrontCamera = true; // This assumes the initial camera is the user-facing one

    return function() {
        // Toggle the camera type
        usingFrontCamera = !usingFrontCamera;
        const constraints = {
            video: { facingMode: (usingFrontCamera ? 'user' : 'environment') }
        };
        
        // Stop any previous stream
        if (video.srcObject) {
            video.srcObject.getTracks().forEach(track => track.stop());
        }
        
        // Start a new stream with the new constraints
        navigator.mediaDevices.getUserMedia(constraints)
            .then(stream => {
                video.srcObject = stream;
            })
            .catch(error => {
                console.error('Error accessing media devices.', error);
            });
    };
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    initializeWebcam();
    initializeSocket();

    document.getElementById('capture').addEventListener('click', getSummariesGPTV);
    document.getElementById('switch-camera').addEventListener('click', switchCamera);

    // Other event listeners here...
});

// Global state
let state = {
    sessionId: null,
    filePath: null,
    frameUrl: null,
    videoProperties: null,
    rois: [],
    isDrawing: false,
    startX: 0,
    startY: 0,
    currentStep: 1,
};

const elements = {
    uploadArea: document.getElementById('uploadArea'),
    videoInput: document.getElementById('videoInput'),
    uploadProgress: document.getElementById('uploadProgress'),
    uploadProgressFill: document.getElementById('uploadProgressFill'),
    uploadStatus: document.getElementById('uploadStatus'),
    uploadSection: document.getElementById('uploadSection'),
    selectionSection: document.getElementById('selectionSection'),
    settingsSection: document.getElementById('settingsSection'),
    processingSection: document.getElementById('processingSection'),
    downloadSection: document.getElementById('downloadSection'),
    frameImage: document.getElementById('frameImage'),
    canvasOverlay: document.getElementById('canvasOverlay'),
    roiCount: document.getElementById('roiCount'),
    clearButton: document.getElementById('clearButton'),
    undoButton: document.getElementById('undoButton'),
    protectBottom: document.getElementById('protectBottom'),
    protectBottomValue: document.getElementById('protectBottomValue'),
    method: document.getElementById('method'),
    videoInfo: document.getElementById('videoInfo'),
    videoRes: document.getElementById('videoRes'),
    videoFps: document.getElementById('videoFps'),
    videoDuration: document.getElementById('videoDuration'),
    backButton: document.getElementById('backButton'),
    nextButton: document.getElementById('nextButton'),
    downloadButton: document.getElementById('downloadButton'),
    processAnotherButton: document.getElementById('processAnotherButton'),
    processingStatus: document.getElementById('processingStatus'),
    processingProgressFill: document.getElementById('processingProgressFill'),
    processingTime: document.getElementById('processingTime'),
};

// Upload functionality
elements.uploadArea.addEventListener('click', () => {
    elements.videoInput.click();
});

elements.uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.uploadArea.classList.add('drag-over');
});

elements.uploadArea.addEventListener('dragleave', () => {
    elements.uploadArea.classList.remove('drag-over');
});

elements.uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.uploadArea.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleVideoUpload(files[0]);
    }
});

elements.videoInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleVideoUpload(e.target.files[0]);
    }
});

function handleVideoUpload(file) {
    const validExtensions = ['mp4', 'mov', 'avi', 'mkv', 'webm', 'flv', 'm4v'];
    const extension = file.name.split('.').pop().toLowerCase();

    if (!validExtensions.includes(extension)) {
        showError('Invalid file type. Supported: MP4, MOV, AVI, MKV, WebM, FLV, M4V');
        return;
    }

    if (file.size > 2 * 1024 * 1024 * 1024) {
        showError('File too large. Maximum size: 2GB');
        return;
    }

    uploadVideo(file);
}

function uploadVideo(file) {
    const formData = new FormData();
    formData.append('video', file);

    elements.uploadProgress.style.display = 'block';

    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            elements.uploadProgressFill.style.width = percentComplete + '%';
            elements.uploadStatus.textContent = `Uploading... ${Math.round(percentComplete)}%`;
        }
    });

    xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
            const response = JSON.parse(xhr.responseText);
            state.sessionId = response.sessionId;
            state.filePath = response.filePath;
            state.frameUrl = response.frameUrl;
            state.videoProperties = response.properties;

            // Update UI
            elements.uploadProgress.style.display = 'none';
            setupVideoInfo();
            goToStep(2);
        } else {
            const error = JSON.parse(xhr.responseText);
            showError(error.error || 'Upload failed');
        }
    });

    xhr.addEventListener('error', () => {
        showError('Upload failed');
    });

    xhr.open('POST', '/api/upload', true);
    xhr.send(formData);
}

function setupVideoInfo() {
    const props = state.videoProperties;
    elements.videoRes.textContent = `${props.width}x${props.height}`;
    elements.videoFps.textContent = props.fps.toFixed(1);
    elements.videoDuration.textContent = props.duration.toFixed(1);
    elements.videoInfo.style.display = 'block';

    // Load frame image
    elements.frameImage.onload = () => {
        setupCanvasOverlay();
    };
    elements.frameImage.src = state.frameUrl;
}

function setupCanvasOverlay() {
    const rect = elements.frameImage.getBoundingClientRect();
    elements.canvasOverlay.style.width = rect.width + 'px';
    elements.canvasOverlay.style.height = rect.height + 'px';
    elements.canvasOverlay.style.position = 'absolute';
    elements.canvasOverlay.style.display = 'block';

    const frameContainer = elements.frameImage.parentElement;
    frameContainer.style.position = 'relative';

    // Scale factor for coordinates mapping
    const scaleX = state.videoProperties.width / elements.frameImage.width;
    const scaleY = state.videoProperties.height / elements.frameImage.height;

    elements.canvasOverlay.addEventListener('mousedown', (e) => {
        state.isDrawing = true;
        state.startX = e.offsetX * scaleX;
        state.startY = e.offsetY * scaleY;
    });

    elements.canvasOverlay.addEventListener('mousemove', (e) => {
        if (state.isDrawing) {
            // Visual feedback (you could draw on canvas here)
        }
    });

    elements.canvasOverlay.addEventListener('mouseup', (e) => {
        if (state.isDrawing) {
            state.isDrawing = false;
            const currentX = e.offsetX * scaleX;
            const currentY = e.offsetY * scaleY;
            const width = Math.abs(currentX - state.startX);
            const height = Math.abs(currentY - state.startY);

            if (width > 20 && height > 20) {
                const roi = [
                    Math.min(state.startX, currentX),
                    Math.min(state.startY, currentY),
                    width,
                    height
                ];
                state.rois.push(roi);
                updateROICount();

                // Visual feedback
                drawROIs();
            }
        }
    });

    // Add visual ROI drawing
    const canvas = document.createElement('canvas');
    canvas.width = elements.frameImage.width;
    canvas.height = elements.frameImage.height;
    canvas.style.position = 'absolute';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.id = 'drawingCanvas';
    frameContainer.insertBefore(canvas, frameContainer.lastChild);
    state.drawingCanvas = canvas;

    elements.canvasOverlay.addEventListener('mousemove', (e) => {
        if (state.isDrawing) {
            const currentX = e.offsetX * scaleX;
            const currentY = e.offsetY * scaleY;
            redrawCanvas(state.startX, state.startY, currentX, currentY);
        }
    });
}

function redrawCanvas(startX, startY, endX, endY) {
    if (!state.drawingCanvas) return;

    const ctx = state.drawingCanvas.getContext('2d');
    const imgWidth = elements.frameImage.width;
    const imgHeight = elements.frameImage.height;
    const scaleX = imgWidth / state.videoProperties.width;
    const scaleY = imgHeight / state.videoProperties.height;

    ctx.clearRect(0, 0, imgWidth, imgHeight);

    // Draw existing ROIs
    for (const roi of state.rois) {
        const [x, y, w, h] = roi;
        ctx.strokeStyle = '#10b981';
        ctx.lineWidth = 2;
        ctx.strokeRect(x * scaleX, y * scaleY, w * scaleX, h * scaleY);
    }

    // Draw current selection
    if (state.isDrawing) {
        const x = Math.min(startX, endX);
        const y = Math.min(startY, endY);
        const w = Math.abs(endX - startX);
        const h = Math.abs(endY - startY);

        ctx.strokeStyle = '#6366f1';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.strokeRect(x * scaleX, y * scaleY, w * scaleX, h * scaleY);
        ctx.setLineDash([]);
    }
}

function drawROIs() {
    redrawCanvas(state.startX, state.startY, state.startX, state.startY);
}

function updateROICount() {
    elements.roiCount.textContent = `Watermarks selected: ${state.rois.length}`;
    elements.clearButton.style.display = state.rois.length > 0 ? 'block' : 'none';
    elements.undoButton.style.display = state.rois.length > 0 ? 'block' : 'none';
}

elements.clearButton.addEventListener('click', () => {
    state.rois = [];
    updateROICount();
    drawROIs();
});

elements.undoButton.addEventListener('click', () => {
    if (state.rois.length > 0) {
        state.rois.pop();
        updateROICount();
        drawROIs();
    }
});

// Settings
elements.protectBottom.addEventListener('input', (e) => {
    elements.protectBottomValue.textContent = e.target.value + '%';
});

// Navigation
function goToStep(step) {
    state.currentStep = step;

    // Hide all sections
    const sections = [
        elements.uploadSection,
        elements.selectionSection,
        elements.settingsSection,
        elements.processingSection,
        elements.downloadSection
    ];

    sections.forEach(section => {
        section.classList.remove('active');
    });

    // Show current section
    [
        elements.uploadSection,
        elements.selectionSection,
        elements.settingsSection,
        elements.processingSection,
        elements.downloadSection
    ][step - 1].classList.add('active');

    // Update navigation buttons
    updateNavigationButtons();
}

function updateNavigationButtons() {
    const step = state.currentStep;
    const canContinue = step < 5 && (step === 1 || (step === 2 && state.rois.length > 0));

    if (step === 1) {
        elements.backButton.style.display = 'none';
        elements.nextButton.style.display = 'none';
    } else if (step === 5) {
        elements.backButton.style.display = 'none';
        elements.nextButton.style.display = 'none';
    } else {
        elements.backButton.style.display = 'block';
        elements.nextButton.style.display = 'block';
        elements.nextButton.disabled = !canContinue;
    }
}

elements.backButton.addEventListener('click', () => {
    goToStep(Math.max(1, state.currentStep - 1));
});

elements.nextButton.addEventListener('click', () => {
    if (state.currentStep === 2 && state.rois.length === 0) {
        showError('Please select at least one watermark');
        return;
    }

    if (state.currentStep === 3) {
        processVideo();
    } else {
        goToStep(state.currentStep + 1);
    }
});

// Processing
function processVideo() {
    goToStep(4);

    const data = {
        sessionId: state.sessionId,
        rois: state.rois,
        protectBottom: parseFloat(elements.protectBottom.value),
        method: elements.method.value
    };

    fetch('/api/process', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            pollProcessingStatus();
        } else {
            showError(data.error || 'Processing failed');
            goToStep(3);
        }
    })
    .catch(error => {
        showError('Processing error: ' + error);
        goToStep(3);
    });
}

function pollProcessingStatus() {
    const pollInterval = setInterval(() => {
        fetch(`/api/status/${state.sessionId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'complete') {
                clearInterval(pollInterval);
                elements.downloadButton.href = `/api/download/${state.sessionId}`;
                goToStep(5);
            }
        });
    }, 2000);

    // Timeout after 1 hour
    setTimeout(() => {
        clearInterval(pollInterval);
        showError('Processing timeout');
        goToStep(3);
    }, 60 * 60 * 1000);
}

elements.processAnotherButton.addEventListener('click', () => {
    location.reload();
});

// Error handling
function showError(message) {
    const modal = document.getElementById('errorModal');
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
    modal.style.display = 'flex';
}

function closeErrorModal() {
    document.getElementById('errorModal').style.display = 'none';
}

window.addEventListener('click', (e) => {
    const modal = document.getElementById('errorModal');
    if (e.target === modal) {
        modal.style.display = 'none';
    }
});

// Initialize
goToStep(1);
updateROICount();

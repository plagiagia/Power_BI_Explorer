document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const uploadProgress = document.getElementById('upload-progress');
    const progressBar = uploadProgress.querySelector('.progress-bar');
    const progressText = uploadProgress.querySelector('.progress-text');
    const uploadStatus = document.getElementById('upload-status');

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight() {
        uploadArea.classList.add('highlight');
    }

    function unhighlight() {
        uploadArea.classList.remove('highlight');
    }

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });

    function validateFile(file) {
        const allowedTypes = ['.bim', '.json', '.tsv'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        return allowedTypes.includes(fileExtension);
    }

    function showProgress(show = true) {
        uploadProgress.style.display = show ? 'block' : 'none';
    }

    function updateProgress(percent) {
        progressBar.style.width = `${percent}%`;
        progressText.textContent = `${Math.round(percent)}%`;
    }

    function showStatus(message, isError = false) {
        uploadStatus.textContent = message;
        uploadStatus.className = 'upload-status ' + (isError ? 'error' : 'success');
        uploadStatus.style.display = 'block';
        setTimeout(() => {
            uploadStatus.style.display = 'none';
        }, 5000);
    }

    async function handleFiles(files) {
        const validFiles = Array.from(files).filter(validateFile);
        
        if (validFiles.length === 0) {
            showStatus('Please upload only .bim, .json, or .tsv files', true);
            return;
        }

        showProgress();
        updateProgress(0);

        for (let i = 0; i < validFiles.length; i++) {
            const file = validFiles[i];
            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                const progressPercent = ((i + 1) / validFiles.length) * 100;
                updateProgress(progressPercent);

                if (result.success) {
                    showStatus(`${file.name} uploaded successfully`);
                } else {
                    showStatus(`Error uploading ${file.name}: ${result.error}`, true);
                }
            } catch (error) {
                showStatus(`Error uploading ${file.name}: ${error.message}`, true);
            }
        }

        setTimeout(() => {
            showProgress(false);
        }, 1000);
    }

    uploadArea.addEventListener('drop', function(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    });

    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });
});

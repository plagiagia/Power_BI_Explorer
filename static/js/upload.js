document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const uploadStatus = document.getElementById('uploadStatus');

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            
            if (result.success) {
                uploadStatus.textContent = 'File uploaded successfully!';
                uploadStatus.className = 'success';
            } else {
                uploadStatus.textContent = result.error || 'Upload failed';
                uploadStatus.className = 'error';
            }
        } catch (error) {
            uploadStatus.textContent = 'Upload failed: ' + error;
            uploadStatus.className = 'error';
        }
    });
});

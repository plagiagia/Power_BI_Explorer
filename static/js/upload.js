document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.querySelector('.upload-area');
    const fileInput = document.querySelector('#file-input');

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        uploadArea.classList.add('highlight');
    }

    function unhighlight() {
        uploadArea.classList.remove('highlight');
    }

    uploadArea.addEventListener('drop', handleDrop, false);
    fileInput.addEventListener('change', handleFileSelect, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    function handleFileSelect(e) {
        const files = e.target.files;
        handleFiles(files);
    }

    async function handleFiles(files) {
        const file = files[0];
        if (!file) return;

        if (!file.name.endsWith('.bim') && !file.name.endsWith('.json')) {
            alert('Please upload a .bim or report.json file');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            if (result.success) {
                displayFileContent(result.data);
            } else {
                alert('Error: ' + result.error);
            }
        } catch (error) {
            alert('Error uploading file: ' + error.message);
        }
    }

    function displayFileContent(data) {
        const contentArea = document.querySelector('#file-content');
        contentArea.innerHTML = '';

        const card = document.createElement('div');
        card.classList.add('data-card');

        if (data.tables) {
            // Display .bim file content
            const tablesList = data.tables.map(table => `
                <div class="mb-3">
                    <h5>${table.name}</h5>
                    <p>Columns: ${table.columns.join(', ')}</p>
                </div>
            `).join('');

            card.innerHTML = `
                <h4>Model Structure</h4>
                <div class="tables-container">
                    ${tablesList}
                </div>
            `;
        } else if (data.pages) {
            // Display report.json content
            const pagesList = data.pages.map(page => `
                <div class="mb-3">
                    <h5>${page.name}</h5>
                    <p>Visualizations: ${page.visuals.join(', ')}</p>
                </div>
            `).join('');

            card.innerHTML = `
                <h4>Report Structure</h4>
                <div class="pages-container">
                    ${pagesList}
                </div>
            `;
        }

        contentArea.appendChild(card);
    }
});

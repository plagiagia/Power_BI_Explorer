document.addEventListener('DOMContentLoaded', function() {
    const chatContainer = document.querySelector('.chat-container');
    const queryInput = document.querySelector('.query-input');
    const queryForm = document.querySelector('#query-form');

    // Initialize Chart.js
    Chart.defaults.color = '#252525';
    Chart.defaults.font.family = "'Segoe UI', sans-serif";

    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(isUser ? 'user-message' : 'system-message');
        messageDiv.textContent = message;
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function createChart(data, containerId) {
        const ctx = document.getElementById(containerId).getContext('2d');
        return new Chart(ctx, {
            type: data.chart_type || 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Values',
                    data: data.values,
                    backgroundColor: '#0078d4',
                    borderColor: '#0078d4',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                }
            }
        });
    }

    function displayQueryResult(result) {
        const resultContainer = document.createElement('div');
        resultContainer.classList.add('data-card', 'mt-3');
        
        if (result.type === 'data' && result.result) {
            const chartId = 'chart-' + Date.now();
            resultContainer.innerHTML = `
                <p>${result.explanation}</p>
                <div class="chart-container" style="height: 300px;">
                    <canvas id="${chartId}"></canvas>
                </div>
            `;
            chatContainer.appendChild(resultContainer);
            createChart(result.result, chartId);
        } else {
            resultContainer.textContent = result.explanation || 'No results found';
            chatContainer.appendChild(resultContainer);
        }
    }

    queryForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const query = queryInput.value.trim();
        if (!query) return;

        addMessage(query, true);
        queryInput.value = '';

        try {
            const response = await fetch('/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query })
            });

            const data = await response.json();
            if (data.success) {
                displayQueryResult(data.result);
            } else {
                addMessage('Error: ' + data.error);
            }
        } catch (error) {
            addMessage('Error processing query: ' + error.message);
        }
    });
});

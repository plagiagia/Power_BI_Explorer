const COPY_ICON = "fa-copy";
const COPIED_ICON = "fa-check";
const EXPAND_ICON = "fa-expand";
const COLLAPSE_ICON = "fa-compress";
const COPY_TIMEOUT = 2000;

document.addEventListener("DOMContentLoaded", function () {
    Prism.highlightAll();
    initializeComplexityCharts();
});

function calculateComplexity(daxExpression) {
    const length = daxExpression.length;
    const functionCount = (daxExpression.match(/[A-Z]+\(/g) || []).length;
    const nestedLevel = (daxExpression.match(/\(/g) || []).length;

    const lengthScore = Math.min(length / 500, 1) * 0.3;
    const functionScore = Math.min(functionCount / 10, 1) * 0.4;
    const nestingScore = Math.min(nestedLevel / 5, 1) * 0.3;

    return {
        total: Math.round((lengthScore + functionScore + nestingScore) * 100),
        lengthScore: Math.round(lengthScore * 100),
        functionScore: Math.round(functionScore * 100),
        nestingScore: Math.round(nestingScore * 100),
    };
}

function createDonutChart(canvas, complexity) {
    // Clear any existing chart
    const existingChart = Chart.getChart(canvas);
    if (existingChart) {
        existingChart.destroy();
    }

    const ctx = canvas.getContext("2d");
    new Chart(ctx, {
        type: "doughnut",
        data: {
            datasets: [
                {
                    data: [complexity, 100 - complexity],
                    backgroundColor: [
                        complexity > 80
                            ? "#ef4444"
                            : complexity > 60
                              ? "#f97316"
                              : complexity > 40
                                ? "#eab308"
                                : "#22c55e",
                        "rgba(255, 255, 255, 0.1)",
                    ],
                    borderWidth: 0,
                    cutout: "80%",
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false },
            },
        },
    });
}

function initializeComplexityCharts() {
    const cards = document.querySelectorAll(".expression-card");
    cards.forEach((card) => {
        const daxExpression = card.querySelector("code").textContent;
        const complexity = calculateComplexity(daxExpression);
        const canvas = card.querySelector(".donut-chart");
        createDonutChart(canvas, complexity.total);
        card.querySelector(".complexity-score").textContent =
            `${complexity.total}%`;
    });
}

function toggleExpand(button) {
    const card = button.closest(".expression-card");
    const title = card.querySelector("h3").textContent;
    const codeText = card.querySelector("code").textContent;
    const complexity = calculateComplexity(codeText);

    // Update modal content
    document.getElementById("modal-title").textContent = title;
    document.getElementById("length-score").textContent =
        complexity.lengthScore;
    document.getElementById("function-score").textContent =
        complexity.functionScore;
    document.getElementById("nesting-score").textContent =
        complexity.nestingScore;

    // Update code content
    const modalBody = document.querySelector(".modal-body");
    modalBody.innerHTML = "";

    const preElement = document.createElement("pre");
    const codeElement = document.createElement("code");
    preElement.className = "language-dax";
    codeElement.className = "language-dax";
    codeElement.id = "modal-code";
    codeElement.textContent = codeText;

    preElement.appendChild(codeElement);
    modalBody.appendChild(preElement);

    // Show modal
    const modal = document.getElementById("modal");
    modal.classList.add("show");

    // Update donut chart
    const modalCanvas = modal.querySelector(".modal-donut-chart");
    createDonutChart(modalCanvas, complexity.total);
    modal.querySelector(".complexity-score").textContent =
        `${complexity.total}%`;

    // Highlight code
    Prism.highlightElement(codeElement);
}

function closeModal() {
    const modal = document.getElementById("modal");
    modal.classList.remove("show");
}

function copyExpression(button) {
    const card = button.closest(".expression-card");
    const codeElement = card.querySelector("code");
    const icon = button.querySelector("i");

    navigator.clipboard
        .writeText(codeElement.textContent)
        .then(() => {
            icon.classList.remove(COPY_ICON);
            icon.classList.add(COPIED_ICON);
            showToast("Expression copied to clipboard!");

            setTimeout(() => {
                icon.classList.remove(COPIED_ICON);
                icon.classList.add(COPY_ICON);
            }, COPY_TIMEOUT);
        })
        .catch((err) => {
            showToast("Failed to copy expression", "error");
        });
}

function copyModalExpression() {
    const codeElement = document.getElementById("modal-code");
    const copyButton = document.querySelector(
        ".modal-actions .action-btn i.fa-copy",
    );

    navigator.clipboard
        .writeText(codeElement.textContent)
        .then(() => {
            copyButton.classList.remove(COPY_ICON);
            copyButton.classList.add(COPIED_ICON);
            showToast("Expression copied to clipboard!");

            setTimeout(() => {
                copyButton.classList.remove(COPIED_ICON);
                copyButton.classList.add(COPY_ICON);
            }, COPY_TIMEOUT);
        })
        .catch((err) => {
            showToast("Failed to copy expression", "error");
        });
}

function showToast(message, type = "success") {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i class="fas ${type === "success" ? "fa-check" : "fa-exclamation-circle"}"></i>
        <span>${message}</span>
    `;
    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add("show"), 100);
    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

document.getElementById("searchInput").addEventListener("input", function (e) {
    const searchTerm = e.target.value.toLowerCase();
    const cards = document.querySelectorAll(".expression-card");

    cards.forEach((card) => {
        const measureName = card.querySelector("h3").textContent.toLowerCase();
        const daxExpression = card
            .querySelector("code")
            .textContent.toLowerCase();
        const isVisible =
            measureName.includes(searchTerm) ||
            daxExpression.includes(searchTerm);
        card.style.display = isVisible ? "flex" : "none";
    });
});

// Close modal when clicking outside
window.onclick = function (event) {
    const modal = document.getElementById("modal");
    if (event.target === modal) {
        closeModal();
    }
};

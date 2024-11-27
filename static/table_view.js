// Global variables
let tableData = [];
let visibleColumns = new Set([0, 1, 2, 3, 4, 5, 6]); // All columns visible by default
let currentSortColumn = null;
let isAscending = true;

// Initialize when document is ready
document.addEventListener("DOMContentLoaded", function() {
    // Get table data
    const table = document.getElementById("visuals-table");
    if (table) {
        const tbody = table.querySelector("tbody");
        if (tbody) {
            tableData = Array.from(tbody.getElementsByTagName("tr")); // Only get rows from tbody
        }

        // Initialize search functionality
        const searchBox = document.getElementById("searchBox");
        if (searchBox) {
            searchBox.addEventListener("input", function() {
                filterTable();
            });
        }
        // Initialize column selector
        initializeColumnSelector();
    }
});

// Filter table based on search input
function filterTable() {
    const searchBox = document.getElementById("searchBox");
    if (!searchBox) return;
    const searchTerm = searchBox.value.toLowerCase();
    const tbody = document.querySelector("#visuals-table tbody");
    tableData.forEach((row) => {
        const text = Array.from(row.cells)
            .filter((_, index) => visibleColumns.has(index))
            .map((cell) => cell.textContent.toLowerCase())
            .join(" ");
        if (text.includes(searchTerm)) {
            row.style.display = ""; // Show row
            row.classList.remove("hidden");
        } else {
            row.style.display = "none"; // Hide row
            row.classList.add("hidden");
        }
    });
}

// Sort table
function sortTable(columnIndex) {
    isAscending = columnIndex === currentSortColumn ? !isAscending : true;
    currentSortColumn = columnIndex;

    const tbody = document.querySelector("#visuals-table tbody");
    if (!tbody) return;
    tableData.sort((a, b) => {
        // Ensure both rows have the cell we're trying to sort
        if (!a.cells[columnIndex] || !b.cells[columnIndex]) {
            return 0;
        }
        let aValue = a.cells[columnIndex].textContent.trim();
        let bValue = b.cells[columnIndex].textContent.trim();
        // Convert to numbers and compare if both values are numeric
        const aNum = parseFloat(aValue);
        const bNum = parseFloat(bValue);
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAscending ? aNum - bNum : bNum - aNum;
        }
        // Default string comparison
        return isAscending 
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue);
    });
    // Clear and repopulate tbody
    tbody.innerHTML = '';
    tableData.forEach(row => tbody.appendChild(row));
    // Update sort icons
    document.querySelectorAll("th.sortable i.fas:not(.fa-file-alt):not(.fa-chart-bar):not(.fa-tag):not(.fa-list):not(.fa-filter):not(.fa-cube):not(.fa-cubes)")
        .forEach(icon => {
            icon.className = "fas fa-sort";
        });
    const clickedHeader = document.querySelectorAll("th.sortable")[columnIndex];
    const sortIcon = clickedHeader?.querySelector(
        "i.fas:not(.fa-file-alt):not(.fa-chart-bar):not(.fa-tag):not(.fa-list):not(.fa-filter):not(.fa-cube):not(.fa-cubes)"
    );
    if (sortIcon) {
        sortIcon.className = `fas fa-sort-${isAscending ? "up" : "down"}`;
    }
}


// Column visibility toggle
function toggleColumnSelector() {
    const selector = document.getElementById("columnSelector");
    if (selector) {
        selector.classList.toggle("hidden");
    }
}

function initializeColumnSelector() {
    const columnSelector = document.getElementById("columnSelector");
    const headers = Array.from(document.querySelectorAll("#visuals-table th"));
    if (columnSelector && headers.length > 0) {
        headers.forEach((header, index) => {
            const checkbox = document.createElement("div");
            checkbox.innerHTML = `
                <label>
                    <input type="checkbox" ${visibleColumns.has(index) ? "checked" : ""} 
                           onchange="toggleColumn(${index})">
                    ${header.textContent.trim()}
                </label>
            `;
            columnSelector.appendChild(checkbox);
        });
    }
}

function toggleColumn(columnIndex) {
    if (visibleColumns.has(columnIndex)) {
        visibleColumns.delete(columnIndex);
    } else {
        visibleColumns.add(columnIndex);
    }

    // Update column visibility
    const table = document.getElementById("visuals-table");
    if (table) {
        Array.from(table.rows).forEach((row) => {
            Array.from(row.cells).forEach((cell, index) => {
                cell.style.display = visibleColumns.has(index) ? "" : "none";
            });
        });
    }

    // Re-filter table to update visibility
    filterTable();
}

// Export functions
function exportToExcel() {
    const table = document.getElementById("visuals-table");
    if (!table) return;

    const ws = XLSX.utils.table_to_sheet(table);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Visual Data");
    XLSX.writeFile(wb, "power_bi_visuals.xlsx");
}

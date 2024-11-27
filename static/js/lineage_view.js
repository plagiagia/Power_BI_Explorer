// Configuration constants
const NETWORK_CONFIG = {
    nodes: {
        borderWidth: 2,
        font: {
            color: "#f8fafc",
            size: 14,
        },
        shadow: {
            enabled: true,
            color: "rgba(0,0,0,0.5)",
            size: 5,
        },
    },
    edges: {
        color: {
            color: "rgba(255,255,255,0.5)",
            highlight: "#fff",
            hover: "#fff",
        },
        arrows: {
            to: {
                enabled: true,
                scaleFactor: 1,
                type: "arrow",
            },
        },
        smooth: {
            type: "cubicBezier",
            forceDirection: "horizontal",
        },
    },
    physics: {
        forceAtlas2Based: {
            gravitationalConstant: -26,
            centralGravity: 0.005,
            springLength: 230,
            springConstant: 0.18,
        },
        maxVelocity: 146,
        solver: "forceAtlas2Based",
        timestep: 0.35,
        stabilization: {
            enabled: true,
            iterations: 150,
            updateInterval: 25,
        },
    },
    layout: {
        improvedLayout: true,
        hierarchical: {
            enabled: false,
            levelSeparation: 150,
            nodeSpacing: 100,
            treeSpacing: 200,
            blockShifting: true,
            edgeMinimization: true,
            parentCentralization: true,
            direction: "UD",
            sortMethod: "hubsize",
        },
    },
    interaction: {
        hover: true,
        navigationButtons: true,
        keyboard: true,
        zoomView: true,
        dragNodes: true,
        dragView: true,
    },
};

const COLORS = {
    parent: "#f1c83b",
    final: "#23c4a7",
    column: "#ADD8E6",
    hover: "#ffffff",
};

class LineageNetwork {
    constructor(container, nodesArray, edgesArray) {
        this.container = container;
        this.nodesArray = nodesArray;
        this.edgesArray = edgesArray;
        this.network = null;
        this.parentNodes = new Set(edgesArray.map((edge) => edge.from));
        this.nodeConnections = this.buildNodeConnections();
        this.init();
    }

    init() {
        this.processNodes();
        this.createNetwork();
        this.addEventListeners();
    }

    buildNodeConnections() {
        const connections = new Map();

        this.edgesArray.forEach(edge => {
            if (!connections.has(edge.from)) {
                connections.set(edge.from, { parents: new Set(), children: new Set() });
            }
            if (!connections.has(edge.to)) {
                connections.set(edge.to, { parents: new Set(), children: new Set() });
            }

            connections.get(edge.from).children.add(edge.to);
            connections.get(edge.to).parents.add(edge.from);
        });

        return connections;
    }

    processNodes() {
        this.nodesArray.forEach((node) => {
            if (node.type === "column") {
                node.color = COLORS.column;
                node.shape = "box";
            } else if (this.parentNodes.has(node.id)) {
                node.color = COLORS.parent;
                node.shape = "circle";
            } else {
                node.color = COLORS.final;
                node.shape = "circle";
            }
            node.hover = {
                border: COLORS.hover,
                background: node.color,
            };
        });
    }

    createNetwork() {
        const data = {
            nodes: new vis.DataSet(this.nodesArray),
            edges: new vis.DataSet(this.edgesArray),
        };
        this.network = new vis.Network(this.container, data, NETWORK_CONFIG);
    }

    addEventListeners() {
        this.network.on("click", (params) => {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                this.highlightConnections(nodeId);
                highlightTableRows(nodeId); // Add table row highlighting
            }
        });
    }

    getConnectedNodes(startNodeId, visited = new Set()) {
        const connectedNodes = new Set([startNodeId]);
        visited.add(startNodeId);

        const node = this.nodesArray.find(n => n.id === startNodeId);
        const connections = this.nodeConnections.get(startNodeId);

        if (connections) {
            connections.parents.forEach(parentId => {
                if (!visited.has(parentId)) {
                    connectedNodes.add(parentId);
                    const parentConnections = this.getConnectedNodes(parentId, visited);
                    parentConnections.forEach(id => connectedNodes.add(id));
                }
            });
        }

        return connectedNodes;
    }

    getConnectedEdges(nodeIds) {
        const connectedEdges = new Set();

        this.edgesArray.forEach(edge => {
            if (nodeIds.has(edge.from) && nodeIds.has(edge.to)) {
                connectedEdges.add(edge.id);
            }
        });

        return connectedEdges;
    }

    highlightConnections(nodeId) {
        const connectedNodes = this.getConnectedNodes(nodeId);
        const connectedEdges = this.getConnectedEdges(connectedNodes);

        this.network.setSelection({
            nodes: Array.from(connectedNodes),
            edges: Array.from(connectedEdges),
        });
    }

    filter(selectedMeasure) {
        let updatedNodes = [];
        let updatedEdges = [];

        if (selectedMeasure === "") {
            updatedNodes = this.nodesArray;
            updatedEdges = this.edgesArray;
        } else {
            const connectedNodes = this.getConnectedNodes(selectedMeasure);

            this.edgesArray.forEach(edge => {
                const fromNode = this.nodesArray.find(n => n.id === edge.from);
                if (fromNode && fromNode.type === 'column' && connectedNodes.has(edge.to)) {
                    connectedNodes.add(edge.from);
                }
            });

            updatedNodes = this.nodesArray.filter(node => connectedNodes.has(node.id));
            updatedEdges = this.edgesArray.filter(edge => 
                connectedNodes.has(edge.from) && connectedNodes.has(edge.to)
            );
        }

        this.network.setData({
            nodes: new vis.DataSet(updatedNodes),
            edges: new vis.DataSet(updatedEdges),
        });

        populateTable(updatedNodes, updatedEdges);
    }
}

function populateTable(nodes, edges) {
    const tableBody = document.getElementById("lineageTable").querySelector("tbody");
    tableBody.innerHTML = "";

    // Create a map for quick node lookups
    const nodeMap = new Map(nodes.map(node => [node.id, node]));

    // Create a map to store relationships
    const relationships = new Map();

    // Process edges to build relationships
    edges.forEach(edge => {
        const fromNode = nodeMap.get(edge.from);
        const toNode = nodeMap.get(edge.to);

        if (!fromNode || !toNode) return;

        if (!relationships.has(toNode.id)) {
            relationships.set(toNode.id, {
                measure: toNode,
                parents: new Set(),
                columns: new Set()
            });
        }

        if (fromNode.type === "column") {
            relationships.get(toNode.id).columns.add(fromNode);
        } else {
            relationships.get(toNode.id).parents.add(fromNode);
        }
    });

    // Create table rows
    relationships.forEach(({ measure, parents, columns }) => {
        const row = tableBody.insertRow();
        row.setAttribute('data-measure-id', measure.id);
        row.innerHTML = `
            <td class="measure-cell">${measure.label}</td>
            <td class="parent-cell">${Array.from(parents).map(p => p.label).join(", ")}</td>
            <td class="columns-cell">${Array.from(columns).map(c => c.label).join(", ")}</td>
        `;

        // Add click event to highlight network
        row.addEventListener('click', () => {
            highlightNetwork(measure.id);
            highlightTableRows(measure.id);
        });

        // Add hover effect
        row.addEventListener('mouseenter', () => {
            row.classList.add('highlighted-row');
        });
        row.addEventListener('mouseleave', () => {
            if (!row.classList.contains('selected-row')) {
                row.classList.remove('highlighted-row');
            }
        });
    });

    // Add sorting functionality
    addTableSorting();
}

function highlightTableRows(measureId) {
    // Remove previous highlighting
    document.querySelectorAll('#lineageTable tbody tr').forEach(row => {
        row.classList.remove('selected-row', 'highlighted-row');
    });

    // Highlight the selected row
    const selectedRow = document.querySelector(`#lineageTable tbody tr[data-measure-id="${measureId}"]`);
    if (selectedRow) {
        selectedRow.classList.add('selected-row');
        selectedRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function highlightNetwork(measureId) {
    const network = document.querySelector('#mynetwork').vis;
    if (network) {
        network.selectNodes([measureId]);
    }
}

function addTableSorting() {
    const table = document.getElementById('lineageTable');
    const headers = table.querySelectorAll('th');

    headers.forEach((header, index) => {
        header.addEventListener('click', () => {
            sortTable(table, index);
        });
    });
}

function sortTable(table, column) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const direction = table.querySelector(`th:nth-child(${column + 1})`).classList.contains('asc') ? -1 : 1;

    // Reset all headers
    table.querySelectorAll('th').forEach(th => th.classList.remove('asc', 'desc'));

    // Set new sort direction
    table.querySelector(`th:nth-child(${column + 1})`).classList.add(direction === 1 ? 'asc' : 'desc');

    // Sort rows
    const sortedRows = rows.sort((a, b) => {
        const aText = a.cells[column].textContent.trim();
        const bText = b.cells[column].textContent.trim();
        return direction * aText.localeCompare(bText);
    });

    // Clear and re-add rows
    tbody.innerHTML = '';
    sortedRows.forEach(row => tbody.appendChild(row));
}

function initializeSelect() {
    const selectElement = document.getElementById("measureSelect");
    const parentNodes = new Set(edgesArray.map((edge) => edge.from));

    const optgroups = {
        parent: document.createElement("optgroup"),
        final: document.createElement("optgroup"),
        column: document.createElement("optgroup"),
    };

    optgroups.parent.label = "Parent Measures";
    optgroups.final.label = "Final Measures";
    optgroups.column.label = "Column Nodes";

    const allOption = document.createElement("option");
    allOption.value = "";
    allOption.textContent = "All Measures";
    selectElement.appendChild(allOption);

    nodesArray.forEach((node) => {
        const option = document.createElement("option");
        option.value = node.id;
        option.textContent = node.label;

        if (node.type === "column") {
            optgroups.column.appendChild(option);
        } else if (parentNodes.has(node.id)) {
            optgroups.parent.appendChild(option);
        } else {
            optgroups.final.appendChild(option);
        }
    });

    Object.values(optgroups).forEach((optgroup) => {
        if (optgroup.children.length > 0) {
            selectElement.appendChild(optgroup);
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("mynetwork");
    const network = new LineageNetwork(container, nodesArray, edgesArray);

    initializeSelect();

    document
        .getElementById("measureSelect")
        .addEventListener("change", (event) => {
            network.filter(event.target.value);
        });

    populateTable(nodesArray, edgesArray);
});
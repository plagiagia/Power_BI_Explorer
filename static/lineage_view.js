// static/js/lineage_view.js

// Initialize the network diagram on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeNetwork(nodesArray, edgesArray);
});

function initializeNetwork(nodesArray, edgesArray) {
    // Create a Set of parent node IDs based on the edges
    const parentNodes = new Set(edgesArray.map(edge => edge.from));

    // Define node colors
    const parentColor = '#f1c83b'; // Orange for parent nodes
    const finalColor = '#23c4a7';  // Light green for final nodes
    const columnColor = '#ADD8E6'; // Light blue for column nodes

    // Process nodes to determine their type and apply appropriate styling
    nodesArray.forEach(node => {
        if (node.type === 'column') {
            // Column node styling
            node.color = columnColor;
            node.shape = 'box';
        } else if (parentNodes.has(node.id)) {
            // Parent node styling
            node.color = parentColor;
            node.shape = 'circle';
        } else {
            // Final node styling
            node.color = finalColor;
            node.shape = 'circle';
        }
    });

    // Instantiate the network
    const container = document.getElementById('mynetwork');
    const data = {
        nodes: new vis.DataSet(nodesArray),
        edges: new vis.DataSet(edgesArray)
    };
    const options = {
        nodes: {
            borderWidth: 2
        },
        edges: {
            color: 'lightgray',
            arrows: {
                to: { enabled: true, scaleFactor: 1, type: 'arrow' }
            }
        },
        physics: {
            forceAtlas2Based: {
                gravitationalConstant: -26,
                centralGravity: 0.005,
                springLength: 230,
                springConstant: 0.18
            },
            maxVelocity: 146,
            solver: 'forceAtlas2Based',
            timestep: 0.35,
            stabilization: { iterations: 150 }
        },
        layout: {
            improvedLayout: true
        },
        interaction: {
            hover: true,
            navigationButtons: true,
            keyboard: true,
            zoomView: true
        }
    };
    const network = new vis.Network(container, data, options);

    // Attach the filtering function to the select element
    document.getElementById('measureSelect').addEventListener('change', () => {
        filterNetwork(network, nodesArray, edgesArray, parentNodes);
    });

    // Populate the measure select options
    populateMeasureSelect(nodesArray, parentNodes);

    // Initially populate the table with all data
    populateTable(nodesArray, edgesArray);
}

// Function to populate the measure select options with optgroups
function populateMeasureSelect(nodesArray, parentNodes) {
    const selectElement = document.getElementById('measureSelect');

    // Create optgroups
    const optgroupParent = document.createElement('optgroup');
    optgroupParent.label = 'Parent Measures';
    const optgroupFinal = document.createElement('optgroup');
    optgroupFinal.label = 'Final Measures';
    const optgroupColumn = document.createElement('optgroup');
    optgroupColumn.label = 'Column Nodes';

    // Categorize nodes and append them to the respective optgroup
    nodesArray.forEach(node => {
        const option = document.createElement('option');
        option.value = node.id;
        option.textContent = node.label;

        if (node.type === 'column') {
            optgroupColumn.appendChild(option);
        } else if (parentNodes.has(node.id)) {
            optgroupParent.appendChild(option);
        } else {
            optgroupFinal.appendChild(option);
        }
    });

    // Add optgroups to the select element
    selectElement.appendChild(optgroupParent);
    selectElement.appendChild(optgroupFinal);
    selectElement.appendChild(optgroupColumn);
}

// Function to filter the network based on selected measure
function filterNetwork(network, nodesArray, edgesArray, parentNodes) {
    const selectedMeasure = document.getElementById('measureSelect').value;
    let updatedNodes = [];
    let updatedEdges = [];

    if (selectedMeasure === "") {
        updatedNodes = nodesArray;
        updatedEdges = edgesArray;
    } else {
        updatedEdges = edgesArray.filter(edge => edge.from === selectedMeasure || edge.to === selectedMeasure);
        const connectedNodeIds = new Set(updatedEdges.flatMap(edge => [edge.from, edge.to]));
        updatedNodes = nodesArray.filter(node => connectedNodeIds.has(node.id));

        // Ensure the selected node is included
        if (!connectedNodeIds.has(selectedMeasure)) {
            const selectedNode = nodesArray.find(node => node.id === selectedMeasure);
            if (selectedNode) {
                updatedNodes.push(selectedNode);
            }
        }
    }

    network.setData({
        nodes: new vis.DataSet(updatedNodes),
        edges: new vis.DataSet(updatedEdges)
    });

    // Update the table with the filtered data
    populateTable(updatedNodes, updatedEdges);
}

// Function to populate the table with lineage data
function populateTable(nodes, edges) {
    const tableBody = document.querySelector('#lineageTable tbody');
    tableBody.innerHTML = ''; // Clear existing table data

    const nodeMap = new Map(nodes.map(node => [node.id, node]));

    edges.forEach(edge => {
        const fromNode = nodeMap.get(edge.from);
        const toNode = nodeMap.get(edge.to);

        const row = tableBody.insertRow();

        // Initialize cell values
        let parentMeasure = '';
        let childMeasure = '';
        let column = '';

        if (fromNode && fromNode.type === 'column') {
            // Edge from column to measure
            column = fromNode.label;
            childMeasure = toNode ? toNode.label : '';
        } else {
            // Edge from measure to measure
            parentMeasure = fromNode ? fromNode.label : '';
            childMeasure = toNode ? toNode.label : '';
        }

        // Populate cells
        row.insertCell().textContent = parentMeasure;
        row.insertCell().textContent = childMeasure;
        row.insertCell().textContent = column;
    });
}

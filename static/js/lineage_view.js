// Initialize the network visualization
document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('mynetwork');
    const measureSelect = document.getElementById('measureSelect');

    // Create the network
    const data = {
        nodes: new vis.DataSet(nodesArray),
        edges: new vis.DataSet(edgesArray)
    };

    // Configuration for the network
    const options = {
        nodes: {
            shape: 'box',
            margin: 10,
            font: {
                size: 14
            },
            color: {
                background: '#ADD8E6',
                border: '#2B7CE9',
                highlight: {
                    background: '#D2E5FF',
                    border: '#2B7CE9'
                }
            }
        },
        edges: {
            arrows: 'to',
            smooth: {
                type: 'cubicBezier',
                forceDirection: 'horizontal',
                roundness: 0.4
            }
        },
        layout: {
            hierarchical: {
                direction: 'LR',
                sortMethod: 'directed',
                nodeSpacing: 150,
                levelSeparation: 200
            }
        },
        physics: false
    };

    // Create the network
    const network = new vis.Network(container, data, options);

    // Populate measure select dropdown
    nodesArray.forEach(node => {
        if (node.type !== 'column') {
            const option = document.createElement('option');
            option.value = node.id;
            option.textContent = node.label;
            measureSelect.appendChild(option);
        }
    });

    // Handle measure selection
    measureSelect.addEventListener('change', function(e) {
        const selectedMeasure = e.target.value;
        if (!selectedMeasure) {
            // Show all nodes and edges
            network.setData({nodes: data.nodes, edges: data.edges});
            return;
        }

        // Find connected nodes
        const connectedNodes = new Set();
        connectedNodes.add(selectedMeasure);

        // Find parent nodes (incoming edges)
        edgesArray.forEach(edge => {
            if (edge.to === selectedMeasure) {
                connectedNodes.add(edge.from);
            }
        });

        // Find child nodes (outgoing edges)
        edgesArray.forEach(edge => {
            if (edge.from === selectedMeasure) {
                connectedNodes.add(edge.to);
            }
        });

        // Filter nodes and edges
        const filteredNodes = nodesArray.filter(node => connectedNodes.has(node.id));
        const filteredEdges = edgesArray.filter(edge => 
            connectedNodes.has(edge.from) && connectedNodes.has(edge.to)
        );

        // Update the network
        network.setData({
            nodes: new vis.DataSet(filteredNodes),
            edges: new vis.DataSet(filteredEdges)
        });
    });

    // Update lineage table
    function updateLineageTable() {
        const tableBody = document.querySelector('#lineageTable tbody');
        tableBody.innerHTML = '';

        edgesArray.forEach(edge => {
            const row = document.createElement('tr');
            const fromNode = nodesArray.find(n => n.id === edge.from);
            const toNode = nodesArray.find(n => n.id === edge.to);

            row.innerHTML = `
                <td>${fromNode.type === 'column' ? '-' : fromNode.label}</td>
                <td>${toNode.type === 'column' ? '-' : toNode.label}</td>
                <td>${fromNode.type === 'column' ? fromNode.label : '-'}</td>
            `;
            tableBody.appendChild(row);
        });
    }

    updateLineageTable();
});

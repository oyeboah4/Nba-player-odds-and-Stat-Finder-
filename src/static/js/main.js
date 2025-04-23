// Main JavaScript file for NBA Stats Analyzer

document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const propsContainer = document.getElementById('propsContainer');
    const propCardTemplate = document.getElementById('propCardTemplate');
    const feedbackDiv = document.createElement('div');
    feedbackDiv.className = 'alert mt-3 d-none';
    uploadForm.parentNode.insertBefore(feedbackDiv, uploadForm.nextSibling);
    
    // Create results container
    const resultsContainer = document.createElement('div');
    resultsContainer.className = 'mt-4 d-none';
    uploadForm.parentNode.insertBefore(resultsContainer, uploadForm.nextSibling);
    
    // Add view mode selector after the form
    const viewModeSelector = document.createElement('select');
    viewModeSelector.className = 'form-select mt-3';
    viewModeSelector.innerHTML = `
        <option value="season">Full Season</option>
        <option value="last_20">Last 20 Games</option>
        <option value="last_10">Last 10 Games</option>
        <option value="last_5">Last 5 Games</option>
    `;
    uploadForm.appendChild(viewModeSelector);
    
    function getRateClass(rate) {
        if (rate >= 70) return 'high';
        if (rate >= 50) return 'medium';
        return 'low';
    }

    function createPropCard(prop) {
        const card = propCardTemplate.content.cloneNode(true);
        const propCard = card.querySelector('.prop-card');

        // Set game info
        propCard.querySelector('.game-info').textContent = prop.game_info;

        // Set player info
        propCard.querySelector('.player-name').textContent = prop.player_name;
        propCard.querySelector('.player-position').textContent = prop.team_name;

        // Set prop details
        propCard.querySelector('.prop-type').textContent = prop.stat_name;
        propCard.querySelector('.prop-line').textContent = `O ${prop.line_score}`;

        // Set success rates
        const timeframes = ['L5', 'L10', 'L20', 'H2H', 'season'];
        timeframes.forEach(timeframe => {
            const indicator = propCard.querySelector(`[data-timeframe="${timeframe}"] .rate-value`);
            const rate = prop[`${timeframe.toLowerCase()}_rate`] || 0;
            indicator.textContent = `${rate}%`;
            indicator.className = `rate-value ${getRateClass(rate)}`;
        });

        // Add click handler for visualization
        propCard.addEventListener('click', function() {
            const vizContainer = this.querySelector('.visualization-container');
            const isActive = vizContainer.classList.contains('active');
            
            // Hide all other visualization containers
            document.querySelectorAll('.visualization-container.active').forEach(container => {
                if (container !== vizContainer) {
                    container.classList.remove('active');
                }
            });

            // Toggle current visualization container
            vizContainer.classList.toggle('active');

            // Load visualization if opening
            if (!isActive) {
                loadVisualization(prop, vizContainer.querySelector('.graph-container'), 'L5');
            }
        });

        // Add click handlers for timeframe tabs
        propCard.querySelectorAll('.timeframe-tab').forEach(tab => {
            tab.addEventListener('click', function(e) {
                e.stopPropagation();  // Prevent card click handler
                
                // Update active tab
                propCard.querySelectorAll('.timeframe-tab').forEach(t => t.classList.remove('active'));
                this.classList.add('active');

                // Load visualization for selected timeframe
                const timeframe = this.dataset.timeframe;
                loadVisualization(prop, propCard.querySelector('.graph-container'), timeframe);
            });
        });

        return propCard;
    }

    async function loadVisualization(prop, container, timeframe) {
        try {
            const response = await fetch('/visualize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    player_name: prop.player_name,
                    team_name: prop.team_name,
                    stat_name: prop.stat_name,
                    line_score: prop.line_score,
                    view_mode: timeframe.toLowerCase()
                })
            });

            const data = await response.json();
            
            if (data.error) {
                container.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            } else {
                container.innerHTML = `<img src="data:image/png;base64,${data.graph}" class="img-fluid" alt="Performance Graph">`;
            }
        } catch (error) {
            container.innerHTML = `<div class="alert alert-danger">Error loading visualization</div>`;
        }
    }

    function showFeedback(message, isError = false) {
        feedbackDiv.className = `alert mt-3 ${isError ? 'alert-danger' : 'alert-success'}`;
        feedbackDiv.textContent = message;
        feedbackDiv.classList.remove('d-none');
    }
    
    function displayAnalysisResults(analysis) {
        // Clear previous results
        resultsContainer.innerHTML = '';
        
        // Create results table
        const table = document.createElement('table');
        table.className = 'table table-striped';
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Player</th>
                    <th>Team</th>
                    <th>Prop</th>
                    <th>Line</th>
                    <th>Hit Rate</th>
                    <th>Hits</th>
                    <th>Total Games</th>
                </tr>
            </thead>
            <tbody></tbody>
        `;
        
        // Add results to table
        const tbody = table.querySelector('tbody');
        analysis.forEach(result => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${result.player_name}</td>
                <td>${result.team_name}</td>
                <td>${result.stat_name}</td>
                <td>${result.line_score}</td>
                <td>${result.hit_rate}%</td>
                <td>${result.hits}</td>
                <td>${result.total_games}</td>
            `;
            tbody.appendChild(row);
        });
        
        resultsContainer.appendChild(table);
        
        // Add visualization container
        const visualizationContainer = document.createElement('div');
        visualizationContainer.className = 'mt-4';
        visualizationContainer.innerHTML = '<h3>Performance Visualization</h3>';
        
        // Add visualization for each prop
        analysis.forEach(result => {
            const graphDiv = document.createElement('div');
            graphDiv.className = 'mb-4';
            graphDiv.innerHTML = `
                <h4>${result.player_name} - ${result.stat_name}</h4>
                <img src="data:image/png;base64,${result.graph}" class="img-fluid" alt="Performance Graph">
            `;
            visualizationContainer.appendChild(graphDiv);
        });
        
        resultsContainer.appendChild(visualizationContainer);
        resultsContainer.classList.remove('d-none');
    }
    
    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            
            const formData = new FormData();
            const nbaStatsFile = document.getElementById('nbaStatsFile').files[0];
            const propsFile = document.getElementById('propsFile').files[0];
            
            if (!nbaStatsFile || !propsFile) {
                showFeedback('Please select both files', true);
                return;
            }
            
            formData.append('nbaStatsFile', nbaStatsFile);
            formData.append('propsFile', propsFile);
            formData.append('viewMode', viewModeSelector.value);  // Add view mode to form data
            
            try {
                // Show loading state
                const submitButton = uploadForm.querySelector('button[type="submit"]');
                const originalText = submitButton.textContent;
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Analyzing...';
                
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showFeedback(data.message);
                    if (data.analysis) {
                        displayAnalysisResults(data.analysis);
                    }
                } else {
                    showFeedback(data.error, true);
                }
            } catch (error) {
                showFeedback('An error occurred while processing files', true);
                console.error('Upload error:', error);
            } finally {
                // Reset button state
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            }
        });
    }
}); 

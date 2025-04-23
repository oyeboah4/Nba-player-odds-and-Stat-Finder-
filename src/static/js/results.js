document.addEventListener('DOMContentLoaded', function() {
    const propsContainer = document.getElementById('propsContainer');
    const propCardTemplate = document.getElementById('propCardTemplate');
    const searchInput = document.querySelector('.search-input');
    const tabs = document.querySelectorAll('.tab');
    const filterModal = document.getElementById('filterModal');
    const filterButton = document.querySelector('.filter-button');
    const closeFilterModal = document.getElementById('closeFilterModal');
    const resetFilters = document.getElementById('resetFilters');
    const applyFilters = document.getElementById('applyFilters');
    const propTypeFilters = document.getElementById('propTypeFilters');
    const gameFilters = document.getElementById('gameFilters');
    
    let currentProps = {};  // Store all props by type
    let activeFilters = {
        propTypes: new Set(),
        games: new Set()
    };

    // Add tab switching functionality
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Show props for selected type
            const type = tab.dataset.type;
            displayPropsByType(type);
        });
    });

    // Filter modal controls
    filterButton.addEventListener('click', () => {
        filterModal.classList.add('active');
    });

    closeFilterModal.addEventListener('click', () => {
        filterModal.classList.remove('active');
    });

    // Close modal when clicking outside
    filterModal.addEventListener('click', (e) => {
        if (e.target === filterModal) {
            filterModal.classList.remove('active');
        }
    });

    function normalizeGameString(game) {
        const [team1, team2] = game.split(' @ ');
        // Sort teams alphabetically to ensure consistent game string regardless of home/away
        return [team1, team2].sort().join(' vs ');
    }

    function getDisplayGameString(game) {
        // Keep original format for display
        return game;
    }

    function initializeFilters(props) {
        // Get unique prop types and games
        const propTypes = new Set();
        const gamesMap = new Map(); // Map normalized game string to display string

        Object.values(props).flat().forEach(prop => {
            propTypes.add(prop.stat_name);
            const gameString = `${prop.game_info.away_team} @ ${prop.game_info.home_team}`;
            const normalizedGame = normalizeGameString(gameString);
            // Keep the first encountered version of the game string for display
            if (!gamesMap.has(normalizedGame)) {
                gamesMap.set(normalizedGame, gameString);
            }
        });

        // Create prop type checkboxes
        propTypeFilters.innerHTML = Array.from(propTypes)
            .sort()
            .map(type => `
                <div class="filter-checkbox">
                    <input type="checkbox" id="prop-${type}" value="${type}" checked>
                    <label for="prop-${type}">${type}</label>
                </div>
            `).join('');

        // Create game checkboxes using normalized games
        gameFilters.innerHTML = Array.from(gamesMap.entries())
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([normalizedGame, displayGame]) => `
                <div class="filter-checkbox">
                    <input type="checkbox" id="game-${normalizedGame}" value="${normalizedGame}" 
                           data-display="${displayGame}" checked>
                    <label for="game-${normalizedGame}">${displayGame}</label>
                </div>
            `).join('');

        // Initialize activeFilters with all options selected
        activeFilters.propTypes = new Set(propTypes);
        activeFilters.games = new Set(gamesMap.keys()); // Store normalized game strings
    }

    resetFilters.addEventListener('click', () => {
        // Check all checkboxes
        document.querySelectorAll('.filter-checkbox input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = true;
        });

        // Reset activeFilters to include all options
        const propTypes = new Set();
        const games = new Set();
        Object.values(currentProps).flat().forEach(prop => {
            propTypes.add(prop.stat_name);
            const gameString = `${prop.game_info.away_team} @ ${prop.game_info.home_team}`;
            games.add(normalizeGameString(gameString));
        });
        activeFilters.propTypes = propTypes;
        activeFilters.games = games;

        // Update display
        const activeTab = document.querySelector('.tab.active');
        displayPropsByType(activeTab.dataset.type);
    });

    applyFilters.addEventListener('click', () => {
        // Update activeFilters based on checked boxes
        activeFilters.propTypes = new Set();
        activeFilters.games = new Set();

        propTypeFilters.querySelectorAll('input[type="checkbox"]:checked').forEach(checkbox => {
            activeFilters.propTypes.add(checkbox.value);
        });

        gameFilters.querySelectorAll('input[type="checkbox"]:checked').forEach(checkbox => {
            activeFilters.games.add(checkbox.value); // This will be the normalized game string
        });

        // Close modal and update display
        filterModal.classList.remove('active');
        const activeTab = document.querySelector('.tab.active');
        displayPropsByType(activeTab.dataset.type);
    });

    function displayPropsByType(type) {
        propsContainer.innerHTML = ''; // Clear existing props
        if (currentProps[type]) {
            const filteredProps = currentProps[type].filter(prop => {
                const gameString = `${prop.game_info.away_team} @ ${prop.game_info.home_team}`;
                const normalizedGame = normalizeGameString(gameString);
                return activeFilters.propTypes.has(prop.stat_name) && 
                       activeFilters.games.has(normalizedGame);
            });

            filteredProps.forEach(prop => {
                const propCard = createPropCard(prop);
                propsContainer.appendChild(propCard);
            });
        }
        // Apply current search filter
        filterProps(searchInput.value);
    }

    function filterProps(searchTerm) {
        searchTerm = searchTerm.toLowerCase();
        document.querySelectorAll('.prop-card').forEach(card => {
            const playerName = card.querySelector('.player-name').textContent.toLowerCase();
            const teamName = card.querySelector('.player-position').textContent.toLowerCase();
            const shouldShow = playerName.includes(searchTerm) || teamName.includes(searchTerm);
            card.style.display = shouldShow ? 'block' : 'none';
        });
    }

    function getRateClass(rate) {
        if (rate >= 70) return 'high';
        if (rate >= 50) return 'medium';
        return 'low';
    }

    function formatGameInfo(game) {
        const date = new Date(game.start_time);
        const timeString = date.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });
        return `${game.away_team} @ ${game.home_team} • ${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} at ${timeString}`;
    }

    function createPropCard(prop) {
        const card = propCardTemplate.content.cloneNode(true);
        const propCard = card.querySelector('.prop-card');

        // Set game info
        propCard.querySelector('.game-info').textContent = formatGameInfo(prop.game_info);

        // Set player info
        propCard.querySelector('.player-name').textContent = prop.player_name;
        propCard.querySelector('.player-position').textContent = prop.team_name;

        // Set prop details
        const propTypeText = `${prop.stat_name} (Over)`;
        propCard.querySelector('.prop-type').textContent = propTypeText;
        propCard.querySelector('.prop-line').textContent = `O ${prop.line_score}`;

        // Set success rates
        const timeframes = [
            { key: 'last_5', label: 'L5' },
            { key: 'last_10', label: 'L10' },
            { key: 'last_20', label: 'L20' },
            { key: 'h2h', label: 'H2H' },
            { key: 'season', label: '24/25' }
        ];

        const ratesContainer = propCard.querySelector('.success-rates');
        timeframes.forEach(({ key, label }) => {
            const rateElement = ratesContainer.querySelector(`[data-timeframe="${label}"]`);
            const rate = prop[`${key}_rate`] || 0;
            const rateValue = rateElement.querySelector('.rate-value');
            rateValue.textContent = `${Math.round(rate)}%`;
            if (key === 'h2h' && prop.h2h_games) {
                rateValue.textContent += ` (${prop.h2h_games})`;
            }
            rateValue.className = `rate-value ${getRateClass(rate)}`;

            // Add click handler for timeframe switching - remove H2H condition
            rateElement.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent card expansion/collapse
                const vizContainer = propCard.querySelector('.visualization-container');
                const graphContainer = vizContainer.querySelector('.graph-container');
                
                // Update active state of timeframe elements
                ratesContainer.querySelectorAll('.rate-indicator').forEach(el => {
                    el.classList.remove('active');
                });
                rateElement.classList.add('active');
                
                // Show visualization container if not already visible
                if (!vizContainer.classList.contains('active')) {
                    vizContainer.classList.add('active');
                }
                
                // Load visualization for selected timeframe
                loadVisualization(prop, graphContainer, key);
            });
        });

        // Add click handler for card expansion
        propCard.addEventListener('click', function(e) {
            // Ignore clicks on buttons or rate indicators
            if (e.target.closest('.card-actions') || e.target.closest('.rate-indicator')) return;

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
                // Set L5 as active by default
                const l5Element = this.querySelector('[data-timeframe="L5"]');
                l5Element.classList.add('active');
                loadVisualization(prop, vizContainer.querySelector('.graph-container'), 'last_5');
            }
        });

        return propCard;
    }

    async function loadVisualization(prop, container, timeframe = 'last_5') {
        try {
            // Show loading state
            container.innerHTML = '<div class="loading">Loading visualization...</div>';
            
            // Clear any existing error classes
            container.classList.remove('error');
            
            // If H2H is selected but no H2H games exist, show error
            if (timeframe === 'h2h' && (!prop.h2h_games || prop.h2h_games === 0)) {
                container.innerHTML = `
                    <div class="error-message">
                        <div class="error-title">No H2H Data</div>
                        <div class="error-details">No head-to-head games found against ${prop.game_info.home_team}</div>
                    </div>`;
                container.classList.add('error');
                return;
            }
            
            const response = await fetch('/visualize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    player_name: prop.player_name,
                    team_name: prop.team_name,
                    stat_name: prop.stat_name,
                    line_score: parseFloat(prop.line_score),
                    timeframe: timeframe
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Visualization response:', data); // Debug log
            
            if (data.error) {
                container.innerHTML = `
                    <div class="error-message">
                        <div class="error-title">Error</div>
                        <div class="error-details">${data.error}</div>
                    </div>`;
                container.classList.add('error');
            } else if (data.graph) {
                // Create a new image element
                const img = new Image();
                
                // Set up load and error handlers before setting src
                img.onload = () => {
                    container.innerHTML = '';
                    container.appendChild(img);
                };
                
                img.onerror = () => {
                    container.innerHTML = `
                        <div class="error-message">
                            <div class="error-title">Error</div>
                            <div class="error-details">Failed to load graph image</div>
                        </div>`;
                    container.classList.add('error');
                };
                
                img.src = `data:image/png;base64,${data.graph}`;
                img.className = 'graph-image';
                img.alt = 'Performance Graph';
            } else {
                container.innerHTML = `
                    <div class="error-message">
                        <div class="error-title">Error</div>
                        <div class="error-details">No visualization data available</div>
                    </div>`;
                container.classList.add('error');
            }
        } catch (error) {
            console.error('Error loading visualization:', error);
            container.innerHTML = `
                <div class="error-message">
                    <div class="error-title">Error</div>
                    <div class="error-details">${error.message}</div>
                </div>`;
            container.classList.add('error');
        }
    }

    // Update search functionality
    searchInput.addEventListener('input', function(e) {
        filterProps(e.target.value);
    });

    // Update loadProps function
    async function loadProps() {
        try {
            const response = await fetch('/get_props');
            const data = await response.json();
            
            if (data.props_by_type) {
                currentProps = data.props_by_type;
                // Initialize filters
                initializeFilters(data.props_by_type);
                // Display standard props by default
                displayPropsByType('standard');
            } else {
                propsContainer.innerHTML = '<div class="error-message">No props data available</div>';
            }
        } catch (error) {
            console.error('Error loading props:', error);
            propsContainer.innerHTML = '<div class="error-message">Error loading props data</div>';
        }
    }

    loadProps();
}); 

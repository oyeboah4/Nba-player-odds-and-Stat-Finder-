# NBA Stats Analyzer

A web application for analyzing NBA player statistics and prop bets. The application allows users to upload NBA stats and prop data, then provides visualizations and analysis of player performance across different timeframes and against specific opponents.

## Features

- Upload NBA stats and prop data via CSV files
- View player props categorized by odds type (Standard, Demon, Goblin)
- Analyze player performance across different timeframes:
  - Last 5 games
  - Last 10 games
  - Last 20 games
  - Season
  - Head-to-Head (H2H) against specific opponents
- Interactive visualizations of player performance
- Filter props by type and game
- Search functionality for quick prop lookup

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Nba-player-odds-and-Stat-Finder-.git
cd Nba-player-odds-and-Stat-Finder-
```

2. Create and activate a virtual environment:
```bash
python -m venv venv # If this doesnt work try python3 instead of python
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Update pip and install dependencies:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If you encounter any issues with the requirements installation, you can install the core dependencies individually:
```bash
pip install flask==3.0.2
pip install pandas==2.2.1
pip install matplotlib==3.8.3
pip install python-dotenv==1.0.1
```

## Usage

1. Start the Flask application:
```bash
python src/app/app.py
```

2. Open your web browser and navigate to `http://localhost:5001`

3. Upload your NBA stats and prop data files(See test_files folder for example files):
   - NBA stats file should be in CSV format with required headers
   - Props file should be in CSV format with required headers

4. Use the interface to:
   - View props by odds type (Standard/Demon/Goblin)
   - Filter props by type and game
   - Search for specific players or teams
   - View performance visualizations
   - Analyze head-to-head matchups

## File Format Requirements

### NBA Stats File
Required headers:
- player_name
- team_abbreviation
- opponent_team
- pts
- reb
- ast
- fg3m
- date

### Props File
Required headers:
- Line Score
- Player Name
- Team Name
- Stat Name
- Start Time
- Opponent Team
- Odds Type

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

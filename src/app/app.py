from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
import pandas as pd
from dotenv import load_dotenv
from data_processor import DataProcessor
from visualizer import DataVisualizer
import json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app with correct template and static folders
template_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'))
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Required headers for each file type
NBA_STATS_REQUIRED_HEADERS = ['player_name', 'team_abbreviation', 'opponent_team', 'pts', 'reb', 'ast', 'fg3m', 'date']
PROPS_REQUIRED_HEADERS = ['Line Score', 'Player Name', 'Team Name', 'Stat Name', 'Start Time', 'Opponent Team', 'Odds Type']

# Valid stat names as per context.md
VALID_STAT_NAMES = [
    'Points',
    '3-PT Made',
    'Pts+Rebs+Asts',
    'Rebounds',
    'Assists',
    'Pts+Rebs',
    'Pts+Asts',
    'Rebs+Asts'
]

# Valid odds types
VALID_ODDS_TYPES = ['standard', 'demon', 'goblin']

def validate_nba_stats_file(df):
    missing_headers = [header for header in NBA_STATS_REQUIRED_HEADERS if header not in df.columns]
    if missing_headers:
        return False, f"Missing required headers in NBA stats file: {', '.join(missing_headers)}"
    return True, "Valid"

def validate_props_file(df):
    missing_headers = [header for header in PROPS_REQUIRED_HEADERS if header not in df.columns]
    if missing_headers:
        return False, f"Missing required headers in props file: {', '.join(missing_headers)}"
    
    # Instead of rejecting the file, filter out invalid stats and warn if any were found
    invalid_stats = df[~df['Stat Name'].isin(VALID_STAT_NAMES)]['Stat Name'].unique()
    if len(invalid_stats) > 0:
        # Filter the dataframe to keep only valid stats
        df_filtered = df[df['Stat Name'].isin(VALID_STAT_NAMES)].copy()
        return True, f"Warning: The following stat types will be skipped: {', '.join(invalid_stats)}", df_filtered
    
    return True, "Valid", df

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/results')
def results():
    return render_template('results.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'nbaStatsFile' not in request.files or 'propsFile' not in request.files:
        logger.error("Missing required files in request")
        return jsonify({'error': 'Both files are required'}), 400
    
    nba_stats_file = request.files['nbaStatsFile']
    props_file = request.files['propsFile']
    
    if nba_stats_file.filename == '' or props_file.filename == '':
        logger.error("Empty filenames submitted")
        return jsonify({'error': 'Both files must be selected'}), 400
    
    try:
        logger.info(f"Processing files: {nba_stats_file.filename} and {props_file.filename}")
        
        # Read and validate NBA stats file
        nba_stats_df = pd.read_csv(nba_stats_file)
        is_valid, message = validate_nba_stats_file(nba_stats_df)
        if not is_valid:
            logger.error(f"NBA stats validation failed: {message}")
            return jsonify({'error': message}), 400
        
        # Read and validate props file
        props_df = pd.read_csv(props_file)
        is_valid, message, filtered_props_df = validate_props_file(props_df)
        
        # Save files if they pass validation
        nba_stats_path = os.path.join(app.config['UPLOAD_FOLDER'], 'nba_stats.csv')
        props_path = os.path.join(app.config['UPLOAD_FOLDER'], 'props.csv')
        
        logger.info(f"Saving files to: {nba_stats_path} and {props_path}")
        nba_stats_df.to_csv(nba_stats_path, index=False)
        filtered_props_df.to_csv(props_path, index=False)
        
        # Return success with warning message if any stats were skipped
        response = {'message': 'Files uploaded successfully', 'redirect': url_for('results')}
        if "Warning" in message:
            response['warning'] = message
            logger.info(f"Upload successful with warning: {message}")
        else:
            logger.info("Upload successful")
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error during upload: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/get_props')
def get_props():
    try:
        props_path = os.path.join(app.config['UPLOAD_FOLDER'], 'props.csv')
        nba_stats_path = os.path.join(app.config['UPLOAD_FOLDER'], 'nba_stats.csv')
        
        logger.info(f"Checking for files at: {props_path} and {nba_stats_path}")
        if not (os.path.exists(props_path) and os.path.exists(nba_stats_path)):
            logger.error("Required files not found")
            return jsonify({'error': 'No data available. Please upload files first.'}), 404
        
        # Read the CSV files
        logger.info("Reading CSV files")
        nba_stats_df = pd.read_csv(nba_stats_path)
        props_df = pd.read_csv(props_path)
        
        # Initialize processor with DataFrames
        logger.info("Initializing DataProcessor")
        processor = DataProcessor(nba_stats_df, props_df)
        
        # Get analysis for different timeframes
        timeframes = ['last_5', 'last_10', 'last_20', 'season']
        props_by_type = {'standard': [], 'demon': [], 'goblin': []}
        
        logger.info("Processing props")
        for prop in props_df.to_dict('records'):
            prop_data = {
                'player_name': prop['Player Name'],
                'team_name': prop['Team Name'],
                'stat_name': prop['Stat Name'],
                'line_score': float(prop['Line Score']),
                'odds_type': prop['Odds Type'].lower(),
                'game_info': {
                    'start_time': prop['Start Time'],
                    'away_team': prop['Team Name'],
                    'home_team': prop['Opponent Team']
                }
            }
            
            # Get analysis for each timeframe
            for timeframe in timeframes:
                analysis = processor.analyze_prop(
                    prop_data['player_name'],
                    prop_data['team_name'],
                    prop_data['stat_name'],
                    prop_data['line_score'],
                    timeframe
                )
                if 'error' not in analysis:
                    prop_data[f"{timeframe}_rate"] = analysis['hit_rate']
                    if timeframe == 'season':
                        prop_data['season_rate'] = analysis['hit_rate']
            
            # Get H2H analysis
            h2h_analysis = processor.analyze_h2h(
                prop_data['player_name'],
                prop_data['team_name'],
                prop_data['game_info']['home_team'],  # Using opponent team
                prop_data['stat_name'],
                prop_data['line_score']
            )
            prop_data['h2h_rate'] = h2h_analysis.get('hit_rate', 0)
            prop_data['h2h_games'] = h2h_analysis.get('total_games', 0)
            
            # Add prop to appropriate category
            odds_type = prop_data['odds_type']
            if odds_type in props_by_type:
                props_by_type[odds_type].append(prop_data)
        
        logger.info(f"Returning props grouped by type: {[f'{k}: {len(v)}' for k, v in props_by_type.items()]}")
        return jsonify({'props_by_type': props_by_type})
        
    except Exception as e:
        logger.error(f"Error in get_props: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/visualize', methods=['POST'])
def visualize():
    try:
        data = request.json
        logger.info(f"Visualization request received for: {data}")
        
        nba_stats_path = os.path.join(app.config['UPLOAD_FOLDER'], 'nba_stats.csv')
        props_path = os.path.join(app.config['UPLOAD_FOLDER'], 'props.csv')
        
        if not (os.path.exists(nba_stats_path) and os.path.exists(props_path)):
            logger.error("Required files not found")
            return jsonify({'error': 'No data available. Please upload files first.'}), 404
        
        # Read both DataFrames
        logger.info("Reading CSV files for visualization")
        nba_stats_df = pd.read_csv(nba_stats_path)
        props_df = pd.read_csv(props_path)
        
        # Log available columns
        logger.info(f"NBA stats columns: {nba_stats_df.columns.tolist()}")
        
        # Get player stats for debugging
        player_stats = nba_stats_df[
            (nba_stats_df['player_name'] == data['player_name']) &
            (nba_stats_df['team_abbreviation'] == data['team_name'])
        ]
        logger.info(f"Found {len(player_stats)} games for {data['player_name']}")
        
        if not player_stats.empty:
            if data['stat_name'] == '3-PT Made':
                if 'fg3m' in player_stats.columns:
                    logger.info(f"3PT stats for last 5 games: {player_stats['fg3m'].head().tolist()}")
                else:
                    logger.error("fg3m column not found in player stats")
        
        logger.info("Creating visualization")
        visualizer = DataVisualizer(nba_stats_df, props_df)
        graph_data = visualizer.create_prop_visualization(
            player_name=data['player_name'],
            team_name=data['team_name'],
            stat_name=data['stat_name'],
            line_score=data['line_score'],
            view_mode=data.get('timeframe', 'last_5')
        )
        
        logger.info(f"Visualization result: {graph_data.keys() if isinstance(graph_data, dict) else 'Not a dict'}")
        return jsonify(graph_data)
        
    except Exception as e:
        logger.error(f"Error in visualize: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    # Use port 5001 instead of 5000
    app.run(debug=True, host='0.0.0.0', port=5001)

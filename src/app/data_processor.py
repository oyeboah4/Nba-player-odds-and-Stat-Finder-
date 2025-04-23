import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class DataProcessor:
    def __init__(self, nba_stats_df: pd.DataFrame, props_df: pd.DataFrame):
        self.nba_stats_df = nba_stats_df
        self.props_df = props_df
        
        # Convert date columns if they exist
        if 'date' in self.nba_stats_df.columns:
            self.nba_stats_df['date'] = pd.to_datetime(self.nba_stats_df['date'])
        if 'Start Time' in self.props_df.columns:
            self.props_df['Start Time'] = pd.to_datetime(self.props_df['Start Time'])
    
    def _convert_to_native_types(self, value):
        """Convert numpy types to native Python types"""
        if isinstance(value, (np.int64, np.int32, np.int16, np.int8)):
            return int(value)
        if isinstance(value, (np.float64, np.float32)):
            return float(value)
        if isinstance(value, np.bool_):
            return bool(value)
        if isinstance(value, pd.Timestamp):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return value

    def get_player_stats(self, player_name: str, team_name: str, 
                        view_mode: str = 'last_5') -> pd.DataFrame:
        """Get player stats based on view mode"""
        # Filter by player and team
        player_stats = self.nba_stats_df[
            (self.nba_stats_df['player_name'] == player_name) &
            (self.nba_stats_df['team_abbreviation'] == team_name)
        ].copy()
        
        if player_stats.empty:
            return pd.DataFrame()
        
        # Sort by date if available
        if 'date' in player_stats.columns:
            player_stats = player_stats.sort_values('date', ascending=False)
        
        # Apply view mode filter
        if view_mode == 'last_5':
            return player_stats.head(5)
        elif view_mode == 'last_10':
            return player_stats.head(10)
        elif view_mode == 'last_20':
            return player_stats.head(20)
        elif view_mode == 'season':
            return player_stats
        else:
            return player_stats.head(5)  # Default to last 5 games
    
    def get_player_props(self, player_name: str, team_name: str) -> pd.DataFrame:
        """Get props for a specific player"""
        return self.props_df[
            (self.props_df['Player Name'] == player_name) &
            (self.props_df['Team Name'] == team_name)
        ]
    
    def analyze_prop(self, player_name: str, team_name: str, 
                    stat_name: str, line_score: float,
                    view_mode: str = 'last_5') -> Dict:
        """Analyze a specific prop bet"""
        try:
            # Filter stats for the player
            player_stats = self.nba_stats_df[
                (self.nba_stats_df['player_name'] == player_name) &
                (self.nba_stats_df['team_abbreviation'] == team_name)
            ].sort_values('date', ascending=False)

            if player_stats.empty:
                return {'error': 'No stats found for player'}

            # Get the appropriate number of games based on view mode
            games_to_analyze = {
                'last_5': 5,
                'last_10': 10,
                'last_20': 20,
                'season': len(player_stats)
            }.get(view_mode, 5)

            player_stats = player_stats.head(games_to_analyze)

            # Calculate the stat value based on stat name
            if stat_name == 'Points':
                stat_values = player_stats['pts']
            elif stat_name == 'Rebounds':
                stat_values = player_stats['reb']
            elif stat_name == 'Assists':
                stat_values = player_stats['ast']
            elif stat_name == '3-PT Made':
                stat_values = player_stats['fg3m']
            elif stat_name == 'Pts+Rebs+Asts':
                stat_values = player_stats['pts'] + player_stats['reb'] + player_stats['ast']
            elif stat_name == 'Pts+Rebs':
                stat_values = player_stats['pts'] + player_stats['reb']
            elif stat_name == 'Pts+Asts':
                stat_values = player_stats['pts'] + player_stats['ast']
            elif stat_name == 'Rebs+Asts':
                stat_values = player_stats['reb'] + player_stats['ast']
            else:
                return {'error': f'Unsupported stat name: {stat_name}'}

            # Calculate hits and hit rate
            hits = sum(stat_values > line_score)
            total_games = len(stat_values)
            hit_rate = (hits / total_games) * 100 if total_games > 0 else 0

            return {
                'player_name': player_name,
                'team_name': team_name,
                'stat_name': stat_name,
                'line_score': self._convert_to_native_types(line_score),
                'hits': self._convert_to_native_types(hits),
                'total_games': self._convert_to_native_types(total_games),
                'hit_rate': round(self._convert_to_native_types(hit_rate), 1)
            }

        except Exception as e:
            return {'error': str(e)}
    
    def get_all_props_analysis(self, view_mode='season'):
        """
        Analyze all props in the props file
        
        Args:
            view_mode (str): One of 'last_5', 'last_10', 'last_20', 'season'
        """
        results = []
        for _, prop in self.props_df.iterrows():
            analysis = self.analyze_prop(
                prop['Player Name'],
                prop['Team Name'],
                prop['Stat Name'],
                float(prop['Line Score']),
                view_mode
            )
            if 'error' not in analysis:
                results.append(analysis)
        return results

    def analyze_h2h(self, player_name: str, team_name: str, opponent_team: str,
                    stat_name: str, line_score: float) -> Dict:
        """Analyze head-to-head performance against a specific opponent"""
        try:
            # Filter stats for the player against the specific opponent
            player_stats = self.nba_stats_df[
                (self.nba_stats_df['player_name'] == player_name) &
                (self.nba_stats_df['team_abbreviation'] == team_name) &
                (self.nba_stats_df['opponent_team'] == opponent_team)
            ].sort_values('date', ascending=False)

            if player_stats.empty:
                return {'error': 'No H2H stats found'}

            # Calculate the stat value based on stat name
            if stat_name == 'Points':
                stat_values = player_stats['pts']
            elif stat_name == 'Rebounds':
                stat_values = player_stats['reb']
            elif stat_name == 'Assists':
                stat_values = player_stats['ast']
            elif stat_name == '3-PT Made':
                stat_values = player_stats['fg3m']
            elif stat_name == 'Pts+Rebs+Asts':
                stat_values = player_stats['pts'] + player_stats['reb'] + player_stats['ast']
            elif stat_name == 'Pts+Rebs':
                stat_values = player_stats['pts'] + player_stats['reb']
            elif stat_name == 'Pts+Asts':
                stat_values = player_stats['pts'] + player_stats['ast']
            elif stat_name == 'Rebs+Asts':
                stat_values = player_stats['reb'] + player_stats['ast']
            else:
                return {'error': f'Unsupported stat name: {stat_name}'}

            # Calculate hits and hit rate
            hits = sum(stat_values > line_score)
            total_games = len(stat_values)
            hit_rate = (hits / total_games) * 100 if total_games > 0 else 0

            return {
                'player_name': player_name,
                'team_name': team_name,
                'opponent_team': opponent_team,
                'stat_name': stat_name,
                'line_score': self._convert_to_native_types(line_score),
                'hits': self._convert_to_native_types(hits),
                'total_games': self._convert_to_native_types(total_games),
                'hit_rate': round(self._convert_to_native_types(hit_rate), 1)
            }

        except Exception as e:
            return {'error': str(e)} 
import matplotlib
matplotlib.use('Agg')  # Set the backend to Agg before importing pyplot
import matplotlib.pyplot as plt
import io
import base64
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

class DataVisualizer:
    def __init__(self, nba_stats_df: pd.DataFrame, props_df: pd.DataFrame):
        self.nba_stats_df = nba_stats_df
        self.props_df = props_df
        
        # Set style for better-looking graphs
        plt.style.use('dark_background')
        
    def _create_stacked_bar_graph(self, player_stats: pd.DataFrame, prop_info: Dict, 
                                stat_components: Dict[str, pd.Series]) -> str:
        """Create a stacked bar graph for a player's performance against a prop line"""
        try:
            # Debug info
            print(f"Player stats shape: {player_stats.shape}")
            print(f"Stat components: {list(stat_components.keys())}")
            
            # Reset index and reverse order (most recent on right)
            player_stats = player_stats.iloc[::-1].reset_index(drop=True)
            
            # Validate inputs
            if player_stats.empty:
                raise ValueError("No player stats available")
            
            if not stat_components:
                raise ValueError("No stat components provided")
            
            # Calculate total values and validate
            total_values = pd.Series(0, index=range(len(player_stats)))
            reversed_components = {}
            for label, values in stat_components.items():
                print(f"Processing {label}: {values.tolist()}")
                values = pd.to_numeric(values, errors='coerce')
                if values.isna().any():
                    print(f"Warning: NaN values found in {label}")
                # Reverse the values to match the reversed player_stats
                reversed_values = values.iloc[::-1].reset_index(drop=True)
                reversed_components[label] = reversed_values
                total_values += reversed_values
            
            if total_values.empty:
                raise ValueError("No valid stat values found")
            
            print(f"Total values: {total_values.tolist()}")
            print(f"Line score: {prop_info['line_score']}")
            
            hits = total_values > prop_info['line_score']
            print(f"Hits: {hits.tolist()}")
            
            plt.figure(figsize=(10, 6))
            
            # Set up the plot
            ax = plt.gca()
            ax.set_facecolor('#1c1c1e')  # Dark background
            plt.gcf().set_facecolor('#1c1c1e')
            
            # Create stacked bars
            bottom = pd.Series(0, index=range(len(player_stats)))
            bars = []
            labels = []
            
            # Color scheme - expanded for more components with more distinct greens
            hit_colors = ['#32d74b', '#00ba34', '#00a025', '#008519']  # More distinct shades of green
            miss_colors = ['#ff453a', '#ff6b63', '#ff918c', '#ffb7b5']  # Different shades of red
            
            # Determine if we should show value labels (hide if more than 25 games)
            show_value_labels = len(player_stats) <= 25
            
            for i, (label, values) in enumerate(reversed_components.items()):
                if values.isna().all():
                    print(f"Skipping {label} - all values are NaN")
                    continue
                
                # Use modulo to cycle through colors if we have more components than colors
                color_idx = i % len(hit_colors)
                colors = [hit_colors[color_idx] if hit else miss_colors[color_idx] for hit in hits]
                
                bar = plt.bar(range(len(values)), values.fillna(0), bottom=bottom, 
                             color=colors, alpha=0.9, width=0.7)
                bottom += values.fillna(0)
                bars.append(bar)
                labels.append(f"{label}")
                
                # Add value labels inside bars only if show_value_labels is True
                if show_value_labels:
                    for j, v in enumerate(values):
                        if pd.notna(v) and v > 0:  # Only show non-zero, non-NA values
                            plt.text(j, bottom[j] - v/2, f"{int(v)}\n{label}", 
                                    ha='center', va='center', color='white', 
                                    fontsize=8, fontweight='bold')
            
            if not bars:
                raise ValueError("No valid data to plot")

            # Add total sum labels at the top of each bar
            for i, total in enumerate(total_values):
                if pd.notna(total) and total > 0:
                    is_hit = total > prop_info['line_score']
                    color = '#32d74b' if is_hit else '#ff453a'  # Green for hits, red for misses
                    # Position the label slightly above the bar
                    label_y = total * 1.02
                    plt.text(i, label_y, f"{int(total)}", 
                            ha='center', va='bottom', color=color,
                            fontsize=10, fontweight='bold')
            
            # Add prop line
            line_score = prop_info['line_score']
            plt.axhline(y=line_score, color='#0a84ff', linestyle='--', linewidth=1)
            
            # Add prop line label
            plt.text(len(player_stats) - 1, line_score, f"O {line_score}", 
                    color='#0a84ff', ha='right', va='bottom')
            
            # Customize axes
            plt.grid(True, axis='y', alpha=0.1)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#86868b')
            ax.spines['bottom'].set_color('#86868b')
            
            # Add game info to x-axis only if not too many games
            if show_value_labels and 'opponent_team' in player_stats.columns and 'date' in player_stats.columns:
                try:
                    dates = pd.to_datetime(player_stats['date']).dt.strftime('%m/%d')
                    team = player_stats['team_abbreviation']
                    opponents = player_stats['opponent_team']
                    
                    # Debug logging
                    print("Game info debug:")
                    print(f"Team abbreviation: {team.tolist()}")
                    print(f"Opponent teams: {opponents.tolist()}")
                    print(f"Dates: {dates.tolist()}")
                    
                    game_labels = []
                    for opp in opponents:
                        if pd.isna(opp):
                            game_labels.append("@???")
                        else:
                            game_labels.append(f"@{opp}")  # Format as "@OPPONENT"
                    
                    plt.xticks(range(len(player_stats)), 
                              [f"{game}\n{date}" for game, date in zip(game_labels, dates)],
                              rotation=0, ha='center', color='#86868b', fontsize=8)
                except Exception as e:
                    print(f"Warning: Could not format game info: {str(e)}")
                    traceback.print_exc()  # Add full traceback for debugging
            else:
                # If too many games, just show minimal ticks
                plt.xticks(range(len(player_stats)), 
                          [''] * len(player_stats))
            
            # Set y-axis properties
            plt.ylabel('Total', color='#86868b', fontsize=10)
            ax.tick_params(axis='y', colors='#86868b')
            
            # Add average line
            avg_total = total_values.mean()
            plt.axhline(y=avg_total, color='white', linestyle=':', linewidth=1, alpha=0.3)
            
            # Calculate plot dimensions and adjust for total sum labels
            y_min, y_max = plt.ylim()
            plt.ylim(y_min, y_max * 1.1)  # Add 10% padding at the top for sum labels
            x_min, x_max = plt.xlim()
            
            # Add hit rate info in top left
            hits_count = sum(hits)
            total_games = len(hits)
            hit_rate = (hits_count / total_games) * 100 if total_games > 0 else 0
            plt.text(x_min, y_max, f'L{total_games} {int(hit_rate)}% • {hits_count}/{total_games} games',
                    color='white', ha='left', va='top', alpha=0.7)
            
            # Add average total in top right
            plt.text(x_max, y_max, f'AVG Total: {int(avg_total)}',
                    color='white', ha='right', va='top', alpha=0.7)
            
            # Adjust layout
            plt.tight_layout()
            
            # Convert plot to base64 string
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            plt.close()
            return base64.b64encode(buf.getvalue()).decode()
            
        except Exception as e:
            print(f"Error in _create_stacked_bar_graph: {str(e)}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"Failed to create visualization: {str(e)}")
    
    def create_prop_visualization(self, player_name: str, team_name: str,
                                stat_name: str, line_score: float,
                                view_mode: str = 'last_5') -> Dict:
        """Create visualization for a specific prop bet"""
        try:
            # Input validation
            if not player_name or not team_name or not stat_name:
                return {'error': 'Missing required parameters'}
            
            if not isinstance(line_score, (int, float)) or line_score < 0:
                return {'error': 'Invalid line score'}
            
            # Special handling for H2H view mode
            if view_mode == 'h2h':
                # Get the opponent team from props
                prop = self.props_df[
                    (self.props_df['Player Name'] == player_name) &
                    (self.props_df['Team Name'] == team_name) &
                    (self.props_df['Stat Name'] == stat_name)
                ].iloc[0]
                
                opponent_team = prop['Opponent Team']
                
                # Get H2H stats
                player_stats = self.nba_stats_df[
                    (self.nba_stats_df['player_name'] == player_name) &
                    (self.nba_stats_df['team_abbreviation'] == team_name) &
                    (self.nba_stats_df['opponent_team'] == opponent_team)
                ].sort_values('date', ascending=False).copy()
                
                if player_stats.empty:
                    return {'error': f'No H2H stats found against {opponent_team}'}
                
            else:
                # Regular view mode handling
                player_stats = self.nba_stats_df[
                    (self.nba_stats_df['player_name'] == player_name) &
                    (self.nba_stats_df['team_abbreviation'] == team_name)
                ].sort_values('date', ascending=False).copy()
                
                if player_stats.empty:
                    return {'error': f'No stats found for player {player_name} on team {team_name}'}
                
                # Apply view mode filter
                games_to_analyze = {
                    'last_5': 5,
                    'last_10': 10,
                    'last_20': 20,
                    'season': len(player_stats)
                }.get(view_mode, 5)
                
                player_stats = player_stats.head(games_to_analyze)
            
            player_stats = player_stats.reset_index(drop=True)
            print(f"Analyzing {len(player_stats)} games for {player_name}")
            
            # Validate required columns
            required_columns = {
                'Points': ['pts'],
                'Rebounds': ['reb'],
                'Assists': ['ast'],
                '3-PT Made': ['fg3m'],
                'Pts+Rebs+Asts': ['pts', 'reb', 'ast'],
                'Pts+Rebs': ['pts', 'reb'],
                'Pts+Asts': ['pts', 'ast'],
                'Rebs+Asts': ['reb', 'ast']
            }
            
            if stat_name not in required_columns:
                return {'error': f'Unsupported stat name: {stat_name}'}
            
            missing_columns = [col for col in required_columns[stat_name] 
                             if col not in player_stats.columns]
            if missing_columns:
                return {'error': f'Missing required stats: {", ".join(missing_columns)}'}
            
            # Convert numeric columns and handle missing values
            for col in required_columns[stat_name]:
                player_stats[col] = pd.to_numeric(player_stats[col], errors='coerce').fillna(0)
                print(f"{col} values: {player_stats[col].tolist()}")
            
            # Prepare stat components based on stat name
            stat_components = {}
            if stat_name == 'Points':
                stat_components = {'PTS': player_stats['pts']}
            elif stat_name == 'Rebounds':
                stat_components = {'REB': player_stats['reb']}
            elif stat_name == 'Assists':
                stat_components = {'AST': player_stats['ast']}
            elif stat_name == '3-PT Made':
                stat_components = {'3PM': player_stats['fg3m']}
            elif stat_name == 'Pts+Rebs+Asts':
                stat_components = {
                    'PTS': player_stats['pts'],
                    'REB': player_stats['reb'],
                    'AST': player_stats['ast']
                }
            elif stat_name == 'Pts+Rebs':
                stat_components = {
                    'PTS': player_stats['pts'],
                    'REB': player_stats['reb']
                }
            elif stat_name == 'Pts+Asts':
                stat_components = {
                    'PTS': player_stats['pts'],
                    'AST': player_stats['ast']
                }
            elif stat_name == 'Rebs+Asts':
                stat_components = {
                    'REB': player_stats['reb'],
                    'AST': player_stats['ast']
                }
            
            # Create visualization
            prop_info = {
                'player_name': player_name,
                'team_name': team_name,
                'stat_name': stat_name,
                'line_score': line_score
            }
            
            graph_data = self._create_stacked_bar_graph(player_stats, prop_info, stat_components)
            
            # Calculate hit rate
            total_values = pd.Series(0, index=range(len(player_stats)))
            for values in stat_components.values():
                values = pd.to_numeric(values, errors='coerce').fillna(0)
                total_values += values
            
            hits = sum(total_values > line_score)
            total_games = len(total_values)
            hit_rate = (hits / total_games) * 100 if total_games > 0 else 0
            
            return {
                'graph': graph_data,
                'hit_rate': round(hit_rate, 1),
                'hits': hits,
                'total_games': total_games
            }
            
        except Exception as e:
            print(f"Error in create_prop_visualization: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)} 
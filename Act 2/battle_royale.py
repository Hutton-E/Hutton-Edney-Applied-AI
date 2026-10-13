"""
battle_royale.py
================
Unit 6 Agent Battle Royale Tournament Module

This module provides bracket and round-robin tournaments for student agents.
Import and run from Jupyter notebook for an interactive tournament experience.
"""

import os
import json
import random
import math
from agents import Agent, INVEST, UNDERCUT
from game_engine import Game, Tournament
from animated_game import show_animated_game
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os
import sys
import json
import importlib.util
from pathlib import Path
# ============================================================================
# EVOLVABLE AGENT CLASS
# ============================================================================

class EvolvableAgent(Agent):
    """Agent from Unit 5 - loads from JSON"""
    
    def __init__(self, genes=None, name="Evolved Agent", student_name="Unknown"):
        if genes is None:
            genes = [random.random() for _ in range(6)]
        self.genes = genes
        self.student_name = student_name
        super().__init__(name, f"by {student_name}")
    
    def choose_action(self) -> bool:
        if self.round_num < 3:
            return random.random() < self.genes[0]
        
        memory_length = max(1, int(self.genes[4] * 10) + 1)
        recent_history = self.history[-memory_length:]
        cooperation_rate = sum(recent_history) / len(recent_history)
        
        if cooperation_rate > 0.8:
            return random.random() < self.genes[1]
        elif cooperation_rate > 0.5:
            coop_prob = self.genes[1] * (cooperation_rate - 0.5) * 2
            return random.random() < coop_prob
        else:
            if random.random() < self.genes[3] * 0.3:
                return INVEST
            else:
                return UNDERCUT


# ============================================================================
# LOAD STUDENT AGENTS
# ============================================================================

def load_student_agents(folder_path="student_agents"):
    """
    Load all student agents from Python files or JSON files.
    Supports both .py files (custom agent classes) and .json files (legacy format).
    
    Args:
        folder_path: Directory containing student agent files
    
    Returns:
        List of Agent instances
    """
    student_agents = []
    
    print("📂 Loading student agents from:", folder_path)
    print("="*70 + "\n")
    
    if not os.path.exists(folder_path):
        print(f"❌ Folder '{folder_path}' not found!")
        print(f"   Creating folder...")
        os.makedirs(folder_path)
        print(f"   Add student agent .py or .json files to this folder")
        return []
    
    # Get all Python and JSON files
    py_files = list(Path(folder_path).glob("*.py"))
    json_files = list(Path(folder_path).glob("*.json"))
    
    print(f"Found {len(py_files)} Python files and {len(json_files)} JSON files\n")
    
    # Load Python files (custom agent classes)
    for filepath in sorted(py_files):
        try:
            # Get module name from filename
            module_name = filepath.stem
            
            # Load the module dynamically
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec is None or spec.loader is None:
                print(f"❌ Could not load spec for {filepath.name}")
                continue
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Try to get the agent using get_agent() function (preferred)
            if hasattr(module, 'get_agent'):
                agent = module.get_agent()
                student_agents.append(agent)
                print(f"✅ {agent.name:30s} from {filepath.name}")
                continue
            
            # Fallback: Look for any Agent subclass in the module
            from agents import Agent
            found_agent = False
            for item_name in dir(module):
                item = getattr(module, item_name)
                if (isinstance(item, type) and 
                    issubclass(item, Agent) and 
                    item is not Agent and
                    item.__module__ == module_name):  # Only classes defined in this module
                    agent = item()
                    student_agents.append(agent)
                    print(f"✅ {agent.name:30s} from {filepath.name}")
                    found_agent = True
                    break
            
            if not found_agent:
                print(f"⚠️  No agent class found in {filepath.name}")
                
        except Exception as e:
            print(f"❌ Error loading {filepath.name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Load JSON files (legacy format - backwards compatibility)
    for filepath in sorted(json_files):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
                # Create EvolvableAgent from JSON
                agent = EvolvableAgent(
                    genes=data['genes'],
                    name=data.get('agent_name', data.get('name', 'Unnamed Agent')),
                    student_name=data.get('student_name', filepath.stem)
                )
                student_agents.append(agent)
                print(f"✅ {agent.name:30s} from {filepath.name} (JSON)")
                
        except Exception as e:
            print(f"❌ Failed to load {filepath.name}: {e}")
    
    print(f"\n📊 Total agents loaded: {len(student_agents)}")
    print("="*70 + "\n")
    
    if len(student_agents) == 0:
        print("⚠️  WARNING: No agents loaded!")
        print("   Make sure your student_agents folder contains:")
        print("   - .py files with agent classes (recommended)")
        print("   - .json files with agent data (legacy)")
    
    return student_agents


# ============================================================================
# BRACKET TOURNAMENT
# ============================================================================

class BracketTournament:
    """Single-elimination bracket tournament"""
    
    def __init__(self, agents, rounds_per_match=100):
        self.agents = agents.copy()
        self.rounds_per_match = rounds_per_match
        self.bracket_history = []
        self.round_names = []
        self.champion = None
        
    def run(self):
        """Run complete bracket tournament"""
        print("\n" + "="*70)
        print("🏆 BRACKET TOURNAMENT: SINGLE ELIMINATION")
        print("="*70 + "\n")
        
        # Shuffle for random seeding
        random.shuffle(self.agents)
        remaining = self.agents.copy()
        
        # Calculate number of rounds
        num_rounds = math.ceil(math.log2(len(remaining)))
        
        print(f"🎲 {len(remaining)} agents randomly seeded")
        print(f"🏟️  {num_rounds} rounds until champion\n")
        
        round_num = 1
        
        while len(remaining) > 1:
            # Determine round name
            if len(remaining) == 2:
                round_name = "🏆 FINALS"
            elif len(remaining) == 4:
                round_name = "🥉 SEMI-FINALS"
            elif len(remaining) == 8:
                round_name = "🎯 QUARTER-FINALS"
            elif len(remaining) == 16:
                round_name = "⚔️  ROUND OF 16"
            else:
                round_name = f"⚔️  ROUND {round_num}"
            
            self.round_names.append(round_name)
            
            print("="*70)
            print(round_name)
            print("="*70 + "\n")
            
            winners = []
            round_results = []
            
            # Pair up agents
            for i in range(0, len(remaining), 2):
                if i + 1 < len(remaining):
                    agent1 = remaining[i]
                    agent2 = remaining[i + 1]
                    
                    # Play match
                    game = Game(agent1, agent2, num_rounds=self.rounds_per_match)
                    score1, score2 = game.play()
                    
                    # Determine winner
                    if score1 > score2:
                        winner = agent1
                        loser = agent2
                        result_str = f"✅ {agent1.name:25s} defeats {agent2.name:25s} ({score1}-{score2})"
                    elif score2 > score1:
                        winner = agent2
                        loser = agent1
                        result_str = f"✅ {agent2.name:25s} defeats {agent1.name:25s} ({score2}-{score1})"
                    else:
                        # Tie - sudden death!
                        print(f"🤝 TIE: {agent1.name} vs {agent2.name} ({score1}-{score2}) - SUDDEN DEATH!")
                        sudden_death = Game(agent1, agent2, num_rounds=10)
                        score1, score2 = sudden_death.play()
                        winner = agent1 if score1 >= score2 else agent2
                        loser = agent2 if winner == agent1 else agent1
                        result_str = f"⚡ {winner.name:25s} wins sudden death! ({score1}-{score2})"
                    
                    print(result_str)
                    winners.append(winner)
                    round_results.append({
                        'agent1': agent1,
                        'agent2': agent2,
                        'score1': score1,
                        'score2': score2,
                        'winner': winner,
                        'loser': loser
                    })
                else:
                    # Bye round
                    print(f"👋 {remaining[i].name:25s} gets a bye (advances automatically)")
                    winners.append(remaining[i])
            
            self.bracket_history.append(round_results)
            remaining = winners
            round_num += 1
            print()
        
        # Champion!
        self.champion = remaining[0]
        print("="*70)
        print("🎉 TOURNAMENT CHAMPION 🎉")
        print("="*70)
        print(f"\n👑 {self.champion.name}")
        print(f"   by {self.champion.student_name}")
        print(f"\n   Survived {len(self.bracket_history)} rounds of elimination!")
        print("="*70 + "\n")
        
        return self.champion
    
    def save_bracket_image(self, filename="tournament_bracket.png"):
        """Save bracket visualization as image with improved layout"""
        if not self.bracket_history:
            print("❌ No bracket data to visualize. Run tournament first!")
            return
        
        import time
        time.sleep(1)
        
        # Calculate dimensions based on bracket structure
        num_rounds = len(self.bracket_history)
        max_matches = len(self.bracket_history[0])
        
        # Better sizing
        fig_width = max(16, num_rounds * 4)
        fig_height = max(10, max_matches * 1.2)
        
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        ax.set_xlim(-0.5, num_rounds + 1.5)
        ax.set_ylim(-1, max_matches * 2 + 1)
        ax.axis('off')
        
        # Title
        ax.text(num_rounds / 2, max_matches * 2 + 0.7, '🏆 Tournament Bracket', 
               fontsize=20, fontweight='bold', ha='center')
        
        # Track positions for connecting lines
        round_positions = []
        
        # Draw rounds from left to right
        for round_idx, (round_name, matches) in enumerate(zip(self.round_names, self.bracket_history)):
            x_pos = round_idx
            matches_in_round = len(matches)
            
            # Calculate spacing for this round
            total_height = max_matches * 2
            spacing = total_height / matches_in_round
            start_y = (total_height - (matches_in_round * spacing)) / 2 + spacing / 2
            
            # Round label
            ax.text(x_pos, total_height + 0.5, round_name, 
                   ha='center', va='bottom', fontsize=11, fontweight='bold')
            
            positions_this_round = []
            
            for match_idx, match in enumerate(matches):
                y_pos = start_y + match_idx * spacing
                positions_this_round.append(y_pos)
                
                # Box dimensions
                box_height = 0.35
                box_width = 0.85
                
                # Agent 1 (top)
                agent1_color = 'lightgreen' if match['winner'] == match['agent1'] else 'lightcoral'
                rect1 = patches.Rectangle((x_pos - box_width/2, y_pos), 
                                          box_width, box_height, 
                                          linewidth=1.5, edgecolor='black', 
                                          facecolor=agent1_color)
                ax.add_patch(rect1)
                
                agent1_text = f"{match['agent1'].name[:18]} ({match['score1']})"
                ax.text(x_pos, y_pos + box_height/2, agent1_text, 
                       ha='center', va='center', fontsize=8, fontweight='bold')
                
                # Agent 2 (bottom)
                agent2_color = 'lightgreen' if match['winner'] == match['agent2'] else 'lightcoral'
                rect2 = patches.Rectangle((x_pos - box_width/2, y_pos - box_height), 
                                          box_width, box_height, 
                                          linewidth=1.5, edgecolor='black', 
                                          facecolor=agent2_color)
                ax.add_patch(rect2)
                
                agent2_text = f"{match['agent2'].name[:18]} ({match['score2']})"
                ax.text(x_pos, y_pos - box_height/2, agent2_text, 
                       ha='center', va='center', fontsize=8, fontweight='bold')
                
                # Draw connecting line to next round
                if round_idx < num_rounds - 1:
                    # Connect to next position (every 2 matches connect to 1)
                    winner_y = y_pos if match['winner'] == match['agent1'] else y_pos - box_height
                    next_match_idx = match_idx // 2
                    
                    # Draw horizontal line from winner
                    ax.plot([x_pos + box_width/2, x_pos + 0.5], 
                           [winner_y, winner_y], 
                           'k-', linewidth=1.5, alpha=0.6)
                    
            round_positions.append(positions_this_round)
            
            # Connect pairs to next round
            if round_idx < num_rounds - 1:
                for next_idx in range(len(round_positions[round_idx + 1]) if round_idx + 1 < len(round_positions) else 0):
                    # Get the two positions that connect to this next position
                    pair_idx_1 = next_idx * 2
                    pair_idx_2 = next_idx * 2 + 1
                    
                    if pair_idx_1 < len(positions_this_round):
                        y1 = positions_this_round[pair_idx_1]
                        y2 = positions_this_round[pair_idx_2] if pair_idx_2 < len(positions_this_round) else y1
                        next_y = (y1 + y2) / 2
                        
                        # Draw vertical connector
                        ax.plot([x_pos + 0.5, x_pos + 0.5], 
                               [y1, y2], 
                               'k-', linewidth=1.5, alpha=0.6)
                        
                        # Draw horizontal to next round
                        ax.plot([x_pos + 0.5, x_pos + 1 - box_width/2], 
                               [next_y, next_y], 
                               'k-', linewidth=1.5, alpha=0.6)
        
        # Champion box
        if self.champion:
            x_pos = num_rounds + 0.5
            y_pos = max_matches
            
            crown_box = patches.FancyBboxPatch((x_pos - 0.7, y_pos - 0.5), 
                                               1.4, 1.0, 
                                               boxstyle="round,pad=0.15", 
                                               linewidth=3, edgecolor='gold', 
                                               facecolor='lightyellow')
            ax.add_patch(crown_box)
            
            ax.text(x_pos, y_pos + 0.3, "👑 CHAMPION", 
                   ha='center', va='center', fontsize=14, fontweight='bold', color='darkgoldenrod')
            ax.text(x_pos, y_pos - 0.2, self.champion.name[:18], 
                   ha='center', va='center', fontsize=11, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"✅ Bracket saved to: {filename}")
        plt.show()


# ============================================================================
# SUPERLATIVE AWARDS
# ============================================================================

def calculate_superlatives(agents, tournament):
    """Calculate fun superlative awards"""
    import time
    time.sleep(2)
    
    print("\n" + "="*70)
    print("🏅 SUPERLATIVE AWARDS")
    print("="*70 + "\n")
    
    time.sleep(1)
    
    results_df = tournament.get_results_dataframe()
    
    # Most Cooperative: Agent with highest average score when both cooperate
    most_coop_scores = {}
    for agent in agents:
        agent_matches = results_df[(results_df['Agent1'] == agent.name) | 
                                   (results_df['Agent2'] == agent.name)]
        scores = []
        for _, row in agent_matches.iterrows():
            if row['Agent1'] == agent.name:
                scores.append(row['Agent1_Score'])
            else:
                scores.append(row['Agent2_Score'])
        most_coop_scores[agent.name] = np.mean(scores) if scores else 0
    
    most_coop = max(most_coop_scores.items(), key=lambda x: x[1])
    print(f"🤝 MOST COOPERATIVE: {most_coop[0]}")
    print(f"   Average score: {most_coop[1]:.1f} (achieves mutual cooperation)")
    
    # Most Aggressive: Agent with most wins
    stats = tournament.get_summary_stats()
    most_wins = max(stats.items(), key=lambda x: x[1]['wins'])
    print(f"\n⚔️  MOST AGGRESSIVE: {most_wins[0]}")
    print(f"   Wins: {most_wins[1]['wins']} ({most_wins[1]['win_rate']:.1%} win rate)")
    
    # Most Consistent: Agent with lowest score variance
    most_consistent_var = {}
    for agent in agents:
        agent_matches = results_df[(results_df['Agent1'] == agent.name) | 
                                   (results_df['Agent2'] == agent.name)]
        scores = []
        for _, row in agent_matches.iterrows():
            if row['Agent1'] == agent.name:
                scores.append(row['Agent1_Score'])
            else:
                scores.append(row['Agent2_Score'])
        most_consistent_var[agent.name] = np.std(scores) if len(scores) > 1 else float('inf')
    
    most_consistent = min(most_consistent_var.items(), key=lambda x: x[1])
    print(f"\n📊 MOST CONSISTENT: {most_consistent[0]}")
    print(f"   Score std dev: {most_consistent[1]:.1f} (very predictable)")
    
    # Biggest Upset: Agent that beat highest-ranked opponent
    rankings = tournament.get_rankings()
    rank_dict = {name: rank for rank, (name, score) in enumerate(rankings, 1)}
    
    biggest_upset = None
    biggest_upset_diff = 0
    
    for _, row in results_df.iterrows():
        rank1 = rank_dict.get(row['Agent1'], 999)
        rank2 = rank_dict.get(row['Agent2'], 999)
        
        if row['Winner'] == row['Agent1'] and rank1 > rank2:
            rank_diff = rank1 - rank2
            if rank_diff > biggest_upset_diff:
                biggest_upset_diff = rank_diff
                biggest_upset = (row['Agent1'], row['Agent2'], rank_diff)
        elif row['Winner'] == row['Agent2'] and rank2 > rank1:
            rank_diff = rank2 - rank1
            if rank_diff > biggest_upset_diff:
                biggest_upset_diff = rank_diff
                biggest_upset = (row['Agent2'], row['Agent1'], rank_diff)
    
    if biggest_upset:
        print(f"\n🎯 BIGGEST UPSET: {biggest_upset[0]}")
        print(f"   Defeated {biggest_upset[1]} (ranked {biggest_upset[2]} spots higher)")
    
    # Glass Cannon: Highest score in a single game
    max_score = 0
    glass_cannon = None
    
    for _, row in results_df.iterrows():
        if row['Agent1_Score'] > max_score:
            max_score = row['Agent1_Score']
            glass_cannon = (row['Agent1'], row['Agent2'], row['Agent1_Score'])
        if row['Agent2_Score'] > max_score:
            max_score = row['Agent2_Score']
            glass_cannon = (row['Agent2'], row['Agent1'], row['Agent2_Score'])
    
    if glass_cannon:
        print(f"\n💥 GLASS CANNON: {glass_cannon[0]}")
        print(f"   Scored {glass_cannon[2]} points vs {glass_cannon[1]} in single game")
    
    # Participation Trophy: Last place with spirit
    last_place = rankings[-1][0]
    print(f"\n🎖️  PARTICIPATION TROPHY: {last_place}")
    print(f"   Finished last but showed up! ({rankings[-1][1]:,} points)")
    
    print("="*70)


def export_tournament_data(bracket_tournament, rr_tournament, student_agents, filename="tournament_results.json"):
    """Export all tournament data to JSON for interactive visualization"""
    import json
    import time
    
    time.sleep(1)
    
    print("\n" + "="*70)
    print("💾 EXPORTING TOURNAMENT DATA")
    print("="*70 + "\n")
    
    rankings = rr_tournament.get_rankings()
    stats = rr_tournament.get_summary_stats()
    results_df = rr_tournament.get_results_dataframe()
    
    # Build comprehensive data structure
    data = {
        "tournament_info": {
            "total_agents": len(student_agents),
            "bracket_champion": bracket_tournament.champion.name,
            "bracket_champion_student": bracket_tournament.champion.student_name,
            "round_robin_champion": rankings[0][0],
            "total_matches": len(results_df),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "agents": [],
        "bracket_rounds": [],
        "round_robin_rankings": [],
        "all_matches": [],
        "superlatives": {}
    }
    
    # Add agent data
    rank_dict = {name: rank for rank, (name, score) in enumerate(rankings, 1)}
    
    for agent in student_agents:
        rank = rank_dict.get(agent.name, 999)
        total_score = next((score for name, score in rankings if name == agent.name), 0)
        agent_stats = stats.get(agent.name, {})
        
        data["agents"].append({
            "student_name": agent.student_name,
            "agent_name": agent.name,
            "genes": agent.genes,
            "rank": rank,
            "total_score": total_score,
            "wins": agent_stats.get('wins', 0),
            "win_rate": agent_stats.get('win_rate', 0),
            "avg_score": agent_stats.get('avg_score_per_match', 0),
            "is_bracket_champion": agent.name == bracket_tournament.champion.name
        })
    
    # Add bracket rounds
    for round_idx, (round_name, matches) in enumerate(zip(bracket_tournament.round_names, 
                                                           bracket_tournament.bracket_history)):
        round_data = {
            "round_number": round_idx + 1,
            "round_name": round_name,
            "matches": []
        }
        
        for match in matches:
            round_data["matches"].append({
                "agent1": match['agent1'].name,
                "agent2": match['agent2'].name,
                "score1": match['score1'],
                "score2": match['score2'],
                "winner": match['winner'].name
            })
        
        data["bracket_rounds"].append(round_data)
    
    # Add rankings
    for rank, (name, score) in enumerate(rankings, 1):
        agent_stats = stats[name]
        data["round_robin_rankings"].append({
            "rank": rank,
            "agent_name": name,
            "total_score": score,
            "wins": agent_stats['wins'],
            "win_rate": agent_stats['win_rate'],
            "avg_score": agent_stats['avg_score_per_match']
        })
    
    # Add all match results
    for _, row in results_df.iterrows():
        data["all_matches"].append({
            "agent1": row['Agent1'],
            "agent2": row['Agent2'],
            "score1": row['Agent1_Score'],
            "score2": row['Agent2_Score'],
            "winner": row['Winner']
        })
    
    # Calculate superlatives
    most_coop_scores = {}
    for agent in student_agents:
        agent_matches = results_df[(results_df['Agent1'] == agent.name) | 
                                   (results_df['Agent2'] == agent.name)]
        scores = []
        for _, row in agent_matches.iterrows():
            if row['Agent1'] == agent.name:
                scores.append(row['Agent1_Score'])
            else:
                scores.append(row['Agent2_Score'])
        most_coop_scores[agent.name] = np.mean(scores) if scores else 0
    
    most_coop = max(most_coop_scores.items(), key=lambda x: x[1])
    most_wins = max(stats.items(), key=lambda x: x[1]['wins'])
    
    data["superlatives"]["most_cooperative"] = {
        "agent": most_coop[0],
        "avg_score": most_coop[1]
    }
    
    data["superlatives"]["most_aggressive"] = {
        "agent": most_wins[0],
        "wins": most_wins[1]['wins'],
        "win_rate": most_wins[1]['win_rate']
    }
    
    # Save to JSON
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Tournament data exported to: {filename}")
    print(f"   Total agents: {len(student_agents)}")
    print(f"   Total matches: {len(results_df)}")
    print(f"   File size: {os.path.getsize(filename) / 1024:.1f} KB")
    
    return data


# ============================================================================
# MAIN TOURNAMENT RUNNER
# ============================================================================

def run_battle_royale(folder_path="student_agents", 
                      bracket_rounds=100, 
                      rr_rounds=100, 
                      num_tournaments=3,
                      save_bracket=True):
    """
    Run complete battle royale tournament
    
    Args:
        folder_path: Path to student agent JSON files
        bracket_rounds: Rounds per match in bracket tournament
        rr_rounds: Rounds per match in round-robin
        num_tournaments: Number of round-robin iterations
        save_bracket: Whether to save bracket image
    
    Returns:
        tuple: (bracket_champion, round_robin_tournament, student_agents)
    """
    import time
    
    print("""
████████╗██╗  ██╗███████╗    ██╗   ██╗██╗  ████████╗██╗███╗   ███╗ █████╗ ████████╗███████╗
╚══██╔══╝██║  ██║██╔════╝    ██║   ██║██║  ╚══██╔══╝██║████╗ ████║██╔══██╗╚══██╔══╝██╔════╝
   ██║   ███████║█████╗      ██║   ██║██║     ██║   ██║██╔████╔██║███████║   ██║   █████╗  
   ██║   ██╔══██║██╔══╝      ██║   ██║██║     ██║   ██║██║╚██╔╝██║██╔══██║   ██║   ██╔══╝  
   ██║   ██║  ██║███████╗    ╚██████╔╝███████╗██║   ██║██║ ╚═╝ ██║██║  ██║   ██║   ███████╗
   ╚═╝   ╚═╝  ╚═╝╚══════╝     ╚═════╝ ╚══════╝╚═╝   ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝
                                                                                              
 █████╗  ██████╗ ███████╗███╗   ██╗████████╗    ██████╗  █████╗ ████████╗████████╗██╗     ███████╗
██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝    ██╔══██╗██╔══██╗╚══██╔══╝╚══██╔══╝██║     ██╔════╝
███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║       ██████╔╝███████║   ██║      ██║   ██║     █████╗  
██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║       ██╔══██╗██╔══██║   ██║      ██║   ██║     ██╔══╝  
██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║       ██████╔╝██║  ██║   ██║      ██║   ███████╗███████╗
╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝       ╚═════╝ ╚═╝  ╚═╝   ╚═╝      ╚═╝   ╚══════╝╚══════╝
                                    UNIT 6: THE SHOWDOWN
""")
    
    time.sleep(1)
    
    # Load agents
    student_agents = load_student_agents(folder_path)
    
    if len(student_agents) < 2:
        print("❌ Need at least 2 agents to run tournament!")
        return None, None, None
    
    time.sleep(1)
    
    # PART 1: Bracket Tournament
    bracket = BracketTournament(student_agents, rounds_per_match=bracket_rounds)
    bracket_champion = bracket.run()
    
    if save_bracket:
        bracket.save_bracket_image()
    
    time.sleep(2)
    
    # PART 2: Round-Robin Tournament
    print("\n" + "="*70)
    print("📊 COMPREHENSIVE ROUND-ROBIN TOURNAMENT")
    print("="*70)
    print(f"\nEvery agent plays every other agent {num_tournaments} time(s)")
    print(f"Each match: {rr_rounds} rounds")
    print(f"Total matches: {len(student_agents) * (len(student_agents) - 1) * num_tournaments}")
    print("="*70 + "\n")
    
    time.sleep(1)
    
    rr_tournament = Tournament(student_agents, rounds_per_match=rr_rounds, num_tournaments=num_tournaments)
    rr_tournament.run_tournament()
    
    time.sleep(1)
    
    # Display results
    print("\n" + "="*70)
    print("🏆 FINAL COMPREHENSIVE RANKINGS")
    print("="*70 + "\n")
    
    rankings = rr_tournament.get_rankings()
    
    for rank, (name, score) in enumerate(rankings, 1):
        emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
        bracket_winner = "👑 BRACKET CHAMPION" if name == bracket_champion.name else ""
        print(f"{emoji} {rank:2d}. {name:30s}: {score:,} points  {bracket_winner}")
    
    time.sleep(2)
    
    # Detailed stats
    print("\n" + "="*70)
    print("📈 DETAILED PERFORMANCE STATISTICS")
    print("="*70 + "\n")
    
    stats = rr_tournament.get_summary_stats()
    
    print(f"{'Agent':<30s} {'Wins':>5s} {'Win Rate':>9s} {'Avg Score':>10s}")
    print("-" * 70)
    for name in [n for n, s in rankings]:
        stat = stats[name]
        print(f"{name:<30s} {stat['wins']:>5d} {stat['win_rate']:>8.1%} {stat['avg_score_per_match']:>10.1f}")
    
    time.sleep(2)
    
    # Comparison
    print("\n" + "="*70)
    print("🤔 BRACKET vs ROUND-ROBIN COMPARISON")
    print("="*70 + "\n")
    
    round_robin_champion = rankings[0][0]
    
    if bracket_champion.name == round_robin_champion:
        print(f"🎉 SAME CHAMPION: {bracket_champion.name}")
        print("   The bracket winner also dominated the comprehensive tournament!")
    else:
        bracket_rr_rank = [i for i, (n, s) in enumerate(rankings, 1) if n == bracket_champion.name][0]
        print(f"👑 Bracket Champion:      {bracket_champion.name}")
        print(f"   Round-Robin Rank:      #{bracket_rr_rank}")
        print()
        print(f"🏆 Round-Robin Champion:  {round_robin_champion}")
        print()
        print("💡 Lesson: Single elimination is exciting but can be random!")
        print("   The most consistent performer wins the comprehensive tournament.")
    
    time.sleep(1)
    
    # Superlatives
    calculate_superlatives(student_agents, rr_tournament)
    
    time.sleep(1)
    
    # SHOW ALL STUDENT AGENTS AND THEIR RANKINGS
    print("\n" + "="*70)
    print("👥 ALL STUDENT AGENTS - FIND YOURS!")
    print("="*70 + "\n")
    
    rank_dict = {name: (rank, score) for rank, (name, score) in enumerate(rankings, 1)}
    
    print(f"{'Student':<25s} {'Agent Name':<30s} {'Rank':>6s} {'Score':>10s}")
    print("-" * 80)
    
    for agent in sorted(student_agents, key=lambda a: rank_dict.get(a.name, (999, 0))[0]):
        rank, score = rank_dict.get(agent.name, (999, 0))
        emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
        print(f"{emoji} {agent.student_name:<25s} {agent.name:<30s} {rank:>4d} {score:>10,}")
    
    # Export tournament data and generate dashboard
    tournament_data = export_tournament_data(bracket, rr_tournament, student_agents)
    generate_interactive_dashboard(tournament_data)
    
    return bracket_champion, rr_tournament, student_agents
def generate_interactive_dashboard(tournament_data, filename="tournament_dashboard.html"):
    """Generate interactive HTML dashboard for exploring results"""
    import time
    
    time.sleep(1)
    
    print("\n" + "="*70)
    print("🌐 GENERATING INTERACTIVE DASHBOARD")
    print("="*70 + "\n")
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tournament Results - Unit 6</title>
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@200;300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            /* Core brand */
            --rize-capstone:   #0159CB; /* deep blue */
            --rize-legacy:     #014195; /* darker blue */
            --rize-pathfinder: #0195FF; /* bright blue */
            --rize-clearsky:   #3FB2FF; /* light blue */
            --rize-spark:      #FFE100; /* CTA yellow */
            --rize-honor:      #FFBB00; /* deeper yellow */
            --rize-midnight:   #001228; /* very dark */
            --rize-slate:      #3C4451; /* neutral dark */
            --rize-stark:      #141A22; /* neutral darkest */
            --rize-quiet:      #F5F7FA; /* near-white */
            --rize-soft:       #D5DAE0; /* light gray */
            --rize-insight:    #8B94A3; /* medium gray */

            /* Semantic app tokens */
            --background: #F0F0F0;
            --foreground: var(--rize-stark);
            --surface: #ffffff;
            --muted: var(--rize-insight);
            --border: var(--rize-soft);

            --primary: var(--rize-capstone);
            --primary-strong: var(--rize-legacy);
            --primary-contrast: #ffffff;

            --accent: var(--rize-spark);
            --accent-strong: var(--rize-honor);
            --accent-contrast: #141A22;

            --link: var(--rize-pathfinder);
            --link-hover: var(--rize-legacy);
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: "Manrope", -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, var(--rize-capstone) 0%, var(--rize-pathfinder) 100%);
            color: var(--foreground);
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            color: var(--primary-contrast);
            margin-bottom: 30px;
        }}
        
        h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .card {{
            background: var(--surface);
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            border: 1px solid var(--border);
        }}
        
        .card h2 {{
            color: var(--primary);
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 3px solid var(--primary);
            padding-bottom: 10px;
            font-weight: 600;
        }}
        
        .champions {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        
        .champion-box {{
            background: linear-gradient(135deg, var(--accent) 0%, var(--accent-strong) 100%);
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            box-shadow: 0 6px 20px rgba(255, 225, 0, 0.3);
            color: var(--accent-contrast);
        }}
        
        .champion-box h3 {{
            font-size: 1.5em;
            margin-bottom: 10px;
            font-weight: 600;
        }}
        
        .champion-box .name {{
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }}
        
        .champion-box .student {{
            font-size: 1.2em;
            color: var(--rize-slate);
        }}
        
        .search-box {{
            margin-bottom: 20px;
        }}
        
        .search-box input {{
            width: 100%;
            padding: 15px;
            font-size: 1.1em;
            border: 2px solid var(--primary);
            border-radius: 8px;
            font-family: inherit;
        }}
        
        .search-box input:focus {{
            outline: none;
            border-color: var(--link);
            box-shadow: 0 0 0 3px rgba(1, 149, 255, 0.1);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th {{
            background: var(--primary);
            color: var(--primary-contrast);
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid var(--border);
        }}
        
        tr:hover {{
            background: var(--rize-quiet);
        }}
        
        .rank-1 {{ background: rgba(255, 225, 0, 0.15); }}
        .rank-2 {{ background: rgba(192, 192, 192, 0.15); }}
        .rank-3 {{ background: rgba(205, 127, 50, 0.15); }}
        
        .medal {{
            font-size: 1.5em;
            margin-right: 5px;
        }}
        
        .tab-container {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }}
        
        .tab {{
            padding: 12px 24px;
            background: var(--rize-quiet);
            border: 1px solid var(--border);
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 600;
            transition: all 0.3s;
            font-family: inherit;
        }}
        
        .tab:hover {{
            background: var(--rize-soft);
            border-color: var(--primary);
        }}
        
        .tab.active {{
            background: var(--primary);
            color: var(--primary-contrast);
            border-color: var(--primary);
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        .tournament-bracket {{
            display: flex;
            padding: 20px;
            overflow-x: auto;
            min-height: 600px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 12px;
            gap: 40px;
            justify-content: center;
        }}
        
        .bracket-round {{
            display: flex;
            flex-direction: column;
            justify-content: space-around;
            min-width: 220px;
            position: relative;
        }}
        
        .bracket-round h3 {{
            color: var(--primary-strong);
            margin-bottom: 20px;
            font-weight: 600;
            text-align: center;
            background: white;
            padding: 8px 16px;
            border-radius: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .bracket-match {{
            background: white;
            border-radius: 12px;
            padding: 16px;
            margin: 8px 0;
            border: 2px solid var(--border);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            position: relative;
            transition: all 0.3s ease;
        }}
        
        .bracket-match:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }}
        
        .bracket-agent {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            margin: 4px 0;
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.2s ease;
        }}
        
        .bracket-agent.winner {{
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            transform: scale(1.02);
        }}
        
        .bracket-agent.loser {{
            background: #f8f9fa;
            color: #6c757d;
            opacity: 0.8;
        }}
        
        .agent-name {{
            font-size: 14px;
            font-weight: 600;
        }}
        
        .agent-score {{
            font-size: 16px;
            font-weight: bold;
            background: rgba(255,255,255,0.2);
            padding: 4px 8px;
            border-radius: 12px;
            min-width: 30px;
            text-align: center;
        }}
        
        .bracket-connector {{
            position: absolute;
            right: -20px;
            top: 50%;
            width: 40px;
            height: 2px;
            background: var(--primary-strong);
            z-index: 1;
        }}
        
        .bracket-connector::after {{
            content: '';
            position: absolute;
            right: -6px;
            top: -4px;
            width: 0;
            height: 0;
            border-left: 8px solid var(--primary-strong);
            border-top: 4px solid transparent;
            border-bottom: 4px solid transparent;
        }}
        
        .championship-trophy {{
            position: absolute;
            top: -10px;
            right: -10px;
            font-size: 24px;
            z-index: 2;
        }}
        
        .agent {{
            flex: 1;
            padding: 10px;
            border-radius: 6px;
        }}
        
        .agent.winner {{
            background: rgba(76, 175, 80, 0.15);
            border-left: 4px solid #4caf50;
            font-weight: bold;
        }}
        
        .agent.loser {{
            background: rgba(244, 67, 54, 0.15);
            border-left: 4px solid #f44336;
            opacity: 0.7;
        }}
        
        .vs {{
            font-weight: bold;
            color: var(--primary);
            padding: 0 15px;
        }}
        
        .superlative {{
            background: linear-gradient(135deg, rgba(1, 89, 203, 0.1) 0%, rgba(1, 149, 255, 0.1) 100%);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            border: 1px solid var(--border);
        }}
        
        .superlative h4 {{
            color: var(--primary);
            margin-bottom: 10px;
            font-size: 1.3em;
            font-weight: 600;
        }}
        
        .highlight {{
            background: yellow;
            padding: 2px 5px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏆 Agent Battle Royale Results</h1>
            <p class="subtitle">Unit 6: The Ultimate Showdown</p>
            <p class="subtitle">Generated: {tournament_data['tournament_info']['generated_at']}</p>
        </header>
        
        <div class="card">
            <h2>🎉 Tournament Champions</h2>
            <div class="champions">
                <div class="champion-box">
                    <h3>👑 Bracket Champion</h3>
                    <div class="name">{tournament_data['tournament_info']['bracket_champion']}</div>
                    <div class="student">by {tournament_data['tournament_info']['bracket_champion_student']}</div>
                    <p style="margin-top: 10px; color: #666;">Won the single-elimination bracket!</p>
                </div>
                <div class="champion-box">
                    <h3>🏆 Round-Robin Champion</h3>
                    <div class="name">{tournament_data['tournament_info']['round_robin_champion']}</div>
                    <p style="margin-top: 10px; color: #666;">Highest total score across all matches!</p>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>📊 Explore Results</h2>
            
            <div class="tab-container">
                <button class="tab active" onclick="showTab('rankings')">🏅 Rankings</button>
                <button class="tab" onclick="showTab('agents')">👥 All Agents</button>
                <button class="tab" onclick="showTab('bracket')">🌳 Bracket</button>
                <button class="tab" onclick="showTab('superlatives')">🎖️ Awards</button>
                <button class="tab" onclick="showTab('glossary')">📚 Glossary</button>
            </div>
            
            <div id="rankings" class="tab-content active">
                <div class="search-box">
                    <input type="text" id="searchRankings" placeholder="🔍 Search by student name or agent name..." 
                           onkeyup="filterTable('rankingsTable', 'searchRankings')">
                </div>
                <table id="rankingsTable">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Agent Name</th>
                            <th>Total Score</th>
                            <th>Wins</th>
                            <th>Win Rate</th>
                            <th>Avg Score</th>
                        </tr>
                    </thead>
                    <tbody>"""
    
    # Add rankings
    for ranking in tournament_data['round_robin_rankings']:
        rank = ranking['rank']
        rank_class = f"rank-{rank}" if rank <= 3 else ""
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else ""
        
        html += f"""
                        <tr class="{rank_class}">
                            <td><span class="medal">{medal}</span>{rank}</td>
                            <td><strong>{ranking['agent_name']}</strong></td>
                            <td>{ranking['total_score']:,}</td>
                            <td>{ranking['wins']}</td>
                            <td>{ranking['win_rate']:.1%}</td>
                            <td>{ranking['avg_score']:.1f}</td>
                        </tr>"""
    
    html += """
                    </tbody>
                </table>
            </div>
            
            <div id="agents" class="tab-content">
                <div class="search-box">
                    <input type="text" id="searchAgents" placeholder="🔍 Search by student name or agent name..." 
                           onkeyup="filterTable('agentsTable', 'searchAgents')">
                </div>
                <table id="agentsTable">
                    <thead>
                        <tr>
                            <th>Student Name</th>
                            <th>Agent Name</th>
                            <th>Rank</th>
                            <th>Total Score</th>
                            <th>Win Rate</th>
                        </tr>
                    </thead>
                    <tbody>"""
    
    # Add all agents sorted by rank
    sorted_agents = sorted(tournament_data['agents'], key=lambda x: x['rank'])
    for agent in sorted_agents:
        rank = agent['rank']
        rank_class = f"rank-{rank}" if rank <= 3 else ""
        bracket_badge = "👑" if agent['is_bracket_champion'] else ""
        
        html += f"""
                        <tr class="{rank_class}">
                            <td>{agent['student_name']}</td>
                            <td><strong>{agent['agent_name']}</strong> {bracket_badge}</td>
                            <td>{rank}</td>
                            <td>{agent['total_score']:,}</td>
                            <td>{agent['win_rate']:.1%}</td>
                        </tr>"""
    
    html += """
                    </tbody>
                </table>
            </div>
            
            <div id="bracket" class="tab-content">
                <div class="tournament-bracket">"""
    
    # Create proper tournament bracket visualization
    for round_idx, bracket_round in enumerate(tournament_data['bracket_rounds']):
        is_final = round_idx == len(tournament_data['bracket_rounds']) - 1
        html += f"""
                    <div class="bracket-round">
                        <h3>{bracket_round['round_name']}</h3>"""
        
        for match in bracket_round['matches']:
            agent1_class = "winner" if match['winner'] == match['agent1'] else "loser"
            agent2_class = "winner" if match['winner'] == match['agent2'] else "loser"
            
            # Add trophy for championship match
            trophy = "🏆" if is_final else ""
            connector = "" if is_final else '<div class="bracket-connector"></div>'
            
            html += f"""
                        <div class="bracket-match">
                            {trophy and '<div class="championship-trophy">🏆</div>'}
                            <div class="bracket-agent {agent1_class}">
                                <span class="agent-name">{match['agent1']}</span>
                                <span class="agent-score">{match['score1']}</span>
                            </div>
                            <div class="bracket-agent {agent2_class}">
                                <span class="agent-name">{match['agent2']}</span>
                                <span class="agent-score">{match['score2']}</span>
                            </div>
                            {connector}
                        </div>"""
        
        html += """
                    </div>"""
    
    html += """
                </div>"""
    
    html += """
            </div>
            
            <div id="superlatives" class="tab-content">
                <div class="superlative">
                    <h4>🤝 Most Cooperative Agent</h4>
                    <p><strong>{}</strong> with an average score of <strong>{:.1f}</strong> points per game</p>
                    <p style="color: #666; margin-top: 5px;">Achieved mutual cooperation consistently</p>
                </div>
                
                <div class="superlative">
                    <h4>⚔️ Most Aggressive Agent</h4>
                    <p><strong>{}</strong> with <strong>{}</strong> wins (<strong>{:.1%}</strong> win rate)</p>
                    <p style="color: #666; margin-top: 5px;">Dominated head-to-head matchups</p>
                </div>
            </div>
            
            <div id="glossary" class="tab-content">
                <div class="glossary-section">
                    <h3>Tournament Structure</h3>
                    <p><strong>Bracket Tournament</strong> is a single-elimination competition where agents are paired off in matches, and the winner advances while the loser is eliminated. This creates a tournament tree that culminates in a single champion. Each pairing is determined by the bracket structure, ensuring every agent has an equal path to victory.</p>
                    
                    <p><strong>Round-Robin Tournament</strong> is a comprehensive format where every agent plays against every other agent multiple times. Unlike the bracket tournament, no one is eliminated - instead, agents accumulate points across all their matches. This format provides a more complete picture of agent performance by testing them against the full field of competitors.</p>
                </div>
                
                <div class="glossary-section">
                    <h3>Scoring and Strategy</h3>
                    <p><strong>Cooperation vs Competition</strong> is the fundamental tension in this tournament. In each round of a match, agents can either INVEST (cooperate) or UNDERCUT (defect). When both agents cooperate, they both receive substantial points. When one cooperates and the other defects, the defector gets maximum points while the cooperator gets minimal points. When both defect, both receive moderate points.</p>
                    
                    <p><strong>The Win Rate Paradox</strong> reveals why having the highest win rate doesn't guarantee the most total points. An agent that consistently undercuts opponents might win many matches by narrow margins, while an agent that seeks mutual cooperation might lose some matches but accumulate far more total points through high-scoring cooperative rounds. Since ties don't count as wins in the win rate calculation, an agent achieving many high-scoring draws through cooperation will have a lower win rate despite superior point accumulation.</p>
                </div>
                
                <div class="glossary-section">
                    <h3>Performance Metrics</h3>
                    <p><strong>Total Score</strong> represents the cumulative points an agent earned across all matches in the round-robin tournament. This is often the most important metric as it reflects sustained performance and strategic effectiveness over many encounters.</p>
                    
                    <p><strong>Win Rate</strong> shows the percentage of matches an agent won outright, calculated as wins divided by total matches (excluding ties). A high win rate indicates consistent dominance in head-to-head matchups, but may not reflect the highest scoring potential.</p>
                    
                    <p><strong>Average Score</strong> normalizes performance by dividing total points by the number of matches played. This metric helps compare agents who may have played different numbers of matches and reveals scoring efficiency.</p>
                </div>
                
                <div class="glossary-section">
                    <h3>Agent Recognition</h3>
                    <p><strong>Most Cooperative Agent</strong> is recognized for achieving the highest average score per game, typically through successful mutual cooperation strategies. This agent demonstrates that fostering collaboration can be more profitable than constant competition.</p>
                    
                    <p><strong>Most Aggressive Agent</strong> is the agent with the highest win rate, showing dominance in head-to-head matchups. This recognition goes to agents that consistently outmaneuver their opponents, even if their total point accumulation isn't the highest.</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function showTab(tabName) {{
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {{
                tab.classList.remove('active');
            }});
            document.querySelectorAll('.tab').forEach(button => {{
                button.classList.remove('active');
            }});
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }}
        
        function filterTable(tableId, searchId) {{
            const input = document.getElementById(searchId);
            const filter = input.value.toUpperCase();
            const table = document.getElementById(tableId);
            const tr = table.getElementsByTagName('tr');
            
            for (let i = 1; i < tr.length; i++) {{
                const td = tr[i].getElementsByTagName('td');
                let found = false;
                
                for (let j = 0; j < td.length; j++) {{
                    if (td[j]) {{
                        const txtValue = td[j].textContent || td[j].innerText;
                        if (txtValue.toUpperCase().indexOf(filter) > -1) {{
                            found = true;
                            break;
                        }}
                    }}
                }}
                
                tr[i].style.display = found ? "" : "none";
            }}
        }}
        
        // Bracket interactive features
        document.addEventListener('DOMContentLoaded', function() {{
            // Add click handlers for bracket matches
            document.querySelectorAll('.bracket-match').forEach(match => {{
                match.addEventListener('click', function() {{
                    // Highlight the match path
                    this.style.transform = 'scale(1.05)';
                    this.style.zIndex = '10';
                    
                    // Reset after animation
                    setTimeout(() => {{
                        this.style.transform = '';
                        this.style.zIndex = '';
                    }}, 300);
                }});
            }});
            
            // Add hover effects for bracket rounds
            document.querySelectorAll('.bracket-round').forEach(round => {{
                round.addEventListener('mouseenter', function() {{
                    this.style.opacity = '1';
                    document.querySelectorAll('.bracket-round').forEach(otherRound => {{
                        if (otherRound !== this) {{
                            otherRound.style.opacity = '0.7';
                        }}
                    }});
                }});
                
                round.addEventListener('mouseleave', function() {{
                    document.querySelectorAll('.bracket-round').forEach(round => {{
                        round.style.opacity = '1';
                    }});
                }});
            }});
        }});
    </script>
</body>
</html>""".format(
        tournament_data['superlatives']['most_cooperative']['agent'],
        tournament_data['superlatives']['most_cooperative']['avg_score'],
        tournament_data['superlatives']['most_aggressive']['agent'],
        tournament_data['superlatives']['most_aggressive']['wins'],
        tournament_data['superlatives']['most_aggressive']['win_rate']
    )
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Interactive dashboard generated: {filename}")
    print(f"   Open this file in your browser to explore results!")
    print(f"   Features:")
    print(f"     - Searchable tables")
    print(f"     - Tabbed interface")
    print(f"     - Bracket visualization")
    print(f"     - Superlative awards")
    
    return filename

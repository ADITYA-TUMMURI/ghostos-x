import os
import re
import sqlite3
from datetime import datetime

# Database path in user's home directory
DB_PATH = os.path.expanduser("~/.local/share/ghostos/activity.db")


def compute_transition_matrix(current_context=None, db_path=DB_PATH):
    """
    Computes transition probabilities P(App_B | App_A) using time-decayed
    weights and optional context-aware adjustments from SQLite history.
    
    Returns:
        dict: A nested dictionary of transition probabilities.
              Example: { 'VSCode': { 'Terminal': 0.8, 'Chrome': 0.2 } }
    """
    if not os.path.exists(db_path):
        return {}
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Load the last 10,000 activities chronologically
        cursor.execute(
            """
            SELECT app_name, start_time, context_hint 
            FROM activity 
            ORDER BY start_time DESC, id DESC 
            LIMIT 10000
            """
        )
        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        print(f"[GhostOS] Database error in Markov Engine: {e}")
        return {}

    if not rows or len(rows) < 2:
        return {}

    # Reverse rows to chronological order
    rows.reverse()
    
    # Transition counts accumulator: app_a -> { app_b: accumulated_weight }
    matrix = {}
    now = datetime.now()
    
    for i in range(len(rows) - 1):
        app_a, start_a, context_a = rows[i]
        app_b, start_b, context_b = rows[i + 1]
        
        # Skip transition endpoints that represent Idle states
        if app_a == "Idle" or app_b == "Idle":
            continue
            
        try:
            dt_b = datetime.fromisoformat(start_b)
        except Exception:
            continue
            
        # Calculate time difference in days
        days_ago = (now - dt_b).days
        
        # Determine time-decay weight
        if days_ago <= 7:
            weight = 1.0
        elif days_ago <= 30:
            weight = 0.5
        else:
            weight = 0.1
            
        # Context-aware prioritization:
        # If a current context hint is active and the starting point (App_A)
        # occurred in that exact context, prioritize the transition.
        if current_context and context_a == current_context:
            weight *= 5.0
            
        if app_a not in matrix:
            matrix[app_a] = {}
        matrix[app_a][app_b] = matrix[app_a].get(app_b, 0.0) + weight
        
    # Convert absolute transition weights to probabilities P(App_B | App_A)
    probabilities = {}
    for app_a, transitions in matrix.items():
        total_weight = sum(transitions.values())
        if total_weight > 0:
            probabilities[app_a] = {
                app_b: weight / total_weight 
                for app_b, weight in transitions.items()
            }
        else:
            probabilities[app_a] = {}
            
    return probabilities


def predict_next_intent(current_app, current_context=None, db_path=DB_PATH):
    """
    Exposes a query interface returning the next predicted application with 
    the highest transition probability from the current_app and context.
    """
    if not current_app or current_app == "Idle":
        return None
        
    matrix = compute_transition_matrix(current_context=current_context, db_path=db_path)
    
    if current_app in matrix and matrix[current_app]:
        transitions = matrix[current_app]
        # Return the destination application with maximum transition probability
        return max(transitions, key=transitions.get)
        
    return None

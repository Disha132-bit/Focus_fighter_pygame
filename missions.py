import pygame
import random

# ─── Mission State ───
mission_active = False
mission_start_time = 0
mission_type = ""
_mission_success = False
_mission_failed = False
_mission_progress = 0
mission_success_time = 0
_powerup_used = False

# ─── Mission List ───
missions = [
    {
        "type": "defeat_enemies",
        "description": "Defeat 10 enemies in 30 seconds",
        "goal": 10,
        "time": 30000
    },
    {
        "type": "no_powerups",
        "description": "Survive 30 seconds without power-ups",
        "goal": 30000,
        "time": 30000
    },
    {
        "type": "accuracy",
        "description": "Maintain 80% accuracy for 1 minute",
        "goal": 80,
        "time": 60000
    }
]

selected_mission = None

def reset_mission():
    global mission_active, mission_start_time, mission_type
    global _mission_success, _mission_failed, _mission_progress
    global selected_mission, mission_success_time, _powerup_used
    mission_active = False
    mission_start_time = 0
    mission_type = ""
    _mission_success = False
    _mission_failed = False
    _mission_progress = 0
    selected_mission = None
    mission_success_time = 0
    _powerup_used = False

def start_random_mission():
    global mission_active, mission_start_time, mission_type, selected_mission
    selected_mission = random.choice(missions)
    mission_type = selected_mission["type"]
    mission_active = True
    mission_start_time = pygame.time.get_ticks()

def update_mission(total_attacks, successful_hits):
    global mission_active, _mission_success, _mission_failed, mission_success_time
    global selected_mission, mission_start_time

    if not mission_active or not selected_mission:
        return

    current_time = pygame.time.get_ticks()
    elapsed = current_time - mission_start_time
    goal = selected_mission["goal"]
    limit = selected_mission["time"]

    if selected_mission["type"] == "defeat_enemies":
        if _mission_progress >= goal:
            _mission_success = True
            mission_active = False
            mission_success_time = current_time
        elif elapsed > limit:
            _mission_failed = True
            mission_active = False
            mission_success_time = current_time

    elif selected_mission["type"] == "no_powerups":
        if _powerup_used:
            _mission_failed = True
            mission_active = False
            mission_success_time = current_time
        elif elapsed > limit:
            _mission_success = True
            mission_active = False
            mission_success_time = current_time

    elif selected_mission["type"] == "accuracy":
        if total_attacks == 0:
            return  # Can't calculate accuracy yet

        accuracy = (successful_hits / total_attacks) * 100

        # ⛔ Fail only if accuracy is strictly less than the goal (e.g. < 80%)
        if accuracy < goal:
            _mission_failed = True
            mission_active = False
            mission_success_time = current_time
            return

        # ✅ Success only if full time passed and accuracy is still high enough
        if elapsed >= limit:
            _mission_success = True
            mission_active = False
            mission_success_time = current_time

# Accessors
def get_mission_description():
    return selected_mission["description"] if selected_mission else ""

def get_mission_progress():
    return _mission_progress

def increment_mission_progress():
    global _mission_progress
    _mission_progress += 1

def mission_success():
    return _mission_success

def mission_failed():
    return _mission_failed

def get_mission_type():
    return mission_type

def get_mission_success_time():
    return mission_success_time

def is_mission_active():
    return mission_active

def mark_powerup_used():
    global _powerup_used
    _powerup_used = True

def get_selected_mission():
    return selected_mission

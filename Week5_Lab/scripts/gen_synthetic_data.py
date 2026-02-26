"""Generate synthetic cybersecurity event data for CS5542 Week5 Lab."""
import csv
import random
import os
from datetime import datetime, timedelta

random.seed(42)

TEAMS = ["SwarmAlpha", "SwarmBeta", "SwarmGamma", "HumanRed", "HumanBlue", "BotNet1", "BotNet2", "BotNet3"]
CATEGORIES = ["recon_scan", "brute_force", "credential_spray", "lateral_move", "data_exfil", "c2_callback", "privilege_esc", "phishing", "port_scan", "exploit_attempt"]
ROLES = ["Orchestrator", "Scanner", "Exploiter", "Exfiltrator", "Analyst", "Operator"]

TEAM_TYPES = {
    "SwarmAlpha": "ai_swarm", "SwarmBeta": "ai_swarm", "SwarmGamma": "ai_swarm",
    "HumanRed": "human", "HumanBlue": "human",
    "BotNet1": "scripted_bot", "BotNet2": "scripted_bot", "BotNet3": "scripted_bot",
}

# --- Users ---
users = []
uid = 1
for team in TEAMS:
    n_members = random.randint(3, 8)
    for i in range(n_members):
        role = random.choice(ROLES)
        created = datetime(2026, 1, 1) + timedelta(days=random.randint(0, 30))
        users.append({
            "USER_ID": f"U{uid:04d}",
            "TEAM": team,
            "ROLE": role,
            "CREATED_AT": created.strftime("%Y-%m-%d %H:%M:%S"),
            "AGENT_TYPE": TEAM_TYPES[team],
        })
        uid += 1

# --- Events ---
events = []
eid = 1
base_time = datetime(2026, 2, 1, 0, 0, 0)

for _ in range(600):
    team = random.choice(TEAMS)
    agent_type = TEAM_TYPES[team]
    cat = random.choice(CATEGORIES)
    
    # AI swarms: bursty, coordinated timing
    if agent_type == "ai_swarm":
        offset_hours = random.gauss(12 * random.randint(0, 14), 2)
        value = round(random.gauss(75, 15), 2)
    # Humans: spread out, variable
    elif agent_type == "human":
        offset_hours = random.uniform(0, 24 * 20)
        value = round(random.gauss(45, 25), 2)
    # Bots: periodic, mechanical
    else:
        offset_hours = random.randint(0, 200) * 2.4
        value = round(random.gauss(60, 5), 2)

    event_time = base_time + timedelta(hours=max(0, offset_hours))
    value = max(0.1, value)

    events.append({
        "EVENT_ID": f"E{eid:05d}",
        "EVENT_TIME": event_time.strftime("%Y-%m-%d %H:%M:%S"),
        "TEAM": team,
        "CATEGORY": cat,
        "VALUE": value,
        "AGENT_TYPE": agent_type,
    })
    eid += 1

# Sort by time
events.sort(key=lambda x: x["EVENT_TIME"])

# --- Write CSVs ---
data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(data_dir, exist_ok=True)

with open(os.path.join(data_dir, "events.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["EVENT_ID", "EVENT_TIME", "TEAM", "CATEGORY", "VALUE", "AGENT_TYPE"])
    w.writeheader()
    w.writerows(events)

with open(os.path.join(data_dir, "users.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["USER_ID", "TEAM", "ROLE", "CREATED_AT", "AGENT_TYPE"])
    w.writeheader()
    w.writerows(users)

print(f"Generated {len(events)} events, {len(users)} users")
print(f"Teams: {len(TEAMS)}, Categories: {len(CATEGORIES)}")
print(f"Agent types: ai_swarm={sum(1 for e in events if e['AGENT_TYPE']=='ai_swarm')}, "
      f"human={sum(1 for e in events if e['AGENT_TYPE']=='human')}, "
      f"scripted_bot={sum(1 for e in events if e['AGENT_TYPE']=='scripted_bot')}")

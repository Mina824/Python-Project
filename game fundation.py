import random


AIRPORTS = {
    "CYVR": {"name": "Vancouver International Airport", "continent": 4, "risk_factor": 2, "clinic": 1, "healing": 20.00,
             "time_factor": 0.60},
    "CYYZ": {"name": "Toronto Pearson International Airport", "continent": 4, "risk_factor": 1, "clinic": 1,
             "healing": 19.00, "time_factor": 0.50},
    "DNMM": {"name": "Murtala Muhammed Intl Airport (Lagos)", "continent": 3, "risk_factor": 1, "clinic": 0,
             "healing": None, "time_factor": None},
    # ... (add all other airports in the same format)
    "ZSPD": {"name": "Shanghai Pudong Intl Airport", "continent": 1, "risk_factor": 1, "clinic": 1, "healing": 22.00,
             "time_factor": 0.65}
}


CONNECTIONS = [
    {"id": 1, "from": "OTHH", "to": "VIDP", "time": 225, "health_cost": 0.05},
    {"id": 2, "from": "VIDP", "to": "OTHH", "time": 240, "health_cost": 0.05},
    {"id": 3, "from": "OTHH", "to": "WSSS", "time": 430, "health_cost": 0.05},
    # ... (add all other connections in the same format)
    {"id": 108, "from": "NZAA", "to": "PHNL", "time": 480, "health_cost": 0.05}
]


RISK_DEPARTURE = [
    {"id": 1, "name": "Severe Weather", "probability": 0.2000, "delay": 120, "health_loss": 1.50},
    {"id": 2, "name": "Technical Issues", "probability": 0.0500, "delay": 360, "health_loss": 3.00},
    {"id": 3, "name": "Crew Fatigue", "probability": 0.0010, "delay": 60, "health_loss": 0.30}
]


RISK_DIVERSION = [
    {"id": 1, "name": "Severe Weather Diversion", "probability": 0.05, "penalty": 240, "health_loss": 2.00},
    {"id": 2, "name": "In-Flight Medical Emergency Diversion", "probability": 0.01, "penalty": 180,
     "health_loss": 2.50},
    {"id": 3, "name": "Air Traffic Control Reroute", "probability": 0.08, "penalty": 120, "health_loss": 2.50},
    {"id": 4, "name": "Cabin Pressure Loss", "probability": 0.02, "penalty": 360, "health_loss": 5.00}
]



def initialize_game():

    airports_with_clinics = [code for code, data in AIRPORTS.items() if data["clinic"] == 1]

    start_location = random.choice(list(AIRPORTS.keys()))

    target_hospital = random.choice(airports_with_clinics)

    while start_location == target_hospital:
        target_hospital = random.choice(airports_with_clinics)

    return start_location, target_hospital

start, target = initialize_game()
print(f"Start Location: {AIRPORTS[start]['name']} ({start})")
print(f"Target Hospital: {AIRPORTS[target]['name']} ({target})")
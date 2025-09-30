import random
import sys
import mysql.connector

maximum_time_minutes = 1440
start_health = 75.0
health_cost_per_minute = 0.080
healing_time_factor = 60

current_health = start_health
total_time_minutes = 0
current_location = None
target_hospital = None

airports = {}
connections = []
departure_risk = []
diversion_risk = []

def get_data_from_database():
    global airports
    global connections
    global departure_risk
    global diversion_risk

    connection = mysql.connector.connect(
        host= 'mysql.metropolia.fi',
        port=3306,
        database='sadhanid',
        user='sadhanid',
        password='123456',
        autocommit=True
    )
    cursor = connection.cursor(dictionary=True)
    print('connected to database ')

    sql_query_airport = """
        SELECT 
            ICAO_Code, Airport_Name, Continent_ID, 
            Risk_Factor_ID, Clinic, Clinic_Healing_Amount, 
            Clinic_Time_Factor 
        FROM Airport table
    """
    cursor.execute(sql_query_airport)
    for row in cursor. fetchall():
        icao_code = row['ICAO_Code']
        airports[icao_code] = {'Name': row['Airport_Name'],
                              'Continent' : row['Continent_ID'],
                              'Clinic' : bool(row['Clinic']),
                              ** ({'Healing Amount' : float(row['Clinic_Healing_Amount']),
                              'Time_Factor': float(row['Clinic_Time_Factor'])}
                              if row['Clinic'] else None) }
    print(f"Loaded {len(airports)} Airports from database")

    sql_query_connection = """
        SELECT  Departure_Airport_ID, Arrival_Airport_ID, Travel_Time_Minutes 
        FROM Interconnection table
    """
    cursor.execute(sql_query_connection)
    for row in cursor. fetchall():
        connections.append({
            'Departure_Airport_ID': row['Departure_Airport_ID'],
            'Arrival_Airport_ID': row['Arrival_Airport_ID'],
            'Time_Minutes' : int(row['Travel_Time_Minutes']),
        })

    sql_query_departure_risk = """ 
        SELECT Departure_Risk_ID, Departure_Risk_Name, Probability_of_Occurring, 
               Time_Delay_Minutes, Health_Loss,
        FROM Departure_Risk table
    """
    cursor.execute(sql_query_departure_risk)
    for row in cursor. fetchall():
        departure_risk.append({
            'Name': row['Departure_Risk_Name'],
            'Probability_of_Occurring': float(row['Probability_of_Occurring']),
            'Time_Delay_Minutes': int(row['Time_Delay_Minutes']),
            'Health_Loss': float(row['Health_Loss']),
        })

    sql_query_diversion_risk = """
        SELECT Diversion_Risk_ID,Diversion_Risk_Name,Probability_of_Occurring,
               Time_Penalty_Minutes, Health_Loss,
        FROM Diversion_Risk table 
    """
    cursor.execute(sql_query_diversion_risk)
    for row in cursor.fetchall():
        departure_risk.append({
            'Name': row['Diversion_Risk_Name'],
            'Probability_of_Occurring': float(row['Probability_of_Occurring']),
            'Time_Delay_Minutes': int(row['Time_Penalty_Minutes']),
            'Health_Loss': float(row['Health_Loss']),
        })
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()

def load_emergency_data():
    global airports, connections, departure_risk, diversion_risk
    airports.update({
        'OTHH': {'Name': 'Doha', 'Continent': 'Asia', 'Clinic': True, 'Healing': 25.0, 'TimeFactor': 0.75},
        'EGLL': {'Name': 'London', 'Continent': 'Europe', 'Clinic': True, 'Healing': 20.0, 'TimeFactor': 0.50},
        'KJFK': {'Name': 'New York', 'Continent': 'North America', 'Clinic': False},
    })
    connections.extend([
        {'Departure_Airport_ID': 'OTHH', 'Arrival_Airport_ID': 'EGLL', 'Time': 420},
        {'Departure_Airport_ID': 'EGLL', 'Arrival_Airport_ID': 'OTHH', 'Time': 400},
        {'Departure_Airport_ID': 'EGLL', 'Arrival_Airport_ID': 'KJFK', 'Time': 450},
        {'Departure_Airport_ID': 'KJFK', 'Arrival_Airport_ID': 'EGLL', 'Time': 380},
    ])
    departure_risk.extend([
        {'Name': 'Weather Delay', 'Probability': 0.50, 'TimePenalty': 60, 'HealthPenalty': 4.80},
    ])
    diversion_risk.extend([
        {'Name': 'Cabin Loss', 'Probability': 0.50, 'TimePenalty': 100, 'HealthPenalty': 8.00},
    ])
    print('Game running with emergency data')

def initialize_game():
    global current_health, total_time_minutes, current_location, target_hospital

    get_data_from_database()

    if not airports:
        print('Airport data is empty, cannot start game')
        sys.exit()

    current_health = start_health
    total_time_minutes = 0

    all_icaos = list(airports.keys())

    current_location_icao = random.choice(all_icaos)
    icao_remaining = [icao for icao in all_icaos if icao != current_location_icao]
    target_hospital_icao = random.choice(icao_remaining)

    print(f"------BEGIN LIFE SAVING MISSION------")
    print(f"GOAL: Patient deliver to {airports[target_hospital_icao]['Name']} ")
    print(f"STARTING AT {airports[target_hospital_icao]['Name']}")
    print(f"This patient need you, Every moment matters: You have {maximum_time_minutes} minutes (24 hours) to save the life!")

def display_current_status():
    minutes_remaining = maximum_time_minutes - total_time_minutes

    print("\n||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")
    print(f"📍Current Location: {airports[current_location] ['Name']}")
    print(f"🏥Target Hospital: {airports[target_hospital]['Name']} ")
    print(f"❤️‍🩹 Health: {current_health:.2f} HP & Time Remaining: {minutes_remaining} Minutes ")
    print("||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")

def check_game_over():
    global current_health, total_time_minutes, current_location, target_hospital
    if current_health <= 0:
        print("😭 Mission Over, Despite your efforts We lost the patient. ")
        return True
    elif total_time_minutes >= maximum_time_minutes:
        print("😭 Mission Over, Patient's health dropped to zero. ")
        return True
    elif current_location == target_hospital and current_health > 0:
        print("🏆Mission Success and Life Saved: Patient now is in experts hand")
        return True
    else:
        return False

        









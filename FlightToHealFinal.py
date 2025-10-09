import random
import sys
import mysql.connector

maximum_time_minutes = 1440
start_health = 75.0
healing_time_base = 60

current_health = start_health
total_time_minutes = 0
current_location_icao = None
target_hospital_icao = None

airports = {}
interconnections = []
departure_risks = []
diversion_risks = []

def get_user_response():
    user_input = input("Enter option number/ICAO (or 'H' to heal): ")
    return user_input.strip().upper()


def _load_emergency_data():
    global airports, interconnections, departure_risks, diversion_risks

    print("--- WARNING: Loading EMERGENCY DATA. Database connection failed. ---")

    airports.clear()
    interconnections.clear()
    departure_risks.clear()
    diversion_risks.clear()

    airports.update({
        'OTHH': {'Name': 'Hamad International Airport', 'Continent': 'Asia', 'Country': 'Qatar', 'Clinic': True,
                 'Healing': 25.0, 'TimeFactor': 0.75},
        'EGLL': {'Name': 'London Heathrow Airport', 'Continent': 'Europe', 'Country': 'United Kingdom', 'Clinic': True,
                 'Healing': 20.0, 'TimeFactor': 0.50},
        'KJFK': {'Name': 'John F. Kennedy Airport', 'Continent': 'North America',
                 'Country': 'United States', 'Clinic': False},
        'WSSS': {'Name': 'Singapore Changi Airport', 'Continent': 'Asia', 'Country': 'Singapore', 'Clinic': True,
                 'Healing': 15.0, 'TimeFactor': 0.80},
        'PADD': {'Name': 'Addu International Airport', 'Continent': 'Asia', 'Country': 'Maldives', 'Clinic': False},
    })

    interconnections.extend([
        {'Departure_Airport_ID': 'OTHH', 'Arrival_Airport_ID': 'EGLL', 'Time': 420, 'Health_Cost_Per_Minute': 0.045},
        {'Departure_Airport_ID': 'OTHH', 'Arrival_Airport_ID': 'WSSS', 'Time': 460, 'Health_Cost_Per_Minute': 0.040},
        {'Departure_Airport_ID': 'EGLL', 'Arrival_Airport_ID': 'KJFK', 'Time': 450, 'Health_Cost_Per_Minute': 0.055},
        {'Departure_Airport_ID': 'WSSS', 'Arrival_Airport_ID': 'EGLL', 'Time': 700, 'Health_Cost_Per_Minute': 0.050},
        {'Departure_Airport_ID': 'OTHH', 'Arrival_Airport_ID': 'PADD', 'Time': 240, 'Health_Cost_Per_Minute': 0.035},
        {'Departure_Airport_ID': 'PADD', 'Arrival_Airport_ID': 'OTHH', 'Time': 240, 'Health_Cost_Per_Minute': 0.035},
    ])

    departure_risks.extend([
        {'Name': 'Weather Delay', 'Probability': 0.50, 'TimePenalty': 60, 'HealthPenalty': 4.80},
    ])
    diversion_risks.extend([
        {'Name': 'Cabin Pressure Loss', 'Probability': 0.50, 'TimePenalty': 100, 'HealthPenalty': 8.00},
    ])

    if not airports or not interconnections:
        print("ERROR: Emergency data is also insufficient. Cannot start game.")
        sys.exit()


def load_game_data_from_database():
    global airports, interconnections, departure_risks, diversion_risks

    connection = None
    cursor = None

    airports.clear()
    interconnections.clear()
    departure_risks.clear()
    diversion_risks.clear()

    try:
        connection = mysql.connector.connect(
            host='mysql.metropolia.fi',
            port=3306,
            database='sadhanid',
            user='sadhanid',
            password='123456',
            autocommit=True
        )
        cursor = connection.cursor(dictionary=True)
        print("--- Database connection successful. Loading data... ---")

        airport_sql_query = """
                            SELECT A.ICAO_Code,
                                   A.Airport_Name,
                                   C.Continent_Name,
                                   A.Country_Name,
                                   A.Clinic,
                                   A.Clinic_Healing_Amount,
                                   A.Clinic_Time_Factor
                            FROM Airport AS A
                                     INNER JOIN Continent AS C
                                                ON A.Continent_ID = C.Continent_ID
                            """
        cursor.execute(airport_sql_query)
        for row in cursor.fetchall():
            try:
                icao_code = row['ICAO_Code']
                is_clinic = bool(row.get('Clinic', 0))
                airport_data = {
                    'Name': row['Airport_Name'],
                    'Continent': row.get('Continent_Name', 'Unknown'),
                    'Country': row.get('Country_Name', 'Unknown'),
                    'Clinic': is_clinic,
                }
                if is_clinic:
                    airport_data.update({
                        'Healing': float(row.get('Clinic_Healing_Amount', 0.0)),
                        'TimeFactor': float(row.get('Clinic_Time_Factor', 1.0))
                    })
                airports[icao_code] = airport_data
            except (KeyError, ValueError, TypeError) as errors:
                print(f"Skipping bad airport data row: {errors}")
                pass

        interconnection_sql_query = """
                                    SELECT Departure_Airport_ID,
                                           Arrival_Airport_ID,
                                           Travel_Time_Minutes,
                                           Health_Cost_Per_Minute
                                    FROM Interconnection
                                    """
        cursor.execute(interconnection_sql_query)
        for row in cursor.fetchall():
            try:
                interconnections.append({
                    'Departure_Airport_ID': row['Departure_Airport_ID'],
                    'Arrival_Airport_ID': row['Arrival_Airport_ID'],
                    'Time': int(row['Travel_Time_Minutes']),
                    'Health_Cost_Per_Minute': float(row['Health_Cost_Per_Minute']),
                })
            except (KeyError, ValueError, TypeError):
                pass

        sql_query_departure_risk = "SELECT Departure_Risk_Name, Probability_of_Occurring, Time_Delay_Minutes, Health_Loss FROM Departure_Risk"
        cursor.execute(sql_query_departure_risk)
        for row in cursor.fetchall():
            departure_risks.append({
                'Name': row['Departure_Risk_Name'],
                'Probability': float(row['Probability_of_Occurring']),
                'TimePenalty': int(row['Time_Delay_Minutes']),
                'HealthPenalty': float(row['Health_Loss']),
            })

        sql_query_diversion_risk = "SELECT Diversion_Risk_Name, Probability_of_Occurring, Time_Penalty_Minutes, Health_Loss FROM Diversion_Risk"
        cursor.execute(sql_query_diversion_risk)
        for row in cursor.fetchall():
            diversion_risks.append({
                'Name': row['Diversion_Risk_Name'],
                'Probability': float(row['Probability_of_Occurring']),
                'TimePenalty': int(row['Time_Penalty_Minutes']),
                'HealthPenalty': float(row['Health_Loss']),
            })

    except mysql.connector.Error as errors:
        print(f"--- DATABASE CONNECTION ERROR: {errors}. Loading BACKUP DATA. ---")
        _load_emergency_data()

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def initialize_game():
    global current_health, total_time_minutes, current_location_icao, target_hospital_icao

    load_game_data_from_database()

    if not airports or not interconnections:
        print("ERROR: Insufficient data loaded (0 airports or 0 connections). Ending Session.")
        sys.exit()

    current_health = start_health
    total_time_minutes = 0

    all_icaos = list(airports.keys())

    possible_starts = [icao for icao in all_icaos if
                       any(conn['Departure_Airport_ID'] == icao for conn in interconnections)]

    if not possible_starts:
        print("ERROR: No airports with outgoing flights available. Ending Session.")
        sys.exit()

    current_location_icao = random.choice(possible_starts)

    icao_remaining = [icao for icao in all_icaos if icao != current_location_icao]

    if not icao_remaining:
        print("ERROR: Need at least two unique airport locations. Ending Session.")
        sys.exit()

    target_hospital_icao = random.choice(icao_remaining)

    start_location = airports[current_location_icao]
    target_location = airports[target_hospital_icao]

    print(f"------✈️ MISSION START ({start_health} HP) ------")
    print(f"GOAL: Deliver patient to {target_location['Name']} ({target_hospital_icao}).")
    print(f"STARTING AT: {start_location['Name']} ({current_location_icao}).")


def display_current_status():
    minutes_remaining = maximum_time_minutes - total_time_minutes
    current_location_data = airports[current_location_icao]
    target_location_data = airports[target_hospital_icao]

    print("---------------- CURRENT STATUS -----------------")
    print(f"📍 Location: {current_location_data['Name']} ({current_location_icao})")
    print(f"🏥 Target: {target_location_data['Name']} ({target_hospital_icao})")
    print(f"❤️‍🩹 Health: {current_health:.2f} HP | Time Left: {minutes_remaining} Minutes ")
    print("-------------------------------------------------")


def check_game_over():
    if current_health <= 0:
        print("😭 MISSION OVER, Despite your efforts We lost the patient. (Health dropped to 0).")
        return True
    elif total_time_minutes >= maximum_time_minutes:
        print("😭 MISSION OVER: Time limit exceeded. Ending Session..")
        return True
    elif current_location_icao == target_hospital_icao and current_health > 0:
        print("🏆 MISSION SUCCESS & LIFE SAVED: Patient now is in experts hand!")
        return True
    else:
        return False


def check_risk(risk_list):
    if not risk_list:
        return None
    for risk in risk_list:
        if random.random() < risk['Probability']:
            return risk
    return None


def _print_risk_summary(event_type):
    minutes_remaining = maximum_time_minutes - total_time_minutes
    print(f"[{event_type} Update] Health: {current_health:.2f} HP | Time Left: {minutes_remaining} Minutes")


def _execute_healing():
    global current_health, total_time_minutes
    healing_data = airports[current_location_icao]
    time_cost = healing_time_base * healing_data.get('TimeFactor', 1.0)
    health_gain = healing_data.get('Healing', 0.0)
    total_time_minutes += int(round(time_cost))
    current_health = min(start_health, current_health + health_gain)

    print(f"--- HEALING COMPLETE: Health +{health_gain:.2f} HP. Time Taken: {int(round(time_cost))} min. ---")
    return check_game_over()


def _execute_flight(flight_information):
    global current_health, total_time_minutes, current_location_icao

    time_cost = flight_information['Time']
    health_cost = flight_information['Health_Loss']

    current_health -= health_cost
    total_time_minutes += time_cost

    if check_game_over():
        return True

    current_location_icao = flight_information['Destination_ICAO']
    destination_airport = airports[current_location_icao]

    print(
        f"--- FLIGHT ARRIVAL: Arrived at {destination_airport['Name']} ({current_location_icao}). Health: -{health_cost:.2f} HP. ---")

    return check_game_over()


def _handle_diversion(original_flight):
    global current_location_icao

    print("🫥 DIVERSION NEEDED: Emergency Landing🛬🛬")

    potential_diversions = []

    for connection in interconnections:
        is_departure_valid = connection['Departure_Airport_ID'] == current_location_icao
        is_new_destination = connection['Arrival_Airport_ID'] != original_flight['Destination_ICAO']
        target_icao = connection['Arrival_Airport_ID']

        if is_departure_valid and is_new_destination and target_icao in airports:
            health_cost = connection['Time'] * connection['Health_Cost_Per_Minute']
            potential_diversions.append({
                'icao': target_icao,
                'name': airports[target_icao]['Name'],
                'time': connection['Time'],
                'health_loss': health_cost,
            })

    diversion_options = potential_diversions[:5]
    options_map = {}

    if not diversion_options:
        print("🚨 CRITICAL FAILURE: No safe diversion points available. Proceeding with original flight despite risk.")
        return "CRITICAL_PROCEED"

    print("--- MANDATORY DIVERSION OPTIONS (Choose by Option Number) ---")

    for idx, option in enumerate(diversion_options, 1):
        option_id = str(idx)
        print(
            f"  [{option_id}]: {option['name']} ({option['icao']}) | Time: {option['time']} min | Loss: {option['health_loss']:.2f} HP")
        options_map[option_id] = option

    print("---------------------------------------------------------")

    while True:
        response = input("Enter option number for diversion: ")

        if response in options_map:
            chosen_diversion = options_map[response]

            original_flight['Destination_ICAO'] = chosen_diversion['icao']
            original_flight['Time'] = chosen_diversion['time']
            original_flight['Health_Loss'] = chosen_diversion['health_loss']

            print(f"☑️ DIVERSION APPLIED: New destination is {chosen_diversion['name']} ({chosen_diversion['icao']}).")
            return "SUCCESS"
        else:
            print(f"👎Invalid choice. You must enter one of the listed option numbers: {list(options_map.keys())}")


def apply_risk_check(flight_info):
    global current_health, total_time_minutes

    departure_risk = check_risk(departure_risks)
    if departure_risk:
        total_time_minutes += departure_risk['TimePenalty']
        current_health -= departure_risk['HealthPenalty']
        print(f"🫥 DEPARTURE DELAY: {departure_risk['Name']}. Penalty applied.")
        _print_risk_summary("Delay")

        if check_game_over():
            return True

        while True:
            # Direct input() call for confirmation
            choice = input("Proceed (P) or Cancel (C)? ").strip().upper()
            if choice == 'C':
                return "CANCELLED"
            elif choice == 'P':
                break
            else:
                print("👎 Invalid input. Enter 'P' or 'C'.")

    if check_game_over():
        return True

    diversion_risk = check_risk(diversion_risks)
    if diversion_risk:
        total_time_minutes += diversion_risk['TimePenalty']
        current_health -= diversion_risk['HealthPenalty']
        print(f" IN-FLIGHT EMERGENCY: {diversion_risk['Name']}! Penalty Applied.")
        _print_risk_summary("Emergency")

        if check_game_over():
            return True

        diversion_result = _handle_diversion(flight_info)

        if diversion_result == "CANCELLED":
            return "CANCELLED"

    return False

def handle_player_turn():
    available_flights = []
    flight_id = 1
    for connection in interconnections:
        if connection['Departure_Airport_ID'] == current_location_icao:
            health_cost = connection['Time'] * connection['Health_Cost_Per_Minute']
            available_flights.append({
                'ID': flight_id, 'Destination_ICAO': connection['Arrival_Airport_ID'],
                'Time': connection['Time'], 'Health_Loss': health_cost,
            })
            flight_id += 1

    print("--- AVAILABLE OPTIONS ---")

    for flight in available_flights:
        dest_airport = airports.get(flight['Destination_ICAO'])
        dest_name = dest_airport['Name'] if dest_airport else "Unknown Airport"
        print(f"  [{flight['ID']}] Fly to {dest_name} (Time: {flight['Time']} minutes) (Loss: {flight['Health_Loss']:.2f} HP)")
    if airports[current_location_icao].get('Clinic', False):
        print("  [H] Stabilize Patient at Clinic")
    if not available_flights and not airports[current_location_icao].get('Clinic', False):
        print("🚫 No routes or healing options available from this location. You must manually quit.")

    while True:
        action = get_user_response()
        if action == 'H':
            if airports[current_location_icao].get('Clinic', False):
                return _execute_healing()
            else:
                print("🚫 No clinic here. Cannot heal.")
                continue

        try:
            choice_id = int(action)
            chosen_flight = next((f for f in available_flights if f['ID'] == choice_id), None)
            if chosen_flight:
                flight_to_execute = chosen_flight.copy()
                risk_result = apply_risk_check(flight_to_execute)
                if risk_result is True:
                    return True
                if risk_result == "CANCELLED":
                    print("Flight cancelled or diversion failed. Choose a new action.")
                    return False
                return _execute_flight(flight_to_execute)
            else:
                print("🚫 Invalid flight number.")
        except ValueError:
            print("🚫 Invalid input. Please enter a number (1, 2...) or 'H'.")
    return False


def run_game():
    initialize_game()

    while not check_game_over():
        display_current_status()
        if handle_player_turn():
            break
    print("--- END OF MISSION REPORT ---")


if __name__ == "__main__":
    try:
        while True:
            run_game()
            play_again = input("Do you want to play another mission? (yes/no): ").strip().upper()
            if play_again != 'YES':
                print("🙏 THANK YOU FOR YOUR HARD EFFORT TO SAVE OUR PATIENT, WE REALLY APPRECIATE IT!")
                break
    except KeyboardInterrupt:
        pass
    except Exception as final_exception:
        print(f"An unexpected error occurred: {final_exception}")


import random
import sys
import mysql.connector

maximum_time_minutes = 1440
start_health = 75.0
healing_time_factor = 60

current_health = start_health
total_time_minutes = 0
current_location = None
target_hospital = None

airports = {}
countries = {}
continents = {}
interconnections = []
departure_risks = []
diversion_risks = []

def load_emergency_data():
    global airports, interconnections, departure_risk, diversion_risk

    airports = {}
    interconnections = []
    departure_risks = []
    diversion_risks = []

    airports.update({
        'OTHH': {'Name': 'Hamad International Airport', 'Continent': 'Asia', 'Country': 'Qatar', 'Clinic': True, 'Healing': 25.0, 'TimeFactor': 0.75},
        'EGLL': {'Name': 'London Heathrow Airport', 'Continent': 'Europe', 'Country': 'United Kingdom', 'Clinic': True, 'Healing': 20.0, 'TimeFactor': 0.50},
        'KJFK': {'Name': 'John F. Kennedy International Airport', 'Continent': 'North America', 'Country': 'United States', 'Clinic': False},
        'WSSS': {'Name': 'Singapore Changi Airport', 'Continent': 'Asia', 'Country': 'Singapore', 'Clinic': True, 'Healing': 15.0, 'TimeFactor': 0.80},
    })
    interconnections.extend([
        {'Departure_Airport_ID': 'OTHH', 'Arrival_Airport_ID': 'EGLL', 'Time': 420, 'Health_Cost_Per_Minute': 0.045},
        {'Departure_Airport_ID': 'EGLL', 'Arrival_Airport_ID': 'OTHH', 'Time': 400, 'Health_Cost_Per_Minute': 0.050},
        {'Departure_Airport_ID': 'OTHH', 'Arrival_Airport_ID': 'KJFK', 'Time': 800, 'Health_Cost_Per_Minute': 0.035},
        {'Departure_Airport_ID': 'EGLL', 'Arrival_Airport_ID': 'KJFK', 'Time': 400, 'Health_Cost_Per_Minute': 0.040},
        {'Departure_Airport_ID': 'OTHH', 'Arrival_Airport_ID': 'WSSS', 'Time': 450, 'Health_Cost_Per_Minute': 0.030},
    ])
    departure_risks.extend([
        {'Name': 'Weather Delay', 'Probability': 0.50, 'TimePenalty': 60, 'HealthPenalty': 4.80},
    ])
    diversion_risks.extend([
        {'Name': 'Cabin Loss', 'Probability': 0.50, 'TimePenalty': 100, 'HealthPenalty': 8.00},
    ])
    print('Game running with emergency data')

def load_emergency_data_from_database():
    global airports, countries, continents, interconnections, departure_risks, diversion_risks

connection = None
cursor = None

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
        #print("Connected to phpMyAdmin database.")

        continent_query = "SELECT Continent_ID, Continent_Name FROM Continent"
        cursor.execute(continent_query)

        airport_sql_query = """
                            SELECT ICAO_Code, 
                                   Airport_Name,
                                   Continent_ID,
                                   Country_Name,
                                   Risk_Factor_ID,
                                   Clinic,
                                   Clinic_Healing_Amount,
                                   Clinic_Time_Factor
                            FROM Airport table 
                            """
        cursor.execute(airport_sql_query)
        for row in cursor.fetchall():
            try:
                icao_code = row['ICAO_Code']
                is_clinic = bool(row['Clinic'])

                clini_details = {}
                if is_clinic:
                    clinic_details = {
                        'Healing': float(row['Clinic_Healing_Amount']),
                        'Time': float(row['Clinic_Time_Factor'])
                    }
                airports[icao_code] = {
                    'Name': row['Airport_Name'],
                    'Continent': continent_lookup.get(row['Continent_ID'], 'Unkonwn'),
                    'Country': country_lookup.get(row['Country_Name'], 'Unkonwn'),
                    'Clinic': is_clinic,
                }
            except (KeyError, ValueError, TypeError) as errors:
                print(f"Skipped an Invalid Airport Row: {row.get('ICAO_Code', 'Unknown ICAO Code')} Error: {errors}")
        print(f"Loaded {len(airports)} Airports.")

        interconnection_sql_query = """
                                    SELECT Departure_Airport_ID, Arrival_Airport_ID, 
                                           Travel_Time_Minutes, Health_Cost_Per_Minutes, 
                                    FROM Interconnection table 
                                    """
        cursor.execute(interconnection_sql_query)
        for row in cursor.fetchall():
            try:
                interconnections.append({
                    'Departure_Airport_ID': row['Departure_Airport_ID'],
                    'Arrival_Airport_ID': row['Arrival_Airport_ID'],
                    'Time_Minutes': int(row['Travel_Time_Minutes']),
                    'Health_Cost_Per_Minutes' : float(row['Health_Cost_Per_Minutes']),
                })
            except (KeyError, ValueError, TypeError) as errors:
                print(f"Skipped an Invalid Interconnection Row. Error: {errors} ")
        print(f"Loaded {len(interconnections)} Routes.")

        sql_query_departure_risk = """
                               SELECT Departure_Risk_ID,
                                      Departure_Risk_Name,
                                      Probability_of_Occurring,
                                      Time_Delay_Minutes,
                                      Health_Loss,
                               FROM Departure_Risk table
                               """
        cursor.execute(sql_query_departure_risk)
        for row in cursor.fetchall():
            try:
                departure_risk.append({
                    'Name': row['Departure_Risk_Name'],
                    'Probability_of_Occurring': float(row['Probability_of_Occurring']),
                    'Time_Delay_Minutes': int(row['Time_Delay_Minutes']),
                    'Health_Loss': float(row['Health_Loss']),
                })
            except (KeyError, ValueError, TypeError) as errors:
                print(f"Skipped an Invalid Departure Risk Row. Error: {errors} ")
        print(f"Loaded {len(departure_risk)} Departure Risks.")

        sql_query_diversion_risk = """
                               SELECT Diversion_Risk_ID,
                                      Diversion_Risk_Name,
                                      Probability_of_Occurring,
                                      Time_Penalty_Minutes,
                                      Health_Loss,
                               FROM Diversion_Risk table
                               """
        cursor.execute(sql_query_diversion_risk)
        for row in cursor.fetchall():
            try:
                diversion_risk.append({
                    'Name': row['Diversion_Risk_Name'],
                    'Probability_of_Occurring': float(row['Probability_of_Occurring']),
                    'Time_Delay_Minutes': int(row['Time_Penalty_Minutes']),
                    'Health_Loss': float(row['Health_Loss']),
                })
            except (KeyError, ValueError, TypeError) as errors:
                print(f"Skipped an Invalid Diversion Risk Row. Error: {errors} ")
        print(f"Loaded {len(departure_risk)} Diversion Risks.")

        except mysql.connector.Error as errors:(
            print("Failed to fetch data from MySQL Database"))
        print(f"Error Details: {errors}")
        print("Loading Emergency Da ta to Continue the Game.")
        load_emergency_data()

        finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected()
            connection.close()
        print(f"Successfully closed MySQL connection.")



def initialize_game():
    global current_health, total_time_minutes, current_location, target_hospital

    load_emergency_data_from_database()

    if not airports:
        print('Airport data is empty, cannot start game')
        sys.exit()

    current_health = start_health
    total_time_minutes = 0

    all_icaos = list(airports.keys())

    current_location_icao = random.choice(all_icaos)
    icao_remaining = [icao for icao in all_icaos if icao != current_location_icao]
    target_hospital_icao = random.choice(icao_remaining)

    start_location = airports[current_location_icao]
    target_location = airports[target_hospital_icao]

    print(f"------BEGIN LIFE SAVING MISSION------")
    print(f"GOAL: Patient deliver to {[target_location]['Name']} ([target_hospital icao]) ")
    print(f"STARTING AT: {start_location['Name']} {current_location_icao}")
    print(f"This patient need you, Every moment matters: You have {maximum_time_minutes} minutes (24 hours) to save the life!")


def display_current_status():
    minutes_remaining = maximum_time_minutes - total_time_minutes

    current_location = airports[current_location_icao]
    target_location = airports[target_hospital_icao]

    print("\n||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")
    print(f"📍Current Location: {current_location['Name']} ({current_location_icao}) ")
    print(f"🏥Target Hospital: {target_location['Name']} ([target_hospital_icao]) ")
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

def display_flight_options():
    available_flights = []
    flight_id = 1

    for connection in interconnections:
        if connection['Departure_Airport_ID'] == current_location:
            time = connection['Time']
            health_cost_per_minute = connection['Health_Cost_Per_Minute']
            health_cost = time * health_cost_per_minute
            available_flights.append({
                'ID': flight_id,
                'Destination_ICAO': connection['Arrival_Airport_ID'],
                'Time': time,
                'Health_Loss': health_cost,
            })
            flight_id += 1

    return available_flights

def execute_healing():
    global current_health, total_time_minutes, current_location, target_hospital

    healing_data = airports[current_location]

    time_cost = healing_time_base * healing_data.get('TimeFactor', 1.0)
    health_gain = healing_data.get('HealthGain', 0.0)

    total_time_minutes += int(round(time_cost))

    new_health = current_health + health_gain
    current_health = min(start_health, new_health)
    print(f"Patient's Condition Improved. Health Increased by: {health_gain:.2f} HP.")
    print(f"Time Taken: {int(round(time_cost))} Minutes.")

    return check_game_over()

def execute_flight(flight_information):
    global current_health, total_time_minutes, current_location, target_hospital

    time_cost = flight_information['Time']
    health_cost = flight_information['Health_Loss']

    destination_airport = airports[flight_information['Destination_ICAO']]

    total_time_minutes += time_cost
    current_health -= health_cost

    print(f"Fight Completed. Your Flight Has Arrived At {destination_airport['Name']} ({flight_information}['Destination_ICAO']} - {destination_airport['Country']}.")
    print(f"Time Taken: {time_cost} Minutes. Health Loss: {health_cost:.2f} HP.")
    current_location = airports[flight_information['Destination_ICAO']]
    return check_game_over()

def _check_risk(risk_list):
    if not risk_list:
        return None

    for risk in risk_list:
        if random.random() < risk['Probability']:
            return risk

    return None


def _handle_diversion(original_flight):
    global current_location_icao, target_hospital_icao

    potential_diversions = []

    for connection in interconnections:
        if connection['Departure_Airport_ID'] == current_location_icao:
            dest_icao = connection['Arrival_Airport_ID']

            is_excluded = (dest_icao == original_flight['Dest_ICAO'] or
                            dest_icao == current_location_icao or
                            dest_icao == target_hospital_icao)

            if not is_excluded and dest_icao in airports:
                time = connection['Time']
                health_cost = time * connection['Health_Cost_Per_Minute']
                dest_airport_data = airports[dest_icao]

                potential_diversions.append({
                    'ICAO': dest_icao,
                    'Name': dest_airport_data['Name'],
                    'Country': dest_airport_data['Country'],
                    'Time': time,
                    'Health_Loss': health_cost,
                })

    if not potential_diversions:
        print("🚨 CRITICAL FAILURE: No safe diversion points available. Forcing return to origin.")
        return current_location_icao

    random.shuffle(potential_diversions)
    strategic_options = potential_diversions[:3]


    print("--- DIVERSION ALERT ---")
    original_dest = airports[original_flight['Dest_ICAO']]
    print(f"The aircraft cannot proceed to {original_dest['Name']} ({original_flight['Dest_ICAO']}) - {original_dest['Country']}.")
    print("Select an alternative diversion airport immediately.")

    icao_to_option_map = {}

    print("\n--- Available Diversion Options ---")
    for option in strategic_options:
        icao_code = option['ICAO']
        print(f"  [{icao_code}] {option['Name']} - {option['Country']} | Added Time: {option['Time']} min | Added Health Loss: {option['Health_Loss']:.2f} HP")
        icao_to_option_map[icao_code] = option
    print("-----------------------------------")

    while True:
        action = input("Enter the ICAO code for your chosen diversion airport: ").strip().upper()

        if action in icao_to_option_map:
            chosen_diversion = icao_to_option_map[action]
            chosen_airport = airports[chosen_diversion['ICAO']]
            print(f"🔄 Diverting to {chosen_airport['Name']} ({chosen_diversion['ICAO']}) - {chosen_airport['Country']}.")

            original_flight['Dest_ICAO'] = chosen_diversion['ICAO']
            original_flight['Time'] = chosen_diversion['Time']
            original_flight['Health_Loss'] = chosen_diversion['Health_Loss']

            return chosen_diversion['ICAO']
        else:
            if action in airports:
                print(f"❌ '{action}' is a known airport but not one of the designated diversion options.")
            else:
                print(f"❌ Invalid ICAO code entered. Please choose one of the options above.")


def apply_risk_check(flight_info):
    global current_health, total_time_minutes

    departure_risk = _check_risk(departure_risks)
    if departure_risk:
        print(f"\n⚠️ DEPARTURE DELAY: {departure_risk['Name']}!")

        total_time_minutes += departure_risk['TimePenalty']
        current_health -= departure_risk['HealthPenalty']

        print(
            f"Penalty applied: Time Loss: {departure_risk['TimePenalty']} min, Health Loss: {departure_risk['HealthPenalty']:.2f} HP.")

        if check_game_end():
            return True

        while True:
            choice = input("Proceed with flight (P) or Cancel mission (C)? ").strip().upper()
            if choice == 'C':
                print("🛑 Flight cancelled. You have returned to the action phase.")
                return "CANCELLED"
            elif choice == 'P':
                break
            else:
                print("❌ Invalid input. Enter 'P' to proceed or 'C' to cancel.")

    diversion_risk = _check_risk(diversion_risks)
    if diversion_risk:
        print(f"\n🚨 IN-FLIGHT EMERGENCY: {diversion_risk['Name']}!")

        total_time_minutes += diversion_risk['TimePenalty']
        current_health -= diversion_risk['HealthPenalty']

        print(
            f"Penalty applied: Time Loss: {diversion_risk['TimePenalty']} min, Health Loss: {diversion_risk['HealthPenalty']:.2f} HP.")

        if check_game_end():
            return True

        _handle_diversion(flight_info)

    return False


def handle_player_turn():
    available_flights = _get_available_flights()

    print("\n--- NEXT MOVE ---")

    for flight in available_flights:
        dest_airport = airports[flight['Dest_ICAO']]
        dest_display = f"{dest_airport['Name']} - {dest_airport['Country']}"
        print(
            f"  [{flight['ID']}] Fly to {dest_display} ({flight['Dest_ICAO']}) (Time: {flight['Time']} min | Health Loss: {flight['Health_Loss']:.2f} HP)")

    clinic_available = airports[current_location_icao].get('Clinic', False)
    if clinic_available:
        healing_data = airports[current_location_icao]
        time_cost = HEALING_TIME_BASE * healing_data.get('TimeFactor', 1.0)
        health_gain = healing_data.get('Healing', 0.0)
        print(f"  [H] Stabilize Patient at Clinic (Gain: {health_gain:.2f} HP | Cost: {int(round(time_cost))} min)")

    print("-" * 15)

    while True:
        action = input("Enter option number (or 'H' to heal): ").strip().upper()

        if action == 'H':
            if clinic_available:
                return _execute_healing()
            else:
                print("❌ No clinic available at this airport. Choose a flight or a different option.")
                continue

        try:
            choice_id = int(action)
            chosen_flight = next((f for f in available_flights if f['ID'] == choice_id), None)

            if chosen_flight:
                risk_result = apply_risk_check(chosen_flight)

                if risk_result is True:
                    return True

                if risk_result == "CANCELLED":
                    return False

                return _execute_flight(chosen_flight)
            else:
                print("❌ Invalid flight option number.")
        except ValueError:
            print("❌ Invalid input. Please enter a number for a flight or 'H' to heal.")



def run_game():
    initialize_game()

    while not check_game_end():
        display_status()
        if handle_player_turn():
            break

    print("\n--- END OF MISSION REPORT ---")


if __name__ == "__main__":
    try:
        while True:
            run_game()

            play_again = input("\ndo you want to play another mission? (yes/no): ").strip().lower()

            if play_again != 'yes':
                print("Thank you for playing Flight to Heal!")
                break
    except KeyboardInterrupt:
        print("\n\nGame interrupted. Goodbye!")
    except Exception as final_e:
        print("\n\n--- UNEXPECTED FATAL ERROR ---")
        print("The game encountered an unexpected error and must close.")
















import random
import sys
import mysql.connector

maximum_time_minutes = 1440
start_health = 75.0
HEALING_TIME_BASE = 60

current_health = start_health
total_time_minutes = 0
current_location_icao = None
target_hospital_icao = None

airports = {}
countries = {}
continents = {}
interconnections = []
departure_risks = []
diversion_risks = []


def _load_default_interconnections():
    """Helper function to load only the hardcoded flight connections (including WSSS outgoing)."""
    global interconnections
    interconnections.extend([
        {'Departure_Airport_ID': 'OTHH', 'Arrival_Airport_ID': 'EGLL', 'Time': 420, 'Health_Cost_Per_Minute': 0.045},
        {'Departure_Airport_ID': 'EGLL', 'Arrival_Airport_ID': 'OTHH', 'Time': 400, 'Health_Cost_Per_Minute': 0.050},
        {'Departure_Airport_ID': 'OTHH', 'Arrival_Airport_ID': 'KJFK', 'Time': 800, 'Health_Cost_Per_Minute': 0.035},
        {'Departure_Airport_ID': 'EGLL', 'Arrival_Airport_ID': 'KJFK', 'Time': 400, 'Health_Cost_Per_Minute': 0.040},
        {'Departure_Airport_ID': 'OTHH', 'Arrival_Airport_ID': 'WSSS', 'Time': 450, 'Health_Cost_Per_Minute': 0.030},
        # GUARANTEED OUTGOING FLIGHT FROM WSSS
        {'Departure_Airport_ID': 'WSSS', 'Arrival_Airport_ID': 'EGLL', 'Time': 700, 'Health_Cost_Per_Minute': 0.050},
    ])


def load_emergency_data():
    """Loads all hardcoded fallback data."""
    global airports, interconnections, departure_risks, diversion_risks

    print("--- DIAGNOSTIC: Loading FULL HARDCODED FALLBACK DATA. DB connection failed. ---")

    # Clear existing data before loading fallback
    airports.clear()
    interconnections.clear()
    departure_risks.clear()
    diversion_risks.clear()

    # Default Airport Data
    airports.update({
        'OTHH': {'Name': 'Hamad International Airport', 'Continent': 'Asia', 'Country': 'Qatar', 'Clinic': True,
                 'Healing': 25.0, 'TimeFactor': 0.75},
        'EGLL': {'Name': 'London Heathrow Airport', 'Continent': 'Europe', 'Country': 'United Kingdom', 'Clinic': True,
                 'Healing': 20.0, 'TimeFactor': 0.50},
        'KJFK': {'Name': 'John F. Kennedy International Airport', 'Continent': 'North America',
                 'Country': 'United States', 'Clinic': False},
        'WSSS': {'Name': 'Singapore Changi Airport', 'Continent': 'Asia', 'Country': 'Singapore', 'Clinic': True,
                 'Healing': 15.0, 'TimeFactor': 0.80},
    })

    # Default Interconnection Data (now includes WSSS -> EGLL)
    _load_default_interconnections()

    # Default Risk Data
    departure_risks.extend([
        {'Name': 'Weather Delay', 'Probability': 0.50, 'TimePenalty': 60, 'HealthPenalty': 4.80},
    ])
    diversion_risks.extend([
        {'Name': 'Cabin Loss', 'Probability': 0.50, 'TimePenalty': 100, 'HealthPenalty': 8.00},
    ])


def load_data_from_database():
    global airports, countries, continents, interconnections, departure_risks, diversion_risks

    connection = None
    cursor = None

    # Clear lists/dicts before attempting load
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
        print("--- DIAGNOSTIC: Database connection successful, attempting to fetch data... ---")

        # ----------------------------------------------------
        # 1. Fetch Airport Data using INNER JOIN
        # ----------------------------------------------------
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
                is_clinic = bool(row['Clinic'])

                airport_data = {
                    'Name': row['Airport_Name'],
                    'Continent': row.get('Continent_Name', 'Unknown'),
                    'Country': row.get('Country_Name', 'Unknown'),
                    'Clinic': is_clinic,
                }

                if is_clinic:
                    airport_data.update({
                        'Healing': float(row['Clinic_Healing_Amount']),
                        'TimeFactor': float(row['Clinic_Time_Factor'])
                    })

                airports[icao_code] = airport_data

            except (KeyError, ValueError, TypeError) as errors:
                pass

        # ----------------------------------------------------
        # 2. Fetch Interconnection Data
        # ----------------------------------------------------
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
            except (KeyError, ValueError, TypeError) as errors:
                pass

        # FIX: If DB connections were empty, load the hardcoded flights to ensure playability.
        if not interconnections:
            print(
                "--- DIAGNOSTIC: DB query successful, but 'Interconnection' table returned NO rows. Loading hardcoded flight routes. ---")
            _load_default_interconnections()
        else:
            print(f"--- DIAGNOSTIC: Loaded {len(interconnections)} flights from the database. ---")

        # ----------------------------------------------------
        # 3. Fetch Departure Risk Data
        # ----------------------------------------------------
        sql_query_departure_risk = """
                                   SELECT Departure_Risk_Name,
                                          Probability_of_Occurring,
                                          Time_Delay_Minutes,
                                          Health_Loss
                                   FROM Departure_Risk \
                                   """
        cursor.execute(sql_query_departure_risk)
        for row in cursor.fetchall():
            try:
                departure_risks.append({
                    'Name': row['Departure_Risk_Name'],
                    'Probability': float(row['Probability_of_Occurring']),
                    'TimePenalty': int(row['Time_Delay_Minutes']),
                    'HealthPenalty': float(row['Health_Loss']),
                })
            except (KeyError, ValueError, TypeError) as errors:
                pass

        # ----------------------------------------------------
        # 4. Fetch Diversion Risk Data
        # ----------------------------------------------------
        sql_query_diversion_risk = """
                                   SELECT Diversion_Risk_Name,
                                          Probability_of_Occurring,
                                          Time_Penalty_Minutes,
                                          Health_Loss
                                   FROM Diversion_Risk \
                                   """
        cursor.execute(sql_query_diversion_risk)
        for row in cursor.fetchall():
            try:
                diversion_risks.append({
                    'Name': row['Diversion_Risk_Name'],
                    'Probability': float(row['Probability_of_Occurring']),
                    'TimePenalty': int(row['Time_Penalty_Minutes']),
                    'HealthPenalty': float(row['Health_Loss']),
                })
            except (KeyError, ValueError, TypeError) as errors:
                pass

    except mysql.connector.Error as errors:
        # If database connection fails entirely, load all default hardcoded data
        print(f"--- DIAGNOSTIC: FATAL DATABASE CONNECTION ERROR ({errors}). Loading ALL hardcoded fallback data. ---")
        load_emergency_data()

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def initialize_game():
    global current_health, total_time_minutes, current_location_icao, target_hospital_icao

    load_emergency_data_from_database()

    if not airports:
        # Exit if no airport data could be loaded (neither from DB nor fallback)
        print("FATAL ERROR: Could not load any airport data. Exiting.")
        sys.exit()

    current_health = start_health
    total_time_minutes = 0

    all_icaos = list(airports.keys())

    # STARTING AT WSSS if available
    if 'WSSS' in airports:
        current_location_icao = 'WSSS'
    else:
        current_location_icao = random.choice(all_icaos)

    icao_remaining = [icao for icao in all_icaos if icao != current_location_icao]

    if not icao_remaining:
        print("FATAL ERROR: Only one airport loaded. Cannot set a target hospital. Exiting.")
        sys.exit()

    target_hospital_icao = random.choice(icao_remaining)

    start_location = airports[current_location_icao]
    target_location = airports[target_hospital_icao]

    print(f"\n------ BEGIN LIFE SAVING MISSION ({start_health} HP) ------")
    print(
        f"GOAL: Deliver patient to {target_location['Name']} ({target_hospital_icao}) in {target_location['Country']}.")
    print(f"STARTING AT: {start_location['Name']} ({current_location_icao}) in {start_location['Country']}.")
    print(f"Every moment matters: You have {maximum_time_minutes} minutes (24 hours) to save the life!")


def display_current_status():
    minutes_remaining = maximum_time_minutes - total_time_minutes

    current_location_data = airports[current_location_icao]
    target_location_data = airports[target_hospital_icao]

    current_location_display = f"{current_location_data['Name']} ({current_location_icao}) in {current_location_data['Country']}"
    target_hospital_display = f"{target_location_data['Name']} ({target_hospital_icao}) in {target_location_data['Country']}"

    print("\n||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")
    print(f"📍Current Location: {current_location_display} ")
    print(f"🏥Target Hospital: {target_hospital_display} ")
    print(f"❤️‍🩹 Health: {current_health:.2f} HP | Time Remaining: {minutes_remaining} Minutes ")
    print("||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")


def check_game_over():
    global current_health, total_time_minutes, current_location_icao, target_hospital_icao

    if current_health <= 0:
        print("\n😭 MISSION FAILED: Despite your efforts, we lost the patient (Health dropped to 0).")
        return True
    elif total_time_minutes >= maximum_time_minutes:
        print("\n😭 MISSION FAILED: Time limit exceeded. We lost the patient.")
        return True
    elif current_location_icao == target_hospital_icao and current_health > 0:
        print("\n🏆 MISSION SUCCESS: Patient now in expert hands!")
        return True
    else:
        return False


def _get_available_flights():
    available_flights = []
    flight_id = 1

    # Check the global interconnections list for flights departing from the current location
    for connection in interconnections:
        if connection['Departure_Airport_ID'] == current_location_icao:
            time = connection['Time']
            health_cost_per_minute = connection['Health_Cost_Per_Minute']
            health_cost = time * health_cost_per_minute
            available_flights.append({
                'ID': flight_id,
                'Dest_ICAO': connection['Arrival_Airport_ID'],
                'Time': time,
                'Health_Loss': health_cost,
            })
            flight_id += 1
    return available_flights


def _execute_healing():
    global current_health, total_time_minutes, current_location_icao

    healing_data = airports[current_location_icao]

    time_cost = HEALING_TIME_BASE * healing_data.get('TimeFactor', 1.0)
    health_gain = healing_data.get('Healing', 0.0)

    total_time_minutes += int(round(time_cost))

    new_health = current_health + health_gain
    current_health = min(start_health, new_health)

    print(f"\n--- HEALING COMPLETE ---")
    print(f"Patient's condition improved. Health Increased by: {health_gain:.2f} HP.")
    print(f"Time Taken: {int(round(time_cost))} Minutes.")
    print("------------------------")

    return check_game_over()


def _execute_flight(flight_information):
    global current_health, total_time_minutes, current_location_icao

    time_cost = flight_information['Time']
    health_cost = flight_information['Health_Loss']

    current_health -= health_cost
    total_time_minutes += time_cost

    if check_game_over():
        return True

    destination_airport = airports[flight_information['Dest_ICAO']]
    current_location_icao = flight_information['Dest_ICAO']

    print(f"\n--- FLIGHT ARRIVAL ---")
    print(
        f"Flight Completed. Arrived at {destination_airport['Name']} ({current_location_icao}) - {destination_airport['Country']}.")
    print(f"Time Taken: {time_cost} Minutes. Health Loss: {health_cost:.2f} HP.")
    print("----------------------")

    return check_game_over()


def _check_risk(risk_list):
    if not risk_list:
        return None

    for risk in risk_list:
        if random.random() < risk['Probability']:
            return risk
    return None


def _print_risk_summary(event_type):
    """Prints a quick summary of the patient's status after a risk event."""
    minutes_remaining = maximum_time_minutes - total_time_minutes
    print(f"    [{event_type} Update] Health: {current_health:.2f} HP | Time Remaining: {minutes_remaining} Minutes")


def _handle_diversion(original_flight):
    global current_location_icao, target_hospital_icao

    potential_diversions = []

    for connection in interconnections:
        if connection['Departure_Airport_ID'] == current_location_icao:
            dest_icao = connection['Arrival_Airport_ID']

            is_excluded = (dest_icao == original_flight['Dest_ICAO'] or
                           dest_icao == current_location_icao)

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
        # If no diversion options, force return to the current location (no change to location_icao)
        return current_location_icao

    random.shuffle(potential_diversions)
    strategic_options = potential_diversions[:3]

    print("\n--- DIVERSION ALERT ---")
    original_dest = airports[original_flight['Dest_ICAO']]
    print(
        f"The aircraft cannot proceed to {original_dest['Name']} ({original_flight['Dest_ICAO']}) - {original_dest['Country']}.")
    print("Select an alternative diversion airport immediately.")

    icao_to_option_map = {}

    print("\n--- Available Diversion Options (New Route from Origin) ---")
    for option in strategic_options:
        icao_code = option['ICAO']
        print(
            f"  [{icao_code}] {option['Name']} - {option['Country']} | Travel Time: {option['Time']} min | Health Loss: {option['Health_Loss']:.2f} HP")
        icao_to_option_map[icao_code] = option
    print("-----------------------------------")

    while True:
        action = input("Enter the ICAO code for your chosen diversion airport: ").strip().upper()

        if action in icao_to_option_map:
            chosen_diversion = icao_to_option_map[action]
            chosen_airport = airports[chosen_diversion['ICAO']]
            print(
                f"🔄 Diverting to {chosen_airport['Name']} ({chosen_diversion['ICAA']}) - {chosen_airport['Country']}.")

            # Update the flight info to the chosen diversion destination
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

        # ADDED STATUS UPDATE FOR DEPARTURE DELAY
        _print_risk_summary("Delay")
        # ---------------------------------------------

        if check_game_over():
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

        # ADDED STATUS UPDATE FOR DIVERSION/IN-FLIGHT EMERGENCY
        _print_risk_summary("Emergency")
        # -----------------------------------------------------------

        if check_game_over():
            return True

        # Handle the diversion logic which will modify chosen_flight in place
        _handle_diversion(flight_info)

    return False


def handle_player_turn():
    available_flights = _get_available_flights()

    print("\n--- NEXT MOVE ---")
    print(f"Current Location: {airports[current_location_icao]['Name']}")

    if available_flights:
        for flight in available_flights:
            dest_airport = airports.get(flight['Dest_ICAO'], {'Name': 'Unknown', 'Country': 'Unknown'})
            dest_display = f"{dest_airport['Name']} - {dest_airport['Country']}"
            print(
                f"  [{flight['ID']}] Fly to {dest_display} ({flight['Dest_ICAO']}) (Time: {flight['Time']} min | Health Loss: {flight['Health_Loss']:.2f} HP)")

    clinic_available = airports[current_location_icao].get('Clinic', False)
    if clinic_available:
        healing_data = airports[current_location_icao]
        time_cost = HEALING_TIME_BASE * healing_data.get('TimeFactor', 1.0)
        health_gain = healing_data.get('Healing', 0.0)
        print(f"  [H] Stabilize Patient at Clinic (Gain: {health_gain:.2f} HP | Cost: {int(round(time_cost))} min)")

    if not available_flights and not clinic_available:
        print("  [!] WARNING: No flights or clinics available at this location. Only option is to quit.")

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

    while not check_game_over():
        display_current_status()
        if handle_player_turn():
            break

    print("\n--- END OF MISSION REPORT ---")


if __name__ == "__main__":
    try:
        while True:
            run_game()

            play_again = input("\nDo you want to play another mission? (yes/no): ").strip().lower()

            if play_again != 'yes':
                break
    except KeyboardInterrupt:
        pass
    except Exception as final_e:
        print(f"An unexpected error occurred: {final_e}")

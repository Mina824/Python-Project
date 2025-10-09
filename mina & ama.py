def handle_healing():

    global current_health, total_time_minutes, current_location

    airport = airports[current_location]

    if not airport['Clinic']:
        print("❌ No clinic available at this airport.")
        return

    healing_amount = airport.get('Healing Amount', 0.0)
    time_factor = airport.get('Time_Factor', 1.0)

    time_cost = healing_time_factor * time_factor
    total_time_minutes += time_cost

    before_health = current_health
    current_health = min(75.0, current_health + healing_amount)

    print(f"🩺 Healing at {airport['Name']}...")
    print(f"⏳ Time Spent: {time_cost} minutes")
    print(f"❤️ Health Restored: {current_health - before_health:.2f} HP (Current: {current_health:.2f})")


def execute_flight(flight):

    global current_health, total_time_minutes, current_location

    flight_time = flight['Time_Minutes']
    health_loss = flight_time * health_cost_per_minute

    total_time_minutes += flight_time
    current_health -= health_loss
    current_location = flight['Arrival_Airport_ID']

    print(f"✈️ Flying from {flight['Departure_Airport_ID']} to {flight['Arrival_Airport_ID']}...")
    print(f"⏳ Flight Time: {flight_time} minutes | ❤️ Health Loss: {health_loss:.2f} HP")
    print(f"📍 Arrived at {airports[current_location]['Name']}")


def present_options():

    print("\nAvailable Actions:")
    available_flights = []
    option_number = 1

    for connection in connections:
        if connection['Departure_Airport_ID'] == current_location:
            flight_time = connection['Time_Minutes']
            health_cost = flight_time * health_cost_per_minute
            dest = connection['Arrival_Airport_ID']
            print(f"{option_number}. Fly to {airports[dest]['Name']} "
                  f"({flight_time} min, -{health_cost:.2f} HP)")
            available_flights.append(connection)
            option_number += 1

    if airports[current_location]['Clinic']:
        print("H. Heal at the local clinic")

    print("Q. Quit Mission")

    return available_flights


def handle_player_choice():
    available_flights = present_options()
    choice = input("\nChoose your action: ").strip().upper()

    if choice == "Q":
        print("👋 Mission Quited.")
        sys.exit()

    elif choice == "H":
        handle_healing()

    elif choice.isdigit():  # only proceed if it's numeric
        choice_num = int(choice)
        if 1 <= choice_num <= len(available_flights):
            flight = available_flights[choice_num - 1]
            execute_flight(flight)
        else:
            print("❌ Invalid option. Try again.")
    else:
        print("❌ Invalid input. Enter a number, 'H', or 'Q'.")
import random



RISK_DEPARTURE = [
    {"name": "Severe Weather Delay", "probability": 0.15, "time_penalty": 30, "health_penalty": 2.5},
    {"name": "Technical Failure", "probability": 0.10, "time_penalty": 45, "health_penalty": 3.0},
]

RISK_DIVERSION = [
    {"name": "In-Flight Medical Emergency", "probability": 0.10, "time_penalty": 60, "health_penalty": 5.0},
    {"name": "Cabin Pressure Loss", "probability": 0.05, "time_penalty": 90, "health_penalty": 7.5},
]


ALL_AIRPORTS_ICAO = [
    'OTHH', 'VIDP', 'VCBI', 'RJAA', 'WSSS', 'ZBAA', 'RKSW', 'VTBSS', 'OMDB', 'RPLI',
    'LEMD', 'LSZH', 'EKCH', 'HECA', 'HKJK', 'FAOR', 'DNMM', 'GMMN', 'CYYZ', 'KORD',
    'CYVR', 'MMMX', 'KJFK', 'SCEL', 'SBGR', 'SAEZ', 'SPJC', 'SVMI', 'YMML', 'YSSY',
    'NZAA', 'YPPH', 'NFFN', 'LIRF', 'LFPB', 'EHAM', 'EGLL', 'EDDB', 'EPWA', 'CDG',
    'FRA', 'JFK'
]


def check_game_end(game_state):

    if game_state['health'] <= 0 or game_state['time_elapsed'] >= 1440:
        print("\n*** GAME OVER ***")
        return True
    return False


def execute_flight(game_state, flight_data):

    pass

def check_departure_risk(game_state):

    print("\n--- Step 6: Departure Risk Check (Before Takeoff) ---")


    for risk in RISK_DEPARTURE:

        if random.random() < risk['probability']:
            print(f"⚠️ Risk Triggered: {risk['name']}!")


            game_state['time_elapsed'] += risk['time_penalty']
            game_state['health'] -= risk['health_penalty']

            print(f"  Penalty Applied: Time +{risk['time_penalty']} min, Health -{risk['health_penalty']:.2f} HP")


            if check_game_end(game_state):
                return False


            return True

    print("✅ Departure is clear. Proceeding to takeoff.")
    return True


def handle_diversion_risk(game_state, original_flight):

    print("\n--- Step 7: Diverting Risk Check (Mid-Flight) ---")


    for risk in RISK_DIVERSION:
        if random.random() < risk['probability']:
            print(f"🚨 Diversion Risk Triggered: {risk['name']}!")


            print(f"  Incident Penalty: Time +{risk['time_penalty']} min, Health -{risk['health_penalty']:.2f} HP")

            decision = input("Do you want to accept the diversion and reroute? (Y/N): ").upper()

            if decision == 'N':

                print("🚫 Diversion refused. Flight continues to original destination.")
                return False


            if decision == 'Y':
                print("👍 Diversion accepted.")


                game_state['time_elapsed'] += risk['time_penalty']
                game_state['health'] -= risk['health_penalty']

                print(f"  Penalties Applied: Time +{risk['time_penalty']} min, Health -{risk['health_penalty']:.2f} HP")

                if check_game_end(game_state):
                    return True


                departure_icao = original_flight['departure_icao']
                arrival_icao = original_flight['arrival_icao']

                valid_diversions = [
                    icao for icao in ALL_AIRPORTS_ICAO
                    if icao != departure_icao and icao != arrival_icao
                ]

                print("\nValid Diversion Options (ICAO Codes):")
                print(valid_diversions)


                while True:
                    new_icao = input("Enter ICAO code for the diversion airport: ").upper()
                    if new_icao in valid_diversions:
                        game_state['current_location'] = new_icao
                        print(f"✈️ Rerouted. Current Location updated to: {new_icao}")

                        return True
                    else:
                        print("Invalid ICAO code. Please choose from the valid options.")


    return False


def attempt_flight(game_state, flight_data):

    print(f"\nAttempting flight from {flight_data['departure_icao']} to {flight_data['arrival_icao']}")


    if not check_departure_risk(game_state):
        return


    flight_diverted = handle_diversion_risk(game_state, flight_data)


    if not flight_diverted:
        print(f"✅ Flight successfully arrived at {flight_data['arrival_icao']}.")

        execute_flight(game_state, flight_data)


        check_game_end(game_state)

    return
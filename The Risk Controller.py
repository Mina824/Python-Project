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
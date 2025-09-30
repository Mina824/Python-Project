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
        password='12',
        autocommit=True
    )
    cursor = connection.cursor(dictionary=True)
    print('connected to database ')

    sql_query_airport = """
        select ICAO_Code, Airport_Name, Continent_ID, 
                Risk_Factor_ID, Clinic, Clinic_Healing_Amount, 
                Clinic_Time_Factor 
        from Airport """
    cursor.execute(sql_query_airport)
    for row in cursor. fetchall():
        icao_code = row['ICAO_Code']
        airport[icao_code] = row['Airport_Name']






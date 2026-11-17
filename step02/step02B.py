# Name: Nick Prouza
# Date: November 13, 2026
# Program Name: SE1
# Description: Road Trip Calculator

#constants
AVERAGE_SPEED = 55

#input
destination = input("Destination: ")
miles = float(input("Trip distance (miles): "))
mpg = float(input("Car's miles per gallon: "))
gas_price = float(input("Gas price per gallon: "))
people = int(input("Number of people splitting the cost: "))

#Processing
gallons = miles / mpg
gas_cost = gallons * gas_price
cost_per_person = gas_cost / people
total_minutes = int(miles / AVERAGE_SPEED * 60)
hours = total_minutes // 60
leftover_minutes = total_minutes % 60
round_trip_gas = gas_cost * 2

#output
print()
print(f"--- Tripo to {destination} ---")
print(f"Gallons of gas:    {gallons:.1f}")
print(f"Gas cost:          ${gas_cost:.2f}")
print(f"Cost per person:   ${cost_per_person:.2f}")
print(f"Driving time:      ${hours} hr {leftover_minutes} min (at {AVERAGE_SPEED} mph)")
print(f"Round trip gas:    ${round_trip_gas:.2f}")
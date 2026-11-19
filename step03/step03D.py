# Name: Nick Prouza
# Date: November 19, 2026
# Program Name: SE1
# BPA Eligibility Checker

# Constants
MIN_GPA = 2.0
OFFICER_GPA = 3.0
HONOR_GPA = 3.5
MAX_EVENTS = 2

# Input
name = input('name: ')
grade = int(input('Grade (9-12): '))
gpa = float(input('GPA (0.0-4.0): '))
dues_paid = input('Dues paid? (y/n): ')
events = int(input('Events signed up for: '))



# Processing and outputs
if grade < 9 or grade > 12:
    print('Error: grade must be 9 to 12.')
elif gpa <0.0 or gpa > 4.0:
    print('Error: GPA must be 0.0 to 4.0')
else:
    is_dues_paid = dues_paid.lower() == 'y'
    eligible = is_dues_paid and gpa >= MIN_GPA

    print()
    print(f"--- BPA Check for {name} ---")

    if eligible:
        print("Status: ELIGIBLE")

        if events == 0:
            print("Sign up for at least one event.")
        elif events == 1:
            print("You are entered in 1 event.")
        elif events == 2:
            print("You are entered in 2 events.")
        else:
            drop = events - MAX_EVENTS
            print(f"You can only enter 2 events. Drop {drop}.")
    else:
        print("Status: NOT ELIGIBLE")

        if not is_dues_paid:
            print("Reason: dues not paid.")

        if gpa < MIN_GPA:
            print("Reason: GPA is below 2.0.")
    if grade == 11 or grade == 12:
        if gpa >= OFFICER_GPA:
            print('You can run for chapter officer.')
    if grade == 12 and gpa >= HONOR_GPA:
        print('Senior honor cord: yes')




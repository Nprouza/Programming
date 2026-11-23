# Name: Nick Prouza
# Date: November 19, 2026
# Program Name: SE1
# Grade Checker

# Input
student_name = input("Student name: ")
score = int(input("Score (0-100): "))

# Processing and Output
if score < 0 or score > 100:
    print("Error: score must be 0 to 100.")
else:
    if score >= 90:
        letter = "A"
    elif score >= 80:
        letter = "B"
    elif score >= 70:
        letter = "C"
    elif score >= 60:
        letter = "D"
    else:
        letter = "F"

    if letter == "A" or letter == "F":
        article = "an"
    else:
        article = "a"

    print(f"{student_name} got {article} {letter}.")

    if score >= 60:
        print(f"{student_name} passed.")
    else:
        print("You did not pass.")

    if score == 100:
        print("Perfect score!")

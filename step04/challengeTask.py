PASSING_SCORE = 70

# Input
students = int(input("How many students? (1-30): "))
while students < 1 or students > 30:
    print("Please enter 1 to 30.")
    students = int(input("How many students? (1-30): "))

# Processing
total = 0
passing = 0

for student in range(1, students + 1):
    score = int(input(f"Score for student {student}: "))
    while score < 0 or score > 100:
        print("Scores must be 0 to 100.")
        score = int(input(f"Score for student {student}: "))

    total += score
    if score >= PASSING_SCORE:
        passing += 1

average = total / students

chart = ""
for _ in range(passing):
    chart += "#"

if passing == 0:
    chart = "none"

# Output
print()
print("--- Class Summary ---")
print(f"Students:  {students}")
print(f"Average:   {average:.1f}")
print(f"Passing:   {passing}")
print(f"Chart:     {chart}")
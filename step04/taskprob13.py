total = 0
count = 0

number = int(input("Enter a number (0 to stop): "))

while number != 0:
    total = total + number
    count = count + 1
    number = int(input("Enter a number (0 to stop): "))

print(f"You entered {count} numbers.")
print("The total is", total)

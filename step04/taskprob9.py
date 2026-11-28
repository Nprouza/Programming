
number = int(input('Enter a number (0 to stop): '))

while number != 0:
    if number < 0:
        print('Negative')
    else: 
        print('Positive')

    number = int(input('Enter a number (0 to stop): '))

print('All done')

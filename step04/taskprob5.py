# Name: Nick Prouza
# Date: November 24, 2026
# password checker

PASSWORD = 'python123'

answer = input('Enter the password: ')
while answer != PASSWORD:
    print('Try again!')
    answer = input('Enter the password: ')

print('Access granted!')
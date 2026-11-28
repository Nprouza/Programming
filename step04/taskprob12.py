name = input('Player name: ')
points = int(input('Points: '))

bar = ''
for _ in range(points):
    bar = bar + '*'

print(name + ': ' + bar)
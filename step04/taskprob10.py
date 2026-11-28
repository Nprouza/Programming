total = 0

for _  in range(5):
    score = float(input('Test score: '))
    total += score

average = total / 5
print(f'Average: {average:.1f}')

rating = int(input('Rate the movie (1-10): '))

while rating < 1 or rating > 10:
    print('please enter a number between 1 and 10')
    rating = int(input('Rate the movie (1-10): '))

print('Thank you for the rating!')
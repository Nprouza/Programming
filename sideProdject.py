
#Constants
TAX = 0.10
TRANSPORTAION = 120
LABOR_INSTALATION = 15000


#input
service = input('Servce: ')
cost = float(input('Cost of service: '))
num = int(input('Number of Services: '))

#processing
subtotal = cost * num
tax_amount = subtotal * TAX 
total_cost = subtotal + TRANSPORTAION + LABOR_INSTALATION + tax_amount

#outpute
print('-' * 32)
print('Cost Overview')
print('-' * 32)
print(f'Service: {service}')
print(f'Cost per service : ${subtotal:.2f}')
print(f'Quantity: {num}')
print(f'Subtotal: ${subtotal:.2f}')
print(f'Tax: ${TAX:.2f}')
print(f'Transportation ${TRANSPORTAION:.2f}')
print('=' * 32)
print(f'Total cost ${total_cost:.2f}')
print('=' * 32)


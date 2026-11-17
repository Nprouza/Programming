
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



#constants
TAX  = 0.20
INSTALL_FEE = 7000
SHIPPING_FEE = 8000


#inputs
pool_service = input('Pool Service: ')
cost = float(input('Cost of pool service: '))


#processing
subtotal = cost
tax_amount = subtotal * TAX
total_cost = subtotal + INSTALL_FEE + SHIPPING_FEE + tax_amount



#outputs

print('=' *32)
print('Cost Overview')
print('=' *32)
print(f'Pool Service: {pool_service}')
print(f'Cost of pool service: ${subtotal:.2f}')
print(f'TAX: ${tax_amount:.2f}')
print(f'Installartion Fee: ${INSTALL_FEE:.2f}')
print(f'Shipping Fee: ${SHIPPING_FEE:.2f}')
print('-' * 32)
print(f'Total Cost: ${total_cost:.2f}')
print('-' * 32)
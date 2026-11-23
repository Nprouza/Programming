# Name: Nick Prouza
# Date: November 23, 2026
# Program Name: SE1
# Snack bar order

TAX_RATE = 0.07

customer_name = input('Customer name: ')
item = input('Item: ')
price = float(input('Price: '))
quantity = int(input('Quantity: '))


subtotal = price * quantity 
tax = subtotal * TAX_RATE
total = subtotal + tax


print()
print(f'--- Receipt for {customer_name} ---')
print(f'Item:      {item}')
print(f'Quantity:  {quantity}')
print(f'Subtotal:  ${subtotal:.2f}')
print(f"Tax (7%):  ${tax:.2f}")
print(f"Total:     ${total:.2f}")





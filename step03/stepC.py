# Name: Nick Prouza
# Date: November 19, 2026
# Program Name: SE1
# Shipping Calculator

# Constnts 
ZONE1_RATE = 0.50
ZONE2_RATE = 0.75
ZONE3_RATE = 1.25
MINIMUN_SHIPPING = 4.00
FREE_SHIPPING_AMOUNT = 50.00
RUSH_FEE = 10.00


# Input
order_total = float(input('Order total: '))
weight = float(input('Pachage weight (lbs): '))
zone = int(input('Shipping zone (1-3): '))
rush = input('Rush delivery? (y/n): ')



# Processing and Output
if order_total <=0 or weight <=0:
    print('Error: order total and weight must be more than 0.')
elif zone != 1 and zone != 2 and zone != 3:
    print('Error: zone must be 1, 2 , or 3.')
else:
    is_rush = rush.lower() == 'y'

    if zone == 1:
        rate = ZONE1_RATE
        delivery_days = 2
    elif zone == 2:
        rate = ZONE2_RATE
        delivery_days = 4
    else:
        rate = ZONE2_RATE
        delivery_days = 6

    shipping = weight * rate

    if shipping < MINIMUN_SHIPPING:
        shipping = MINIMUN_SHIPPING

    if order_total >= FREE_SHIPPING_AMOUNT and not is_rush:
        shipping = 0.00

    if is_rush:
        shipping += RUSH_FEE
        if zone == 1 or zone ==2:
            delivery_days = 1
        else:
            delivery_days = 2

    heavy_package = weight > 50
    if heavy_package:
        delivery_days += 2

    grand_total = order_total + shipping

    print()
    print('--- Shipping Summary ---')
    print(f'Order total:  ${order_total:.2f}')

    if shipping == 0:
        print('Shipping      FREE')
    else:
        print(f'Shipping:     ${shipping:.2f}')
    print(f'Grand total:  ${grand_total}')

    if delivery_days == 1:
        print('Arrives in:  1 day')
    else:
        print(f'Arrives in:    {delivery_days} days')

    if heavy_package:
        print('Note: heavy package, 2 extra days added.')
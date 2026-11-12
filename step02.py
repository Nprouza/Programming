INSTALL_FEE = 25.00
onwer = input("Owner: ")
cost_per_foot = float(input("Cost per square foot"))
square_feet = int(input("Square feet: "))
material_cost = cost_per_foot * square_feet
total_cost = material_cast + INNSTALL_FEE

print(f"--- Estiimate for {owner} ---")
print(f"Material : ${material_cost:.2f}")
print(f"Install: ${INSTALL_FEE: .2f}")
print(f"Total:   ${total_cost:.2f}")

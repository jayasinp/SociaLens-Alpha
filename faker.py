import pandas as pd
import random
from faker import Faker

# Generate random data for Individuals sheet
def generate_individuals_data(num_individuals=100):
    faker = Faker()
    individuals_data = {
        "ID": range(1, num_individuals + 1),
        "Name": [faker.name() for _ in range(num_individuals)],
        "Age": [random.randint(18, 60) for _ in range(num_individuals)],
        "Occupation": [faker.job() for _ in range(num_individuals)]
    }
    return pd.DataFrame(individuals_data)

# Generate random network adjacencies
def generate_network_data(ids):
    num_links = len(ids) * 2  # Example: two edges per individual
    network_data = {
        "Source": [random.choice(ids) for _ in range(num_links)],
        "Target": [random.choice(ids) for _ in range(num_links)]
    }
    return pd.DataFrame(network_data)

# Main function to create Excel file with two sheets
def create_excel_file(filename="output.xlsx"):
    # Create DataFrame for each sheet
    df_individuals = generate_individuals_data(100)  # 100 individuals
    df_network = generate_network_data(df_individuals['ID'].tolist())

    # Create a Pandas Excel writer using Openpyxl as the engine
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df_individuals.to_excel(writer, sheet_name='Individuals', index=False)
        df_network.to_excel(writer, sheet_name='Network', index=False)

    print(f"Excel file '{filename}' has been created with two sheets.")

# Execute the function
create_excel_file()
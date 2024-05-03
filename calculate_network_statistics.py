import os
import pandas as pd
import networkx as nx

def calculate_network_statistics(file_path):
    """Calculates network statistics on selected Excel file."""
    base_path = 'network_prompt_files'
    dataset_name = os.path.splitext(os.path.basename(file_path))[0]
    folder_path = os.path.join(base_path, dataset_name)

    # Ensure the directory exists
    os.makedirs(folder_path, exist_ok=True)

    network_stats = []

    try:
        excel_file = pd.ExcelFile(file_path)
        print(f"Processing {len(excel_file.sheet_names)} sheets...")

        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            print(f"Processing sheet: {sheet_name} with columns {df.columns.tolist()}")

            if len(df.columns) != 2:
                print(f"Skipping '{sheet_name}' due to incorrect column count.")
                continue

            if pd.isna(df.columns).all():
                df.columns = ['Source', 'Target']
                print(f"Renamed columns for sheet '{sheet_name}'.")

            G = nx.from_pandas_edgelist(df, source='Source', target='Target')
            print(f"Graph for '{sheet_name}' created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

            sheet_stats = {
                'sheet_name': sheet_name,
                'node_degrees': dict(G.degree()),
                'degree_centrality': nx.degree_centrality(G),
                'betweenness_centrality': nx.betweenness_centrality(G),
                'closeness_centrality': nx.closeness_centrality(G),
                'eigenvector_centrality': nx.eigenvector_centrality(G, max_iter=1000, tol=1e-06),
                'density': nx.density(G)
            }
            network_stats.append(sheet_stats)

            # Writing results to text files
            file_name = f"{dataset_name}_{sheet_name}_network_stats.txt"
            full_file_path = os.path.join(folder_path, file_name)
            with open(full_file_path, 'w') as file:
                file.write(f"Network Statistics for '{sheet_name}'\n\n")
                for key, value in sheet_stats.items():
                    if isinstance(value, dict):
                        max_node = max(value, key=value.get)
                        min_node = min(value, key=value.get)
                        file.write(f"{key.title()} - Max: Node {max_node} with {value[max_node]:.4f}, Min: Node {min_node} with {value[min_node]:.4f}\n")
                    else:
                        file.write(f"{key.title()}: {value:.4f}\n")
                file.write("\n")
                print(f"Statistics written to {full_file_path}")

    except Exception as e:
        print(f"Error processing file: {e}")

    return network_stats

# Example usage
# file_path = 'path_to_your_excel_file.xlsx'
# stats = calculate_network_statistics(file_path)

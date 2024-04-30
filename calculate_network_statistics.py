import pandas as pd
import networkx as nx

def calculate_network_statistics(file_path):
    """Calculates network statistics on selected Excel file.

    Args:
        file_path (str): Path to the Excel file.

    Returns:
        list: A list of dictionaries, each containing sheet name and calculated statistics.
    """

    network_stats = []

    try:
        excel_file = pd.ExcelFile(file_path)

        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            # Only process sheets with two columns
            if len(df.columns) != 2:
                print(f"Sheet '{sheet_name}' has {len(df.columns)} columns, skipping...")
                continue  

            # Handle potential absence of headers
            if pd.isna(df.columns).all():  
                df.columns = ['Column1', 'Column2']  
                print(f"Sheet '{sheet_name}': Headers were missing, assigned generic names")

            # Create NetworkX graph
            G = nx.from_pandas_edgelist(df, source='Source', target='Target')

            sheet_stats = {
                'sheet_name': sheet_name,
                'node_degrees': dict(G.degree()),
                'degree_centrality': nx.degree_centrality(G),
                'betweenness_centrality': nx.betweenness_centrality(G),
                'closeness_centrality': nx.closeness_centrality(G),
                'eigenvector_centrality': nx.eigenvector_centrality(G),
                'density': nx.density(G)
            }

            network_stats.append(sheet_stats)

    except Exception as e:
        print(f"Error processing file: {e}")

    return network_stats

# Example usage
file_path = 'path_to_your_excel_file.xlsx'
stats = calculate_network_statistics(file_path)

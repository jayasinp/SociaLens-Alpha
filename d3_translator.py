# Declan: Function to convert Excel and CSV files to JSON - This is not neccessary if networks can be saved from networkx graph data in networkx_graphobject.py
import json
import os
import pandas as pd


def convert_network_to_json(file_path):
    # Check file type
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path)  # Read Excel file
    elif file_extension == '.csv':
        df = pd.read_csv(file_path)  # Read CSV file
    else:
        print("Unsupported file format:", file_extension)
        return
    
    # Extract links data from the dataframe
    if 'Source' in df.columns and 'Target' in df.columns:
        links_data = df[['Source', 'Target']].to_dict(orient='records')
        
        # Prepare nodes data by extracting unique values from 'source' and 'target' columns
        nodes_data = list(set(df['Source'].tolist() + df['Target'].tolist()))
        
        # Prepare the JSON object
        json_data = {"nodes": [], "links": []}
        
        # Assign group value and format nodes data
        group_value = 1
        for node in nodes_data:
            json_data["nodes"].append({"id": str(node), "group": group_value})
        
        # Format links data
        for link in links_data:
            json_data["links"].append({"source": str(link["Source"]), "target": str(link["Target"])})

        # Write JSON to file
        json_file_path = os.path.join('network_objects', os.path.splitext(os.path.basename(file_path))[0] + '.json')
        with open(json_file_path, 'w') as json_file:
            json.dump(json_data, json_file, indent=4)
        
        print("Conversion successful. JSON file saved at:", json_file_path)
    else:
        print("Columns 'source' and 'target' not found in the dataframe.")
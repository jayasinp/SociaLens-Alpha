from flask import Flask, request
import pandas as pd
import networkx as nx

app = Flask(__name__)

def create_graph_from_excel(file_path):
    # Read the Excel file into a Pandas DataFrame
    xls = pd.ExcelFile(file_path)
    sheets_with_2_columns = []
    
    # Iterate through each sheet in the Excel file
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name)
        
        # Check if the DataFrame has exactly 2 numerical columns
        if df.shape[1] == 2 and all(df[col].dtype == 'float64' or df[col].dtype == 'int64' for col in df.columns):
            sheets_with_2_columns.append(sheet_name)
        
        # Create a graph object from the DataFrame
        g = nx.from_pandas_edgelist(df, source=df.columns[0], target=df.columns[1])
        # You can store the graph object for future use here, such as saving it to a file or storing it in a database
    
    return sheets_with_2_columns

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file:
        # Save the uploaded file to a temporary location
        file_path = '/tmp/' + file.filename
        file.save(file_path)
        
        # Create graph objects from the uploaded Excel file
        sheets_with_2_columns = create_graph_from_excel(file_path)
        
        # Return a response indicating the sheets with 2 numerical columns
        return {'sheets_with_2_columns': sheets_with_2_columns}, 200
    else:
        return {'error': 'No file provided'}, 400

if __name__ == '__main__':
    app.run(debug=True)

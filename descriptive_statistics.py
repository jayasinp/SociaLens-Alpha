import pandas as pd

def analyze_file(file_path):
    output = {}
    try:
        # Attempt to read file based on its extension
        if file_path.endswith(('.xlsx', '.xls')):
            data = pd.read_excel(file_path, sheet_name=None)  # None reads all sheets
        elif file_path.endswith('.csv'):
            data = {'CSV': pd.read_csv(file_path)}
        else:
            return {'error': "Unsupported file format"}

        # Analyze each sheet
        for sheet_name, df in data.items():
            # Prepare data dictionary for each sheet
            stats = {}
            numeric_columns = df.select_dtypes(include=['float64', 'int64'])
            for column in numeric_columns:
                stats[column] = {
                    'Mean': numeric_columns[column].mean(),
                    'Median': numeric_columns[column].median(),
                    'Mode': numeric_columns[column].mode().values.tolist(),
                    'Standard Deviation': numeric_columns[column].std(),
                    'Variance': numeric_columns[column].var(),
                    'Skewness': numeric_columns[column].skew(),
                    'Kurtosis': numeric_columns[column].kurt(),
                    'Min': numeric_columns[column].min(),
                    'Max': numeric_columns[column].max(),
                    '25th Percentile': numeric_columns[column].quantile(0.25),
                    '50th Percentile': numeric_columns[column].quantile(0.5),
                    '75th Percentile': numeric_columns[column].quantile(0.75),
                    'Count': numeric_columns[column].count(),
                    'Missing Values': numeric_columns[column].isna().sum()
                }
            output[sheet_name] = stats
    except Exception as e:
        return {'error': f"Failed to process file: {str(e)}"}

    return output

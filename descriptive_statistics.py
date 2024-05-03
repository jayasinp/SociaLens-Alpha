import os
import pandas as pd

def analyze_file(file_path):
    base_path = 'descriptive'
    output = {}

    # Extract filename without extension to use as a folder name
    dataset_name = os.path.splitext(os.path.basename(file_path))[0]
    folder_path = os.path.join(base_path, dataset_name)

    # Ensure the directory exists
    os.makedirs(folder_path, exist_ok=True)
    
    try:
        # Determine the type of file and read it
        if file_path.endswith(('.xlsx', '.xls')):
            data = pd.read_excel(file_path, sheet_name=None)  # Read all sheets
        elif file_path.endswith('.csv'):
            data = {'CSV': pd.read_csv(file_path)}
        else:
            return {'error': "Unsupported file format"}

        # Process each sheet
        for sheet_name, df in data.items():
            # Initialize stats dictionary for the current sheet
            stats = {}
            numeric_columns = df.select_dtypes(include=['float64', 'int64'])

            # Creating filename with prefix of the dataset name and the sheet name
            file_name = f"{dataset_name}_{sheet_name}.txt"
            full_file_path = os.path.join(folder_path, file_name)

            with open(full_file_path, 'w') as file:
                for column in numeric_columns:
                    column_stats = {
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
                    stats[column] = column_stats

                    # Write each statistic in a formatted string
                    file.write(f"Statistics for column '{column}' in sheet '{sheet_name}':\n")
                    for stat, value in column_stats.items():
                        file.write(f"The {stat} for column '{column}' is {value}\n")
                    file.write("\n")

            output[sheet_name] = stats

    except Exception as e:
        return {'error': f"Failed to process file: {str(e)}"}

    return output
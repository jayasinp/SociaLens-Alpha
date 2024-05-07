import os
import pandas as pd
import networkx as nx
from rpy2.robjects.packages import importr
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
from pathlib import Path # DEBUG


class ErgmProcessFileException(Exception):
    pass


def setup_r_packages():
    """Load necessary R packages."""
    pandas2ri.activate()
    base = importr('base')
    network = importr('network', on_conflict="warn")
    ergm = importr('ergm', on_conflict="warn")

def calculate_ergm_from_edgelist(edgelist):
    """Calculate ERGM given an edgelist DataFrame."""
    setup_r_packages()
    r_dataframe = pandas2ri.py2rpy(edgelist)
    ro.globalenv['edgelist'] = r_dataframe
    ro.r('''
    # Initialize a network object, specifying the dataframe and allowing multiple edges
    net <- network(edgelist, directed=FALSE, loops=TRUE, multiple=TRUE)
    # Define and fit the ERGM model, including basic network terms such as edges and triangles
    fit <- ergm(net ~ edges + triangle)
    return(summary(fit))  # Return a summary of the ERGM fit
    ''')
    results = ro.r('summary')
    return results

def process_file(file_path):
    """Process an Excel file to extract edgelists and compute ERGM."""
    try:
        data = pd.read_excel(file_path, sheet_name=None) # TODO Consider using R's read excel function instead, and then remove the import pandas line
        results = {}
        for sheet, df in data.items():
            if df.shape[1] == 2 and not df.isnull().values.any():
                # Assuming the columns are correctly ordered as Source, Target
                result = calculate_ergm_from_edgelist(df)
                results[sheet] = result
        return results
    except Exception as e:
        #raise #lets the exception happen # DEBUG
        # raise ErgmProcessFileException("We couldnt read the file. The path was") # DEBUG
        return str(e)


# DEGUG
if __name__ == "__main__":
    #path = r"/Users/pravinjayasinghe/Desktop/Swinburne Courses/Semester 1 2024/Tech Innovation/SociaLens-Alpha/raw_data_objects/Jan-Cleaned/Jan-Cleaned_net_0_Friends.xlsx"
    path = Path.cwd() / "raw_data_objects/Jan-Cleaned/Jan-Cleaned_net_0_Friends.xlsx" 
    results = process_file(path)
    print("STOP")
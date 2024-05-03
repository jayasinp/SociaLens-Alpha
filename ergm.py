import os
import pandas as pd
import networkx as nx
from rpy2.robjects.packages import importr
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri

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
    net <- network(edgelist, directed=FALSE)
    fit <- ergm(net ~ edges + triangle)
    summary <- summary(fit)
    ''')
    results = ro.r('summary')
    return results

def process_file(file_path):
    """Process an Excel file to extract edgelists and compute ERGM."""
    try:
        data = pd.read_excel(file_path, sheet_name=None)
        results = {}
        for sheet, df in data.items():
            if df.shape[1] == 2 and not df.isnull().values.any():
                # Assuming the columns are correctly ordered as Source, Target
                result = calculate_ergm_from_edgelist(df)
                results[sheet] = result
        return results
    except Exception as e:
        return str(e)

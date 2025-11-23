# Simple Data Preparation Recipe
# This recipe demonstrates basic data transformation

import dataiku
from dataiku import pandasutils as pdu
import pandas as pd
from datetime import datetime

# Read input dataset
input_dataset = dataiku.Dataset("RAW_DATA")
df = input_dataset.get_dataframe()

# Data transformations
def prepare_data(df):
    """
    Prepare data for analysis

    Steps:
    1. Filter out invalid records
    2. Calculate derived fields
    3. Add metadata
    """
    # Filter: Remove records with null values
    df = df[df['value'].notna()]

    # Derive: Calculate normalized value
    df['value_normalized'] = df['value'] / df['value'].max()

    # Derive: Add processing timestamp
    df['processed_at'] = datetime.utcnow()

    # Derive: Extract date for partitioning
    df['created_date'] = pd.to_datetime(df['created_at']).dt.date

    return df

# Apply transformations
df_prepared = prepare_data(df)

# Write output dataset
output_dataset = dataiku.Dataset("PREPARED_DATA")
output_dataset.write_with_schema(df_prepared)

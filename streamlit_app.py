import streamlit as st
import pandas as pd
import os

# Title of the app
st.title("Simple CSV Viewer App")

# Create a file uploader widget
#uploaded_file = st.file_uploader("Upload a CSV file", type="csv")

csv_file_path = os.path.join(os.getcwd(), "weather.csv")

# Check if the file exists
if os.path.exists(csv_file_path):
    # Read the CSV file
    df = pd.read_csv(csv_file_path)

    # Display the dataframe in a table
    st.write("### Data Preview")
    st.dataframe(df)

    # Show some basic statistics of the dataframe
    st.write("### Data Statistics")
    st.write(df.describe())
else:
    st.error(f"CSV file not found at path: {csv_file_path}")
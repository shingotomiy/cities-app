import pandas as pd
import os
import re
import numpy as np
from shapely.geometry import Point, Polygon
import ast
import requests


import geopandas as gpd
from shapely.geometry import Point, Polygon
import pandas as pd
import numpy as np
import streamlit as st 

import os
from itertools import combinations

school_csv_file_path = os.path.join(os.getcwd(), "calgary_school_list.csv")
catchment_tsv_file_path = os.path.join(os.getcwd(), "calgary_school_catchment.tsv")


# Check if the file exists
if os.path.exists(school_csv_file_path):
    # Read the CSV file
    school_df = pd.read_csv(school_csv_file_path)

    # Display the dataframe in a table
#    st.write("### Data Preview")
 #   st.dataframe(school_df)

    # Show some basic statistics of the dataframe
    #st.write("### Data Statistics")
    #st.write(df.describe())
else:
    st.error(f"CSV file not found at path: {school_csv_file_path}")

# Check if the file exists
if os.path.exists(catchment_tsv_file_path):
    # Read the CSV file
    catchment_df = pd.read_csv(catchment_tsv_file_path, sep='\t')

    # Display the dataframe in a table
 #   st.write("### Data Preview")
#    st.dataframe(catchment_df)

    # Show some basic statistics of the dataframe
    #st.write("### Data Statistics")
    #st.write(df.describe())
else:
    st.error(f"CSV file not found at path: {catchment_tsv_file_path}")



#tabs = st.tabs(["学校一覧","住所から絞り込み","小学校、中学校ともに徒歩通学のエリア一覧"])


# Assuming school_df and catchment_df are already defined and loaded
merged_df = pd.merge(school_df, catchment_df, on='school_id', how='outer')

merged_df['list_of_type_2_elem'] = merged_df['list_of_type_2_elem'].apply(lambda x: str(x).strip())
merged_df['list_of_type_2_elem'] = merged_df['list_of_type_2_elem'].apply(lambda x: str(x).replace(',"', '\',\'').replace('"', ''))
merged_df['list_of_type_2_elem'] = merged_df['list_of_type_2_elem'].fillna('')

merged_df['list_of_type_5_elem'] = merged_df['list_of_type_5_elem'].apply(lambda x: str(x).strip())
merged_df['list_of_type_5_elem'] = merged_df['list_of_type_5_elem'].apply(lambda x: str(x).replace(',"', '\',\'').replace('"', ''))
merged_df['list_of_type_5_elem'] = merged_df['list_of_type_5_elem'].fillna('')

merged_df = merged_df[merged_df['Grades Offered'] != '10-12']
#st.write(len(merged_df))
#st.stop()
def parse_multiple_polygons(polygon_str):
    
    #print(f"Original data: {polygon_str}")
    
    # Check for None, empty list, or invalid data
    if polygon_str is None or not isinstance(polygon_str, str) or polygon_str == "[]":
        return []  # Return an empty list for None, empty, or invalid data
    
    try:
        # Clean the string: remove the outer square brackets
        cleaned_str = polygon_str.strip("[]").replace(" 0 0", "")
        
        # Split by "', '" to separate different polygons (this handles cases where polygons are separated by a comma and single quotes)
        polygon_strings = re.split(r"','|', '", cleaned_str)
        
        # Further clean the first and last polygon strings by removing any remaining single quotes
        polygon_strings[0] = polygon_strings[0].lstrip("'")
        polygon_strings[-1] = polygon_strings[-1].rstrip("'")
        
        # List to store all polygons
        polygons = []
        
        # Iterate through each polygon string
        for polygon in polygon_strings:
            point_pairs = polygon.split(', ')
            
            # Convert each pair into a (longitude, latitude) tuple
            polygon_points = [(float(p.split()[0]), float(p.split()[1])) for p in point_pairs if len(p.split()) >= 2]
            
            if len(polygon_points) >= 3:  # Only valid polygons have 3 or more points
                polygons.append(polygon_points)  # Add the parsed polygon to the list
          #  else:
         #       print(f"Invalid polygon: {polygon_points}")
        
        return polygons
    
    except (ValueError, IndexError) as e:
        #print(f"Error occurred: {e}")
        return []



# Function to generate the geo grid
def generate_geo_grid(min_lat, max_lat, min_lng, max_lng, step=0.0002):
    latitudes = np.arange(min_lat, max_lat, step)
    longitudes = np.arange(min_lng, max_lng, step)
    
    # Create a list of all combinations of latitudes and longitudes
    geo_points = [(lat, lng) for lat in latitudes for lng in longitudes]
    
    return gpd.GeoDataFrame(geometry=[Point(lng, lat) for lat, lng in geo_points], crs="EPSG:4326")

# Define the boundaries of Calgary (based on your calculated global min/max)
min_lat = 50.8428
max_lat = 51.1980
min_lng = -114.3158
max_lng = -113.8655

# Create the geo grid as a GeoDataFrame

geo_grid_gdf = generate_geo_grid(min_lat, max_lat, min_lng, max_lng, step=0.0002)

#geo_grid_gdf = geo_grid_gdf[:1000]

# Function to parse multiple polygons
def parse_multiple_polygons(polygon_str):
    if polygon_str is None or not isinstance(polygon_str, str) or polygon_str == "[]":
        return []  # Return an empty list for None, empty, or invalid data
    
    try:
        cleaned_str = polygon_str.strip("[]").replace(" 0 0", "")
        polygon_strings = re.split(r"','|', '", cleaned_str)
        polygon_strings[0] = polygon_strings[0].lstrip("'")
        polygon_strings[-1] = polygon_strings[-1].rstrip("'")
        
        polygons = []
        for polygon in polygon_strings:
            point_pairs = polygon.split(', ')
            polygon_points = [(float(p.split()[0]), float(p.split()[1])) for p in point_pairs if len(p.split()) >= 2]
            if len(polygon_points) >= 3:  # Only valid polygons have 3 or more points
                polygons.append(polygon_points)  # Add the parsed polygon to the list
        
        return polygons
    
    except (ValueError, IndexError):
        return []

# Create polygons for each school catchment area
def create_catchment_polygons(df):
    df['catchment_polygons'] = df['list_of_type_5_elem'].apply(lambda x: Polygon(parse_multiple_polygons(x)[0]) if parse_multiple_polygons(x) else None)
    return df.dropna(subset=['catchment_polygons'])

# Parse multiple polygons and catchment areas into GeoDataFrame
catchment_gdf = create_catchment_polygons(merged_df)
catchment_gdf = gpd.GeoDataFrame(catchment_gdf, geometry='catchment_polygons', crs="EPSG:4326")

#catchment_gdf
#geo_grid_gdf

#st.write(geo_grid_gdf.crs)
#st.write(catchment_gdf.crs)

catchment_gdf = catchment_gdf[catchment_gdf.is_valid]
geo_grid_gdf = geo_grid_gdf[geo_grid_gdf.is_valid]

#catchment_gdf

if geo_grid_gdf.crs != catchment_gdf.crs:
    geo_grid_gdf = geo_grid_gdf.to_crs(catchment_gdf.crs)

# Perform a spatial join to find points within polygons using the predicate argument

# Perform the spatial join
try:
    result_gdf = gpd.sjoin(geo_grid_gdf, catchment_gdf, how='inner', predicate='within')
except Exception as e:
    print(f"Error during spatial join: {e}")

'now showing result_gdf'
#result_gdf

# Group by the geo point (geometry) and aggregate the unique schools at each point
schools_at_each_geo_point = result_gdf.groupby(['geometry']).agg(
    school_names=('School Name', lambda x: tuple(sorted(x.unique()))),  # Unique and sorted school names as tuples
    school_ids=('school_id', lambda x: tuple(sorted(x.unique()))),  # Unique and sorted school IDs as tuples
    grades_offered=('Data Grades', lambda x: tuple(sorted(x.unique()))),  # Unique and sorted school IDs as tuples
).reset_index()

'now showing schools at each geo point'
#schools_at_each_geo_point

# Filter to keep only the geo points where more than 1 unique school is present
geo_points_with_multiple_schools = schools_at_each_geo_point[
    schools_at_each_geo_point['school_names'].apply(lambda x: len(x) > 1)
]

# Remove the geometry column and keep only the unique combinations of schools
unique_school_combinations = geo_points_with_multiple_schools.drop_duplicates(subset=['school_names']).reset_index(drop=True)

# Create a final dataframe showing only school names and IDs
final_df = pd.DataFrame({
    'School Names': unique_school_combinations['school_names'],
    'School IDs': unique_school_combinations['school_ids'],
    'Data Grades': unique_school_combinations['grades_offered']
})

st.write('now showing unique combination')
# Display the final result
st.dataframe(final_df)

print(final_df)


# Flatten the tuples in each row
#final_df['Flattened Grades'] = final_df['Data Grades'].apply(lambda x: [item for tup in x for item in tup])
#final_df['Flattened Grades'] = final_df['Data Grades'].apply(lambda x: [int(num) for num in x.split(',') if num])

final_df['Flattened Grades'] = final_df['Data Grades'].apply(
    lambda row: [int(num) for tup in row for num in tup.split(',') if num.isdigit()]
)


def has_all_grades(grades):
    return set(range(1, 10)).issubset(grades)


# Display the DataFrame with the new column
final_df['Covering_one_to_nine'] = final_df['Flattened Grades'].apply(has_all_grades)


final_df[final_df['Covering_one_to_nine']]
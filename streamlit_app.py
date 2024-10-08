from jscomponent import jscomponent
import streamlit as st
import pandas as pd
import os
import pydeck as pdk
import re
import numpy as np
from shapely.geometry import Point, Polygon, MultiPolygon
import requests
import streamlit.components.v1 as components


st.set_page_config(layout="wide", page_title="Cities")

google_map_api_key = st.secrets["google_map_api_key"]

_ = """
##### 引っ越し先の希望事項
 - 共同住宅（コンド、マンション）よりも一軒家がいいね
 - Semi Detachedは？　Townhouseは？
 - 大通りに面していない、できるだけ閑静な住宅街
 - （しほ）平屋ならいいな
　- （しほ）太陽が出ている日が多いほうがいい。　(降水量?　日照時間?　Sunny Days?)
 - （しんご）タイミングはさておきバンクーバーには絶対住む

##### 住宅購入の予算　（ざっくり1ドル=100円で計算）
###### 手出し
- 現時点でポンと出せるのは2500万円
- 特に何もしなければ一年間に250万ずつ増えていく
- 来年購入なら2750万円、再来年購入なら3000万円

(内訳)
- RRSP 600万円、TFSA 110万円、FSHA 100万円
- しほ口座 1550万円
- 年間の増額は、しほの金利で60万円、FHSAで70万、TFSAで120万

###### ローン
- 解雇がなければ、だいたい一億円まで借りられる
- House Poorは避けたいので、あまり高い金額を借りたくない
- 5年固定金利、一時期6%だったが4%代前半まで下がってきている（2024年9月時点）
- 3〜4000万円借りて、10年以内に返し切るのが理想？

##### 住宅購入イメージ(カルガリー)
6000万円の家を、頭金2000万、ローン4000万で購入

諸経費に250万円

リフォームに600万円

引っ越しに150万円

##### 住宅購入イメージ(ビクトリア)
1億円の家を、頭金2000万、ローン8000万で購入

諸経費に400万円

リフォームに350万円

引っ越しに150万円
 
##### 日本へのアクセス
 - 飛行機代
 - フライト時間
 - 直通便が通年あるか、季節限定であるか


##### 引っ越しのタイミング
 - 今のコンド、更新できなかったらどうする？
 - 今のコンド、近隣の建設ラッシュで住みにくくなっていく？
 - 今のコンドにいつまででも住めるとして、太郎は５年生まで？６年生まで？

##### 引っ越し先の太郎、次郎の小学校、中学校、高校
 - ”いい”学校

"""



school_csv_file_path = os.path.join(os.getcwd(), "calgary_school_list.csv")
catchment_tsv_file_path = os.path.join(os.getcwd(), "calgary_school_catchment.tsv")
school_review_google_file_path = os.path.join(os.getcwd(), "calgary_school_google_review.tsv")
fraser_scores_file_path = os.path.join(os.getcwd(), "fraser_scores.tsv")

# Check if the file exists
if os.path.exists(school_csv_file_path):
    school_df = pd.read_csv(school_csv_file_path)
else:
    st.error(f"CSV file not found at path: {school_csv_file_path}")

# Check if the file exists
if os.path.exists(catchment_tsv_file_path):
    # Read the TSV file
    catchment_df = pd.read_csv(catchment_tsv_file_path, sep='\t')

else:
    st.error(f"CSV file not found at path: {catchment_tsv_file_path}")

# Check if the file exists
if os.path.exists(school_review_google_file_path):
    # Read the TSV file
    google_review_df = pd.read_csv(school_review_google_file_path, sep='\t')

else:
    st.error(f"CSV file not found at path: {school_review_google_file_path}")

# Check if the file exists
if os.path.exists(fraser_scores_file_path):
    # Read the TSV file
    fraser_scores_df = pd.read_csv(fraser_scores_file_path, sep='\t')

else:
    st.error(f"CSV file not found at path: {fraser_scores_file_path}")

# Title of the app
st.title("カルガリーの公立学校、不動産価格と各エリア(Ward)の特色")

tabs = st.tabs(["学校一覧","住所から絞り込み","小学校、中学校ともに徒歩通学のエリア一覧", "川へのアクセス", "地域の人種構成", "QoLのアンケート結果","犯罪マップ","過去一年の不動産データ"])


# Assuming school_df and catchment_df are already defined and loaded
merged_df = pd.merge(school_df, catchment_df, on='school_id', how='outer')
merged_df = pd.merge(merged_df, google_review_df, on='School Name', how='left')
merged_df = pd.merge(merged_df, fraser_scores_df, on='Phone', how='left')

merged_df['list_of_type_2_elem'] = merged_df['list_of_type_2_elem'].apply(lambda x: str(x).strip())
merged_df['list_of_type_2_elem'] = merged_df['list_of_type_2_elem'].apply(lambda x: str(x).replace(',"', '\',\'').replace('"', ''))
merged_df['list_of_type_2_elem'] = merged_df['list_of_type_2_elem'].fillna('')

merged_df['list_of_type_5_elem'] = merged_df['list_of_type_5_elem'].apply(lambda x: str(x).strip())
merged_df['list_of_type_5_elem'] = merged_df['list_of_type_5_elem'].apply(lambda x: str(x).replace(',"', '\',\'').replace('"', ''))
merged_df['list_of_type_5_elem'] = merged_df['list_of_type_5_elem'].fillna('')


merged_df['Google Review'] = merged_df['Google Review'].fillna('-')
merged_df['Fraser Score'] = merged_df['Fraser Score'].fillna('-')
merged_df['Fraser Ranking'] = merged_df['Fraser Ranking'].fillna('N/A')
merged_df['ESL(%)'] = merged_df['ESL(%)'].fillna('-')
merged_df['Special Needs(%)'] = merged_df['Special Needs(%)'].fillna('-')


#merged_df = merged_df[merged_df['school_id'].isin([131])]

def remove_grades_info(program):
    if isinstance(program, str):  # Only apply regex if the value is a string
        return re.sub(r'\(Grades:.*?\)', '', program).strip()
    else:
        return program
    

# Apply the function to the 'Programs' column
merged_df['Programs'] = merged_df['Programs'].apply(remove_grades_info)

columns_to_display = ["School Name", "Google Review", "Fraser Score", "Fraser Ranking", "ESL(%)", "Special Needs(%)", "Address", "Programs", "Total Enrollment", "Grade 1", "Grade 2", "Grade 6", "Grade 7", "Grade 10", "Grade 12", "URL"]


with tabs[0]:
    @st.fragment
    def render_tab_0():
        # Initialize the DataFrame to be used for filtering
        filtered_df = merged_df.copy()

        with st.form("my_form"):
            cal_columns = st.columns(2)
            # Multiselect for Grades Offered
            selected_grade_offered = cal_columns[0].multiselect(
                'Grades Offered', 
                sorted(filtered_df['Grades Offered'].dropna().unique())
            )

            # Filter the DataFrame based on selected grades
            if selected_grade_offered:
                filtered_df = filtered_df[filtered_df['Grades Offered'].isin(selected_grade_offered)]

            def filter_schools_by_grades(df, selected_grades):
                # Function to check if the grade overlaps with selected grades
                def grade_in_selection(grade_range, selected_grades):
                    # Split the grades range, e.g., "1-6" becomes [1,6] or "K-6" becomes ["K",6]
                    start, end = grade_range.split('-')
                    
                    if start == 'K':
                        start = 0  # Treat K as 0 for numeric comparison
                    start, end = int(start), int(end)
                    
                    # Check if any of the selected grades fall within the range
                    for grade in selected_grades:
                        if grade == 'K':  # Handle the case for Kindergarten
                            if start == 0:  # Kindergarten (K) is treated as grade 0
                                return True
                        elif start <= int(grade) <= end:
                            return True
                    return False
                
                # Apply the filtering to the DataFrame
                filtered_df = df[df['Grades Offered'].apply(lambda x: grade_in_selection(x, selected_grades))]
                return filtered_df


            selected_grade = cal_columns[0].number_input("Select Grade", min_value=0, max_value=12, step = 1)#, value=12)

            if selected_grade:
                filtered_df = filter_schools_by_grades(filtered_df, [selected_grade])

            cal_columns[1].image('ward.png', caption='Wards of Calgary', width=300)
            # Multiselect for Ward
            selected_ward = cal_columns[0].multiselect(
                'Ward', 
                sorted(filtered_df['Ward'].dropna().unique())
            )
            # Filter the DataFrame based on selected wards
            if selected_ward:
                filtered_df = filtered_df[filtered_df['Ward'].isin(selected_ward)]

            # Multiselect for Area
            selected_area = cal_columns[0].multiselect(
                'Area', 
                sorted(filtered_df['Area'].fillna('Unknown').astype(str).unique())
            )

            # Filter the DataFrame based on selected areas
            if selected_area:
                filtered_df = filtered_df[filtered_df['Area'].fillna('Unknown').astype(str).isin(selected_area)]

            # Multiselect for Programs
            selected_program = cal_columns[0].multiselect(
                'Programs', 
                sorted(filtered_df['Programs'].fillna('Unknown').astype(str).unique())#,
                #default = ['Regular (10-12) , Early French Immersion (10-12) , International Baccalaureate (IB) (10-12) , Late French Immersion (10-12) , International Baccalaureate (French Immersion) (10-12)', 'Regular (10-12) , International Baccalaureate (IB) (10-12)', 'Regular (10-12) , International Baccalaureate (IB) (10-12) , International Baccalaureate (Career) (10-12)']
            )

            # Filter the DataFrame based on selected programs
            if selected_program:
                filtered_df = filtered_df[filtered_df['Programs'].fillna('Unknown').astype(str).isin(selected_program)]

            # Multiselect for Address
            selected_address = cal_columns[0].multiselect(
                'Address', 
                sorted(filtered_df['Address'].dropna().unique())
            )

            # Filter the DataFrame based on selected addresses
            if selected_address:
                filtered_df = filtered_df[filtered_df['Address'].isin(selected_address)]


            # Multiselect for Address
            selected_school_name = cal_columns[0].multiselect(
                'School Name', 
                sorted(filtered_df['School Name'].dropna().unique())
            )

            # Filter the DataFrame based on selected addresses
            if selected_school_name:
                filtered_df = filtered_df[filtered_df['School Name'].isin(selected_school_name)]

            # Multiselect for Address
            selected_school_id = cal_columns[0].multiselect(
                'School ID', 
                sorted(filtered_df['school_id'].dropna().unique())
            )

            # Filter the DataFrame based on selected addresses
            if selected_school_id:
                filtered_df = filtered_df[filtered_df['school_id'].isin(selected_school_id)]

            schools = []

            #school_info = {
            #    "title": "Belvedere Parkway School",
            #    "lat": 51.0927959,
            #    "lng": -114.211518,
            #    "url": "https://www.indeed.com",
            #    "catchment": "-114.259479182059 51.102261091026833 0 0, -114.2596970021098 51.102258969542191 0 0, -114.2599129717761 51.1022398073628 0 0, -114.26012952695351 51.102226037279841 0 0",
            #    "walk": "-114.2229115093496 51.09863804697887 0, -114.2230201444176 51.0945872555229 0, -114.2222124372001 51.094491968494538 0, -114.221982608032 51.0946618485736 0, -114.21049961386819 51.088558910685812 0, -114.212143246507 51.08657102806756 0, -114.2127165297312 51.0858680052535 0"
            #
            #}

            #schools.append(school_info)
            submitted = st.form_submit_button("絞り込み")

        
        df_selected = st.dataframe(filtered_df[columns_to_display], hide_index=True, on_select='rerun')
        about_school = st.container()
        if df_selected and 'selection' in df_selected and 'rows' in df_selected['selection']:
            selected_rows = df_selected['selection']['rows']

            if selected_rows:
                filtered_df = filtered_df.iloc[selected_rows]
                #about_school.caption(filtered_df['School Text'].iloc[0])
                #about_school.dataframe(filtered_df)


        limit_to_walk = st.toggle("徒歩通学の範囲を表示(学校のコミュニティ内)", value=True)

        filtered_df = filtered_df.replace({np.nan: None})          
        
        for index, row in filtered_df.iterrows():
            if not (pd.isnull(row['Latitude']) or pd.isnull(row['Longitude'])):
                try:
                    lat = float(row['Latitude'])
                    lng = float(row['Longitude'])
                except ValueError:
                    print(f"Invalid coordinates for {row['title']}, skipping this entry.")
                    continue
                
                if limit_to_walk:
                    row['list_of_type_2_elem'] = []
                else:
                    row['list_of_type_5_elem'] = []
                school_info = {
                    "title": row['School Name'], 
                    "lat": row['Latitude'],            
                    "lng": row['Longitude'],           
                    "url": row['URL'],
                    "catchment": row['list_of_type_2_elem'],
                    "walk": row['list_of_type_5_elem'] 
                }
                
                # Append each school_info dictionary to the schools list
                schools.append(school_info)
            else:
                print(f"Skipping school: {row['School Name']} due to missing lat/lng")
        
        jscomponent(my_schools_value=schools, height=1200)    

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
                    else:
                        print(f"Invalid polygon: {polygon_points}")
                
                return polygons
            
            except (ValueError, IndexError) as e:
                print(f"Error occurred: {e}")
                return []
    render_tab_0()            
        
with tabs[1]:
    @st.fragment
    def render_tab_1():
        value = jscomponent(show_blank_map=True, height=1200)

        #st.write("Received", value)

        def is_point_in_polygon(lat, lng, polygon_str):
            polygons = parse_multiple_polygons(polygon_str)
        
            # Create a point with given lat and lng
            point = Point(lng, lat)  # Note: Point takes (longitude, latitude)

            for polygon_points in polygons:
                polygon = Polygon(polygon_points)
                if point.within(polygon):
                    return True
            
            return False

        if value:

            def calculate_walking_time(origin, destination):
                params = {
                    'origins': origin,
                    'destinations': destination,
                    'mode': 'walking',  
                    'units': 'metric',
                    'key': 'AIzaSyBcAGp1w4qYE45ADHvJtGxBNHsy0_bywVM'
                }

                response = requests.get('https://maps.googleapis.com/maps/api/distancematrix/json', params=params)

                if response.status_code == 200:
                    data = response.json()

                    if data['rows'][0]['elements'][0]['status'] == 'OK':
                        walking_time = data['rows'][0]['elements'][0]['duration']['text']
                        walking_distance = data['rows'][0]['elements'][0]['distance']['text']
                        return walking_time, walking_distance
                    else:
                        return "No walking route found", ""
                else:
                    return f"Error: {response.status_code}"

            origin_to_calc_distance = f"{value[0]}, {value[1]}"

            merged_df['catching_the_address'] = merged_df['list_of_type_2_elem'].apply(lambda x: is_point_in_polygon(value[0], value[1], x))
            merged_df['the_address_in_walk_area'] = merged_df['list_of_type_5_elem'].apply(lambda x: is_point_in_polygon(value[0], value[1], x))

            walk_df = merged_df[merged_df['the_address_in_walk_area'] == True]

            def add_walking_time_to_df(df):
                df['徒歩'] = ""
                df['家からの距離'] = ""
                
                for index, row in df.iterrows():
                    destination_lat_lng = f"{row['Latitude']}, {row['Longitude']}"
                    walking_time, walking_distance = calculate_walking_time(origin_to_calc_distance, destination_lat_lng)
                    
                    df.at[index, '徒歩'] = walking_time
                    df.at[index, '家からの距離'] = walking_distance
                
                return df

            # Add walking times and distances to the walk_df
            walk_df = add_walking_time_to_df(walk_df)

            '徒歩で通学圏内の学校'
            walk_df_selected = st.dataframe(walk_df[['徒歩', '家からの距離'] + columns_to_display], hide_index=True, on_select='rerun')

            if walk_df_selected and 'selection' in walk_df_selected and 'rows' in walk_df_selected['selection']:
                selected_rows = walk_df_selected['selection']['rows']

                if selected_rows:
                    walk_df = walk_df.iloc[selected_rows]                
            
            include_bus = st.toggle("通学圏全体を表示")

            walk_df = walk_df.replace({np.nan: None})          
        
            hand_picked_walk_schools = []
            for index, row in walk_df.iterrows():
                if not (pd.isnull(row['Latitude']) or pd.isnull(row['Longitude'])):
                    try:
                        lat = float(row['Latitude'])
                        lng = float(row['Longitude'])
                    except ValueError:
                        print(f"Invalid coordinates for {row['title']}, skipping this entry.")
                        continue
                    
                    if not include_bus:
                        row['list_of_type_2_elem'] = []
                    school_info = {
                        "title": row['School Name'], 
                        "lat": row['Latitude'],            
                        "lng": row['Longitude'],           
                        "url": row['URL'],
                        "catchment": row['list_of_type_2_elem'],
                        "walk": row['list_of_type_5_elem'] 
                    }
                    
                    # Append each school_info dictionary to the schools list
                    hand_picked_walk_schools.append(school_info)
                else:
                    print(f"Skipping school: {row['School Name']} due to missing lat/lng")
            
            jscomponent(my_schools_value=hand_picked_walk_schools, height=1200)   
            
            catchment_df = merged_df[merged_df['catching_the_address'] == True]
            '徒歩ではないけど通学可能な学校'
            st.dataframe(catchment_df[columns_to_display], hide_index=True)
    render_tab_1() 

with tabs[2]:

    @st.fragment
    def render_tab_2():
        schools_with_walk_area_overwrap = [[198,212], [63,212], [246, 2477], [217,246], [92,157], [82,134], [124,134], [79,124,134], [79,134], [82,124,134], [67,124], [67,124,134], [79,124], [92,146,157], [70,146], [70,92,146], [70,138,228], [138,228], [70,146,228], [70,138,146], [138,146,228], [67,146], [67,70,124], [71,138,228], [68,138], [8,148,171], [8,148], [11,24,143], [11,24,143,171], [17,142,171,221], [142,171,221], [9,142,171,221], [9,142,171], [9,17,142,171,221], [9,17,142,221], [9,17,18,142,221], [17,142], [17,142,221], [17,171,221], [17,171], [17,18,142], [17,18,142,221], [191,247], [220,245], [13,127], [12,127], [208,223], [223,235], [208,223,235], [218,239], [106,158], [86,158], [86,106,158], [52,86,158], [28,52,158], [28,149], [52,149], [35,149], [28,33,149], [28,35,149], [111,165], [189,197], [225,230], [211,225], [211,225,230], [38,54,104,154], [38,54,154], [36,42,132,195], [48,154,195], [36,48,154,195], [48,132,195], [36,48,132,195], [36,132,195], [34,36,132], [36,42,132], [34,36,42,132], [34,144,174], [34,131,144,174], [34,39,44,132], [34,36,39,132], [34,44,132], [36,132], [36,39,132], [39,123], [39,44,123], [39,44,132], [39,123,129], [37,39,118,123,166], [37,39,123,129], [37,39,118,123], [39,118,123], [39,118,123,166], [32,131,174], [29,118,131,166], [37,118,131,166], [29,37,118,131,166], [43,118,131,166], [32,131,144,174], [32,34,131,144,174], [32,34,39,131,144,174], [32,39,131,144,174], [34,39,131,144,174], [32,131,166,174], [29,118,166], [29,118,131], [29,49,118,131], [49,131], [28,131,144,174], [28,144,174], [28,149,174], [28,34,131,144,174], [28,34,131,144], [28,34,144,174], [28,34,149], [28,144], [33,149], [28,33,50,149], [28,50,149], [53,149], [28,53,149], [49,118,131], [23,136], [25,136], [22,23,136], [22,25,136], [25,136,253], [22,25,136,253], [22,23,136,253], [136,253], [22,136,253], [9,25,136,253], [9,22,25,136,253], [9,25,142,253], [25,142,253], [18,142,253], [17,18,142,253], [9,17,18,142,221,253], [9,18,142,221,253], [9,25,142,221,253], [25,142,221,253], [9,142,221,253], [9,17,25,142,221], [9,25,142,221], [9,25,142], [9,25,136], [9,136], [6,9,142], [6,9,142,221], [6,9,17,142,221], [9,142,221], [6,9,142,171,221], [6,143], [6,142,221], [6,143,171], [11,143,171], [6,24,143], [101,143], [6,9,143], [43,166], [43,118,166], [43,101,143], [43,143], [14,143], [37,118,166], [37,39,118,166], [47,166], [47,123,166], [15,143], [15,24,143], [123,129], [47,125], [123,125,129], [123,125], [46,123,125,130], [46,125,130], [125,130], [94,128], [94,128,150], [150,209], [94,150], [40,151], [27,151], [51,151], [41,123,130], [123,125,130], [41,123,125,130], [27,125,151], [48,154], [30,141], [30,123,141], [41,123,141], [41,123,130,141], [30,41,123,141], [39,123,141], [46,123,130], [123,129,166], [36,39,123,141], [36,39,123,132], [36,123,132], [30,36,141], [30,36,123,141], [36,123,141], [30,36,132,141,195], [30,36,141,195], [38,154,195], [45,154,195], [38,54,154,195], [54,58,154], [45,54,154], [45,154], [58,154], [38,54,58,154], [2,222,471], [222,230], [194,222], [194,222,230], [64,164], [107,164], [64,107,164], [188,248], [231,248], [213,224], [219,231], [231,233], [110,164], [107,110,164], [160,190], [108,152], [87,96,160], [55,90,152], [55,83,90,152], [85,107,109,164], [88,97,162], [85,109,162], [105,159], [88,162], [97,162], [95,159], [75,83,133], [83,133], [87,96,105,160], [87,96,159], [55,75,83,90,152], [55,75,83,90,133], [72,147], [89,100,147], [55,83,90,147,152], [83,89,147,152], [72,89,147], [93,147], [76,147], [76,147,150], [72,147,150], [75,83,133,147], [147,150,209], [76,147,150,209], [77,128], [77,128,242], [62,77,128], [89,93,100,147], [94,128,242], [102,139], [73,140], [73,140,145], [66,73,140,145], [66,140,145], [66,74,145], [74,145], [66,74,78,145], [74,78,155], [74,78,145], [74,78], [74,155], [66,74,78,155], [66,145], [66,78,145], [71,138], [71,138,146], [66,74,78], [92,146], [74,78,92], [78,92,146], [78,91,156], [74,78,156], [80,91,156], [98,161], [59,161], [115,207], [84,161], [59,84,161], [114,186], [61,114,186], [81,161], [81,98,161], [80,98,161], [81,156], [81,91,156], [81,84,161], [61,186], [99,186], [216,243], [115,216,243], [2,432,476], [24,312,228], [216,232,243], [232,243], [23,212,223], [23,224,312,223], [2,321,222,312,228], [214,236], [192,207], [237,240], [237,244], [2,361,120,212,223], [2,321,120,212,223], [1,120,212,223], [2,441,120,212,223], [1,222,312,228]]


        def compute_overlapping_area(polygon_list):
            # Ensure we have at least two polygons to compute the overlap
            if len(polygon_list) < 2:
                return None
            
            overlap = Polygon(polygon_list[0])
        
            # Iteratively compute the intersection with the remaining polygons
            for polygon_points in polygon_list[1:]:
                polygon = Polygon(polygon_points)
                overlap = overlap.intersection(polygon)

            #print(overlap)
            # Return the overlapping area (or None if no overlap)
            if overlap.is_empty:
                return None
            return overlap

        overwrapping_schools = []
        for school_ids in schools_with_walk_area_overwrap:
            if isinstance(school_ids, int):
                school_ids = [school_ids]  # Wrap single integers in a list


            overwrapping_df = merged_df[merged_df['school_id'].isin(school_ids)]
            #overrapping_area = # overwrapping areas from polygons from row['list_of_type_5_elem'] 


            polygons = []
            for index, row in overwrapping_df.iterrows():
                polygons = polygons + parse_multiple_polygons(row['list_of_type_5_elem'])
            
            #print(school_ids)
            overlapping_area = compute_overlapping_area(polygons)
            lat_lng_list = []
            if isinstance(overlapping_area, MultiPolygon):
                # Handle each polygon in the MultiPolygon
                for polygon in overlapping_area.geoms:
                    lat_lng_list.extend([(y, x) for x, y in polygon.exterior.coords])

            elif isinstance(overlapping_area, Polygon):
                # Handle the single Polygon case
                lat_lng_list = [(y, x) for x, y in overlapping_area.exterior.coords]


    #        lat_lng_list = [(y, x) for x, y in overrapping_area.exterior.coords]


            #print(lat_lng_list)
            formatted_string = ", ".join([f"{lng} {lat} 0 0" for lat, lng in lat_lng_list])
            formatted_string = f"['{formatted_string}']"
            #print(formatted_string)

            for index, row in overwrapping_df.iterrows():
                if not (pd.isnull(row['Latitude']) or pd.isnull(row['Longitude'])):
                    try:
                        lat = float(row['Latitude'])
                        lng = float(row['Longitude'])
                    except ValueError:
                        print(f"Invalid coordinates for {row['title']}, skipping this entry.")
                        continue
                    

                    school_info = {
                        "title": row['School Name'], 
                        "lat": row['Latitude'],            
                        "lng": row['Longitude'],           
                        "url": row['URL'],
                        "catchment": [],
                        "walk": formatted_string#row['list_of_type_5_elem']
                    }
                    
                    # Append each school_info dictionary to the schools list
                    overwrapping_schools.append(school_info)
                else:
                    print(f"Skipping school: {row['School Name']} due to missing lat/lng")
            
        jscomponent(my_schools_value=overwrapping_schools, height=1200)   
    render_tab_2()

with tabs[3]:
    @st.fragment
    def render_tab_3():
        components.iframe("https://storymaps.arcgis.com/stories/f31df73c7bba4fae95b6da3cb920c34d?", height=1200)
    render_tab_3()

with tabs[4]:
    @st.fragment
    def render_tab_4():
        components.iframe("https://maps.calgary.ca/language/", height=1200)
    render_tab_4()


with tabs[5]:
    st.caption("https://www.calgary.ca/research/ward-reports.html")
    st.image("proud.png")
    st.image("qol.png")

with tabs[6]:
    @st.fragment
    def render_tab_6():
        components.iframe("https://www.arcgis.com/apps/dashboards/09ef336a4b8d4f8b98045821edea71a2", height=1200)
    render_tab_6()


with tabs[7]:
    @st.fragment
    def render_tab_7():
        components.iframe("https://housesigma.com/ab/map/?status=for-sale,sold&lat=50.991638&lon=-114.093939&zoom=11", height=1200)
    render_tab_7()


if False:
    # Assuming you already have your map function defined:
    def map(data, lat, lon, zoom):
        st.write(
            pdk.Deck(
                #map_style="mapbox://styles/mapbox/light-v9",
                map_style="road",
                initial_view_state={
                    "latitude": lat,
                    "longitude": lon,
                    "zoom": zoom,
                    "pitch": 500,
                },
                views=pdk.View(type="PerspectiveView", controller=True)
                #layers=[
                ##    pdk.Layer(
                #       "HexagonLayer",
                #       data=data,
                #       get_position=["lon", "lat"],
                #       radius=100,
                #       elevation_scale=10,
                #       elevation_range=[0, 1000],
                #       pickable=True,
                #       extruded=True,
                #   ),
                #],
            )
        )

    # Create dummy data for each city with 'lon' and 'lat' values
    data_calgary = pd.DataFrame({
        'lon': [-114.0719],
        'lat': [51.0447]
    })

    data_vancouver = pd.DataFrame({
        'lon': [-123.1216],
        'lat': [49.2827]
    })

    data_victoria = pd.DataFrame({
        'lon': [-123.3656],
        'lat': [48.4284]
    })

    # Call the function for each city
    city_columns = st.columns(3)
    with city_columns[0]:
        # Calgary
        st.header("Calgary")
        map(data_calgary, lat=51.0447, lon=-114.0719, zoom=10)

    with city_columns[1]:
        # Vancouver
        st.header("Vancouver")
        map(data_vancouver, lat=49.2827, lon=-123.1216, zoom=10)
        "Maple Ridge, North Vancouver, Coquitlam, White Rock"

    with city_columns[2]:
        # Victoria
        st.header("Victoria")
        map(data_victoria, lat=48.4284, lon=-123.3656, zoom=10)

#IMPORT STATEMENTS
import pandas as pd
import folium
from collections import defaultdict
from folium.features import CustomIcon
import os
from datetime import datetime
import pytz

#CREATE DATAFRAME FROM FILE.  FOR TESTING/DEV WORK, DOWNLOADED LOCALLY BUT WHEN PUSHED INTO NIGHTLY RUN WILL POIN TO FILE AT 
#Data found at https://www.cleansheethockey.com/databases/2025-mens-transfer-portal
#Used with permission from @sydneyisawolf at Clean Sheet Hockey account (@CleanSheetHKY)
#cleansheethockey.com
# Load data 
 

#df_transfers = pd.read_excel("Division I NCAA Men's Portal 2025.xlsx")
df_transfers = pd.read_csv("https://docs.google.com/spreadsheets/d/10YakMFgL26THDHzK7pn688RYimMofcmUwGQNpTzs1Hc/export?format=csv&gid=0")
df_schoollatlongs = pd.read_excel("NCAASchoolLatLong.xlsx")
df_transfers = df_transfers.dropna(subset=['Player'])

# Join lat/longs
df_full = pd.merge(df_transfers, df_schoollatlongs, left_on='2024/25 TEAM', right_on='Team', how='left')
df_full = pd.merge(df_full, df_schoollatlongs, left_on='DESTINATION TEAM', right_on='Team', how='left')

# Rename columns
df_full.rename(columns={
    'Lat_x': 'Lat 2024/25 TEAM',
    'Long_x': 'Long 2024/25 TEAM',
    'Lat_y': 'Lat DESTINATION TEAM',
    'Long_y': 'Long DESTINATION TEAM',
    'Player': 'Player Name'
}, inplace=True)

# Select necessary columns
df_full = df_full[['Player Name', '2024/25 TEAM', 'Lat 2024/25 TEAM', 'Long 2024/25 TEAM',
                   'DESTINATION TEAM', 'Lat DESTINATION TEAM', 'Long DESTINATION TEAM']]

# Fill and reset
df_full['DESTINATION TEAM'] = df_full['DESTINATION TEAM'].fillna('TBD')
df_full.reset_index(drop=True, inplace=True)

# Create map
m = folium.Map(location=[39.8283, -98.5795], zoom_start=3)

# Group messages by location
marker_data = defaultdict(list)
for _, row in df_full.iterrows():
    from_loc = (row['Lat 2024/25 TEAM'], row['Long 2024/25 TEAM'])
    marker_data[from_loc].append(f"{row['Player Name']} → {row['DESTINATION TEAM']}")
    
    if row['DESTINATION TEAM'] != 'TBD' and pd.notna(row['Lat DESTINATION TEAM']) and pd.notna(row['Long DESTINATION TEAM']):
        to_loc = (row['Lat DESTINATION TEAM'], row['Long DESTINATION TEAM'])
        marker_data[to_loc].append(f"{row['Player Name']} ← {row['2024/25 TEAM']}")

# Map team to location
team_lookup = {}
for _, row in df_full.iterrows():
    team_lookup[(row['Lat 2024/25 TEAM'], row['Long 2024/25 TEAM'])] = row['2024/25 TEAM']
    if row['DESTINATION TEAM'] != 'TBD' and pd.notna(row['Lat DESTINATION TEAM']) and pd.notna(row['Long DESTINATION TEAM']):
        team_lookup[(row['Lat DESTINATION TEAM'], row['Long DESTINATION TEAM'])] = row['DESTINATION TEAM']

# Add custom icon markers
for location, messages in marker_data.items():
    team_name = team_lookup.get(location, "Team")
    popup_html = f"<strong>{team_name}</strong><br>" + "<br>".join(messages)
    
    # Path to icon file
    icon_path = f"images/{team_name}.gif"
    
    # Check if icon exists, use fallback if not
    if os.path.isfile(icon_path):
        icon = CustomIcon(icon_image=icon_path, icon_size=(40, 40))
    else:
        # Optional: fallback to a default icon if image not found
        icon = folium.DivIcon(html='<div style="font-size: 24px; color: black;">❓</div>')
    folium.Marker(
        location=location,
        popup=folium.Popup(popup_html, max_width=300),
        icon=icon
    ).add_to(m)


# Save map
m.save("index.html")

# Set Central Time Zone (US/Central)
central_tz = pytz.timezone("US/Central")

# Get current time in Central Time zone
now_central = datetime.now(central_tz).strftime("%B %d, %Y %I:%M %p")

# Get current timestamp
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Prepare your top and bottom content
top_content = f"""
    <div style="font-size:12px; text-align:center; font-weight:bold; margin-bottom:10px;">
        Welcome to the NCAA 2025-26 NCAA Men's Ice Hockey Transfer Portal Map! This map shows player transfers between NCAA Mens Ice Hockey teams.  Click a team logo to see players arriving or leaving each team.  
        <br>
        Special Thanks to <a href='https://x.com/sydneyisawolf' target="_blank" >@sydneyisawolf</a> / <a href='https://x.com/CleanSheetHKY' target="_blank">@CleanSheetHKY</a> / <a href='https://www.cleansheethockey.com/' target="_blank">www.cleansheethockey.com</a> for providing data for this.  
        <br>
        <p style='text-align:center; font-size:12px;'>Last Updated: {now_central} (Central Time)</p>
    </div>
""" 

# Read the existing index.html content
with open("index.html", "r", encoding="utf-8") as f:
    html_content = f.read()

# Insert the new content at the right places
# Insert the top content right after the <body> tag
html_content = html_content.replace("<body>", f"<body>{top_content}", 1)
 

# Write the modified content back to the file
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

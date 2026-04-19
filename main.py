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
url = "https://docs.google.com/spreadsheets/d/1ZMgAFehVLUsOd-KEgQKgljeBk7pDN3PWdFnGC8o1x18/export?format=csv&gid=0"

df_transfers = pd.read_csv(url)
print('able to read')
df_schoollatlongs = pd.read_excel("NCAASchoolLatLong.xlsx") 
df_transfers = df_transfers.dropna(subset=['PLAYER']) 

df_transfers["2025-26 TEAM"] = df_transfers["2025-26 TEAM"].str.rstrip()
df_transfers["DESTINATION TEAM"] = df_transfers["DESTINATION TEAM"].str.rstrip()

print(df_transfers)

# Join lat/longs
df_full = pd.merge(df_transfers, df_schoollatlongs, left_on='2025-26 TEAM', right_on='Team', how='left')
df_full = pd.merge(df_full, df_schoollatlongs, left_on='DESTINATION TEAM', right_on='Team', how='left')

# Rename columns
df_full.rename(columns={
    'Lat_x': 'Lat 2025-26 TEAM',
    'Long_x': 'Long 2025-26 TEAM',
    'Lat_y': 'Lat DESTINATION TEAM',
    'Long_y': 'Long DESTINATION TEAM',
    'PLAYER': 'Player Name'
}, inplace=True)

# Select necessary columns
df_full = df_full[['Player Name', '2025-26 TEAM', 'Lat 2025-26 TEAM', 'Long 2025-26 TEAM',
                   'DESTINATION TEAM', 'Lat DESTINATION TEAM', 'Long DESTINATION TEAM']]

# Fill and reset
df_full['DESTINATION TEAM'] = df_full['DESTINATION TEAM'].fillna('TBD')
df_full.reset_index(drop=True, inplace=True)

# Create map
m = folium.Map(location=[39.8283, -98.5795], zoom_start=3)

# -------------------------------------------------
# Store incoming / outgoing popup rows
# -------------------------------------------------
marker_data = defaultdict(lambda: {"incoming": [], "outgoing": []})

for _, row in df_full.iterrows():

    player    = row["Player Name"]
    from_team = row["2025-26 TEAM"]
    to_team   = row["DESTINATION TEAM"]

    from_loc = (row["Lat 2025-26 TEAM"], row["Long 2025-26 TEAM"])

    # -------------------------------------------------
    # OUTGOING (RED)
    # -------------------------------------------------
    if to_team != "TBD":
        dest_icon_path = f"images/{to_team}.gif"
        dest_icon = (
            f"<img src='{dest_icon_path}' width='18' height='18'>"
            if os.path.isfile(dest_icon_path)
            else "❓"
        )
    else:
        dest_icon = "❓"

    marker_data[from_loc]["outgoing"].append(
        (from_team, player, to_team, dest_icon)
    )

    # -------------------------------------------------
    # INCOMING (GREEN)
    # -------------------------------------------------
    if (
        to_team != "TBD"
        and pd.notna(row["Lat DESTINATION TEAM"])
        and pd.notna(row["Long DESTINATION TEAM"])
    ):
        to_loc = (row["Lat DESTINATION TEAM"], row["Long DESTINATION TEAM"])

        source_icon_path = f"images/{from_team}.gif"
        source_icon = (
            f"<img src='{source_icon_path}' width='18' height='18'>"
            if os.path.isfile(source_icon_path)
            else "❓"
        )

        marker_data[to_loc]["incoming"].append(
            (player, from_team, to_team, source_icon)
        )

# -------------------------------------------------
# Team lookup
# -------------------------------------------------
team_lookup = {}

for _, row in df_full.iterrows():
    team_lookup[(row["Lat 2025-26 TEAM"], row["Long 2025-26 TEAM"])] = row["2025-26 TEAM"]

    if (
        row["DESTINATION TEAM"] != "TBD"
        and pd.notna(row["Lat DESTINATION TEAM"])
        and pd.notna(row["Long DESTINATION TEAM"])
    ):
        team_lookup[
            (row["Lat DESTINATION TEAM"], row["Long DESTINATION TEAM"])
        ] = row["DESTINATION TEAM"]

# -------------------------------------------------
# Build markers
# -------------------------------------------------
for location, data in marker_data.items():

    team_name = team_lookup.get(location, "Team")

    self_icon_path = f"images/{team_name}.gif"
    self_icon = (
        f"<img src='{self_icon_path}' width='18' height='18'>"
        if os.path.isfile(self_icon_path)
        else "❓"
    )

    incoming_html = ""
    for player, from_team, to_team, icon in sorted(data["incoming"]):
        incoming_html += f"""
        <div style='color:green; margin-bottom:2px; display:flex;
                    align-items:center; width:100%;'>

            <span style='width:20px;"'>{self_icon}</span>

            <span style=' padding-left:6px;'>
                {player}
            </span>

            <span style='padding-left:6px;text-align:center;'>
            {from_team}
            </span>

            <span style='width:20px;opacity:0.5; text-align:right;'>
                {icon}
            </span>

        </div>
        """

    outgoing_html = ""
    for from_team, player, to_team, icon in sorted(data["outgoing"]):
        outgoing_html += f"""
        <div style='color:red; margin-bottom:2px; display:flex;
                    align-items:center; width:100%;'>

            <span style='width:20px;opacity:0.5;'>{self_icon}</span>

            <span style=' padding-left:6px;'>
                {player} 
            </span>

            <span style='padding-left:6px;text-align:center;'>
              {to_team}
            </span>

            <span style='width:20px; text-align:right;'>
                {icon}
            </span>

        </div>
        """

    popup_html = f"""
    <div style='font-size:14px; min-width:275px;'>
        <strong style='font-size:16px;'>{team_name}</strong><br>
        <span style='color:green;'>Incoming: {len(data["incoming"])}</span><br>
        <span style='color:red;'>Outgoing: {len(data["outgoing"])}</span>
        <hr style='margin:4px 0;'>
        {incoming_html}
        <hr style='margin:3px 0;'>
        {outgoing_html}
    </div>
    """

    icon_path = f"images/{team_name}.gif"

    icon = (
        CustomIcon(icon_image=icon_path, icon_size=(40, 40))
        if os.path.isfile(icon_path)
        else folium.DivIcon(html="<div style='font-size:24px;'>❓</div>")
    )

    folium.Marker(
        location=location,
        popup=folium.Popup(popup_html, max_width=520),
        icon=icon
    ).add_to(m)

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

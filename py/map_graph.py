import pandas as pd
import folium

df = pd.read_csv('csv\\flats_data_coords.csv')

df['coords'] = df['coords'].str.replace("(", "").str.replace(")", "").str.replace("'", "")

df = df[df['coords'].notnull()]
df = df[df['coords'].str.contains(",")]

df[['latitude', 'longitude']] = df['coords'].str.split(",", expand=True)

df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

df = df.dropna(subset=['latitude', 'longitude'])

moscow_map = folium.Map(location=[55.751244, 37.618423], zoom_start=10)

for index, row in df.iterrows():
    folium.Marker([row['latitude'], row['longitude']],
                  popup=f"Price: {row['price']}, Rooms: {row['rooms']}").add_to(moscow_map)

moscow_map.save('moscow_flats_map.html')
moscow_map
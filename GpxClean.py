from os import listdir 
from os.path import join, isfile 
import argparse
import fiona

parser = argparse.ArgumentParser(description='Get filepaths.')
parser.add_argument('--path', '-P', type=str, 
                    help='Directory containing GPX files.')
parser.add_argument('--output', '-O', type=str, default='.',
                   help='Output file path')
args = parser.parse_args() 

files = listdir(args.path)
files = [join(args.path, f) for f in files if isfile(join(args.path, f))]
    
#Load all points into dataframe 
import gpxpy
import pandas as pd 
    
coords = []
for f in files:
    print(f)
    #fiona.open(f, layer='tracks')
    gpx_file = open(f, 'r')
    gpx = gpxpy.parse(gpx_file)
    for track in gpx.tracks: 
        for segment in track.segments: 
            for point in segment.points:
                coords.append([point.time, point.latitude, point.longitude, point.elevation])

cols = ['Time', 'Lat', 'Lon', 'Elev']
coords_df = pd.DataFrame(coords, columns=cols)

print(coords_df.head())
#print(coords_df.info())

#Remove duplicate points based on timestamp 
coords_df.drop_duplicates(subset='Time', inplace=True)
    
#Sort by time
coords_df.sort_values(by='Time', inplace=True) 

print(coords_df.info())

#Convert points into a GeoDataframe 
import geopandas as gpd
from shapely.geometry import Point

geom = [Point(xy) for xy in zip(coords_df.Lon, coords_df.Lat, coords_df.Elev)]
#coords_df.drop(['Lat', 'Lon'], axis=1)
crs = {'init': 'epsg:4326'}
coords_gdf = gpd.GeoDataFrame(coords_df, crs=crs, geometry=geom)

print(coords_gdf.info())
print(coords_gdf.head())

#Write points to file 
#note: to_file can't handle datetimes
schema = {
    'geometry': 'Point',
    'properties': {
        'Time': 'datetime',
        'Lat': 'float',
        'Lon': 'float',
        'Elev': 'float',
}}
#coords_gdf.to_file("points_cleaned.geojson", driver='GeoJSON', schema=schema)
#coords_gdf.to_file("cleaned.gpkg", layer='Track points', driver='GPKG', schema=schema)
#coords_gdf[['geometry','Lat','Lon','Elev']].to_file("points_cleaned.shp")

#Create linestrings
#[(x1, y1, z1), ... (xn, yn, zn)]
from shapely.geometry import LineString
from geopy.distance import vincenty 

ls_geom = []
ls_data = [] #[Start Time, End Time, Start Elev, End Elev, geometry] 
total_dist = 0

for i in range(0, coords_gdf.shape[0]-1):
    p0 = coords_gdf.iloc[i]
    p1 = coords_gdf.iloc[i+1]

    p0_geom = p0['geometry']
    p1_geom = p1['geometry']

    p0_coords = (p0_geom.y, p0_geom.x, p0_geom.z)
    p1_coords = (p1_geom.y, p1_geom.x, p1_geom.z)
    dist = vincenty(p0_coords, p1_coords).meters/1000

    if dist > 500: 
        print(dist)
    else: 
        line_data = [p0['Time'], p1['Time'], p0['Elev'], p1['Elev']]

        p0_coords = (p0_geom.x, p0_geom.y, p0_geom.z)
        p1_coords = (p1_geom.x, p1_geom.y, p1_geom.z)
        ls_data.append(line_data)
        ls_geom.append(LineString([p0_coords, p1_coords]))
        
        total_dist += dist 

print(total_dist)
print(total_dist)
print(total_dist)

#Creating GeoDataFrame for LineStrings
cols = ['Start Time', 'End Time', 'Start Elev', 'End Elev']
line_df = pd.DataFrame(ls_data, columns=cols)
line_gdf = gpd.GeoDataFrame(line_df, crs=crs, geometry=ls_geom)
print(line_gdf.head())

#Write lines to file 
#note: to_file can't handle datetimes, need schema
schema = {
    'geometry': 'LineString',
    'properties': {
        'Start Time': 'datetime',
        'End Time': 'datetime',
        'Start Elev': 'float',
        'End Elev': 'float',
}}
#line_gdf.to_file("lines_cleaned.geojson", driver='GeoJSON', schema=schema)
#line_gdf.to_file("cleaned.gpkg", layer='LineStrings (<500km gaps)', driver='GPKG', schema=schema)
#line_gdf[['geometry','Start Elev','End Elev']].to_file("lines_cleaned.shp")

#Calculate statistics
#Num points, total distance, elevations
#Countries visited, time spent per country 

#Visualize with matplotplib, Folium
#Visualize wholedataset 
#Visualize one country in particular 

import matplotlib.pyplot as plt

'''
ax = coords_gdf.plot(markersize=2)
line_gdf.plot(ax=ax)
plt.show()
'''

'''
#Sanity check: View points as one LineString
coords = zip(coords_gdf.Lon, coords_gdf.Lat, coords_gdf.Elev)
coords_ls = LineString(coords)
ax = coords_gdf.plot()
gpd.plotting.plot_linestring_collection(ax=ax, geoms=[coords_ls])
plt.show()
'''

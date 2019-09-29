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
    
points = []
for f in files:
    print(f)
    #fiona.open(f, layer='tracks')
    gpx_file = open(f, 'r')
    gpx = gpxpy.parse(gpx_file)
    for track in gpx.tracks: 
        for segment in track.segments: 
            for point in segment.points:
                points.append([point.time, point.latitude, point.longitude, point.elevation])

cols = ['Time', 'Lat', 'Lon', 'Elev']
points_df = pd.DataFrame(points, columns=cols)

print(points_df.head())
#print(points_df.info())

#Remove duplicate points based on timestamp 
points_df.drop_duplicates(subset='Time', inplace=True)
    
#Sort by time
points_df.sort_values(by='Time', inplace=True) 

print(points_df.info())

#Convert points into a GeoDataframe 
import geopandas as gpd
from shapely.geometry import Point

geom = [Point(xy) for xy in zip(points_df.Lon, points_df.Lat, points_df.Elev)]
#points_df.drop(['Lat', 'Lon'], axis=1)
crs = {'init': 'epsg:4326'}
points_gdf = gpd.GeoDataFrame(points_df, crs=crs, geometry=geom)

print(points_gdf.info())
print(points_gdf.head())

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
#points_gdf.to_file("points_cleaned.geojson", driver='GeoJSON', schema=schema)
#points_gdf.to_file("cleaned.gpkg", layer='Track points', driver='GPKG', schema=schema)
#points_gdf[['geometry','Lat','Lon','Elev']].to_file("points_cleaned.shp")

#Create linestrings
#[(x1, y1, z1), ... (xn, yn, zn)]
from shapely.geometry import LineString
from geopy.distance import vincenty 

ls_geom = []
ls_data = [] #[Start Time, End Time, Start Elev, End Elev, geometry] 
total_dist = 0

for i in range(0, points_gdf.shape[0]-1):
    p0 = points_gdf.iloc[i]
    p1 = points_gdf.iloc[i+1]

    p0_geom = p0['geometry']
    p1_geom = p1['geometry']

    p0_points = (p0_geom.y, p0_geom.x, p0_geom.z)
    p1_points = (p1_geom.y, p1_geom.x, p1_geom.z)
    dist = vincenty(p0_points, p1_points).meters/1000

    if dist > 500: 
        print(dist)
    else: 
        line_data = [p0['Time'], p1['Time'], p0['Elev'], p1['Elev']]

        p0_points = (p0_geom.x, p0_geom.y, p0_geom.z)
        p1_points = (p1_geom.x, p1_geom.y, p1_geom.z)
        ls_data.append(line_data)
        ls_geom.append(LineString([p0_points, p1_points]))
        
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

import folium
pointlist = zip(points_gdf.Lat, points_gdf.Lon)
fmap = folium.Map(location=[0,0], zoom_start=1)
folium.PolyLine(pointlist,color='red', weight=2, opacity=1).add_to(fmap)
fmap.save('test.html')
'''
import matplotlib.pyplot as plt
ax = points_gdf.plot(markersize=2)
line_gdf.plot(ax=ax)
plt.show()
'''

'''
#Sanity check: View points as one LineString
points = zip(points_gdf.Lon, points_gdf.Lat, points_gdf.Elev)
points_ls = LineString(points)
ax = points_gdf.plot()
gpd.plotting.plot_linestring_collection(ax=ax, geoms=[points_ls])
plt.show()
'''

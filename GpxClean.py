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

if __name__ == "__main__":
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

    cols = ['Time', 'Latitude', 'Longitude', 'Elevation']
    coords_df = pd.DataFrame(coords, columns=cols)

    print(coords_df.head())
    print(coords_df.info())

    #Remove duplicate points based on timestamp 
    coords_df.drop_duplicates(subset='Time', inplace=True)

    print(coords_df.info())

    #Convert into a GeoDataframe 
    import geopandas as gpd
    from shapely.geometry import Point

    geom = [Point(xy) for xy in zip(coords_df.Longitude, coords_df.Latitude)]
    coords_df.drop(['Latitude', 'Longitude'], axis=1)
    crs = {'init': 'epsg:4326'}
    coords_gdf = gpd.GeoDataFrame(coords_df, crs=crs, geometry=geom)

    print(coords_df.head())
    print(coords_df.info())

    #Create linestrings
    #[(y1, x1), ... (yn, xn)]

    #Calculate statistics
    #Num points, total distance, elevations
    #Countries visited, time spent per country (spatial join/group by) 

    #Visualize with matplotplib, Folium
    #Visualize wholedataset 
    #Visualize one country in particular 
    import matplotlib.pyplot as plt
    coords_gdf.plot()
    plt.show()


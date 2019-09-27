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

    cols = ['Time', 'Lat', 'Lon', 'Elev']
    coords_df = pd.DataFrame(coords, columns=cols)

    print(coords_df.head())
    print(coords_df.info())

    #Remove duplicate points based on timestamp 
    coords_df.drop_duplicates(subset='Time', inplace=True)

    print(coords_df.info())

    #Convert into a GeoDataframe 
    import geopandas as gpd
    from shapely.geometry import Point

    geom = [Point(xy) for xy in zip(coords_df.Lon, coords_df.Lat)]
    coords_df.drop(['Lat', 'Lon'], axis=1)
    crs = {'init': 'epsg:4326'}
    coords_gdf = gpd.GeoDataFrame(coords_df, crs=crs, geometry=geom)
    coords_gdf.sort_values(by='Time', inplace=True) 

    print(coords_df.head())
    print(coords_df.info())

    #Create linestrings
    #[(x1, y1, z1), ... (xn, yn, zn)]
    #TODO: Add elevations 
    #TODO: Split linestrings where distances are large (500-1000km?)
    #TODO: Import linestrings into GeoDataframe 
    from shapely.geometry import LineString
    coords = zip(coords_gdf.Lon, coords_gdf.Lat)
    coords_ls = LineString(coords)

    #Calculate statistics
    #Num points, total distance, elevations
    #Countries visited, time spent per country 

    #Visualize with matplotplib, Folium
    #Visualize wholedataset 
    #Visualize one country in particular 
    import matplotlib.pyplot as plt
    ax = coords_gdf.plot()
    gpd.plotting.plot_linestring_collection(ax=ax, geoms=[coords_ls])
    plt.show()


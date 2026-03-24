import geopandas as gpd

gdf = gpd.read_file('output/beaching_hotspots.geojson')
gdf.to_file('output/tiles/beaching_hotspots.gpkg', driver='GPKG')
print(f'Saved GeoPackage: {len(gdf)} features')
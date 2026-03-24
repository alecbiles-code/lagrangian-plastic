import geopandas as gpd
cvi = gpd.read_file('data/coastlines/cvi/CVI/GULF/GULF.shp')
print(cvi.columns)
cvi.to_parquet('data/coastlines/cvi_gulf.parquet')
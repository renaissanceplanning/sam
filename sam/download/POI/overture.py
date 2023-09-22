# Beginings of an Oveture Places Downloader
# TODO fully implement, and recode the 700 categories

import duckdb 
import pandas as pd
import geopandas as gpd

from rputils import make_path

data_dir = make_path(
    'D:/Renaissance Planning Group',
    'BCDCOG Berkeley Charleston Dorchester Council of Governments - LCRT_TOD_Phase2',
    'tech_group/data/RAW'
    )

study_area = gpd.read_file(
    make_path(data_dir, 'full_mask.shp')    
    ).to_crs('WGS84')

db = duckdb.connect()

db.execute(
       """
       INSTALL spatial;
       INSTALL httpfs;
       LOAD spatial;
       LOAD httpfs;
       SET s3_region='us-west-2';
       """
       )
 
query =  f"""
     SELECT
         type,           
         json_extract_string(names, '$.common[0].value') as name,
         json_extract_string(categories, '$.main') as category_main,
         confidence,
         geometry
     FROM 
         read_parquet('s3://overturemaps-us-west-2/release/2023-07-26-alpha.0/theme=places/type=*/*', filename=true, hive_partitioning=1)     
     WHERE
         bbox.minX > {study_area.total_bounds[0]} and 
         bbox.maxX < {study_area.total_bounds[2]} and 
         bbox.minY > {study_area.total_bounds[1]} and 
         bbox.maxY < {study_area.total_bounds[3]};
  """

db.execute(query)

df = db.df()

df['geometry'] = df['geometry'].apply(bytes)

gdf = gpd.GeoDataFrame(
    df, geometry=gpd.GeoSeries.from_wkb(df['geometry'].apply(bytes)),
    crs='EPSG:4326'
    )

len(gdf['category_main'].unique())

gdf.to_file(make_path(data_dir, "oveture_test.shp"))
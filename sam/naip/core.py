import os
import requests
import geopandas as gpd
import rasterio as rio

from rputils import make_path
from math import floor, ceil
from tqdm import tqdm
from glob import glob
from rasterio.merge import merge

# TODO set to use temp

routes = gpd.read_file(
    make_path(
        "D:/Renaissance Planning Group",
        "District One - TWO_17_DW_BRT_Feasibility_Study",
        "tech_group","data", "INTERIM","Highlight",
        "BRTRoutes_HalfMileBuffer.shp"
    )
).to_crs(102100)

test_out_dir = make_path("D:/Renaissance Planning Group",
                         "District One - TWO_17_DW_BRT_Feasibility_Study",
                         "tech_group","data","RAW","naip")

route = routes.loc[routes.RouteName == "I-75"]

url = (r"https://naip.imagery1.arcgis.com/arcgis/rest/"
       r"services/NAIP/ImageServer/exportImage?")

def mosaic_naip(dir, out_dir, out_name):
    """Mosaics NAIP imagery chunks into a single GeoTIFF file.

    Args:
    dir (str): Path to the directory containing NAIP imagery chunks.
    out_dir (str): Path to the output directory for the mosaicked file.
    out_name (str): Desired filename for the output mosaic (without extension).

    Returns:
    None

    Raises:
    FileNotFoundError: If any input chunks are not found.
    RuntimeError: If any other errors occur during processing.
    """
    search_criteria = "*_chunk_*.tif"
    query = make_path(dir, search_criteria)
    chunks = glob(query)
    
    to_mosaic = []
    for chunk in tqdm(chunks):
        try:
            img = rio.open(chunk)
            to_mosaic.append(img)
        except:
            print(f"Failed with {chunk}")
            
    mosaic, out_trans = merge(to_mosaic)
    out_meta = img.meta.copy()
    
    out_meta.update({
        "driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": out_trans,
        "crs": img.meta['crs'] 
    })
    
    out_file = make_path(out_dir, f"{out_name}.tif")
    
    with rio.open(out_file, "w", **out_meta) as dest:
        dest.write(mosaic)
    
    for img in to_mosaic:
        img.close()
        
    for chunk in tqdm(chunks):
        os.remove(chunk)

def fetch_naip(gdf, out_dir, out_name):
    """Fetches NAIP imagery for a given geometry and mosaics it if necessary.

    Args:
    gdf (GeoDataFrame): A GeoDataFrame containing the geometry for which to fetch imagery.
    out_dir (str): Path to the output directory for the fetched imagery.
    out_name (str): Desired filename for the output imagery (without extension).

    Returns:
    None

    Raises:
    requests.exceptions.RequestException: If any errors occur during the image download process.
    RuntimeError: If any other errors occur during processing.

    Notes:
    - The function assumes the existence of a global variable url containing the base URL for the NAIP imagery service.
    - If the bounding box of the geometry exceeds 2000x2000 pixels, the function fetches the imagery in chunks and mosaics them together.
    """
    minX = gdf.total_bounds[0]
    maxX = gdf.total_bounds[2]
    minY = gdf.total_bounds[1]
    maxY = gdf.total_bounds[3]

    width = floor(maxX - minX)
    height = floor(maxY - minY)
    
    if width > 2000 or height > 2000:
        nrow = ceil(height / 2000) + 1
        ncol = ceil(width / 2000) + 1
        nchunks = nrow * ncol
        
        chunk_bboxs = []
        for col in range(int(ncol)):
            for row in range(int(nrow)):
                chunk_min_x = minX + (2000 * (col))
                chunk_max_x = minX + (2000 * (col+1))
                chunk_min_y = minY + (2000 * (row))
                chunk_max_y = minY + (2000 * (row + 1))
                
                chunk_bb = (f"{chunk_min_x}, {chunk_min_y},"
                            f"{chunk_max_x}, {chunk_max_y}")
                chunk_bboxs.append(chunk_bb)
                
        print(f"Grabbing imagrey in {nchunks} chunks")
        
        chunk_num = 1
        for chunk in tqdm(chunk_bboxs):
            params = {
                "f": "image",
                "bbox": chunk,
                "size": f"2000, 2000",
                "imageSR": 102100,
                "format": "tiff",
            }

            response = requests.get(url=url, 
                                    params=params, 
                                    allow_redirects=True)
            
            out_path = make_path(
                out_dir,
                f'{out_name}_chunk_{chunk_num}.tif'
            )

            with open(out_path, mode='wb') as localfile:
                localfile.write(response.content)
                
            chunk_num += 1
            
        mosaic_naip(
            dir = out_dir,
            out_dir=out_dir,
            out_name=out_name
        )    
    else:
        size = f"{width}, {height}"
        bbox_str = f"{minX}, {minY}, {maxX}, {maxY}"
        
        params = {
            "f": "image",
            "bbox": bbox_str,
            "size": size,
            "imageSR": 102100,
            "format": "tiff",
        }

        response = requests.get(url=url, 
                                params=params, 
                                allow_redirects=True)
        
        out_path = make_path(
                out_dir,
                f'{out_name}_.tif'
            )

        with open(out_path, mode='wb') as localfile:
            localfile.write(response.content)



if __name__ == "__main__":
    fetch_naip(
        gdf = route,
        out_dir=test_out_dir,
        out_name="func_test"
    )
"""
NLCD data manipulation and analysis utilities.

This module provides tools for working with downloaded NLCD rasters,
including clipping, reclassification, and zonal statistics.
"""

import geopandas as gpd
import rasterio
from rasterio.mask import mask
from pathlib import Path
import numpy as np
from typing import Dict, List, Optional

# Import the download function from the download module
from sam.download.nlcd import download_nlcd as _download_nlcd


class NLCD:
    """
    Class for working with NLCD raster data.
    
    Handles operations like:
    - Clipping to area of interest
    - Reclassifying land cover categories
    - Calculating statistics
    - Extracting impervious surface percentages
    """
    
    def __init__(self, raster_path: Path):
        """
        Initialize NLCD object from a raster file.
        
        Args:
            raster_path: Path to NLCD GeoTIFF file
        """
        self.path = Path(raster_path)
        self.src = None
        self._load_raster()
    
    def _load_raster(self):
        """Load the raster file."""
        self.src = rasterio.open(self.path)
        self.crs = self.src.crs
        self.bounds = self.src.bounds
        self.transform = self.src.transform
    
    @classmethod
    def from_download(
        cls,
        geoid: List[str],
        year: int,
        dataset: str = 'land_cover',
        output_dir: Optional[Path] = None
    ):
        """
        Download NLCD data and create an NLCD object.
        
        Args:
            geoid: List of county FIPS codes
            year: Target year
            dataset: NLCD dataset type
            output_dir: Where to save downloaded file
            
        Returns:
            NLCD object ready for manipulation
        """
        # Download the data
        downloaded_path = _download_nlcd(geoid, year, dataset, output_dir)
        
        # Extract if it's a zip (would need to implement)
        # For now, assume user extracts manually
        print("Please extract the downloaded zip file and call NLCD(path_to_tif)")
        
        return cls(downloaded_path)
    
    def clip_to_geometry(
        self,
        geometry: gpd.GeoDataFrame,
        output_path: Optional[Path] = None
    ) -> 'NLCD':
        """
        Clip NLCD raster to a geometry.
        
        Args:
            geometry: GeoDataFrame with area of interest
            output_path: Where to save clipped raster
            
        Returns:
            New NLCD object with clipped data
        """
        # Reproject geometry to match raster CRS
        geom_reproj = geometry.to_crs(self.crs)
        
        # Clip the raster
        out_image, out_transform = mask(
            self.src,
            geom_reproj.geometry,
            crop=True,
            filled=True
        )
        
        # Update metadata
        out_meta = self.src.meta.copy()
        out_meta.update({
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform
        })
        
        # Save if path provided
        if output_path:
            output_path = Path(output_path)
            with rasterio.open(output_path, "w", **out_meta) as dest:
                dest.write(out_image)
            
            return NLCD(output_path)
        else:
            # Return in-memory version (would need more implementation)
            return self
    
    def reclassify(
        self,
        reclassification_dict: Dict[int, int],
        output_path: Optional[Path] = None
    ) -> 'NLCD':
        """
        Reclassify NLCD values.
        
        Args:
            reclassification_dict: Mapping of old values to new values
                Example: {21: 1, 22: 1, 23: 1, 24: 1}  # All developed to 1
            output_path: Where to save reclassified raster
            
        Returns:
            New NLCD object with reclassified data
        """
        # Read the data
        data = self.src.read(1)
        
        # Reclassify
        reclassified = np.copy(data)
        for old_val, new_val in reclassification_dict.items():
            reclassified[data == old_val] = new_val
        
        # Save if path provided
        if output_path:
            output_path = Path(output_path)
            out_meta = self.src.meta.copy()
            
            with rasterio.open(output_path, "w", **out_meta) as dest:
                dest.write(reclassified, 1)
            
            return NLCD(output_path)
        else:
            return self
    
    def get_land_cover_stats(self) -> Dict[int, Dict[str, float]]:
        """
        Calculate statistics for each land cover class.
        
        Returns:
            Dictionary with class codes and their pixel counts and percentages
        """
        data = self.src.read(1)
        unique, counts = np.unique(data[data != self.src.nodata], return_counts=True)
        
        total_pixels = counts.sum()
        
        stats = {}
        for value, count in zip(unique, counts):
            stats[int(value)] = {
                'count': int(count),
                'percentage': (count / total_pixels) * 100,
                'area_sq_m': count * abs(self.transform.a * self.transform.e)
            }
        
        return stats
    
    def calculate_impervious_percentage(self) -> float:
        """
        Calculate average impervious percentage for the raster.
        
        Returns:
            Average impervious percentage (0-100)
            
        Note:
            Only works with NLCD impervious dataset
        """
        data = self.src.read(1)
        valid_data = data[data != self.src.nodata]
        
        return float(np.mean(valid_data))
    
    def to_vector(
        self,
        output_path: Optional[Path] = None
    ) -> gpd.GeoDataFrame:
        """
        Convert raster to vector polygons.
        
        Args:
            output_path: Where to save the shapefile (optional)
            
        Returns:
            GeoDataFrame with polygonized raster
        """
        # This would use rasterio.features.shapes
        # Implementation left as TODO
        raise NotImplementedError("Vector conversion not yet implemented")
    
    def close(self):
        """Close the raster file."""
        if self.src:
            self.src.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Land cover classification mappings
NLCD_CLASSES = {
    11: "Open Water",
    12: "Perennial Ice/Snow",
    21: "Developed, Open Space",
    22: "Developed, Low Intensity",
    23: "Developed, Medium Intensity",
    24: "Developed, High Intensity",
    31: "Barren Land",
    41: "Deciduous Forest",
    42: "Evergreen Forest",
    43: "Mixed Forest",
    52: "Shrub/Scrub",
    71: "Grassland/Herbaceous",
    81: "Pasture/Hay",
    82: "Cultivated Crops",
    90: "Woody Wetlands",
    95: "Emergent Herbaceous Wetlands"
}

# Common reclassification schemes
DEVELOPED_RECLASSIFICATION = {
    21: 1, 22: 1, 23: 1, 24: 1,  # All developed
}

NATURAL_RECLASSIFICATION = {
    41: 1, 42: 1, 43: 1,  # All forest
    90: 2, 95: 2,          # All wetlands
}
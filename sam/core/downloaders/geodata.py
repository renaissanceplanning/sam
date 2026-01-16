"""
GeoData downloader for GIS data (returns GeoDataFrame).
"""

from io import BytesIO
import geopandas as gpd
import requests

from sam.core.downloader import BaseDownloader


class GeoDataDownloader(BaseDownloader):
    """
    Downloads GIS data and returns GeoDataFrame.

    Default implementation handles GeoJSON and formats readable by
    geopandas.read_file(). Override _process_response() for custom formats.

    Attributes:
        SUPPORTED_FORMATS (list): File formats this downloader supports

    Examples:
        >>> class MyGeoDownloader(GeoDataDownloader):
        ...     def _validate_parameters(self):
        ...         if not self.kwargs.get('state'):
        ...             raise ValueError("state is required")
        ...
        ...     def _build_url(self):
        ...         state = self.kwargs['state']
        ...         return f"https://example.com/data/{state}.geojson"
        ...
        >>> downloader = MyGeoDownloader(state='NC')
        >>> gdf = downloader.download()
        >>> print(type(gdf))
        <class 'geopandas.geodataframe.GeoDataFrame'>
    """

    SUPPORTED_FORMATS = ['geojson', 'shapefile', 'geopackage']

    def _process_response(self, response: requests.Response) -> gpd.GeoDataFrame:
        """
        Parse response into GeoDataFrame.

        Default implementation assumes GeoJSON or format readable by
        geopandas.read_file() from BytesIO. Override for custom parsing.

        Args:
            response: HTTP response with geospatial data

        Returns:
            GeoDataFrame with geospatial features

        Raises:
            ValueError: If data cannot be parsed

        Examples:
            >>> def _process_response(self, response):
            ...     # Custom parsing for specific format
            ...     return gpd.read_file(
            ...         BytesIO(response.content),
            ...         driver='GeoJSON',
            ...         **self.kwargs
            ...     )
        """
        self._log("Parsing geospatial data...")

        try:
            gdf = gpd.read_file(BytesIO(response.content), **self.kwargs)
            self._log(f"Loaded {len(gdf)} features")
            return gdf

        except Exception as e:
            raise ValueError(
                f"Failed to parse geospatial data: {e}. "
                f"Ensure response is in a format supported by geopandas "
                f"(GeoJSON, Shapefile, etc.)"
            )

"""
ZIP archive downloader with in-memory processing.
"""

from abc import abstractmethod
from typing import Any
from zipfile import ZipFile
from io import BytesIO
import requests

from sam.core.downloader import BaseDownloader


class ZipDownloader(BaseDownloader):
    """
    Downloads and processes ZIP archives in-memory.

    Subclasses must implement _extract_from_zip() to process the ZIP contents.

    Examples:
        >>> class MyZipDownloader(ZipDownloader):
        ...     def _validate_parameters(self):
        ...         pass
        ...
        ...     def _build_url(self):
        ...         return "https://example.com/data.zip"
        ...
        ...     def _extract_from_zip(self, zf):
        ...         # Extract specific file
        ...         with zf.open('data.txt') as f:
        ...             return f.read()
        ...
        >>> downloader = MyZipDownloader()
        >>> data = downloader.download()
    """

    @abstractmethod
    def _extract_from_zip(self, zf: ZipFile) -> Any:
        """
        Extract and process files from ZIP archive.

        Args:
            zf: ZipFile object opened in read mode

        Returns:
            Processed data (format varies by subclass)

        Examples:
            >>> def _extract_from_zip(self, zf):
            ...     # List files
            ...     files = zf.namelist()
            ...     # Extract first .shp file
            ...     shp = [f for f in files if f.endswith('.shp')][0]
            ...     return gpd.read_file(zf.open(shp))
        """
        pass

    def _process_response(self, response: requests.Response) -> Any:
        """
        Extract ZIP archive in-memory and process contents.

        Args:
            response: HTTP response containing ZIP data

        Returns:
            Processed data from _extract_from_zip()
        """
        self._log("Extracting ZIP archive...")

        with ZipFile(BytesIO(response.content)) as zf:
            self.logger.debug(f"ZIP contains {len(zf.namelist())} files: {zf.namelist()}")
            result = self._extract_from_zip(zf)

        self._log("ZIP extraction complete")
        return result

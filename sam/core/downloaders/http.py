"""
HTTP downloader for simple file downloads.
"""

from pathlib import Path
from typing import Union
import requests

from sam.core.downloader import BaseDownloader


class HTTPDownloader(BaseDownloader):
    """
    Downloads simple files via HTTP.

    Saves file to output_path if specified, otherwise returns bytes.

    Examples:
        >>> class MyFileDownloader(HTTPDownloader):
        ...     def _validate_parameters(self):
        ...         pass
        ...
        ...     def _build_url(self):
        ...         return "https://example.com/data.csv"
        ...
        >>> downloader = MyFileDownloader(output_path="data.csv")
        >>> path = downloader.download()
    """

    def _process_response(self, response: requests.Response) -> Union[bytes, Path]:
        """
        Save file to output_path or return bytes.

        Args:
            response: HTTP response

        Returns:
            Path if output_path specified, otherwise bytes
        """
        if self.output_path:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_path, 'wb') as f:
                f.write(response.content)
            self._log(f"Saved to {self.output_path}")
            return self.output_path

        return response.content

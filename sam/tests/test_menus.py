import os
os.environ["PROJ_LIB"] = r"C:\ProgramData\miniforge3\envs\sam\Library\share\proj\proj.db"
from sam.menus import DataMenuDownloader
import rputils
import geopandas as gpd

DATA = rputils.Paths(data_dir="data")
DATA_ROOT = DATA.dir_data
RAW = DATA.dir_raw
PROCESSED = DATA.dir_out
AOI = gpd.read_file(rputils.Path(DATA_ROOT, "test_geom", "AOI.shp"))


if __name__ == '__main__':
    fetcher = DataMenuDownloader(
        summary_areas=AOI,
        data_dir=DATA.dir_data,
        prj_crs=None,
        years=None
    )
    # fetcher.pull_replica_network()
    fetcher.pull_replica_acs()
    fetcher.pull_replica_population()
    fetcher.pull_replica_trip_table()

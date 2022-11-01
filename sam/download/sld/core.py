import fiona
import geopandas as gpd
import numpy as np
from urllib.request import urlopen
from warnings import warn
SLD_LINK = "https://edg.epa.gov/EPADataCommons/public/OA/SLD/SmartLocationDatabaseV3.zip"
SLD_GDB = "SmartLocationDatabase.gdb"
SLD_LAYER = "EPA_SLD_Database_V3"
SLD_GEOS = np.array([
    "GEOID10","GEOID20","CSA","CSA_Name","CBSA","CBSA_Name"
])
SLD_FIELDS = np.array([
    "GEOID10", "GEOID20", "STATEFP", "COUNTYFP", "TRACTCE", "BLKGRPCE",
    "CSA", "CSA_Name", "CBSA", "CBSA_Name", "CBSA_POP", "CBSA_EMP",
    "CBSA_WRK", "Ac_Total", "Ac_Water", "Ac_Land", "Ac_Unpr", "TotPop",
    "CountHU", "HH", "P_WrkAge", "AutoOwn0", "Pct_AO0", "AutoOwn1",
    "Pct_AO1", "AutoOwn2p", "Pct_AO2p", "Workers", "R_LowWageWk",
    "R_MedWageWk", "R_HiWageWk", "R_PCTLOWWAGE", "TotEmp", "E5_Ret",
    "E5_Off", "E5_Ind", "E5_Svc", "E5_Ent", "E8_Ret", "E8_off",
    "E8_Ind", "E8_Svc", "E8_Ent", "E8_Ed", "E8_Hlth", "E8_Pub",
    "E_LowWageWk", "E_MedWageWk", "E_HiWageWk", "E_PctLowWage", "D1A",
    "D1B", "D1C", "D1C5_RET", "D1C5_OFF", "D1C5_IND", "D1C5_SVC",
    "D1C5_ENT", "D1C8_RET", "D1C8_OFF", "D1C8_IND", "D1C8_SVC",
    "D1C8_ENT", "D1C8_ED", "D1C8_HLTH", "D1C8_PUB", "D1D", "D1_FLAG",
    "D2A_JPHH", "D2B_E5MIX", "D2B_E5MIXA", "D2B_E8MIX", "D2B_E8MIXA",
    "D2A_EPHHM", "D2C_TRPMX1", "D2C_TRPMX2", "D2C_TRIPEQ",
    "D2R_JOBPOP", "D2R_WRKEMP", "D2A_WRKEMP", "D2C_WREMLX", "D3A",
    "D3AAO", "D3AMM", "D3APO", "D3B", "D3BAO", "D3BMM3", "D3BMM4",
    "D3BPO3", "D3BPO4", "D4A", "D4B025", "D4B050", "D4C", "D4D", "D4E",
    "D5AR", "D5AE", "D5BR", "D5BE", "D5CR", "D5CRI", "D5CE", "D5CEI",
    "D5DR", "D5DRI", "D5DE", "D5DEI", "D2A_Ranked", "D2B_Ranked",
    "D3B_Ranked", "D4A_Ranked", "NatWalkInd", "Region", "Households",
    "Workers_1", "Residents", "Drivers", "Vehicles", "White", "Male",
    "Lowwage", "Medwage", "Highwage", "W_P_Lowwage", "W_P_Medwage",
    "W_P_Highwage", "GasPrice", "logd1a", "logd1c", "logd3aao",
    "logd3apo", "d4bo25", "d5dei_1", "logd4d", "UPTpercap",
    "B_C_constant", "B_C_male", "B_C_ld1c", "B_C_drvmveh", "B_C_ld1a",
    "B_C_ld3apo", "B_C_inc1", "B_C_gasp", "B_N_constant", "B_N_inc2",
    "B_N_inc3", "B_N_white", "B_N_male", "B_N_drvmveh", "B_N_gasp",
    "B_N_ld1a", "B_N_ld1c", "B_N_ld3aao", "B_N_ld3apo", "B_N_d4bo25",
    "B_N_d5dei", "B_N_UPTpc", "C_R_Households", "C_R_Pop",
    "C_R_Workers", "C_R_Drivers", "C_R_Vehicles", "C_R_White",
    "C_R_Male", "C_R_Lowwage", "C_R_Medwage", "C_R_Highwage",
    "C_R_DrmV", "NonCom_VMT_Per_Worker", "Com_VMT_Per_Worker",
    "VMT_per_worker", "VMT_tot_min", "VMT_tot_max", "VMT_tot_avg",
    "GHG_per_worker", "Annual_GHG", "SLC_score", "Shape_Length",
    "Shape_Area"
])
def dl_sld(columns=None, **kwargs):
    '''
    Download data from the most recent Smart Location Database (SLD)
    Parameters
    ----------
    columns : str, or iterable of str, optional
        SLD data columns to be downloaded; see documentation for column
        specifications. The default is None, in which case all columns are
        retained.
    **kwargs
        Passed to `gpd.read_file()`.
    Notes
    -----
    Opening the SLD zip takes a bit of time -- so be sure that your
    specifications for reading are as correct and comprehensive as possible to
    limit number of reads!
    Regardless of the specifications in `columns`, unique geographic identifier
    columns will be retained in the download; for the current SLD, this
    includes GEOID10, GEOID20, CSA + CSA name, and CBSA + CBSA name. Thus, 
    these columns need not be specified in `columns`. Note that while state
    fips (STATEFP), county fips (COUNTYFP), tract number (TRACTCE), and block
    group number (BLKGRPCE) are also geographic identifiers available in the
    SLD, they are technically non-unique, because they can be derived from 
    GEOID10 or GEOID20. As such, they are not automatically retained, but may 
    be kept by specifying them in `columns`.
    See also
    --------
    Current SLD technical documentation is available at:
    https://www.epa.gov/sites/default/files/2021-06/documents/epa_sld_3.0_technicaldocumentationuserguide_may2021.pdf
    Returns
    -------
    gdf : gpd.GeoDataFrame
        Table of requested SLD data with geometries (in crs ESRI:102039)
    '''
    # Open the SLD zip -- this takes some time! (I timed it at ~4 mins)
    sld_zip = urlopen(SLD_LINK).read()
    # Open the SLD gdb from zip. It only has one layer, so we really only
    # need to concern ourselves with accessing the gdb itself (accessing the
    # layer is trivial)
    with fiona.io.ZipMemoryFile(sld_zip) as sz:
        # Open the gdb
        with sz.open(SLD_GDB) as gdb:
            # Before reading, set the columns we wish to retain
            with fiona.open(gdb.path, layer=SLD_LAYER) as src:
                if columns is None:
                    # No column specs; we'll keep em all!
                    ign_fields = []
                else:
                    # Identify the fields in the SLD
                    fields = np.array(list(src.schema["properties"].keys()))
                    # Format our requested columns to np.array for vectorized 
                    # processing
                    if isinstance(columns, str):
                        cols = np.array([columns])
                    else:
                        cols = np.array(columns)
                    # Combine our requested columns with fixed geographic ID
                    # columns
                    cols = np.unique(np.concatenate([cols, SLD_GEOS]))
                    # Set the download columns by retaining only those in the
                    # SLD
                    cols_sel = cols[np.isin(cols, fields)]
                    # If any of our requested columns were not in the SLD, warn
                    # that they will be tossed
                    if len(cols) != len(cols_sel):
                        msg = ', '.join(list(set(cols)-set(cols_sel)))
                        warn("The following fields were requested "\
                             f"but are not in the SLD: {msg}. "\
                             "These columns will be ignored.")
                    # If all of our download columns were fixed geog ID
                    # columns, warn that you're not really getting any data
                    if np.all(np.isin(cols_sel, SLD_GEOS)):
                        warn("Only geographic ID columns have been selected; "\
                             "no SLD data will be returned.")
                    # Set the fields to ignore for our call to gpd.read_file
                    ign_fields = fields[np.isin(fields, cols_sel, invert=True)]
                    ign_fields = list(ign_fields)
                # Read the SLD layer from the gdb
                kwargs = kwargs.pop("ignore_fields", None)
                gdf = gpd.read_file(gdb.path, layer=SLD_LAYER,
                                    ignore_fields=ign_fields, **kwargs)
    # Return the gdf as read
    return gdf
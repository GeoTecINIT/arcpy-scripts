# Author:   GEOTEC, UJI
# Date:     July 2015
# Update:   February 2016
#
# Purpose:  This script creates a list of empty mosaic data sets.
#           To do so, it reads an input file (2nd input parameter) in which each line contains:
#           1/ source folder where raster files are placed
#           2/ geo database where mosaic data sets are going to be created
#           3/ names of mosaic data sets
#           4/ nodata value per mosaic. Otherwise NA.
#           This script uses 2/, 3/ and 4/.
#
# Note:     It should be executed ONCE at the beginning of the season
#
# Update:   Define no data value; use os.path; naming convention (Jan 2016)
# Update:   Add custom flag to be used only for mosaic data sets with forecast data (Feb 2016)
#
# Usage:    python CreateMosaicDatasets.py <target_folder> <source_folders> <log_file>
# Example:  python CreateMosaicDatasets.py c:/ERMES/PRODUCTS/SCRIPTS IT_2016_folders.txt IT_2016.log


def log_tool():
    # log all informative messages returned by the last tool executed
    if len(arcpy.GetMessages(0)) > 0:
        logging.info(arcpy.GetMessages(0))
    # Log all warnings messages returned by the last tool executed
    if len(arcpy.GetMessages(1)) > 0:
        logging.warning(arcpy.GetMessages(1))


def create_mosaic(_database_path, _mosaic_name, _nodata_value):
    """Create empty mosaic data sets

    :param _database_path:
    :param _mosaic_name:
    :param _nodata_value:
    :return:
    """
    mosaic_path = os.path.join(_database_path, _mosaic_name)

    # Set up geoprocessing environment defaults
    arcpy.env.workspace = _database_path  # that's more useful
    sr = arcpy.SpatialReference()
    sr.loadFromString(
        "PROJCS['ETRS_1989_LAEA',GEOGCS['GCS_ETRS_1989',DATUM['D_ETRS_1989',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Lambert_Azimuthal_Equal_Area'],PARAMETER['False_Easting',4321000.0],PARAMETER['False_Northing',3210000.0],PARAMETER['Central_Meridian',10.0],PARAMETER['Latitude_Of_Origin',52.0],UNIT['Meter',1.0]];-8426600 -9526700 10000;-100000 10000;-100000 10000;0.001;0.001;0.001;IsHighPrecision")
    arcpy.env.outputCoordinateSystem = sr

    if arcpy.Exists(mosaic_path):
        logging.info("Mosaic data set %s exists, will be deleted.", _mosaic_name)
        arcpy.DeleteMosaicDataset_management(in_mosaic_dataset=mosaic_path,
                                             delete_overview_images="DELETE_OVERVIEW_IMAGES",
                                             delete_item_cache="DELETE_ITEM_CACHE")
        log_tool()

    logging.info("Creating mosaic data set %s in geo database %s", _mosaic_name, os.path.basename(_database_path))
    arcpy.CreateMosaicDataset_management(in_workspace=_database_path,
                                         in_mosaicdataset_name=_mosaic_name,
                                         coordinate_system=sr,
                                         num_bands="",
                                         pixel_type="", product_definition="NONE", product_band_definitions="")
    log_tool()
    logging.info("Created new mosaic data set %s", _mosaic_name)

    if _nodata_value != "NA":
        logging.info("Define noData value of %s for %s mosaic data set.", _nodata_value, _mosaic_name)

        arcpy.DefineMosaicDatasetNoData_management(
            in_mosaic_dataset=mosaic_path,
            num_bands="1",
            bands_for_nodata_value=" ".join(["ALL_BANDS", _nodata_value]),
            bands_for_valid_data_range="",
            where_clause="",
            Composite_nodata_value="NO_COMPOSITE_NODATA")
        log_tool()

    # Add fields to mosaic data set for web application
    logging.info("Adding custom fields...")
    arcpy.AddField_management(mosaic_path, "PARAMNAME", "TEXT", "", "", 50, "PARAMNAME", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(mosaic_path, "YEAR", "TEXT", "", "", 4, "YEAR", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(mosaic_path, "SDATE", "TEXT", "", "", 10, "SDATE", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(mosaic_path, "DATE", "DATE")
    # Only for forecast data
    arcpy.AddField_management(mosaic_path, "FORE", "SHORT", "", "", "", "FORE", "NULLABLE", "NON_REQUIRED", "")

    # Assign default values to custom fields
    arcpy.AssignDefaultToField_management(mosaic_path, "PARAMNAME", "NA")  # NA means no paramname
    arcpy.AssignDefaultToField_management(mosaic_path, "FORE", 0)  # 0 = FALSE; 1 = TRUE


def update_mosaic_statistics(_database_path, _mosaic_name):
    """Before adding images to the mosaic data set, calculate statistics

    :param _database_path:
    :param _mosaic_name:
    :return:
    """
    mosaic_path = os.path.join(_database_path, _mosaic_name)

    # logging.debug("Building pyramids...")
    # Pyramids are simply lower-resolution versions of rasters that improve drawing performance at smaller scales.
    # arcpy.BuildPyramidsandStatistics_management(
    #    in_workspace=_database_path,
    #    include_subdirectories="NONE",
    #    build_pyramids="BUILD_PYRAMIDS", 
    #    calculate_statistics="CALCULATE_STATISTICS",
    #    BUILD_ON_SOURCE="NONE", 
    #    estimate_statistics="ESTIMATE_STATISTICS", 
    #    x_skip_factor="1", y_skip_factor="1",
    #    ignore_values="", pyramid_level="-1", 
    #    SKIP_FIRST="NONE",
    #    resample_technique="NEAREST", 
    #    compression_type="DEFAULT",
    #    compression_quality="75",
    #    skip_existing="SKIP_EXISTING")

    logging.info("Calculating statistics...")
    # Statistics are required for mosaic data sets to perform certain tasks,
    # such as applying a contrast stretch or classifying data
    arcpy.CalculateStatistics_management(
        in_raster_dataset=mosaic_path,
        x_skip_factor="1", y_skip_factor="1",
        ignore_values="", skip_existing="OVERWRITE",
        area_of_interest="".join([_mosaic_name, "\Footprint"]))
    log_tool()

    logging.info("Performing final checks...")
    # Performs checks on a mosaic data set for errors and possible improvements.
    arcpy.AnalyzeMosaicDataset_management(
        in_mosaic_dataset=mosaic_path,
        where_clause="",
        checker_keywords="FOOTPRINT;FUNCTION;RASTER;PATHS;SOURCE_VALIDITY;STALE;PYRAMIDS;STATISTICS;PERFORMANCE;INFORMATION")
    log_tool()


# main programme
try:
    # Import the modules
    import arcpy, logging, sys, os

    # Set the workspace and global variables
    ENV_PATH = os.path.normpath(os.path.join(sys.argv[1], ".."))
    MOSAICS_FILENAME = sys.argv[2]
    LOG_FILENAME = sys.argv[3]
    arcpy.env.workspace = ENV_PATH  # Not really useful here
    arcpy.env.overwriteOutput = True

    # Do not spread operations across multiple processes.
    arcpy.env.parallelProcessingFactor = "0"

    # Create logger object 
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(filename)s %(levelname)-8s %(message)s',
                        datefmt='%d %b %Y %H:%M:%S',
                        filename=LOG_FILENAME)

    logging.info("Script initiating...")
    f = open(MOSAICS_FILENAME, "r")
    mosaics = []
    for x in f.readlines():
        line = x.strip().split(";")
        mosaics.append(line)

    # For each item, create an empty mosaic data set
    for mosaic in mosaics:
        database_name = mosaic[1]
        country_code = database_name[:2]  # IT_2016.gdb --> IT
        database_path = os.path.join(ENV_PATH, country_code, database_name)
        mosaic_name = mosaic[2]
        nodata_value = mosaic[3]
        create_mosaic(database_path, mosaic_name, nodata_value)
        update_mosaic_statistics(database_path, mosaic_name)

    f.close()
    logging.info("Script finished.")

except arcpy.ExecuteError:
    logging.info("Script did not complete.")
    # log errors
    logging.error(arcpy.GetMessages(2))

except:
    logging.info(arcpy.GetMessages())

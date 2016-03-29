# Author:   GEOTEC, UJI
# Date:     July 2015
# Update:   February 2016
#
# Purpose:  This script updates a list of existing mosaic data sets with new raster files.
#           To do so, it reads an input file (2nd input parameter) in which each line contains:
#           1/ source folder where raster files are placed
#           2/ geo database where mosaic data sets are going to be created
#           3/ names of mosaic data sets
#           4/ nodata value per mosaic. Otherwise NA.
#           This script uses 1/, 2/ and 3/.
#
# Note:     It should be executed ONCE at the beginning of the season
#
# Update:   Define no data value; use os.path; naming convention (Feb 2016)
# Update:   Enhancement of update cursor (Feb 2016)
#
# Usage:    python UpdateMosaicDatasetsLTA.py <target_folder> <source_folders> <log_file>
# Example:  python UpdateMosaicDatasetsLTA.py c:/ERMES/PRODUCTS/SCRIPTS IT_2016_folders_LTA.txt IT_2016_LTA.log


def log_tool():
    # log all informative messages returned by the last tool executed
    if len(arcpy.GetMessages(0)) > 0:
        logging.info(arcpy.GetMessages(0))
    # Log all warnings messages returned by the last tool executed
    if len(arcpy.GetMessages(1)) > 0:
        logging.warning(arcpy.GetMessages(1))


def update_mosaic(_database_path, _mosaic_name, _source_folder):
    """Update mosaic data set with incoming raster files from LTA source folders

    :param _database_path:
    :param _mosaic_name:
    :param _source_folder:
    :return:
    """
    mosaic_path = os.path.join(_database_path, _mosaic_name)

    # Set up geoprocessing environment defaults
    arcpy.env.workspace = _database_path  # that's more useful

    logging.info("Updating mosaic data set %s in geo database %s.", _mosaic_name, os.path.basename(_database_path))

    # it sets "Exclude Duplicates" to true. 
    arcpy.AddRastersToMosaicDataset_management(in_mosaic_dataset=mosaic_path,
                                               raster_type="Raster Dataset",
                                               input_path=_source_folder,
                                               update_cellsize_ranges="UPDATE_CELL_SIZES",
                                               update_boundary="UPDATE_BOUNDARY",
                                               update_overviews="NO_OVERVIEWS",
                                               maximum_pyramid_levels="",
                                               maximum_cell_size="0",
                                               minimum_dimension="1500",
                                               spatial_reference="",
                                               filter="*.tif",
                                               sub_folder="NO_SUBFOLDERS",
                                               duplicate_items_action="EXCLUDE_DUPLICATES",
                                               build_pyramids="BUILD_PYRAMIDS",
                                               calculate_statistics="CALCULATE_STATISTICS",
                                               build_thumbnails="NO_THUMBNAILS",
                                               operation_description="#",
                                               force_spatial_reference="NO_FORCE_SPATIAL_REFERENCE")
    log_tool()

    logging.info("Updating custom fields...")
    # Create the SQL expression for the update cursor. Custom fields are uppercase
    fields = ["Name", "PARAMNAME", "YEAR", "SDATE", "DATE"]
    # Create the update cursor that updates custom fields (all rows)
    with arcpy.da.UpdateCursor(mosaic_path, fields) as cursor:
        for row in cursor:
            # Name is 0, PARAMNAME is 1, YEAR is 2, SDATE is 3, DATE is 4
            raster_filename = row[0]
            parts = raster_filename.split("_")  # Ex: IT_avg_Monitoring_NDVI_2003_2015_001.tif
            row[1] = parts[1].upper()  # avg or std
            row[2] = parts[5]  # 2015
            day = int(parts[6])  # 001
            date_value = datetime.datetime(int(parts[5]), 1, 1) + datetime.timedelta(day - 1)
            date_formatted = date_value.strftime('%Y/%m/%d')
            row[3] = date_formatted  # String/text type
            row[4] = date_value  # Date type
            cursor.updateRow(row)
        del cursor, row


# main programme
try:
    # Import the modules
    import arcpy, logging, sys, os
    import datetime

    # Set the workspace
    ENV_PATH = os.path.normpath(os.path.join(sys.argv[1], ".."))
    MOSAICS_FILENAME = sys.argv[2]
    LOG_FILENAME = sys.argv[3]
    arcpy.env.workspace = ENV_PATH
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

    for mosaic in mosaics:
        source_folder = mosaic[0]
        database_name = mosaic[1]
        country_code = database_name[:2]  # IT_2016.gdb --> IT
        database_path = os.path.join(ENV_PATH, country_code, database_name)
        mosaic_name = mosaic[2]
        update_mosaic(database_path, mosaic_name, source_folder)

    f.close()
    logging.info("Script finished.")

except arcpy.ExecuteError:
    logging.debug("Script did not complete.")
    # log errors
    logging.error(arcpy.GetMessages(2))

except:
    logging.info(arcpy.GetMessages())

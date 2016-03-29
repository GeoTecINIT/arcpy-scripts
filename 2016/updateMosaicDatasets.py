# Author:   GEOTEC, UJI
# Date:     June 2015
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
# Note:     It should be executed during the current season ON A DAILY BASIS
#
# Update:   Define no data value; use os.path; naming convention (Jan 2016)
# Update:   Enhancement of update cursor by previously selecting rows to be updated (Feb 2016)
# Update:   Conditional to create or not an update cursor for custom fields (Feb 2016)
#
# Usage:    python UpdateMosaicDatasets.py <target_folder> <source_folders> <log_file>
# Example:  python UpdateMosaicDatasets.py c:/ERMES/PRODUCTS/SCRIPTS IT_2016_folders.txt IT_2016.log


def log_tool():
    # log all informative messages returned by the last tool executed
    if len(arcpy.GetMessages(0)) > 0:
        logging.info(arcpy.GetMessages(0))
    # Log all warnings messages returned by the last tool executed
    if len(arcpy.GetMessages(1)) > 0:
        logging.warning(arcpy.GetMessages(1))


def get_number_records(_mosaic):
    counts = int(arcpy.GetCount_management(_mosaic).getOutput(0))
    log_tool()
    return counts


def update_mosaic(_database_path, _mosaic_name, _source_folder):
    """Update mosaic data set with incoming raster files from current year source folders (REGIONAL)

    :param _database_path:
    :param _mosaic_name:
    :param _source_folder:
    :return:
    """
    mosaic_path = os.path.join(_database_path, _mosaic_name)

    # Set up geoprocessing environment defaults
    arcpy.env.workspace = _database_path  # that's more useful

    # Number of raster files in mosaic before calling AddRastersToMosaicDataset_management
    counts_before = get_number_records(mosaic_path)

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

    counts_after = get_number_records(mosaic_path)
    added_rasters = counts_after - counts_before
    logging.info("Number of new entries after AddRasterToMosaicDataset: %s", added_rasters)

    if added_rasters > 0:
        logging.info("Updating custom fields...")
        # Create the SQL expression for the update cursor. Custom fields are uppercase
        fields = ["Name", "PARAMNAME", "YEAR", "SDATE", "DATE"]
        sql_field = arcpy.AddFieldDelimiters(arcpy.env.workspace, "PARAMNAME")
        sql_expr = sql_field + " = " + "'NA'"  # If PARAMNAME is NA, that row is a new entry

        # Create the update cursor that updates custom fields of row returned by the SQL expression
        with arcpy.da.UpdateCursor(mosaic_path, fields, sql_expr) as cursor:
            for row in cursor:
                # Name is 0, PARAMNAME is 1, YEAR is 2, SDATE is 3, DATE is 4
                raster_filename = row[0]
                parts = raster_filename.split("_")  # Ex: IT_Monitoring_NDVI_2015_001.tif
                row[1] = parts[2]  # NDVI
                row[2] = parts[3]  # 2015
                day = int(parts[4])  # 001
                date_value = datetime.datetime(int(parts[3]), 1, 1) + datetime.timedelta(day - 1)
                date_formatted = date_value.strftime('%Y/%m/%d')
                row[3] = date_formatted  # String/text type
                row[4] = date_value  # Date type
                cursor.updateRow(row)
            del cursor, row
    else:
        logging.info("No updates for mosaic data set %s in geo database %s.",
                     _mosaic_name, os.path.basename(_database_path))


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

    # For each data source (folder) update corresponding mosaic dataset
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

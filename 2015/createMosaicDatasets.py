# -*- coding: cp1252 -*-
# Author:   GEOTEC, UJI
# Date:     July 2015
#
# Purpose:  This script creates a list of empty mosaic datasets.
#           To do so, it reads a input file that contains per each line:
#           1/ list of folders where raster failes are placed
#           2/ workspace name where mosaic datasets are located
#           3/ names of mosaic datasets
#           This script uses (2/) workspace name and (3/) the names of mosaic datasets.
# Example:  python CreateMosaicDatasets.py c:/ERMES/PRODUCTS/IT_2015 foldersIT_2015.txt IT_2015.log


# Create Mosaic Dataset  
def createMosaic(workspaceName, mosaicName):
    mosaicPath = workspaceName + "/" + mosaicName
    
    if arcpy.Exists(mosaicPath):
        logging.debug(mosaicName + " exists, will be deleted")
        arcpy.DeleteMosaicDataset_management(in_mosaic_dataset=mosaicPath,
                                             delete_overview_images="DELETE_OVERVIEW_IMAGES",
                                             delete_item_cache="DELETE_ITEM_CACHE")
     
    logging.debug("Creating Mosaic Dataset..." + mosaicName)
    arcpy.CreateMosaicDataset_management(in_workspace=workspaceName,
                                         in_mosaicdataset_name=mosaicName,
                                         coordinate_system="PROJCS['ETRS_1989_LAEA',GEOGCS['GCS_ETRS_1989',DATUM['D_ETRS_1989',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Lambert_Azimuthal_Equal_Area'],PARAMETER['False_Easting',4321000.0],PARAMETER['False_Northing',3210000.0],PARAMETER['Central_Meridian',10.0],PARAMETER['Latitude_Of_Origin',52.0],UNIT['Meter',1.0]];-8426600 -9526700 10000;-100000 10000;-100000 10000;0.001;0.001;0.001;IsHighPrecision",
                                         num_bands="", pixel_type="", product_definition="NONE", product_band_definitions="")
    logging.debug("New mosaic dataset " + mosaicName + " was created.")

    
    logging.debug("Calculating Statistics...")
    areaOfInterest = mosaicName + "\Footprint"
    arcpy.CalculateStatistics_management(in_raster_dataset=mosaicPath,
                                         x_skip_factor="1",
                                         y_skip_factor="1",
                                         ignore_values="",
                                         skip_existing="OVERWRITE",  # "SKIP_EXISTING"?
                                         area_of_interest=areaOfInterest)

    logging.debug("Analyzing Mosaic Dataset " + mosaicName)
    arcpy.AnalyzeMosaicDataset_management(in_mosaic_dataset=mosaicPath,
                                          where_clause="",
                                          checker_keywords="FOOTPRINT;FUNCTION;RASTER;PATHS;SOURCE_VALIDITY;STALE;PYRAMIDS;STATISTICS;PERFORMANCE;INFORMATION")    

    # Add fields to mosaic dataset for web application
    logging.debug("Adding custom fields...")
    arcpy.AddField_management(mosaicPath, "PARAMNAME", "TEXT", "", "", 15, "PARAMNAME", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(mosaicPath, "YEAR", "TEXT", "", "", 4, "YEAR", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(mosaicPath, "SDATE", "TEXT", "", "", 10, "SDATE", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(mosaicPath, "DATE", "DATE")
    
def foo():
    arcpy.BuildPyramidsandStatistics_management(in_workspace="C:/Users/cgranell/Data/mosaic/IT_2015.gdb/REGIONAL_METEO_TMAX",
                                                include_subdirectories="INCLUDE_SUBDIRECTORIES",
                                                build_pyramids="BUILD_PYRAMIDS", calculate_statistics="CALCULATE_STATISTICS",
                                                BUILD_ON_SOURCE="NONE", block_field="",
                                                estimate_statistics="ESTIMATE_STATISTICS", x_skip_factor="1", y_skip_factor="1",
                                                ignore_values="", pyramid_level="-1", SKIP_FIRST="NONE",
                                                resample_technique="NEAREST", compression_type="DEFAULT", compression_quality="75",
                                                skip_existing="SKIP_EXISTING")
    
# main programme
try:
    # Import the modules
    import arcpy, logging, sys

    # Set the workspace and global variables
    ENV_PATH = sys.argv[1]
    FOLDER_FILENAME = sys.argv[2]
    LOG_FILENAME = sys.argv[3]
    arcpy.env.workspace = ENV_PATH

    arcpy.env.parallelProcessingFactor = "0"
    
    # Create logger stuff 
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename=LOG_FILENAME)

    logging.debug("Creating Mosaic Datasets process initiated...")    
    f = open(FOLDER_FILENAME, "r")
    folders = []
    for x in f.readlines():
        line = x.strip().split(";")
        folders.append(line) 

    #print folders
    for folder in folders:
        logging.debug("Creating: " + folder[1] + " mosaic name: " + folder[2])  
        createMosaic(folder[1], folder[2])
        
    f.close()
    # log all informative messages (tool start and end times, tool progress
    logging.info(arcpy.GetMessages(0))
    if len(arcpy.GetMessages(1)) > 0:
        # Log warnings
        logging.warning(arcpy.GetMessages(1))
    logging.debug("Creating Mosaic Datasets process finished.")    
    

except arcpy.ExecuteError:
    logging.debug("Creating Mosaic Datasets process did not complete.")
    # log errors
    logging.error(arcpy.GetMessages(2))
    
except:
    logging.info(arcpy.GetMessages())
    

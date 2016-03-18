# Author:   GEOTEC, UJI
# Date:     July 2015
#
# Purpose:  This script updates a list of existing mosaic datasets with new raster files.
#           To do so, it reads a input file that contains per each line:
#           1/ list of folders where raster failes are placed
#           2/ workspace name where mosaic datasets are located
#           3/ names of mosaic datasets
#           This script uses all parameters above.
# Purpose:  This script reads folders from a file and lists raster files in each folder
# Example:  python UpdateMosaicDatasetsLTA.py c:/ERMES/PRODUCTS/IT_2015 foldersIT_2015_LTA.txt IT_2015_LTA.log

   
def updateMosaic(inputFolder, workspaceName, mosaicName):
    # workspace path + mosaic dataset name
    mosaicPath = workspaceName + "/" + mosaicName
    
    logging.debug("Updating Mosaic Dataset..." + mosaicName)

    #arcpy.AddRastersToMosaicDataset_management(agroMosaic, "Raster Dataset", Rasters, "UPDATE_CELL_SIZES", "UPDATE_BOUNDARY", "NO_OVERVIEWS", "", "0", "1500", Proj, "", "SUBFOLDERS", "OVERWRITE_DUPLICATES", "NO_PYRAMIDS", "CALCULATE_STATISTICS", "NO_THUMBNAILS", "", "NO_FORCE_SPATIAL_REFERENCE")
    
    # it sets "Exclude Duplicates" to true. 
    arcpy.AddRastersToMosaicDataset_management(in_mosaic_dataset=mosaicPath,
                                               raster_type="Raster Dataset",
                                               input_path=inputFolder,
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

    
    # Create the SQL expression for the update cursor.
    fields = ["Name","PARAMNAME", "YEAR", "SDATE", "DATE"] # Name is 0, PARAMNAME is 1, YEAR is 2, SDATE is 3, DATE is 4
    # Create the update cursor and update each row returned by the SQL expression
    with arcpy.da.UpdateCursor(mosaicPath, fields) as cursor:
        for row in cursor:
            if row[1] == None: # If PARAMNAME is null
    		rasterFileName = row[0]
    		parts =  rasterFileName.split("_")  # Ex: IT_avg_Monitoring_NDVI_2003_2015_001.tif
    		row[1] = parts[1].upper()	# avg or std
    		row[2] = parts[5]	        # 2015
    		day = int(parts[6])	        # 001
    		dateValue = datetime.datetime(int(parts[5]), 1, 1) + datetime.timedelta(day-1)
                formattedDate = dateValue.strftime('%Y/%m/%d')
                row[3] = formattedDate  # String/text type
                row[4] = dateValue      # Date type
    		cursor.updateRow(row)

    del cursor, row
    logging.debug("Populating fields...")

# main programme
try:
    # Import the modules
    import arcpy, logging, sys
    import datetime

    # Set the workspace
    #path = "C:/Users/cgranell/Data/scripts"
    ENV_PATH = sys.argv[1]
    FOLDER_FILENAME = sys.argv[2]
    LOG_FILENAME = sys.argv[3]
    arcpy.env.workspace = ENV_PATH

    # Do not spread operations accross multiple processes.
    arcpy.env.parallelProcessingFactor = "0"

    # Create logger stuff 
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename=LOG_FILENAME)

    logging.debug("Updating Mosaic Datasets process initiated...")    
    f = open(FOLDER_FILENAME, "r")
    folders = []
    for x in f.readlines():
        line = x.strip().split(";")
        folders.append(line) 

    #print folders
    for folder in folders:
        logging.debug("Processing input folder..." + folder[0])
        updateMosaic(folder[0], folder[1], folder[2])
        
    f.close()
    # log all informative messages (tool start and end times, tool progress
    logging.info(arcpy.GetMessages(0))
    if len(arcpy.GetMessages(1)) > 0:
        # Log warnings
        logging.warning(arcpy.GetMessages(1))
    logging.debug("Updating Mosaic Datasets process finished.")    
    

except arcpy.ExecuteError:
    logging.debug("Updating Mosaic Datasets process did not complete.")
    # log errors
    logging.error(arcpy.GetMessages(2))
    
except:
    logging.info(arcpy.GetMessages())
    

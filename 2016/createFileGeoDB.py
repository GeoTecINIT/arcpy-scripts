# Author:   GEOTEC, UJI
# Date:     January 2016
#
# Purpose:  This script creates a list of empty File Geodabases.
#           To do so, it reads an input file that each line contains:
#           1/ target folder where geo databases are placed
#           2/ name of geo databases
#
# Note:     It should be executed ONCE at the beginning of the season
#
# Usage:    python CreateFileGeoDB.py <target_folder> <databases>
# Example:  python CreateFileGeoDB.py c:/ERMES/PRODUCTS/SCRIPTS GeoDB_2016.txt


 # Import the modules
import arcpy, sys, os

# Set the workspace and global variables
ENV_PATH =  os.path.normpath(os.path.join(sys.argv[1], ".."))
DB_FILENAME = sys.argv[2]
arcpy.env.workspace = ENV_PATH
arcpy.env.overwriteOutput = True

f = open(DB_FILENAME, "r")
databases = []
for x in f.readlines():
    line = x.strip().split(";")
    databases.append(line) 

# For each database create an empty File Geodatabase 
for database in databases:
    arcpy.CreateFileGDB_management(
    	out_folder_path=database[0], #"C:/ERMES/products/IT", 
		out_name=database[1], #"IT2006", 
		out_version="CURRENT")
        
f.close()

print "Script 'CreateFileGeoDB' completed."

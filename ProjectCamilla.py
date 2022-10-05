#1st Assignment Programming 2

""" 2.Merge the Dublin local authorities into one and store in a new shapefile.
    Don't forget to store the attributes as well as the geometry.
	3.	Calculate the centroid for Dublin merged and store this in a new shapefile.
	4.	Geocode the address of this centroid.
	You will need to convert the CRS to WGS84. This should be stored in the shapefile you created in the last step. 
"""

#importing necessary libraries
import gdal_workaround #it will bring all the integrations needed
from shapely.geometry import shape, mapping  #to be able to create a new shapefile and to deal with this type of data
from shapely.ops import unary_union #merging tool
import ops
import fiona #to be able to read and write shapefiles
from friona.crs import to_string #to be able to give coordenates to our new shapefile
from collections import OrderedDict #to be able to work with a fiona schema
import utilities.geopy_nominatim as geocode #suggestion to be able to give an address to geocode
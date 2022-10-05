#Camilla Casella Programming 2 - 2022


#basic imports
import gdal_workaround
import os
import fiona
import geopandas
import geopy
from geopy.geocoders import Nominatim

#imports from packaged
from fiona.crs import from_epsg
from shapely.ops import cascaded_union
from shapely.geometry import shape, mapping, MultiPoint, LineString, Point
from utilities.download_from_geoserver import download_wfs_data as get_geoserver
from utilities.get_or_create_temporary_directory import get_temporary_directory as get_temp
from datetime import datetime

#imports for the GUI and layout
from tkinter import *
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

#Most part of this defaults I used Markfoleys help scripts.
#I have tried to run with other counties as well but Dublin has worked better for me as a default.
# Altought the address is not showing like expected. Also, I wasn't able to recreate that to other counties.

DEFAULTS = {
    "HOST": "https://markfoley.info/geoserver",
    "TEMP_DIR": ".ca2_temp",
    "WORKSPACE_POLYS": "census2011",
    "DATASET_POLYS": "electoral_divisions",
    "POLYS_CQL_FILTER": "countyname = 'Donegal County'",
    "WORKSPACE_POINTS": "TUDublin",
    "DATASET_POINTS": "geonames_ie",
    "POINTS_CQL_FILTER": "featurecode = 'PPL' AND admin2code ='6'",
    "POLYS_PROPERTY_FILTER": ["countyname", "total2011"],
    "SRS_CODE": 29903
}

#references from Markfoleys scripts
def do_analysis(**defaults):
    result_log = ""

    try:
        # Getting Polygon (counties) data from geoserver, using the default options.
        local_polys = get_geoserver(
            host=defaults["HOST"],
            workspace=defaults["WORKSPACE_POLYS"],
            dataset=defaults["DATASET_POLYS"],
            filter_expression=defaults["POLYS_CQL_FILTER"],
            property_list=defaults["POLYS_PROPERTY_FILTER"],
            srs=defaults["SRS_CODE"])

        # Converting the Polygon data to a shapely format.
        feature_polys = []
        population = 0
        for feature in local_polys["geojson_data"]["features"]:
            feature_polys.append(shape(feature["geometry"]))
            population += feature["properties"]["total2011"]

        # Using the cascaded_union function to merge the selected counties into one.
        merged_polys = cascaded_union(feature_polys)

        # Forming a schema for the merged polygon.
        outgoing_schema = {
            "geometry": 'Polygon',
            "properties": {
                "countyname": 'str',
                "population": 'int',
            }
        }

        outgoing_feature = {
            "geometry": mapping(merged_polys),
            "properties": {
                "countyname": 'str',
                "population": population,
            }
        }

        # Creating a temporary directory to run analysis and create new shapefiles.
        tmp_dir = get_temp(__file__, defaults['TEMP_DIR'])

        target_file = os.path.join(tmp_dir, f"Mayo.shp")

        with fiona.open(target_file,
                        "w", driver="ESRI Shapefile",
                        crs=from_epsg(f"{defaults['SRS_CODE']}"),
                        schema=outgoing_schema) as fh:
            fh.write(outgoing_feature)

        # Finding the centroid of the created merged polys polygon.
        poly_centroid = merged_polys.centroid

        #finding the ddress or our centroid.
        poly_cen_sch = {'geometry': 'Point',
                        'properties': {
                            'address': 'str'}
                        }

        og_poly_cen = {'geometry': mapping(poly_centroid),
                       'properties': {
                           'address': "adress"
                       }}
        # Writing the shapefile for the merged polygon centroid.
        with fiona.open('.ca2_temp/Poly_Centroid.shp',
                        'w',
                        'ESRI Shapefile',
                        crs=from_epsg(f"{defaults['SRS_CODE']}"),
                        schema=poly_cen_sch) as pc:
            pc.write(og_poly_cen)

        #getting points from the geoserver.
        local_points = get_geoserver(
            host=defaults["HOST"],
            workspace=defaults["WORKSPACE_POINTS"],
            dataset=defaults["DATASET_POINTS"],
            filter_expression=defaults["POINTS_CQL_FILTER"],
            srs=defaults["SRS_CODE"])

        points = []
        for i in local_points['geojson_data']['features']:
            points.append(i)

        # Writing the schema for the outgoing points.
        outgoing_point_schema = {
            "id": "float",
            "geometry_column": 'str',
            "geometry_name": 'str',
            "type": "str",
            "geometry": "Point",
            "properties": {'geonameid': 'int', 'name': 'str', 'id': 'str', 'asciiname': 'str', 'alternatenames': 'str',
                           'latitude': 'float', 'longitude': 'float', 'featureclass': 'str', 'featurecode': 'str',
                           'countrycode': 'str', 'cc2': 'str', 'admin1code': 'str', 'admin2code': 'int',
                           'admin3code': 'int', 'admin4code': 'str', 'population': 'int', 'elevation': 'int',
                           'dem': 'str',
                           'timezone': 'str', 'modificationdate': 'str'}

        }
        # File path for the points shapefile to be stored.
        points_file = os.path.join(tmp_dir, f"Points.shp")

        # Writing the shapefile for the points data.
        with fiona.open(points_file,
                        'w',
                        driver='ESRI Shapefile',
                        crs=from_epsg(f"{defaults['SRS_CODE']}"),
                        schema=outgoing_point_schema) as ft:
            for t in points:
                ft.write(t)

        # Creating the convex hull from the points data.
        mpt = MultiPoint([shape(point['geometry'])
                          for point in fiona.open('.ca2_temp/Points.shp')])

        hull = mpt.convex_hull

        hull_schema = {'geometry': 'Polygon',
                       "properties": {'address': 'str'}}
        with fiona.open('.ca2_temp/Convex_hull.shp',
                        'w',
                        'ESRI Shapefile',
                        crs=from_epsg(f"{defaults['SRS_CODE']}"),
                        schema=hull_schema) as con_result:
            con_result.write({'geometry': mapping(hull),
                              'properties': {'address': '0'}})

        # Finding the centroid of the Convex Hull polygon - entire Ireland.
        hull_centroid = mpt.convex_hull.centroid

        # Geocoding the location of the Convex Hull polygon and format of the location information.

        # Schema for the Convex Hull centroid.
        hull_cen_sch = {'geometry': 'Point',
                        'properties': {
                            'address': 'str'}
                        }
        # Outgoing schema for centroid.
        og_hull_cen = {'geometry': mapping(hull_centroid),
                       'properties': {
                           'address': "sss"
                       }}
        # Writing the shapefile for the Convex Hull centroid.
        with fiona.open('.ca2_temp/ConvexHull_Centroid.shp',
                        'w',
                        'ESRI Shapefile',
                        crs=from_epsg(f"{defaults['SRS_CODE']}"),
                        schema=hull_cen_sch) as pt:
            pt.write(og_hull_cen)

        # Calculating the distance between the two centroid.
        #past exercises used as references - and github from markfoley.
        t1 = Point(314167.758, 239312.854)
        t = geopandas.GeoSeries(t1)

        t2 = Point(187405.015, 231262.219)

        dist = t.distance(t2)
        print("The Distance between the Convex Hull Centroid and Merged Polygon Centroid is:", dist)

        P1 = ".ca2_temp/Poly_Centroid.shp"
        P2 = ".ca2_temp/ConvexHull_Centroid.shp"

        # Opening the Merged Polygon and Convex HuLL centroid and geometry.
        with fiona.open(P1) as tbh:
            for elem in tbh:
                if elem['id'] == '0':
                    geom1 = shape(elem['geometry'])

        with fiona.open(P2) as tbf:
            for elem in tbf:
                if elem['id'] == '0':
                    geom2 = shape(elem['geometry'])

        # Setting the location of the Linestring (between both centroids)
        linestring = LineString([geom1, geom2])

        # Schema for Linestring
        ls_schema = {'geometry': 'LineString'}

        # Writing the Linestring schema
        with fiona.open('.ca2_temp/LineString.shp',
                        'w',
                        'ESRI Shapefile',
                        crs=from_epsg(f"{defaults['SRS_CODE']}"),
                        schema=ls_schema) as fy:
            fy.write({'geometry': mapping(linestring)})
    except Exception as e:
        print(f"{e}")
        quit(1)

    return result_log

#GUI creation - interative but can use the default information given in the begging
def main():
    defaults = {}
    defaults["HOST"] = input(f"Input Geoserver URL or press ENTER for {DEFAULTS['HOST']} ") or DEFAULTS['HOST']
    defaults["TEMP_DIR"] = input(f"Input Temp Directory or press ENTER for {DEFAULTS['TEMP_DIR']} ") or DEFAULTS[
        'TEMP_DIR']
    defaults["WORKSPACE_POLYS"] = input(f"Input Polygon workspace or press ENTER for {DEFAULTS['WORKSPACE_POLYS']} ") or \
                                  DEFAULTS['WORKSPACE_POLYS']
    defaults["DATASET_POLYS"] = input(f"Input Polygon dataset or press ENTER for {DEFAULTS['DATASET_POLYS']} ") or \
                                DEFAULTS['DATASET_POLYS']
    defaults["WORKSPACE_POINTS"] = input(
        f"Input Points workspace or press ENTER for {DEFAULTS['WORKSPACE_POINTS']} ") or DEFAULTS['WORKSPACE_POINTS']
    defaults["DATASET_POINTS"] = input(f"Input Points dataset or press ENTER for {DEFAULTS['DATASET_POINTS']} ") or \
                                 DEFAULTS['DATASET_POINTS']
    defaults["POLYS_CQL_FILTER"] = input(
        f"Input Polygon CQL filter or press ENTER for {DEFAULTS['POLYS_CQL_FILTER']} ") or DEFAULTS['POLYS_CQL_FILTER']
    defaults["POINTS_CQL_FILTER"] = input(
        f"Input Points CQL filter or press ENTER for {DEFAULTS['POINTS_CQL_FILTER']} ") or DEFAULTS['POINTS_CQL_FILTER']
    defaults["SRS_CODE"] = input(f"Input SRS code or press ENTER for {DEFAULTS['SRS_CODE']} ") or DEFAULTS['SRS_CODE']

    do_analysis(**DEFAULTS)

#calling the GUI packages
def main_gui():
    root = tk.Tk()
    GUI(root, **DEFAULTS)
    root.mainloop()


class GUI:
    def __init__(self, parent, **defaults):

        self.parent = parent

        try:
            self.defaults = {}
            for k, v in defaults.items():
                self.defaults[k.lower()] = tk.StringVar()
                self.defaults[k.lower()].set(v)

        except Exception as e:
            print(f"{e}")
            return

        self.main_frame = Frame(self.parent, padx=10, pady=10)
        self.main_frame.grid(row=0, column=0)

        # General Inputs (Geoserver,SRS and Temp Directory)
        self.GeneralInputs = Label(self.main_frame, padx=5, pady=10,
                                   text="Input of Geoserver and general data:",
                                   font="arial 10 bold")
        self.GeneralInputs.grid(row=0, column=0, sticky=W)

        self.HOST = Label(self.main_frame, padx=5, pady=5, text="Enter Geoserver URL", font="arial 10")
        self.HOST.grid(row=1, column=0, sticky=W) #row = linha

        self.TEMP_DIR = Label(self.main_frame, padx=5, pady=5, text="Enter Temp Directory",
                              font="arial 10")
        self.TEMP_DIR.grid(row=2, column=0, sticky=W)

        self.SRS_CODE = Label(self.main_frame, padx=5, pady=5, text="Enter SRS code", font="arial 10")
        self.SRS_CODE.grid(row=3, column=0, sticky=W)

        # Input Labels for Polygon Settings
        self.PolygonHeading = Label(self.main_frame, padx=5, pady=10, text="Polygon data:",
                                    font="arial 10 bold")
        self.PolygonHeading.grid(row=4, column=0, sticky=W)

        self.POLY_WORKSPACE = Label(self.main_frame, padx=5, pady=5, text="Enter Polygon data workspace",
                                    font="arial 10")
        self.POLY_WORKSPACE.grid(row=5, column=0, sticky=W)

        self.POLY_DATASET = Label(self.main_frame, padx=5, pady=5, text="Enter Polygon dataset",
                                  font="arial 10")
        self.POLY_DATASET.grid(row=6, column=0, sticky=W)

        self.POLY_CQL = Label(self.main_frame, padx=5, pady=5, text="Enter Polygon CQL filters",
                              font="arial 10")
        self.POLY_CQL.grid(row=7, column=0, sticky=W)

        # Input Labels for Point Data settings
        self.PointHeading = Label(self.main_frame, padx=5, pady=10, text="Data points:",
                                  font="arial 10 bold")
        self.PointHeading.grid(row=8, column=0, sticky=W)

        self.POINT_WORKSPACE = Label(self.main_frame, padx=5, pady=5, text="Enter Points data workspace",
                                     font="arial 10")
        self.POINT_WORKSPACE.grid(row=9, column=0, sticky=W)

        self.POINT_DATASET = Label(self.main_frame, padx=5, pady=5, text="Enter Points dataset",
                                   font="arial 10")
        self.POINT_DATASET.grid(row=10, column=0, sticky=W)

        self.POINT_CQL = Label(self.main_frame, padx=5, pady=5, text="Enter Points CQL filter",
                               font="arial 10")
        self.POINT_CQL.grid(row=11, column=0, sticky=W)

        # Entry boxes for Inputs
        self.HOST = Entry(self.main_frame, textvariable=self.HOST, justify=RIGHT)
        self.HOST.grid(row=1, column=1, sticky=W)

        self.TEMP_DIR = Entry(self.main_frame, textvariable=self.TEMP_DIR, justify=RIGHT)
        self.TEMP_DIR.grid(row=2, column=1, sticky=W)

        self.SRS_CODE = Entry(self.main_frame, textvariable=self.SRS_CODE, justify=RIGHT)
        self.SRS_CODE.grid(row=3, column=1, sticky=W)

        self.POLY_WORKSPACE = Entry(self.main_frame, textvariable=self.POLY_WORKSPACE, justify=RIGHT)
        self.POLY_WORKSPACE.grid(row=5, column=1, sticky=W)

        self.POLY_DATASET = Entry(self.main_frame, textvariable=self.POLY_DATASET, justify=RIGHT)
        self.POLY_DATASET.grid(row=6, column=1, sticky=W)

        self.POLY_CQL = Entry(self.main_frame, textvariable=self.POLY_CQL, justify=RIGHT)
        self.POLY_CQL.grid(row=7, column=1, sticky=W)

        self.POINT_WORKSPACE = Entry(self.main_frame, textvariable=self.POINT_WORKSPACE, justify=RIGHT)
        self.POINT_WORKSPACE.grid(row=9, column=1, sticky=W)

        self.POINT_DATASET = Entry(self.main_frame, textvariable=self.POINT_DATASET, justify=RIGHT)
        self.POINT_DATASET.grid(row=10, column=1, sticky=W)

        self.POINT_CQL = Entry(self.main_frame, textvariable=self.POINT_CQL, justify=RIGHT)
        self.POINT_CQL.grid(row=11, column=1, sticky=W)

        # Enter button
        self.btn = Button(self.main_frame, text="Run", padx=5, pady=5, command=self.run_analysis,
                          bg="purple", fg="white", font="arial 10 bold")
        self.btn.grid(row=12, column=0, columnspan=2, sticky=W + E)

        # Title of frame
        self.parent.title("Camilla Casella 2022")

        parent.protocol("WM_DELETE_WINDOW", self.catch_destroy)

        self.parent.option_add('*tearOff', tk.FALSE)

        self.menu = tk.Menu(self.parent)

        # File menu with File and Exit, Exit closes GUI and File opens options
        self.file_menu = tk.Menu(self.menu)
        self.file_menu.add_command(label="Exit", command=self.catch_destroy)
        self.menu.add_cascade(label="Programming Assigment 2", menu=self.file_menu)

        self.parent.config(menu=self.menu)

    # Destroys GUI window when the close button is pushed
    def catch_destroy(self):

        # Asks the user confirmation to close winder
        if messagebox.askokcancel("Don't leave now! ):", "Are you you want to quite?"):
            self.parent.destroy()

    #if we don't run the analysis within GUI nothing will be created.
    def run_analysis(self):
        do_analysis(**DEFAULTS)

        self.result.insert(tk.END, f"{'' * 60}\n")

        for k in self.defaults:
            DEFAULTS[k.upper()] = self.defaults[k].get()
            self.result.insert(tk.END, f"{k}: {self.defaults[k].get()}\n")

        # Do actual spatial analysis
        result = do_analysis(**DEFAULTS)

        # Write results to scrolledtext widget
        self.result.insert(tk.END, f"{datetime.now().isoformat()}: Analysis completed...\n")
        self.result.insert(tk.END, result)
        self.result.insert(tk.END, f"{'-' * 60}\n")
        self.result.insert(tk.END, f"{'-' * 60}\n")
        for k in self.defaults:
            self.result.insert(tk.END, f"{k}: {self.defaults[k].get()}\n")


if __name__ == "__main__":
    # main()
    main_gui()


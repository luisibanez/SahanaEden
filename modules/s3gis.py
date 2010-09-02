# -*- coding: utf-8 -*-

"""
    Sahana Eden GIS Module

    @version: 0.0.8
    @requires: U{B{I{shapely}} <http://trac.gispython.org/lab/wiki/Shapely>}

    @author: Fran Boon <francisboon@gmail.com>
    @author: Timothy Caro-Bruce <tcarobruce@gmail.com>
    @copyright: (c) 2010 Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.

"""

__name__ = "S3GIS"

__all__ = ["GIS", "GoogleGeocoder", "YahooGeocoder"]

#import logging
import os
import re
import sys
import random           # Needed when feature_queries are passed in without a name
import urllib           # Needed for urlencoding
import urllib2          # Needed for error handling on fetch
#import uuid
import Cookie           # Needed for Sessions on Internal KML feeds
try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO
import zipfile          # Needed to unzip KMZ files
from lxml import etree  # Needed to follow NetworkLinks
KML_NAMESPACE = "http://earth.google.com/kml/2.2"

from gluon.storage import Storage, Messages
from gluon.html import *
#from gluon.http import HTTP
from gluon.tools import fetch

SHAPELY = False
try:
    import shapely
    import shapely.geometry
    from shapely.wkt import loads as wkt_loads
    SHAPELY = True
except ImportError:
    print >> sys.stderr, "WARNING: %s: Shapely GIS library not installed" % __name__

# Map WKT types to db types (multi-geometry types are mapped to single types)
GEOM_TYPES = {
    "point": 1,
    "multipoint": 1,
    "linestring": 2,
    "multilinestring": 2,
    "polygon": 3,
    "multipolygon": 3,
}

# -----------------------------------------------------------------------------
class GIS(object):
    """ GIS functions """

    def __init__(self, environment, deployment_settings, db, auth=None, cache=None):
        self.environment = Storage(environment)
        self.request = self.environment.request
        self.response = self.environment.response
        self.session = self.environment.session
        self.T = self.environment.T
        self.deployment_settings = deployment_settings
        assert db is not None, "Database must not be None."
        self.db = db
        self.cache = cache and (cache.ram, 60) or None
        assert auth is not None, "Undefined authentication controller"
        self.auth = auth
        self.messages = Messages(None)
        #self.messages.centroid_error = str(A("Shapely", _href="http://pypi.python.org/pypi/Shapely/", _target="_blank")) + " library not found, so can't find centroid!"
        self.messages.centroid_error = "Shapely library not functional, so can't find centroid! Install Geos & Shapely for Line/Polygon support"
        self.messages.unknown_type = "Unknown Type!"
        self.messages.invalid_wkt_point = "Invalid WKT: Must be like POINT(3 4)!"
        self.messages.invalid_wkt_linestring = "Invalid WKT: Must be like LINESTRING(3 4,10 50,20 25)!"
        self.messages.invalid_wkt_polygon = "Invalid WKT: Must be like POLYGON((1 1,5 1,5 5,1 5,1 1),(2 2, 3 2, 3 3, 2 3,2 2))!"
        self.messages.lon_empty = "Invalid: Longitude can't be empty if Latitude specified!"
        self.messages.lat_empty = "Invalid: Latitude can't be empty if Longitude specified!"
        self.messages.unknown_parent = "Invalid: %(parent_id)s is not a known Location"
        self.messages["T"] = self.T
        self.messages.lock_keys = True

    # -----------------------------------------------------------------------------
    def abbreviate_wkt(self, wkt, max_length=30):
        if not wkt:
            # Blank WKT field
            return None
        elif len(wkt) > max_length:
            return "%s(...)" % wkt[0:wkt.index("(")]
        else:
            return wkt

    # -----------------------------------------------------------------------------
    def download_kml(self, url, public_url):
        """
            Download a KML file:
                unzip it if-required
                follow NetworkLinks recursively if-required

            Returns a file object
        """

        response = self.response
        session = self.session

        file = ""
        warning = ""

        if len(url) > len(public_url) and url[:len(public_url)] == public_url:
            # Keep Session for local URLs
            cookie = Cookie.SimpleCookie()
            cookie[response.session_id_name] = response.session_id
            session._unlock(response)
            try:
                file = fetch(url, cookie=cookie)
            except urllib2.URLError:
                warning = "URLError"
                return file, warning
            except urllib2.HTTPError:
                warning = "HTTPError"
                return file, warning

        else:
            try:
                file = fetch(url)
            except urllib2.URLError:
                warning = "URLError"
                return file, warning
            except urllib2.HTTPError:
                warning = "HTTPError"
                return file, warning

            if file[:2] == "PK":
                # Unzip
                fp = StringIO(file)
                myfile = zipfile.ZipFile(fp)
                try:
                    file = myfile.read("doc.kml")
                except:
                    file = myfile.read(myfile.infolist()[0].filename)
                myfile.close()

            # Check for NetworkLink
            if "<NetworkLink>" in file:
                # Remove extraneous whitespace
                #file = " ".join(file.split())
                try:
                    parser = etree.XMLParser(recover=True, remove_blank_text=True)
                    tree = etree.XML(file, parser)
                    # Find contents of href tag (must be a better way?)
                    url = ""
                    for element in tree.iter():
                        if element.tag == "{%s}href" % KML_NAMESPACE:
                            url = element.text
                    if url:
                        file, warning2 = self.download_kml(url, public_url)
                        warning += warning2
                except (etree.XMLSyntaxError,):
                    e = sys.exc_info()[1]
                    warning += "<ParseError>%s %s</ParseError>" % (e.line, e.errormsg)

            # Check for Overlays
            if "<GroundOverlay>" in file:
                warning += "GroundOverlay"
            if "<ScreenOverlay>" in file:
                warning += "ScreenOverlay"

        return file, warning

    # -----------------------------------------------------------------------------
    def get_api_key(self, layer="google"):
        " Acquire API key from the database "

        db = self.db
        query = db.gis_apikey.name == layer
        return db(query).select(db.gis_apikey.apikey, limitby=(0, 1)).first().apikey

    # -----------------------------------------------------------------------------
    def get_bearing(self, lat_start, lon_start, lat_end, lon_end):
        """
            Given a Start & End set of Coordinates, return a Bearing
            Formula from: http://www.movable-type.co.uk/scripts/latlong.html
        """

        import math

        delta_lon = lon_start - lon_end
        bearing = math.atan2( math.sin(delta_lon)*math.cos(lat_end) , (math.cos(lat_start)*math.sin(lat_end)) - (math.sin(lat_start)*math.cos(lat_end)*math.cos(delta_lon)) )
        # Convert to a compass bearing
        bearing = (bearing + 360) % 360

        return bearing

    # -----------------------------------------------------------------------------
    def _min_not_none(self, *args):
        """
            Utility function returns minimal argument that is not None.
        """
        return min(*(a for a in args if a is not None))

    # -----------------------------------------------------------------------------
    def get_bounds(self, features=[]):
        """
            Calculate the Bounds of a list of Features
            e.g. to use in GPX export for correct zooming
            @ToDo: Optimised Geospatial routines rather than this crude hack
        """
        min_lon = 180
        min_lat = 90
        max_lon = -180
        max_lat = -90
        min_not_none = self._min_not_none  # use this instead of min
        for feature in features:
            min_lon = min_not_none(feature.lon, feature.lon_min, min_lon)
            min_lat = min_not_none(feature.lat, feature.lat_min, min_lat)
            max_lon = max(feature.lon, feature.lon_max, max_lon)
            max_lat = max(feature.lat, feature.lat_max, max_lat)

        # Check that we're still within overall bounds
        config = self.get_config()
        min_lon = max(config.lon, min_lon)
        min_lat = max(config.lat, min_lat)
        max_lon = min_not_none(config.lon, max_lon)
        max_lat = min_not_none(config.lat, max_lat)

        return dict(min_lon=min_lon, min_lat=min_lat, max_lon=max_lon, max_lat=max_lat)

    # -----------------------------------------------------------------------------
    def get_children(self, parent_id):
        """
            Return a list of all GIS Features which are children of the requested feature
            @ ToDo Switch to modified preorder tree traversal:
            http://eden.sahanafoundation.org/wiki/HaitiGISToDo#HierarchicalTrees
        """

        db = self.db
        _locations = db.gis_location

        deleted = (_locations.deleted == False)
        query = deleted & (_locations.parent == parent_id)
        children = db(query).select()
        for child in children:
            children = children & self.get_children(child.id)

        return children

    # -----------------------------------------------------------------------------
    def get_parents(self, feature_id):
        """
            Return a list of all GIS Features which are parents of the requested feature
            @ ToDo Switch to modified preorder tree traversal:
            http://eden.sahanafoundation.org/wiki/HaitiGISToDo#HierarchicalTrees
        """

        db = self.db
        _locations = db.gis_location

        deleted = (_locations.deleted == False)
        query = deleted & (_locations.id == feature_id)
        feature = db(query).select(_locations.parent, limitby=(0, 1)).first()
        if feature and feature.parent:
            parents = db(_locations.id == feature.parent).select(limitby=(0, 1))
            _parents = self.get_parents(feature.parent)
            if _parents:
                parents = parents & _parents
            return parents
        else:
            return None

    # -----------------------------------------------------------------------------
    def get_config(self):
        " Reads the current GIS Config from the DB "

        auth = self.auth
        db = self.db
        
        _config = db.gis_config
        _projection = db.gis_projection
        
        # Default config is the 1st
        config = 1 
        if auth.is_logged_in():
            # Read personalised config, if available
            personalised = db((db.pr_person.uuid == auth.user.person_uuid) & (_config.pe_id == db.pr_person.pe_id)).select(_config.id, limitby=(0, 1)).first()
            if personalised:
                config = personalised.id
            
        query = (_config.id == config)
        
        query = query & (_projection.id == _config.projection_id)
        config = db(query).select(limitby=(0, 1)).first()
        
        output = Storage()
        for item in config["gis_config"]:
            output[item] = config["gis_config"][item]
        
        for item in config["gis_projection"]:
            if item in ["epsg", "units", "maxResolution", "maxExtent"]:
                output[item] = config["gis_projection"][item]
        
        return output

    # -----------------------------------------------------------------------------
    def get_feature_class_id_from_name(self, name):
        """
            Returns the Feature Class ID from it's name
        """

        db = self.db

        feature = db(db.gis_feature_class.name == name).select(db.gis_feature_class.id, limitby=(0, 1)).first()
        if feature:
            return feature.id
        else:
            return None

    # -----------------------------------------------------------------------------
    def get_feature_layer(self, module, resource, layername, popup_label, marker=None, filter=None, active=True):
        """
            Return a Feature Layer suitable to display on a map
            @param: layername: Used as the label in the LayerSwitcher
            @param: popup_label: Used in Cluster Popups to differentiate between types
        """
        db = self.db
        deployment_settings = self.deployment_settings
        request = self.request
        
        # Hide deleted Resources
        query = (db.gis_location.deleted == False)
            
        if filter:
            query = query & (db[filter.tablename].id == filter.id)
        
        # Hide Resources recorded to Country Locations on the map?
        if not deployment_settings.get_gis_display_l0():
            query = query & ((db.gis_location.level != "L0") | (db.gis_location.level == None))
            
        query = query & (db.gis_location.id == db["%s_%s" % (module, resource)].location_id)
        locations = db(query).select(db.gis_location.id, db.gis_location.uuid, db.gis_location.parent, db.gis_location.name, db.gis_location.wkt, db.gis_location.lat, db.gis_location.lon)
        for i in range(0, len(locations)):
            locations[i].popup_label = locations[i].name + "-" + popup_label
        popup_url = URL(r=request, c=module, f=resource, args="read.plain?%s.location_id=" % resource)
        try:
            marker = db(db.gis_marker.name == marker).select(db.gis_marker.id, limitby=(0, 1)).first().id
            layer = {"name":layername, "query":locations, "active":active, "marker":marker, "popup_url": popup_url}
        except:
            layer = {"name":layername, "query":locations, "active":active, "popup_url": popup_url}

        return layer
    
    # -----------------------------------------------------------------------------
    def get_features_in_radius(self, lat, lon, radius):
        """
            Returns Features within a Radius (in km) of a LatLon Location
            Calling function has the job of filtering features by the type they are interested in
            Formula from: http://blog.peoplesdns.com/archives/24
            Spherical Law of Cosines (accurate down to around 1m & computationally quick): http://www.movable-type.co.uk/scripts/latlong.html

            IF PROJECTION CHANGES THIS WILL NOT WORK
        """

        import math
        
        db = self.db

        # km
        radius_earth = 6378.137
        pi = math.pi

        # ToDo: Do a Square query 1st & then run the complex query over subset (to improve performance)
        lat_max = 90
        lat_min = -90
        lon_max = 180
        lon_min = -180
        table = db.gis_location
        query = (table.lat > lat_min) & (table.lat < lat_max) & (table.lon < lon_max) & (table.lon > lon_min)
        deleted = ((table.deleted==False) | (table.deleted==None))
        query = deleted & query

        # ToDo: complete port from PHP to Eden
        pilat180 = pi * lat /180
        #calc = "radius_earth * math.acos((math.sin(pilat180) * math.sin(pi * table.lat /180)) + (math.cos(pilat180) * math.cos(pi*table.lat/180) * math.cos(pi * table.lon/180-pi* lon /180)))"
        #query2 = "SELECT DISTINCT table.lon, table.lat, calc AS distance FROM table WHERE calc <= radius ORDER BY distance"
        #query2 = (radius_earth * math.acos((math.sin(pilat180) * math.sin(pi * table.lat /180)) + (math.cos(pilat180) * math.cos(pi*table.lat/180) * math.cos(pi * table.lon/180-pi* lon /180))) < radius)
        # TypeError: unsupported operand type(s) for *: 'float' and 'Field'
        query2 = (radius_earth * math.acos((math.sin(pilat180) * math.sin(pi * table.lat /180))) < radius)
        #query = query & query2
        features = db(query).select()
        #features = db(query).select(orderby=distance)

        return features

    # -----------------------------------------------------------------------------
    def get_latlon(self, feature_id, filter=False):
    
        """ Returns the Lat/Lon for a Feature (using recursion where necessary)

            @param feature_id: the feature ID (int) or UUID (str)
            @param filter: Filter out results based on deployment_settings
            @ToDo Rewrite to use self.get_parents()
        """
        
        db = self.db
        deployment_settings = self.deployment_settings
        table_feature = db.gis_location
        
        if isinstance(feature_id, int):
            query = (table_feature.id == feature_id)
        elif isinstance(feature_id, str):
            query = (table_feature.uuid == feature_id)
        else:
            # What else could feature_id be?
            return None
        
        feature = db(query).select(table_feature.lat, table_feature.lon, table_feature.parent, limitby=(0, 1)).first()
        
        query = (table_feature.deleted == False)
        if filter and not deployment_settings.get_gis_display_l0():
            query = query & ((table_feature.level != "L0") | (table_feature.level == None))

        try:
            lat = feature.lat
            lon = feature.lon
            if (lat is not None) and (lon is not None):
                # Zero is allowed
                return dict(lat=lat, lon=lon)
            else:
                # Try the Parent (e.g. L5)
                parent_id = feature.parent
                if parent_id:
                    # @ToDo Recursion
                    #latlon = self.get_latlon(parent_id)
                    parent = db(query & (table_feature.id == parent_id)).select(table_feature.lat, table_feature.lon, table_feature.parent, limitby=(0, 1)).first()
                    lat = parent.lat
                    lon = parent.lon
                    if (lat is not None) and (lon is not None):
                        # Zero is allowed
                        return dict(lat=lat, lon=lon)
                    else:
                        # Try the Parent (e.g. L4)
                        parent_id = feature.parent
                        if parent_id:
                            parent = db(query & (table_feature.id == parent_id)).select(table_feature.lat, table_feature.lon, table_feature.parent, limitby=(0, 1)).first()
                            lat = parent.lat
                            lon = parent.lon
                            if (lat is not None) and (lon is not None):
                                # Zero is allowed
                                return dict(lat=lat, lon=lon)
                            else:
                                # Try the Parent (e.g. L3)
                                parent_id = feature.parent
                                if parent_id:
                                    parent = db(query & (table_feature.id == parent_id)).select(table_feature.lat, table_feature.lon, table_feature.parent, limitby=(0, 1)).first()
                                    lat = parent.lat
                                    lon = parent.lon
                                    if (lat is not None) and (lon is not None):
                                        # Zero is allowed
                                        return dict(lat=lat, lon=lon)
                                    else:
                                        # Try the Parent (e.g. L2)
                                        parent_id = feature.parent
                                        if parent_id:
                                            parent = db(query & (table_feature.id == parent_id)).select(table_feature.lat, table_feature.lon, table_feature.parent, limitby=(0, 1)).first()
                                            lat = parent.lat
                                            lon = parent.lon
                                            if (lat is not None) and (lon is not None):
                                                # Zero is allowed
                                                return dict(lat=lat, lon=lon)
                                            else:
                                                # Try the Parent (e.g. L1)
                                                parent_id = feature.parent
                                                if parent_id:
                                                    parent = db(query & (table_feature.id == parent_id)).select(table_feature.lat, table_feature.lon, table_feature.parent, limitby=(0, 1)).first()
                                                    lat = parent.lat
                                                    lon = parent.lon
                                                    if (lat is not None) and (lon is not None):
                                                        # Zero is allowed
                                                        return dict(lat=lat, lon=lon)
                                                    else:
                                                        # Try the Parent (e.g. L0)
                                                        parent_id = feature.parent
                                                        if parent_id:
                                                            parent = db(query & (table_feature.id == parent_id)).select(table_feature.lat, table_feature.lon, table_feature.parent, limitby=(0, 1)).first()
                                                            lat = parent.lat
                                                            lon = parent.lon
                                                            if (lat is not None) and (lon is not None):
                                                                # Zero is allowed
                                                                return dict(lat=lat, lon=lon)
        except:
            # Invalid feature_id
            pass
        
        return None

    # -----------------------------------------------------------------------------
    def get_marker(self, feature_id):

        """ Returns the Marker URL for a Feature

            @param feature_id: the feature ID (int) or UUID (str)
            @ToDo: Update for new FeatureClass/Symbology
        """

        cache = self.cache
        db = self.db
        table_feature = db.gis_location
        table_marker = db.gis_marker
        _image = table_marker.image
        #table_fclass = db.gis_feature_class
        #table_symbology = db.gis_symbology_to_feature_class

        config = self.get_config()
        symbology = config.symbology_id

        query = None

        if isinstance(feature_id, int):
            query = (table_feature.id == feature_id)
        elif isinstance(feature_id, str):
            query = (table_feature.uuid == feature_id)

        #feature = db(query).select(table_feature.marker_id,
        #                           table_feature.feature_class_id,
        #                           limitby=(0, 1)).first()
        #if feature:
        #    feature_class =  feature.feature_class_id
        #    marker_id =  feature.marker_id

            # 1st choice for a Marker is the Feature's
        #    if marker_id:
        #        query = (table_marker.id == marker_id)
        #        marker = db(query).select(_image, limitby=(0, 1),
        #                                  cache=cache)
        #        if marker:
        #            return marker.first().image

            # 2nd choice for a Marker is the Symbology for the Feature Class
            #query = (table_symbology.feature_class_id == feature_class) & \
            #        (table_symbology.symbology_id == symbology) & \
            #        (table_marker.id == table_symbology.marker_id)
            #marker = db(query).select(_image, limitby=(0, 1),
            #                          cache=cache)
            #if marker:
            #    return marker.first().image

            # 3rd choice for a Marker is the Feature Class's
            #query = (table_fclass.id == feature_class) & \
            #        (table_marker.id == table_fclass.marker_id)
            #marker = db(query).select(_image, limitby=(0, 1),
            #                          cache=cache)
            #if marker:
            #    return marker.first().image

        # 4th choice for a Marker is the default
        query = (table_marker.id == config.marker_id)
        marker = db(query).select(_image, limitby=(0, 1),
                                  cache=cache)
        if marker:
            return marker.first().image
        else:
            return ""

    # -----------------------------------------------------------------------------
    def latlon_to_wkt(self, lat, lon):
        """
            Convert a LatLon to a WKT string

            >>> s3gis.latlon_to_wkt(6, 80)
            'POINT(80 6)'
        """
        WKT = "POINT(%f %f)" % (lon, lat)
        return WKT

    # -----------------------------------------------------------------------------
    def layer_subtypes(self, layer="openstreetmap"):
        """ Return a lit of the subtypes available for a Layer """

        if layer == "openstreetmap":
            #return ["Mapnik", "Osmarender", "Aerial"]
            return ["Mapnik", "Osmarender", "Taiwan"]
        elif layer == "google":
            return ["Satellite", "Maps", "Hybrid", "Terrain"]
        elif layer == "yahoo":
            return ["Satellite", "Maps", "Hybrid"]
        elif layer == "bing":
            return ["Satellite", "Maps", "Hybrid", "Terrain"]
        else:
            return None


    # -----------------------------------------------------------------------------
    def parse_location(self, wkt, lon=None, lat=None):
        """
            Parses a location from wkt, returning wkt, lat, lon, bounding box and type.
            For points, wkt may be None if lat and lon are provided; wkt will be generated.
            For lines and polygons, the lat, lon returned represent the shape's centroid.
            Centroid and bounding box will be None if shapely is not available.
        """

        if not wkt:
            assert lon is not None and lat is not None, "Need wkt or lon+lat to parse a location"
            wkt = "POINT(%f %f)" % (lon, lat)
            geom_type = GEOM_TYPES["point"]
            bbox = (lon, lat, lon, lat)
        else:
            if SHAPELY:
                shape = shapely.wkt.loads(wkt)
                centroid = shape.centroid
                lat = centroid.y
                lon = centroid.x
                geom_type = GEOM_TYPES[shape.type.lower()]
                bbox = shape.bounds
            else:
                lat = None
                lon = None
                geom_type = GEOM_TYPES[wkt.split("(")[0].lower()]
                bbox = None

        res = {"wkt": wkt, "lat": lat, "lon": lon, "gis_feature_type": geom_type}
        if bbox:
            res["lon_min"], res["lat_min"], res["lon_max"], res["lat_max"] = bbox

        return res

    # -----------------------------------------------------------------------------
    def update_location_tree(self):
        """
            Update the Tree for GIS Locations:
            http://eden.sahanafoundation.org/wiki/HaitiGISToDo#HierarchicalTrees
        """

        db = self.db

        # tbc

        return

    # -----------------------------------------------------------------------------
    def wkt_centroid(self, form):
        """
            OnValidation callback:
            If a Point has LonLat defined: calculate the WKT.
            If a Line/Polygon has WKT defined: validate the format, 
                calculate the LonLat of the Centroid, and set bounds
            Centroid and bounds calculation is done using Shapely, which wraps Geos.
            A nice description of the algorithm is provided here: http://www.jennessent.com/arcgis/shapes_poster.htm
        """

        if not "gis_feature_type" in form.vars:
            # Default to point
            form.vars.gis_feature_type = "1"

        if form.vars.gis_feature_type == "1":
            # Point
            if form.vars.lon == None and form.vars.lat == None:
                # No geo to create WKT from, so skip
                return
            elif form.vars.lat == None:
                form.errors["lat"] = self.messages.lat_empty
                return
            elif form.vars.lon == None:
                form.errors["lon"] = self.messages.lon_empty
                return
            else:
                form.vars.wkt = "POINT(%(lon)f %(lat)f)" % form.vars
                form.vars.lon_min = form.vars.lon_max = form.vars.lon
                form.vars.lat_min = form.vars.lat_max = form.vars.lat
                return

        elif form.vars.gis_feature_type in ("2","3"):
            # Parse WKT for LineString, Polygon
            try:
                try:
                    shape = wkt_loads(form.vars.wkt)
                except:
                    form.errors["wkt"] = {
                        "2": self.messages.invalid_wkt_linestring,
                        "3": self.messages.invalid_wkt_polygon,
                    }
                    return
                centroid_point = shape.centroid
                form.vars.lon = centroid_point.x
                form.vars.lat = centroid_point.y
                bounds = shape.bounds
                form.vars.lon_min = bounds[0]
                form.vars.lat_min = bounds[1]
                form.vars.lon_max = bounds[2]
                form.vars.lat_max = bounds[3]
            except:
                form.errors.gis_feature_type = self.messages.centroid_error
        else:
            form.errors.gis_feature_type = self.messages.unknown_type

        return

    # -----------------------------------------------------------------------------
    def query_features_by_bbox(self, lon_min, lat_min, lon_max, lat_max):
        """
            Returns a query of all locations objects in the given bounding box
        """
        db = self.db
        _location = db.gis_location
        query = (_location.lat_min <= lat_max) & (_location.lat_max >= lat_min) & (_location.lon_min <= lon_max) & (_location.lon_max >= lon_min)
        return query

    # -----------------------------------------------------------------------------
    def get_features_by_bbox(self, lon_min, lat_min, lon_max, lat_max):
        """
            Returns Rows of locations whose shape intersects the given bbox.
        """
        db = self.db
        return db(self.query_features_by_bbox(lon_min, lat_min, lon_max, lat_max)).select()

    # -----------------------------------------------------------------------------
    def _get_features_by_shape(self, shape):
        """
            Returns Rows of locations whose shape intersects the given shape.
            
            Relies on shapely for wkt parsing and intersection.
        """

        db = self.db
        in_bbox = self.query_features_by_bbox(*shape.bounds)
        has_wkt = (db.gis_location.wkt != None) & (db.gis_location.wkt != '')

        for loc in db(in_bbox & has_wkt).select():
            try: 
                location_shape = wkt_loads(loc.wkt)
                if location_shape.intersects(shape):
                    yield loc
            except shapely.geos.ReadingError:
                print >> sys.stderr, "Error reading wkt of location with id %d" % loc.id

    # -----------------------------------------------------------------------------
    def _get_features_by_latlon(self, lat, lon):
        """
        Returns a generator of locations whose shape intersects the given LatLon.
        
        Relies on shapely.
        """

        point = shapely.geometry.point.Point(lon, lat)
        return self._get_features_by_shape(point)

    # -----------------------------------------------------------------------------
    def _get_features_by_feature(self, feature):
        """
        Returns all locations whose geometry intersects the given feature.
        
        Relies on shapely.
        """
        shape = wkt_loads(feature.wkt)
        return self.get_features_by_shape(shape)

    # -----------------------------------------------------------------------------
    if SHAPELY:
        get_features_by_shape = _get_features_by_shape
        get_features_by_latlon = _get_features_by_latlon
        get_features_by_feature = _get_features_by_feature
        
    # -----------------------------------------------------------------------------
    def set_all_bounds(self):
        """
        Sets bounds for all locations without them.
        
        If shapely is present, and a location has wkt, bounds of the geometry 
        are used.  Otherwise, the (lat, lon) are used as bounds.
        """
        db = self.db
        _location = db.gis_location
        no_bounds = (_location.lon_min == None) & (_location.lat_min == None) & (_location.lon_max == None) & (_location.lat_max == None) & (_location.lat != None) & (_location.lon != None)
        if SHAPELY:
            wkt_no_bounds = no_bounds & (_location.wkt != None) & (_location.wkt != '')
            for loc in db(wkt_no_bounds).select():
                try :
                    shape = wkt_loads(loc.wkt)
                except:
                    print >> sys.stderr, "Error reading wkt %s" % loc.wkt
                    continue
                bounds = shape.bounds
                _location[loc.id] = dict(
                    lon_min = bounds[0],
                    lat_min = bounds[1],
                    lon_max = bounds[2],
                    lat_max = bounds[3],
                )
                    
        db(no_bounds).update(lon_min=_location.lon, lat_min=_location.lat, lon_max=_location.lon, lat_max=_location.lat)

    # -----------------------------------------------------------------------------
    def show_map( self,
                  height = None,
                  width = None,
                  bbox = {},
                  lat = None,
                  lon = None,
                  zoom = None,
                  projection = None,
                  add_feature = False,
                  add_feature_active = False,
                  feature_queries = [],
                  wms_browser = {},
                  catalogue_overlays = False,
                  catalogue_toolbar = False,
                  legend = False,
                  toolbar = False,
                  search = False,
                  mouse_position = "normal",
                  print_tool = {},
                  mgrs = {},
                  window = False,
                  window_hide = False,
                  collapsed = False,
                  public_url = "http://127.0.0.1:8000"
                ):
        """
            Returns the HTML to display a map
            
            Normally called in the controller as: map = gis.show_map()
            In the view, put: {{=XML(map)}}

            @param height: Height of viewport (if not provided then the default setting from the Map Service Catalogue is used)
            @param width: Width of viewport (if not provided then the default setting from the Map Service Catalogue is used)
            @param bbox: default Bounding Box of viewport (if not provided then the Lat/Lon/Zoom are used) (Dict):
                {
                "max_lat" : float,
                "max_lon" : float,
                "min_lat" : float,
                "min_lon" : float
                }
            @param lat: default Latitude of viewport (if not provided then the default setting from the Map Service Catalogue is used)
            @param lon: default Longitude of viewport (if not provided then the default setting from the Map Service Catalogue is used)
            @param zoom: default Zoom level of viewport (if not provided then the default setting from the Map Service Catalogue is used)
            @param projection: EPSG code for the Projection to use (if not provided then the default setting from the Map Service Catalogue is used)
            @param add_feature: Whether to include a DrawFeature control to allow adding a marker to the map
            @param add_feature_active: Whether the DrawFeature control should be active by default
            @param feature_queries: Feature Queries to overlay onto the map & their options (List of Dicts):
                [{
                 name   : "MyLabel",    # A string: the label for the layer
                 query  : query,        # A gluon.sql.Rows of gis_locations, which can be from a simple query or a Join. Extra fields can be added for 'marker' or 'shape' (with optional 'color' & 'size') & 'popup_label'
                 active : False,        # Is the feed displayed upon load or needs ticking to load afterwards?
                 popup_url : None,      # The URL which will be used to fill the pop-up. it will be appended by the Location ID.
                 marker : None,         # The marker_id for the icon used to display the feature (over-riding the normal process).
                 polygons : False       # Use Polygon data, if-available (defaults to just using Point)
                }]
            @param wms_browser: WMS Server's GetCapabilities & options (dict)
                {
                name: string,           # Name for the Folder in LayerTree
                url: string             # URL of GetCapabilities
                }
            @param catalogue_overlays: Show the Overlays from the GIS Catalogue (@ToDo: make this a dict of which external overlays to allow)
            @param catalogue_toolbar: Show the Catalogue Toolbar
            @param legend: Show the Legend panel
            @param toolbar: Show the Icon Toolbar of Controls
            @param search: Show the Geonames search box
            @param mouse_position: Show the current coordinates in the bottom-right of the map. 3 Options: 'normal' (default), 'mgrs' (MGRS), False (off)
            @param print_tool: Show a print utility (NB This requires server-side support: http://eden.sahanafoundation.org/wiki/BluePrintGISPrinting)
                {
                url: string,            # URL of print service (e.g. http://localhost:8080/geoserver/pdf/)
                mapTitle: string        # Title for the Printed Map (optional)
                subTitle: string        # subTitle for the Printed Map (optional)
                }
            @param mgrs: Use the MGRS Control to select PDFs
                {
                name: string,           # Name for the Control
                url: string             # URL of PDF server
                }
            @param window: Have viewport pop out of page into a resizable window
            @param window_hide: Have the window hidden by default, ready to appear (e.g. on clicking a button)
            @param collapsed: Start the Tools panel (West region) collapsed
            @param public_url: pass from model (not yet defined when Module instantiated
        """

        request = self.request
        response = self.response
        if not response.warning:
            response.warning = ""
        session = self.session
        T = self.T
        db = self.db
        auth = self.auth
        cache = self.cache
        deployment_settings = self.deployment_settings

        # Read configuration
        config = self.get_config()
        if not height:
            height = config.map_height
        if not width:
            width = config.map_width
        if bbox and (-90 < bbox["max_lat"] < 90) and (-90 < bbox["min_lat"] < 90) and (-180 < bbox["max_lon"] < 180) and (-180 < bbox["min_lon"] < 180):
            # We have sane Bounds provided, so we should use them
            pass
        else:
            # No bounds or we've been passed bounds which aren't sane
            bbox = None
        # Support bookmarks (such as from the control)
        # - these over-ride the arguments
        if "lat" in request.vars:
            lat = request.vars.lat
        elif not lat:
            lat = config.lat
        if "lon" in request.vars:
            lon = request.vars.lon
        elif not lon:
            lon = config.lon
        if "zoom" in request.vars:
            zoom = request.vars.zoom
        elif not zoom:
            zoom = config.zoom
        if not projection:
            projection = config.epsg
        units = config.units
        maxResolution = config.maxResolution
        maxExtent = config.maxExtent
        numZoomLevels = config.zoom_levels
        marker_default = config.marker_id
        cluster_distance = config.cluster_distance
        cluster_threshold = config.cluster_threshold

        markers = {}
        
        html = DIV(_id="map_wrapper")

        #####
        # CSS
        #####
        if session.s3.debug:
            html.append(LINK( _rel="stylesheet", _type="text/css", _href=URL(r=request, c="static", f="styles/gis/ie6-style.css"), _media="screen", _charset="utf-8") )
            html.append(LINK( _rel="stylesheet", _type="text/css", _href=URL(r=request, c="static", f="styles/gis/google.css"), _media="screen", _charset="utf-8") )
            html.append(LINK( _rel="stylesheet", _type="text/css", _href=URL(r=request, c="static", f="styles/gis/geoext-all-debug.css"), _media="screen", _charset="utf-8") )
            html.append(LINK( _rel="stylesheet", _type="text/css", _href=URL(r=request, c="static", f="styles/gis/gis.css"), _media="screen", _charset="utf-8") )
        else:
            html.append(LINK( _rel="stylesheet", _type="text/css", _href=URL(r=request, c="static", f="styles/gis/gis.min.css"), _media="screen", _charset="utf-8") )

        ######
        # HTML
        ######
        # Catalogue Toolbar
        if catalogue_toolbar:
            if auth.has_membership(1):
                config_button = SPAN( A(T("Defaults"), _href=URL(r=request, c="gis", f="config", args=["1", "update"])), _class="rheader_tab_other" )
            else:
                config_button = SPAN( A(T("Defaults"), _href=URL(r=request, c="gis", f="config", args=["1", "display"])), _class="rheader_tab_other" )
            catalogue_toolbar = DIV(
                config_button,
                SPAN( A(T("Layers"), _href=URL(r=request, c="gis", f="map_service_catalogue")), _class="rheader_tab_other" ),
                #SPAN( A(T("Feature Layers"), _href=URL(r=request, c="gis", f="feature_layer")), _class="rheader_tab_other" ),
                #SPAN( A(T("Feature Classes"), _href=URL(r=request, c="gis", f="feature_class")), _class="rheader_tab_other" ),
                SPAN( A(T("Markers"), _href=URL(r=request, c="gis", f="marker")), _class="rheader_tab_other" ),
                SPAN( A(T("Keys"), _href=URL(r=request, c="gis", f="apikey")), _class="rheader_tab_other" ),
                SPAN( A(T("Projections"), _href=URL(r=request, c="gis", f="projection")), _class="rheader_tab_other" ),
                _id="rheader_tabs")
            html.append(catalogue_toolbar)

        # Map (Embedded not Window)
        html.append(DIV(_id="map_panel"))

        # Status Reports
        html.append(TABLE(TR(
            TD(
                # Somewhere to report details of OSM File Features via on_feature_hover()
                DIV(_id="status_osm"),
                _style="border: 0px none ;", _valign="top",
            ),
            TD(
                # Somewhere to report whether GeoRSS feed is using cached copy or completely inaccessible
                DIV(_id="status_georss"),
                # Somewhere to report whether KML feed is using cached copy or completely inaccessible
                DIV(_id="status_kml"),
                # Somewhere to report if Files are not found
                DIV(_id="status_files"),
                _style="border: 0px none ;", _valign="top",
            )
        )))

        #########
        # Scripts
        #########
        if session.s3.debug:
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/gis/openlayers/lib/OpenLayers.js")))
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/gis/OpenStreetMap.js")))
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/gis/MP.js")))
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/gis/usng2.js")))
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/gis/RemoveFeature.js")))
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/gis/osm_styles.js")))
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/gis/geoext/lib/GeoExt.js")))
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/gis/geoext/ux/GeoNamesSearchCombo.js")))
        else:
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/gis/OpenLayers.js")))
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/gis/OpenStreetMap.js")))
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/gis/RemoveFeature.js")))
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/gis/GeoExt.js")))

        if print_tool:
            url = print_tool["url"] + "info.json?var=printCapabilities"
            html.append(SCRIPT(_type="text/javascript", _src=url))

        #######
        # Tools
        #######

        # MGRS
        if mgrs:
            mgrs_html = """
var selectPdfControl = new OpenLayers.Control();
OpenLayers.Util.extend( selectPdfControl, {
    draw: function () {
        this.box = new OpenLayers.Handler.Box( this, {
                'done': this.getPdf
            });
        this.box.activate();
        },
    response: function(req) {
        this.w.destroy();
        var gml = new OpenLayers.Format.GML();
        var features = gml.read(req.responseText);
        var html = features.length + ' pdfs. <br /><ul>';
        if (features.length) {
            for (var i = 0; i < features.length; i++) {
                var f = features[i];
                var text = f.attributes.utm_zone + f.attributes.grid_zone + f.attributes.grid_square + f.attributes.easting + f.attributes.northing;
                html += "<li><a href='" + features[i].attributes.url + "'>" + text + '</a></li>';
            }
        }
        html += '</ul>';
        this.w = new Ext.Window({
            'html': html,
            width: 300,
            'title': 'Results',
            height: 200
        });
        this.w.show();
    },
    getPdf: function (bounds) {
        var ll = map.getLonLatFromPixel(new OpenLayers.Pixel(bounds.left, bounds.bottom)).transform(projection_current, proj4326);
        var ur = map.getLonLatFromPixel(new OpenLayers.Pixel(bounds.right, bounds.top)).transform(projection_current, proj4326);
        var boundsgeog = new OpenLayers.Bounds(ll.lon, ll.lat, ur.lon, ur.lat);
        bbox = boundsgeog.toBBOX();
        OpenLayers.Request.GET({
            url: '""" + str(XML(mgrs["url"])) + """&bbox=' + bbox,
            callback: OpenLayers.Function.bind(this.response, this)
        });
        this.w = new Ext.Window({
            'html':'Searching """ + mgrs["name"] + """, please wait.',
            width: 200,
            'title': "Please Wait."
            });
        this.w.show();
    }
});
"""
            mgrs2 = """
    // MGRS Control
    var mgrsButton = new GeoExt.Action({
        text: 'Select """ + mgrs["name"] + """',
        control: selectPdfControl,
        map: map,
        toggleGroup: toggleGroup,
        allowDepress: false,
        tooltip: 'Select """ + mgrs["name"] + """',
        // check item options group: 'draw'
    });
    """
            mgrs3 = """
    toolbar.add(mgrsButton);
    toolbar.addSeparator();
    """
        else:
            mgrs_html = ""
            mgrs2 = ""
            mgrs3 = ""

        # Legend panel
        if legend:
            legend1= """
        legendPanel = new GeoExt.LegendPanel({
            id: 'legendpanel',
            title: '""" + str(T("Legend")) + """',
            defaults: {
                labelCls: 'mylabel',
                style: 'padding:5px'
            },
            bodyStyle: 'padding:5px',
            autoScroll: true,
            collapsible: true,
            collapseMode: 'mini',
            lines: false
        });
        """
            legend2 = ", legendPanel"
        else:
            legend1= ""
            legend2 = ""

        # Draw Feature Control
        crosshair_on = "$('.olMapViewport').addClass('crosshair');"
        crosshair_off = "$('.olMapViewport').removeClass('crosshair');"
        crosshair = ""
        if add_feature:
            if add_feature_active:
                draw_depress = "true"
                crosshair = crosshair_on
            else:
                draw_depress = "false"
            draw_feature = """
        // Controls for Draft Features
        // - interferes with popupControl which is active on allLayers
        //var selectControl = new OpenLayers.Control.SelectFeature(draftLayer, {
        //    onSelect: onFeatureSelect,
        //    onUnselect: onFeatureUnselect,
        //    multiple: false,
        //    clickout: true,
        //    isDefault: true
        //});

        //var removeControl = new OpenLayers.Control.RemoveFeature(draftLayer, {
        //    onDone: function(feature) {
        //        console.log(feature)
        //    }
        //});

        //var selectButton = new GeoExt.Action({
            //control: selectControl,
        //    map: map,
        //    iconCls: 'searchclick',
            // button options
        //    tooltip: '""" + str(T("Query Feature")) + """',
        //    toggleGroup: 'controls',
        //    enableToggle: true
        //});

        pointButton = new GeoExt.Action({
            control: new OpenLayers.Control.DrawFeature(draftLayer, OpenLayers.Handler.Point, {
                // custom Callback
                'featureAdded': function(feature){
                    // Remove previous point
                    if (lastDraftFeature){
                        lastDraftFeature.destroy();
                    }
                    // updateFormFields
                    centerPoint = feature.geometry.getBounds().getCenterLonLat();
                    centerPoint.transform(projection_current, proj4326);
                    $('#gis_location_lon').val(centerPoint.lon);
                    $('#gis_location_lat').val(centerPoint.lat);
                    // Prepare in case user selects a new point
                    lastDraftFeature = feature;
                }
            }),
            handler: function(){
                if (pointButton.items[0].pressed) {
                    """ + crosshair_on + """
                } else {
                    """ + crosshair_off + """
                }
            },
            map: map,
            iconCls: 'drawpoint-off',
            tooltip: '""" + str(T("Add Point")) + """',
            toggleGroup: 'controls',
            allowDepress: true,
            enableToggle: true,
            pressed: """ + draw_depress + """
        });
        
        //var lineButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.DrawFeature(draftLayer, OpenLayers.Handler.Path),
        //    map: map,
        //    iconCls: 'drawline-off',
        //    tooltip: '""" + str(T("Add Line")) + """',
        //    toggleGroup: 'controls'
        //});

        //var polygonButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.DrawFeature(draftLayer, OpenLayers.Handler.Polygon),
        //    map: map,
        //    iconCls: 'drawpolygon-off',
        //    tooltip: '""" + str(T("Add Polygon")) + """',
        //    toggleGroup: 'controls'
        //});

        //var dragButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.DragFeature(draftLayer),
        //    map: map,
        //    iconCls: 'movefeature',
        //    tooltip: '""" + str(T("Move Feature: Drag feature to desired location")) + """',
        //    toggleGroup: 'controls'
        //});

        //var resizeButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.ModifyFeature(draftLayer, { mode: OpenLayers.Control.ModifyFeature.RESIZE }),
        //    map: map,
        //    iconCls: 'resizefeature',
        //    tooltip: '""" + str(T("Resize Feature: Select the feature you wish to resize & then Drag the associated dot to your desired size")) + """',
        //    toggleGroup: 'controls'
        //});

        //var rotateButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.ModifyFeature(draftLayer, { mode: OpenLayers.Control.ModifyFeature.ROTATE }),
        //    map: map,
        //    iconCls: 'rotatefeature',
        //    tooltip: '""" + str(T("Rotate Feature: Select the feature you wish to rotate & then Drag the associated dot to rotate to your desired location")) + """',
        //    toggleGroup: 'controls'
        //});

        //var modifyButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.ModifyFeature(draftLayer),
        //    map: map,
        //    iconCls: 'modifyfeature',
        //    tooltip: '""" + str(T("Modify Feature: Select the feature you wish to deform & then Drag one of the dots to deform the feature in your chosen manner")) + """',
        //    toggleGroup: 'controls'
        //});

        //var removeButton = new GeoExt.Action({
        //    control: removeControl,
        //    map: map,
        //    iconCls: 'removefeature',
        //    tooltip: '""" + str(T("Remove Feature: Select the feature you wish to remove & press the delete key")) + """',
        //    toggleGroup: 'controls'
        //});
        """
            draw_feature2 = """
        // Draw Controls
        //toolbar.add(selectButton);
        toolbar.add(pointButton);
        //toolbar.add(lineButton);
        //toolbar.add(polygonButton);
        //toolbar.add(dragButton);
        //toolbar.add(resizeButton);
        //toolbar.add(rotateButton);
        //toolbar.add(modifyButton);
        //toolbar.add(removeButton);
        toolbar.addSeparator();
        """
        else:
            draw_feature = ""
            draw_feature2 = ""

        # Toolbar
        if toolbar or add_feature:
            #if 1 in session.s3.roles or auth.shn_has_role("MapAdmin"):
            if auth.is_logged_in():
                # Provide a way to save the viewport
                # @ToDo Extend to personalised Map Views
                # @ToDo Extend to choice of Base Layer & Enabled status of Overlays
                save_button = """
        var saveButton = new Ext.Toolbar.Button({
            iconCls: 'save',
            tooltip: '""" + str(T("Save: Default Lat, Lon & Zoom for the Viewport")) + """',
            handler: function() {
                // Read current settings from map
                var lonlat = map.getCenter();
                var zoom_current = map.getZoom();
                // Convert back to LonLat for saving
                lonlat.transform(map.getProjectionObject(), proj4326);
                // Use AJAX to send back
                var url = '""" + URL(r=request, c="gis", f="config", args=["1.url", "update"]) + """';
                Ext.Ajax.request({
                    url: url,
                    method: 'GET',
                    params: {
                        uuid: '""" + config.uuid + """',
                        lat: lonlat.lat,
                        lon: lonlat.lon,
                        zoom: zoom_current
                    }
                });
            }
        });
        """
                save_button2 = """
        toolbar.addSeparator();
        // Save Viewport
        toolbar.addButton(saveButton);
        """
            else:
                save_button = ""
                save_button2 = ""

            if add_feature:
                pan_depress = "false"
            else:
                pan_depress = "true"
            
            toolbar = """
        toolbar = mapPanel.getTopToolbar();
        
        // OpenLayers controls
        
        // Measure Controls
        var measureSymbolizers = {
            'Point': {
                pointRadius: 5,
                graphicName: 'circle',
                fillColor: 'white',
                fillOpacity: 1,
                strokeWidth: 1,
                strokeOpacity: 1,
                strokeColor: '#f5902e'
            },
            'Line': {
                strokeWidth: 3,
                strokeOpacity: 1,
                strokeColor: '#f5902e',
                strokeDashstyle: 'dash'
            },
            'Polygon': {
                strokeWidth: 2,
                strokeOpacity: 1,
                strokeColor: '#f5902e',
                fillColor: 'white',
                fillOpacity: 0.5
            }
        };
        var styleMeasure = new OpenLayers.Style();
        styleMeasure.addRules([
            new OpenLayers.Rule({symbolizer: measureSymbolizers})
        ]);
        var styleMapMeasure = new OpenLayers.StyleMap({'default': styleMeasure});
        
        var length = new OpenLayers.Control.Measure(
            OpenLayers.Handler.Path, {
                geodesic: true,
                persist: true,
                handlerOptions: {
                    layerOptions: {styleMap: styleMapMeasure}
                }
            }
        );
        length.events.on({
            'measure': function(evt) {
                alert('""" + str(T("The length is ")) + """' + evt.measure.toFixed(2) + ' ' + evt.units);
            }
        });
        var area = new OpenLayers.Control.Measure(
            OpenLayers.Handler.Polygon, {
                geodesic: true,
                persist: true,
                handlerOptions: {
                    layerOptions: {styleMap: styleMapMeasure}
                }
            }
        );
        area.events.on({
            'measure': function(evt) {
                alert('""" + str(T("The area is ")) + """' + evt.measure.toFixed(2) + ' ' + evt.units + '2');
            }
        });

        var nav = new OpenLayers.Control.NavigationHistory();

        // GeoExt Buttons
        var zoomfull = new GeoExt.Action({
            control: new OpenLayers.Control.ZoomToMaxExtent(),
            map: map,
            iconCls: 'zoomfull',
            // button options
            tooltip: '""" + str(T("Zoom to maximum map extent")) + """'
        });

        var zoomout = new GeoExt.Action({
            control: new OpenLayers.Control.ZoomBox({ out: true }),
            map: map,
            iconCls: 'zoomout',
            // button options
            tooltip: '""" + str(T("Zoom Out: click in the map or use the left mouse button and drag to create a rectangle")) + """',
            toggleGroup: 'controls'
        });

        var zoomin = new GeoExt.Action({
            control: new OpenLayers.Control.ZoomBox(),
            map: map,
            iconCls: 'zoomin',
            // button options
            tooltip: '""" + str(T("Zoom In: click in the map or use the left mouse button and drag to create a rectangle")) + """',
            toggleGroup: 'controls'
        });

        var pan = new GeoExt.Action({
            control: new OpenLayers.Control.Navigation(),
            map: map,
            iconCls: 'pan-off',
            // button options
            tooltip: '""" + str(T("Pan Map: keep the left mouse button pressed and drag the map")) + """',
            toggleGroup: 'controls',
            allowDepress: true,
            pressed: """ + pan_depress + """
        });

        // 1st of these 2 to get activated cannot be deselected!
        var lengthButton = new GeoExt.Action({
            control: length,
            map: map,
            iconCls: 'measure-off',
            // button options
            tooltip: '""" + str(T("Measure Length: Click the points along the path & end with a double-click")) + """',
            toggleGroup: 'controls',
            allowDepress: true,
            enableToggle: true
        });

        var areaButton = new GeoExt.Action({
            control: area,
            map: map,
            iconCls: 'measure-area',
            // button options
            tooltip: '""" + str(T("Measure Area: Click the points around the polygon & end with a double-click")) + """',
            toggleGroup: 'controls',
            allowDepress: true,
            enableToggle: true
        });

        """ + mgrs2 + """

        """ + draw_feature + """

        var navPreviousButton = new Ext.Toolbar.Button({
            iconCls: 'back',
            tooltip: '""" + str(T("Previous View")) + """',
            handler: nav.previous.trigger
        });

        var navNextButton = new Ext.Toolbar.Button({
            iconCls: 'next',
            tooltip: '""" + str(T("Next View")) + """',
            handler: nav.next.trigger
        });

        """ + save_button + """

        // Add to Map & Toolbar
        toolbar.add(zoomfull);
        toolbar.add(zoomfull);
        toolbar.add(zoomout);
        toolbar.add(zoomin);
        toolbar.add(pan);
        toolbar.addSeparator();
        // Measure Tools
        toolbar.add(lengthButton);
        toolbar.add(areaButton);
        toolbar.addSeparator();
        """ + mgrs3 + """
        """ + draw_feature2 + """
        // Navigation
        map.addControl(nav);
        nav.activate();
        toolbar.addButton(navPreviousButton);
        toolbar.addButton(navNextButton);
        """ + save_button2
            toolbar2 = "Ext.QuickTips.init();"
        else:
            toolbar = ""
            toolbar2 = ""

        # Search
        if search:
            search = """
        var mapSearch = new GeoExt.ux.geonames.GeoNamesSearchCombo({
            map: map,
            zoom: 8
         });

        var searchCombo = new Ext.Panel({
            title: '""" + str(T("Search Geonames")) + """',
            layout: 'border',
            rootVisible: false,
            split: true,
            autoScroll: true,
            collapsible: true,
            collapseMode: 'mini',
            lines: false,
            html: '""" + str(T("Geonames.org search requires Internet connectivity!")) + """',
            items: [{
                    region: 'center',
                    items: [ mapSearch ]
                }]
        });
        """
            search2 = """,
                            searchCombo"""
        else:
            search = ""
            search2 = ""

        # WMS Browser
        if wms_browser:
            name = wms_browser["name"]
            # urlencode the URL
            url = urllib.quote(wms_browser["url"])
            layers_wms_browser = """
        var root = new Ext.tree.AsyncTreeNode({
            expanded: true,
            loader: new GeoExt.tree.WMSCapabilitiesLoader({
                url: OpenLayers.ProxyHost + '""" + url + """',
                layerOptions: {buffer: 1, singleTile: false, ratio: 1, wrapDateLine: true},
                layerParams: {'TRANSPARENT': 'TRUE'},
                // customize the createNode method to add a checkbox to nodes
                createNode: function(attr) {
                    attr.checked = attr.leaf ? false : undefined;
                    return GeoExt.tree.WMSCapabilitiesLoader.prototype.createNode.apply(this, [attr]);
                }
            })
        });
        wmsBrowser = new Ext.tree.TreePanel({
            id: 'wmsbrowser',
            title: '""" + name + """',
            root: root,
            rootVisible: false,
            split: true,
            autoScroll: true,
            collapsible: true,
            collapseMode: 'mini',
            lines: false,
            listeners: {
                // Add layers to the map when checked, remove when unchecked.
                // Note that this does not take care of maintaining the layer
                // order on the map.
                'checkchange': function(node, checked) {
                    if (checked === true) {
                        mapPanel.map.addLayer(node.attributes.layer);
                    } else {
                        mapPanel.map.removeLayer(node.attributes.layer);
                    }
                }
            }
        });
        """
            layers_wms_browser2 = """,
                            wmsBrowser"""
        else:
            layers_wms_browser = ""
            layers_wms_browser2 = ""

        # Mouse Position
        if mouse_position and mouse_position is not "mgrs":
            mouse_position = "map.addControl(new OpenLayers.Control.MousePosition());"
        elif mouse_position == "mgrs":
            mouse_position = "map.addControl(new OpenLayers.Control.MGRSMousePosition());"
        else:
            mouse_position = ""
        
        # Print
        if print_tool:
            url = print_tool["url"]
            if "title" in print_tool:
                mapTitle = str(print_tool["mapTitle"])
            else:
                mapTitle = str(T("Map from Sahana Eden"))
            if "subtitle" in print_tool:
                subTitle = str(print_tool["subTitle"])
            else:
                subTitle = str(T("Printed from Sahana Eden"))
            if session.auth:
                creator = session.auth.user.email
            else:
                creator = ""
            print_tool1 = """
        if (typeof(printCapabilities) != 'undefined') {
            // info.json from script headers OK
            printProvider = new GeoExt.data.PrintProvider({
                //method: 'POST',
                //url: '""" + url + """',
                method: 'GET', // 'POST' recommended for production use
                capabilities: printCapabilities, // from the info.json returned from the script headers
                customParams: {
                    mapTitle: '""" + mapTitle + """',
                    subTitle: '""" + subTitle + """',
                    creator: '""" + creator + """'
                }
            });
            // Our print page. Stores scale, center and rotation and gives us a page
            // extent feature that we can add to a layer.
            printPage = new GeoExt.data.PrintPage({
                printProvider: printProvider
            });
            
            //var printExtent = new GeoExt.plugins.PrintExtent({
            //    printProvider: printProvider
            //});
            // A layer to display the print page extent
            //var pageLayer = new OpenLayers.Layer.Vector('""" + str(T("Print Extent")) + """');
            //pageLayer.addFeatures(printPage.feature);
            //pageLayer.setVisibility(false);
            //map.addLayer(pageLayer);
            //var pageControl = new OpenLayers.Control.TransformFeature();
            //map.addControl(pageControl);                                
            //map.setOptions({
            //    eventListeners: {
                    // recenter/resize page extent after pan/zoom
            //        'moveend': function() {
            //            printPage.fit(mapPanel, true);
            //        }
            //    }
            //});
            // The form with fields controlling the print output
            var formPanel = new Ext.form.FormPanel({
                title: '""" + str(T("Print Map")) + """',
                rootVisible: false,
                split: true,
                autoScroll: true,
                collapsible: true,
                collapsed: true,
                collapseMode: 'mini',
                lines: false,
                bodyStyle: 'padding:5px',
                labelAlign: 'top',
                defaults: {anchor: '100%'},
                listeners: {
                    'expand': function() {
                        //if (null == mapPanel.map.getLayersByName('""" + str(T("Print Extent")) + """')[0]) {
                        //    mapPanel.map.addLayer(pageLayer);
                        //}
                        if (null == mapPanel.plugins[0]) {
                            //map.addLayer(pageLayer);
                            //pageControl.activate();
                            //mapPanel.plugins = [ new GeoExt.plugins.PrintExtent({
                            //    printProvider: printProvider,
                            //    map: map,
                            //    layer: pageLayer,
                            //    control: pageControl
                            //}) ];
                            //mapPanel.plugins[0].addPage();
                        }
                    },
                    'collapse':  function() {
                        //mapPanel.map.removeLayer(pageLayer);
                        //if (null != mapPanel.plugins[0]) {
                        //    map.removeLayer(pageLayer);
                        //    mapPanel.plugins[0].removePage(mapPanel.plugins[0].pages[0]);
                        //    mapPanel.plugins = [];
                        //}
                    }
                },
                items: [{
                    xtype: 'textarea',
                    name: 'comment',
                    value: '',
                    fieldLabel: '""" + str(T("Comment")) + """',
                    plugins: new GeoExt.plugins.PrintPageField({
                        printPage: printPage
                    })
                }, {
                    xtype: 'combo',
                    store: printProvider.layouts,
                    displayField: 'name',
                    fieldLabel: '""" + str(T("Layout")) + """',
                    typeAhead: true,
                    mode: 'local',
                    triggerAction: 'all',
                    plugins: new GeoExt.plugins.PrintProviderField({
                        printProvider: printProvider
                    })
                }, {
                    xtype: 'combo',
                    store: printProvider.dpis,
                    displayField: 'name',
                    fieldLabel: '""" + str(T("Resolution")) + """',
                    tpl: '<tpl for="."><div class="x-combo-list-item">{name} dpi</div></tpl>',
                    typeAhead: true,
                    mode: 'local',
                    triggerAction: 'all',
                    plugins: new GeoExt.plugins.PrintProviderField({
                        printProvider: printProvider
                    }),
                    // the plugin will work even if we modify a combo value
                    setValue: function(v) {
                        v = parseInt(v) + ' dpi';
                        Ext.form.ComboBox.prototype.setValue.apply(this, arguments);
                    }
                //}, {
                //    xtype: 'combo',
                //    store: printProvider.scales,
                //    displayField: 'name',
                //    fieldLabel: '""" + str(T("Scale")) + """',
                //    typeAhead: true,
                //    mode: 'local',
                //    triggerAction: 'all',
                //    plugins: new GeoExt.plugins.PrintPageField({
                //        printPage: printPage
                //    })
                //}, {
                //    xtype: 'textfield',
                //    name: 'rotation',
                //    fieldLabel: '""" + str(T("Rotation")) + """',
                //    plugins: new GeoExt.plugins.PrintPageField({
                //        printPage: printPage
                //    })
                }],
                buttons: [{
                    text: '""" + str(T("Create PDF")) + """',
                    handler: function() {
                        // the PrintExtent plugin is the mapPanel's 1st plugin
                        //mapPanel.plugins[0].print();
                        // convenient way to fit the print page to the visible map area
                        printPage.fit(mapPanel, true);
                        // print the page, including the legend, where available
                        if (null == legendPanel) {
                            printProvider.print(mapPanel, printPage);
                        } else {
                            printProvider.print(mapPanel, printPage, {legend: legendPanel});
                        }
                    }
                }]
            });
        } else {
            // Display error diagnostic
            var formPanel = new Ext.Panel ({
                title: '""" + str(T("Print Map")) + """',
                rootVisible: false,
                split: true,
                autoScroll: true,
                collapsible: true,
                collapsed: true,
                collapseMode: 'mini',
                lines: false,
                bodyStyle: 'padding:5px',
                labelAlign: 'top',
                defaults: {anchor: '100%'},
                html: '""" + str(T("Printing disabled since server not accessible: ")) + "<BR />" + url + """'
            });
        }
        """
            print_tool2 = """,
                    formPanel"""
        else:
            print_tool1 = ""
            print_tool2 = ""
            
        ##########
        # Settings
        ##########

        # Strategy
        # Need to be uniquely instantiated
        strategy_fixed = """new OpenLayers.Strategy.Fixed()"""
        strategy_cluster = """new OpenLayers.Strategy.Cluster({distance: """ + str(cluster_distance) + """, threshold: """ + str(cluster_threshold) + """})"""

        # Layout
        if window and window_hide:
            layout = """
        win = new Ext.Window({
            collapsible: true,
            constrain: true,
            closeAction: 'hide',
            """
            layout2 = """
        //win.show();
        //win.maximize();
        """
        elif window:
            layout = """
        win = new Ext.Window({
            collapsible: true,
            constrain: true,
            """
            layout2 = """
        win.show();
        win.maximize();
        """
        else:
            # Embedded
            layout = """
        var panel = new Ext.Panel({
            renderTo: "map_panel",
            """
            layout2 = ""

        # Collapsed
        if collapsed:
            collapsed = "true"
        else:
            collapsed = "false"
            
        # Bounding Box
        if bbox:
            # Calculate from Bounds
            center = """
    var bottom_left = new OpenLayers.LonLat(""" + str(bbox["min_lon"]) + "," + str(bbox["min_lat"]) + """);
    bottom_left.transform(proj4326, projection_current);
    var left = bottom_left.lon;
    var bottom = bottom_left.lat;
    top_right = new OpenLayers.LonLat(""" + str(bbox["max_lon"]) + "," + str(bbox["max_lat"]) + """);
    top_right.transform(proj4326, projection_current);
    var right = top_right.lon;
    var top = top_right.lat;
    var bounds = OpenLayers.Bounds.fromArray([left, bottom, right, top]);
    var center = bounds.getCenterLonLat();
    """
            zoomToExtent = """
        map.zoomToExtent(bounds);
        """
        else:
            center = """
    var lat = """ + str(lat) + """;
    var lon = """ + str(lon) + """;
    var center = new OpenLayers.LonLat(lon, lat);
    center.transform(proj4326, projection_current);
    """
            zoomToExtent = ""
            
        ########
        # Layers
        ########

        #
        # Base Layers
        #

        layers_openstreetmap = ""
        layers_google = ""
        layers_yahoo = ""
        layers_bing = ""

        # OpenStreetMap
        gis_layer_openstreetmap_subtypes = self.layer_subtypes("openstreetmap")
        openstreetmap = Storage()
        openstreetmap_enabled = db(db.gis_layer_openstreetmap.enabled == True).select()
        for layer in openstreetmap_enabled:
            for subtype in gis_layer_openstreetmap_subtypes:
                if layer.subtype == subtype:
                    openstreetmap["%s" % subtype] = layer.name

        if openstreetmap:
            functions_openstreetmap = """
        function osm_getTileURL(bounds) {
            var res = this.map.getResolution();
            var x = Math.round((bounds.left - this.maxExtent.left) / (res * this.tileSize.w));
            var y = Math.round((this.maxExtent.top - bounds.top) / (res * this.tileSize.h));
            var z = this.map.getZoom();
            var limit = Math.pow(2, z);
            if (y < 0 || y >= limit) {
                return OpenLayers.Util.getImagesLocation() + '404.png';
            } else {
                x = ((x % limit) + limit) % limit;
                return this.url + z + '/' + x + '/' + y + '.' + this.type;
            }
        }
        """
            if openstreetmap.Mapnik:
                layers_openstreetmap += """
        //var mapnik = new OpenLayers.Layer.TMS( '""" + openstreetmap.Mapnik + """', 'http://tile.openstreetmap.org/', {type: 'png', getURL: osm_getTileURL, displayOutsideMaxExtent: true, attribution: '<a href="http://www.openstreetmap.org/">OpenStreetMap</a>' } );
        var mapnik = new OpenLayers.Layer.OSM.Mapnik('""" + openstreetmap.Mapnik + """', {
                displayOutsideMaxExtent: true,  // Not working! Can revert to TMS, if necessary
                wrapDateLine: true,
                layerCode: 'M'
        });
        map.addLayer(mapnik);
                    """
            if openstreetmap.Osmarender:
                layers_openstreetmap += """
        //var osmarender = new OpenLayers.Layer.TMS( '""" + openstreetmap.Osmarender + """', 'http://tah.openstreetmap.org/Tiles/tile/', {type: 'png', getURL: osm_getTileURL, displayOutsideMaxExtent: true, attribution: '<a href="http://www.openstreetmap.org/">OpenStreetMap</a>' } );
        var osmarender = new OpenLayers.Layer.OSM.Osmarender('""" + openstreetmap.Osmarender + """', {
            layerCode: 'O',
            displayOutsideMaxExtent: true,  // Not working! Can revert to TMS, if necessary
            wrapDateLine: true
        });
        map.addLayer(osmarender);
                    """
            if openstreetmap.Aerial:
                layers_openstreetmap += """
        var oam = new OpenLayers.Layer.TMS( '""" + openstreetmap.Aerial + """', 'http://tile.openaerialmap.org/tiles/1.0.0/openaerialmap-900913/', {type: 'png', getURL: osm_getTileURL } );
        map.addLayer(oam);
                    """
            if openstreetmap.Taiwan:
                layers_openstreetmap += """
        var osmtw = new OpenLayers.Layer.TMS( '""" + openstreetmap.Taiwan + """', 'http://tile.openstreetmap.tw/tiles/', {type: 'png', getURL: osm_getTileURL } );
        map.addLayer(osmtw);
                    """
        else:
            functions_openstreetmap = ""

        # Only enable commercial base layers if using a sphericalMercator projection
        if projection == 900913:

            # Google
            gis_layer_google_subtypes = self.layer_subtypes("google")
            google = Storage()
            google_enabled = db(db.gis_layer_google.enabled == True).select()
            if google_enabled:
                google.key = self.get_api_key("google")
                for layer in google_enabled:
                    for subtype in gis_layer_google_subtypes:
                        if layer.subtype == subtype:
                            google["%s" % subtype] = layer.name
            if google:
                html.append(SCRIPT(_type="text/javascript", _src="http://maps.google.com/maps?file=api&v=2&key=" + google.key))
                if google.Satellite:
                    layers_google += """
        var googlesat = new OpenLayers.Layer.Google( '""" + google.Satellite + """' , {type: G_SATELLITE_MAP, 'sphericalMercator': true } );
        map.addLayer(googlesat);
                    """
                if google.Maps:
                    layers_google += """
        var googlemaps = new OpenLayers.Layer.Google( '""" + google.Maps + """' , {type: G_NORMAL_MAP, 'sphericalMercator': true } );
        map.addLayer(googlemaps);
                    """
                if google.Hybrid:
                    layers_google += """
        var googlehybrid = new OpenLayers.Layer.Google( '""" + google.Hybrid + """' , {type: G_HYBRID_MAP, 'sphericalMercator': true } );
        map.addLayer(googlehybrid);
                    """
                if google.Terrain:
                    layers_google += """
        var googleterrain = new OpenLayers.Layer.Google( '""" + google.Terrain + """' , {type: G_PHYSICAL_MAP, 'sphericalMercator': true } )
        map.addLayer(googleterrain);
                    """

            # Yahoo
            gis_layer_yahoo_subtypes = self.layer_subtypes("yahoo")
            yahoo = Storage()
            yahoo_enabled = db(db.gis_layer_yahoo.enabled == True).select()
            if yahoo_enabled:
                yahoo.key = self.get_api_key("yahoo")
                for layer in yahoo_enabled:
                    for subtype in gis_layer_yahoo_subtypes:
                        if layer.subtype == subtype:
                            yahoo["%s" % subtype] = layer.name
            if yahoo:
                html.append(SCRIPT(_type="text/javascript", _src="http://api.maps.yahoo.com/ajaxymap?v=3.8&appid=" + yahoo.key))
                if yahoo.Satellite:
                    layers_yahoo += """
        var yahoosat = new OpenLayers.Layer.Yahoo( '""" + yahoo.Satellite + """' , {type: YAHOO_MAP_SAT, 'sphericalMercator': true } );
        map.addLayer(yahoosat);
                    """
                if yahoo.Maps:
                    layers_yahoo += """
        var yahoomaps = new OpenLayers.Layer.Yahoo( '""" + yahoo.Maps + """' , {'sphericalMercator': true } );
        map.addLayer(yahoomaps);
                    """
                if yahoo.Hybrid:
                    layers_yahoo += """
        var yahoohybrid = new OpenLayers.Layer.Yahoo( '""" + yahoo.Hybrid + """' , {type: YAHOO_MAP_HYB, 'sphericalMercator': true } );
        map.addLayer(yahoohybrid);
                    """

            # Bing - Broken in GeoExt currently: http://www.geoext.org/pipermail/users/2009-December/000417.html
            bing = False
            #gis_layer_bing_subtypes = self.layer_subtypes("bing")
            #bing = Storage()
            #bing_enabled = db(db.gis_layer_bing.enabled == True).select()
            #for layer in bing_enabled:
            #    for subtype in gis_layer_bing_subtypes:
            #        if layer.subtype == subtype:
            #            bing["%s" % subtype] = layer.name
            if bing:
                html.append(SCRIPT(_type="text/javascript", _src="http://ecn.dev.virtualearth.net/mapcontrol/mapcontrol.ashx?v=6.2&mkt=en-us"))
                if bing.Satellite:
                    layers_bing += """
        var bingsat = new OpenLayers.Layer.VirtualEarth( '""" + bing.Satellite + """' , {type: VEMapStyle.Aerial, 'sphericalMercator': true } );
        map.addLayer(bingsat);
                    """
                if bing.Maps:
                    layers_bing += """
        var bingmaps = new OpenLayers.Layer.VirtualEarth( '""" + bing.Maps + """' , {type: VEMapStyle.Road, 'sphericalMercator': true } );
        map.addLayer(bingmaps);
                    """
                if bing.Hybrid:
                    layers_bing += """
        var binghybrid = new OpenLayers.Layer.VirtualEarth( '""" + bing.Hybrid + """' , {type: VEMapStyle.Hybrid, 'sphericalMercator': true } );
        map.addLayer(binghybrid);
                    """
                if bing.Terrain:
                    layers_bing += """
        var bingterrain = new OpenLayers.Layer.VirtualEarth( '""" + bing.Terrain + """' , {type: VEMapStyle.Shaded, 'sphericalMercator': true } );
        map.addLayer(bingterrain);
                    """

        # WFS
        layers_wfs = ""
        wfs_enabled = db(db.gis_layer_wfs.enabled == True).select()
        for layer in wfs_enabled:
            name = layer.name
            name_safe = re.sub('\W', '_', name)
            url = layer.url
            try:
                wfs_version = layer.version
            except:
                wfs_version = ""
            featureType = layer.featureType
            featureNS = layer.featureNS
            try:
                wfs_projection = db(db.gis_projection.id == layer.projection_id).select(db.gis_projection.epsg, limitby=(0, 1)).first().epsg
                wfs_projection = "srsName: 'EPSG:" + wfs_projection + "',"
            except:
                wfs_projection = ""
            if layer.visible:
                wfs_visibility = ""
            else:
                wfs_visibility = "wfsLayer" + name_safe + ".setVisibility(false);"
            #if layer.editable:
            #    wfs_strategy = "strategies: [new OpenLayers.Strategy.BBOX(), new OpenLayers.Strategy.Save()],"
            wfs_strategy = "new OpenLayers.Strategy.BBOX()"
            layers_wfs  += """
        var wfsLayer""" + name_safe + """ = new OpenLayers.Layer.Vector( '""" + name + """', {
                strategies: [""" + wfs_strategy + """],
                projection: projection_current,
                protocol: new OpenLayers.Protocol.WFS({
                    version: '""" + wfs_version + """',
                    """ + wfs_projection + """
                    url:  '""" + url + """',
                    featureType: '""" + featureType + """',
                    featureNS: '""" + featureNS + """'
                    //,geometryName: "the_geom"
                })
                //,styleMap: styleMap
            });
        map.addLayer(wfsLayer""" + name_safe + """);
        """ + wfs_visibility + """
        """

        # WMS
        layers_wms = ""
        wms_enabled = db(db.gis_layer_wms.enabled == True).select()
        for layer in wms_enabled:
            name = layer.name
            name_safe = re.sub('\W', '_', name)
            url = layer.url
            try:
                wms_version = "version: '" + layer.version + "',"
            except:
                wms_version = ""
            try:
                wms_map = "map: '" + layer.map + "',"
            except:
                wms_map = ""
            wms_layers = layer.layers
            try:
                format = "type: '" + layer.format + "',"
            except:
                format = ""
            if layer.transparent:
                transparent = "transparent: true,"
            else:
                transparent = ""
            options = "wrapDateLine: 'true'"
            if not layer.base:
                options += """,
                    isBaseLayer: false"""
                if not layer.visible:
                    options += """,
                    visibility: false"""

            layers_wms  += """
        var wmsLayer""" + name_safe + """ = new OpenLayers.Layer.WMS(
            '""" + name + """', '""" + url + """', {
               """ + wms_map + """
               layers: '""" + wms_layers + """',
               """ + format + """
               """ + transparent + """
               """ + wms_version + """
               },
               {
               """ + options + """
               }
            );
        map.addLayer(wmsLayer""" + name_safe + """);
        """

        # TMS
        layers_tms = ""
        tms_enabled = db(db.gis_layer_tms.enabled == True).select()
        for layer in tms_enabled:
            name = layer.name
            name_safe = re.sub('\W', '_', name)
            url = layer.url
            tms_layers = layer.layers
            try:
                format = "type: '" + layer.format + "'"
            except:
                format = ""

            layers_tms  += """
        var tmsLayer""" + name_safe + """ = new OpenLayers.Layer.TMS( '""" + name + """', '""" + url + """', {
                layername: '""" + tms_layers + """',
                """ + format + """
            });
        map.addLayer(tmsLayer""" + name_safe + """);
        """

        # XYZ
        layers_xyz = ""
        xyz_enabled = db(db.gis_layer_tms.enabled == True).select()
        for layer in xyz_enabled:
            name = layer.name
            name_safe = re.sub('\W', '_', name)
            url = layer.url
            if layer.sphericalMercator:
                sphericalMercator = "sphericalMercator: 'true',"
            else:
                sphericalMercator = ""
            if layer.transitionEffect:
                transitionEffect = "transitionEffect: '{{=xyz_layers[layer].transitionEffect}}',"
            else:
                transitionEffect = ""
            if layer.numZoomLevels:
                xyz_numZoomLevels = "numZoomLevels: '" + layer.numZoomLevels + "'"
            else:
                xyz_numZoomLevels = ""
            if layer.base:
                base = "isBaseLayer: 'true'"
            else:
                base = ""
                if layer.transparent:
                    base += "transparent: 'true',"
                if layer.visible:
                    base += "visibility: 'true',"
                if layer.opacity:
                    base += "opacity: '" + layer.opacity + "',"
                base += "isBaseLayer: 'false'"

            layers_xyz  += """
        var xyzLayer""" + name_safe + """ = new OpenLayers.Layer.XYZ( '""" + name + """', '""" + url + """', {
                """ + sphericalMercator + """
                """ + transitionEffect + """
                """ + xyz_numZoomLevels + """
                """ + base + """
            });
        map.addLayer(xyzLayer""" + name_safe + """);
        """

        # JS
        layers_js = ""
        js_enabled = db(db.gis_layer_tms.enabled == True).select()
        for layer in js_enabled:
            layers_js  += layer.code

        #
        # Overlays
        #

        # Can we cache downloaded feeds?
        # Needed for unzipping & filtering as well
        cachepath = os.path.join(request.folder, "uploads", "gis_cache")
        if os.access(cachepath, os.W_OK):
            cacheable = True
        else:
            cacheable = False

        #
        # Features
        #
        layers_features = ""
        if feature_queries or add_feature:

            cluster_style = """
        // Needs to be uniquely instantiated
        var style_cluster = new OpenLayers.Style(style_cluster_style, style_cluster_options);
        // Define StyleMap, Using 'style_cluster' rule for 'default' styling intent
        var featureClusterStyleMap = new OpenLayers.StyleMap({
                                          'default': style_cluster,
                                          'select': {
                                              fillColor: '#ffdc33',
                                              strokeColor: '#ff9933'
                                          }
        });
        """

            layers_features += """
        var featureLayers = new Array();
        var features = [];
        var parser = new OpenLayers.Format.WKT();
        var geom, featureVec;

        // Style Rule For Clusters
        var style_cluster_style = {
            label: '${label}',
            pointRadius: '${radius}',
            fillColor: '#8087ff',
            fillOpacity: 0.5,
            strokeColor: '#2b2f76',
            strokeWidth: 2,
            strokeOpacity: 1
        };
        var style_cluster_options = {
            context: {
                radius: function(feature) {
                    // Size For Unclustered Point
                    var pix = 6;
                    // Size For Clustered Point
                    if(feature.cluster) {
                        pix = Math.min(feature.attributes.count, 7) + 4;
                    }
                    return pix;
                },
                label: function(feature) {
                    // Label For Unclustered Point or Cluster of just 2
                    var label = '';
                    // Size For Clustered Point
                    if(feature.cluster && feature.attributes.count > 2) {
                        label = feature.attributes.count;
                    }
                    return label;
                }
            }
        };
        
        function addFeature(feature_id, name, geom, styleMarker, image, popup_url) {
            geom = geom.transform(proj4326, projection_current);
            // Needs to be uniquely instantiated
            var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
            if ('' == styleMarker.iconURL) {
                style_marker.graphicName = styleMarker.graphicName;
                style_marker.pointRadius = styleMarker.pointRadius;
                style_marker.fillColor = styleMarker.fillColor;
                style_marker.fillOpacity = 0.4;
                style_marker.strokeColor = styleMarker.fillColor;
                style_marker.strokeWidth = 2;
                style_marker.strokeOpacity = 1;
            } else {
                // Set icon dims (set in onload)
                width = image.width;
                height = image.height;
                style_marker.graphicOpacity = 1;
                style_marker.graphicWidth = width;
                style_marker.graphicHeight = height;
                style_marker.graphicXOffset = -(width / 2);
                style_marker.graphicYOffset = -height;
                style_marker.externalGraphic = styleMarker.iconURL;
            }
            // Create Feature Vector
            var featureVec = new OpenLayers.Feature.Vector(geom, null, style_marker);
            featureVec.fid = feature_id;
            // Store the popup_url in the feature so that onFeatureSelect can read it
            featureVec.popup_url = popup_url;
            featureVec.attributes.name = name;
            return featureVec;
        }

        function onFeatureSelect(event) {
            // unselect any previous selections
            tooltipUnselect(event);
            var feature = event.feature;
            var id = 'featureLayerPopup';
            centerPoint = feature.geometry.getBounds().getCenterLonLat();
            if(feature.cluster) {
                // Cluster
                var name, uuid, url;
                var html = '""" + str(T("There are multiple records at this location")) + """:<ul>';
                for (var i = 0; i < feature.cluster.length; i++) {
                    name = feature.cluster[i].attributes.name;
                    uuid = feature.cluster[i].fid;
                    url = feature.cluster[i].popup_url + uuid;
                    html += "<li><a href='javascript:loadClusterPopup(" + "\\"" + url + "\\", \\"" + id + "\\"" + ")'>" + name + "</a></li>";
                }
                html += '</ul>';
                html += "<div align='center'><a href='javascript:zoomToSelectedFeature(" + centerPoint.lon + "," + centerPoint.lat + ", 3)'>Zoom in</a></div>";
                var popup = new OpenLayers.Popup.FramedCloud(
                    id,
                    centerPoint,
                    new OpenLayers.Size(200, 200),
                    html,
                    null,
                    true,
                    onPopupClose
                );
                feature.popup = popup;
                map.addPopup(popup);
            } else {
                // Single Feature
                var popup_url = feature.popup_url;
                var popup = new OpenLayers.Popup.FramedCloud(
                    id,
                    centerPoint,
                    new OpenLayers.Size(200, 200),
                    "Loading...<img src='" + ajax_loader + "' border=0>",
                    null,
                    true,
                    onPopupClose
                );
                feature.popup = popup;
                map.addPopup(popup);
                // call AJAX to get the contentHTML
                var uuid = feature.fid;
                loadDetails(popup_url + uuid, id, popup);
            }
        }

        function loadDetails(url, id, popup) {
            //$.getS3(
            $.get(
                    url,
                    function(data) {
                        $('#' + id + '_contentDiv').html(data);
                        popup.updateSize();
                    },
                    'html'
                );
        }

        """
            # Draft Features
            # This is currently used just to select the Lat/Lon for a Location, so no Features pre-loaded
            if add_feature:
                layers_features += """
            //features = [];
        """ + cluster_style + """
        draftLayer = new OpenLayers.Layer.Vector(
            '""" + str(T("Draft Features")) + """', {}
            //{
            //    strategies: [ """ + strategy_cluster + """ ],
            //    styleMap: featureClusterStyleMap
            //}
        );
        draftLayer.setVisibility(true);
        map.addLayer(draftLayer);
        //draftLayer.events.on({
        //    "featureselected": onFeatureSelect,
        //    "featureunselected": onFeatureUnselect
        //});
        // Don't include here as we don't want the highlightControl & currently gain nothing else from it
        //featureLayers.push(draftLayer);

        // We don't currently do anything here
        //function onFeatureSelect(event) {
            // unselect any previous selections
        //    tooltipUnselect(event);
        //    var feature = event.feature;
        //    var id = 'draftLayerPopup';
        //    if(feature.cluster) {
                // Cluster
        //        centerPoint = feature.geometry.getBounds().getCenterLonLat();
        //    } else {
                // Single Feature
        //    }
        //}
        """
            
            # Feature Queries
            for layer in feature_queries:
                # Features passed as Query
                if "name" in layer:
                    name = layer["name"]
                else:
                    name = "Query" + str(int(random.random()*1000))

                if "marker" in layer:
                    markerLayer = db(db.gis_marker.id == layer["marker"]).select(db.gis_marker.image, limitby=(0, 1), cache=cache).first()
                else:
                    markerLayer = ""

                if "popup_url" in layer:
                    _popup_url = urllib.unquote(layer["popup_url"])
                else:
                    _popup_url = urllib.unquote(URL(r=request, c="gis", f="location", args=["read.popup?location.id="]))

                if "polygon" in layer and layer.polygon:
                    polygons = True
                else:
                    polygons = False

                # Generate HTML snippet
                name_safe = re.sub("\W", "_", name)
                if "active" in layer and layer["active"]:
                    visibility = "featureLayer" + name_safe + ".setVisibility(true);"
                else:
                    visibility = "featureLayer" + name_safe + ".setVisibility(false);"
                layers_features += """
        features = [];
        var popup_url = '""" + _popup_url + """';
        """ + cluster_style + """
        var featureLayer""" + name_safe + """ = new OpenLayers.Layer.Vector(
            '""" + name + """',
            {
                strategies: [ """ + strategy_cluster + """ ],
                styleMap: featureClusterStyleMap
            }
        );
        """ + visibility + """
        map.addLayer(featureLayer""" + name_safe + """);
        featureLayer""" + name_safe + """.events.on({
            "featureselected": onFeatureSelect,
            "featureunselected": onFeatureUnselect
        });
        featureLayers.push(featureLayer""" + name_safe + """);
        """
                features = layer["query"]
                for _feature in features:
                    try:
                        _feature.gis_location.id
                        # Query was generated by a Join
                        feature = _feature.gis_location
                    except (AttributeError, KeyError):
                        # Query is a simple select
                        feature = _feature
                    # Should we use Polygons or Points?
                    if polygons:
                        # Deal with manually-imported Features which are missing WKT
                        if feature.get("wkt"):
                            wkt = feature.wkt
                        else:
                            try:
                                lat = feature.lat
                                lon = feature.lon
                                if (lat is None) or (lon is None):
                                    # Zero is allowed but not None
                                    if feature.get("parent"):
                                        # Skip the current record if we can
                                        latlon = self.get_latlon(feature.parent)
                                    elif feature.get("id"):
                                        latlon = self.get_latlon(feature.id)
                                    else:
                                        # nothing we can do!
                                        continue
                                    if latlon:
                                        lat = latlon["lat"]
                                        lon = latlon["lon"]
                                    else:
                                        # nothing we can do!
                                        continue
                            except:
                                if feature.get("parent"):
                                    # Skip the current record if we can
                                    latlon = self.get_latlon(feature.parent)
                                elif feature.get("id"):
                                    latlon = self.get_latlon(feature.id)
                                else:
                                    # nothing we can do!
                                    continue
                                if latlon:
                                    lat = latlon["lat"]
                                    lon = latlon["lon"]
                                else:
                                    # nothing we can do!
                                    continue
                            wkt = self.latlon_to_wkt(lat, lon)
                    else:
                        # Just display Point data, even if we have Polygons
                        # ToDo: DRY with Polygon
                        try:
                            lat = feature.lat
                            lon = feature.lon
                            if (lat is None) or (lon is None):
                                # Zero is allowed but not None
                                if feature.get("parent"):
                                    # Skip the current record if we can
                                    latlon = self.get_latlon(feature.parent)
                                elif feature.get("id"):
                                    latlon = self.get_latlon(feature.id)
                                else:
                                    # nothing we can do!
                                    continue
                                if latlon:
                                    lat = latlon["lat"]
                                    lon = latlon["lon"]
                                else:
                                    # nothing we can do!
                                    continue
                        except:
                            if feature.get("parent"):
                                # Skip the current record if we can
                                latlon = self.get_latlon(feature.parent)
                            elif feature.get("id"):
                                latlon = self.get_latlon(feature.id)
                            else:
                                # nothing we can do!
                                continue
                            if latlon:
                                lat = latlon["lat"]
                                lon = latlon["lon"]
                            else:
                                # nothing we can do!
                                continue
                        wkt = self.latlon_to_wkt(lat, lon)

                    try:
                        # Has a per-feature Vector Shape been added to the query?
                        graphicName = feature.shape
                        if graphicName not in ["circle", "square", "star", "x", "cross", "triangle"]:
                            # Default to Circle
                            graphicName = "circle"
                        try:
                            pointRadius = feature.size
                            if not pointRadius:
                                pointRadius = 6
                        except (AttributeError, KeyError):
                            pointRadius = 6
                        try:
                            fillColor = feature.color
                            if not fillColor:
                                fillColor = "orange"
                        except (AttributeError, KeyError):
                            fillColor = "orange"
                        marker_url = ""
                    except (AttributeError, KeyError):
                        # Use a Marker not a Vector Shape
                        try:
                            # Has a per-feature marker been added to the query?
                            _marker = feature.marker
                            if _marker:
                                marker = _marker.image
                            else:
                                marker = self.get_marker(feature.id)
                        except (AttributeError, KeyError):
                            if markerLayer:
                                # Marker specified at the layer level
                                marker = markerLayer.image
                            else:
                                marker = self.get_marker(feature.id)
                        # Faster to bypass the download handler
                        #marker_url = URL(r=request, c="default", f="download", args=[marker])
                        marker_url = URL(r=request, c="static", f="img", args=["markers", marker])
                        
                    try:
                        # Has a per-feature popup_label been added to the query?
                        popup_label = feature.popup_label
                    except (AttributeError, KeyError):
                        popup_label = feature.name

                    # Deal with apostrophes in Feature Names
                    fname = re.sub("'", "\\'", popup_label)
                    
                    if marker_url:
                        layers_features += """
        styleMarker.iconURL = '""" + marker_url + """';
        // Pre-cache this image
        // Need unique names
        var i = new Image();
        i.onload = scaleImage;
        i.src = styleMarker.iconURL;
        """
                    else:
                        layers_features += """
        styleMarker.iconURL = '';
        styleMarker.graphicName = '""" + graphicName + """';
        styleMarker.pointRadius = """ + str(pointRadius) + """;
        styleMarker.fillColor = '""" + fillColor + """';
        """
                    layers_features += """
        geom = parser.read('""" + wkt + """').geometry;
        featureVec = addFeature('""" + str(feature.id) + """', '""" + fname + """', geom, styleMarker, i, popup_url)
        features.push(featureVec);
        """
                # Append to Features layer
                layers_features += """
        featureLayer""" + name_safe + """.addFeatures(features);
        """
            # Append to Features section
            layers_features += """
        allLayers = allLayers.concat(featureLayers);
        """

        else:
            # No Feature Layers requested
            pass

        layers_georss = ""
        layers_gpx = ""
        layers_kml = ""
        if catalogue_overlays:
            # GeoRSS
            query = (db.gis_layer_georss.enabled == True) # No deletable field
            georss_enabled = db(query).select(db.gis_layer_georss.name, db.gis_layer_georss.url, db.gis_layer_georss.visible, db.gis_layer_georss.projection_id, db.gis_layer_georss.marker_id)
            if georss_enabled:
                layers_georss += """
        var georssLayers = new Array();
        var format_georss = new OpenLayers.Format.GeoRSS();
        function onGeorssFeatureSelect(event) {
            // unselect any previous selections
            tooltipUnselect(event);
            var feature = event.feature;
            var selectedFeature = feature;
            centerPoint = feature.geometry.getBounds().getCenterLonLat();
            if (undefined == feature.attributes.description) {
                var popup = new OpenLayers.Popup.FramedCloud('georsspopup',
                centerPoint,
                new OpenLayers.Size(200, 200),
                '<h2>' + feature.attributes.title + '</h2>',
                null, true, onPopupClose);
            } else {
                var popup = new OpenLayers.Popup.FramedCloud('georsspopup',
                centerPoint,
                new OpenLayers.Size(200, 200),
                '<h2>' + feature.attributes.title + '</h2>' + feature.attributes.description,
                null, true, onPopupClose);
            };
            feature.popup = popup;
            popup.feature = feature;
            map.addPopup(popup);
        }
        """
                for layer in georss_enabled:
                    name = layer["name"]
                    url = layer["url"]
                    visible = layer["visible"]
                    georss_projection = db(db.gis_projection.id == layer["projection_id"]).select(db.gis_projection.epsg, limitby=(0, 1)).first().epsg
                    if georss_projection == 4326:
                        projection_str = "projection: proj4326,"
                    else:
                        projection_str = "projection: new OpenLayers.Projection('EPSG:" + georss_projection + "'),"
                    marker_id = layer["marker_id"]
                    if marker_id:
                        marker = db(db.gis_marker.id == marker_id).select(db.gis_marker.image, limitby=(0, 1)).first().image
                    else:
                        marker = db(db.gis_marker.id == marker_default).select(db.gis_marker.image, limitby=(0, 1)).first().image
                    marker_url = URL(r=request, c="static", f="img", args=["markers", marker])

                    if cacheable:
                        # Download file
                        try:
                            file = fetch(url)
                            warning = ""
                        except urllib2.URLError:
                            warning = "URLError"
                        except urllib2.HTTPError:
                            warning = "HTTPError"
                        _name = name.replace(" ", "_")
                        _name = _name.replace(",", "_")
                        filename = "gis_cache.file." + _name + ".rss"
                        filepath = os.path.join(cachepath, filename)
                        f = open(filepath, "w")
                        # Handle errors
                        if "URLError" in warning or "HTTPError" in warning:
                            # URL inaccessible
                            if os.access(filepath, os.R_OK):
                                # Use cached version
                                date = db(db.gis_cache.name == name).select(db.gis_cache.modified_on, limitby=(0, 1)).first().modified_on
                                response.warning += url + " " + str(T("not accessible - using cached version from")) + " " + str(date) + "\n"
                                url = URL(r=request, c="default", f="download", args=[filename])
                            else:
                                # No cached version available
                                response.warning += url + " " + str(T("not accessible - no cached version available!")) + "\n"
                                # skip layer
                                continue
                        else:
                            # Download was succesful
                            # Write file to cache
                            f.write(file)
                            f.close()
                            records = db(db.gis_cache.name == name).select()
                            if records:
                                records[0].update(modified_on=response.utcnow)
                            else:
                                db.gis_cache.insert(name=name, file=filename)
                            url = URL(r=request, c="default", f="download", args=[filename])
                    else:
                        # No caching possible (e.g. GAE), display file direct from remote (using Proxy)
                        pass

                    # Generate HTML snippet
                    name_safe = re.sub("\W", "_", name)
                    if visible:
                        visibility = "georssLayer" + name_safe + ".setVisibility(true);"
                    else:
                        visibility = "georssLayer" + name_safe + ".setVisibility(false);"
                    layers_georss += """
        iconURL = '""" + marker_url + """';
        // Pre-cache this image
        // Need unique names
        var i = new Image();
        i.onload = scaleImage;
        i.src = iconURL;
        // Needs to be uniquely instantiated
        var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
        style_marker.graphicOpacity = 1;
        style_marker.graphicWidth = width;
        style_marker.graphicHeight = height;
        style_marker.graphicXOffset = -(width / 2);
        style_marker.graphicYOffset = -height;
        style_marker.externalGraphic = iconURL;
        var georssLayer""" + name_safe + """ = new OpenLayers.Layer.Vector(
            '""" + name_safe + """',
            {
                """ + projection_str + """
                strategies: [ """ + strategy_fixed + ", " + strategy_cluster + """ ],
                style: style_marker,
                protocol: new OpenLayers.Protocol.HTTP({
                    url: '""" + url + """',
                    format: format_georss
                })
            }
        );
        """ + visibility + """
        map.addLayer(georssLayer""" + name_safe + """);
        georssLayers.push(georssLayer""" + name_safe + """);
        georssLayer""" + name_safe + """.events.on({ "featureselected": onGeorssFeatureSelect, "featureunselected": onFeatureUnselect });
        """
                layers_georss += """
        allLayers = allLayers.concat(georssLayers);
        """

            # GPX
            gpx_enabled = db(db.gis_layer_gpx.enabled == True).select()
            if gpx_enabled:
                layers_gpx += """
        var georssLayers = new Array();
        var format_gpx = new OpenLayers.Format.GPX();
        function onGpxFeatureSelect(event) {
            // unselect any previous selections
            tooltipUnselect(event);
            var feature = event.feature;
            // Anything we want to do here?
        }
        """
                for layer in gpx_enabled:
                    name = layer["name"]
                    track = db(db.gis_track.id == layer.track_id).select(db.gis_track.track, limitby=(0, 1)).first()
                    if track:
                        url = track.track
                    else:
                        url = ""
                    visible = layer["visible"]
                    marker_id = layer["marker_id"]
                    if marker_id:
                        marker = db(db.gis_marker.id == marker_id).select(db.gis_marker.image, limitby=(0, 1)).first().image
                    else:
                        marker = db(db.gis_marker.id == marker_default).select(db.gis_marker.image, limitby=(0, 1)).first().image
                    marker_url = URL(r=request, c="static", f="img", args=["markers", marker])

                    # Generate HTML snippet
                    name_safe = re.sub("\W", "_", name)
                    if visible:
                        visibility = "gpxLayer" + name_safe + ".setVisibility(true);"
                    else:
                        visibility = "gpxLayer" + name_safe + ".setVisibility(false);"
                    layers_gpx += """
        iconURL = '""" + marker_url + """';
        // Pre-cache this image
        // Need unique names
        var i = new Image();
        i.onload = scaleImage;
        i.src = iconURL;
        // Needs to be uniquely instantiated
        var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
        style_marker.graphicOpacity = 1;
        style_marker.graphicWidth = width;
        style_marker.graphicHeight = height;
        style_marker.graphicXOffset = -(width / 2);
        style_marker.graphicYOffset = -height;
        style_marker.externalGraphic = iconURL;
        var gpxLayer""" + name_safe + """ = new OpenLayers.Layer.Vector(
            '""" + name_safe + """',
            {
                projection: proj4326,
                strategies: [ """ + strategy_fixed + ", " + strategy_cluster + """ ],
                style: style_marker,
                protocol: new OpenLayers.Protocol.HTTP({
                    url: '""" + url + """',
                    format: format_gpx
                })
            }
        );
        """ + visibility + """
        map.addLayer(gpxLayer""" + name_safe + """);
        gpxLayers.push(gpxLayer""" + name_safe + """);
        gpxLayer""" + name_safe + """.events.on({ 'featureselected': onGpxFeatureSelect, 'featureunselected': onFeatureUnselect });
        """
                layers_gpx += """
        allLayers = allLayers.concat(gpxLayers);
        """

            # KML
            kml_enabled = db(db.gis_layer_kml.enabled == True).select()
            if kml_enabled:
                layers_kml += """
        var kmlLayers = new Array();
        var format_kml = new OpenLayers.Format.KML({
            extractStyles: true,
            extractAttributes: true,
            maxDepth: 2
        })
        function onKmlFeatureSelect(event) {
            // unselect any previous selections
            tooltipUnselect(event);
            var feature = event.feature;
            centerPoint = feature.geometry.getBounds().getCenterLonLat();
            var selectedFeature = feature;
            var title = feature.layer.title;
            var _attributes = feature.attributes;
            var type = typeof _attributes[title];
            if ('object' == type) {
                _title = _attributes[title].value;
            } else {
                _title = _attributes[title];
            }
            var body = feature.layer.body.split(' ');
            var content = '';
            for (var i = 0; i < body.length; i++) {
                type = typeof _attributes[body[i]];
                if ('object' == type) {
                    // Geocommons style
                    var displayName = _attributes[body[i]].displayName;
                    if (displayName == '') {
                        displayName = body[i];
                    }
                    var value = _attributes[body[i]].value;
                    var row = '<b>' + displayName + '</b>: ' + value + '<br />';
                } else {
                    var row = _attributes[body[i]] + '<br />';
                }
                content += row;
            }
            // Protect the content against JavaScript attacks
            if (content.search('<script') != -1) {
                content = 'Content contained Javascript! Escaped content below.<br />' + content.replace(/</g, '<');
            }
            var contents = '<h2>' + _title + '</h2>' + content;
            
            var popup = new OpenLayers.Popup.FramedCloud('kmlpopup',
                centerPoint,
                new OpenLayers.Size(200, 200),
                contents,
                null, true, onPopupClose
            );
            feature.popup = popup;
            popup.feature = feature;
            map.addPopup(popup);
        }
        """
                for layer in kml_enabled:
                    name = layer["name"]
                    url = layer["url"]
                    visible = layer["visible"]
                    title = layer["title"] or "name"
                    body = layer["body"] or "description"
                    projection_str = "projection: proj4326,"
                    if cacheable:
                        # Download file
                        file, warning = self.download_kml(url, public_url)
                        _name = name.replace(" ", "_")
                        _name = _name.replace(",", "_")
                        filename = "gis_cache.file." + _name + ".kml"
                        filepath = os.path.join(cachepath, filename)
                        f = open(filepath, "w")
                        # Handle errors
                        if "URLError" in warning or "HTTPError" in warning:
                            # URL inaccessible
                            if os.access(filepath, os.R_OK):
                                statinfo = os.stat(filepath)
                                if statinfo.st_size:
                                    # Use cached version
                                    date = db(db.gis_cache.name == name).select(db.gis_cache.modified_on, limitby=(0, 1)).first().modified_on
                                    response.warning += url + " " + str(T("not accessible - using cached version from")) + " " + str(date) + "\n"
                                    url = URL(r=request, c="default", f="download", args=[filename])
                                else:
                                    # 0k file is all that is available
                                    response.warning += url + " " + str(T("not accessible - no cached version available!")) + "\n"
                                    # skip layer
                                    continue
                            else:
                                # No cached version available
                                response.warning += url + " " + str(T("not accessible - no cached version available!")) + "\n"
                                # skip layer
                                continue
                        else:
                            # Download was succesful
                            if "ParseError" in warning:
                                # @ToDo Parse detail
                                response.warning += str(T("Layer")) + ": " + name + " " + str(T("couldn't be parsed so NetworkLinks not followed.")) + "\n"
                            if "GroundOverlay" in warning or "ScreenOverlay" in warning:
                                response.warning += str(T("Layer")) + ": " + name + " " + str(T("includes a GroundOverlay or ScreenOverlay which aren't supported in OpenLayers yet, so it may not work properly.")) + "\n"
                            # Write file to cache
                            f.write(file)
                            f.close()
                            records = db(db.gis_cache.name == name).select()
                            if records:
                                records[0].update(modified_on=response.utcnow)
                            else:
                                db.gis_cache.insert(name=name, file=filename)
                            url = URL(r=request, c="default", f="download", args=[filename])
                    else:
                        # No caching possible (e.g. GAE), display file direct from remote (using Proxy)
                        pass

                    # Generate HTML snippet
                    name_safe = re.sub("\W", "_", name)
                    layer_name = "kmlLayer" + name_safe
                    if visible:
                        visibility = layer_name + ".setVisibility(true);"
                    else:
                        visibility = layer_name + ".setVisibility(false);"
                    layers_kml += """
        iconURL = '""" + marker_url + """';
        // Pre-cache this image
        // Need unique names
        var i = new Image();
        i.onload = scaleImage;
        i.src = iconURL;
        // Needs to be uniquely instantiated
        var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
        style_marker.graphicOpacity = 1;
        style_marker.graphicWidth = width;
        style_marker.graphicHeight = height;
        style_marker.graphicXOffset = -(width / 2);
        style_marker.graphicYOffset = -height;
        style_marker.externalGraphic = iconURL;
        var kmlLayer""" + name_safe + """ = new OpenLayers.Layer.Vector(
            '""" + name + """',
            {
                """ + projection_str + """
                strategies: [ """ + strategy_fixed + ", " + strategy_cluster + """ ],
                style: style_marker,
                protocol: new OpenLayers.Protocol.HTTP({
                    url: '""" + url + """',
                    format: format_kml
                })
            }
        );
        """ + visibility + """
        kmlLayer""" + name_safe + """.title = '""" + title + """';
        kmlLayer""" + name_safe + """.body = '""" + body + """';
        map.addLayer(kmlLayer""" + name_safe + """);
        kmlLayers.push(kmlLayer""" + name_safe + """);
        kmlLayer""" + name_safe + """.events.on({ "featureselected": onKmlFeatureSelect, "featureunselected": onFeatureUnselect });
        """
                layers_kml += """
        allLayers = allLayers.concat(kmlLayers);
        """

        #############
        # Main script
        #############

        html.append(SCRIPT("""
    var map, mapPanel, legendPanel, toolbar, win;
    var pointButton, lastDraftFeature, draftLayer;
    var centerPoint, currentFeature, popupControl, highlightControl;
    var wmsBrowser, printProvider;
    var allLayers = new Array();
    S3.gis.Images = new Array();
    OpenLayers.ImgPath = '/""" + request.application + """/static/img/gis/openlayers/';
    var ajax_loader = '""" + str(URL(r=request, c="static", f="img")) + """/ajax-loader.gif';
    // avoid pink tiles
    OpenLayers.IMAGE_RELOAD_ATTEMPTS = 3;
    OpenLayers.Util.onImageLoadErrorColor = "transparent";
    OpenLayers.ProxyHost = '""" + str(URL(r=request, c="gis", f="proxy")) + """?url=';
    // See http://crschmidt.net/~crschmidt/spherical_mercator.html#reprojecting-points
    var proj4326 = new OpenLayers.Projection('EPSG:4326');
    var projection_current = new OpenLayers.Projection('EPSG:""" + str(projection) + """');
    """ + center + """
    var options = {
        displayProjection: proj4326,
        projection: projection_current,
        units: '""" + units + """',
        maxResolution: """ + str(maxResolution) + """,
        maxExtent: new OpenLayers.Bounds(""" + maxExtent + """),
        numZoomLevels: """ + str(numZoomLevels) + """
    };

    // Functions which are called by user & hence need to be in global scope

    // Replace Cluster Popup contents with selected Feature Popup
    function loadClusterPopup(url, id) {
        //$.getS3(
        $.get(
                url,
                function(data) {
                    $('#' + id + '_contentDiv').html(data);
                    map.popups[0].updateSize();
                },
                'html'
            );
    }

    // Zoom to Selected Feature from within Popup
    function zoomToSelectedFeature(lon, lat, zoomfactor) {
        var lonlat = new OpenLayers.LonLat(lon, lat);
        // Get Current Zoom
        currZoom = map.getZoom();
        // New Zoom
        newZoom = currZoom + zoomfactor;
        // Center and Zoom
        map.setCenter(lonlat, newZoom);
        // Remove Popups
        for (var i=0; i<map.popups.length; ++i)	{
            map.removePopup(map.popups[i]);
        }
    }
    
    function addLayers(map) {
        // Base Layers
        // OSM
        """ + layers_openstreetmap + """
        // Google
        """ + layers_google + """
        // Yahoo
        """ + layers_yahoo + """
        // Bing
        """ + layers_bing + """
        // TMS
        """ + layers_tms + """
        // WFS
        """ + layers_wfs + """
        // WMS
        """ + layers_wms + """
        // XYZ
        """ + layers_xyz + """
        // JS
        """ + layers_js + """

        // Overlays
        var max_w = 30;
        var max_h = 35;
        var styleMarker = new Object();
        var iconURL;

        var scaleImage = function(){
            //s3_debug('image', i.src);
            //s3_debug('initial height', i.height);
            //s3_debug('initial width', i.width);
            var scaleRatio = i.height/i.width;
            var w = Math.min(i.width, max_w);
            var h = w * scaleRatio;
            if (h > max_h) {
                    h = max_h;
                    scaleRatio = w/h;
                    w = w * scaleRatio;
                }
            i.height = h;
            i.width = w;
            //s3_debug('post height', i.height);
            //s3_debug('post width', i.width);
        }
        
        // Features
        """ + layers_features + """

        // GeoRSS
        """ + layers_georss + """

        // GPX
        """ + layers_gpx + """

        // KML
        """ + layers_kml + """
    }

    """ + functions_openstreetmap + """

    // Supports popupControl for All Vector Layers
    function onFeatureUnselect(event) {
        var feature = event.feature;
        if (feature.popup) {
            map.removePopup(feature.popup);
            feature.popup.destroy();
            delete feature.popup;
        }
    }
    function onPopupClose(evt) {
        //currentFeature.popup.hide();
        popupControl.unselectAll();
    }

    // Supports highlightControl for All Vector Layers
    var lastFeature = null;
    var tooltipPopup = null;
    function tooltipSelect(event){
        var feature = event.feature;
        if(feature.cluster) {
            // Cluster
            // no tooltip
        } else {
            // Single Feature
            var selectedFeature = feature;
            // if there is already an opened details window, don\'t draw the tooltip
            if(feature.popup != null){
                return;
            }
            // if there are other tooltips active, destroy them
            if(tooltipPopup != null){
                map.removePopup(tooltipPopup);
                tooltipPopup.destroy();
                if(lastFeature != null){
                    delete lastFeature.popup;
                    tooltipPopup = null;
                }
            }
            lastFeature = feature;
            centerPoint = feature.geometry.getBounds().getCenterLonLat();
            _attributes = feature.attributes;
            if (undefined == _attributes.name && undefined == _attributes.title) {
                // KML Layer
                var title = feature.layer.title;
                if (undefined == title) {
                    // We don't have a suitable title, so don't display a tooltip
                    tooltipPopup = null;
                } else {
                    var type = typeof _attributes[title];
                    if ('object' == type) {
                        _title = _attributes[title].value;
                    } else {
                        _title = _attributes[title];
                    }
                    tooltipPopup = new OpenLayers.Popup("activetooltip",
                        centerPoint,
                        new OpenLayers.Size(80, 12),
                        _title,
                        false
                    );
                }
            } else if (undefined == _attributes.title) {
                // Features
                tooltipPopup = new OpenLayers.Popup("activetooltip",
                        centerPoint,
                        new OpenLayers.Size(80, 12),
                        _attributes.name,
                        false
                );
            } else {
                // GeoRSS
                tooltipPopup = new OpenLayers.Popup("activetooltip",
                        centerPoint,
                        new OpenLayers.Size(80, 12),
                        _attributes.title,
                        false
                );
            }
            if (tooltipPopup != null) {
                // should be moved to CSS
                tooltipPopup.contentDiv.style.backgroundColor='ffffcb';
                tooltipPopup.contentDiv.style.overflow='hidden';
                tooltipPopup.contentDiv.style.padding='3px';
                tooltipPopup.contentDiv.style.margin='10px';
                tooltipPopup.closeOnMove = true;
                tooltipPopup.autoSize = true;
                tooltipPopup.opacity = 0.6;
                feature.popup = tooltipPopup;
                map.addPopup(tooltipPopup);
            }
        }
    }
    function tooltipUnselect(event){
        var feature = event.feature;
        if(feature != null && feature.popup != null){
            map.removePopup(feature.popup);
            feature.popup.destroy();
            delete feature.popup;
            tooltipPopup = null;
            lastFeature = null;
        }
    }

    Ext.onReady(function() {
        map = new OpenLayers.Map('center', options);
        addLayers(map);

        map.addControl(new OpenLayers.Control.ScaleLine());
        """ + mouse_position + """
        map.addControl(new OpenLayers.Control.Permalink());
        map.addControl(new OpenLayers.Control.OverviewMap({mapOptions: options}));

        // Popups
        // onClick Popup
        popupControl = new OpenLayers.Control.SelectFeature(
            allLayers, {
                toggle: true,
                clickout: true,
                multiple: false
            }
        );
        // onHover Tooltip
        highlightControl = new OpenLayers.Control.SelectFeature(
            allLayers, {
                hover: true,
                highlightOnly: true,
                renderIntent: "temporary",
                eventListeners: {
                    featurehighlighted: tooltipSelect,
                    featureunhighlighted: tooltipUnselect
                }
            }
        );
        map.addControl(highlightControl);
        map.addControl(popupControl);
        highlightControl.activate();
        popupControl.activate();

        """ + mgrs_html + """

        mapPanel = new GeoExt.MapPanel({
            region: 'center',
            height: """ + str(height) + """,
            width: """ + str(width) + """,
            id: 'mappanel',
            xtype: 'gx_mappanel',
            map: map,
            center: center,
            zoom: """ + str(zoom) + """,
            plugins: [],
            tbar: new Ext.Toolbar()
        });

        """ + print_tool1 + """

        """ + toolbar + """

        """ + search + """

        var layerTreeBase = {
            text: '""" + str(T("Base Layers")) + """',
            nodeType: 'gx_baselayercontainer',
            layerStore: mapPanel.layers,
            leaf: false,
            expanded: false
        };

        var layerTreeFeaturesExternal = {
            text: '""" + str(T("External Features")) + """',
            nodeType: 'gx_overlaylayercontainer',
            layerStore: mapPanel.layers,
            leaf: false,
            expanded: true
        };

        var layerTreeFeaturesInternal = {
            //text: '""" + str(T("Internal Features")) + """',
            text: '""" + str(T("Overlays")) + """',
            nodeType: 'gx_overlaylayercontainer',
            layerStore: mapPanel.layers,
            leaf: false,
            expanded: true
        };

        """ + layers_wms_browser + """

        var layerTree = new Ext.tree.TreePanel({
            id: 'treepanel',
            title: '""" + str(T("Layers")) + """',
            loader: new Ext.tree.TreeLoader({applyLoader: false}),
            root: new Ext.tree.AsyncTreeNode({
                expanded: true,
                children: [
                    layerTreeBase,
                    //layerTreeFeaturesExternal,
                    layerTreeFeaturesInternal
                ]
            }),
            rootVisible: false,
            split: true,
            autoScroll: true,
            collapsible: true,
            collapseMode: 'mini',
            lines: false,
            enableDD: true
        });

        """ + legend1 + """
        
        """ + layout + """
            autoScroll: true,
            maximizable: true,
            titleCollapse: true,
            height: """ + str(height) + """,
            width: """ + str(width) + """,
            layout: 'border',
            items: [{
                    region: 'west',
                    id: 'tools',
                    title: '""" + str(T("Tools")) + """',
                    border: true,
                    width: 250,
                    collapsible: true,
                    collapseMode: 'mini',
                    collapsed: """ + collapsed + """,
                    split: true,
                    items: [
                        layerTree""" + layers_wms_browser2 + search2 + print_tool2 + legend2 + """
                        ]
                    },
                    mapPanel
                    ]
        });
        """ + layout2 + """
        """ + zoomToExtent + """
        """ + toolbar2 + """
    });
    """))

        return html.xml()

# -----------------------------------------------------------------------------
class Geocoder(object):
    " Base class for all Geocoders "

    def __init__(self, db):
        " Initializes the page content object "
        self.db = db
        self.api_key = self.get_api_key()

# -----------------------------------------------------------------------------
class GoogleGeocoder(Geocoder):
    " Google Geocoder module "

    def __init__(self, location, db):
        " Initialise parent class & make any necessary modifications "
        Geocoder.__init__(self, db)
        params = {"q": location, "key": self.api_key}
        self.url = "http://maps.google.com/maps/geo?%s" % urllib.urlencode(params)

    def get_api_key(self):
        " Acquire API key from the database "
        db = self.db
        query = db.gis_apikey.name == "google"
        return db(query).select(db.gis_apikey.apikey, limitby=(0, 1)).first().apikey

    def get_kml(self):
        " Returns the output in KML format "
        url = self.url
        page = fetch(url)
        return page

# -----------------------------------------------------------------------------
class YahooGeocoder(Geocoder):
    " Yahoo Geocoder module "

    def __init__(self, location, db):
        " Initialise parent class & make any necessary modifications "
        Geocoder.__init__(self, db)
        params = {"location": location, "appid": self.api_key}
        self.url = "http://local.yahooapis.com/MapsService/V1/geocode?%s" % urllib.urlencode(params)
        
    def get_api_key(self):
        " Acquire API key from the database "
        db = self.db
        query = db.gis_apikey.name == "yahoo"
        return db(query).select(db.gis_apikey.apikey, limitby=(0, 1)).first().apikey

    def get_xml(self):
        " Return the output in XML format "
        url = self.url
        page = fetch(url)
        return page

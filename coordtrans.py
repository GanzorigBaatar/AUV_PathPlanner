from builtins import object
from .model.point import Point
from qgis.core import QgsMessageLog, Qgis, QgsProject
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsPointXY

class Wgs84ToNed:
    def __init__(self, lon_ref, lat_ref):
        if Qgis.QGIS_VERSION_INT < 31400:
            targetCrs = QgsCoordinateReferenceSystem()
            targetCrs.createFromProj("+proj=stere +ellps=WGS84 +lon_0=%.12f +lat_0=%.12f +no_defs" % (lon_ref, lat_ref))
        else:
            targetCrs = QgsCoordinateReferenceSystem("PROJ:+proj=stere +ellps=WGS84 +lon_0=%.12f +lat_0=%.12f +no_defs" % (lon_ref, lat_ref))
        # Source CRS is WGS84 (epsg:4326)
        QgsCoordinateReferenceSystem.invalidateCache()
        QgsCoordinateTransform.invalidateCache()

        self.transform = QgsCoordinateTransform(
            QgsCoordinateReferenceSystem("EPSG:4326"), targetCrs, QgsProject.instance())

    def convert(self, point):
        if isinstance(point, Point):
            transformed = self.transform.transform(point.getX(), point.getY())
            return Point(transformed.x(), transformed.y())
        else:
            return None

    def convert_(self, lon, lat):
        """
        Convert given (float) longitude and latitude to north, east
        :param lon: longitude to convert
        :param lat: latitude to convert
        :return: pair of east, north values (east first)
        """
        transformed = self.transform.transform(lon, lat)
        return (transformed.x(), transformed.y())

class NedToWgs84:
    def __init__(self, lon_ref, lat_ref):
        if Qgis.QGIS_VERSION_INT < 31400:
            srcCrs = QgsCoordinateReferenceSystem()
            srcCrs.createFromProj("+proj=stere +ellps=WGS84 +lon_0=%.12f +lat_0=%.12f +no_defs" % (lon_ref, lat_ref))
        else:
            srcCrs = QgsCoordinateReferenceSystem("PROJ:+proj=stere +ellps=WGS84 +lon_0=%.12f +lat_0=%.12f +no_defs" % (lon_ref, lat_ref))
        # Source CRS is WGS84 (epsg:4326)

        QgsCoordinateReferenceSystem.invalidateCache()
        QgsCoordinateTransform.invalidateCache()

        self.transform = QgsCoordinateTransform(
            srcCrs, QgsCoordinateReferenceSystem("EPSG:4326"), QgsProject.instance())

    def convert(self, point):
        if isinstance(point, Point):
            transformed = self.transform.transform(point.getX(), point.getY())
            return Point(transformed.x(), transformed.y())
        else:
            return None

    def convert_(self, east, north):
        """
        Convert given east, north values to longitude and latitude
        :param east: east value to convert
        :param north: north value to convert
        :return: pair of lon, lat (lon first)
        """
        transformed = self.transform.transform(east, north)
        return (transformed.x(), transformed.y())

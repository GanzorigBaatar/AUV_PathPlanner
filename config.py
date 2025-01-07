import json

from future import standard_library
standard_library.install_aliases()
from configparser import ConfigParser
import os, traceback
from qgis.core import QgsMessageLog
from qgis.core import Qgis
from qgis.PyQt.QtWidgets import QMessageBox


# set this to False to reload configuration all times get_configuration() is called (may be useful to see changes
# directly as developer)
enable_config_caching=True

global_config = None
coord_decimals = 6    # precision for coordinates


class JsonPropertiesParser(object):
    def __init__(self, fname):
        try:
            self.conf = {}
            f = open(fname, "rt")
            self.conf = json.load(f)
            f.close()
        except Exception as e:
            QMessageBox.critical(None, "Pathplanner configuration error",
                                 "Unable to read configuration file '{}': {}".format(fname, str(e)))

    def get(self, section, value):
        """Read maneuver property"""
        try:
            d = self.conf["Properties"]["maneuver"]
            # directly load from section
            if section in d and value in d[section]:
                return d[section][value]
            # read from combined section
            for key, val in d.items():
                if section in key and value in d[key]:
                    return d[key][value]
            # read from common
            if "common" in d and value in d["common"]:
                return d["common"][value]
            # Not found. Write to log
            QgsMessageLog.logMessage("Configuration value {}.{} not found!".format(section, value),
                                     tag="Pathplanner", level=Qgis.Critical)
        except Exception as e:
            QMessageBox.critical(self, "Pathplanner configuration read error",
                                 "Unable to read value '{}.{}': {}".format(section, value, str(e)))
        return None

    def get_defaults(self, parent_section, maneuver):
        """Return all default maneuver properties"""
        ret = {}
        if parent_section in self.conf["Properties"]:
            d = self.conf["Properties"][parent_section]
            # directly load from section
            if maneuver in d:
                ret.update(d[maneuver])
            # read from combined section
            for key, val in d.items():
                if maneuver in key:
                    ret.update(d[key])
            if "common" in d:
                ret.update(d["common"])
        #QgsMessageLog.logMessage("{} configuration for {} is {}.".format(parent_section, maneuver,
        #                                                                 json.dumps(ret, indent=0)),
        #                         tag="Pathplanner", level=Qgis.Info)
        return ret

    def get_defaults_maneuver(self, maneuver):
        return self.get_defaults("maneuver", maneuver)

    def get_defaults_gui(self, maneuver):
        return self.get_defaults("gui", maneuver)

_json_config = None


def get_configuration_json():
    try:
        global _json_config
        if enable_config_caching and _json_config: return _json_config
        _json_config = JsonPropertiesParser(os.path.join(os.path.dirname(__file__), 'PathPlanner.json'))
        return _json_config
    except:
        QgsMessageLog.logMessage(traceback.format_exc(), tag="Pathplanner", level=Qgis.Critical)
        return None


def get_configuration():
    """
    Opens the configuration file PathPlanner.conf and returns the parser object
    :return:
    """
    try:
        global global_config, coord_decimals
        if enable_config_caching and global_config:
            return global_config

        config_parser = ConfigParser()
        config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'PathPlanner.conf')
        ext = ""
        if enable_config_caching:
            ext = "Caching is activated, changes to configuration file need a plugin or QGIS restart!"
        QgsMessageLog.logMessage("Trying to read configuration file %s...\n%s" % (config_file, ext), tag="Pathplanner",
                                 level=Qgis.Info)
        files = config_parser.read(config_file)
        if len(files) == 0:
            return None
        # try to read planner type
        try:
            config_parser.plannerType = config_parser.get('PlannerModel', 'PlannerType').lower()
        except:
            config_parser.plannerType = 'default'
        QgsMessageLog.logMessage("Planner type is %s" % (config_parser.plannerType), tag="Pathplanner",
                                 level=Qgis.Info)
        try:
            coord_decimals = config_parser.getint('General', 'CoordinateDecimals')
        except:
            pass
        global_config = config_parser
        return global_config
    except:
        QgsMessageLog.logMessage(traceback.format_exc(), tag="Pathplanner", level=Qgis.Critical)
        return None

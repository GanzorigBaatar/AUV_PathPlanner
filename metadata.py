from future import standard_library

standard_library.install_aliases()
from configparser import ConfigParser
import os, io, traceback, sys
from qgis.PyQt.QtWidgets import QMessageBox


def get_plugin_metadata():
    try:
        config = ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'metadata.txt'))
        return {
            'name': config.get('general', 'name'),
            'description': config.get('general', 'description'),
            'version': config.get('general', 'version'),
            'author': config.get('general', 'author'),
            'email': config.get('general', 'email')
        }
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        errorbox = QMessageBox()
        errorbox.setText("Exception occurred!\n" + repr(traceback.format_tb(exc_traceback)))
        errorbox.exec_()
        return {
            'name': '',
            'description': '',
            'version': '',
            'author': '',
            'email': ''
        }

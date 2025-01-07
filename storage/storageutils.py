from qgis.core import QgsProject
import os

class storageutils:
    def __init__(self):
        result=[]

    def getStoragePath(self):
        my_path = QgsProject.instance().homePath()
        if not my_path:
            my_path = os.path.expanduser('~')
        return my_path

    def getXmlNodeText(node):
        nodelist = node.childNodes
        result = []
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                result.append(node.data)
            return ' '.join(result)

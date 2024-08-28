#gets API key and saves it to a .txt document
import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
from qgis.core import *
from qgis.utils import iface

pluginPath = os.path.dirname(__file__)
uiPath = os.path.join(pluginPath, 'apikey.ui')
keyPath = os.path.join(pluginPath, 'orsApiKey.txt')
WIDGET, BASE = uic.loadUiType(uiPath)

class ApiKey(BASE, WIDGET):
    def __init__(self, parent):
        self.iface=iface
        super().__init__(parent)
        self.setupUi(self)
        self.cancel.clicked.connect(self.close)
        self.OK.clicked.connect(self.getApiKey)
        if os.path.isfile(keyPath):
            currentKey = open(keyPath, 'r')
            keyString = currentKey.read()
            self.apiKey.clear()
            self.apiKey.setText(keyString)
            currentKey.close()

    def getApiKey(self):
        keyString = self.apiKey.text()
        f = open(keyPath, 'w')
        f.write(keyString)
        f.close()
        self.close()

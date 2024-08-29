# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Reach
                                 A QGIS plugin
 Selections and joins based on real transit time
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-08-26
        copyright            : (C) 2024 by Austin Kotting
        email                : kotting@au-st.in
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Austin Kotting'
__date__ = '2024-08-26'
__copyright__ = '(C) 2024 by Austin Kotting'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import sys
import inspect
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import processing
from qgis.core import QgsProcessingAlgorithm, QgsApplication
from .reach_provider import ReachAlgorithmProvider
from .getapi import *

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

class ReachAlgorithmPlugin:

    def __init__(self, iface):
        self.provider = ReachAlgorithmProvider()
        self.iface = iface

    def initProcessing(self):
        """Init Processing provider for QGIS >= 3.8."""

        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()
        self.menu = QMenu(self.iface.mainWindow())
        self.menu.setTitle('Reach')
        qgisMenu = self.iface.mainWindow().menuBar()
        qgisMenu.insertMenu(self.iface.firstRightStandardMenu().menuAction(), self.menu)
        self.openApi = QAction('Input ORS API Key', self.iface.mainWindow())
        self.menu.addAction(self.openApi)
        self.openApi.triggered.connect(self.getApi)
        iconFolder = os.path.dirname(__file__) #gets path to folder containing this file
        joinIconPath = os.path.join(iconFolder, 'join_icon.png')
        selectIconPath = os.path.join(iconFolder, 'select_icon.png')
        joinIcon = QIcon(joinIconPath)
        selectIcon = QIcon(selectIconPath)
        self.join = QAction('Join by transit time', self.iface.mainWindow())
        self.select = QAction('Select by transit time', self.iface.mainWindow())
        self.join.setIcon(joinIcon)
        self.select.setIcon(selectIcon)
        self.pluginToolbar = self.iface.addToolBar('Reach')
        self.pluginToolbar.addAction(self.join)
        self.pluginToolbar.addAction(self.select)
        self.join.triggered.connect(self.runJoin)
        self.select.triggered.connect(self.runSelect)


    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
        self.iface.removePluginMenu('Reach', self.openApi)
        self.menu.deleteLater()

    def getApi(self):
        self.getKey = ApiKey(self.iface.mainWindow())
        self.getKey.exec()

    def runJoin(self):
        processing.execAlgorithmDialog("reach:joinbytransittime")

    def runSelect(self):
        processing.execAlgorithmDialog("reach:selectbytransittime")


"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProject,
                       QgsFeatureRequest,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink)
from qgis import processing
import datetime
import requests
import json
import os


class TransitSelectAlgorithm(QgsProcessingAlgorithm):

    INPUT = 'INPUT'
    TARGET = 'TARGET'
    TRANSIT_MEANS = 'TRANSIT_MEANS'
    MAX_TIME = 'MAX_TIME'
    MIN_TIME = 'MIN_TIME'
    UNITS_MIN = 'UNITS_MIN'
    SELECT_TYPE = 'SELECT_TYPE'


    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return TransitSelectAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'selectbytransittime'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Select by Transit Time')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return ''

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("Example algorithm short description")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        #self.addParameter
        print('my dick is on the phone and it says initAlgorithm was run')

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Select from features in'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.TARGET,
                self.tr('By transit time from'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        mt = QgsProcessingParameterNumber(
                self.MAX_TIME,
                description=self.tr('Maximum transit time'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10
            )

        mt.setMetadata({'widget_wrapper':
            { 'decimals': 2 }
        })

        self.addParameter(mt)

        mint = QgsProcessingParameterNumber(
                self.MIN_TIME,
                description=self.tr('Minimum transit time'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0,
                optional=True
            )

        mint.setMetadata({'widget_wrapper':
            { 'decimals': 2 }
        })

        self.addParameter(mint)





        self.addParameter(
            QgsProcessingParameterBoolean(
                self.UNITS_MIN,
                description=self.tr('Transit time is in minutes (uncheck to use hours)'),
                defaultValue=True
            )
        )
        tt = QgsProcessingParameterString(
            self.TRANSIT_MEANS,
            description=self.tr('Means of transit'),
            defaultValue='Walking'
        )
        tt.setMetadata({'widget_wrapper':
            { 'value_hints': ['Walking',
                'Wheelchair',
                'Driving (car)',
                'Driving (HGV)',
                'Cycling (regular)',
                'Cycling (road)',
                'Cycling (mountain)',
                'Cycling (electric)',
                'Hiking']
            }
        })
        self.addParameter(tt)
        st = QgsProcessingParameterString(
            self.SELECT_TYPE,
            description=self.tr('Type of selection'),
            defaultValue='New Selection'
        )
        st.setMetadata({'widget_wrapper':
            { 'value_hints': ['New Selection',
                'Add to Selection',
                'Remove from Selection']
            }
        })
        self.addParameter(st)

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.

        filename = os.path.basename(__file__).split('.')[0]
        print(filename)
        saveAs = filename + str(datetime.datetime.now()).replace(':','_').replace('.','_') + '.txt'
        pluginPath = os.path.dirname(__file__)
        logFolder = r"D:\Python_plugins\Reach_Debug"
        keyPath = os.path.join(pluginPath, 'orsApiKey.txt')

        logPath = os.path.join(logFolder, saveAs) #time is defined at the very beginning so we don't have a bunch of different time stamps
        apiLinks = {'Walking':'https://api.openrouteservice.org/v2/matrix/foot-walking',
            'Wheelchair':'https://api.openrouteservice.org/v2/matrix/wheelchair',
            'Driving (car)':'https://api.openrouteservice.org/v2/matrix/driving-car',
            'Driving (HGV)':'https://api.openrouteservice.org/v2/matrix/driving-hgv',
            'Cycling (regular)':'https://api.openrouteservice.org/v2/matrix/cycling-regular',
            'Cycling (road)':'https://api.openrouteservice.org/v2/matrix/cycling-road',
            'Cycling (mountain)':'https://api.openrouteservice.org/v2/matrix/cycling-mountain',
            'Cycling (electric)':'https://api.openrouteservice.org/v2/matrix/cycling-electric',
            'Hiking':'https://api.openrouteservice.org/v2/matrix/foot-hiking'
        }
        def rec(content):
            f = open(logPath, 'a')
            f.write(str(content))
            f.write('\n')
            f.close()

        src = self.parameterAsSource(
            parameters,
            self.INPUT,
            context
        )
        #rec(src)
        srcLayName = src.sourceName()
        dest = self.parameterAsSource(
            parameters,
            self.TARGET,
            context
        )

        maxTime = self.parameterAsDouble(
            parameters,
            self.MAX_TIME,
            context
        )
        minTime = self.parameterAsDouble(
            parameters,
            self.MIN_TIME,
            context
        )

        unitsMin = self.parameterAsBoolean(
            parameters,
            self.UNITS_MIN,
            context
        )

        transitType = self.parameterAsString(
            parameters,
            self.TRANSIT_MEANS,
            context
        )

        selType = self.parameterAsString(
            parameters,
            self.SELECT_TYPE,
            context
        )

        locs=[]

        if unitsMin:
            t = (maxTime*60)
            tmin = (minTime*60)
            timeSuffix = '_min'
        else:
            t = (maxTime*3600)
            tmin = (minTime*3600)
            timeSuffix = '_hr'

        if os.path.isfile(keyPath):
            currentKey = open(keyPath, 'r')
            schluessel = currentKey.read()
        else:
            iface.messageBar().pushMessage('Error', 'API key not found', level=Qgis.Critical, duration=3)

        apilink = apiLinks[transitType]

        srcIds = []

        for feat in src.getFeatures():
            srcIds.append(feat.id())
        #rec(srcIds)


        def getpoints(lay):
            lay = lay.materialize(QgsFeatureRequest())
            crs = lay.crs()
            l = processing.run('native:reprojectlayer', {
            'INPUT': lay,
            'TARGET_CRS': 'EPSG:4326',
            'OUTPUT': 'memory:Reprojected'})
            for p in l['OUTPUT'].getFeatures():
                c = p.geometry().centroid().asWkt()
                c = c.split(' ', 1)[1].replace('(', '').replace(')', '')
                c = c.split()
                c[0]=float(c[0])
                c[1]=float(c[1])
                locs.append(c)
            return l['OUTPUT'] #need this?

        getpoints(src)
        numSrc = len(src)
        numDest = len(dest)
        getpoints(dest)
        sources = list(range(0, numSrc))
        numAll = numSrc + numDest
        dests = list(range(numSrc,numAll))
        body = {"locations":locs, 'sources': sources, 'destinations':dests} #yes this is right, it makes more sense with the way the API returns stuff
        headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        'Authorization': schluessel,
        'Content-Type': 'application/json; charset=utf-8'
        }
        call = requests.post(apilink, json=body, headers=headers)
        m = json.loads(call.text)
        srcLay = QgsProject.instance().mapLayersByName(srcLayName)[0]
        if call.ok:
            durations = m['durations']
            valid = []
            validSources =[]
            for n, pt in list(enumerate(durations)):
                if min(pt) <= t and min(pt) >= tmin:
                    valid.append(n)
                    nearest = pt.index(min(pt))

            for val in valid:
                validSources.append(srcIds[val])
            if selType == 'Add to Selection':
                srcLay.select(validSources)
            elif (selType == 'Remove from Selection'):
                srcLay.deselect(validSources)
            else:
                srcLay.removeSelection()
                srcLay.select(validSources)
            #rec(valid)
            #rec(validSources)

        else:
            iface.messageBar().pushMessage('Error', 'API Call Error', level=Qgis.Critical, duration=3)
        return {}






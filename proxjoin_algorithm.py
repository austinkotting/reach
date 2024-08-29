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
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
from qgis.core import *
from qgis.utils import iface




from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterString,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFeatureSink,
                       QgsFeatureRequest)
import processing
import datetime
import requests
import json
import os



class TransitJoinAlgorithm(QgsProcessingAlgorithm):


    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    JOIN = 'JOIN'
    OUTPUT = 'OUTPUT'
    FIELDS_TO_ADD = 'FIELDS_TO_ADD'
    FIELD_PREFIX = 'FIELD_PREFIX'
    TRANSIT_MEANS = 'TRANSIT_MEANS'
    MAX_TIME = 'MAX_TIME'
    MIN_TIME = 'MIN_TIME'
    UNITS_MIN = 'UNITS_MIN'
    TIME_FIELD = 'TIME_FIELD'
    TIME_FIELD_NAME = 'TIME_FIELD_NAME'



    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return TransitJoinAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'joinbytransittime'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Join by Transit Time')

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

    def flags(self):
        return super().flags() | QgsProcessingAlgorithm.FlagNoThreading

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
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Join to features in'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.JOIN,
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



        self.addParameter(
            QgsProcessingParameterField(
                self.FIELDS_TO_ADD,
                description=self.tr('Fields to copy (will copy all fields if left blank)'),
                allowMultiple = True,
                parentLayerParameterName = self.JOIN,
                defaultToAllFields = True

            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.FIELD_PREFIX,
                description=self.tr('Prefix for joined fields (underscore will be automatically added)'),
                optional=True,
                defaultValue=r'Joined'
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.TIME_FIELD,
                description=self.tr('Include transit time in new field?'),
                defaultValue=True
                )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.TIME_FIELD_NAME,
                description=self.tr('Name of transit time field'),
                optional=True
            )
        )


##        tt.setMetadata({'widget_wrapper':
##            { 'value_hints': ['Walking',
##                    'Wheelchair',
##                    'Driving (car)',
##                    'Driving (HGV)',
##                    'Cycling (regular)',
##                    'Cycling (road)',
##                    'Cycling (mountain)',
##                    'Cycling (electric)',
##                    'Hiking']
##            }
##        })






        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.

        """
        time = str(datetime.datetime.now()).replace(':','_').replace('.','_') + '.txt'
        pluginPath = os.path.dirname(__file__)
        logFolder = r"D:\Python_plugins\Reach_Debug"
        keyPath = os.path.join(pluginPath, 'orsApiKey.txt')

        logPath = os.path.join(logFolder, time) #time is defined at the very beginning so we don't have a bunch of different time stamps
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

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.


        inputLay = self.parameterAsSource(
            parameters,
            self.INPUT,
            context
        )

        joinLay = self.parameterAsSource(
            parameters,
            self.JOIN,
            context
        )


        fieldsToAdd = self.parameterAsFields(
            parameters,
            self.FIELDS_TO_ADD,
            context
        )

        transitType = self.parameterAsString(
            parameters,
            self.TRANSIT_MEANS,
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
        includeTime = self.parameterAsBoolean(
            parameters,
            self.TIME_FIELD,
            context
        )
        timeFieldName = self.parameterAsString(
            parameters,
            self.TIME_FIELD_NAME,
            context
        )
        fieldPrefix = self.parameterAsString(
            parameters,
            self.FIELD_PREFIX,
            context
        )



        joinTypes = {'One-to-many (separate features for each matching feature)':0,
            'One-to-one (attributes only from first matching feature)':1
        }







        # If source was not found, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSourceError method to return a standard
        # helper text for when a source cannot be evaluated
        if inputLay is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))







        locs=[]
        inputFeatures = inputLay.getFeatures()
        joinFeatures = joinLay.getFeatures()
        inputIdsAll = []
        joinIdsAll = []
        for f in inputFeatures:
            inputIdsAll.append(f.id())

        for f in joinFeatures:
            joinIdsAll.append(f.id())

        if unitsMin:
            t = (maxTime*60)
            tmin = (minTime*60)
            timeSuffix = '_min'
        else:
            t = (maxTime*3600)
            tmin = (minTime*3600)
            timeSuffix = '_hr'

        if len(timeFieldName) != 0:
            includeTimeName = timeFieldName + timeSuffix
        else:
            includeTimeName = 'Time_' + transitType.replace(' (', '_').replace(')', '') + timeSuffix

        if os.path.isfile(keyPath):
            currentKey = open(keyPath, 'r')
            schluessel = currentKey.read()
        else:
            iface.messageBar().pushMessage('Error', 'API key not found', level=Qgis.Critical, duration=3)

        apilink = apiLinks[transitType]

        def getpoints(lay): ## this accepts a source instead of a layer, 'materialize' turns it into a layer i guess?
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
            return l['OUTPUT']

        clone_layer = getpoints(inputLay)
        #rec(clone_layer)
        numInput = len(clone_layer)
        clone_join_temp = getpoints(joinLay)
        j = processing.run('native:retainfields', {
            'INPUT': clone_join_temp,
            'FIELDS': fieldsToAdd,
            'OUTPUT': 'memory:'
        })
        clone_join = j['OUTPUT']


        fieldPrefix = fieldPrefix + r'_'
        joinFields = clone_join.fields()

        clone_join.startEditing()
        for field in clone_join.fields():
            name = field.name()
            idx = clone_join.fields().indexFromName(field.name())

            clone_join.renameAttribute(idx, fieldPrefix+name)
        clone_join.commitChanges()


        numJoin = len(clone_join)
        sources = list(range(0, numInput))
        numAll = numInput + numJoin
        dests = list(range(numInput, numAll))
        body = {"locations":locs, 'sources': sources, 'destinations':dests} #changed from the select prox function!
        headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        'Authorization': schluessel,
        'Content-Type': 'application/json; charset=utf-8'
        }

        call = requests.post(apilink, json=body, headers=headers)
        errorMessage = 'API Error: ' + str(call)
        m = json.loads(call.text)

        if call.ok:

            #rec('call is okay')
            durations = m['durations']

            validInputIds = []
            validJoinIds = []
            times = {}
            pairs = {}
            for n, pt in list(enumerate(durations, 1)):
                if min(pt) <= t and min(pt) >= tmin:
                    validInputIds.append(n)
                    nearest = pt.index(min(pt))+1
                    validJoinIds.append(nearest)
                    pairs[n] = nearest
                    if unitsMin:
                        times[n] = (min(pt))/60
                    else:
                        times[n] = (min(pt))/3600




            fieldList = clone_layer.fields()



            joinFieldList = clone_join.fields().names()
            #rec(joinFieldList)






            clone_layer.dataProvider().addAttributes([QgsField("temp",  QVariant.Int)])

            clone_layer.dataProvider().addAttributes([QgsField(includeTimeName, QVariant.Double, prec=2)])


            clone_layer.updateFields()
            clone_join.dataProvider().addAttributes([QgsField("temp_j",  QVariant.Int)])
            clone_join.updateFields()

            idxTempInput = clone_layer.fields().indexFromName('temp')
            ##fieldList.remove(idxTempInput)
            idxTimeInput = clone_layer.fields().indexFromName(includeTimeName)


            idxTempJoin = clone_join.fields().indexFromName('temp_j')
            for i in validInputIds:

                clone_layer.dataProvider().changeAttributeValues({i:{idxTempInput:pairs[i], idxTimeInput:times[i]}})


            clone_layer.updateFields()
            for i in validJoinIds:
                clone_join.dataProvider().changeAttributeValues({i:{idxTempJoin:i}})
            clone_join.updateFields()





##this is where the sink definition was before, let's see if it works better in a different spot




            # Send some information to the user
            feedback.pushInfo(f'CRS is {inputLay.sourceCrs().authid()}')

            # If sink was not created, throw an exception to indicate that the algorithm
            # encountered a fatal error. The exception text can be any string, but in this
            # case we use the pre-built invalidSinkError method to return a standard
            # helper text for when a sink cannot be evaluated


            #rec(fieldPrefix)
            #rec('line 524')
            params = {
                'INPUT': clone_layer,
                'FIELD': 'temp',
                'INPUT_2': clone_join,
                'FIELD_2': 'temp_j',



                'OUTPUT': 'memory:',
                'DISCARD_NONMATCHING': True
            }
            new = processing.run("native:joinattributestable", params)['OUTPUT']
            new = processing.run("native:reprojectlayer", {'INPUT': new,'TARGET_CRS': inputLay.sourceCrs(),'OUTPUT': 'memory:'})['OUTPUT']
            idxTempJoinPost = new.fields().indexFromName('temp_j')
            new.dataProvider().deleteAttributes([idxTempInput, idxTempJoinPost])
            new.updateFields()
            #rec('fields updated line 532')
            features = new.getFeatures()
            invalidFeatures = []
            for f in features:
                if f[includeTimeName] == NULL:
                    invalidFeatures.append(f.id())

            new.dataProvider().deleteFeatures(invalidFeatures)
            new.updateFields()
            #rec('line 549')

            ##here we take out the time column
            if includeTime == False:
                idxTimePost = new.fields().indexFromName(includeTimeName)
                new.dataProvider().deleteAttributes([idxTimePost])
                new.updateFields()
            #rec(new.fields().names())
            allFeatures = new.getFeatures()
            newFields = new.fields()


            (sink, dest_id) = self.parameterAsSink(
                parameters,
                self.OUTPUT,
                context,
                newFields,
                inputLay.wkbType(),
                inputLay.sourceCrs()
            )
            if sink is None:
                raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
            sink.addFeatures(allFeatures, QgsFeatureSink.FastInsert)
            #rec('reached end of script')

            ##joinLay.removeSelection()


        # Compute the number of steps to display within the progress bar and
        # get features from source
##        total = 100.0 / source.featureCount() if source.featureCount() else 0
##        features = source.getFeatures()
##
##        for current, feature in enumerate(features):
##            # Stop the algorithm if cancel button has been clicked
##            if feedback.isCanceled():
##                break
##
##            # Add a feature in the sink
##            sink.addFeature(feature, QgsFeatureSink.FastInsert)
##
##            # Update the progress bar
##            feedback.setProgress(int(current * total))

        # To run another Processing algorithm as part of this algorithm, you can use
        # processing.run(...). Make sure you pass the current context and feedback
        # to processing.run to ensure that all temporary layer outputs are available
        # to the executed algorithm, and that the executed algorithm can send feedback
        # reports to the user (and correctly handle cancellation and progress reports!)


        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
            return {self.OUTPUT: dest_id}

Reach is a plugin for QGIS which allows selections and joins based on estimated travel time between points on one layer and points on another layer. 

It is intended to augment the existing QGIS Spatial Join and Select by Location features, allowing connections to be made not simply based on cartographic distance, but based on a "real" measure of how reachable one place is from another.

This initial version is based around an API call to Open Route Services. ORS offers travel time estimates for the following means of transportation:
  	
Walking, Hiking, Wheelchair, Electric bike, Road bike, Mountain bike, "Regular" bike, Car, Truck

Open Route Services limits the number of routes that can be calculated in one call to 3500. Because of this, the plugin cannot handle large numbers of source and target points at this time.

Reach establishes two new processing algorithms for QGIS: Join by transit time (reach:joinbytransittime) and Select by transit time (reach:selectbytransittime).

Known issues:

In "Select by transit time", the layer on which you intend to select items should have a unique name within the project. If the layer name is not unique, the plugin will select the features with the "correct" IDs from the first layer it finds with the matching name, which can lead to random features on an unexpected layer being selected.
  	
Open Route Services will not return wheelchair travel time information for all pairs of points, if it considers one or both to be fundamentally imaccessible to wheelchair users.

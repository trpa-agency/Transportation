# Transportation
Repository to hold all scripts related to transportation data

## Crash_Analysis_HighInjuryNetwork.py

### Summary

#### We used the SWITRS and NDOT crash data to produce High Injury Networks (HINs) for car, pedestrian, and bicycle injuries in the Lake Tahoe Basin. We also assigned a weighted crash metric to each segment of the road network based on the number of crashes that occurred on the segment with fatalities, serious injuries and Bike/Pedestrian involved crashes weighted more heavily. That weighted crash value was then used to identify hot spots of crashes on the street network.

- Initial data processing
    - To weight crashes by their severity, each crash in our database was given a “crash severity value” of 5 for a mortality, 3 for a severe injury, 2 for any crash involving a bicyclist or pedestrian and 1 for all other crashes with an injury. Property only crashes were excluded from the analysis because they are not reported for California.
    - Each crash was snapped to the nearest line in our street network dataset. 
    - The injuries and fatalities for each mode of transportation as well as the crash severity values calculated in the previous step were summed for all crashes along each segment of the streets network using the arcpy.SpatialJoin tool to provide segment totals.
- Creating the HIN
    - Injuries and fatalities were summed by mode of transportation for each segment and divided by the segment length to provide a “victims per mile” metric.
    - Because Nevada does not report bike or pedestrian fatalities separately, we summed the number of bike or pedestrian involved accidents for each segment and used that to calculate a “bike involved per mile” and “pedestrian involved per mile” metric.
    - Segments were then selected in descending order of victims or crashes per mile until 65% of the total number of victims had been accounted for. These segments constituted the HIN for that mode of transportation.
    -  Following SCAG’s approach (https://scag.ca.gov/sites/main/files/file-attachments/scag-hin-methodology-072022.pdf?1658855532) we initially set a length threshold of >.25 miles for a segment to be included in the HIN but because so many of our segments are small this didn’t account for 65% of the total number of victims, leading to every segment >.25 being included in the HIN. We tested adjusting the length threshold and determined that either no threshold or >.05 is a better fit for our current network. This is something that we want to revisit if we can improve our street network.
- Hot Spot Analysis
    - Crash values were weighted by severity (‘Fatal’ = 5, ‘Severe Injury’ = 3, ‘Pedestrian or Bike Involved’ = 2, ‘Minor/Other’ = 1), then crash points were snapped to the nearest street segment, and individual crash weights were summed by the segment they were spatially joined to. 
    - The summed ‘Crash_Rate_Weighted’ value was used as the input field for the arcpy.stats.HotSpots tool to analyze hot spots by street segment. To keep the crash hot spots local, the Impedance Cutoff was set to 100 meters (about the length of a football field). This is the minimum stopping sight distance for a vehicle traveling 45MPH. To ensure the results are reliable, while keeping the size of the spatial weights matrix manageable, the Maximum Number of Neighbors was limited to 30. 
    - The results were displayed as a gradient of confidence intervals, with cold to hot being represented as statistically significant break points of 90, 95, 99% confidence intervals.

### Next Steps…

    - Better streets network. 
    - Method for dealing with overweighting single accidents 
    - County level analysis
    - Method to create standard segment lengths
    -  Develop/Test Emerging Hot Spot analysis methods again (space-time cube didn’t produce expected results this time around)

### Works Cited

    [ESRI Crash Analysis Workflow] (https://desktop.arcgis.com/fr/analytics/case-studies/analyzing-crashes-2-pro-workflow.htm)

    [SCAG HIN Methods] (https://scag.ca.gov/sites/main/files/file-attachments/scag-hin-methodology-072022.pdf?1658855532)

### Local Project Information

    - Network Path: F:\GIS\PROJECTS\Transportation\Vision Zero\CrashAnalysis
    - Web Map: https://trpa.maps.arcgis.com/home/item.html?id=ddfe6635070e4063bb411d12225ad45f
    - ArcGIS Pro Project: "F:\GIS\PROJECTS\Transportation\Vision Zero\CrashAnalysis\Crash Analysis.aprx"
    - Python Notebook: "F:\GIS\PROJECTS\Transportation\Vision Zero\CrashAnalysis\CrashAnalysis.ipynb"


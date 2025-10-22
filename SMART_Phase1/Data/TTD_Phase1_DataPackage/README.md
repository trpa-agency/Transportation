# README for Intelligent Sensor Integration on Rural Multi-Modal System with an Urban Recreation Travel Demand, Lake Tahoe Basin, NV and CA
Strengthening Mobility and Revolutionizing Transportation (SMART) Program, U.S. Department of Transportation (USDOT)
10.10.2025 


## Links to Dataset  
Dataset Archive Link: <https://doi.org/10.21949/1530332>  
Data Management Plan DOI: <https://dmphub.uc3prd.cdlib.net/dmps/10.48321/D1F82E31EA>  

## Summary of Dataset  

`The Tahoe Transportation District (TTD) and regional partners are seeking to enhance transportation safety and mobility along key corridors in the Lake Tahoe Basin. The roadway network entering, traveling within, and leaving the Tahoe Basin lacks the infrastructure required to acquire real-time and historical traffic and congestion data. This pilot project aims to support TTD and the regional partners in collecting accurate count data at each of the
seven entry/exit points of the Tahoe Basin and along the Truckee/US80/SR267/SR89 roadways.

The project is designed to plan, prototype, test, and evaluate a limited deployment of a data collection sensor infrastructure to gather transportation and traveler-related information. The goal is to integrate this information into a single cloud-based open source or interface for reporting and management. This information will be utilized by TTD, TRPA, partners, commuters, and travelers within the Tahoe Basin and adjoining areas to provide an integrated infrastructure for collecting vehicle data. This data will be incorporated into a database for various stakeholders.
Furthermore, the project will establish the framework for long-term data collection across the region and integrate multiple transportation data sources for efficient use by partner agencies. It will propel the region toward real-time parking availability for motorists and improve the ease of transit use, walking, and bicycling. Other long-term uses include sharing information about weather hazards, closures, construction, or crashes.
`  


## Tables of Contents  
##### A. General Information  
##### B. Sharing/Access & Policies Information  
##### C. Data and Related Files Overview  
##### D. Methodological Information  
##### E. Data-Specific Information for: TTD_Phase1_Dataset
##### F. Update Log  


## A. General Information  

TTD_Phase1_Dataset  

**Description of the Dataset:** Sample data collected during Phase 1 of Tahoe Transportation District's SMART grant from AI Cameras deployed around the Tahoe Basin. The dataset includes camera locations, safety insights, vehicle counts, VRU counts, and sample videos recorded of wrong way drivers.

**Dataset Archive Link:** <https://doi.org/10.21949/1530332>  

**Authorship Information:**  

>  *Principal Data Creator or Data Manager Contact Information*  
>  Name: Mason Bindl
>  Institution: Tahoe Regional Planning Agency    
>  Address: 128 Market Street, Stateline, Nevada 
>  Email: gis@trpa.gov

>  *Associate Data Creator Contact Information*  
>  Name: Andrew McClary 
>  Institution: Tahoe Regional Planning Agency 
>  Address: 128 Market Street, Stateline, Nevada   
>  Email: gis@trpa.gov     

>  *Associate Data Creator Contact Information*  
>  Name: Rachael Shaw 
>  Institution: Tahoe Regional Planning Agency 
>  Address: 128 Market Street, Stateline, Nevada   
>  Email: gis@trpa.gov  

>  *Organizational Contact Information*  
>  Name: Tara Styer 
>  Institution: Tahoe Transportation District
>  Address: 128 Market Street, Stateline, Nevada
>  Email: tstyer@tahoetransportation.org   

**Date of data collection and update interval:** January 2025 to October 2025

**Geographic location of data collection:** Lake Tahoe Region, California and Nevada, United States of America 

**Information about funding sources that supported the collection of the data:** This dataset package was funded through the USDOT Strengthening Mobility and Revolutionizing Transportation (SMART) Program. The grant number for this project is: SMARTFY22N1P1G41.

## B. Sharing/Access and Policies Information  

**Recommended citation for the data:**  

>  Bindl, Mason., McCLary, Andrew., Shaw, Rachael., Styer, Tara. (2025). TTD ATMS Data Aggregation Plan. Strengthening Mobility and Revolutionizing Transportation (SMART) Program. <https://doi.org/10.21949/1530332>  

**Licenses/restrictions placed on the data:** This document is disseminated under the sponsorship of the U.S. Department of Transportation in the interest of information exchange. The United States Government assumes no liability for the contents thereof. To protect the privacy of subject participants and conform to the restrictions of the Institutional Review Board, raw and individual-level data will not be made available.  

**Was data derived from another source?:** No

This document was created to meet the requirements enumerated in the U.S. Department of Transportation's Plan to Increase Public Access to the Results of Federally-Funded Scientific Research Version 1.1(https://doi.org/10.21949/1520559) and guidelines suggested by the DOT Public Access website(https://doi.org/10.21949/1503647), in effect and current as of December 03, 2020.  

 
## C. Data and Related Files Overview  

File List for the TTD_Phase1_Dataset

>  1. Filename: TTD_SMART_SafetyInsights.csv 
>  Short Description:  A .csv, Comma Separated Value, file of safety insights from the SMART Grant cameras in the Tahoe Basin  

>  2. Filename: TTD_SMART_Speed.csv  
>  Short Description:  The .csv, Comma Separated Value, file of vehicle speed data from the SMART Grant cameras in the Tahoe Basin 

>  3. Filename: TTD_SMART_TrafficCameraLocations.geojson
>  Short Description:  A .geojson spatial file with the locations of the SMART Grant cameras in the Tahoe Basin 

>  4. Filename: TTD_SMART_VehicleCounts.csv
>  Short Description:  A .csv, Comma Separated Value, file of vehicle counts from the SMART Grant cameras in the Tahoe Basin 

>  5. Filename: TTD_SMART_VRUCounts.csv  
>  Short Description:  A .csv, Comma Separated Value, file of vulnerable road user counts from the SMART Grant cameras in the Tahoe Basin

>  6. Filename: WWDriverVideo_03.08.2025.wmv
>  Short Description:  Video of a recorded wrong way driver event at Meyers Roundabout/US 50 on 03.08.2025

>  7. Filename: WWDriverVideo_04.19.2025.wmv
>  Short Description:  Video of a recorded wrong way driver event at Meyers Roundabout/US 50 on 04.19.2025

>  8. Filename: WWDriverVideo_07.19.2025.wmv
>  Short Description:  Video of a recorded wrong way driver event at Meyers Roundabout/US 50 on 07.19.2025

>  9. Filename: WWDriverVideo_07.20.2025.wmv  
>  Short Description:  Video of a recorded wrong way driver event at Meyers Roundabout/US 50 on 07.20.2025

>  10. Filename: WWDriverVideo_08.02.2025.wmv 
>  Short Description:  Video of a recorded wrong way driver event at Meyers Roundabout/US 50 on 08.02.2025

>  11. Filename: WWDriverVideo_08.03.2025.wmv 
>  Short Description:  Video of a recorded wrong way driver event at Meyers Roundabout/US 50 on 08.03.2025

## D. Methodological Information  

**Description of methods used for collection/generation of data:** The Intelligent Sensor Integration on Rural Multi-Modal System project leverages a suite of innovative, cloud-based and AI-driven technologies to modernize data collection and enhance transportation safety and planning in the Lake Tahoe Basin.The project deploys AI-powered video sensors at multiple locations throughout the Lake Tahoe Basin to capture multimodal traffic activity, including vehicle counts, pedestrian movements, bicyclist volumes, travel speeds, and roadway safety events. These sensors operate in three different technical configurations: 

Edge Processing: Video streams are analyzed directly in the field using AI processors connected through commercial cellular networks. 

Edge Processing: Video streams are analyzed directly in the field using AI processors connected through commercial Satellite network. 

Centralized Server Processing: Video feeds are transmitted to an AI server located at the Caltrans Traffic Management Center (TMC), where advanced analytics extract multimodal data. 

Cloud Processing: Video feeds provided by NDOT are analyzed using cloud-based machine learning platforms for scalable data extraction. 

All collected data is aggregated in a secure, cloud-hosted platform for storage, processing, and integration. The system uses Microsoft Fabric with Power BI visualization tools to enable real-time dashboards, analytics, and reporting. This infrastructure supports data sharing across agencies and lays the foundation for integration with additional datasets such as transit and parking in future stages. 

The project emphasizes interoperability and accessibility by developing an online open-data portal in collaboration with the Tahoe Regional Planning Agency (TRPA). This portal provides authenticated access for partner agencies to visualize, download, and analyze multimodal traffic and safety data. Using available tools such as ArcGIS Online and open-source Python libraries, TRPA will enhance the data presentation layers  to include more interactive dashboards, charts, and geospatial visualizations. 

**Instrument or software-specific information needed to interpret the data:** 
The .csv, Comma Separated Value, file is a simple format that is designed for a database table and supported by many applications. The .csv file is often used for moving tabular data between two different computer programs, due to its open format. The most common software used to open .csv files are Microsoft Excel and RecordEditor, (for more information on .csv files and software, please visit https://www.file-extensions.org/csv-file-extension).

The .geojson format is an open geospatial format used to encode a variety of geographic data structures. The file type can be opened and use by many GIS programs, such as ArcGIS and QGIS (for more information on .geojson files and software, please visit https://www.file-extensions.org/geojson-file-extension).

The .wmv format is a multimedia format storing videos. These files can be played using most standard audio and visual software, such as Windows Media Player or VLC Media Player (for more information on .aiff files and software, please visit https://www.file-extensions.org/aiff-file-extension). 

## E. Data-Specific Information  

1. TTD_SMART_SafetyInsights.csv 
- Number of variables (columns): 12 
- Number of cases/rows: 24245  
- Each row represents: 1 recorded safety event
- Data Dictionary/Variable List: DataDictionary 

2. TTD_SMART_Speed.csv 
- Number of variables (columns): 5
- Number of cases/rows: 364 
- Each row represents: Recorded vehicle counts for a given speed interval from a specific direction at a specified camera location
- Data Dictionary/Variable List: DataDictionary  

3. TTD_SMART_TrafficCameraLocations.geojson
-A feature layer of the SMART Traffic Camera Locations with longitude and latitude 
- Data Dictionary/Variable List: DataDictionary  

4. TTD_SMART_VehicleCounts.csv
- Number of variables (columns): 8
- Number of cases/rows: 450242
- Each row represents: Recorded vehicle counts during a specified time interval from a specific direction at a specified camera location, classified by vehicle type
- Data Dictionary/Variable List: DataDictionary 

5. TTD_SMART_VRUCounts.csv
- Number of variables (columns): 7
- Number of cases/rows: 43631
- Each row represents: Recorded vulnerable road user counts for a given time interval from a specific direction at a specified camera location
- Data Dictionary/Variable List: DataDictionary 

## F. Update Log  

This README.txt file was originally created on 2025-10-10 by Rachael Shaw, Associate Transportation Planner, Tahoe Regional Planning Agency, gis@trpa.gov.

2025-10-10: Original file created

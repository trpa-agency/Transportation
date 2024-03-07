with query_geo as (
SELECT raw_id as name, geom as geometry FROM `replica-customer.Geos.trct_2020` where raw_id in ('06061020107',
'06061020106',
'06061020104',
'06061020105',
'06061022100',
'06017030402',
'06017031601',
'06017030404',
'06017031602',
'06017030301',
'06017030302',
'06017032002',
'06017032001',
'06017030506',
'06017030201',
'06017030507',
'06017030202',
'06017030403',
'06017030502',
'06017030504',
'06061022200',
'06061022300',
'32031003311',
'32031003305',
'32031003306',
'32031003308',
'32031003307',
'32031003310',
'32005001800',
'32005001700',
'32005001600')
),
Tahoe_Network_Segments as 
(
SELECT
	stableEdgeId, streetName, distance, osmid
	
FROM `replica-customer.cal_nev.cal_nev_2022_Q4_network_segments` as b
JOIN query_geo AS o
	ON ST_INTERSECTS(o.geometry, b.geometry))
	
Select 
 travel_purpose, stableEdgeID, streetname, osmid, sum(distance)*0.00000062 as segment_distance_traveled, count(activity_id) as number_of_trips
from   
`replica-customer.cal_nev.cal_nev_2022_Q4_thursday_trip` 
as trips
cross join unnest(trips.network_link_ids) as linkids
Join
Tahoe_Network_Segments
ON 
stableEdgeId = linkids
group by travel_purpose, stableEdgeID, streetname, osmid
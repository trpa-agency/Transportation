with query_geo as (
SELECT raw_id as name, geom as geometry FROM `geo_table` where raw_id in ('06061020107',
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
	stableEdgeID, distance
	
FROM `segment_table` as b
JOIN query_geo AS o
	ON ST_INTERSECTS(o.geometry, b.geometry)),
Tahoe_Trips as (
select activity_id, person_id, sum(Tahoe_Network_Segments.distance) as distance_in_basin
from   
`trip_table` 
as trips
cross join unnest(trips.network_link_ids) as linkids
Join
Tahoe_Network_Segments
ON 
stableEdgeId = linkids
group by activity_id, person_id
)	
Select 
 origin_bgrp, destination_bgrp, mode, travel_purpose, Population.BLOCKGROUP,
 origin_bgrp_lat, origin_bgrp_lng, destination_bgrp_lat, destination_bgrp_lng,
 sum(distance_in_basin) as total_distance_in_basin,
 Population.lat as home_lat, Population.lng as home_lng, 
 count(Tahoe_Trips.activity_id) as number_of_trips,
sum(distance_miles) as total_distance_miles
from `trip_table` as Full_Trip
inner join Tahoe_Trips ON Full_Trip.activity_id = Tahoe_Trips.activity_id
left join `population_table` as Population
on Tahoe_Trips.person_id = Population.person_id
GROUP BY
origin_bgrp, destination_bgrp, mode, travel_purpose, Population.BLOCKGROUP,
origin_bgrp_lat, origin_bgrp_lng, destination_bgrp_lat, destination_bgrp_lng,
Population.lat, Population.lng


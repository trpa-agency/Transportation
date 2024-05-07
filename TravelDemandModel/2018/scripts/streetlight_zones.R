library(pacman)
p_load(tidyverse, sf, mapview,tmap)

taz<-st_read("model_taz","taz_sde") %>%
  st_transform(crs=4326)

rec14<- read_csv("2014BaseRTP011516 - RTP 2017 base year/zonal/OvernightVisitorZonalData_Summer.csv") %>%
  select(taz, beach) %>%
  filter(beach!=0) %>%
  rename(TAZ=taz)

rec14_taz<-taz %>% left_join(rec14, by="TAZ") %>%
  filter(!is.na(beach)) 
rec14_taz <- bind_cols(rec14_taz, data.frame(st_area(rec14_taz) * 0.000001) %>% rename(km2=st_area.rec14_taz....1e.06)) %>%
  mutate(km2=as.numeric(km2), 
         size=case_when(km2 > 4 ~ "larger than 4km2", 
                        TRUE ~ as.character("smaller than 4km2")))

nonrec14<-taz %>% left_join(rec14, by="TAZ") %>%
  filter(is.na(beach))
nonrec14<- bind_cols(nonrec14, data.frame(st_area(nonrec14) * 0.000001) %>% rename(km2=st_area.nonrec14....1e.06)) %>%
  mutate(km2=as.numeric(km2),
         size=case_when(km2 > 4 ~ "larger than 4km2", 
                        TRUE ~ as.character("smaller than 4km2")))

tm_shape(rec14_taz) + tm_polygons(col="red", alpha=.2) + tm_shape(nonrec14) + tm_polygons(col="blue", alpha=.2)

## tazs that were not 'rec' previously but which have rec areas in them

add_to_rec_tazs<-data.frame(
  TAZ=c(45,53,44,10,64,99,100,101,115,111,132,87,122,155,154,159,157,158,162,173,185,186,187,182,286, 289, 271,270,266,229,217,219,206,205,201,216 ,207, 9,22,30, 96, 98),
  label=c('tahoe keys','tahoe keys','tahoe keys','heavenly gondola','high meadows','washoe meadows','washoe meadows','tahoe mountain','cascade lake','glen alpine trailhead', 'echo lake', 'big meadow trailhead', 'rubicon peak trailhead', 'fanny bridge','william b layton park', 'tahoe state rec area', 'tahoe commons beach', 'tahoe city golf course', 'truckee river - tahoe city', 'burton creek state park','north tahoe regional park','brockway summit', 'brockway summit','brockway golf club', 'incline flume','incline flume','incline golf course','incline golf course','east shore trailhead','zephyr cove','rabe meadows','round hill','rabe meadows', 'kahle community park','edgewood golf', 'castle rock trailhead', 'van sickle trailhead','lakeside beach','bijou golf source', 'bijou park','tahoe paradise park', 'lake tahoe golf course')
)

add <- nonrec14 %>% left_join(add_to_rec_tazs,by="TAZ") %>%
  filter(!is.na(label))

rec18_taz <-rbind(rec14_taz %>% mutate(label=NA),add) %>%
  filter(size=="smaller than 4km2")

zones_shrunk<-st_read("rec_attractiveness","big_zones")

final_rec<- rbind(zones_shrunk, rec18_taz) 
final_rec<- bind_cols(final_rec %>% data.frame(),
    data.frame(st_area(final_rec) * 0.000001) %>% rename(km2_final=st_area.final_rec....1e.06)
    )
 
st_write(final_rec, "rec_attractiveness/final_rec_zones", driver="ESRI Shapefile")



tm_shape(nonrec14) + tm_polygons(col="blue", alpha=.2) + tm_shape(rec18_taz) + tm_polygons(col="red", alpha=.2) 
 
 st_write(rec18_taz %>% filter(size=="larger than 4km2"), "rec_attractiveness","big_zones", driver="ESRI Shapefile")

taz <-st_read("H:/model/model_update_2019/WSP/Streetlight/taz_trpa", "taz_trpa") %>%
  st_transform(crs=4326)
taz_group <- read_csv("H:/model/model_update_2019/WSP/Streetlight/taz_grouping_forstreetlight_RH.csv")
group<-taz %>% left_join(taz_group, by=c("TAZ"="taz"))

map<-group %>% group_by(group) %>% summarise() %>% mapview()
mapshot(map, "H:/model/model_update_2019/WSP/Streetlight/taz_trpa/rec_zones.html")


raghu <-st_read("H:/model/model_update_2019/WSP/Streetlight", "taz_trpa_grouped")
area<-st_area(raghu) %>% data.frame()
colnames(area) <- "area"
rec<-bind_cols(raghu,area) %>%
  mutate(area=area/1000)


library(pacman)
p_load(tidycensus, tidyverse,leaflet, geojsonio, sf, tmap, tmaptools, DT, xfun,readxl, mapview)

tmap_mode("view")

taz<-st_read("model_taz","taz_sde") %>%
  st_transform(crs=4326)

# traffic count data
continuous<-read_csv("H:/model/model_update_2019/validation/continuous.csv") %>%
  mutate(weekday=wday(Date, label=TRUE), month=month(Date, label=TRUE), Day1=as.character(Day)) %>%
  mutate(station_code=station)

# traffic counts for factoring
counts <- continuous %>%
  mutate(Day1=as.character(Day)) %>%
  filter(month %in% c("Jun","Aug","Sep")) %>%
  group_by(Day1, month, weekday) %>%
  summarise(Count=sum(Count, na.rm=T))

weekday <- counts %>% filter(Day1 %in% c("2018-06-04","2018-06-05","2018-06-06","2018-06-07",
                                                   "2018-06-11","2018-06-12","2018-06-13","2018-06-14",
                                                   "2018-08-30","2018-08-29","2018-08-28","2018-08-27",
                                                   "2018-09-10","2018-09-11", "2018-09-12","2018-09-13",
                                                   "2018-09-17","2018-09-18","2018-09-19","2018-09-20")) %>% ungroup() %>%
  mutate(av_count=mean(Count, na.rm=T))
unique(weekday$av_count)

all <- counts %>% ungroup() %>%
  mutate(av_count=mean(Count, na.rm=T))
unique(all$av_count)

#ratio - apply a 90% factor (or 10% reduction in the CSLT occupancy rates)
unique(weekday$av_count)/unique(all$av_count)

camp<-st_read("F:/GIS/PROJECTS/ResearchAnalysis/Recreation/Data/Campgrounds.gdb", "Campground_Access_Points") %>%
  st_transform(crs=4326) %>%
  mutate(CAMPSITE_SOURCE=as.character(CAMPSITE_SOURCE)) %>%
  select(RECREATION_NAME) %>%
  left_join(read_csv( "campsites/campsites_final.csv" ), by="RECREATION_NAME") %>%
  mutate(Occupancy= case_when(is.na(Occupancy) ~ mean(Occupancy, na.rm=T),
                              TRUE ~ as.numeric(Occupancy)),
         Occupancy=case_when(RECREATION_NAME=="CAMPGROUND BY THE LAKE" ~ Occupancy,
                             TRUE ~ Occupancy * (unique(weekday$av_count)/unique(all$av_count))))

camp_taz<-st_join(camp, st_buffer(taz,0)) %>%
  group_by(TAZ) %>%
  summarise(NUMBER_OF_SITES=sum(NUMBER_OF_SITES,na.rm=T),
            occ=mean(Occupancy,na.rm=T))

write.csv(camp_taz %>% data.frame() %>% select(-Shape), "final_inputs_2020_RTP/campsites.csv")


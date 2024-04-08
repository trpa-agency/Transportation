library(pacman)
p_load(tidyverse, sf, ggmap,mapview, tmap)

# google key
register_google(key="AIzaSyA3lBYiTffOPFATH9Brv0eJ0IR6DgXK5tY")

taz<-st_read("model_taz","taz_sde") %>%
  st_transform(crs=4326)

school <- read_csv("school_enrollment/tahoe_schools.csv") %>%
  mutate(address_full=paste(address, zip, state, sep=" "))


school_geocode<-geocode(school$address_full, output="more") %>%
  select(lon, lat)

school_final<-bind_cols(school, school_geocode) %>%
  spread(school_level, enrollment) %>%
  st_as_sf(crs=4326, coords=c("lon","lat"))

school_taz <- st_join(school_final,st_buffer(taz,0), largest=T) %>%
  data.frame() %>% 
  group_by(TAZ) %>% 
  summarise(college=sum(college, na.rm=T),elementary=sum(elementary, na.rm=T),middle=sum(middle, na.rm=T),high=sum(high, na.rm=T))

write.csv(school_taz, "final_inputs_2020_RTP/school_enrollment.csv")


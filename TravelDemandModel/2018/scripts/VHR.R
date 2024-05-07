library(pacman)
p_load(tidycensus, tidyverse,leaflet, geojsonio, sf, tmap, tmaptools, DT, xfun,readxl)

taz<-st_read("model_taz","taz_sde") %>%
  st_transform(crs=4326)

#VHR by jurisdiction
vhr <- st_read("F:/GIS/PROJECTS/ResearchAnalysis/VHR/Data/VHR_Fall2018.gdb" , "Parcel_Master_VHR_Fall2018") %>%
  filter(VHR != 0) %>%
  st_transform(crs=4326)


vhr_taz<-st_join(st_buffer(vhr,0), st_buffer(taz,0), largest=TRUE) %>%
  data.frame() %>%
  group_by(TAZ) %>% 
  summarise(VHR=sum(VHR, na.rm=T))



vhr %>% data.frame() %>% group_by(JURISDICTION) %>%
  summarise(VHR=sum(VHR, na.rm=T)) %>%
  add_row(JURISDICTION="WA", VHR=963) %>%
  mutate(total_vhr=sum(VHR))


# washoe VHR
acs_var <- load_variables(2017, "acs5", cache = TRUE)
wa_acs <- get_acs(geography = "block group", year=2017, 
                  variables =  c("B25004_006"),
                  state = "NV", county="Washoe", geometry = T)

wa_vhr<- wa_acs %>%
  left_join(data.frame(block_group), by="GEOID") %>%
  filter(!is.na(STATEFP)) %>%
  mutate(variable_name = case_when (variable== "B25004_006" ~ "Vacant Units - seasonal/rec/occasional")) %>%
  select(GEOID, NAME.x, variable, estimate, variable_name) %>%
  mutate(total=sum(estimate), percent=estimate/total,
         total_wa_vhr=963,
         vhr_block_group= round(total_wa_vhr * percent,0))
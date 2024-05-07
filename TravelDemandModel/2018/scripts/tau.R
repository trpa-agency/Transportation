library(pacman)
p_load(tidycensus, tidyverse,leaflet, geojsonio, sf, tmap, tmaptools, DT, xfun)

taz<-st_read("model_taz","taz_sde") %>%
  st_transform(crs=4326)

parcel<-st_read("F:/GIS/PROJECTS/ResearchAnalysis/AnnualReport/2018/Data", "parcel_master_commodities_2018_report") %>%
  st_transform(crs=st_crs(taz))
 # filter(RES_UNITS !=0 | TAU_UNITS !=0 | !is.na(RES_UNITS) | !is.na(TAU_UNITS))

dev_rights_taz<- st_join(st_buffer(parcel,0), st_buffer(taz,0), largest=TRUE) 

# taus by unit type

tau_type <- read_excel("TAU/2018_tau_lindsey_data_revised1_kk_final.xlsx", sheet = "Sheet3") %>% mutate(APN1=APN)

tau_type_final<-dev_rights_taz %>% data.frame() %>% filter(TAU_UNITS !=0) %>% 
  left_join(tau_type, by="APN") %>%
  select(APN,APN1,`Type of Establishment`, TAU_UNITS.x,TAZ, `Checked TAU_UNITS_no`) %>%
  group_by(TAZ, `Type of Establishment`) %>% summarise(TAU_Units= sum(TAU_UNITS.x), TAU_units_lindsey=sum(`Checked TAU_UNITS_no`)) 

# tau occupancy rate

alec<-read_excel("lodging_occupancy/taus_alec_AO.xlsx", sheet="alec") %>%
  mutate(address=paste(APO_ADD, "CA","96150", sep=" ")) %>%
  filter(!is.na(`Peak Summer Occupancy Rate`)) %>% 
  filter(`Peak Summer Occupancy Rate` != 0) %>%
  filter(`Peak Summer Occupancy Rate` <= 1)

alec_parcel <- dev_rights_taz %>% left_join(alec, by="APN") %>%
  filter(!is.na(`Peak Summer Occupancy Rate`)) %>%
  group_by(TAZ, `Type of Establishment`) %>%
  summarise(peak_summer_occupancy=mean(`Peak Summer Occupancy Rate`, na.rm=T))


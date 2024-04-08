library(pacman)
p_load(tidycensus, tidyverse,leaflet, geojsonio, sf, tmap, tmaptools, DT, xfun,readxl, ggmap, mapview, lubridate)

county <- geojson_read("https://opendata.arcgis.com/datasets/85a2e8e4bf994742a5855c1339517681_16.geojson", what='sp') %>% st_as_sf() %>% st_transform(4326) %>%
  st_cast("MULTIPOLYGON")

boundary <- geojson_read("https://opendata.arcgis.com/datasets/85a2e8e4bf994742a5855c1339517681_0.geojson", what='sp') %>% st_as_sf() %>% st_transform(4326) 

# traffic count data
continuous<-read_csv("H:/model/model_update_2019/validation/continuous.csv") %>%
  mutate(weekday=wday(Date, label=TRUE), month=month(Date, label=TRUE), Day1=as.character(Day)) %>%
  mutate(station_code=station)

# 2014 data
fourteen_on <- read_csv("H:/model/final_2014_RTP_scenarios/2014BaseRTP011516/2014BaseRTP011516/zonal/OvernightVisitorZonalData_Summer.csv") %>%
  rowwise() %>%
  mutate(lodging_total=sum(c(hotelmotel,resort,casino)))

fourteen_onr <- read_csv("H:/model/final_2014_RTP_scenarios/2014BaseRTP011516/2014BaseRTP011516/zonal/VisitorOccupancyRates_Summer.csv") %>%
  rowwise() %>%
  mutate(lodging_av=mean(c(hotelmotel,resort,casino))) %>%
  left_join(fourteen_on, by="taz") %>%
  rowwise() %>%
  mutate(occupied_lodging_units=lodging_av * lodging_total,
         occupied_campground= campground.x * campground.y)

# TAZ
taz<-st_join(
    st_buffer(
  st_read("model_taz","taz_sde") %>%
  st_transform(crs=4326),0),
    st_buffer(
      county,0), largest=TRUE)

#parcel
parcel<-st_read("F:/GIS/PROJECTS/ResearchAnalysis/AnnualReport/2018/Data", "parcel_master_commodities_2018_report") %>%
  st_transform(crs=st_crs(taz)) %>%
  mutate(APN=as.character(APN))

# google key
register_google(key="AIzaSyA3lBYiTffOPFATH9Brv0eJ0IR6DgXK5tY")

## TAU numbers
tau <- read_excel("lodging_occupancy/2018_tau_lindsey_data_revised1_kk_final.xlsx", sheet="Sheet1")

tau_kk<-tau %>% select(APN, `Checked TAU_UNITS`,`Linda - Model Type`, `CURRENT ESTABLISHMENT NAME`, KK) %>%
  rename(tau=`Checked TAU_UNITS`,type=`Linda - Model Type`, name=`CURRENT ESTABLISHMENT NAME`) %>%
  filter(tau !=0)

tau_parcel<- st_join(
  st_buffer(parcel %>% left_join(tau_kk, by="APN") %>% filter(!is.na(type)) %>% select(APN, tau, type,name),0),
  st_buffer(taz,0),largest=T)

tau_taz<- st_join(
  st_buffer(parcel %>% left_join(tau_kk, by="APN") %>% filter(!is.na(type)) %>% select(APN, tau, type),0),
  st_buffer(taz,0),largest=T) %>%
  data.frame() %>%
  group_by(TAZ,type) %>%
  summarise(tau=sum(tau,na.rm=T)) %>%
  pivot_wider(names_from=type, values_from=tau) %>%
  rename(hotelmotel=`Hotel/Motel`, resort=Resort, casino=Casino)
  

##### CSLT rates #####

# traffic counts for factoring
cslt_counts <- continuous %>%
  mutate(Day1=as.character(Day)) %>%
  filter(station %in% c("Midway","Bigler","F_Street", "Echo_Summit", "Sawmill") & month %in% c("Jun","Aug")) %>%
  group_by(Day1, month, weekday) %>%
  summarise(Count=sum(Count, na.rm=T))

cslt_weekday <- cslt_counts %>% filter(Day1 %in% c("2018-06-04","2018-06-05","2018-06-06","2018-06-07",
                                                   "2018-06-11","2018-06-12","2018-06-13","2018-06-14",
                                                   "2018-08-30","2018-08-29","2018-08-28","2018-08-27",
                                                   "2018-09-10","2018-09-11", "2018-09-12","2018-09-13",
                                                   "2018-09-17","2018-09-18","2018-09-19","2018-09-20")) %>% ungroup() %>%
  mutate(av_count=mean(Count, na.rm=T))
unique(cslt_weekday$av_count)

cslt_all <- cslt_counts %>% ungroup() %>%
  mutate(av_count=mean(Count, na.rm=T))
unique(cslt_all$av_count)

#ratio - apply a 90% factor (or 10% reduction in the CSLT occupancy rates)
unique(cslt_weekday$av_count)/unique(cslt_all$av_count)

## cslt rates
cslt <- read_excel("lodging_occupancy/Annual_Patterns_KK.xlsx", sheet="CSLT Hotel Motel Occupancy", skip=4) %>%
  mutate(Address_Full=paste(Address, "CA", "96150", sep=" "))
  
cslt_occ<-geocode(cslt$Address_Full, output="more")

cslt_occ_sf<- bind_cols(cslt, cslt_occ) %>%
  st_as_sf(coords=c("lon","lat")) %>%
  st_set_crs(4326)

cslt_occ_taz <- st_join(cslt_occ_sf,st_buffer(taz,0), largest=T) %>%
  rowwise() %>%
  mutate(rooms_av=sum(c(`June 2018 - Total Rms Avail/Month`,`Aug 2018 - Total Rms Avail/Month`)), 
         rooms_oc=sum(c(`June 2018 - No Rms Rented`,`Aug 2018 - No Rms Rented`))) %>%
  group_by(TAZ,type) %>% summarise(rooms_oc=sum(rooms_oc,na.rm=T),rooms_av=sum(rooms_av,na.rm=T)) %>%
  mutate(occ=(rooms_oc/rooms_av) * (unique(cslt_weekday$av_count)/unique(cslt_all$av_count))) %>%
  select(1,2,5) %>%
  pivot_wider(names_from = type, values_from =occ ) %>%
  rename(hotelmotel=`Hotel/Motel`, resort=Resort) %>%
  mutate(casino=NA) 

## douglas

dg_counts <- continuous %>%
  mutate(Day1=as.character(Day)) %>%
  filter(station %in% c("Lower Kingsbury (SR 207)") & month %in% c("Jun","Aug","Sep")) %>%
  group_by(Day1, month, weekday) %>%
  summarise(Count=sum(Count, na.rm=T))

dg_weekday <- dg_counts %>% filter(Day1 %in% c("2018-06-04","2018-06-05","2018-06-06","2018-06-07",
                                                 "2018-06-11","2018-06-12","2018-06-13","2018-06-14",
                                                 "2018-08-30","2018-08-29","2018-08-28","2018-08-27",
                                                 "2018-09-10","2018-09-11", "2018-09-12","2018-09-13",
                                                 "2018-09-17","2018-09-18","2018-09-19","2018-09-20")) %>% ungroup() %>%
  mutate(av_count=mean(Count, na.rm=T))
unique(dg_weekday$av_count)

dg_all <- dg_counts %>% ungroup() %>%
  mutate(av_count=mean(Count, na.rm=T))
unique(dg_all$av_count)

#ratio - apply a 90% factor (or 10% reduction in the CSLT occupancy rates)
unique(dg_weekday$av_count)/unique(dg_all$av_count)

# douglas occupancy data from Douglas_County_Room Tax Reports 18-19 Revised 9-4-2019-1 PDF -
# june august and september all days
dg_occ<-taz %>% filter(COUNTY=="DOUGLAS") %>%
  mutate(occ_june_2018= case_when(TAZ %in% c(200,202,206) ~ 0.8094,
                                  TRUE ~ 0.5925),
         occ_aug_2018= case_when(TAZ %in% c(200,202,206) ~ 0.8224,
                                  TRUE ~ 0.7105),
         occ_sep_2018= case_when(TAZ %in% c(200,202,206) ~ 0.7670,
                                  TRUE ~ 0.6011),
         type=case_when(TAZ %in% c(200,202,206) ~ 'casino',
                        TAZ==210 ~ 'resort',
                        TRUE ~ as.character('hotelmotel'))
         ) %>%
  data.frame() %>%
  select(TAZ, occ_june_2018, occ_aug_2018, occ_sep_2018, type) %>%
  rowwise() %>%
  mutate(avg_occ=mean(c(occ_june_2018,occ_aug_2018,occ_sep_2018, na.rm=T)) * (unique(dg_weekday$av_count)/unique(dg_all$av_count))) %>%
  select(TAZ, type, avg_occ) %>%
  pivot_wider(names_from=type, values_from=avg_occ)

## washoe

wa_counts <- continuous %>%
  mutate(Day1=as.character(Day)) %>%
  filter(station %in% c("SR 28 & Lakeshore Dr (Incline)") & month %in% c("Jun","Aug","Sep")) %>%
  group_by(Day1, month, weekday) %>%
  summarise(Count=sum(Count, na.rm=T))

wa_weekday <- wa_counts %>% 
                filter(Day1 %in% c("2018-06-04","2018-06-05","2018-06-06","2018-06-07",
                                   "2018-06-11","2018-06-12","2018-06-13","2018-06-14",
                                    "2018-08-30","2018-08-29","2018-08-28","2018-08-27",
                                    "2018-09-10","2018-09-11", "2018-09-12","2018-09-13",
                                    "2018-09-17","2018-09-18","2018-09-19","2018-09-20")) %>% ungroup() %>%
  mutate(av_count=mean(Count, na.rm=T))
unique(wa_weekday$av_count)

wa_all <- dg_counts %>% ungroup() %>%
  mutate(av_count=mean(Count, na.rm=T))
unique(wa_all$av_count)

#ratio - apply a 90% factor (or 10% reduction in the CSLT occupancy rates)
unique(wa_weekday$av_count)/unique(wa_all$av_count)

## washoe occupancyr for june aug and sep
wa_occ<-taz %>% filter(COUNTY=="WASHOE") %>%
  mutate(occ_june_2018= 0.809 * (unique(wa_weekday$av_count)/unique(wa_all$av_count)),
         occ_aug_2018=0.841* (unique(wa_weekday$av_count)/unique(wa_all$av_count)),
         occ_sep_2018=0.762* (unique(wa_weekday$av_count)/unique(wa_all$av_count))) %>%
  data.frame() %>%
  select(TAZ, occ_june_2018, occ_aug_2018, occ_sep_2018) %>%
  rowwise() %>%
  mutate(avg_occ=mean(occ_june_2018, occ_aug_2018, occ_sep_2018,na.rm=T),
         casino=avg_occ, hotelmotel=avg_occ, resort=avg_occ) %>%
  select(TAZ, hotelmotel, resort, casino)
  

## placer

pla_counts <- continuous %>%
  mutate(Day1=as.character(Day)) %>%
  filter(station %in% c("Brockway_Summit") & month %in% c("Apr","May","Jun","July","Aug","Sep")) %>%
  group_by(Day1, month, weekday) %>%
  summarise(Count=sum(Count, na.rm=T))

pla_weekday <- pla_counts %>% 
  filter(Day1 %in% c("2018-06-04","2018-06-05","2018-06-06","2018-06-07",
                     "2018-06-11","2018-06-12","2018-06-13","2018-06-14",
                     "2018-08-30","2018-08-29","2018-08-28","2018-08-27",
                     "2018-09-10","2018-09-11", "2018-09-12","2018-09-13",
                     "2018-09-17","2018-09-18","2018-09-19","2018-09-20")) %>% ungroup() %>%
  mutate(av_count=mean(Count, na.rm=T))
unique(pla_weekday$av_count)

pla_all <- pla_counts %>% ungroup() %>%
  mutate(av_count=mean(Count, na.rm=T))
unique(pla_all$av_count)

#ratio - apply a 90% factor (or 10% reduction in the CSLT occupancy rates)
unique(pla_weekday$av_count)/unique(pla_all$av_count)

## placer occupancyr for April thru september

pla_katie <- st_read("lodging_occupancy","Other") %>%
  st_transform(crs=4326)

pla_occ <- st_join(st_buffer(taz,0),
                    st_buffer(pla_katie,0), largest=T) %>%
  filter(!is.na(AREA_DESC)) %>%
  mutate(unit_av=case_when(
    AREA_DESC == "Carnelian Bay" ~ 736,
    AREA_DESC == "Kings Beach" ~ 27+27+11647+12267,
    AREA_DESC == "Tahoe City" ~ 6097+6164+ 9115+9381,
    AREA_DESC == "Tahoe City O.P.A." ~ 1911+1932,
    AREA_DESC == "Tahoe Vista" ~ 455+180+18723+18696+4823+4906,
    AREA_DESC == "West Shore" ~ 2821+2852+1472+1472+1092+1104
  ), unit_occ=case_when(
    AREA_DESC == "Carnelian Bay" ~ 570,
    AREA_DESC == "Kings Beach" ~ 5+11+3915+7667,
    AREA_DESC == "Tahoe City" ~ 3319+4751+5660+7246,
    AREA_DESC == "Tahoe City O.P.A." ~ 929+1499,
    AREA_DESC == "Tahoe Vista" ~ 36+17+7946+14278+267+571,
    AREA_DESC == "West Shore" ~ 1460+2438+546+1066+443+756
    )) %>% filter(!is.na(unit_av)) %>% data.frame() %>%
  mutate(hotelmotel=(unit_occ/unit_av) * (unique(pla_weekday$av_count)/unique(pla_all$av_count)) ,
         casino=NA, 
         resort=hotelmotel) %>%
  select(TAZ,hotelmotel,resort,casino) 

## combined occ
occ_all <- bind_rows(pla_occ, wa_occ, dg_occ,cslt_occ_taz) %>%
  filter_at(.vars = vars(hotelmotel, casino, resort), .vars_predicate = any_vars(!is.na(.))) 

## final taus and occupancy

tau_final<-tau_taz %>% left_join(occ_all, by="TAZ") %>% # join the tau units to the occupancy
  mutate(resort.y=case_when(is.na(resort.y) & !is.na(resort.x) ~ hotelmotel.y,
                            TRUE ~ as.numeric(resort.y)),
         resort.y=case_when(is.na(resort.x) ~ NA_real_ ,
                            TAZ == 125 ~ 0.61354750,
                            TAZ == 103 ~ 0.61354750,
                            TRUE ~ as.numeric(resort.y)),
         casino.y=case_when(is.na(casino.x) ~ NA_real_ ,
                            TRUE ~ as.numeric(casino.y)),
         hotelmotel.y=case_when(is.na(hotelmotel.x) ~ NA_real_,
                                TAZ==210 ~ resort.y,
                                TAZ==200 ~ 0.70584028,
                                TAZ %in% c(38,39) ~ 0.08558102,
                                TAZ == 61 ~ 0.67602264,
                                TAZ == 54 ~ 0.67602264,
                                TAZ %in% c(131) ~ 	0.61354750,
                                TAZ %in% c(42,43) ~ 	0.11429641,
                                TAZ %in% c(173,176) ~ 	0.67439650,
                                TRUE ~as.numeric(hotelmotel.y)),
         hotelmotel_oc=hotelmotel.x*hotelmotel.y,
         resort_oc=resort.x*resort.y,
         casino_oc=casino.x*casino.y) %>%
  filter(!(TAZ==295 & is.na(casino.y)))


write.csv(tau_final, "final_inputs_2020_RTP/tau.csv")

# vhr occupancy

# traffic counts for factoring
cslt_vhr_counts <- continuous %>%
  mutate(Day1=as.character(Day)) %>%
  filter(station %in% c("Midway","Bigler","F_Street", "Echo_Summit", "Sawmill") & month %in% c("Jun","Aug","Sep")) %>%
  group_by(Day1, month, weekday) %>%
  summarise(Count=sum(Count, na.rm=T))

cslt_vhr_weekday <- cslt_vhr_counts %>% filter(Day1 %in% c("2018-06-04","2018-06-05","2018-06-06","2018-06-07",
                                                   "2018-06-11","2018-06-12","2018-06-13","2018-06-14",
                                                   "2018-08-30","2018-08-29","2018-08-28","2018-08-27",
                                                   "2018-09-10","2018-09-11", "2018-09-12","2018-09-13",
                                                   "2018-09-17","2018-09-18","2018-09-19","2018-09-20")) %>% ungroup() %>%
  mutate(av_count=mean(Count, na.rm=T))
unique(cslt_vhr_weekday$av_count)

cslt_vhr_all <- cslt_vhr_counts %>% ungroup() %>%
  mutate(av_count=mean(Count, na.rm=T))
unique(cslt_vhr_all$av_count)

#ratio - apply a 90% factor (or 10% reduction in the CSLT occupancy rates)
unique(cslt_vhr_weekday$av_count)/unique(cslt_vhr_all$av_count)

#cslt "Zone and Room Category Sheet 1718"

cslt_vhr <- data.frame(month=c("june","aug","sep"),
                           units_available=c(28500,29264,28560),
                           units_rented=c(10894,14362,9130))

cslt_vhr_taz<-st_join(
  st_buffer(parcel %>% filter(JURISDI=="CSLT"),0),
  st_buffer(taz,0),largest=T) %>% data.frame() %>% filter(!is.na(JURISDI)) %>%
  distinct(TAZ) %>%
  mutate(occ=(sum(cslt_vhr$units_rented)/sum(cslt_vhr$units_available)) *(unique(cslt_vhr_weekday$av_count)/unique(cslt_vhr_all$av_count)))
  
# placer "Placer Statistical YTC feb 2019"

pla_vhr_counts <- continuous %>%
  mutate(Day1=as.character(Day)) %>%
  filter(station %in% c("Brockway_Summit") & month %in% c("Apr","May","Jun","July","Aug","Sep")) %>%
  group_by(Day1, month, weekday) %>%
  summarise(Count=sum(Count, na.rm=T))

pla_vhr_weekday <- pla_vhr_counts %>% 
  filter(Day1 %in% c("2018-06-04","2018-06-05","2018-06-06","2018-06-07",
                     "2018-06-11","2018-06-12","2018-06-13","2018-06-14",
                     "2018-08-30","2018-08-29","2018-08-28","2018-08-27",
                     "2018-09-10","2018-09-11", "2018-09-12","2018-09-13",
                     "2018-09-17","2018-09-18","2018-09-19","2018-09-20")) %>% ungroup() %>%
  mutate(av_count=mean(Count, na.rm=T))
unique(pla_vhr_weekday$av_count)

pla_vhr_all <- pla_vhr_counts %>% ungroup() %>%
  mutate(av_count=mean(Count, na.rm=T))
unique(pla_vhr_all$av_count)

#ratio - apply a 90% factor (or 10% reduction in the CSLT occupancy rates)
unique(pla_vhr_weekday$av_count)/unique(pla_vhr_all$av_count)

pla_katie <- st_read("lodging_occupancy","Other") %>%
  st_transform(crs=4326)

pla_vhr_occ <- st_join(st_buffer(taz,0),
                   st_buffer(pla_katie,0), largest=T) %>%
  filter(!is.na(AREA_DESC)) %>%
  mutate(unit_av=case_when(
    AREA_DESC == "Carnelian Bay" ~ 91+92+4062+4038+21131+26241,
    AREA_DESC == "Kings Beach" ~ 486+541+544+702+1417+1018+13381+12217,
    AREA_DESC == "Kings Beach O.P.A." ~ 182+184+7861+10333+182+276+7657+9110,
    AREA_DESC == "Tahoe City" ~ 904+6239+6625+91+92+272+367+2557+3242,
    AREA_DESC == "Tahoe City O.P.A." ~ 30+10104+13339+12781+18803,
    AREA_DESC == "Tahoe Vista" ~ 91+92 +6663+6819+91+36+91+92+6227+7843,
    AREA_DESC == "Tahoe Vista O.P.A." ~ 91+92+3011+3502,
    AREA_DESC == "West Shore" ~ 91+92+19114+20503+182+184+763+915+32722
  ), unit_occ=case_when(
    AREA_DESC == "Carnelian Bay" ~ 66+77+1132+2367+5441+12409,
    AREA_DESC == "Kings Beach" ~ 235+469+238+395+238+698+2476+4949,
    AREA_DESC == "Kings Beach O.P.A." ~ 69+99+1090+3188+93+160+1626+3439,
    AREA_DESC == "Tahoe City" ~ 252+1107+2901+21+69+109+150+770+1510,
    AREA_DESC == "Tahoe City O.P.A." ~ 2+13+1970+5680+3147+7659,
    AREA_DESC == "Tahoe Vista" ~ 14+39+2121+4369+59+20+15+77+1370+3539,
    AREA_DESC == "Tahoe Vista O.P.A." ~ 52+50+894+1711 ,
    AREA_DESC == "West Shore" ~ 85+89+8742+12597+35+69+341+552+8626
  )) %>% filter(!is.na(unit_av)) %>% data.frame() %>%
  mutate(occ=(unit_occ/unit_av)*(unique(pla_vhr_weekday$av_count)/unique(pla_vhr_all$av_count))) %>%
  select(TAZ, occ)


## vhr occ final

vhr_occ_final<-bind_rows(pla_vhr_occ, cslt_vhr_taz %>% mutate(area="cslt") %>% select(TAZ,occ))

write.csv(vhr_occ_final,"final_inputs_2020_RTP/vhr_occ.csv")


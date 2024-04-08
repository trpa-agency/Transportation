library(pacman)
p_load(tidycensus, sf, tidyverse, geojsonio, mapview, ggmap,readxl, readr)
census_api_key("680398dff0a2f4c566f10c95888da7f25e55147b")
options(tigris_use_cache = TRUE)
tract <- geojson_read("https://opendata.arcgis.com/datasets/85a2e8e4bf994742a5855c1339517681_3.geojson", what="sp") %>%
  st_as_sf() %>% st_transform(4326)
block_group<-geojson_read("https://opendata.arcgis.com/datasets/85a2e8e4bf994742a5855c1339517681_2.geojson", what="sp") %>% st_as_sf() %>% st_transform(4326)
block<-geojson_read("https://opendata.arcgis.com/datasets/85a2e8e4bf994742a5855c1339517681_1.geojson", what="sp") %>% st_as_sf() %>% st_transform(4326)
county <- geojson_read("https://opendata.arcgis.com/datasets/85a2e8e4bf994742a5855c1339517681_16.geojson", what='sp') %>% st_as_sf() %>% st_transform(4326) %>%
  st_cast("MULTIPOLYGON")
taz<-st_read("model_taz","taz_sde") %>%
  st_transform(crs=4326)

# google key
register_google(key="AIzaSyA3lBYiTffOPFATH9Brv0eJ0IR6DgXK5tY")

## residential units

parcel<-st_read("F:/GIS/PROJECTS/ResearchAnalysis/AnnualReport/2018/Data", "parcel_master_commodities_2018_report") %>%
  st_transform(crs=st_crs(taz))
# filter(RES_UNITS !=0 | TAU_UNITS !=0 | !is.na(RES_UNITS) | !is.na(TAU_UNITS))
# county provided units
#wa_units<-st_read("F:/GIS/ParcelUpdate/2018_10/Washoe/Modified/WA_Staging.gdb", "Washoe_Parcels") %>%
 # select(APN, UNITS, BEDROOMS, BATHS) %>% data.frame()
#ed_units<-st_read("F:/GIS/ParcelUpdate/2018_10/El_Dorado/Modified/EL_Staging.gdb", "El_Dorado_Parcels") %>%
  #select(APN_NEW, UNIT_NBR) %>%
  #rename(APN=APN_NEW,UNITS=UNIT_NBR) %>% data.frame()

# tau
tau <- read_excel("lodging_occupancy/2018_tau_lindsey_data_revised1_kk_final.xlsx", sheet="Sheet1")
tau_kk<-tau %>% select(APN, `Checked TAU_UNITS`,`Linda - Model Type`, `CURRENT ESTABLISHMENT NAME`, KK) %>%
  rename(tau=`Checked TAU_UNITS`,type=`Linda - Model Type`, tau_name=`CURRENT ESTABLISHMENT NAME`) %>%
  select(APN,tau, tau_name) %>%
  filter(tau!=0)

#rez <- read_csv("F:/Research and Analysis/Commodities Tracking/Residential_Units/res_units_11_15_19.csv")
#for_ken<-parcel %>% data.frame() %>% left_join(rez, by="APN") %>% left_join(tau_kk, by="APN")
# vhr occupancy

vhr_occ_final<-read_csv("final_inputs_2020_RTP/vhr_occ.csv")

# ken verified

ken<-read_excel("residential_units/Residential Updates_kk.xlsx", sheet="Sheet1")
ken_multi<-read_excel("residential_units/Multifamily_verified_kk_aly.xlsx", sheet="Multifamily research")

# reid verified

rh<-read_csv("H:/model/model_update_2019/data_inputs/residential_units/RH_verified.csv")

#STPUD sewer
#stpud_lat<-st_read("F:/GIS/GIS_DATA/Sewer_Infrastructure/STPUD/STPUD_20190620.gdb","sLateralLine") %>%
 # st_transform(crs=4326)

# CSLT verified

cslt_multi<-read_excel("residential_units/CSLT MFD Changes.xlsx", sheet="Sheet1")

## CSLT SRO units 

SRO <- data.frame(
  address=c("4081 Cedar Ave","913 Friday Ave","4122 Pine Blvd","920 Alameda Ave","3918 Pioneer Trail","1040 Martin Ave","2215 Lake Tahoe Blvd","4085 Pine Blvd","2187 Lake Tahoe Blvd","580 Emerald Bay Rd","947 Poplar St","977 Park Ave","953 Park Ave","4131 Manzanita Ave","3994 Pine Blvd","947 Park Ave"),
  name=c("Mellow Mountain Hostel","Stateline Lodge","The Shamrock","Tahoe Pines Motel","Elizabeth Lodge","Sierra Pines","El Nido Motel","Tahoe Country Inn","Matterhorn Inn","The Mountain Resort","Poplar Apts","Ski Haus","Paradice Motel","All Seasons Cottages","La Bella Apts","Mark Twain"),
  units=c(4,31,23,15,20,26,20,12,18,11,5,19,5,5,3,14)
) %>%
  mutate(full_address=paste(address, "96150","CA", sep=" "))
SRO_geocode<-geocode(SRO$full_address, output="more")
sro_final <- bind_cols(SRO, SRO_geocode) %>%
  select(address, name, units, lon,lat) %>%
  st_as_sf(crs=4326, coords=c("lon","lat"))
sro_parcels <- st_join(sro_final, st_buffer(parcel,0)) %>%
  data.frame() %>% select(APN, units,name) %>%
  rename(sro_units=units, sro_name=name)

## retired parcels

retired_res<- read_csv("residential_units/Parcels_for_retired.csv") %>%
  filter(RetiredFromDevelopment=="Yes")
retired_parcels<-parcel %>% data.frame() %>% 
  left_join(retired_res %>% select(RetiredFromDevelopment, APN), by="APN") %>%
  filter(RetiredFromDevelopment=="Yes") %>%
  select(APN, RetiredFromDevelopment)

## residential allocations

alloc <- read_excel("residential_units/residentialAllocationGrid.xlsx", sheet = "First Sheet") %>%
  filter(`Allocation Status` %in% c("Allocated","Allocated w/out Transaction")) %>%
  filter(!is.na(`Receiving Parcel APN`)) %>%
  filter(`Receiving Parcel APN` != " ") %>%
  rename(APN=`Receiving Parcel APN`) %>%
  distinct(APN,`Allocation Status`) %>%
  arrange(APN) %>%
  slice(-1)
alloc_res<-parcel %>% data.frame() %>%
  left_join(alloc, by="APN") %>%
  filter(!is.na(`Allocation Status`)) %>%
  select(`Allocation Status`, APN)

## BMP verified parcels

bmp<-read_csv("residential_units/BMP_Verified_LandUse.csv") 
parcel_bmp <- parcel %>% data.frame() %>%
  left_join(bmp, by="APN") %>%
  select(APN, Verified_L) %>%
  filter(!is.na(Verified_L)) %>%
  rename(bmp_verified_land_use=Verified_L)
bmp_cert <- read_csv("residential_units/BMP_Status.csv") %>%
  filter(BMPStatus=="BMP") %>%
  select(APN,LandUse,TMDL_LandU) %>%
  rename(bmp_cert_land_use=LandUse, bmp_cert_TMDL_land_use=TMDL_LandU) %>%
  mutate(bmp_cert_yes_no="yes")

## zillow land use

zillow<-foreign::read.dbf("residential_units/zillow.dbf") %>%
  distinct(Address, Home_Type, Lattitude, Longitude, Tax_Year, Year_Sold) %>%
  st_as_sf(crs=4326, coords=c("Longitude","Lattitude"))
zparcel<-st_join(zillow, st_buffer(parcel,0)) %>% data.frame() %>%
  mutate(Address=as.character(Address),APO_ADD=as.character(APO_ADD)) %>%
  #filter(Address==APO_ADD) %>%
  rename(zillow_home_type=Home_Type,
         zillow_year_sold=Year_Sold,
         zillow_tax_year=Tax_Year) %>%
  select(APN, Address, APO_ADD, zillow_home_type, zillow_year_sold) %>%
  group_by(APN) %>%
  summarise(Address=paste(Address, collapse=" & "),
            zillow_home_type=paste(zillow_home_type, collapse=" & "),
            zillow_year_sold=paste(zillow_year_sold, collapse=" & "),
            APO_ADD=paste(APO_ADD, collapse=" & "),
            n_zillow=n())

## VHR

vhr_wo_washoe_18 <- st_read("F:/GIS/PROJECTS/ResearchAnalysis/VHR/Data/VHR_Fall2018.gdb" , "Parcel_Master_VHR_Fall2018") %>%
  filter(VHR != 0) %>%
  st_transform(crs=4326) %>%
  select(APN, VHR) 

## aly's web research on VHRs for Washoe - she estimated 547 compared to the 963 provided to use in 2018
vhr_washoe_19<-st_read("F:/GIS/PROJECTS/ResearchAnalysis/VHR/Data/VHR_Fall2019.gdb","Parcel_Master_VHR_WA_EstimateAdded") %>%
  filter(!is.na(VACATION_HOME_RENTAL) & JURISDICTION=="WA") %>%
  st_transform(crs=4326) %>%
  select(APN,VACATION_HOME_RENTAL) %>%
  rename(VHR=VACATION_HOME_RENTAL)

vhr_all <- bind_rows(vhr_wo_washoe_18 %>% data.frame(), vhr_washoe_19 %>% data.frame())

## assign 963 washoe VHRs spatially by Allys 2019 count
vhr_washoe_19_taz<-st_join(st_buffer(vhr_washoe_19,0), st_buffer(taz,0), largest=TRUE) %>%
  group_by(TAZ) %>%
  summarise(VACATION_HOME_RENTAL=sum(VHR,na.rm=T)) %>%
  mutate(total_vhr=sum(VACATION_HOME_RENTAL), 
         proportion=VACATION_HOME_RENTAL/total_vhr,
         vhr_2018=proportion * 963) %>%
  data.frame() %>% 
  select(TAZ, vhr_2018) %>% 
  rename(VHR=vhr_2018)

## VHR by TAZ
vhr_taz<-bind_rows(
  st_join(st_buffer(vhr_wo_washoe_18,0), st_buffer(taz,0), largest=TRUE) %>%
    data.frame() %>%
    group_by(TAZ) %>%
    summarise(VHR=sum(VHR, na.rm=T)), vhr_washoe_19_taz)

## buildings
build<-st_read("residential_units/buildings","buildings")
parcel_buildings <- st_join(
  st_buffer(build %>% st_transform(crs=4326) %>% mutate(building="yes"),0),
  st_buffer(parcel,0), largest=T,
) %>% filter(!is.na(APN))

## final layer
dev<-parcel %>%
  mutate(RES_UNITS=na_if(RES_UNITS,0)) %>%
  mutate(RES_UNITS = replace(RES_UNITS, which(RES_UNITS<0), NA)) %>%
  left_join(tau_kk, by="APN") %>%
  left_join(cslt_multi, by="APN") %>%
  left_join(ken_multi %>% select(APN,`KK Verified`), by="APN") %>%
  left_join(rh %>% select(APN,rh_verified), by="APN") %>%
  left_join(ken %>% select(-Address), by='APN') %>%
  left_join(sro_parcels, by="APN") %>%
  left_join(retired_parcels, by="APN") %>%
  left_join(alloc_res, by="APN") %>%
  left_join(parcel_bmp, by= "APN") %>%
  left_join(bmp_cert, by="APN") %>%
  left_join(zparcel, by="APN") %>%
  left_join(vhr_all, by="APN") %>%
  left_join(parcel_buildings %>% data.frame() %>% distinct(APN,building) %>% select(APN, building), by="APN") %>%
  select(APN,APO_ADD.x,RES_UNITS, TAU_UNITS, CFA_SQFT, tau, tau_name, sro_name, sro_units,RetiredFromDevelopment,`Allocation Status`,bmp_verified_land_use, bmp_cert_land_use,bmp_cert_TMDL_land_use, bmp_cert_yes_no, zillow_home_type, zillow_year_sold,n_zillow, VHR, building,IMPERVI,TRPA_LU,Address,`Verified RES Units`,`KK Verified`,rh_verified, `CSLT MFDs`) %>%
  mutate(tau_final = tau,
        res_final=case_when(!is.na(`Verified RES Units`) ~ `Verified RES Units`,
                            !is.na(`CSLT MFDs`) ~ `CSLT MFDs`,
                            !is.na(`KK Verified`) ~ `KK Verified`,
                            !is.na(rh_verified) ~ rh_verified,
                            RetiredFromDevelopment == "Yes" ~ 0,
                             !is.na(sro_units) ~ sro_units, 
                            !is.na(tau_final) ~ 0,
                             !is.na(VHR) ~ as.numeric(VHR),
                            bmp_verified_land_use %in% c("Residential - Single Family Dwelling","Residential - Multi-Family Dwelling") & bmp_cert_yes_no=="yes" ~ RES_UNITS,
                            bmp_verified_land_use %in% c("Residential - Single Family Dwelling","Residential - Multi-Family Dwelling","Residential - Single Family Dwelling") ~ RES_UNITS,
                            bmp_cert_yes_no=="yes" & IMPERVI !=0~ RES_UNITS,
                            bmp_cert_land_use== "Single Family Residential"~ RES_UNITS,
                            grepl("SingleFamily",zillow_home_type) ~ RES_UNITS,
                            IMPERVI < 300 & is.na(building) & 
                               is.na(zillow_home_type) & 
                              is.na(bmp_verified_land_use) & 
                              is.na(RetiredFromDevelopment) & 
                              is.na(bmp_cert_yes_no) & 
                              !is.na(RES_UNITS) & 
                              is.na(VHR) & 
                              is.na(`Allocation Status`) & 
                              is.na(`Verified RES Units`) & 
                              TRPA_LU=="Vacant" ~ 0,
                             bmp_verified_land_use=="Residential - Single Family Dwelling" ~ 1,
                             zillow_home_type == "SingleFamily"~ 1,
                            zillow_home_type=="Duplex" ~ 2,
                            zillow_home_type=="Triplex" ~ 3,
                            zillow_home_type=="Quadruplex" ~ 4,
                            zillow_home_type=="MultiFamily2To4" ~ 3,
                            zillow_home_type=="MultiFamily5Plus" ~ 5,
                            `Allocation Status`== "Allocated"  & !is.na(RES_UNITS) ~ RES_UNITS,
                            building=="yes" & !is.na(RES_UNITS) ~ RES_UNITS,
                            IMPERVI >= 300 & !is.na(RES_UNITS)~ RES_UNITS,
                             TRUE ~ NA_real_),
        res_source=case_when(!is.na(`Verified RES Units`) ~ 'TRPA Staff Verified',
                            !is.na(`KK Verified`) ~  'TRPA Staff Verified',
                            !is.na(rh_verified) ~ 'TRPA Staff Verified',
                            RetiredFromDevelopment == "Yes" ~ "Retired",
                            !is.na(sro_units) ~ 'SRO', 
                            !is.na(tau_final) ~ 'TAU',
                            !is.na(VHR) ~ 'VHR',
                            bmp_verified_land_use %in% c("Residential - Single Family Dwelling","Residential - Multi-Family Dwelling") & bmp_cert_yes_no=="yes" ~ "Previous Res w/ BMP Verified",
                            bmp_verified_land_use %in% c("Residential - Single Family Dwelling","Residential - Multi-Family Dwelling","Residential - Single Family Dwelling") ~ "Previous Res w/ BMP Verified",
                            bmp_cert_yes_no=="yes" & IMPERVI !=0~ "Previous Res w/ BMP Verified & Impervious",
                           bmp_cert_land_use== "Single Family Residential"~ 'Previous Res w/ BMP Verified',
                           grepl("SingleFamily",zillow_home_type) ~ 'Previous Res and zillow',
                            IMPERVI < 300 & is.na(building) & 
                              is.na(zillow_home_type) & 
                              is.na(bmp_verified_land_use) & 
                              is.na(RetiredFromDevelopment) & 
                              is.na(bmp_cert_yes_no) & 
                              !is.na(RES_UNITS) & 
                              is.na(VHR) & 
                              is.na(`Allocation Status`) & 
                              is.na(`Verified RES Units`) & 
                              TRPA_LU=="Vacant" ~ 'Vacant Determination',
                            bmp_verified_land_use=="Residential - Single Family Dwelling" ~ 'BMP verified single family',
                            zillow_home_type == "SingleFamily"~ 'zillow',
                            zillow_home_type=="Duplex" ~ 'zillow',
                            zillow_home_type=="Triplex" ~ 'zillow',
                            zillow_home_type=="Quadruplex" ~ 'zillow',
                            zillow_home_type=="MultiFamily2To4" ~ 'zillow',
                            zillow_home_type=="MultiFamily5Plus" ~ 'zillow',
                            `Allocation Status`== "Allocated"  & !is.na(RES_UNITS) ~ 'Previous Res Unit w/ Allocation',
                            building=="yes" & !is.na(RES_UNITS) ~ 'Previous Res Unit w/ Building',
                            IMPERVI >= 300 & !is.na(RES_UNITS)~ 'Previous Res Unit w/ Imperious Area',
                            TRUE ~ NA_character_),
         diff=RES_UNITS-res_final,
         cfa_final=CFA_SQFT) %>%
  mutate(res_final=na_if(res_final,0),
         tau_final=na_if(tau_final,0),
         cfa_final=na_if(cfa_final,0)) 

write.csv(dev, "H:/model/model_update_2019/data_inputs/final_inputs_2020_RTP/dev_rights_parcel.csv")

dev<-read_csv( "H:/model/model_update_2019/data_inputs/final_inputs_2020_RTP/dev_rights_parcel.csv")

parcel_updated<-parcel %>% select(APN) %>%
  left_join(dev %>% data.frame() %>% select(APN, res_final, tau_final, cfa_final), by="APN") 

fgdb_path <- file.path("F:/GIS/PROJECTS/ResearchAnalysis/Development_Rights/Development_Rights.gdb")
arc.write(file.path(fgdb_path, "dev_rights_2018"), data=parcel_updated)


#qaqc parcels which have a change in residential units

dev %>% filter((is.na(res_final) & !is.na(RES_UNITS)) | (!is.na(res_final) & is.na(RES_UNITS))) %>% select(res_final, RES_UNITS, res_source, everything()) %>% View()

# res units by taz

res_unit <- st_join(st_buffer(dev %>% filter(!is.na(res_final)),0),
          st_buffer(taz,0),largest=T) %>%
  data.frame() %>%
  group_by(TAZ) %>%
  summarise(total_residential_units=sum(res_final, na.rm=T)) 

write.csv(res_unit, "H:/model/model_update_2019/data_inputs/final_inputs_2020_RTP/res_units.csv")

res_unit<-read_csv("H:/model/model_update_2019/data_inputs/final_inputs_2020_RTP/res_units.csv")

## census occupany rate

acs_var <- load_variables(2017, "acs5", cache = TRUE)
dg_acs <- get_acs(geography = "block group", year=2017, 
                  variables =  c("B25002_001","B25002_002","B25002_003"),
                  state = "NV", county="Douglas", geometry = T)
wa_acs <- get_acs(geography = "block group", year=2017, 
                  variables =  c("B25002_001","B25002_002","B25002_003"),
                  state = "NV", county="Washoe", geometry = T)
pla_acs <- get_acs(geography = "block group", year=2017, 
                   variables =  c("B25002_001","B25002_002","B25002_003"),
                   state = "CA",county="Placer", geometry = T)
ed_acs <- get_acs(geography = "block group", year=2017, 
                  variables =  c("B25002_001","B25002_002","B25002_003"),
                  state = "CA",county="El Dorado", geometry = T)
all<- rbind(dg_acs, wa_acs, pla_acs, ed_acs) %>%
  left_join(data.frame(block_group), by="GEOID") %>%
  filter(!is.na(STATEFP)) %>%
  mutate(variable_name = case_when (variable== "B25002_001" ~ "Housing Units",
                                    variable== "B25002_002" ~ "Occupied Units",
                                    variable== "B25002_003" ~ "Vacant Units"))
rate <- all %>% select(GEOID, NAME.x, variable, estimate) %>%
  filter(variable %in% c("B25002_001","B25002_002")) %>%
  spread(variable, estimate) %>%
  mutate(census_occ_rate=round(B25002_002/B25002_001,2 )) %>%
  st_transform(crs=4326)

census_occ <- st_join(
  st_buffer(taz,0), 
  st_buffer(rate,0), largest=T) %>% 
  data.frame() %>%
  select(TAZ, census_occ_rate)

#write.csv(rate %>% data.frame() %>% select(-geometry.x), "final_inputs_2020_RTP/census_occ_rate.csv")


## seasonal

acs_var <- load_variables(2018, "acs5", cache = TRUE)

dg_acs <- get_acs(geography = "block group", year=2018, 
                  variables =  c("B25002_001","B25002_002","B25002_003","B25004_002","B25004_003","B25004_004","B25004_005","B25004_006","B25004_007","B25004_008"),
                  state = "NV", county="Douglas", geometry = T)
wa_acs <- get_acs(geography = "block group", year=2018, 
                  variables =  c("B25002_001","B25002_002","B25002_003","B25004_002","B25004_003","B25004_004","B25004_005","B25004_006","B25004_007","B25004_008"),
                  state = "NV", county="Washoe", geometry = T)
pla_acs <- get_acs(geography = "block group", year=2018, 
                   variables =  c("B25002_001","B25002_002","B25002_003","B25004_002","B25004_003","B25004_004","B25004_005","B25004_006","B25004_007","B25004_008"),
                   state = "CA",county="Placer", geometry = T)
ed_acs <- get_acs(geography = "block group", year=2018, 
                  variables =  c("B25002_001","B25002_002","B25002_003","B25004_002","B25004_003","B25004_004","B25004_005","B25004_006","B25004_007","B25004_008"),
                  state = "CA",county="El Dorado", geometry = T)
all<- rbind(dg_acs, wa_acs, pla_acs, ed_acs) %>%
  left_join(data.frame(block_group), by="GEOID") %>%
  filter(!is.na(STATEFP)) %>%
  mutate(variable_name = case_when (variable== "B25002_001" ~ "Housing Units",
                                    variable== "B25002_002" ~ "Occupied Units",
                                    variable== "B25002_003" ~ "Vacant Units",
                                    variable== "B25004_002" ~ "Vacant Units - for rent",
                                    variable== "B25004_003" ~ "Vacant Units - rented, not occupied",
                                    variable== "B25004_004" ~ "Vacant Units - for sale",
                                    variable== "B25004_005" ~ "Vacant Units - sold, not occupied",
                                    variable== "B25004_006" ~ "Vacant Units - seasonal/rec/occasional",
                                    variable== "B25004_007" ~ "Vacant Units - migrant workers",
                                    variable== "B25004_008" ~ "Vacant Units - other vacant")) %>%
  select(GEOID, NAME.x, variable, estimate, variable_name) %>%
  st_transform(crs=4326) %>%
  select(variable_name, estimate, GEOID) %>%
  spread(variable_name, estimate)

seas_TAZ <- st_join(st_buffer(taz,0), st_buffer(all,0), largest=TRUE) %>%
  group_by(TAZ) %>%
  summarise(`Vacant Units - seasonal/rec/occasional`=sum(`Vacant Units - seasonal/rec/occasional`,na.rm=T), 
            `Vacant Units`=sum(`Vacant Units`,na.rm=T),
            unocc_seasonal_percent=`Vacant Units - seasonal/rec/occasional`/`Vacant Units`) %>% 
  data.frame() %>%
  select(TAZ,unocc_seasonal_percent)
  
## combined

hhsize<-read_csv("final_inputs_2020_RTP/pers_per_occ_unit.csv") %>%
  select(TAZ, persons_per_occ_unit)

res_unit_file<-res_unit %>% 
  left_join(census_occ, by="TAZ") %>%
  left_join(hhsize, by="TAZ") %>%
  rowwise() %>%
  mutate(census_occ_rate_new= census_occ_rate * 1.09115, # adjust the occupancy rate upward
         persons_per_occ_unit_new= persons_per_occ_unit,
    occ_res_unit=total_residential_units * census_occ_rate_new,
    unocc_res_unit=total_residential_units - occ_res_unit,
    unocc_res_unit=case_when(unocc_res_unit <0 ~ 0, TRUE ~ as.numeric(unocc_res_unit)),
         persons= round(persons_per_occ_unit_new * occ_res_unit,0)) %>%
  left_join(vhr_taz, by="TAZ") %>%
  left_join(vhr_occ_final %>% select(-X1) %>% rename(vhr_occ=occ),by="TAZ") %>%
  left_join(seas_TAZ, by="TAZ") %>%
  mutate(VHR=case_when(TAZ == 268 ~ 2, TAZ == 269 ~65,# remove 3 VHRS from TAZ 268 and add to 269
                       TAZ == 280 ~ 2, TAZ == 281 ~23, # remove 7 VHRS from TAZ 280 and add to 281
                       TAZ == 265 ~ 6, TAZ == 262 ~49, # remove 3 VHRS from TAZ 265 and add to 281
                       TAZ == 209 ~ 27, TAZ == 211 ~56, # remove 10 VHRS from TAZ 209 and move to 211
                       TAZ == 210 ~ 20, TAZ == 216 ~65, # remove 53 VHRS from TAZ 210 and move to 216
                       TAZ == 10 ~ 1, TAZ == 9 ~26,
                       TAZ == 206 ~ 0, # remove 4 VHRS from TAZ 206
                       is.na(VHR) ~ 0,
                       TRUE ~ as.numeric(VHR)),
         seas_unit_w_vhr=unocc_res_unit * unocc_seasonal_percent, ##unoccupied seasonal units with VHRS
         seas_unit_wo_vhr=seas_unit_w_vhr-VHR, #unoccupied seasonal units without VHRS
         seas_unit_wo_vhr= case_when(seas_unit_wo_vhr<0 ~ 0, TRUE ~ as.numeric(seas_unit_wo_vhr)),
         percentHouseSeasonal=seas_unit_wo_vhr/unocc_res_unit,
         percentHouseSeasonal=case_when(is.na(percentHouseSeasonal)~ 0, 
                                        percentHouseSeasonal < 0 ~ 0,
                                        TRUE ~ as.numeric(percentHouseSeasonal)),
         vhr_occ=case_when(!is.na(VHR) & is.na(vhr_occ) ~ 0.3863335, # assign the average vhr occupancy rate when theres a VHR without an occ rate
                           is.na(VHR) ~ NA_real_,
                           TRUE ~as.numeric(vhr_occ)),
         seas_occ=vhr_occ,
         vhr_occupied=round(VHR * vhr_occ,0),
         seas_occupied= round(seas_unit_wo_vhr * seas_occ,0),
         other_unoccupied=unocc_res_unit- (VHR+seas_unit_wo_vhr),
         other_unoccupied=case_when(other_unoccupied < 0 ~ 0, TRUE ~ as.numeric(other_unoccupied))
         ) 

sum(res_unit_file$VHR,na.rm=T)
sum(res_unit_file$vhr_occupied,na.rm=T)

sum(res_unit_file$seas_occupied,na.rm=T)
sum(res_unit_file$seas_unit_wo_vhr,na.rm=T)

test<-res_unit_file %>%
  mutate(unocc_units=total_residential_units - occ_res_unit,
         seas_units_final= percentHouseSeasonal * unocc_units,
         vhr_occ_units_final=(unocc_units-seas_units_final) * vhr_occ)

sum(test$unocc_res_unit,na.rm=T)

sum(test$seas_units_final,na.rm=T)

sum(test$vhr_occ_units_final,na.rm=T)

sum(test$vhr_occ_units,na.rm=T)

# res unit file

write.csv(res_unit_file,"final_inputs_2020_RTP/res_unit_file.csv")

## percentHouseSeasonal
#write.csv(res_occ %>% select(TAZ, percentHouseSeasonal),  "H:/model/model_update_2019/data_inputs/final_inputs_2020_RTP/percentHouseSeasonal.csv")

## occupied res unit
#write.csv(res_occ %>% select(TAZ, occ_res_unit),  "H:/model/model_update_2019/data_inputs/final_inputs_2020_RTP/occ_res_unit.csv")

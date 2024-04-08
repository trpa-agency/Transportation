library(pacman)
p_load(tidyverse, sf, formattable, mapview, tmap)

taz<-st_read("model_taz","taz_sde") %>%
  st_transform(crs=4326) %>%
  st_cast("MULTIPOLYGON")

## seasonal and VHR calcs

seas_vhr_17<-fourteen_socio %>%
  left_join(fourteen_on,by="taz") %>%
  mutate(seasonal_units=unocc_units * percentHouseSeasonal,
         VHR_and_other_unocc=unocc_units-seasonal_units)

sum(seas_vhr_17$seasonal_units,na.rm=T)

sum(seas_vhr_17$VHR_and_other_unocc,na.rm=T)

# Socioeconomic File Forecasts

fourteen_socio <- read_csv("H:/model/final_2014_RTP_scenarios/2014BaseRTP011516/2014BaseRTP011516/zonal/SocioEcon_Summer.csv") %>%
  rowwise() %>%
  mutate(emp_total=sum(c(emp_retail,emp_srvc,emp_game,emp_other, emp_rec)),
         unocc_units=total_residential_units - total_occ_units)

twenty_socio <- read_csv("H:/model/final_2014_RTP_scenarios/RTP2020030116/RTP2020030116/zonal/SocioEcon_Summer.csv")  %>%
  rowwise() %>%
  mutate(emp_total=sum(c(emp_retail,emp_srvc,emp_game,emp_other, emp_rec)))

forty_socio <- read_csv("H:/model/final_2014_RTP_scenarios/2040RTP/2040RTP/zonal/SocioEcon_Summer.csv")  %>%
    rowwise() %>%
    mutate(emp_total=sum(c(emp_retail,emp_srvc,emp_game,emp_other, emp_rec)))

socio_change <- data.frame(change=c(
## 2020 employment  
(sum(twenty_socio$emp_total) / sum(fourteen_socio$emp_total))-1,
## 2040 employment  - 3.8%
(sum(forty_socio$emp_total) / sum(fourteen_socio$emp_total))-1,
## 2020 residential unit  - 2.1%
(sum(twenty_socio$total_residential_units) / sum(fourteen_socio$total_residential_units)) - 1,
## 2040 residential unit  - 5.23%
(sum(forty_socio$total_residential_units) / sum(fourteen_socio$total_residential_units)) -1,
## 2020 total persons  - 2.06%
(sum(twenty_socio$total_persons) / sum(fourteen_socio$total_persons))-1,
## 2040 total persons   - 5.54%
(sum(forty_socio$total_persons) / sum(fourteen_socio$total_persons))-1,
## 2020 occupancy rate  - 0%
 -abs((sum(twenty_socio$total_occ_units,na.rm=T)/sum(twenty_socio$total_residential_units,na.rm=T) )- (sum(fourteen_socio$total_occ_units,na.rm=T)/sum(fourteen_socio$total_residential_units,na.rm=T)))/
  (sum(fourteen_socio$total_occ_units,na.rm=T)/sum(fourteen_socio$total_residential_units,na.rm=T)),
## 2040 occupancy rate  - 0%
-abs((sum(forty_socio$total_occ_units,na.rm=T)/sum(forty_socio$total_residential_units,na.rm=T) )- (sum(fourteen_socio$total_occ_units,na.rm=T)/sum(fourteen_socio$total_residential_units,na.rm=T)))/
  (sum(fourteen_socio$total_occ_units,na.rm=T)/sum(fourteen_socio$total_residential_units,na.rm=T)),
## 2020 low income res unit  - 0%
(sum(twenty_socio$occ_units_low_inc) / sum(fourteen_socio$occ_units_low_inc))-1,
## 2040 low income res unit  - 0%
(sum(forty_socio$occ_units_low_inc) / sum(fourteen_socio$occ_units_low_inc))-1,
## 2020 medium income res unit  - 0%
(sum(twenty_socio$occ_units_med_inc) / sum(fourteen_socio$occ_units_med_inc))-1,
## 2040 medium income res unit  - 0%
(sum(forty_socio$occ_units_med_inc) / sum(fourteen_socio$occ_units_med_inc))-1,
## 2020 high income res unit  - 0%
(sum(twenty_socio$occ_units_high_inc) / sum(fourteen_socio$occ_units_high_inc))-1 ,
## 2040 high income res unit  - 0%
(sum(forty_socio$occ_units_high_inc) / sum(fourteen_socio$occ_units_high_inc))-1,
## 2020 total occupied unit  - 2.01%
(sum(twenty_socio$total_occ_units) / sum(fourteen_socio$total_occ_units))-1 ,
## 2040 total income res unit  - 5.25%
(sum(forty_socio$total_occ_units) / sum(fourteen_socio$total_occ_units))-1 ,
## 2020 persons per unit change
(mean(twenty_socio %>% filter(persons_per_occ_unit !=0) %>% pull(persons_per_occ_unit)) / mean(fourteen_socio %>% filter(persons_per_occ_unit !=0) %>% pull(persons_per_occ_unit)))-1,
## 2040 persons per unit change
(mean(forty_socio %>% filter(persons_per_occ_unit !=0) %>% pull(persons_per_occ_unit)) / mean(fourteen_socio %>% filter(persons_per_occ_unit !=0) %>% pull(persons_per_occ_unit)))-1),
forecast_value=c(sum(twenty_socio$emp_total),
        sum(forty_socio$emp_total),
        sum(twenty_socio$total_residential_units),
        sum(forty_socio$total_residential_units),
        sum(twenty_socio$total_persons),
        sum(forty_socio$total_persons),
        sum(twenty_socio$total_occ_units,na.rm=T)/sum(twenty_socio$total_residential_units,na.rm=T),
        sum(forty_socio$total_occ_units,na.rm=T)/sum(forty_socio$total_residential_units,na.rm=T),
        sum(twenty_socio$occ_units_low_inc),
        sum(forty_socio$occ_units_low_inc),
        sum(twenty_socio$occ_units_med_inc),
        sum(forty_socio$occ_units_med_inc),
        sum(twenty_socio$occ_units_high_inc),
        sum(forty_socio$occ_units_high_inc),
        sum(twenty_socio$total_occ_units),
        sum(forty_socio$total_occ_units),
        mean(twenty_socio %>% filter(persons_per_occ_unit !=0) %>% pull(persons_per_occ_unit)),
        mean(forty_socio %>% filter(persons_per_occ_unit !=0) %>% pull(persons_per_occ_unit))),
base_value=c(sum(fourteen_socio$emp_total),
                 sum(fourteen_socio$emp_total),
                 sum(fourteen_socio$total_residential_units),
                 sum(fourteen_socio$total_residential_units),
                 sum(fourteen_socio$total_persons),
                 sum(fourteen_socio$total_persons),
             sum(fourteen_socio$total_occ_units,na.rm=T)/sum(fourteen_socio$total_residential_units,na.rm=T),
             sum(fourteen_socio$total_occ_units,na.rm=T)/sum(fourteen_socio$total_residential_units,na.rm=T),
                 sum(fourteen_socio$occ_units_low_inc),
                 sum(fourteen_socio$occ_units_low_inc),
                 sum(fourteen_socio$occ_units_med_inc),
                 sum(fourteen_socio$occ_units_med_inc),
                 sum(fourteen_socio$occ_units_high_inc),
                 sum(fourteen_socio$occ_units_high_inc),
                 sum(fourteen_socio$total_occ_units),
                 sum(fourteen_socio$total_occ_units),
             mean(fourteen_socio %>% filter(persons_per_occ_unit !=0) %>% pull(persons_per_occ_unit)),
             mean(fourteen_socio %>% filter(persons_per_occ_unit !=0) %>% pull(persons_per_occ_unit))),
forecast_year=c(2020,2040,2020,2040,2020,2040,2020,2040,2020,2040,2020,2040,2020,2040,2020,2040,2020,2040),
base_year=c(2014,2014,2014,2014,2014,2014,2014,2014,2014,2014,2014,2014,2014,2014,2014,2014,2014,2014),
category=c("employment ","employment ","residential unit ","residential unit ","total persons ","total persons ", "census occupancy rate ", "census occupancy rate ","low income res unit ","low income res unit ","medium income res unit ","medium income res unit ","high income res unit ","high income res unit ","total occupied unit ","total occupied unit ", "persons per occupied unit", "persons per occupied unit")
)

# School Enrollment Forecasts

fourteen_school <- read_csv("H:/model/final_2014_RTP_scenarios/2014BaseRTP011516/2014BaseRTP011516/zonal/SchoolEnrollment.csv") %>%
  rowwise() %>%
  mutate(school_total=sum(c(elementary_school_enrollment,middle_school_enrollment,high_school_enrollment,college_enrollment)))

twenty_school <- read_csv("H:/model/final_2014_RTP_scenarios/RTP2020030116/RTP2020030116/zonal/SchoolEnrollment.csv") %>%
  rowwise() %>%
  mutate(school_total=sum(c(elementary_school_enrollment,middle_school_enrollment,high_school_enrollment,college_enrollment)))

forty_school <- read_csv("H:/model/final_2014_RTP_scenarios/2040RTP/2040RTP/zonal/SchoolEnrollment.csv") %>%
  rowwise() %>%
  mutate(school_total=sum(c(elementary_school_enrollment,middle_school_enrollment,high_school_enrollment,college_enrollment)))

school_change<- data.frame(change=c(
## 2020 school enrollment  - 2.58%
  (sum(twenty_school$school_total) / sum(fourteen_school$school_total))-1,
  ## 2040 school enrollment  - 12.1%
(sum(forty_school$school_total) / sum(fourteen_school$school_total))-1),
base_year=c(2014,2014),
base_value=c(sum(fourteen_school$school_total)),
forecast_year=c(2020,2040),
forecast_value=c(sum(twenty_school$school_total),sum(forty_school$school_total)),
category=c("school enrollment ","school enrollment "))

# Overnight Visitor Forecasts

fourteen_on <- read_csv("H:/model/final_2014_RTP_scenarios/2014BaseRTP011516/2014BaseRTP011516/zonal/OvernightVisitorZonalData_Summer.csv") %>%
  rowwise() %>%
  mutate(lodging_total=sum(c(hotelmotel,resort,casino)))

twenty_on <- read_csv("H:/model/final_2014_RTP_scenarios/RTP2020030116/RTP2020030116/zonal/OvernightVisitorZonalData_Summer.csv") %>%
  rowwise() %>%
  mutate(lodging_total=sum(c(hotelmotel,resort,casino)))

forty_on <- read_csv("H:/model/final_2014_RTP_scenarios/2040RTP/2040RTP/zonal/OvernightVisitorZonalData_Summer.csv") %>%
  rowwise() %>%
  mutate(lodging_total=sum(c(hotelmotel,resort,casino)))

ov_unit_change<- data.frame(change=c(
## 2020 lodging unit  - 0.8%%
(sum(twenty_on$lodging_total) / sum(fourteen_on$lodging_total))-1,
## 2040 lodging unit  - 1.5%%
(sum(forty_on$lodging_total) / sum(fourteen_on$lodging_total))-1,
## 2020 campground  - 0%%
(sum(twenty_on$campground) / sum(fourteen_on$campground))-1,
## 2040 campground  - 0%%
(sum(forty_on$campground) / sum(fourteen_on$campground))-1,
## 2020 percentHouseSeasonal  - 0%%
(mean(twenty_on %>% filter(percentHouseSeasonal != 0) %>% pull(percentHouseSeasonal)) / mean(fourteen_on %>% filter(percentHouseSeasonal != 0) %>% pull(percentHouseSeasonal)))-1,
## 2040 percentHouseSeasonal  - 0%%
(mean(forty_on %>% filter(percentHouseSeasonal != 0) %>% pull(percentHouseSeasonal)) / mean(fourteen_on %>% filter(percentHouseSeasonal != 0) %>% pull(percentHouseSeasonal)))-1),
forecast_year=c(2020,2040,2020,2040,2020,2040),
forecast_value=c(sum(twenty_on$lodging_total),
                 sum(forty_on$lodging_total),
                 sum(twenty_on$campground),
                 sum(forty_on$campground),
                 mean(twenty_on %>% filter(percentHouseSeasonal != 0) %>% pull(percentHouseSeasonal)),
                 mean(forty_on %>% filter(percentHouseSeasonal != 0) %>% pull(percentHouseSeasonal))),
base_year=c(2014,2014,2014,2014,2014,2014),
base_value=c(sum(fourteen_on$lodging_total),
             sum(fourteen_on$lodging_total),
             sum(fourteen_on$campground),
             sum(fourteen_on$campground),
             mean(fourteen_on %>% filter(percentHouseSeasonal != 0) %>% pull(percentHouseSeasonal)),
             mean(fourteen_on %>% filter(percentHouseSeasonal != 0) %>% pull(percentHouseSeasonal))),
category=c("lodging unit ","lodging unit ","campground ","campground ","percentHouseSeasonal ","percentHouseSeasonal ")
)

# Overnight Visitor Rate Forecasts

fourteen_onr <- read_csv("H:/model/final_2014_RTP_scenarios/2014BaseRTP011516/2014BaseRTP011516/zonal/VisitorOccupancyRates_Summer.csv") %>%
  left_join(fourteen_on, by="taz") %>%
  rowwise() %>%
  mutate( hotelmotel_oc=hotelmotel.x*hotelmotel.y,
         resort_oc=resort.x*resort.y,
         casino_oc=casino.x*casino.y,
         occ_total=sum(c(casino_oc,resort_oc, hotelmotel_oc,na.rm=T )),
         occupied_campground= campground.x * campground.y)

twenty_onr <- read_csv("H:/model/final_2014_RTP_scenarios/RTP2020030116/RTP2020030116/zonal/VisitorOccupancyRates_Summer.csv") %>%
  rowwise() %>%
  mutate(lodging_av=mean(c(hotelmotel,resort,casino))) %>%
  left_join(twenty_on, by="taz") %>%
  rowwise() %>%
  mutate(occupied_lodging_units=lodging_av * lodging_total,
         occupied_campground= campground.x * campground.y)

forty_onr <- read_csv("H:/model/final_2014_RTP_scenarios/2040RTP/2040RTP/zonal/VisitorOccupancyRates_Summer.csv") %>%
  rowwise() %>%
  mutate(lodging_av=mean(c(hotelmotel,resort,casino))) %>%
  left_join(forty_on, by="taz") %>%
  rowwise() %>%
  mutate(occupied_lodging_units=lodging_av * lodging_total,
         occupied_campground= campground.x * campground.y)

ov_rate_change <- data.frame(change=c(
## 2020 lodging occupancy rate  - 22%%
  (sum(twenty_onr$occupied_lodging_units, na.rm=T)/ sum(twenty_onr$lodging_total, na.rm=T)) /
     (sum(fourteen_onr$occ_total, na.rm=T)/ sum(fourteen_onr$lodging_total, na.rm=T))-1,
## 2040 lodging occupancy rate  - 34%%
(sum(forty_onr$occupied_lodging_units, na.rm=T)/ sum(twenty_onr$lodging_total, na.rm=T)) /
   (sum(fourteen_onr$occ_total, na.rm=T)/ sum(fourteen_onr$lodging_total, na.rm=T))-1 ,
## 2020 campground.x occupancy rate  - 0%%
(sum(twenty_onr$occupied_campground, na.rm=T)/ sum(twenty_onr$campground.y, na.rm=T)) /
  (sum(fourteen_onr$occupied_campground, na.rm=T)/ sum(fourteen_onr$campground.y, na.rm=T))-1,
## 2040 campground.x occupancy rate  - 9%%
(sum(forty_onr$occupied_campground, na.rm=T)/ sum(forty_onr$campground.y, na.rm=T)) /
  (sum(fourteen_onr$occupied_campground, na.rm=T)/ sum(fourteen_onr$campground.y, na.rm=T))-1,
## 2020 house(VHR) rate  - 0%%
(mean(twenty_onr %>% filter(house !=0) %>% pull(house))/ mean(fourteen_onr %>% filter(house !=0) %>% pull(house)))-1,
## 2040 house(VHR) rate  - 16%%
(mean(forty_onr %>% filter(house !=0) %>% pull(house))/mean(fourteen_onr %>% filter(house !=0) %>% pull(house)))-1,
## 2020 seasonal rate  - 0%%
(mean(twenty_onr %>% filter(seasonal !=0) %>% pull(seasonal)) / mean(fourteen_onr %>% filter(seasonal !=0) %>% pull(seasonal)))-1,
## 2040 seasonal rate  - 16%%
(mean(forty_onr %>% filter(seasonal !=0) %>% pull(seasonal))/mean(fourteen_onr %>% filter(seasonal !=0) %>% pull(seasonal)))-1),
forecast_year=c(2020,2040,2020,2040,2020,2040,2020,2040),
forecast_value=c((sum(twenty_onr$occupied_lodging_units, na.rm=T)/ sum(twenty_onr$lodging_total, na.rm=T)),
                 (sum(forty_onr$occupied_lodging_units, na.rm=T)/ sum(twenty_onr$lodging_total, na.rm=T)),
                 mean(twenty_onr %>% filter(campground.x !=0) %>% pull(campground.x)),
                 mean(forty_onr %>% filter(campground.x !=0) %>% pull(campground.x)),
                 mean(twenty_onr %>% filter(house !=0) %>% pull(house)),
                 mean(forty_onr %>% filter(house !=0) %>% pull(house)),
                 mean(twenty_onr %>% filter(seasonal !=0) %>% pull(seasonal)),
                 mean(forty_onr %>% filter(seasonal !=0) %>% pull(seasonal))),
base_year=c(2014,2014,2014,2014,2014,2014,2014,2014),
base_value=c(sum(fourteen_onr$occ_total,na.rm=T)/sum(fourteen_onr$lodging_total, na.rm=T),
             sum(fourteen_onr$occ_total,na.rm=T)/sum(fourteen_onr$lodging_total, na.rm=T),
             mean(fourteen_onr %>% filter(campground.x !=0) %>% pull(campground.x)),
             mean(fourteen_onr %>% filter(campground.x !=0) %>% pull(campground.x)),
             mean(fourteen_onr %>% filter(house !=0) %>% pull(house)),
             mean(fourteen_onr %>% filter(house !=0) %>% pull(house)),
             mean(fourteen_onr %>% filter(seasonal !=0) %>% pull(seasonal)),
             mean(fourteen_onr %>% filter(seasonal !=0) %>% pull(seasonal))),
category=c("lodging occupancy rate ","lodging occupancy rate ","campground occupancy rate ","campground occupancy rate ","house(VHR) rate ","house(VHR) rate ","seasonal rate ","seasonal rate ")
)

all <- bind_rows(ov_rate_change, ov_unit_change, school_change, socio_change) %>%
  mutate(percent_growth=round(change,2), base_value=format(round(base_value,4), big.mark=","),
         forecast_value=format(round(forecast_value,4),big.mark=","),
         source="2017 RTP Model Inputs") %>% 
  select(-change) %>%
  select(category, base_year, base_value, forecast_year, forecast_value, percent_growth, source)

formattable(all)

write.csv(all,"H:/model/model_update_2019/data_inputs/final_inputs_2020_RTP/2017_RTP_Model_Input_Summary.csv")


data<-forty_socio %>%
  left_join(forty_on, by="taz") %>%
  select(taz, total_residential_units, emp_total, lodging_total) %>%
  rename(employees=emp_total) %>%
  mutate(source="2017 RTP - 2040 forecast")

write.csv(data,"F:/Research and Analysis/Transportation/RTP/2020RTP/Land_Use_Forecasts/data/2017_RTP_forecasts/2017_RTP_2040_Forecast.csv")

tmap_mode("view")

forty.sf<-
  taz %>%
  left_join( data %>%
  pivot_longer(cols=c("total_residential_units","employees","lodging_total"), names_to="category", values_to="values"),
  by=c("TAZ"="taz")
  )
  
forty.sf %>% tm_shape() + tm_polygons("values", palette = "RdYlBu") + tm_facets(nrow=3,by="category")




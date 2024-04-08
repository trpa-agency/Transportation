library(pacman)
p_load(tidyverse, sf, formattable, geojsonio)


# TAZ to TAZ comparison of 2014 to 2018 base years

fourteen_socio <- read_csv("H:/model/final_2014_RTP_scenarios/2014BaseRTP011516/2014BaseRTP011516/zonal/SocioEcon_Summer.csv") %>%
  rowwise() %>%
  mutate(emp_total=sum(c(emp_retail,emp_srvc,emp_game,emp_other, emp_rec)),
         unocc_units=total_residential_units - total_occ_units)
fourteen_school <- read_csv("H:/model/final_2014_RTP_scenarios/2014BaseRTP011516/2014BaseRTP011516/zonal/SchoolEnrollment.csv") %>%
  rowwise() %>%
  mutate(school_total=sum(c(elementary_school_enrollment,middle_school_enrollment,high_school_enrollment,college_enrollment)))
fourteen_on <- read_csv("H:/model/final_2014_RTP_scenarios/2014BaseRTP011516/2014BaseRTP011516/zonal/OvernightVisitorZonalData_Summer.csv") %>%
  rowwise() %>%
  mutate(lodging_total=sum(c(hotelmotel,resort,casino)))
fourteen_onr <- read_csv("H:/model/final_2014_RTP_scenarios/2014BaseRTP011516/2014BaseRTP011516/zonal/VisitorOccupancyRates_Summer.csv") %>%
  rowwise() %>%
  mutate(lodging_total=sum(c(hotelmotel,resort,casino)))

# block group

block_group<-geojson_read("https://opendata.arcgis.com/datasets/85a2e8e4bf994742a5855c1339517681_2.geojson", what="sp") %>% st_as_sf() %>% st_transform(4326)

#taz
taz<-st_read("model_taz","taz_sde")

# 2014 numbers

input14 <-read_csv("H:/model/model_update_2019/data_inputs/final_inputs_2020_RTP/2017_RTP_Model_Input_Summary.csv") %>%
  select(-X1) %>%
  pivot_wider(id_cols=c(category, base_year, base_value, source),names_from=forecast_year, values_from=forecast_value)

# school enrollment
school_taz<-read_csv("final_inputs_2020_RTP/school_enrollment.csv") %>%
  select(-X1) %>%
  rename(taz=TAZ, elementary_school_enrollment=elementary, middle_school_enrollment=middle, high_school_enrollment=high, college_enrollment=college)
school_taz<-taz %>% data.frame() %>% select(TAZ) %>%
  left_join(school_taz, by=c("TAZ"="taz")) %>%
  rename(taz=TAZ)
school_taz[is.na(school_taz)] = 0

## total school enrollment
school_total <- school_taz %>%
  rowwise() %>%
  mutate(school_total=sum(c(college, elementary, middle,high),na.rm=T))

sum(school_total$college)
sum(school_total$elementary)
sum(school_total$middle)
sum(school_total$high)

# TAZ school comparison

## there is 220 students in external TAZs not accounted for
school_comp<-fourteen_school %>% 
  left_join(school_total, by=c("taz"="TAZ")) %>%
  mutate(school_total.y = coalesce(school_total.y, 0),
         diff=abs(school_total.x-school_total.y)) %>%
  select(school_total.x, school_total.y, diff,everything())

tm_shape(taz %>% left_join(school_comp, by=c("TAZ"="taz"))) + tm_polygons(alpha=.3)

# campsites
campsites<-read_csv("final_inputs_2020_RTP/campsites.csv")

#campsite comparison

camp_comp <- fourteen_on %>% 
  left_join(campsites,by=c("taz"="TAZ")) %>%
  mutate(NUMBER_OF_SITES = coalesce(NUMBER_OF_SITES, 0),
         diff=abs(campground-NUMBER_OF_SITES)) %>%
  select(taz,campground,NUMBER_OF_SITES,diff)

## recreation attractiveness
rec<-read_csv("final_inputs_2020_RTP/rec_attractiveness.csv")

## employment
emp<-read_csv("final_inputs_2020_RTP/employment.csv") %>%
  rowwise() %>%
  mutate(emp_total=sum(c(emp_srvc, emp_retail, emp_rec, emp_other,emp_gaming),na.rm=T))
emp <- taz %>% 
  left_join(emp, by="TAZ")

emp %>% group_by(COUNTY) %>%
  summarise(total=sum(emp_total,na.rm=T))

## taus - units and occupancy
tau <- read_csv("final_inputs_2020_RTP/tau.csv") %>%
  rowwise() %>%
  mutate(tau_total=sum(c(hotelmotel.x,resort.x,casino.x),na.rm=T),
         tau_occ_total=round(sum(c(hotelmotel_oc,resort_oc,casino_oc),na.rm=T),0))

sum(tau$tau_occ_total,na.rm=T)
sum(tau$tau_total,na.rm=T)
round(sum(tau$resort_oc,na.rm=T),0)
round(sum(tau$hotelmotel_oc,na.rm=T),0)
round(sum(tau$casino_oc,na.rm=T),0)

## vhr occ
#
#vhr_occ<-write.csv("final_inputs_2020_RTP/vhr_occ.csv")

## residential file - includes occupancy, res units, VHRs, seasonal units

res_file <- read_csv("final_inputs_2020_RTP/res_unit_file.csv")

## percentHouseSeasonal

percentHouseSeasonal <- res_file %>% select(TAZ, percentHouseSeasonal)

# res income

inc<-read_csv('final_inputs_2020_RTP/res_income.csv') %>%
  select(TAZ, high_income_per, med_income_per, low_income_per)

# socioecon file
socio18<-taz %>% data.frame() %>% dplyr::select(TAZ) %>%
  left_join(res_file, by="TAZ") %>%
  left_join(emp, by="TAZ") %>%
  left_join(inc, by="TAZ") %>%
  mutate(occ_units_low_inc=round(occ_res_unit * low_income_per,10),
          occ_units_med_inc=round(occ_res_unit * med_income_per,10),
          occ_units_high_inc=round(occ_res_unit * high_income_per,10)) %>%
  dplyr::select(TAZ, census_occ_rate_new,occ_res_unit, unocc_res_unit,occ_units_low_inc,occ_units_med_inc,occ_units_high_inc,persons_per_occ_unit,persons,emp_other, emp_rec,emp_retail,emp_srvc, emp_gaming, emp_total ,percentHouseSeasonal) %>%
  rowwise() %>%
  mutate(emp_other=round(emp_other,0),
         emp_rec=round(emp_rec,0),
         emp_retail=round(emp_retail,0),
         emp_srvc=round(emp_srvc,0),
         emp_gaming=round(emp_gaming,0), 
         emp_total=round(emp_total,0),
         total_residential_units=sum(c(occ_res_unit,unocc_res_unit),na.rm=T)) %>%
  rename(taz=TAZ, total_occ_units=occ_res_unit, total_persons=persons,census_occ_rate=census_occ_rate_new) %>%
  dplyr::select(taz, total_residential_units,census_occ_rate,total_occ_units,occ_units_low_inc,occ_units_med_inc,occ_units_high_inc,persons_per_occ_unit, total_persons, emp_other, emp_rec,emp_retail,emp_srvc, emp_gaming, emp_total)
socio18[is.na(socio18)] = 0

write.csv(socio18, 'final_inputs_2020_RTP/socio.csv')

#population


# total res units
sum(res_file$occ_res_unit,na.rm=T) + sum(res_unit_file$unocc_res_unit,na.rm=T)

# occupied units
sum(res_file$occ_res_unit,na.rm=T)

# unoccupied units
sum(res_unit_file$unocc_res_unit,na.rm=T)

#VHR unoccupied units
sum(res_unit_file$VHR)

#seasonal unoccupied units
sum(res_unit_file$seas_unit_wo_vhr)

#other unoccupied units
sum(res_unit_file$other_unoccupied)

# persons per occ unit
round(sum(res_unit_file$persons,na.rm=T)/sum(res_unit_file$occ_res_unit, na.rm=T),2)

#occ rate
round(sum(res_unit_file$occ_res_unit,na.rm=T)/sum(res_unit_file$total_residential_units,na.rm=T),2)

## inputs summarized and compared to 2014
inputs<-input14 %>%
  mutate(RTP_20_base_year_2018=case_when(category=="low income res unit" ~ sum(socio18$occ_units_low_inc,na.rm=T),
                                  category=="medium income res unit" ~ sum(socio18$occ_units_med_inc,na.rm=T),
                                  category=="high income res unit" ~ sum(socio18$occ_units_high_inc,na.rm=T),
                                  category=="total persons" ~ sum(socio18$total_persons,na.rm=T),
                                  category=="total occupied unit" ~ sum(socio18$total_occ_units,na.rm=T),
                                  category=="residential unit" ~ round(sum(socio18$total_residential_units,na.rm=T),0),
                                  category=="school enrollment" ~ sum(school_total$school_total,na.rm=T),
                                  category=="census occupancy rate" ~ sum(socio18$occ_res_unit,na.rm=T)/sum(socio18$total_residential_units,na.rm=T),
                                  category=="campground" ~ sum(campsites$NUMBER_OF_SITES,na.rm=T),
                                  category=="persons per occupied unit" ~ sum(socio18$persons,na.rm=T)/sum(socio18$occ_res_unit,na.rm=T),
                                  category== "employment" ~ sum(emp$emp_total, na.rm=T),
                                  category== "lodging unit" ~ sum(tau$tau_total, na.rm=T),
                                  category== "lodging occupancy rate" ~ sum(tau$tau_occ_total,na.rm=T)/sum(tau$tau_total,na.rm=T),
                                  category== "house(VHR) rate" ~ sum(res_file$vhr_occupied,na.rm=T)/sum(res_file$VHR,na.rm=T),
                                  category== "seasonal rate" ~ sum(res_file$seas_occupied,na.rm=T)/ sum(res_file$seas_unit_wo_vhr,na.rm=T) )) %>%
  rename(RTP_17_base_year_2014=base_value, RTP_17_forecast_year_2020=`2020`, RTP_17_forecast_year_2040=`2040`) %>%
  select(category,RTP_20_base_year_2018, RTP_17_base_year_2014) %>%
  mutate_if(is.numeric, round, digits=2) 

write.csv(inputs, "H:/model/model_update_2019/data_inputs/final_inputs_2020_RTP/inputs_summarized.csv")


# overnight zonal

on<-taz %>% data.frame() %>% select(TAZ) %>%
  left_join(tau, by="TAZ") %>%
  left_join(campsites, by="TAZ") %>%
  left_join(rec, by="TAZ") %>%
  left_join(percentHouseSeasonal,by="TAZ") %>%
  select(TAZ,hotelmotel.x, resort.x, casino.x,NUMBER_OF_SITES,percentHouseSeasonal, beach) %>%
  rename(taz=TAZ,hotelmotel=hotelmotel.x, resort=resort.x, casino=casino.x, campground=NUMBER_OF_SITES)
on[is.na(on)] = 0

write.csv(on, "final_inputs_2020_RTP/overnight_zonal.csv")

# overnight occupancy rates

onr<-taz %>% data.frame() %>% select(TAZ) %>%
  left_join(
    res_file %>% select(TAZ, vhr_occ, seas_occ) %>% rename(seasonal=seas_occ, house=vhr_occ), by="TAZ") %>%
  left_join(tau, by="TAZ") %>%
  left_join(campsites, by="TAZ") %>%
  select(TAZ,hotelmotel.y, resort.y, casino.y, occ, house, seasonal) %>%
  rename(taz=TAZ, hotelmotel=hotelmotel.y, resort=resort.y, casino=casino.y, campground=occ )
onr[is.na(onr)] = 0

write.csv(onr, "final_inputs_2020_RTP/overnight_rates.csv")

# school enrollment

write.csv(school_taz, "final_inputs_2020_RTP/school.csv")

## compare socio files
comp_socio<-bind_cols(
socio18 %>%
  select(taz, total_residential_units, census_occ_rate, total_occ_units, persons_per_occ_unit, total_persons),
fourteen_socio %>%
  select(taz, total_residential_units, census_occ_rate, total_occ_units, persons_per_occ_unit, total_persons)) %>%
  mutate(occ_unit_diff=total_occ_units-total_occ_units1,
         occ_rate_diff=census_occ_rate-census_occ_rate1)

## taz to taz comparison

socio18 <- read_csv('final_inputs_2020_RTP/socio.csv')
onr18 <- read_csv("final_inputs_2020_RTP/overnight_rates.csv")
on18 <- read_csv("final_inputs_2020_RTP/overnight_zonal.csv")
school18 <- read_csv("final_inputs_2020_RTP/school.csv")


school_comp <- school18 %>%
  replace(., is.na(.), 0) %>%
  left_join(fourteen_school, by="taz") %>%
  mutate(college_diff=abs(college_enrollment.x-college_enrollment.y),
         elementary_diff=abs(elementary_school_enrollment.x-elementary_school_enrollment.y),
         middle_diff=abs(middle_school_enrollment.x-middle_school_enrollment.y),
         high_diff=abs(high_school_enrollment.x-high_school_enrollment.y))
  

socio_comp <- socio18 %>%
  replace(., is.na(.), 0) %>%
  left_join(fourteen_socio, by="taz") %>%
  mutate(res_unit_diff=abs(total_residential_units.x-total_residential_units.y),
         occ_unit_diff=abs(total_occ_units.x-total_occ_units.y),
         low_income_diff=abs(occ_units_low_inc.x-occ_units_low_inc.y),
         med_income_diff=abs(occ_units_low_inc.x-occ_units_low_inc.y),
         high_income_diff=abs(occ_units_high_inc.x-occ_units_high_inc.y),
         emp_other_diff=abs(emp_other.x-emp_other.y),
         emp_rec_diff=abs(emp_rec.x-emp_rec.y),
         emp_retail_diff=abs(emp_retail.x-emp_retail.y),
         emp_srvc_diff=abs(emp_srvc.x-emp_srvc.y),
         emp_gaming_diff=abs(emp_gaming-emp_game))

on_comp <- on18 %>%
  replace(., is.na(.), 0) %>%
  left_join(fourteen_on, by="taz") %>%
  mutate(hotelmotel_diff=abs(hotelmotel.x-hotelmotel.y),
         resort_diff=abs(resort.x-resort.y),
         casino_diff=abs(casino.x-casino.y),
         campground_diff=abs(campground.x-campground.y),
         percentHouseSeasonal_diff=percentHouseSeasonal.x-percentHouseSeasonal.y)

onr_comp <- onr18 %>%
  replace(., is.na(.), 0) %>%
  left_join(fourteen_onr, by="taz") %>%
  mutate(hotelmotel_rate_diff=abs(hotelmotel.x-hotelmotel.y),
         resort_rate_diff=abs(resort.x-resort.y),
         casino_rate_diff=abs(casino.x-casino.y),
         campground_rate_diff=abs(campground.x-campground.y),
         house_rate_diff=abs(house.x-house.y),
         seasonal_rate_diff=abs(seasonal.x-seasonal.y))

## dev rights base year TAZ 

base<-socio18 %>%
  left_join(on, by="taz") %>%
  rowwise() %>%
  mutate(lodging_total=sum(hotelmotel,resort,casino)) %>%
  select(taz, total_residential_units, emp_total, lodging_total) %>%
  rename(employees=emp_total) %>%
  mutate(source="2020 RTP - 2018 base year")

tmap_mode("view")

base.sf<-
  taz %>%
  left_join( base %>%
               pivot_longer(cols=c("total_residential_units","employees","lodging_total"), names_to="category", values_to="values"),
             by=c("TAZ"="taz")
  )

base.sf %>% tm_shape() + tm_polygons("values", palette = "RdYlBu") + tm_facets(nrow=3,by="category")



library(pacman)
p_load(tidycensus, tidyverse,leaflet, geojsonio, sf, tmap, tmaptools, DT, xfun)
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
#Brings in 2017 ACS data?
acs_var <- load_variables(2017, "acs5", cache = TRUE)

var <- data.frame(variable=c("B19001_002","B19001_003","B19001_004","B19001_005","B19001_006","B19001_007","B19001_008","B19001_009", "B19001_010","B19001_011","B19001_012","B19001_013","B19001_014","B19001_015","B19001_016","B19001_017"), 
                  name=c("Estimate!!Total!!Less than $10 000","Estimate!!Total!!$10 000 to $14 999","Estimate!!Total!!$15 000 to $19 999","Estimate!!Total!!$20 000 to $24 999","Estimate!!Total!!$25 000 to $29 999","Estimate!!Total!!$30 000 to $34 999","Estimate!!Total!!$35 000 to $39 999","Estimate!!Total!!$40 000 to $44 999","Estimate!!Total!!$45 000 to $49 999","Estimate!!Total!!$50 000 to $59 999","Estimate!!Total!!$60 000 to $74 999","Estimate!!Total!!$75 000 to $99 999","Estimate!!Total!!$100 000 to $124 999","Estimate!!Total!!$125 000 to $149 99","Estimate!!Total!!$150 000 to $199 999","Estimate!!Total!!$200 000 or more"))


dg_acs <- get_acs(geography = "block group", year=2017, 
                  variables =  c("B19001_002","B19001_003","B19001_004","B19001_005","B19001_006","B19001_007","B19001_008","B19001_009", "B19001_010","B19001_011","B19001_012","B19001_013","B19001_014","B19001_015","B19001_016","B19001_017"), state = "NV", county="Douglas", geometry = T) %>%
  mutate(county="douglas")
wa_acs <- get_acs(geography = "block group", year=2017, 
                  variables =  c("B19001_002","B19001_003","B19001_004","B19001_005","B19001_006","B19001_007","B19001_008","B19001_009", "B19001_010","B19001_011","B19001_012","B19001_013","B19001_014","B19001_015","B19001_016","B19001_017"),
                  state = "NV", county="Washoe", geometry = T) %>%
  mutate(county="washoe")
pla_acs <- get_acs(geography = "block group", year=2017, 
                   variables =  c("B19001_002","B19001_003","B19001_004","B19001_005","B19001_006","B19001_007","B19001_008","B19001_009", "B19001_010","B19001_011","B19001_012","B19001_013","B19001_014","B19001_015","B19001_016","B19001_017"),
                   state = "CA",county="Placer", geometry = T) %>%
  mutate(county="placer")
ed_acs <- get_acs(geography = "block group", year=2017, 
                  variables =  c("B19001_002","B19001_003","B19001_004","B19001_005","B19001_006","B19001_007","B19001_008","B19001_009", "B19001_010","B19001_011","B19001_012","B19001_013","B19001_014","B19001_015","B19001_016","B19001_017"),
                  state = "CA",county="El Dorado", geometry = T) %>%
  mutate(county="el dorado")

#Adding up the income categories by block group
all<- rbind(dg_acs, wa_acs, pla_acs, ed_acs) %>%
  left_join(data.frame(block_group), by="GEOID") %>%
  filter(!is.na(NAME.y)) %>%
  left_join(var, by="variable") %>%
  select(name, GEOID, variable, estimate, moe) %>%
  mutate(income_category=case_when(name %in% c("Estimate!!Total!!Less than $10 000","Estimate!!Total!!$10 000 to $14 999","Estimate!!Total!!$15 000 to $19 999","Estimate!!Total!!$20 000 to $24 999","Estimate!!Total!!$25 000 to $29 999","Estimate!!Total!!$30 000 to $34 999","Estimate!!Total!!$35 000 to $39 999","Estimate!!Total!!$40 000 to $44 999","Estimate!!Total!!$45 000 to $49 999","Estimate!!Total!!$50 000 to $59 999") ~ "low income",
                                   name %in% c("Estimate!!Total!!$60 000 to $74 999","Estimate!!Total!!$75 000 to $99 999") ~ "medium income",
                                   name %in% c("Estimate!!Total!!$100 000 to $124 999","Estimate!!Total!!$125 000 to $149 99","Estimate!!Total!!$150 000 to $199 999","Estimate!!Total!!$200 000 or more") ~ "high income",
                                   )) %>%
  group_by(GEOID, income_category) %>% summarise(estimate=sum(estimate,na.rm=T))

income<-all %>%
  group_by(GEOID, income_category) %>%
  summarise (n = sum(estimate)) %>%
  spread(income_category, n) %>%
st_transform(crs=4326)
  #mutate(freq = n / sum(n)) %>%
 # st_transform(crs=st_crs(taz))
#Join the income data to the TAZs based on the largest overlap
income_taz<-st_join(st_buffer(taz %>% select(TAZ),0), st_buffer(income,0), largest=TRUE)
colnames(income_taz) <- c("TAZ", "TAZ1","GEOID", "high income", "low income", "medium income","geometry")
income_taz <- income_taz %>%
  rowwise() %>%
  mutate(total_res=sum(c(`low income`, `high income` ,`medium income`)),
         high_income_per=`high income`/total_res,
         med_income_per=`medium income`/total_res,
         low_income_per=`low income`/total_res) %>%
  data.frame() %>%
  select(-c(geometry,TAZ1))

write.csv(income_taz,'H:/model/model_update_2019/data_inputs/final_inputs_2020_RTP/res_income.csv')


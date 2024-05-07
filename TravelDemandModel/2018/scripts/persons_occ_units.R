library(pacman)
p_load(tidycensus, sf, tidyverse, geojsonio)

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

dg_acs <- get_acs(geography = "block group", year=2017, 
                  variables =  "B25010_001",
                  state = "NV", county="Douglas", geometry = T)
wa_acs <- get_acs(geography = "block group", year=2017, 
                  variables =  "B25010_001",
                  state = "NV", county="Washoe", geometry = T)
pla_acs <- get_acs(geography = "block group", year=2017, 
                   variables =  "B25010_001",
                   state = "CA",county="Placer", geometry = T)
ed_acs <- get_acs(geography = "block group", year=2017, 
                  variables =  "B25010_001",
                  state = "CA",county="El Dorado", geometry = T)

all<- rbind(dg_acs, wa_acs, pla_acs, ed_acs) %>%
  left_join(data.frame(block_group), by="GEOID") %>%
  filter(!is.na(STATEFP)) %>%
  mutate(variable_name = case_when (variable== "B25010_001" ~ "Average HH Size of Occupied Units")) %>%
  st_transform(crs=4326) %>%
  select(variable, estimate, GEOID)

hh_size <- st_join(st_buffer(taz,0), st_buffer(all,0), largest=TRUE) %>%
  data.frame() %>%
  select(TAZ, estimate) %>%
  rename(persons_per_occ_unit=estimate) %>%
  mutate(persons_per_occ_unit=persons_per_occ_unit * 1.0173913) ## increase the household size by a factor to reach 2.3 regionally

write.csv(hh_size, "final_inputs_2020_RTP/pers_per_occ_unit.csv")






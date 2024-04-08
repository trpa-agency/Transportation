library(pacman)
p_load(tidycensus, tidyverse,leaflet, geojsonio, sf, tmap, tmaptools, DT, xfun, readxl,ggmap)
census_api_key("680398dff0a2f4c566f10c95888da7f25e55147b")
options(tigris_use_cache = TRUE)

# naics codes
naics<-read_excel("employment/6-digit_2017_Codes.xlsx", sheet="2017_6-digit_industries")

# 2014 model socio
fourteen_socio <- read_csv("H:/model/final_2014_RTP_scenarios/2014BaseRTP011516/2014BaseRTP011516/zonal/SocioEcon_Summer.csv") %>%
  rowwise() %>%
  mutate(emp_total=sum(c(emp_retail,emp_srvc,emp_game,emp_other, emp_rec)))

# google key
register_google(key="AIzaSyA3lBYiTffOPFATH9Brv0eJ0IR6DgXK5tY")

#county
county <- geojson_read("https://opendata.arcgis.com/datasets/85a2e8e4bf994742a5855c1339517681_16.geojson", what='sp') %>% st_as_sf() %>% st_transform(4326) %>%
  st_cast("MULTIPOLYGON")

# census geometries
block<-geojson_read("https://opendata.arcgis.com/datasets/85a2e8e4bf994742a5855c1339517681_1.geojson", what="sp") %>% st_as_sf() %>% st_transform(4326)

block <- st_join(st_buffer(block,0), st_buffer(county,0), largest=TRUE) %>%
  select(GEOID, COUNTY)
tract <- geojson_read("https://opendata.arcgis.com/datasets/85a2e8e4bf994742a5855c1339517681_3.geojson", what="sp") %>%
  st_as_sf() %>% st_transform(4326)

# TAZ
taz<-st_read("model_taz","taz_sde") %>%
  st_transform(crs=4326) %>%
  st_cast("MULTIPOLYGON")

# Nevada 2018
options(scipen=999)
detr_block<-read_csv("employment/Nevada_DETR/Area and Industry by Census Block.csv")
detr_tract<-read_csv("employment/Nevada_DETR/Area and Industry by Census Tract.csv")


detr_tract %>% mutate(av_emp_per_employer=round(Average_Employment/Number_Employers,0)) %>% 
  ungroup() %>%
  mutate(av_emp_per_employer=as.numeric(av_emp_per_employer)) %>%
  ggplot(aes(av_emp_per_employer,Number_Employers)) + geom_col() +
  scale_x_continuous(breaks=c(0,10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180,190),
                     labels=c(0,10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180,190)) + 
  theme_minimal() + xlab("Average Employees Per Employer (Per Census Tract)") + ylab("Number of Employers") + ggtitle("Nevada - Number of Employers by Average Number of Employees")

ggsave("Nevada_Employment.png",height=6, width=10)

write.csv(
detr_tract %>% mutate(av_emp_per_employer=round(Average_Employment/Number_Employers,0)) %>% 
  ungroup() %>%
  mutate(av_emp_per_employer=as.numeric(av_emp_per_employer)) %>%
  select(av_emp_per_employer,Number_Employers), "Nevada_Employment.csv"
)

detr_tract_clean<-detr_tract %>%
  mutate(Census_Tract=as.factor(Census_Tract)) %>%
  left_join(tract, by=c("Census_Tract"="GEOID")) %>%
  st_as_sf()

test<-detr_block %>%
  mutate(Census_Block=as.factor(Census_Block)) %>%
  left_join(block, by=c("Census_Block"="GEOID")) %>%
  st_as_sf()

detr_tract_taz<-st_join(st_buffer(detr_tract_clean,0), st_buffer(taz,0), largest=TRUE)

detr_tract_clean<-detr_tract %>%
  rowwise() %>%
  mutate(Census_Tract=as.factor(Census_Tract), emp_q3_q2_av= mean(c(Total_Employment_Q2,Total_Employment_Q3)),
         category=case_when(Industry %in% c("Retail Trade") ~ "emp_retail",
                            Industry %in% c("Accommodation and Food Services","Other Services, Except Public Administration") ~ "emp_srvc",
                            Industry %in% c("Arts, Entertainment, and Recreation") ~ "emp_rec",
                            Industry %in% c("") ~ "emp_game",
                            TRUE ~ as.character("emp_other"))) %>%
  select(Census_Tract, category, emp_q3_q2_av) %>%
  group_by(Census_Tract, category) %>% summarise(emp_q3_q2_av=sum(emp_q3_q2_av)) %>%
  spread(category, emp_q3_q2_av) %>%
  left_join(tract, by=c("Census_Tract"="GEOID")) %>%
  st_as_sf() %>%
  select(-c(16:24)) %>%
  select(Census_Tract, emp_other, emp_rec, emp_retail, emp_srvc)

detr_block_taz<-st_join(st_buffer(taz %>% select(TAZ),0), st_buffer(detr_tract_clean,0), largest=TRUE) %>%
  select(1,5,6,7,8)

colnames(detr_block_taz) <- c("TAZ","emp_other", "emp_rec", "emp_retail", "emp_srvc","geometry")

detr_block_final<-detr_block_taz %>% filter(!is.na(emp_other) | !is.na(emp_rec) | !is.na(emp_retail) | !is.na(emp_srvc)) %>% data.frame() %>%
  rowwise() %>%
  mutate(emp_total=sum(c(emp_other, emp_rec, emp_retail, emp_srvc), na.rm=T))

## 2018 estimate

nv_emp_est<-st_join(st_buffer(taz,0), st_buffer(county,0), largest=T) %>%
  left_join(fourteen_socio %>% select(-c(2:9)), by=c("TAZ"="taz")) %>%
  filter(COUNTY %in% c("DOUGLAS", "CARSON","WASHOE")) %>%
  mutate(nv_emp_14=sum(emp_total,na.rm=T)) %>%
  mutate(nv_emp_18=round(mean(c(10750,11465)),0)) %>% # include an average of the totals from Dave Schmit
  mutate(emp_retail_per14=emp_retail/nv_emp_14,
         emp_srvc_per14=emp_srvc/nv_emp_14,
         emp_game_per14=emp_game/nv_emp_14,
         emp_rec_per14=emp_rec/nv_emp_14,
         emp_other_per14=emp_other/nv_emp_14,
         emp_retail_18=emp_retail_per14 * nv_emp_18,
         emp_srvc_18=emp_srvc_per14 * nv_emp_18,
         emp_game_18=emp_game_per14 * nv_emp_18,
         emp_rec_18=emp_rec_per14 * nv_emp_18,
         emp_other_18=emp_other_per14 * nv_emp_18) %>% data.frame() %>%
         select(c(6,31:35)) %>%
  rename(emp_retail=emp_retail_18,
         emp_srvc=emp_srvc_18,
         emp_rec=emp_rec_18,
         emp_other=emp_other_18,
         emp_gaming=emp_game_18)

# California EDD

q2<- read_xls("H:/SFT_Restricted/TRPA_2018-2.xls", sheet = "2018-2") %>%
  rowwise() %>%
  mutate(id=paste(NAICSCODE, LEGAL_NAME,PHYSICAL_STREET,LATITUDE, LONGITUDE,PHYSICAL_ZIP, TRADE_NAME, OWNERSHIPCODE, sep=","), 
  max_emp=max(c(EMPMONTH1,EMPMONTH2,EMPMONTH3)))
  
q3<- read_xls("H:/SFT_Restricted/TRPA_2018-3.xls", sheet = "2018-3")%>%
  rowwise() %>%
  mutate(id=paste(NAICSCODE, LEGAL_NAME,PHYSICAL_STREET,LATITUDE, LONGITUDE,PHYSICAL_ZIP, TRADE_NAME, OWNERSHIPCODE, sep=","), 
         max_emp=max(c(EMPMONTH1,EMPMONTH2,EMPMONTH3)))

q1<- read_xls("H:/SFT_Restricted/TRPA_2018-1.xls", sheet = "2018-1")%>%
  rowwise() %>%
  mutate(id=paste(NAICSCODE, LEGAL_NAME,PHYSICAL_STREET,LATITUDE, LONGITUDE,PHYSICAL_ZIP, TRADE_NAME, OWNERSHIPCODE, sep=","), 
         max_emp=max(c(EMPMONTH1,EMPMONTH2,EMPMONTH3)))

q4<- read_xls("H:/SFT_Restricted/TRPA_2018-4.xls", sheet = "2018-4")%>%
  rowwise() %>% 
  mutate(id=paste(NAICSCODE, LEGAL_NAME,PHYSICAL_STREET,LATITUDE, LONGITUDE,PHYSICAL_ZIP, TRADE_NAME, OWNERSHIPCODE, sep=","), 
         max_emp=max(c(EMPMONTH1,EMPMONTH2,EMPMONTH3)))

EDD<-q3 %>% left_join(q2, by="id") %>%
  na_if(0) %>%
  rowwise() %>%
  st_as_sf(coords=c("LONGITUDE.x","LATITUDE.x"), crs = 4326) %>%
  select(LEGAL_NAME.x,EMPMONTH2.x,EMPMONTH3.x,EMPMONTH3.y,PHYSICAL_STREET.x, PHYSICAL_CITY.x, PHYSICAL_STATE.x, PHYSICAL_ZIP.x,NAICSCODE.x)

EDD1<-q3 %>% left_join(q2, by="id") %>%
  left_join(q1, by="id") %>%
  left_join(q4, by="id") %>%
  na_if(0) %>%
  rowwise() %>%
  st_as_sf(coords=c("LONGITUDE.x","LATITUDE.x"), crs = 4326) %>%
  mutate(average_monthly_emp=mean(c(EMPMONTH1.x,EMPMONTH2.x,EMPMONTH3.x,EMPMONTH1.y,EMPMONTH2.y,EMPMONTH3.y,EMPMONTH1.x.x,EMPMONTH2.x.x,EMPMONTH3.x.x,EMPMONTH1.y.y,EMPMONTH2.y.y,EMPMONTH3.y.y),na.rm=T))


write.csv(EDD1 %>%
  count(average_monthly_emp) %>%
  data.frame() %>%
  select(1,2), "california_employment.csv"
)
  
EDD1 %>%
  ggplot(aes(average_monthly_emp)) + geom_histogram(binwidth=5) +
  scale_x_continuous(labels=c(0,50,100,150,200,250,300,350,400,450,500,550,600,650,700),
                     breaks=c(0,50,100,150,200,250,300,350,400,450,500,550,600,650,700)) +
  scale_y_continuous(labels=c(0,50,100,150,200,250,300,350,400,450,500,550,600),
                     breaks=c(0,50,100,150,200,250,300,350,400,450,500,550,600)) +
  theme_minimal() +
  xlab("Average Monthly # of Employees") + ylab("# of Employers/Businesses")+
  ggtitle("California - Number of Employers by Average Monthly Employees")

ggsave("California_Employment.png",height=6, width=10)

employ_EDD <- st_join(EDD, st_buffer(taz,0), largest=TRUE) 

EDD_NA<-employ_EDD %>% filter(is.na(TAZ)) %>%
  mutate(Address_Full=paste(PHYSICAL_STREET.x, PHYSICAL_CITY.x, PHYSICAL_STATE.x, PHYSICAL_ZIP.x, sep=" ")) %>%
  mutate(Address_Full=case_when(Address_Full=="1700 RIVER ROAD #B TAHOE CITY CA 96145" ~ "1700 RIVER ROAD TAHOE CITY CA 96145", 
                                Address_Full=="1730 HWY 89 SUITE 70 & 80 TAHOE CITY CA 96145" ~ "1730 River Road TAHOE CITY CA 96145", 
                                Address_Full=="1730 RIVER ROAD SUITE #202 TAHOE CITY CA 96145" ~ "1730 River Road TAHOE CITY CA 96145", 
                                Address_Full=="700 RIVER ROAD #F TAHOE CITY CA 96145" ~ "700 RIVER ROAD TAHOE CITY CA 96145", 
                                Address_Full=="1700 HWY 89 STE C TAHOE CITY CA 96145" ~ "1700 RIVER ROAD TAHOE CITY CA 96145",
                                TRUE ~ as.character(Address_Full)))

EDD_NA_fixed<-geocode(EDD_NA$Address_Full, output="more")

EDD_missing<-bind_cols(EDD_NA, EDD_NA_fixed) %>%
  filter(!is.na(lon)) %>% data.frame() %>%
  st_as_sf(coords=c("lon","lat"), crs = 4326)

EDD_missing_final<-st_join(EDD_missing, st_buffer(taz,0), largest=TRUE) %>% filter(!is.na(TAZ.y)) %>%
  select(TAZ.y,EMPMONTH2.x,EMPMONTH3.x,EMPMONTH3.y,LEGAL_NAME.x,NAICSCODE.x) %>%
  rename(TAZ=TAZ.y)
EDD_not_missing<-employ_EDD %>% filter(!is.na(TAZ)) %>%
  select(TAZ,EMPMONTH2.x,EMPMONTH3.x,EMPMONTH3.y,LEGAL_NAME.x,NAICSCODE.x)

EDD_final<-bind_rows(EDD_missing_final, EDD_not_missing) %>% 
  rowwise() %>%
  mutate(employees=mean(c(EMPMONTH2.x,EMPMONTH3.x,EMPMONTH3.y), na.rm=T)) %>%
  filter(employees != "NaN") %>% data.frame() %>%
  select(TAZ, employees,NAICSCODE.x, LEGAL_NAME.x) %>%
  mutate(source="EDD",NAICSCODE.x=as.numeric(NAICSCODE.x) ) %>%
  left_join(naics, by=c("NAICSCODE.x"="2017 NAICS Code")) %>%
  select(-c(`...3`)) %>%
  mutate(naics_type=case_when(is.na(`2017 NAICS Title`) ~ "Other", 
                              TRUE ~as.character(`2017 NAICS Title`)),
         model_emp_type= case_when(naics_type %in% c("All Other Miscellaneous Store Retailers (except Tobacco Stores)",
                                                     "All Other Specialty Food Stores",
                                                     "Art Dealers",
                                                     "Automotive Parts and Accessories Stores",
                                                     "Automotive Glass Replacement Shops",
                                                     "Beer, Wine, and Liquor Stores",
                                                     "Boat Dealers",
                                                     "Book Stores",
                                                     "Book, Periodical, and Newspaper Merchant Wholesalers",
                                                     "Children's and Infants' Clothing Stores",
                                                     "Clothing Accessories Stores",
                                                     "Commercial Printing (except Screen and Books)",
                                                     "Convenience Stores",
                                                     "Cosmetics, Beauty Supplies, and Perfume Stores",
                                                     "Dairy Product (except Dried or Canned) Merchant Wholesalers",
                                                     "Department Stores",
                                                     "Drugs and Druggists' Sundries Merchant Wholesalers",
                                                     "Electrical Apparatus and Equipment, Wiring Supplies, and Related Equipment Merchant Wholesalers",
                                                     "Electronics Stores",
                                                     "Family Clothing Stores",
                                                     "Floor Covering Stores",
                                                     "Florists",
                                                     "Furniture Stores",
                                                     "Gasoline Stations with Convenience Stores",
                                                     "Gift, Novelty, and Souvenir Stores",
                                                     "Hardware Stores",
                                                     "Hobby, Toy, and Game Stores",
                                                     "Industrial Machinery and Equipment Merchant Wholesalers",
                                                     "Jewelry Stores",
                                                     "Jewelry, Watch, Precious Stone, and Precious Metal Merchant Wholesalers",   
                                                     "Locksmiths",
                                                     "Meat Markets",
                                                     "New Car Dealers",
                                                     "Nursery, Garden Center, and Farm Supply Stores" ,
                                                     "Optical Goods Stores",
                                                     "Outdoor Power Equipment Stores",
                                                     "Other Clothing Stores",
                                                     "Other Gasoline Stations",
                                                     "Other Grocery and Related Products Merchant Wholesalers"  ,
                                                     "Other Electronic Parts and Equipment Merchant Wholesalers",
                                                     "Other Miscellaneous Nondurable Goods Merchant Wholesalers",
                                                     "Paint and Wallpaper Stores",
                                                     "Pet and Pet Supplies Stores",
                                                     "Pharmacies and Drug Stores",
                                                     "Plumbing and Heating Equipment and Supplies (Hydronics) Merchant Wholesalers",
                                                     "Retail Bakeries",
                                                     "Shoe Stores",
                                                     "Sporting and Recreational Goods and Supplies Merchant Wholesalers",
                                                     "Sporting Goods Stores",
                                                     "Supermarkets and Other Grocery (except Convenience) Stores",
                                                     "Support Activities for Printing",
                                                     "Tire Dealers",
                                                     "Tobacco Stores",
                                                     "Used Car Dealers" ,
                                                     "Used Merchandise Stores",
                                                     "Window Treatment Stores",
                                                     "Women's Clothing Stores" ) ~ "emp_retail",
                                   naics_type %in% c("Bed-and-Breakfast Inns",
                                                     "Breweries",
                                                     "Car Washes",
                                                     "Coin-Operated Laundries and Drycleaners",
                                                     "Commercial Bakeries",
                                                     "Distilleries",
                                                     "Drinking Places (Alcoholic Beverages)",
                                                     "Full-Service Restaurants",
                                                     "Hotels (except Casino Hotels) and Motels",
                                                     "Linen Supply",
                                                     "Limousine Service",
                                                     "Limited-Service Restaurants",
                                                     "Nail Salons",
                                                     "Snack and Nonalcoholic Beverage Bars",
                                                     "Food Service Contractors") ~ "emp_srvc",
                                   naics_type %in% c("All Other Amusement and Recreation Industries",
                                                     "Convention and Visitors Bureaus",
                                                     "Fitness and Recreational Sports Centers",
                                                     "Golf Courses and Country Clubs",
                                                     "Marinas",
                                                     "Motion Picture Theaters (except Drive-Ins)",
                                                     "Nature Parks and Other Similar Institutions" ,
                                                     "Recreational and Vacation Camps (except Campgrounds)", 
                                                     "Museums",
                                                     "Recreational Goods Rental",
                                                     "Scenic and Sightseeing Transportation, Other",
                                                     "Scenic and Sightseeing Transportation, Water",
                                                     "Skiing Facilities",
                                                     "Sports and Recreation Instruction",
                                                     "Tour Operators",
                                                     "Promoters of Performing Arts, Sports, and Similar Events with Facilities",
                                                     "Inland Water Passenger Transportation") ~ "emp_rec",
                                   naics_type %in% c() ~ "emp_game",
                                   TRUE ~ as.character("emp_other")),
         TAZ=case_when(LEGAL_NAME.x=="AMERICANA VACATION CLUB" ~ 15,
                       LEGAL_NAME.x %in% c("ALOHA ICE CREAM","SATO JAPANESE RESTAURANT") ~ 21,
                       LEGAL_NAME.x=="ACROPOLIS HOTELS & RESORTS" ~ 20,
                       LEGAL_NAME.x %in% c("JOSHUA MARK DAVIS","SIERRA SERVICES") ~ 30,
                       LEGAL_NAME.x=="LOUIS BARNAS" ~ 33,
                       LEGAL_NAME.x %in% c('VALLEJO & SONS PAINTING',"ALOHA BOOKKEEPING COMPANY") ~ 51,
                       LEGAL_NAME.x %in% c("MISSION AJUSTERS","ED COOK CRANE SERVICE") ~ 66,
                       LEGAL_NAME.x=="HANDYMAN HOTLINE INC" ~ 69,
                       LEGAL_NAME.x=="A & P LANDSCAPE MAINTENANCE" ~ 71,
                       LEGAL_NAME.x=="W.D.H LAND SURVEYING" ~ 71,
                       LEGAL_NAME.x=="MING YII KONG" ~ 78,
                       LEGAL_NAME.x %in% c("STMICROELECTRONICS, INC.","MARK D KLOVER CPA") ~ 82,
                       LEGAL_NAME.x %in% c("ROLLING FRITO-LAY SALES, LP","GB SCIENTIFIC INC") ~ 83,
                       LEGAL_NAME.x %in%c("MOUNTAIN VIEW DAY CARE","ALL SEASONS PLUMBING") ~ 90,
                       LEGAL_NAME.x=="CALIFORNIA SPORTS ACCESSORIES" ~ 91,
                       LEGAL_NAME.x %in%c("MYI EQUIPMENT INC.","JOHNNY'S GARDEN") ~ 94,
                       LEGAL_NAME.x %in% c("F. JONES MOBILE DIESEL REPAIR","FRANKIE N JONES") ~ 98,
                       LEGAL_NAME.x %in% c("CARO CONSTRUCTION","TAHOE CERTIFIED HOME INSPECTIONS, I","FALLEN LEAF MUTUAL WATER CO") ~ 102,
                       LEGAL_NAME.x %in% c("TAHOE OUTDOOR LIVING","RD MCINTYRE CONSTRUCTION","ASPEN HOLLOW") ~ 103,
                       LEGAL_NAME.x=="SHES SUCH A LADY LLC" ~ 124,
                       LEGAL_NAME.x=="MEEKS BAY FIRE PROTECTION DISTRICT" ~ 129,
                       LEGAL_NAME.x=="DURKIN TREE SERVICE INC." ~ 132,
                       LEGAL_NAME.x=="MATTHEW LEE CONSTRUCTION" ~ 134,
                       LEGAL_NAME.x %in% c("RB WATERFRONTS LLC","BIENATI CONSULTING GROUP, INC.") ~ 136,
                       LEGAL_NAME.x=="HOMEWOOD OPERATIONS MANAGEMENT, LLC" ~ 139,
                       LEGAL_NAME.x %in% c("DENNIS L SCHLUMPF & ASSOC","SIERRA WATERSHED EDUCATION PARTNERS") ~ 141,
                       LEGAL_NAME.x=="SUNNYSIDE MARINA INC" ~149,
                       LEGAL_NAME.x=="GRANLIBAKKEN MANAGEMENT COMPANY, LT"~ 153,
                       LEGAL_NAME.x=="SAFEWAY STORES INC" ~ 156,
                       LEGAL_NAME.x=="BASILE MANAGEMENT PRACTICE, LLC" ~ 168,
                       LEGAL_NAME.x=="PAYCHEX PEO V LLC" ~ 160,
                       LEGAL_NAME.x=="SUMMIT ICE MELT SYSTEMS, INC."~ 167,
                       LEGAL_NAME.x=="SIERRA BOAT CO., INC." ~ 176,
                       LEGAL_NAME.x=="HUNTER METAL" ~ 180,
                       LEGAL_NAME.x=="NORTH TAHOE WATERSPORTS, INC." ~ 190,
                       LEGAL_NAME.x=="MARRIOTT RESORTS HOSP CORP" ~ 17,
                       TRUE ~ as.numeric(TAZ))) 

emp_ca_taz18 <- EDD_final %>%
group_by(TAZ) %>% 
  mutate(employees_taz=sum(employees,na.rm=T), n_firms=n_distinct(LEGAL_NAME.x), percent=employees/employees_taz)

emp_ca_taz18 %>% filter(n_firms < 3) %>% filter(percent > .8) %>% View()


%>%
  pivot_wider(names_from="model_emp_type", values_from="employees_taz") 

%>%
  summarise(total_taz_emp=sum(employees, na.rm=T), n_firms=n_distinct(LEGAL_NAME.x)) 
  

## 2018 final employment
employ_all <- bind_rows(emp_ca_taz18, nv_emp_est)

write.csv(employ_all, "final_inputs_2020_RTP/employment.csv")


## 2018 estimate

ca_emp_est<-st_join(st_buffer(taz,0), st_buffer(county,0)) %>%
  left_join(fourteen_socio %>% select(-c(2:9)), by=c("TAZ"="taz")) %>%
  filter(COUNTY %in% c("EL DORADO", "PLACER")) %>%
  mutate(ca_emp_14=sum(emp_total,na.rm=T)) %>%
  mutate(ca_emp_18=sum(EDD$employees,na.rm=T)) %>%
  mutate(emp_retail_per14=emp_retail/ca_emp_14,
         emp_srvc_per14=emp_srvc/ca_emp_14,
         emp_game_per14=emp_game/ca_emp_14,
         emp_rec_per14=emp_rec/ca_emp_14,
         emp_other_per14=emp_other/ca_emp_14,
         emp_retail_18_est14=emp_retail_per14 * ca_emp_18,
         emp_srvc_18_est14=emp_srvc_per14 * ca_emp_18,
         emp_game_18_est14=emp_game_per14 * ca_emp_18,
         emp_rec_18_est14=emp_rec_per14 * ca_emp_18,
         emp_other_18_est14=emp_other_per14 * ca_emp_18) %>%
  select(-c(1:5, 7:10, 12:16))

#compare 2014 to 2018 california employees
ca_comp<-data.frame(
  emp14=c(
sum(ca_emp_est$emp_retail,na.rm=T),
sum(ca_emp_est$emp_srvc,na.rm=T),
sum(ca_emp_est$emp_gaming,na.rm=T),
sum(ca_emp_est$emp_rec,na.rm=T),
sum(ca_emp_est$emp_other,na.rm=T)
),
 emp18=c(
sum(emp_ca_taz18$emp_retail,na.rm=T),
sum(emp_ca_taz18$emp_srvc,na.rm=T),
sum(emp_ca_taz18$emp_gaming,na.rm=T),
sum(emp_ca_taz18$emp_rec,na.rm=T),
sum(emp_ca_taz18$emp_other,na.rm=T)
),
type=c("retail","service","gaming","rec","other")
)

#### scratch

## el dorado employees
st_join(st_buffer(taz,0), st_buffer(county,0),largest=TRUE) %>%
  left_join(EDD_final, by="TAZ") %>% group_by(COUNTY) %>%
  summarise(employees=sum(employees,na.rm=T))

## douglas employees

detr_tract_clean %>% group_by(County) %>%
summarise(Total_Employment_Q3=sum(Total_Employment_Q3,na.rm=T))

sum(doug$Total_Employment_Q3, na.rm=T)




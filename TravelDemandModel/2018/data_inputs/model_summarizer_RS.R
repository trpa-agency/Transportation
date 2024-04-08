library(tidyverse)


thru<-read_csv("model_summarizer/PartyArray_afterThruVisitors.pam") %>%
  mutate(partyType=case_when(stayType==1 ~ "seasonal"))

### read in trip file ###
trip_file<-read_csv("model_summarizer/trip_file.csv") %>%
  mutate(id=paste(startTaz, endTaz, sep="-"), id2=paste(startTaz, endTaz, skim, sep="-")) %>% 
  mutate(modeAgg = case_when(
    mode %in% c('drive alone','shared auto')~'drive',
    mode %in% c('drive to transit','walk to transit')~'transit',
    mode %in% c('non motorized')~'non-motorized',
    mode %in% c('visitor shuttle')~'other')) %>% 
  left_join(thru, by=c("partyID"="id"))

trip_file %>% group_by(partyType.y,partyType.x) %>% count()

### read in and combine distances skim files ###
pm<-read_csv("model_summarizer/SummerPMPeakDriveDistanceSkim.csv") %>%
  mutate(skim=2,id2=paste(`TAZ:1`, TAZ,skim, sep="-")) %>%
  rename(trip_time=`AB_PM_IVTT / BA_PM_IVTT`)
am<-read_csv("model_summarizer/SummerAMPeakDriveDistanceSkim.csv") %>%
  mutate(skim=1,id2=paste(`TAZ:1`, TAZ,skim, sep="-")) %>%
  rename(trip_time=`AB_AM_IVTT / BA_AM_IVTT`)
ln<-read_csv("model_summarizer/SummerLateNightDriveDistanceSkim.csv") %>%
  mutate(skim=4,id2=paste(`TAZ:1`, TAZ, skim, sep="-")) %>%
  rename(trip_time=`AB_LN_IVTT / BA_LN_IVTT`)
md<-read_csv("model_summarizer/SummerMiddayDriveDistanceSkim.csv") %>%
  mutate(skim=3, id2=paste(`TAZ:1`, TAZ, skim, sep="-")) %>%
  rename(trip_time=`AB_MD_IVTT / BA_MD_IVTT`)
dist <- bind_rows(pm,am,ln,md)

### trip_length_summary ###

trip_len_sum <- trip_file %>% left_join(dist, by="id2") %>%
  group_by(partyType, tripType, modeAgg, skim.x) %>%
  summarise(Average_Trip_Length_Miles=mean(`Length (Skim)`, na.rm=T),
            Average_Trip_Time_Minutes=mean(trip_time, na.rm=T),
            count=n()) %>%
  mutate(Time=case_when(skim.x==1 ~ "AM",
                        skim.x==2 ~ "PM",
                        skim.x==3 ~ "MD",
                        skim.x==4 ~ "LN")) %>%
  select(partyType, tripType, modeAgg, Time, Average_Trip_Length_Miles,Average_Trip_Time_Minutes, count)

### export trip summary file ### 

write.csv(trip_len_sum,"./trip_length_summary.csv")

### tour_length_summary ###

tour_len_sum <- trip_file %>% left_join(dist, by="id2") %>%
  group_by(tourID, modeAgg, tripType, partyType) %>% 
  summarise(trip_time=sum(trip_time),Length_Skim=sum(`Length (Skim)`)) %>%
  group_by(partyType, tripType, modeAgg) %>%
  summarise(Average_Tour_Length_Miles=mean(Length_Skim, na.rm=T),
            Average_Tour_Time_Minutes=mean(trip_time, na.rm=T),
            count=n())

### export tour summary file ### 

write.csv(tour_len_sum,"./tour_length_summary.csv")
 



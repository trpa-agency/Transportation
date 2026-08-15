import pandas as pd

# get feature service as dataframe
def get_fs_as_df(url: str):
    layer = FeatureLayer(url, gis=GIS()) 
    return pd.DataFrame.spatial.from_layer(layer)


### DERQ API FUNCTIONS ###

# Get DERQ locations for Tahoe
def get_derq_locations():
    url = derq_api_url + '/locations'
    return requests.get(url, headers=headers).json()
# parse as dataframe
def parse_locations_response(response: dict) -> pd.DataFrame:
    """Parse the DERQ API response to extract location data."""
    locations = response.get("body", [])
    return pd.DataFrame(locations)
# get veh counts for a location
def get_derq_veh_counts(location_id: str, start_date: str, end_date: str) -> dict:
    """
    Fetch vehicle count data for a given location and time range.

    Parameters:
        location_id (str): Location ID to query
        start_date (str): Start date in 'YYYY-MM-DD' format
        end_date (str): End date in 'YYYY-MM-DD' format

    Returns:
        dict: JSON response from the API containing vehicle counts
    """
    url = f"{derq_api_url}/counts/vehicle?locationId={location_id}&startDate={start_date}&endDate={end_date}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

# Get vehicle counts for multiple locations
def parse_vehicle_counts_response(response: dict) -> pd.DataFrame:
    all_data = []
    for location_name, payload in response.items():
        if payload.get("statusCode") == "200":
            for entry in payload.get("body", []):
                entry["LocationName"] = location_name
                all_data.append(entry)
    return pd.DataFrame(all_data)

def get_derq_safety_insights(location_id: str, start_date: str, end_date: str) -> dict:
    """
    Fetch safety insights data for a given location and time range.

    Parameters:
        location_id (str): Location ID to query
        start_date (str): Start date in 'YYYY-MM-DD' format
        end_date (str): End date in 'YYYY-MM-DD' format

    Returns:
        dict: JSON response from the API containing safety insights
    """
    url = f"{derq_api_url}/safety-insights?locationId={location_id}&startDate={start_date}&endDate={end_date}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def parse_safety_insights_response(response: dict) -> pd.DataFrame:
    if response.get("statusCode") == "200":
        return pd.DataFrame(response.get("body", []))
    else:
        return pd.DataFrame()
# get derq vru counts function
def get_derq_vru_counts(location_id: str, start_date: str, end_date: str) -> dict:
    """
    Fetch VRU count data for a given location and time range.

    Parameters:
        location_id (str): Location ID to query
        start_date (str): Start date in 'YYYY-MM-DD' format
        end_date (str): End date in 'YYYY-MM-DD' format

    Returns:
        dict: JSON response from the API containing VRU counts
    """
    url = f"{derq_api_url}/counts/vru?locationId={location_id}&startDate={start_date}&endDate={end_date}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

# parse vru counts response
def parse_vru_counts_response(response: dict) -> pd.DataFrame:
    if response.get("statusCode") == "200":
        return pd.DataFrame(response.get("body", []))
    else:
        return pd.DataFrame()

# get derq single location vehicle counts function
def parse_single_location_vehicle_counts(response: dict) -> pd.DataFrame:
    if response.get("statusCode") == "200":
        return pd.DataFrame(response.get("body", []))
    else:
        return pd.DataFrame()  # Return empty DataFrame if error

# get derq speed counts function
def get_derq_speeds(location_id: str, start_date: str, end_date: str, buckets=default_speed_buckets, unit='mph') -> dict:
    """
    Fetch speed distribution data for a given location and time range.

    Parameters:
        location_id (str): Location ID to query
        start_date (str): Start date in 'YYYY-MM-DD' format
        end_date (str): End date in 'YYYY-MM-DD' format
        buckets (str): Speed buckets for the distribution
        unit (str): Speed unit (e.g., 'mph', 'km/h')

    Returns:
        dict: JSON response from the API containing speed distribution data
    """
    url = f"{derq_api_url}/speed-distribution?locationId={location_id}&startDate={start_date}&endDate={end_date}&speedBuckets={buckets}&speedUnit={unit}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()
# parse speed response
def parse_speed_response(response: dict) -> pd.DataFrame:
    if response.get("statusCode") == "200":
        return pd.DataFrame(response.get("body", []))
    else:
        return pd.DataFrame()
    
## Reed's work ###
def get_derq_events(location, start, end, event_types=all_event_types):
    url = derq_api_url + f'/safety-insights?locationId={location}&startDate={start}&endDate={end}&eventTypes={event_types}'
    return requests.get(url, headers=headers).json()

def get_derq_veh_counts(location, start, end):
    url = derq_api_url + f'/counts/vehicle?locationId={location}&startDate={start}&endDate={end}'
    return requests.get(url, headers=headers).json()

def get_derq_vru_counts(location, start, end):
    url = derq_api_url + f'/counts/vru?locationId={location}&startDate={start}&endDate={end}'
    return requests.get(url, headers=headers).json()

def get_derq_speeds(location, start, end, buckets=default_speed_buckets, unit='mph'):
    url = derq_api_url + f'/speed-distribution?locationId={location}&startDate={start}&endDate={end}&speedBuckets={buckets}&speedUnit={unit}'
    return requests.get(url, headers=headers).json()

def process_response_derq(response, intersection_id, df_list):
    if response:
        data = response.get('body', [])
        if data:
            df = pd.DataFrame(data)
            df['intersection_id'] = intersection_id
            df_list.append(df)
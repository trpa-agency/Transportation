import pandas as pd
from pathlib import Path
from utils import *

def get_adjusted_future_units(dfPool, zone_proportions):
    def _get_proportions_(jurisdiction, unit_pool):
        return zone_proportions.get((jurisdiction, unit_pool), zone_proportions['default'])

    proportions = dfPool.apply(lambda r: _get_proportions_(r['Jurisdiction'], r['Unit_Pool']), axis=1)
    dfPool['Future_Units_MF']     = (dfPool['Future_Units'] * proportions.map(lambda p: p['mf'])).round().astype(int)
    dfPool['Future_Units_SF']     = (dfPool['Future_Units'] * proportions.map(lambda p: p['sf'])).round().astype(int)
    dfPool['Future_Units_Infill'] = (dfPool['Future_Units'] * proportions.map(lambda p: p['infill'])).round().astype(int)

    # Assign any rounding error to the single family pool
    dfPool['Adjustment'] = (dfPool['Future_Units']
                            - dfPool['Future_Units_MF']
                            - dfPool['Future_Units_SF']
                            - dfPool['Future_Units_Infill'])
    dfPool['Future_Units_SF'] = dfPool['Future_Units_SF'] + dfPool['Adjustment']
    dfPool.drop(columns=['Adjustment'], inplace=True)
    return dfPool

# ═══════════════════════════════════════════════════════════════════════════════
# Forecast Jurisdiction Pools
# ═══════════════════════════════════════════════════════════════════════════════

def forecast_jurisdiction_pools(sdfParcels, dfPool, conditions):
    """Allocate residential units to jurisdiction-level bonus and general pools."""
    assignments = [
        ##-- Bonus Unit Assignments --##
        ('CSLT_Bonus_MF',      'CSLT', 'Bonus Unit', 'MF',     'CSLT Bonus Units MF',     forecast_residential_units),
        ('CSLT_Bonus_SF',      'CSLT', 'Bonus Unit', 'SF',     'CSLT Bonus Units SF',     forecast_residential_units),
        ('CSLT_Bonus_Infill',  'CSLT', 'Bonus Unit', 'Infill', 'CSLT Bonus Units Infill', forecast_residential_units_infill),
        ('DG_Bonus_MF',        'DG',   'Bonus Unit', 'MF',     'DG Bonus Units MF',       forecast_residential_units),
        ('DG_Bonus_SF',        'DG',   'Bonus Unit', 'SF',     'DG Bonus Units SF',       forecast_residential_units),
        ('DG_Bonus_Infill',    'DG',   'Bonus Unit', 'Infill', 'DG Bonus Units Infill',   forecast_residential_units_infill),
        ('PL_Bonus_MF',        'PL',   'Bonus Unit', 'MF',     'PL Bonus Units MF',       forecast_residential_units),
        ('PL_Bonus_SF',        'PL',   'Bonus Unit', 'SF',     'PL Bonus Units SF',       forecast_residential_units),
        ('PL_Bonus_Infill',    'PL',   'Bonus Unit', 'Infill', 'PL Bonus Units Infill',   forecast_residential_units_infill),
        ('WA_Bonus_MF',        'WA',   'Bonus Unit', 'MF',     'WA Bonus Units MF',       forecast_residential_units),
        ('WA_Bonus_SF',        'WA',   'Bonus Unit', 'SF',     'WA Bonus Units SF',       forecast_residential_units),
        ('WA_Bonus_Infil',     'WA',   'Bonus Unit', 'Infill', 'WA Bonus Units Infill',   forecast_residential_units_infill),
        ##-- General Unit Assignments --##
        ('CSLT_General_MF',    'CSLT', 'General', 'MF',     'CSLT General Units MF',     forecast_residential_units),
        ('CSLT_General_SF',    'CSLT', 'General', 'SF',     'CSLT General Units SF',     forecast_residential_units),
        ('CSLT_General_Infill','CSLT', 'General', 'Infill', 'CSLT General Units Infill', forecast_residential_units_infill),
        ('EL_General_MF',      'EL',   'General', 'MF',     'EL General Units MF',       forecast_residential_units),
        ('EL_General_SF',      'EL',   'General', 'SF',     'EL General Units SF',       forecast_residential_units),
        ('EL_General_Infill',  'EL',   'General', 'Infill', 'EL General Units Infill',   forecast_residential_units_infill),
        ('PL_General_MF',      'PL',   'General', 'MF',     'PL General Units MF',       forecast_residential_units),
        ('PL_General_SF',      'PL',   'General', 'SF',     'PL General Units SF',       forecast_residential_units),
        ('PL_General_Infill',  'PL',   'General', 'Infill', 'PL General Units Infill',   forecast_residential_units_infill),
        ('DG_General_MF',      'DG',   'General', 'MF',     'DG General Units MF',       forecast_residential_units),
        ('DG_General_SF',      'DG',   'General', 'SF',     'DG General Units SF',       forecast_residential_units),
        ('DG_General_Infill',  'DG',   'General', 'Infill', 'DG General Units Infill',   forecast_residential_units_infill),
        ('WA_General_MF',      'WA',   'General', 'MF',     'WA General Units MF',       forecast_residential_units),
        ('WA_General_SF',      'WA',   'General', 'SF',     'WA General Units SF',       forecast_residential_units),
        ('WA_General_Infill',  'WA',   'General', 'Infill', 'WA General Units Infill',   forecast_residential_units_infill),
    ]

    df_built_parcels = pd.DataFrame()
    for condition_key, jurisdiction, pool, unit_type, label, fn in assignments:
        target_sum             = get_target_sum(dfPool, jurisdiction, pool, unit_type)
        sdfParcels, df_summary = fn(sdfParcels, conditions[condition_key], target_sum, label)
        df_built_parcels       = pd.concat([df_built_parcels, df_summary], ignore_index=True)

    return sdfParcels, df_built_parcels


# ═══════════════════════════════════════════════════════════════════════════════
# Forecast TRPA Pools
# ═══════════════════════════════════════════════════════════════════════════════

def forecast_trpa_pools(sdfParcels, dfPool, conditions, df_built_parcels):
    """Allocate residential units to TRPA-administered bonus unit, general, and ADU pools."""
    trpa_assignments = [
        ('TRPA_Bonus_MF',      'TRPA', 'Bonus Unit', 'MF',     'TRPA Bonus Units MF',      forecast_residential_units),
        ('TRPA_Bonus_SF',      'TRPA', 'Bonus Unit', 'SF',     'TRPA Bonus Units SF',      forecast_residential_units),
        ('TRPA_Bonus_Infill',  'TRPA', 'Bonus Unit', 'Infill', 'TRPA Bonus Units Infill',  forecast_residential_units_infill),
        ('TRPA_General_MF',    'TRPA', 'General',    'MF',     'TRPA General Units MF',    forecast_residential_units),
        ('TRPA_General_SF',    'TRPA', 'General',    'SF',     'TRPA General Units SF',    forecast_residential_units),
        ('TRPA_General_Infill','TRPA', 'General',    'Infill', 'TRPA General Units Infill', forecast_residential_units_infill),
        ('TRPA_ADU',           'TRPA', 'ADU',         'ADU',    'TRPA ADU Units',            forecast_residential_units),
        ('TRPA_Affordable_MF',      'TRPA', 'Affordable',   'MF',     'TRPA Affordable Units MF',  forecast_residential_units),
        ('TRPA_Affordable_SF',      'TRPA', 'Affordable',   'SF',     'TRPA Affordable Units SF',  forecast_residential_units),
        ('TRPA_Affordable_Infill',  'TRPA', 'Affordable',   'Infill', 'TRPA Affordable Units Infill',  forecast_residential_units_infill),
        ('TRPA_Moderate_MF',      'TRPA', 'Moderate',   'MF',     'TRPA Moderate Units MF',  forecast_residential_units),
        ('TRPA_Moderate_SF',      'TRPA', 'Moderate',   'SF',     'TRPA Moderate Units SF',  forecast_residential_units),
        ('TRPA_Moderate_Infill',  'TRPA', 'Moderate',   'Infill', 'TRPA Moderate Units Infill',  forecast_residential_units_infill),
        ('TRPA_Achievable_Bonus_MF',      'TRPA', 'Achievable Bonus',   'MF',     'TRPA Achievable Bonus Units MF',  forecast_residential_units),
        ('TRPA_Achievable_Bonus_SF',      'TRPA', 'Achievable Bonus',   'SF',     'TRPA Achievable Bonus Units SF',  forecast_residential_units),
        ('TRPA_Achievable_Bonus_Infill',  'TRPA', 'Achievable Bonus',   'Infill', 'TRPA Achievable Bonus Units Infill',  forecast_residential_units_infill),
        ('TRPA_Affordable_BD_MF',      'TRPA', 'Affordable by Design',   'MF',     'TRPA Affordable BD Units MF',  forecast_residential_units),
        ('TRPA_Affordable_BD_SF',      'TRPA', 'Affordable by Design',   'SF',     'TRPA Affordable BD Units SF',  forecast_residential_units),
        ('TRPA_Affordable_BD_Infill',  'TRPA', 'Affordable by Design',   'Infill', 'TRPA Affordable BD Units Infill',  forecast_residential_units_infill),
        ('TRPA_Achievable_Gen_MF',      'TRPA', 'Achievable General',   'MF',     'TRPA Achievable General Units MF',  forecast_residential_units),
        ('TRPA_Achievable_Gen_SF',      'TRPA', 'Achievable General',   'SF',     'TRPA Achievable General Units SF',  forecast_residential_units),
        ('TRPA_Achievable_Gen_Infill',  'TRPA', 'Achievable General',   'Infill', 'TRPA Achievable General Units Infill',  forecast_residential_units_infill),
        ('TRPA_JADU',           'TRPA', 'JADU',         'JADU',    'TRPA JADU Units',            forecast_residential_units)
    ]

    for condition_key, jurisdiction, pool, unit_type, label, fn in trpa_assignments:
        target_sum             = get_target_sum(dfPool, jurisdiction, pool, unit_type)
        print(f'TRPA pool assignment - {label} - target units to assign = {target_sum}')
        if target_sum == 0:
            continue
        else:
            sdfParcels, df_summary = fn(sdfParcels, conditions[condition_key], target_sum, label)
            df_built_parcels       = pd.concat([df_built_parcels, df_summary], ignore_index=True)

    return sdfParcels, df_built_parcels


# ═══════════════════════════════════════════════════════════════════════════════
# Assign the Remainders
# ═══════════════════════════════════════════════════════════════════════════════

def assign_remainders(sdfParcels, conditions, df_built_parcels, adu_target=4319):
    """Assign remainder units as infill and fill the ADU pool to target."""
    df_remaining = df_built_parcels.loc[df_built_parcels.Total_Remaining_Units > 0].copy()
    df_remaining['Jurisdiction'] = df_remaining['Reason'].str.split(' ').str[0]

    remainder_assignments = [
        ('WA Bonus Units SF',      'WA_Bonus_Infil',     'WA Bonus Units Infill',     forecast_residential_units_infill),
        ('EL General Units MF',    'EL_General_Infill',  'EL General Units Infill',   forecast_residential_units_infill),
        ('PL General Units MF',    'PL_General_Infill',  'PL General Units Infill',   forecast_residential_units_infill),
        ('DG General Units MF',    'DG_General_Infill',  'DG General Units Infill',   forecast_residential_units),
        ('WA General Units MF',    'WA_General_Infill',  'WA General Units Infill',   forecast_residential_units_infill),
        ('WA General Units SF',    'WA_General_Infill',  'WA General Units Infill',   forecast_residential_units_infill),
        ('TRPA General Units MF',  'TRPA_General_Infill','TRPA General Units Infill', forecast_residential_units_infill),
    ]

    for remaining_reason, condition_key, label, fn in remainder_assignments:
        target_sum             = df_remaining.loc[df_remaining.Reason == remaining_reason, 'Total_Remaining_Units'].values[0]
        sdfParcels, df_summary = fn(sdfParcels, conditions[condition_key], target_sum, label)
        df_built_parcels       = pd.concat([df_built_parcels, df_summary], ignore_index=True)

    # ADU assignment to eligible residential parcels
    TRPA_ADU_condition = conditions['TRPA_ADU']
    target_sum = adu_target - sdfParcels.FORECASTED_RESIDENTIAL_UNITS.sum()
    sdfParcels, df_summary = forecast_residential_units(sdfParcels, TRPA_ADU_condition, target_sum, 'TRPA ADU Units')
    df_built_parcels = pd.concat([df_built_parcels, df_summary], ignore_index=True)

    return sdfParcels, df_built_parcels


# ═══════════════════════════════════════════════════════════════════════════════
# Check Results
# ═══════════════════════════════════════════════════════════════════════════════

def check_forecast_results(sdfParcels, dfPool):
    """Compare forecasted units against pool targets; returns a comparison DataFrame."""
    dfPoolMelt = dfPool.melt(
        id_vars=['Jurisdiction', 'Unit_Pool'],
        value_vars=['Future_Units_MF', 'Future_Units_SF', 'Future_Units_Infill'])
    dfPoolMelt['variable'] = dfPoolMelt['variable'].str.replace('Future_Units_', '')
    dfPoolMelt['Unit_Pool'] = dfPoolMelt['Jurisdiction'] + ' ' + dfPoolMelt['Unit_Pool']
    dfPoolMelt.rename(columns={'variable': 'Reason', 'value': 'Units'}, inplace=True)

    dfForecastGroup = sdfParcels.groupby(['FORECAST_REASON'])['FORECASTED_RESIDENTIAL_UNITS'].sum().reset_index()
    dfForecastGroup['Reason']       = dfForecastGroup['FORECAST_REASON'].str.split(' ').str[-1]
    dfForecastGroup['Jurisdiction'] = dfForecastGroup['FORECAST_REASON'].str.split(' ').str[0]
    dfForecastGroup.loc[dfForecastGroup['FORECAST_REASON'].str.contains('Bonus'),   'Unit_Pool'] = dfForecastGroup.Jurisdiction + ' ' + 'Bonus Unit'
    dfForecastGroup.loc[dfForecastGroup['FORECAST_REASON'].str.contains('General'), 'Unit_Pool'] = dfForecastGroup.Jurisdiction + ' ' + 'General'

    dfMerge = dfForecastGroup.merge(dfPoolMelt, on=['Unit_Pool', 'Reason'], how='left')
    dfMerge['Unit_Diff'] = dfMerge['FORECASTED_RESIDENTIAL_UNITS'] - dfMerge['Units']
    return dfMerge


# ═══════════════════════════════════════════════════════════════════════════════
# Assign Forecast Year
# ═══════════════════════════════════════════════════════════════════════════════

def assign_development_year(sdfParcels, dfResZoned):
    """Assign Development_Year (2035 or 2050) to each forecasted parcel."""
    TotalDevelopment = dfResZoned.Future_Units.sum()
    Development_2035 = (TotalDevelopment * 0.33).astype(int)
    sdfParcels['Development_Year'] = None

    sdfParcels.loc[
        (sdfParcels['FORECAST_REASON'] == 'Assigned') & (sdfParcels['FORECASTED_RESIDENTIAL_UNITS'] >= 1),
        'Development_Year'] = 2035
    RemainingDevelopment_2035 = Development_2035 - sdfParcels.loc[
        sdfParcels['FORECAST_REASON'] == 'Assigned', 'FORECASTED_RESIDENTIAL_UNITS'].sum()

    Development_2035_Condition = sdfParcels['FORECASTED_RESIDENTIAL_UNITS'].where(
        sdfParcels['FORECAST_REASON'] != 'Assigned').cumsum()
    sdfParcels.loc[
        (Development_2035_Condition < RemainingDevelopment_2035) & (sdfParcels['FORECASTED_RESIDENTIAL_UNITS'] >= 1),
        'Development_Year'] = 2035
    sdfParcels.loc[
        (sdfParcels['FORECAST_REASON'] != '') & (sdfParcels['Development_Year'].isnull()) & (sdfParcels['FORECASTED_RESIDENTIAL_UNITS'] >= 1),
        'Development_Year'] = 2050

    return sdfParcels


# ═══════════════════════════════════════════════════════════════════════════════
# Assign Occupancy Rate
# ═══════════════════════════════════════════════════════════════════════════════

def assign_occupancy_rate(sdfParcels, occupancy_rates, res_assigned_lookup_path='res_assigned_lookup.csv'):
    """Map known-project occupancy rates to parcels, then apply keyword-based overrides.

    Returns (sdfParcels, dfResAssigned) so the income function can reuse dfResAssigned.
    """
    sdfParcels['FORECASTED_RES_OCCUPANCY_RATE'] = 0

    dfResAssigned = pd.read_csv(res_assigned_lookup_path)
    string_cols = dfResAssigned.select_dtypes(include=['string']).columns
    dfResAssigned[string_cols] = dfResAssigned[string_cols].astype(object)
    dfResAssigned['Occupancy_Rate'] = dfResAssigned['Occupancy_Rate'].astype(float)

    string_cols = sdfParcels.select_dtypes(include=['string']).columns
    sdfParcels[string_cols] = sdfParcels[string_cols].astype(object)
    sdfParcels['FORECASTED_RES_OCCUPANCY_RATE'] = sdfParcels['APN'].map(
        dict(zip(dfResAssigned.APN, dfResAssigned['Occupancy_Rate'])))

    for reason_keyword, rate in occupancy_rates.items():
        mask = sdfParcels['FORECAST_REASON'].fillna('').str.contains(reason_keyword)
        sdfParcels.loc[mask, 'FORECASTED_RES_OCCUPANCY_RATE'] = rate

    return sdfParcels, dfResAssigned


# ═══════════════════════════════════════════════════════════════════════════════
# Assign Household Income Category
# ═══════════════════════════════════════════════════════════════════════════════

def assign_income_categories(sdfParcels, dfResAssigned, income_proportions):
    """Assign Low/Medium/High income proportions to forecasted parcels."""
    sdfParcels['FORECASTED_RES_INCOME_LOW']    = 0.0
    sdfParcels['FORECASTED_RES_INCOME_MEDIUM'] = 0.0
    sdfParcels['FORECASTED_RES_INCOME_HIGH']   = 0.0

    sdfParcels['FORECAST_RES_INCOME_CATEGORY'] = sdfParcels.APN.map(
        dict(zip(dfResAssigned.APN, dfResAssigned['HH Income Category'])))
    sdfParcels.loc[sdfParcels['FORECAST_RES_INCOME_CATEGORY'] == 'Achievable', 'FORECAST_RES_INCOME_CATEGORY'] = 'Medium'
    sdfParcels.loc[sdfParcels['FORECAST_RES_INCOME_CATEGORY'] == 'Affordable',  'FORECAST_RES_INCOME_CATEGORY'] = 'Low'

    def _income_category(df, category):
        df.loc[df['FORECAST_RES_INCOME_CATEGORY'] == category, 'FORECASTED_RES_INCOME_' + str(category).upper()] = 1
        return df

    for category in ['Low', 'Medium', 'High']:
        sdfParcels = _income_category(sdfParcels, category)

    for reason_keyword, props in income_proportions.items():
        mask = sdfParcels['FORECAST_REASON'].fillna('').str.contains(reason_keyword)
        sdfParcels.loc[mask, 'FORECASTED_RES_INCOME_LOW']    = props['low']
        sdfParcels.loc[mask, 'FORECASTED_RES_INCOME_MEDIUM'] = props['medium']
        sdfParcels.loc[mask, 'FORECASTED_RES_INCOME_HIGH']   = props['high']

    return sdfParcels


# ═══════════════════════════════════════════════════════════════════════════════
# Summary — Build TAZ Summary
# ═══════════════════════════════════════════════════════════════════════════════

def build_taz_summary(sdfParcels, dfSocio):
    """Aggregate parcel forecasts to TAZ level for the 2035 and 2050 model years."""
    sdfParcels['FORECASTED_OCCUPIED_UNITS']          = sdfParcels['FORECASTED_RESIDENTIAL_UNITS'] * sdfParcels['FORECASTED_RES_OCCUPANCY_RATE']
    sdfParcels['FORECASTED_RES_INCOME_LOW_UNITS']    = sdfParcels['FORECASTED_RES_INCOME_LOW']    * sdfParcels['FORECASTED_OCCUPIED_UNITS']
    sdfParcels['FORECASTED_RES_INCOME_MEDIUM_UNITS'] = sdfParcels['FORECASTED_RES_INCOME_MEDIUM'] * sdfParcels['FORECASTED_OCCUPIED_UNITS']
    sdfParcels['FORECASTED_RES_INCOME_HIGH_UNITS']   = sdfParcels['FORECASTED_RES_INCOME_HIGH']   * sdfParcels['FORECASTED_OCCUPIED_UNITS']

    agg_cols = {
        'FORECASTED_RESIDENTIAL_UNITS':      'sum',
        'FORECASTED_OCCUPIED_UNITS':         'sum',
        'FORECASTED_RES_INCOME_LOW_UNITS':   'sum',
        'FORECASTED_RES_INCOME_MEDIUM_UNITS':'sum',
        'FORECASTED_RES_INCOME_HIGH_UNITS':  'sum',
    }

    df = sdfParcels.loc[sdfParcels['FORECASTED_RESIDENTIAL_UNITS'] > 0]
    dfTAZ_Summary_2035 = df.loc[df['Development_Year'] == 2035].groupby('TAZ').agg(agg_cols).reset_index()
    dfTAZ_Summary_2050 = df.groupby('TAZ').agg(agg_cols).reset_index()

    def _merge_socio(df_taz, dfSocio):
        df_taz = dfSocio.merge(df_taz, on='TAZ', how='left')
        df_taz = df_taz.fillna(0)

        df_taz['TOTAL_FORECASTED_UNITS_LOW_INCOME']  = df_taz['FORECASTED_RES_INCOME_LOW_UNITS']    + df_taz['occ_units_low_inc']
        df_taz['TOTAL_FORECASTED_UNITS_MED_INCOME']  = df_taz['FORECASTED_RES_INCOME_MEDIUM_UNITS'] + df_taz['occ_units_med_inc']
        df_taz['TOTAL_FORECASTED_UNITS_HIGH_INCOME'] = df_taz['FORECASTED_RES_INCOME_HIGH_UNITS']   + df_taz['occ_units_high_inc']
        df_taz['TOTAL_FORECASTED_UNITS_OCCUPIED']    = df_taz['FORECASTED_OCCUPIED_UNITS']          + df_taz['total_occ_units']
        df_taz['TOTAL_FORECASTED_RESIDENTIAL_UNITS'] = df_taz['FORECASTED_RESIDENTIAL_UNITS']       + df_taz['total_residential_units']
        df_taz['FORECASTED_PERSONS'] = df_taz['FORECASTED_OCCUPIED_UNITS'] * df_taz['persons_per_occ_unit']
        df_taz['TOTAL_FORECASTED_PERSONS'] = df_taz['FORECASTED_PERSONS'] + df_taz['total_persons']
        df_taz['NEW_OCCUPANCY_RATE'] = (
            (df_taz['FORECASTED_OCCUPIED_UNITS'] + df_taz['total_occ_units']) /
            (df_taz['total_residential_units']   + df_taz['FORECASTED_RESIDENTIAL_UNITS'])
        )

        
        return df_taz

    dfTAZ_Summary_2035 = _merge_socio(dfTAZ_Summary_2035, dfSocio)
    dfTAZ_Summary_2050 = _merge_socio(dfTAZ_Summary_2050, dfSocio)

    return dfTAZ_Summary_2035, dfTAZ_Summary_2050


# ═══════════════════════════════════════════════════════════════════════════════
# Adjust persons per unit for population targets
# ═══════════════════════════════════════════════════════════════════════════════

def adjust_population_targets(dfTAZ_Summary_2035, dfTAZ_Summary_2050, data_dir,
                               target_sum_2035=55592, target_sum_2050=57611):
    """Scale persons-per-occupied-unit to reach regional population targets and save summaries."""
    dfTAZ_Summary_2035['FORECASTED_POPULATION'] = (
        dfTAZ_Summary_2035['TOTAL_FORECASTED_UNITS_OCCUPIED'] * dfTAZ_Summary_2035['persons_per_occ_unit'])
    forecasted_population_2035 = dfTAZ_Summary_2035['FORECASTED_POPULATION'].sum()

    dfTAZ_Summary_2050['FORECASTED_POPULATION'] = (
        dfTAZ_Summary_2050['TOTAL_FORECASTED_UNITS_OCCUPIED'] * dfTAZ_Summary_2050['persons_per_occ_unit'])
    forecasted_population_2050 = dfTAZ_Summary_2050['FORECASTED_POPULATION'].sum()

    adjustment_factor_2035 = target_sum_2035 / forecasted_population_2035
    adjustment_factor_2050 = target_sum_2050 / forecasted_population_2050

    dfTAZ_Summary_2035['Adjusted_Persons_Per_Occupied_Unit'] = dfTAZ_Summary_2035['persons_per_occ_unit'] * adjustment_factor_2035
    dfTAZ_Summary_2050['Adjusted_Persons_Per_Occupied_Unit'] = dfTAZ_Summary_2050['persons_per_occ_unit'] * adjustment_factor_2050

    dfTAZ_Summary_2035['FORECASTED_POPULATION'] = dfTAZ_Summary_2035['TOTAL_FORECASTED_UNITS_OCCUPIED'] * dfTAZ_Summary_2035['Adjusted_Persons_Per_Occupied_Unit']
    dfTAZ_Summary_2050['FORECASTED_POPULATION'] = dfTAZ_Summary_2050['TOTAL_FORECASTED_UNITS_OCCUPIED'] * dfTAZ_Summary_2050['Adjusted_Persons_Per_Occupied_Unit']

    forecasted_population_2035 = dfTAZ_Summary_2035['FORECASTED_POPULATION'].sum()
    forecasted_population_2050 = dfTAZ_Summary_2050['FORECASTED_POPULATION'].sum()

    print(forecasted_population_2035)
    print(forecasted_population_2050)
    print(dfTAZ_Summary_2050['TOTAL_FORECASTED_UNITS_OCCUPIED'].sum())
    print(dfTAZ_Summary_2035['TOTAL_FORECASTED_UNITS_OCCUPIED'].sum())
    print(dfTAZ_Summary_2035['TOTAL_FORECASTED_UNITS_MED_INCOME'].sum() + dfTAZ_Summary_2035['TOTAL_FORECASTED_UNITS_LOW_INCOME'].sum() + dfTAZ_Summary_2035['TOTAL_FORECASTED_UNITS_HIGH_INCOME'].sum())
    print(dfTAZ_Summary_2050['TOTAL_FORECASTED_UNITS_MED_INCOME'].sum() + dfTAZ_Summary_2050['TOTAL_FORECASTED_UNITS_LOW_INCOME'].sum() + dfTAZ_Summary_2050['TOTAL_FORECASTED_UNITS_HIGH_INCOME'].sum())

    dfTAZ_Summary_2035.to_pickle(data_dir / 'taz_summary_2035.pickle')
    dfTAZ_Summary_2035.to_csv(data_dir / 'taz_summary_2035.csv')
    dfTAZ_Summary_2050.to_pickle(data_dir / 'taz_summary_2050.pickle')
    dfTAZ_Summary_2050.to_csv(data_dir / 'taz_summary_2050.csv')

    return dfTAZ_Summary_2035, dfTAZ_Summary_2050


# ═══════════════════════════════════════════════════════════════════════════════
# QA Extra
# ═══════════════════════════════════════════════════════════════════════════════

def qa_checks(sdfParcels, dfPool):
    """Run QA comparisons against pool targets. Saves unit_comparison.csv.

    Returns (unit_comparison, by_town_center, by_taz, by_dev_year).
    """
    built_units = sdfParcels.groupby('FORECAST_REASON').agg({'FORECASTED_RESIDENTIAL_UNITS': 'sum'})
    dfResZoned = dfPool.copy()

    Forecast_Reason_lookup = {
        'CSLT Bonus Units Built':  {'Jurisdiction': 'CSLT', 'Unit_Pool': 'Bonus Unit'},
        'CSLT General Units Built':{'Jurisdiction': 'CSLT', 'Unit_Pool': 'General'},
        'EL General Units Built':  {'Jurisdiction': 'EL',   'Unit_Pool': 'General'},
        'PL Bonus Units Built':    {'Jurisdiction': 'PL',   'Unit_Pool': 'Bonus Unit'},
        'PL General Units Built':  {'Jurisdiction': 'PL',   'Unit_Pool': 'General'},
        'WA Bonus Units Built':    {'Jurisdiction': 'WA',   'Unit_Pool': 'Bonus Unit'},
        'WA General Units Built':  {'Jurisdiction': 'WA',   'Unit_Pool': 'General'},
        'DG Bonus Units Built':    {'Jurisdiction': 'DG',   'Unit_Pool': 'Bonus Unit'},
        'DG General Units Built':  {'Jurisdiction': 'DG',   'Unit_Pool': 'General'},
        'TRPA Bonus Units Built':  {'Jurisdiction': 'TRPA', 'Unit_Pool': 'Bonus Unit'},
        'TRPA General Units Built':{'Jurisdiction': 'TRPA', 'Unit_Pool': 'General'},
        'ADU Units Built':         {'Jurisdiction': 'TRPA', 'Unit_Pool': 'ADU'},
    }

    built_units['Jurisdiction'] = built_units.index.map(lambda x: Forecast_Reason_lookup.get(x, {}).get('Jurisdiction'))
    built_units['Unit_Pool']    = built_units.index.map(lambda x: Forecast_Reason_lookup.get(x, {}).get('Unit_Pool'))

    unit_comparison = built_units.merge(dfResZoned, how='left', on=['Jurisdiction', 'Unit_Pool'])
    unit_comparison['Difference'] = unit_comparison['Future_Units_Adjusted'] - unit_comparison['FORECASTED_RESIDENTIAL_UNITS']
    unit_comparison.to_csv('unit_comparison.csv', index=False)

    by_town_center = sdfParcels.groupby(['LOCATION_TO_TOWNCENTER', 'FORECAST_REASON'])['FORECASTED_RESIDENTIAL_UNITS'].sum()
    by_taz         = sdfParcels.groupby('TAZ')[['FORECASTED_RESIDENTIAL_UNITS', 'Residential_Units']].sum().reset_index()
    by_dev_year    = sdfParcels.groupby('Development_Year')[['FORECASTED_RESIDENTIAL_UNITS', 'Residential_Units']].sum().reset_index()

    return unit_comparison, by_town_center, by_taz, by_dev_year


# ═══════════════════════════════════════════════════════════════════════════════
# Tourist Accommodation Forecast
# ═══════════════════════════════════════════════════════════════════════════════

def forecast_tourist_units(sdfParcels, tau_assigned_lookup='Lookup_Lists/forecast_tourist_assigned_units.csv'):
    """Assign forecasted tourist accommodation units from the assigned units lookup."""
    dfTouristAssigned = pd.read_csv(tau_assigned_lookup)
    sdfParcels['FORECASTED_TOURIST_UNITS'] = 0
    sdfParcels['FORECASTED_TOURIST_UNITS'] = sdfParcels.APN.map(
        dict(zip(dfTouristAssigned.APN, dfTouristAssigned['Unit_Pool'])))
    return sdfParcels


# ═══════════════════════════════════════════════════════════════════════════════
# Commercial Floor Area Forecast
# ═══════════════════════════════════════════════════════════════════════════════

def forecast_commercial_floor_area(sdfParcels, cfa_assigned_lookup='Lookup_Lists/forecast_commercial_assigned_units.csv'):
    """Assign forecasted commercial floor area from the assigned units lookup."""
    dfCommercialAssigned = pd.read_csv(cfa_assigned_lookup)
    sdfParcels['FORECASTED_COMMERCIAL_FLOOR_AREA'] = 0
    sdfParcels['FORECASTED_COMMERCIAL_FLOOR_AREA'] = sdfParcels.APN.map(
        dict(zip(dfCommercialAssigned.APN, dfCommercialAssigned.SqFt)))
    return sdfParcels


# ═══════════════════════════════════════════════════════════════════════════════
# Exports
# ═══════════════════════════════════════════════════════════════════════════════

def adjust_school_enrollment(df_taz_2035, df_taz_2050, dfSocio, dfSchool):
    """Scale school enrollment proportionally to population change for 2035 and 2050."""


    base_population = dfSocio['total_persons'].sum()
    print(f"Base population: {base_population}")
    school_adj_2035 = (((df_taz_2035['total_persons'].sum() - base_population)/base_population) / 2)
    print(f"2035 population: {df_taz_2035['total_persons'].sum()}, adjustment factor: {school_adj_2035}")
    school_adj_2050 = (((df_taz_2050['total_persons'].sum() - base_population)/base_population) / 2)
    print(f"2050 population: {df_taz_2050['total_persons'].sum()}, adjustment factor: {school_adj_2050}")

    dfSchool_2035 = dfSchool.copy()
    dfSchool_2050 = dfSchool.copy()
    enrollment_fields = ['elementary_school_enrollment', 'middle_school_enrollment',
       'high_school_enrollment', 'college_enrollment']
    for field in enrollment_fields:
        dfSchool_2035[field] = dfSchool_2035[field] + (dfSchool_2035[field] * school_adj_2035)
        dfSchool_2035[field] = dfSchool_2035[field].round(0).astype(int)
        dfSchool_2050[field] = dfSchool_2050[field] + (dfSchool_2050[field] * school_adj_2050)
        dfSchool_2050[field] = dfSchool_2050[field].round(0).astype(int)
    return dfSchool_2035, dfSchool_2050


def export_forecast(sdfParcels, data_dir, gdb, parcel_pickle_part2):
    """Export parcel forecast to pickle, CSV, GDB feature class, and TAZ summary CSV."""
    sdfParcels.to_pickle(parcel_pickle_part2)
    sdfParcels.to_csv(data_dir / 'Parcels_Forecast.csv', index=False)
    sdfParcels.spatial.to_featureclass(Path(gdb) / 'Parcel_Forecast')

    dfTAZ = sdfParcels.groupby('TAZ')[['FORECASTED_RESIDENTIAL_UNITS', 'Residential_Units']].sum().reset_index()
    dfTAZ.to_csv(data_dir / 'TAZ_Units.csv', index=False)
    return dfTAZ
def clean_taz_summary(df_taz, taz_field_mapping):
    df_taz = df_taz[list(taz_field_mapping.keys())].rename(columns=taz_field_mapping)
    # Zero out People where there are no occupied units
    pop_fix = (df_taz["total_persons"] > 0) & (df_taz['total_occ_units'] == 0)
    if pop_fix.sum() > 0:
        print(f"  Population zeroed for {pop_fix.sum()} parcels with 0 occupied units")
        df_taz.loc[pop_fix, "total_persons"] = 0
    else:
        print("  Population fix: no parcels affected")

    # Round at TAZ level
    for col in ["total_occ_units", "occ_units_high_inc", "occ_units_med_inc", "occ_units_low_inc"]:
        df_taz[col] = df_taz[col].round(0).astype(int)

        # Ensure income categories sum to total_occ_units
    income_cols = ["occ_units_high_inc", "occ_units_med_inc", "occ_units_low_inc"]

    income_sum_taz = df_taz[income_cols].sum(axis=1)
    diff = df_taz["total_occ_units"] - income_sum_taz

    fix_needed = diff != 0
    if fix_needed.sum() > 0:
        print(f"  Income balancing applied to {fix_needed.sum()} TAZs")

        for idx in df_taz[fix_needed].index:
            d = diff.loc[idx]

            # If we need to add units
            if d > 0:
                # Distribute to the largest existing category (or cycle if all zero)
                for _ in range(d):
                    row = df_taz.loc[idx, income_cols]
                    target_col = row.idxmax() if row.sum() > 0 else income_cols[0]
                    df_taz.loc[idx, target_col] += 1

            # If we need to remove units
            elif d < 0:
                for _ in range(abs(d)):
                    row = df_taz.loc[idx, income_cols]
                    # Only subtract from non-zero categories
                    non_zero = row[row > 0]
                    if len(non_zero) == 0:
                        break
                    target_col = non_zero.idxmax()
                    df_taz.loc[idx, target_col] -= 1
    else:
        print("  Income balancing: no TAZs affected")

    # Zero out People where OccupiedUnits == 0 at TAZ level
    pop_fix_taz = (df_taz["total_persons"] > 0) & (df_taz["total_occ_units"] == 0)
    if pop_fix_taz.sum() > 0:
        print(f"  TAZ population zeroed for {pop_fix_taz.sum()} TAZs with 0 occupied units")
        df_taz.loc[pop_fix_taz, "total_persons"] = 0
    # If occupancy rate is null fill with 0
    df_taz['census_occ_rate'] = df_taz['census_occ_rate'].fillna(0)
    df_taz.columns
    return df_taz
def adjust_taz_population(df_taz, target_population):
    # Use the weighted sum as the true current population base so that the
    # factor is consistent with the equation: total_persons = total_occ_units * persons_per_occ_unit
    current_population = (df_taz["total_occ_units"] * df_taz["persons_per_occ_unit"]).sum()
    print(f"Current total population (weighted): {current_population}")

    adjustment_factor = target_population / current_population
    print(f"Adjustment factor: {adjustment_factor:.4f}")

    df_taz['persons_per_occ_unit'] = df_taz['persons_per_occ_unit'] * adjustment_factor
    df_taz["total_persons"] = (df_taz["total_occ_units"] * df_taz["persons_per_occ_unit"]).round(0).astype(int)
    print(f"Adjusted total population: {df_taz['total_persons'].sum()}")
    return df_taz
def adjust_taz_persons_per_occ_unit(df_taz, persons_per_occ_unit_df):
    """Adjust the TAZ persons per occupied unit values from the input persons_per_occ_unit
    table (TAZ / persons_per_occ_unit) to the TAZ summary table so that total_persons
    = total_occ_units * persons_per_occ_unit is consistent with the input table.
    """
    # Normalize TAZ types so the join works regardless of int vs str
    df_taz['TAZ'] = df_taz['TAZ'].astype(int)
    persons_per_occ_unit_df = persons_per_occ_unit_df.copy()
    persons_per_occ_unit_df['TAZ'] = persons_per_occ_unit_df['TAZ'].astype(int)
    df_taz = df_taz.merge(persons_per_occ_unit_df, on='TAZ', how='left', suffixes=('', '_target'))
    missing_taz = df_taz['persons_per_occ_unit_target'].isna().sum()
    if missing_taz > 0:
        print(f"  Warning: {missing_taz} TAZs in the forecast TAZ table missing persons_per_occ_unit from the input table")
    # Only overwrite where a target value exists; keep existing value for unmatched TAZs
    df_taz['persons_per_occ_unit'] = df_taz['persons_per_occ_unit_target'].fillna(df_taz['persons_per_occ_unit'])
    df_taz["total_persons"] = (df_taz["total_occ_units"] * df_taz["persons_per_occ_unit"]).round(0).astype(int)
    df_taz.drop(columns=['persons_per_occ_unit_target'], inplace=True)
    return df_taz
def update_employment_numbers(df_taz, employment_df):
    """Update the TAZ level employment numbers from the input employment table (TAZ / employment
    counts by sector) so that the TAZ summary table has the employment numbers from the
    input table.
    """
    # Normalize TAZ types so the join works regardless of int vs str
    df_taz['TAZ'] = df_taz['TAZ'].astype(int)
    employment_df = employment_df.copy()
    # rename taz as TAZ
    employment_df.rename(columns={'taz':'TAZ'}, inplace=True)
    employment_df['TAZ'] = employment_df['TAZ'].astype(int)

    df_taz = df_taz.merge(employment_df, on='TAZ', how='left', suffixes=('', '_target'))
    missing_taz = df_taz.filter(like='_target').isna().sum().sum()
    if missing_taz > 0:
        print(f"  Warning: {missing_taz} employment values missing from the input employment table for TAZs in the forecast TAZ table")

    # overwrite the employment numbers in the TAZ table with the input table values where they exist
    emp_cols = [c for c in df_taz.columns if c.endswith('_target')]
    jobs_columns = ['emp_retail','emp_srvc','emp_rec','emp_game','emp_other']

    for col in emp_cols:
        base_col = col.replace('_target','')
        if base_col in jobs_columns:
            df_taz[base_col] = df_taz[col].fillna(df_taz[base_col])
    df_taz.drop(columns=emp_cols, inplace=True)
    return df_taz
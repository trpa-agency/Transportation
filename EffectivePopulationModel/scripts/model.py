"""
model.py
--------
Core math of the Tahoe Effective Population Model (TEPM).

This is a direct translation of the reactive expressions in the original R-Shiny
application (app.R / script.R, trpa-reid/tahoe_effective_population_model).
Nothing in this module touches the filesystem or the network, so the arithmetic
can be unit-tested and reused from a notebook.

Model structure
---------------
Effective population is the number of people physically present in the Tahoe
region on an annual average day. It is built from five sub-populations:

    effective population = full-time residents
                         + non-resident commuters
                         + day visitors
                         + overnight visitors (hotel/motel/resort/casino, STR, campground)
                         + second home occupants

Overnight segments each contribute two groups of people: those *staying* in the
region on an average day, and those *arriving* on an average day (people in
vehicles crossing an entry station that day). Day visitors are the residual of
the entry-station volume after every other known entering vehicle group is
removed, multiplied by day-visitor vehicle occupancy.

Faithfulness notes (quirks preserved from the R model)
------------------------------------------------------
1. Second-home stay population is "occupied homes x vehicle occupancy" -- the
   vehicles-per-home factor is NOT applied, unlike the other overnight segments.
   The second-home arrival population does apply it. See
   OvernightSegment.count_vehicles_in_stay_population.
2. Second-home arrivals are divided by the *STR* length of stay in the R app.
   ModelInputs.second_home_length_of_stay defaults to that behavior but can be
   set explicitly in the config to override it.
3. Effective population rounds the *sum* of the three visitor populations once,
   then adds the two integer resident/commuter counts -- it does not round each
   component separately. Python's round and R's round both use
   round-half-to-even, so results match exactly.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

DAYS_PER_YEAR = 365

SECOND_HOME_SEGMENT = "Second home"


# ==============================================================================
# Overnight lodging segment
# ==============================================================================

@dataclass(frozen=True)
class OvernightSegment:
    """
    One overnight accommodation type (hotel, STR, campground, second home).

    Parameters
    ----------
    name : str
        Display label used in output tables.
    occupied_units : float
        Units (rooms, STR units, campsites, homes) occupied on an average day.
    vehicles_per_unit : float
        Average vehicles associated with each occupied unit.
    length_of_stay : float
        Average nights per stay. Converts vehicles present into vehicles arriving.
    vehicle_occupancy : float
        Average people per vehicle for this segment.
    count_vehicles_in_stay_population : bool
        True  -> stay population = vehicles present x vehicle occupancy.
        False -> stay population = occupied units x vehicle occupancy.
        False reproduces the R model's second-home treatment (see module docstring).
    """

    name: str
    occupied_units: float
    vehicles_per_unit: float
    length_of_stay: float
    vehicle_occupancy: float
    count_vehicles_in_stay_population: bool = True

    @property
    def vehicles_present(self) -> float:
        """Vehicles parked in the region for this segment on an average day."""
        return self.occupied_units * self.vehicles_per_unit

    @property
    def arriving_vehicles(self) -> float:
        """Vehicles of this segment crossing an entry station on an average day."""
        if self.length_of_stay <= 0:
            raise ValueError(
                f"{self.name}: length_of_stay must be greater than 0, got {self.length_of_stay}"
            )
        return self.vehicles_present / self.length_of_stay

    @property
    def stay_population(self) -> float:
        """People of this segment already in the region on an average day."""
        basis = self.vehicles_present if self.count_vehicles_in_stay_population else self.occupied_units
        return basis * self.vehicle_occupancy

    @property
    def arrival_population(self) -> float:
        """People of this segment entering the region on an average day."""
        return self.arriving_vehicles * self.vehicle_occupancy

    @property
    def population(self) -> float:
        return self.stay_population + self.arrival_population

    def to_row(self) -> dict:
        return {
            "segment":            self.name,
            "occupied_units":     self.occupied_units,
            "vehicles_per_unit":  self.vehicles_per_unit,
            "length_of_stay":     self.length_of_stay,
            "vehicle_occupancy":  self.vehicle_occupancy,
            "vehicles_present":   self.vehicles_present,
            "arriving_vehicles":  self.arriving_vehicles,
            "stay_population":    self.stay_population,
            "arrival_population": self.arrival_population,
            "total_population":   self.population,
        }


# ==============================================================================
# Model inputs
# ==============================================================================

@dataclass
class ModelInputs:
    """
    Every assumption the model needs. Field names map one-to-one onto the
    "inputs" block of a scenario config JSON.

    freight_trips, discretionary_trips and second_home_length_of_stay may be left
    null in the config, in which case resolve_derived_inputs fills them from
    DerivedInputRules exactly as the Shiny app's dynamic defaults did.
    """

    # -- Regional entry volume and resident/commuter populations --------------
    entry_volume: float                   # annual average daily inbound (EI) vehicles
    resident_population: float            # full-time residents (ACS)
    nonresident_commuters: float          # in-commuters living outside the basin
    resident_commuters: float             # residents commuting out of the basin

    # -- Entry trips that are not day visitors --------------------------------
    freight_trips: Optional[float]        # None -> derived from entry volume
    discretionary_trips: Optional[float]  # None -> derived from overnight population

    # -- Day visitors ---------------------------------------------------------
    day_visitor_vehicle_occupancy: float

    # -- Second homes ---------------------------------------------------------
    second_homes: float                   # seasonal/rec/occasional units, net of STRs
    second_home_occupancy: float          # share occupied on an average day (0-1)
    vehicles_per_second_home: float
    second_home_vehicle_occupancy: float
    second_home_length_of_stay: Optional[float]   # None -> use STR length of stay

    # -- Short-term rentals (VHRs) --------------------------------------------
    str_units_rented_annual: float        # annual unit-nights rented
    vehicles_per_str_unit: float
    str_length_of_stay: float
    str_vehicle_occupancy: float

    # -- Hotel / motel / resort / casino --------------------------------------
    hotel_units_rented_annual: float      # annual room-nights rented
    vehicles_per_hotel_room: float
    hotel_length_of_stay: float
    hotel_vehicle_occupancy: float

    # -- Campgrounds ----------------------------------------------------------
    campsites_rented_annual: float        # annual site-nights rented
    vehicles_per_campsite: float
    campsite_length_of_stay: float
    campsite_vehicle_occupancy: float

    # -- Conversion constant --------------------------------------------------
    days_per_year: int = DAYS_PER_YEAR


@dataclass
class DerivedInputRules:
    """
    Rules used to fill inputs left null in the config. These reproduce the default
    values the Shiny app computed on the fly in its renderUI blocks:

        freight       = round(entry_volume * 0.03)
        discretionary = round(round(overnight_population) * 0.07) + 5750
    """

    freight_share_of_entry_volume: float = 0.03
    discretionary_share_of_overnight_population: float = 0.07
    discretionary_base_trips: float = 5750.0


# ==============================================================================
# Results
# ==============================================================================

@dataclass
class ModelResults:
    """Structured output of a single model run."""

    scenario_name: str
    inputs: ModelInputs
    segments: list = field(default_factory=list)          # list[OvernightSegment]

    # Populations
    resident_population: float = 0.0
    commuter_population: float = 0.0
    day_visitor_population: float = 0.0
    overnight_visitor_population: float = 0.0             # hotel + STR + campground
    second_home_population: float = 0.0
    effective_population: int = 0

    # Entry-volume accounting
    day_visitor_vehicles: float = 0.0
    freight_trips: float = 0.0
    discretionary_trips: float = 0.0
    overnight_arriving_vehicles: float = 0.0              # all segments incl. second homes

    # Diagnostics
    warnings: list = field(default_factory=list)

    # -- Derived reporting metrics --------------------------------------------
    @property
    def visitor_population(self) -> float:
        """All non-resident, non-commuter people present on an average day."""
        return (self.day_visitor_population
                + self.overnight_visitor_population
                + self.second_home_population)

    @property
    def peaking_ratio(self) -> float:
        """Effective population divided by the full-time resident population."""
        if self.resident_population <= 0:
            return float("nan")
        return self.effective_population / self.resident_population

    def population_rows(self) -> list:
        """Sub-population breakdown, ordered as the Shiny dashboard displayed it."""
        total = self.effective_population
        rows = [
            ("Full-time residents", self.resident_population),
            ("Commuters",           self.commuter_population),
            ("Day visitors",        self.day_visitor_population),
            ("Overnight visitors",  self.overnight_visitor_population),
            ("Second home owners",  self.second_home_population),
        ]
        out = [
            {
                "component":      name,
                "population":     value,
                "share_of_total": (value / total) if total else float("nan"),
            }
            for name, value in rows
        ]
        out.append({"component": "Effective population", "population": total, "share_of_total": 1.0})
        return out

    def entry_volume_rows(self) -> list:
        """
        Average-daily entry-vehicle accounting. The subtracted components plus the
        day-visitor residual reconstruct the total entry volume.
        """
        i = self.inputs
        rows = [("Total entry volume", i.entry_volume, "input")]
        rows += [
            ("Freight trips",               self.freight_trips,       "subtracted"),
            ("Discretionary trips",         self.discretionary_trips, "subtracted"),
            ("Non-resident commuter trips", i.nonresident_commuters,  "subtracted"),
            ("Resident commuter trips",     i.resident_commuters,     "subtracted"),
        ]
        rows += [(f"{s.name} arriving vehicles", s.arriving_vehicles, "subtracted")
                 for s in self.segments]
        rows += [("Day visitor vehicles", self.day_visitor_vehicles, "residual")]
        return [{"component": n, "vehicles": v, "role": r} for n, v, r in rows]

    def segment_rows(self) -> list:
        return [s.to_row() for s in self.segments]

    def summary_row(self) -> dict:
        """One flat row per scenario, for cross-scenario comparison tables."""
        return {
            "scenario_name":                self.scenario_name,
            "effective_population":         self.effective_population,
            "resident_population":          self.resident_population,
            "commuter_population":          self.commuter_population,
            "day_visitor_population":       self.day_visitor_population,
            "overnight_visitor_population": self.overnight_visitor_population,
            "second_home_population":       self.second_home_population,
            "visitor_population":           self.visitor_population,
            "peaking_ratio":                self.peaking_ratio,
            "entry_volume":                 self.inputs.entry_volume,
            "day_visitor_vehicles":         self.day_visitor_vehicles,
            "freight_trips":                self.freight_trips,
            "discretionary_trips":          self.discretionary_trips,
            "overnight_arriving_vehicles":  self.overnight_arriving_vehicles,
        }

    def to_dict(self) -> dict:
        return {
            "scenario_name":        self.scenario_name,
            "effective_population": self.effective_population,
            "peaking_ratio":        self.peaking_ratio,
            "populations":          self.population_rows(),
            "entry_volume":         self.entry_volume_rows(),
            "segments":             self.segment_rows(),
            "inputs":               asdict(self.inputs),
            "warnings":             self.warnings,
        }


# ==============================================================================
# Segment construction
# ==============================================================================

def build_segments(inputs: ModelInputs) -> list:
    """
    Build the four overnight segments from model inputs.

    Hotel, STR and campground occupancy come from annual unit-nights rented
    divided by days per year. Second homes are already a stock, so occupied units
    are the housing-unit count times the share occupied on an average day.
    """
    days = inputs.days_per_year
    if days <= 0:
        raise ValueError(f"days_per_year must be greater than 0, got {days}")

    sh_los = (inputs.second_home_length_of_stay
              if inputs.second_home_length_of_stay is not None
              else inputs.str_length_of_stay)

    return [
        OvernightSegment(
            name="Hotel/motel/resort/casino",
            occupied_units=inputs.hotel_units_rented_annual / days,
            vehicles_per_unit=inputs.vehicles_per_hotel_room,
            length_of_stay=inputs.hotel_length_of_stay,
            vehicle_occupancy=inputs.hotel_vehicle_occupancy,
        ),
        OvernightSegment(
            name="Short-term rental",
            occupied_units=inputs.str_units_rented_annual / days,
            vehicles_per_unit=inputs.vehicles_per_str_unit,
            length_of_stay=inputs.str_length_of_stay,
            vehicle_occupancy=inputs.str_vehicle_occupancy,
        ),
        OvernightSegment(
            name="Campground",
            occupied_units=inputs.campsites_rented_annual / days,
            vehicles_per_unit=inputs.vehicles_per_campsite,
            length_of_stay=inputs.campsite_length_of_stay,
            vehicle_occupancy=inputs.campsite_vehicle_occupancy,
        ),
        OvernightSegment(
            name=SECOND_HOME_SEGMENT,
            occupied_units=inputs.second_homes * inputs.second_home_occupancy,
            vehicles_per_unit=inputs.vehicles_per_second_home,
            length_of_stay=sh_los,
            vehicle_occupancy=inputs.second_home_vehicle_occupancy,
            # R model omits vehicles-per-home from the stay population; see module docstring.
            count_vehicles_in_stay_population=False,
        ),
    ]


def overnight_visitor_population(segments: list) -> float:
    """
    Hotel + STR + campground population. Excludes second homes, which the
    dashboard reported as its own sub-population.
    """
    return sum(s.population for s in segments if s.name != SECOND_HOME_SEGMENT)


# ==============================================================================
# Derived input resolution
# ==============================================================================

def resolve_derived_inputs(inputs: ModelInputs, rules: DerivedInputRules) -> tuple:
    """
    Fill freight_trips and discretionary_trips when the config left them null,
    reproducing the Shiny app's dynamically rendered defaults.

    Returns
    -------
    (inputs, notes) : (ModelInputs, list[str])
        inputs is mutated in place and returned for convenience. notes records
        which values were derived, for the model_inputs provenance table.
    """
    notes = []

    if inputs.freight_trips is None:
        inputs.freight_trips = float(round(inputs.entry_volume * rules.freight_share_of_entry_volume))
        notes.append(
            f"freight_trips derived as round(entry_volume x "
            f"{rules.freight_share_of_entry_volume}) = {inputs.freight_trips:,.0f}"
        )

    if inputs.discretionary_trips is None:
        # Depends only on the overnight segments, so there is no circular
        # dependency with the day-visitor residual.
        on_pop = overnight_visitor_population(build_segments(inputs))
        inputs.discretionary_trips = float(
            round(round(on_pop) * rules.discretionary_share_of_overnight_population)
            + rules.discretionary_base_trips
        )
        notes.append(
            f"discretionary_trips derived as round(round(overnight_population) x "
            f"{rules.discretionary_share_of_overnight_population}) + "
            f"{rules.discretionary_base_trips:,.0f} = {inputs.discretionary_trips:,.0f}"
        )

    return inputs, notes


# ==============================================================================
# Main computation
# ==============================================================================

def compute(inputs: ModelInputs,
            rules: Optional[DerivedInputRules] = None,
            scenario_name: str = "scenario") -> ModelResults:
    """
    Run the effective population model.

    Parameters
    ----------
    inputs : ModelInputs
        Model assumptions. Null freight/discretionary values are resolved here.
    rules : DerivedInputRules, optional
        Rules for resolving null inputs. Defaults to the R model's rules.
    scenario_name : str
        Label carried into the results.

    Returns
    -------
    ModelResults
    """
    rules = rules or DerivedInputRules()
    inputs, _ = resolve_derived_inputs(inputs, rules)

    segments = build_segments(inputs)
    warnings = []

    # -- Overnight and second home populations --------------------------------
    on_pop = overnight_visitor_population(segments)
    sh_pop = next(s.population for s in segments if s.name == SECOND_HOME_SEGMENT)

    # -- Day visitors: residual of the entry-station volume -------------------
    arriving = sum(s.arriving_vehicles for s in segments)
    day_vehicles = (inputs.entry_volume
                    - inputs.freight_trips
                    - inputs.discretionary_trips
                    - inputs.nonresident_commuters
                    - inputs.resident_commuters
                    - arriving)
    day_pop = day_vehicles * inputs.day_visitor_vehicle_occupancy

    if day_vehicles < 0:
        warnings.append(
            f"Day visitor vehicles are negative ({day_vehicles:,.1f}). Non-day-visitor "
            f"entry trips exceed the total entry volume of {inputs.entry_volume:,.0f}, so "
            f"effective population is understated. Check entry_volume, freight_trips, "
            f"discretionary_trips and the lodging assumptions."
        )

    # -- Effective population -------------------------------------------------
    # Rounded once over the summed visitor populations, matching the R value box.
    effective = int(inputs.resident_population
                    + inputs.nonresident_commuters
                    + round(day_pop + on_pop + sh_pop))

    if not 0.0 <= inputs.second_home_occupancy <= 1.0:
        warnings.append(
            f"second_home_occupancy of {inputs.second_home_occupancy} is outside the 0-1 range."
        )
    if inputs.day_visitor_vehicle_occupancy <= 0:
        warnings.append("day_visitor_vehicle_occupancy must be greater than 0.")

    return ModelResults(
        scenario_name=scenario_name,
        inputs=inputs,
        segments=segments,
        resident_population=float(inputs.resident_population),
        commuter_population=float(inputs.nonresident_commuters),
        day_visitor_population=day_pop,
        overnight_visitor_population=on_pop,
        second_home_population=sh_pop,
        effective_population=effective,
        day_visitor_vehicles=day_vehicles,
        freight_trips=float(inputs.freight_trips),
        discretionary_trips=float(inputs.discretionary_trips),
        overnight_arriving_vehicles=arriving,
        warnings=warnings,
    )

"""Extraction output schema and the matching format for golden labels.

Validate raw model responses with VehicleAccident.model_validate_json(raw_text).
JSON-mode validation accepts enum strings while enforcing strict JSON types.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AccidentType(str, Enum):
    rear_end = "rear_end"
    angle = "angle"
    head_on = "head_on"
    sideswipe = "sideswipe"
    single_vehicle = "single_vehicle"
    other = "other"


class Weather(str, Enum):
    clear = "clear"
    cloudy = "cloudy"
    rain = "rain"
    snow = "snow"
    fog = "fog"
    other = "other"


class RoadSurface(str, Enum):
    dry = "dry"
    wet = "wet"
    snow_ice = "snow_ice"
    other = "other"


class Lighting(str, Enum):
    daylight = "daylight"
    dark_lit = "dark_lit"
    dark_unlit = "dark_unlit"
    dark_unknown = "dark_unknown"
    dawn_dusk = "dawn_dusk"


class LocationType(str, Enum):
    intersection = "intersection"
    ramp = "ramp"
    driveway = "driveway"
    non_junction = "non_junction"


class AreaType(str, Enum):
    urban = "urban"
    rural = "rural"
    residential = "residential"


class CriticalReason(str, Enum):
    driver = "driver"
    vehicle = "vehicle"
    environment = "environment"
    unknown = "unknown"


class Vehicle(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    label: str | None = Field(
        description='Normalize numbered references such as "V1", "Vehicle one", '
        '"Vehicle #1", and "Fordon ett" to V1, V2, etc., following the text\'s '
        "numbering rather than order of appearance. Null if unnumbered."
    )
    year: int | None = Field(description="Stated model year, or null; never guess.")
    make: str | None = Field(description="Stated manufacturer in English, or null.")
    model: str | None = Field(description="Stated model in English, or null.")
    towed: bool | None = Field(
        description="True when towed, including explicitly being loaded onto a tow "
        "truck. False only when explicitly not towed or driven away from the scene. "
        "Merely moved after impact, not stated, or ambiguous means null."
    )


class VehicleAccident(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    accident_type: AccidentType | None = Field(
        description="Classify the first collision, not later impacts. Rear_end: "
        "front-to-rear impact, including a rear-end chain collision. Angle: crossing "
        "paths, including a left turn across oncoming traffic. Head_on: front-to-front "
        "impact of vehicles traveling in opposing directions. Sideswipe: glancing "
        "side contact. Single_vehicle: one moving motor vehicle in the first collision, "
        "including hitting an object, animal, pedestrian, cyclist or parked vehicle, "
        "or a rollover; later involvement of another "
        "vehicle does not change that first-collision type. Other: clearly described "
        "but outside these categories. Null if unstated or ambiguous."
    )
    weather: list[Weather] = Field(
        description="Weather at the time of the accident, with no duplicate values. "
        '"No adverse weather" means clear. Earlier rain or a wet road alone does '
        "not establish current rain. Strong wind is other and may coexist with "
        "clear. Empty list if unstated. Do not infer weather from lighting."
    )
    road_surface: RoadSurface | None = Field(
        description="Only the stated surface condition: dry, wet, snow_ice, or other. "
        "Snow, ice, or frost on the roadway means snow_ice. "
        '"No adverse road conditions" alone is null. Null if unstated or ambiguous.'
    )
    lighting: Lighting | None = Field(
        description="Daylight, dark_lit, dark_unlit, dark_unknown, or dawn_dusk when "
        "explicitly supported. Darkness without information about illumination is "
        "dark_unknown. Morning or evening alone does not establish lighting. "
        "Null if unstated or ambiguous."
    )
    location_type: LocationType | None = Field(
        description="Where the first collision happened relative to a junction (MMUCC relation to "
        "junction, simplified). intersection: in or at an intersection, including T-junctions. "
        "ramp: on an entrance or exit ramp. driveway: at a driveway or parking-lot access. "
        "non_junction: on a road section with no junction involved. Null if unclear."
    )
    area_type: list[AreaType] = Field(
        description="Type of area where the accident happened, as stated, with no duplicate values: "
        "urban (city, town, downtown, city street), rural (countryside, forest, landsbygd, skog), residential "
        "(residential area, bostadsområde). Values can combine, such as a rural residential area. "
        "Empty list if not stated. Do not infer the area from road type or traffic."
    )
    speed_limit_mph: int | None = Field(
        ge=5,
        le=90,
        description="Posted speed limit in mph, 5–90. Prefer stated mph; otherwise "
        "convert km/h to mph and round to the nearest integer. Ignore advisory "
        "limits and actual travel or impact speeds. If several posted limits are "
        "given, use V1's road. Null if no posted limit is stated or it is ambiguous."
    )
    vehicles: list[Vehicle] = Field(
        description="Every motor vehicle that made contact in the accident, including "
        "later impacts and vehicles that left the scene. Contact with an object "
        "or animal also counts. Exclude non-contact vehicles. A tractor and its "
        "attached trailer count as one vehicle, using the tractor's details. "
        "Emit one object per such vehicle, filling only stated details and leaving "
        "the rest null; use an empty list only when no such vehicle is mentioned. "
        "Non-null labels must be unique; multiple unnumbered vehicles may have "
        "null labels. Preserve reported identities; never correct them by guessing."
    )
    injuries_reported: bool | None = Field(
        description="True when an injury or possible injury is explicitly stated, "
        'including "transported for possible injuries". False only when the text '
        "establishes that nobody was injured; one uninjured person is insufficient. "
        "A statement that only some people were uninjured is insufficient for false; "
        "use null unless an injury is reported. "
        "Transport or examination alone, no transport, or injury status not stated "
        "means null. Do not infer injuries from accident severity."
    )
    critical_reason: CriticalReason | None = Field(
        description="The coded critical reason for the accident, whichever vehicle it "
        "is assigned to. Driver errors such as overcompensation or inadequate "
        'surveillance mean driver even without the words "driver related". '
        "Use vehicle for a coded vehicle failure and environment for a coded "
        "environmental cause. An explicitly unknown reason means unknown, but an "
        "explicitly driver-related error of unknown subtype remains driver. "
        "Unstated or conflicting categories mean null. Do not substitute "
        "the reported \"pre-crash event\" or an associated factor for the coded critical reason."
    )

    @field_validator("weather", "area_type")
    @classmethod
    def no_duplicates(cls, value: list) -> list:
        if len(value) != len(set(value)):
            raise ValueError("list must not contain duplicates")
        return value

    @field_validator("vehicles")
    @classmethod
    def unique_vehicle_labels(cls, value: list[Vehicle]) -> list[Vehicle]:
        labels = [vehicle.label for vehicle in value if vehicle.label is not None]
        if len(labels) != len(set(labels)):
            raise ValueError("non-null vehicle labels must be unique")
        return value


class GoldenRecord(BaseModel):
    """One record in golden.jsonl; labels use the model output schema."""

    model_config = ConfigDict(extra="forbid", strict=True)

    id: str = Field(description="Case ID matching the text filename without .txt.")
    labels: VehicleAccident
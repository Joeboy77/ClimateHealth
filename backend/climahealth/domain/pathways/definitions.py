from climahealth.domain.models import (
    ClimateDriver,
    Comparison,
    ContextCondition,
    ContextMultiplier,
    GateDefinition,
    HealthCondition,
    LagWindow,
    PathwayDefinition,
    Season,
    SignalName,
    TriggerDefinition,
)

MALARIA_PATHWAY = PathwayDefinition(
    condition=HealthCondition.MALARIA,
    driver=ClimateDriver.RAIN_FLOOD,
    gate=GateDefinition(),
    triggers=(
        TriggerDefinition(
            signal=SignalName.RAINFALL_7D_MM,
            comparison=Comparison.AT_LEAST,
            threshold=50.0,
            saturation=150.0,
            weight=3.0,
            description="Heavy rainfall in the past week creates mosquito breeding sites",
        ),
        TriggerDefinition(
            signal=SignalName.RAINFALL_14D_MM,
            comparison=Comparison.AT_LEAST,
            threshold=80.0,
            saturation=250.0,
            weight=2.0,
            description="Sustained rainfall over two weeks keeps breeding sites active",
        ),
        TriggerDefinition(
            signal=SignalName.HUMIDITY_MEAN_PERCENT,
            comparison=Comparison.AT_LEAST,
            threshold=60.0,
            saturation=90.0,
            weight=2.5,
            description="High humidity extends adult mosquito survival",
        ),
        TriggerDefinition(
            signal=SignalName.TEMPERATURE_MEAN_C,
            comparison=Comparison.AT_LEAST,
            threshold=22.0,
            saturation=28.0,
            weight=1.5,
            description="Temperature is warm enough for parasite development in the mosquito",
        ),
        TriggerDefinition(
            signal=SignalName.TEMPERATURE_MEAN_C,
            comparison=Comparison.AT_MOST,
            threshold=32.0,
            saturation=28.0,
            weight=1.0,
            description="Temperature is below the ceiling where mosquito survival drops",
        ),
        TriggerDefinition(
            signal=SignalName.STAGNANT_WATER_INDEX,
            comparison=Comparison.AT_LEAST,
            threshold=0.5,
            saturation=1.0,
            weight=2.0,
            description="Standing water is common in this district",
        ),
    ),
    lag_window=LagWindow(minimum_days=14, maximum_days=42),
    vulnerable_group="Children under five and pregnant women",
)

CHOLERA_PATHWAY = PathwayDefinition(
    condition=HealthCondition.CHOLERA,
    driver=ClimateDriver.RAIN_FLOOD,
    gate=GateDefinition(),
    triggers=(
        TriggerDefinition(
            signal=SignalName.RAINFALL_7D_MM,
            comparison=Comparison.AT_LEAST,
            threshold=80.0,
            saturation=200.0,
            weight=3.0,
            description="Flood-level rainfall can overwhelm drainage and contaminate water",
        ),
        TriggerDefinition(
            signal=SignalName.RAINFALL_14D_MM,
            comparison=Comparison.AT_LEAST,
            threshold=120.0,
            saturation=300.0,
            weight=2.0,
            description="Prolonged rainfall keeps water sources contaminated",
        ),
        TriggerDefinition(
            signal=SignalName.POOR_SANITATION_INDEX,
            comparison=Comparison.AT_LEAST,
            threshold=0.5,
            saturation=1.0,
            weight=3.0,
            description="Sanitation coverage in this district is weak",
        ),
        TriggerDefinition(
            signal=SignalName.UNSAFE_WATER_RATIO,
            comparison=Comparison.AT_LEAST,
            threshold=0.4,
            saturation=1.0,
            weight=2.5,
            description="A large share of households rely on unsafe drinking water",
        ),
        TriggerDefinition(
            signal=SignalName.TEMPERATURE_MEAN_C,
            comparison=Comparison.AT_LEAST,
            threshold=26.0,
            saturation=32.0,
            weight=1.0,
            description="Warm water favours survival of the cholera bacterium",
        ),
    ),
    multipliers=(
        ContextMultiplier(
            condition=ContextCondition.COASTAL,
            factor=1.15,
            description="Coastal district: saline intrusion and tidal flooding foul drinking water",
        ),
        ContextMultiplier(
            condition=ContextCondition.FLOOD_PRONE,
            factor=1.15,
            description="District has a history of flooding",
        ),
    ),
    lag_window=LagWindow(minimum_days=2, maximum_days=10),
    vulnerable_group="Children under five and densely settled low-sanitation communities",
)

MENINGITIS_PATHWAY = PathwayDefinition(
    condition=HealthCondition.MENINGITIS,
    driver=ClimateDriver.HARMATTAN_DUST,
    gate=GateDefinition(
        permitted_seasons=(Season.DRY,),
        requires_meningitis_belt=True,
    ),
    triggers=(
        TriggerDefinition(
            signal=SignalName.DUST_CONCENTRATION_UG_M3,
            comparison=Comparison.AT_LEAST,
            threshold=50.0,
            saturation=150.0,
            weight=3.0,
            description="Harmattan dust damages the lining of the throat and nose",
        ),
        TriggerDefinition(
            signal=SignalName.HUMIDITY_MEAN_PERCENT,
            comparison=Comparison.AT_MOST,
            threshold=30.0,
            saturation=12.0,
            weight=3.0,
            description="Very dry air dries out the mucous barrier that blocks infection",
        ),
        TriggerDefinition(
            signal=SignalName.CONSECUTIVE_DRY_DAYS,
            comparison=Comparison.AT_LEAST,
            threshold=14.0,
            saturation=45.0,
            weight=2.0,
            description="A long dry spell sustains the conditions that spread infection",
        ),
        TriggerDefinition(
            signal=SignalName.TEMPERATURE_MAX_C,
            comparison=Comparison.AT_LEAST,
            threshold=35.0,
            saturation=41.0,
            weight=2.0,
            description="High daytime heat is associated with the meningitis season",
        ),
        TriggerDefinition(
            signal=SignalName.PARTICULATE_MATTER_10_UG_M3,
            comparison=Comparison.AT_LEAST,
            threshold=100.0,
            saturation=220.0,
            weight=1.5,
            description="Airborne particulates irritate the respiratory tract",
        ),
    ),
    lag_window=LagWindow(minimum_days=7, maximum_days=28),
    vulnerable_group="Children and young adults under thirty",
)

DIARRHOEAL_DISEASE_PATHWAY = PathwayDefinition(
    condition=HealthCondition.DIARRHOEAL_DISEASE,
    driver=ClimateDriver.RAIN_FLOOD,
    gate=GateDefinition(),
    triggers=(
        TriggerDefinition(
            signal=SignalName.UNSAFE_WATER_RATIO,
            comparison=Comparison.AT_LEAST,
            threshold=0.3,
            saturation=1.0,
            weight=3.0,
            description="Households depend on water sources that are not safely managed",
        ),
        TriggerDefinition(
            signal=SignalName.POOR_SANITATION_INDEX,
            comparison=Comparison.AT_LEAST,
            threshold=0.4,
            saturation=1.0,
            weight=2.5,
            description="Sanitation gaps allow faecal contamination of water",
        ),
        TriggerDefinition(
            signal=SignalName.RAINFALL_7D_MM,
            comparison=Comparison.AT_LEAST,
            threshold=60.0,
            saturation=180.0,
            weight=2.0,
            description="Runoff from heavy rain carries contamination into water supplies",
        ),
        TriggerDefinition(
            signal=SignalName.TEMPERATURE_MEAN_C,
            comparison=Comparison.AT_LEAST,
            threshold=28.0,
            saturation=34.0,
            weight=1.5,
            description="Heat accelerates bacterial growth in food and water",
        ),
    ),
    multipliers=(
        ContextMultiplier(
            condition=ContextCondition.FLOOD_PRONE,
            factor=1.1,
            description="District has a history of flooding",
        ),
    ),
    lag_window=LagWindow(minimum_days=3, maximum_days=14),
    vulnerable_group="Children under five",
)

RESPIRATORY_HEAT_ILLNESS_PATHWAY = PathwayDefinition(
    condition=HealthCondition.RESPIRATORY_HEAT_ILLNESS,
    driver=ClimateDriver.HARMATTAN_DUST,
    gate=GateDefinition(),
    triggers=(
        TriggerDefinition(
            signal=SignalName.TEMPERATURE_MAX_C,
            comparison=Comparison.AT_LEAST,
            threshold=38.0,
            saturation=44.0,
            weight=3.0,
            description="Extreme daytime heat drives heat exhaustion and heat stroke",
        ),
        TriggerDefinition(
            signal=SignalName.DUST_CONCENTRATION_UG_M3,
            comparison=Comparison.AT_LEAST,
            threshold=40.0,
            saturation=150.0,
            weight=2.5,
            description="Dust in the air inflames the airways",
        ),
        TriggerDefinition(
            signal=SignalName.PARTICULATE_MATTER_10_UG_M3,
            comparison=Comparison.AT_LEAST,
            threshold=80.0,
            saturation=250.0,
            weight=2.5,
            description="Particulate pollution exceeds safe breathing levels",
        ),
        TriggerDefinition(
            signal=SignalName.HUMIDITY_MEAN_PERCENT,
            comparison=Comparison.AT_MOST,
            threshold=25.0,
            saturation=10.0,
            weight=1.5,
            description="Dry air worsens asthma and airway irritation",
        ),
        TriggerDefinition(
            signal=SignalName.CONSECUTIVE_DRY_DAYS,
            comparison=Comparison.AT_LEAST,
            threshold=10.0,
            saturation=45.0,
            weight=1.0,
            description="A sustained dry spell keeps dust suspended in the air",
        ),
    ),
    lag_window=LagWindow(minimum_days=0, maximum_days=3),
    vulnerable_group="Older adults, young children and people with asthma",
)

TIER_ONE_PATHWAYS: tuple[PathwayDefinition, ...] = (
    MALARIA_PATHWAY,
    CHOLERA_PATHWAY,
    MENINGITIS_PATHWAY,
    DIARRHOEAL_DISEASE_PATHWAY,
    RESPIRATORY_HEAT_ILLNESS_PATHWAY,
)


DENGUE_PATHWAY = PathwayDefinition(
    condition=HealthCondition.DENGUE,
    driver=ClimateDriver.RAIN_FLOOD,
    gate=GateDefinition(),
    triggers=(
        TriggerDefinition(
            signal=SignalName.RAINFALL_7D_MM,
            comparison=Comparison.AT_LEAST,
            threshold=40.0,
            saturation=140.0,
            weight=2.5,
            description="Rain fills the containers Aedes mosquitoes breed in",
        ),
        TriggerDefinition(
            signal=SignalName.TEMPERATURE_MEAN_C,
            comparison=Comparison.AT_LEAST,
            threshold=26.0,
            saturation=31.0,
            weight=3.0,
            description="Warmth shortens the virus incubation period in the mosquito",
        ),
        TriggerDefinition(
            signal=SignalName.TEMPERATURE_MAX_C,
            comparison=Comparison.AT_LEAST,
            threshold=31.0,
            saturation=38.0,
            weight=2.0,
            description="Hot afternoons increase Aedes biting activity",
        ),
        TriggerDefinition(
            signal=SignalName.HUMIDITY_MEAN_PERCENT,
            comparison=Comparison.AT_LEAST,
            threshold=65.0,
            saturation=90.0,
            weight=2.0,
            description="Humid air extends adult mosquito lifespan",
        ),
        TriggerDefinition(
            signal=SignalName.STAGNANT_WATER_INDEX,
            comparison=Comparison.AT_LEAST,
            threshold=0.4,
            saturation=1.0,
            weight=2.0,
            description="Stored and standing water around homes breeds Aedes",
        ),
    ),
    lag_window=LagWindow(minimum_days=14, maximum_days=42),
    vulnerable_group="Adults and older children in dense urban areas",
)

TYPHOID_PATHWAY = PathwayDefinition(
    condition=HealthCondition.TYPHOID_FEVER,
    driver=ClimateDriver.RAIN_FLOOD,
    gate=GateDefinition(),
    triggers=(
        TriggerDefinition(
            signal=SignalName.RAINFALL_7D_MM,
            comparison=Comparison.AT_LEAST,
            threshold=70.0,
            saturation=200.0,
            weight=3.0,
            description="Runoff carries sewage into drinking water sources",
        ),
        TriggerDefinition(
            signal=SignalName.UNSAFE_WATER_RATIO,
            comparison=Comparison.AT_LEAST,
            threshold=0.3,
            saturation=1.0,
            weight=3.0,
            description="Households draw water from unprotected sources",
        ),
        TriggerDefinition(
            signal=SignalName.POOR_SANITATION_INDEX,
            comparison=Comparison.AT_LEAST,
            threshold=0.4,
            saturation=1.0,
            weight=2.5,
            description="Weak sanitation lets Salmonella typhi reach the water supply",
        ),
        TriggerDefinition(
            signal=SignalName.TEMPERATURE_MEAN_C,
            comparison=Comparison.AT_LEAST,
            threshold=27.0,
            saturation=33.0,
            weight=1.5,
            description="Warm water favours bacterial survival",
        ),
    ),
    lag_window=LagWindow(minimum_days=7, maximum_days=21),
    vulnerable_group="School-age children and young adults",
)

SCHISTOSOMIASIS_PATHWAY = PathwayDefinition(
    condition=HealthCondition.SCHISTOSOMIASIS,
    driver=ClimateDriver.RAIN_FLOOD,
    gate=GateDefinition(),
    triggers=(
        TriggerDefinition(
            signal=SignalName.RAINFALL_14D_MM,
            comparison=Comparison.AT_LEAST,
            threshold=90.0,
            saturation=260.0,
            weight=3.0,
            description="Sustained rain expands the surface water snails live in",
        ),
        TriggerDefinition(
            signal=SignalName.TEMPERATURE_MEAN_C,
            comparison=Comparison.AT_LEAST,
            threshold=25.0,
            saturation=31.0,
            weight=2.5,
            description="Warm water speeds parasite development inside the snail",
        ),
        TriggerDefinition(
            signal=SignalName.STAGNANT_WATER_INDEX,
            comparison=Comparison.AT_LEAST,
            threshold=0.4,
            saturation=1.0,
            weight=3.0,
            description="Slow-moving water is where transmission happens",
        ),
    ),
    lag_window=LagWindow(minimum_days=28, maximum_days=84),
    vulnerable_group="Children who swim, fish or fetch water",
)

LASSA_FEVER_PATHWAY = PathwayDefinition(
    condition=HealthCondition.LASSA_FEVER,
    driver=ClimateDriver.HARMATTAN_DUST,
    gate=GateDefinition(permitted_seasons=(Season.DRY,)),
    triggers=(
        TriggerDefinition(
            signal=SignalName.CONSECUTIVE_DRY_DAYS,
            comparison=Comparison.AT_LEAST,
            threshold=21.0,
            saturation=70.0,
            weight=3.0,
            description="A long dry spell drives rodents into homes and food stores",
        ),
        TriggerDefinition(
            signal=SignalName.HUMIDITY_MEAN_PERCENT,
            comparison=Comparison.AT_MOST,
            threshold=40.0,
            saturation=15.0,
            weight=2.5,
            description="Dry conditions concentrate rodents around stored grain",
        ),
        TriggerDefinition(
            signal=SignalName.TEMPERATURE_MAX_C,
            comparison=Comparison.AT_LEAST,
            threshold=33.0,
            saturation=41.0,
            weight=1.5,
            description="Peak dry-season heat coincides with the Lassa season",
        ),
    ),
    lag_window=LagWindow(minimum_days=7, maximum_days=21),
    vulnerable_group="Rural households storing grain indoors",
)

YELLOW_FEVER_PATHWAY = PathwayDefinition(
    condition=HealthCondition.YELLOW_FEVER,
    driver=ClimateDriver.RAIN_FLOOD,
    gate=GateDefinition(),
    triggers=(
        TriggerDefinition(
            signal=SignalName.RAINFALL_7D_MM,
            comparison=Comparison.AT_LEAST,
            threshold=85.0,
            saturation=200.0,
            weight=3.0,
            description="Sustained heavy rain creates the breeding sites vectors need",
        ),
        TriggerDefinition(
            signal=SignalName.HUMIDITY_MEAN_PERCENT,
            comparison=Comparison.AT_LEAST,
            threshold=80.0,
            saturation=95.0,
            weight=2.5,
            description="High humidity supports vector survival",
        ),
        TriggerDefinition(
            signal=SignalName.TEMPERATURE_MEAN_C,
            comparison=Comparison.AT_LEAST,
            threshold=24.0,
            saturation=29.0,
            weight=2.0,
            description="Temperature is in the band for viral replication in the vector",
        ),
        TriggerDefinition(
            signal=SignalName.TEMPERATURE_MEAN_C,
            comparison=Comparison.AT_MOST,
            threshold=32.0,
            saturation=28.0,
            weight=1.0,
            description="Temperature is below the ceiling for vector survival",
        ),
        TriggerDefinition(
            signal=SignalName.RAINFALL_14D_MM,
            comparison=Comparison.AT_LEAST,
            threshold=140.0,
            saturation=320.0,
            weight=2.5,
            description="A prolonged wet spell sustains vector populations",
        ),
    ),
    lag_window=LagWindow(minimum_days=21, maximum_days=42),
    vulnerable_group="Unvaccinated people of any age",
)

LEPTOSPIROSIS_PATHWAY = PathwayDefinition(
    condition=HealthCondition.LEPTOSPIROSIS,
    driver=ClimateDriver.RAIN_FLOOD,
    gate=GateDefinition(),
    triggers=(
        TriggerDefinition(
            signal=SignalName.RAINFALL_7D_MM,
            comparison=Comparison.AT_LEAST,
            threshold=100.0,
            saturation=250.0,
            weight=3.5,
            description="Flood water carries rodent urine into contact with people",
        ),
        TriggerDefinition(
            signal=SignalName.RAINFALL_14D_MM,
            comparison=Comparison.AT_LEAST,
            threshold=150.0,
            saturation=350.0,
            weight=2.0,
            description="Prolonged flooding keeps contaminated water on the ground",
        ),
        TriggerDefinition(
            signal=SignalName.TEMPERATURE_MEAN_C,
            comparison=Comparison.AT_LEAST,
            threshold=25.0,
            saturation=31.0,
            weight=1.5,
            description="Warm water keeps the bacterium viable for longer",
        ),
    ),
    multipliers=(
        ContextMultiplier(
            condition=ContextCondition.COASTAL,
            factor=1.1,
            description="Coastal district: storm surge leaves standing water people wade through",
        ),
        ContextMultiplier(
            condition=ContextCondition.FLOOD_PRONE,
            factor=1.2,
            description="District has a history of flooding",
        ),
    ),
    lag_window=LagWindow(minimum_days=5, maximum_days=14),
    vulnerable_group="People wading through flood water, farmers and refuse workers",
)

TRACHOMA_PATHWAY = PathwayDefinition(
    condition=HealthCondition.TRACHOMA,
    driver=ClimateDriver.HARMATTAN_DUST,
    gate=GateDefinition(permitted_seasons=(Season.DRY,)),
    triggers=(
        TriggerDefinition(
            signal=SignalName.DUST_CONCENTRATION_UG_M3,
            comparison=Comparison.AT_LEAST,
            threshold=40.0,
            saturation=160.0,
            weight=3.0,
            description="Airborne dust irritates the eyes and spreads infection",
        ),
        TriggerDefinition(
            signal=SignalName.HUMIDITY_MEAN_PERCENT,
            comparison=Comparison.AT_MOST,
            threshold=35.0,
            saturation=12.0,
            weight=2.5,
            description="Dry air and scarce washing water raise transmission",
        ),
        TriggerDefinition(
            signal=SignalName.CONSECUTIVE_DRY_DAYS,
            comparison=Comparison.AT_LEAST,
            threshold=20.0,
            saturation=70.0,
            weight=2.0,
            description="Extended drought reduces the water available for face washing",
        ),
    ),
    lag_window=LagWindow(minimum_days=56, maximum_days=168),
    vulnerable_group="Young children and the women who care for them",
)

HEAT_STROKE_PATHWAY = PathwayDefinition(
    condition=HealthCondition.HEAT_STROKE,
    driver=ClimateDriver.EXTREME_HEAT,
    gate=GateDefinition(),
    triggers=(
        TriggerDefinition(
            signal=SignalName.TEMPERATURE_MAX_C,
            comparison=Comparison.AT_LEAST,
            threshold=37.0,
            saturation=45.0,
            weight=3.5,
            description="Daytime heat is at the level that causes heat illness",
        ),
        TriggerDefinition(
            signal=SignalName.TEMPERATURE_MEAN_C,
            comparison=Comparison.AT_LEAST,
            threshold=30.0,
            saturation=36.0,
            weight=2.5,
            description="Nights stay warm enough to prevent the body cooling down",
        ),
        TriggerDefinition(
            signal=SignalName.HUMIDITY_MEAN_PERCENT,
            comparison=Comparison.AT_LEAST,
            threshold=60.0,
            saturation=85.0,
            weight=1.5,
            description="Humidity stops sweat evaporating, so the body cannot shed heat",
        ),
    ),
    lag_window=LagWindow(minimum_days=0, maximum_days=3),
    vulnerable_group="Outdoor workers, older adults and infants",
)

TIER_TWO_PATHWAYS: tuple[PathwayDefinition, ...] = (
    DENGUE_PATHWAY,
    TYPHOID_PATHWAY,
    SCHISTOSOMIASIS_PATHWAY,
    LASSA_FEVER_PATHWAY,
    YELLOW_FEVER_PATHWAY,
    LEPTOSPIROSIS_PATHWAY,
    TRACHOMA_PATHWAY,
    HEAT_STROKE_PATHWAY,
)

ALL_PATHWAYS: tuple[PathwayDefinition, ...] = TIER_ONE_PATHWAYS + TIER_TWO_PATHWAYS


AIR_POLLUTION_PATHWAY = PathwayDefinition(
    condition=HealthCondition.AIR_POLLUTION_CARDIORESPIRATORY,
    driver=ClimateDriver.AIR_POLLUTION,
    gate=GateDefinition(),
    triggers=(
        TriggerDefinition(
            signal=SignalName.PARTICULATE_MATTER_10_UG_M3,
            comparison=Comparison.AT_LEAST,
            threshold=50.0,
            saturation=150.0,
            weight=3.0,
            description="Particulate matter is above the WHO 24-hour guideline",
        ),
        TriggerDefinition(
            signal=SignalName.PARTICULATE_MATTER_10_UG_M3,
            comparison=Comparison.AT_LEAST,
            threshold=100.0,
            saturation=300.0,
            weight=2.5,
            description=("Particulate matter is at a level that drives hospital admissions"),
        ),
        TriggerDefinition(
            signal=SignalName.DUST_CONCENTRATION_UG_M3,
            comparison=Comparison.AT_LEAST,
            threshold=30.0,
            saturation=120.0,
            weight=2.0,
            description="Airborne dust is adding to the particulate load",
        ),
        TriggerDefinition(
            signal=SignalName.CONSECUTIVE_DRY_DAYS,
            comparison=Comparison.AT_LEAST,
            threshold=7.0,
            saturation=40.0,
            weight=1.5,
            description="No rain has washed particulates out of the air",
        ),
        TriggerDefinition(
            signal=SignalName.TEMPERATURE_MAX_C,
            comparison=Comparison.AT_LEAST,
            threshold=33.0,
            saturation=41.0,
            weight=1.0,
            description="Heat compounds the cardiovascular strain of polluted air",
        ),
    ),
    lag_window=LagWindow(minimum_days=3, maximum_days=21),
    vulnerable_group=(
        "Adults over fifty, children under five, and people with heart or lung disease"
    ),
)

TIER_TWO_PATHWAYS = (*TIER_TWO_PATHWAYS, AIR_POLLUTION_PATHWAY)
ALL_PATHWAYS = (*TIER_ONE_PATHWAYS, *TIER_TWO_PATHWAYS)


CHILD_UNDERNUTRITION_PATHWAY = PathwayDefinition(
    condition=HealthCondition.CHILD_UNDERNUTRITION,
    driver=ClimateDriver.DROUGHT,
    gate=GateDefinition(),
    triggers=(
        TriggerDefinition(
            signal=SignalName.RAINFALL_14D_MM,
            comparison=Comparison.AT_MOST,
            threshold=15.0,
            saturation=0.0,
            weight=3.0,
            description="Rainfall deficit over two weeks threatens the growing season",
        ),
        TriggerDefinition(
            signal=SignalName.CONSECUTIVE_DRY_DAYS,
            comparison=Comparison.AT_LEAST,
            threshold=21.0,
            saturation=90.0,
            weight=3.0,
            description="A prolonged dry spell puts the harvest and household income at risk",
        ),
        TriggerDefinition(
            signal=SignalName.TEMPERATURE_MAX_C,
            comparison=Comparison.AT_LEAST,
            threshold=36.0,
            saturation=44.0,
            weight=1.5,
            description="Extreme heat compounds crop stress and water scarcity",
        ),
    ),
    lag_window=LagWindow(minimum_days=90, maximum_days=365),
    vulnerable_group="Children under five, most acutely in the northern regions",
)

MATERNAL_HEAT_PATHWAY = PathwayDefinition(
    condition=HealthCondition.MATERNAL_HEAT_OUTCOMES,
    driver=ClimateDriver.EXTREME_HEAT,
    gate=GateDefinition(),
    triggers=(
        TriggerDefinition(
            signal=SignalName.TEMPERATURE_MAX_C,
            comparison=Comparison.AT_LEAST,
            threshold=35.0,
            saturation=43.0,
            weight=3.0,
            description="Daytime heat is at the level linked to raised miscarriage risk",
        ),
        TriggerDefinition(
            signal=SignalName.TEMPERATURE_MEAN_C,
            comparison=Comparison.AT_LEAST,
            threshold=29.0,
            saturation=35.0,
            weight=2.5,
            description="Nights stay warm, so there is no overnight recovery from heat strain",
        ),
        TriggerDefinition(
            signal=SignalName.HUMIDITY_MEAN_PERCENT,
            comparison=Comparison.AT_LEAST,
            threshold=60.0,
            saturation=85.0,
            weight=2.0,
            description=("Humidity prevents sweat evaporating, which raises effective heat load"),
        ),
    ),
    lag_window=LagWindow(minimum_days=3, maximum_days=28),
    vulnerable_group="Pregnant women, especially those working outdoors",
)

TIER_TWO_PATHWAYS = (
    *TIER_TWO_PATHWAYS,
    CHILD_UNDERNUTRITION_PATHWAY,
    MATERNAL_HEAT_PATHWAY,
)
ALL_PATHWAYS = (*TIER_ONE_PATHWAYS, *TIER_TWO_PATHWAYS)

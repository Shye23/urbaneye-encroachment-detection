"""
UrbanEye - Final Spatial Analysis
==================================

Purpose:
    Combine satellite-derived change polygons with cadastral parcels,
    roads, and buildings to determine whether detected changes have
    spatial evidence of potential encroachment.

Important:
    Satellite change != encroachment.

    This module only identifies:
        - potential public-space encroachment
        - potential government-land encroachment
        - potential public-land encroachment
        - potential parcel-boundary encroachment
        - changes with no encroachment evidence
        - changes requiring verification

    It does NOT determine legal encroachment.

Coordinate system:
    Expected UTM Zone 43N / EPSG:32643

Input:
    outputs/gis/AOI10_change_polygons.gpkg
    data/cadastral/synthetic_cadastral.gpkg
    data/cadastral/synthetic_roads.gpkg
    data/cadastral/synthetic_buildings.gpkg

Output:
    outputs/gis/AOI10_spatial_analysis.gpkg
    outputs/gis/AOI10_spatial_analysis.csv
"""

import os
import warnings
import sys

import geopandas as gpd
import pandas as pd
import numpy as np

from shapely.geometry import GeometryCollection
from shapely.ops import unary_union


# ============================================================
# CONFIGURATION
# ============================================================
sys.path.insert(0,r"E:\UrbanEye")
ROOT = r"E:\UrbanEye"

CHANGE_FILE = os.path.join(
    ROOT,
    "outputs",
    "gis",
    "AOI10_change_polygons.gpkg"
)

PARCEL_FILE = os.path.join(
    ROOT,
    "processed_data",
    "cadastral",
    "synthetic_cadastral.gpkg"
)

ROAD_FILE = os.path.join(
    ROOT,
    "processed_data",
    "cadastral",
    "synthetic_roads.gpkg"
)

BUILDING_FILE = os.path.join(
    ROOT,
    "processed_data",
    "cadastral",
    "synthetic_buildings.gpkg"
)

OUTPUT_DIR = os.path.join(
    ROOT,
    "outputs",
    "gis"
)

OUTPUT_GPKG = os.path.join(
    OUTPUT_DIR,
    "AOI10_spatial_analysis.gpkg"
)

OUTPUT_CSV = os.path.join(
    OUTPUT_DIR,
    "AOI10_spatial_analysis.csv"
)

EXPECTED_CRS = "EPSG:32643"


# ============================================================
# ANALYSIS THRESHOLDS
# ============================================================

# Ignore extremely tiny geometric slivers.
MIN_OVERLAP_AREA = 1.0

# Meaningful government/public intrusion.
MIN_LAND_INTRUSION_AREA = 50.0
MIN_LAND_INTRUSION_PERCENT = 10.0

# Meaningful road overlap.
MIN_ROAD_INTRUSION_AREA = 25.0
MIN_ROAD_INTRUSION_PERCENT = 5.0

# Meaningful building overlap.
MIN_BUILDING_OVERLAP_AREA = 10.0

# If a change is explained by less than this percentage of
# a single parcel, it should not automatically be considered
# a normal parcel-contained change.
PRIMARY_PARCEL_THRESHOLD = 90.0

# Minimum percentage of a change that must be covered by
# cadastral parcels before we consider the parcel evidence
# reasonably complete.
MIN_PARCEL_COVERAGE_PERCENT = 90.0


# ============================================================
# CLASSIFICATION LABELS
# ============================================================

ENCROACHMENT_CLASSES = [
    "Potential Public-Space Encroachment",
    "Potential Government-Land Encroachment",
    "Potential Public-Land Encroachment",
    "Potential Parcel-Boundary Encroachment",
]

NON_ENCROACHMENT_CLASSES = [
    "Change Detected, No Encroachment Evidence",
    "Normal Building Change",
    "Change on Government Land",
    "Change on Public Land",
]

SPECIAL_CLASSES = [
    "Requires Verification",
]


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def print_header(title):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def safe_float(value, default=0.0):
    """
    Safely convert values to float.
    Handles NaN, None and invalid strings.
    """
    try:
        value = float(value)

        if not np.isfinite(value):
            return default

        return value

    except (TypeError, ValueError):
        return default


def clean_category(value):
    """
    Normalize land-category values.
    """
    if value is None:
        return ""

    if pd.isna(value):
        return ""

    value = str(value).strip().upper()

    if value in ["NAN", "NONE", "NULL", ""]:
        return ""

    return value


def repair_geometry(geometry):
    """
    Attempt to repair invalid geometries.
    """
    if geometry is None:
        return None

    if geometry.is_empty:
        return None

    if geometry.is_valid:
        return geometry

    try:
        repaired = geometry.buffer(0)

        if repaired.is_empty:
            return None

        return repaired

    except Exception:
        return None


def clean_geodataframe(gdf, name):
    """
    Clean geometries and remove empty/invalid records.
    """
    original_count = len(gdf)

    gdf = gdf.copy()

    gdf["geometry"] = gdf["geometry"].apply(
        repair_geometry
    )

    gdf = gdf[
        gdf["geometry"].notna()
        &
        (~gdf.geometry.is_empty)
    ].copy()

    removed = original_count - len(gdf)

    if removed > 0:
        print(
            f"{name}: removed {removed} invalid/empty geometries."
        )

    return gdf


def check_required_file(path, name):
    """
    Stop with a clear error if an input file is missing.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"\n{name} not found:\n{path}"
        )


def load_layer(path, layer_name, description):
    """
    Load a specific GeoPackage layer.
    """
    check_required_file(path, description)

    try:
        gdf = gpd.read_file(
            path,
            layer=layer_name
        )

    except Exception as exc:
        raise RuntimeError(
            f"\nCould not load {description}.\n"
            f"File: {path}\n"
            f"Layer: {layer_name}\n"
            f"Error: {exc}"
        )

    if gdf.empty:
        raise ValueError(
            f"\n{description} is empty:\n{path}"
        )

    if gdf.crs is None:
        raise ValueError(
            f"\n{description} has no CRS defined:\n{path}"
        )

    return gdf


def prepare_crs(gdf, name):
    """
    Ensure all datasets use the project CRS.
    """
    if gdf.crs is None:
        raise ValueError(
            f"{name} does not have a CRS."
        )

    if str(gdf.crs) != EXPECTED_CRS:
        print(
            f"{name}: reprojecting "
            f"{gdf.crs} -> {EXPECTED_CRS}"
        )

        gdf = gdf.to_crs(EXPECTED_CRS)

    return gdf


def calculate_percentage(numerator, denominator):
    """
    Safe percentage calculation.
    """
    if denominator <= 0:
        return 0.0

    return (numerator / denominator) * 100.0


# ============================================================
# LOAD DATA
# ============================================================

def load_all_data(
    change_file=CHANGE_FILE,
    parcel_file=PARCEL_FILE,
    road_file=ROAD_FILE,
    building_file=BUILDING_FILE,
):

    print_header(
        "Loading UrbanEye spatial data"
    )

    # --------------------------------------------------------
    # Change polygons
    # --------------------------------------------------------

    print("\nLoading change polygons...")

    change = load_layer(
        change_file,
        "change_polygons",
        "Change polygons"
    )

    change = prepare_crs(
        change,
        "Change polygons"
    )

    change = clean_geodataframe(
        change,
        "Change polygons"
    )

    print(
        f"Change polygons: {len(change)}"
    )

    print(
        f"Change polygons CRS: {change.crs}"
    )

    # --------------------------------------------------------
    # Parcels
    # --------------------------------------------------------

    print("\nLoading cadastral parcels...")

    parcels = load_layer(
        parcel_file,
        "parcels",
        "Cadastral parcels"
    )

    parcels = prepare_crs(
        parcels,
        "Cadastral parcels"
    )

    parcels = clean_geodataframe(
        parcels,
        "Cadastral parcels"
    )

    print(
        f"Parcels: {len(parcels)}"
    )

    print(
        f"Parcels CRS: {parcels.crs}"
    )

    # --------------------------------------------------------
    # Roads
    # --------------------------------------------------------

    print("\nLoading roads...")

    roads = load_layer(
        road_file,
        "roads",
        "Roads"
    )

    roads = prepare_crs(
        roads,
        "Roads"
    )

    roads = clean_geodataframe(
        roads,
        "Roads"
    )

    print(
        f"Roads: {len(roads)}"
    )

    print(
        f"Roads CRS: {roads.crs}"
    )

    # --------------------------------------------------------
    # Buildings
    # --------------------------------------------------------

    print("\nLoading buildings...")

    buildings = load_layer(
        building_file,
        "buildings",
        "Buildings"
    )

    buildings = prepare_crs(
        buildings,
        "Buildings"
    )

    buildings = clean_geodataframe(
        buildings,
        "Buildings"
    )

    print(
        f"Buildings: {len(buildings)}"
    )

    print(
        f"Buildings CRS: {buildings.crs}"
    )

    return (
        change,
        parcels,
        roads,
        buildings
    )


# ============================================================
# PARCEL ANALYSIS
# ============================================================

def analyze_parcels(change, parcels):

    print_header(
        "Analyzing parcel intersections"
    )

    # Keep only required parcel fields.
    parcel_columns = [
        col
        for col in [
            "parcel_id",
            "land_category",
            "land_use",
            "authority"
        ]
        if col in parcels.columns
    ]

    parcel_data = parcels[
        parcel_columns + ["geometry"]
    ].copy()

    results = []

    for index, change_row in change.iterrows():

        geometry = change_row.geometry

        change_area = safe_float(
            geometry.area
        )

        intersections = []

        # Spatial index candidate filtering.
        try:
            candidate_indices = list(
                parcels.sindex.query(
                    geometry,
                    predicate="intersects"
                )
            )

        except Exception:
            candidate_indices = list(
                range(len(parcels))
            )

        for parcel_index in candidate_indices:

            parcel = parcels.iloc[parcel_index]

            try:
                if not geometry.intersects(
                    parcel.geometry
                ):
                    continue

                intersection = geometry.intersection(
                    parcel.geometry
                )

                if intersection.is_empty:
                    continue

                overlap_area = safe_float(
                    intersection.area
                )

                if overlap_area < MIN_OVERLAP_AREA:
                    continue

                category = clean_category(
                    parcel.get(
                        "land_category",
                        ""
                    )
                )

                intersections.append({
                    "parcel_id": parcel.get(
                        "parcel_id",
                        None
                    ),
                    "land_category": category,
                    "land_use": parcel.get(
                        "land_use",
                        None
                    ),
                    "authority": parcel.get(
                        "authority",
                        None
                    ),
                    "overlap_area": overlap_area,
                })

            except Exception:
                continue

        # ----------------------------------------------------
        # No parcel intersection
        # ----------------------------------------------------

        if not intersections:

            results.append({
                "primary_parcel_id": None,
                "primary_land_category": None,
                "primary_land_use": None,
                "primary_authority": None,
                "parcel_count": 0,
                "parcel_overlap_area_m2": 0.0,
                "parcel_coverage_pct": 0.0,
                "primary_parcel_overlap_m2": 0.0,
                "primary_parcel_overlap_pct": 0.0,
                "government_overlap_m2": 0.0,
                "public_overlap_m2": 0.0,
            })

            continue

        # ----------------------------------------------------
        # Sort by overlap
        # ----------------------------------------------------

        intersections.sort(
            key=lambda x: x["overlap_area"],
            reverse=True
        )

        primary = intersections[0]

        total_parcel_overlap = sum(
            item["overlap_area"]
            for item in intersections
        )

        # Do not allow overlapping parcel geometries to produce
        # more than 100% coverage.
        parcel_coverage_area = min(
            total_parcel_overlap,
            change_area
        )

        parcel_coverage_pct = calculate_percentage(
            parcel_coverage_area,
            change_area
        )

        primary_overlap_pct = calculate_percentage(
            primary["overlap_area"],
            change_area
        )

        government_overlap = sum(
            item["overlap_area"]
            for item in intersections
            if item["land_category"] == "GOVERNMENT"
        )

        public_overlap = sum(
            item["overlap_area"]
            for item in intersections
            if item["land_category"] == "PUBLIC"
        )

        results.append({
            "primary_parcel_id": primary[
                "parcel_id"
            ],
            "primary_land_category": primary[
                "land_category"
            ],
            "primary_land_use": primary[
                "land_use"
            ],
            "primary_authority": primary[
                "authority"
            ],
            "parcel_count": len(
                intersections
            ),
            "parcel_overlap_area_m2": parcel_coverage_area,
            "parcel_coverage_pct": parcel_coverage_pct,
            "primary_parcel_overlap_m2": primary[
                "overlap_area"
            ],
            "primary_parcel_overlap_pct": primary_overlap_pct,
            "government_overlap_m2": government_overlap,
            "public_overlap_m2": public_overlap,
        })

    return pd.DataFrame(results)


# ============================================================
# ROAD ANALYSIS
# ============================================================

def analyze_roads(change, roads):

    print_header(
        "Analyzing road intersections"
    )

    results = []

    for index, change_row in change.iterrows():

        geometry = change_row.geometry

        road_overlap = 0.0

        try:
            candidate_indices = list(
                roads.sindex.query(
                    geometry,
                    predicate="intersects"
                )
            )

        except Exception:
            candidate_indices = list(
                range(len(roads))
            )

        for road_index in candidate_indices:

            road = roads.iloc[road_index]

            try:
                if not geometry.intersects(
                    road.geometry
                ):
                    continue

                intersection = geometry.intersection(
                    road.geometry
                )

                if intersection.is_empty:
                    continue

                area = safe_float(
                    intersection.area
                )

                if area >= MIN_OVERLAP_AREA:
                    road_overlap += area

            except Exception:
                continue

        # Prevent accidental >100% due to overlapping
        # synthetic road geometries.
        road_overlap = min(
            road_overlap,
            safe_float(geometry.area)
        )

        results.append({
            "road_overlap_m2": road_overlap
        })

    return pd.DataFrame(results)


# ============================================================
# BUILDING ANALYSIS
# ============================================================

def analyze_buildings(change, buildings):

    print_header(
        "Analyzing building intersections"
    )

    results = []

    for index, change_row in change.iterrows():

        geometry = change_row.geometry

        building_overlap = 0.0
        building_count = 0

        try:
            candidate_indices = list(
                buildings.sindex.query(
                    geometry,
                    predicate="intersects"
                )
            )

        except Exception:
            candidate_indices = list(
                range(len(buildings))
            )

        for building_index in candidate_indices:

            building = buildings.iloc[
                building_index
            ]

            try:
                if not geometry.intersects(
                    building.geometry
                ):
                    continue

                intersection = geometry.intersection(
                    building.geometry
                )

                if intersection.is_empty:
                    continue

                area = safe_float(
                    intersection.area
                )

                if area < MIN_OVERLAP_AREA:
                    continue

                building_overlap += area

                if area >= MIN_BUILDING_OVERLAP_AREA:
                    building_count += 1

            except Exception:
                continue

        building_overlap = min(
            building_overlap,
            safe_float(geometry.area)
        )

        results.append({
            "building_overlap_m2": building_overlap,
            "building_count": building_count
        })

    return pd.DataFrame(results)


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_change(row):

    change_area = safe_float(
        row.get("change_area_m2", 0)
    )

    if change_area <= 0:
        return "Requires Verification"

    primary_category = clean_category(
        row.get(
            "primary_land_category",
            ""
        )
    )

    parcel_count = int(
        safe_float(
            row.get("parcel_count", 0)
        )
    )

    parcel_coverage_pct = safe_float(
        row.get(
            "parcel_coverage_pct",
            0
        )
    )

    primary_parcel_overlap_pct = safe_float(
        row.get(
            "primary_parcel_overlap_pct",
            0
        )
    )

    road_overlap = safe_float(
        row.get(
            "road_overlap_m2",
            0
        )
    )

    government_overlap = safe_float(
        row.get(
            "government_overlap_m2",
            0
        )
    )

    public_overlap = safe_float(
        row.get(
            "public_overlap_m2",
            0
        )
    )

    building_overlap = safe_float(
        row.get(
            "building_overlap_m2",
            0
        )
    )

    road_pct = calculate_percentage(
        road_overlap,
        change_area
    )

    government_pct = calculate_percentage(
        government_overlap,
        change_area
    )

    public_pct = calculate_percentage(
        public_overlap,
        change_area
    )

    # ========================================================
    # IMPORTANT:
    # No parcel means we cannot determine ownership.
    # A road intersection alone does not prove encroachment.
    # ========================================================

    has_primary_parcel = (
        primary_category != ""
        and
        row.get(
            "primary_parcel_id",
            None
        ) is not None
        and
        not pd.isna(
            row.get(
                "primary_parcel_id",
                None
            )
        )
    )

    # ========================================================
    # 1. PUBLIC-SPACE / ROAD ENCROACHMENT
    #
    # Only flag when the change is associated with a PRIVATE
    # parcel. A change directly on a road may simply represent
    # road maintenance, resurfacing, widening, etc.
    # ========================================================

    significant_road_overlap = (
        road_overlap >= MIN_ROAD_INTRUSION_AREA
        and
        road_pct >= MIN_ROAD_INTRUSION_PERCENT
    )

    if significant_road_overlap:

        if primary_category == "PRIVATE":

            return (
                "Potential Public-Space "
                "Encroachment"
            )

        if not has_primary_parcel:

            return "Requires Verification"

    # ========================================================
    # 2. GOVERNMENT-LAND ENCROACHMENT
    #
    # Government overlap is only treated as encroachment
    # when the primary change location is PRIVATE land.
    # ========================================================

    significant_government_overlap = (
        government_overlap >= MIN_LAND_INTRUSION_AREA
        and
        government_pct >= MIN_LAND_INTRUSION_PERCENT
    )

    if significant_government_overlap:

        if primary_category == "PRIVATE":

            return (
                "Potential Government-Land "
                "Encroachment"
            )

    # ========================================================
    # 3. PUBLIC-LAND ENCROACHMENT
    # ========================================================

    significant_public_overlap = (
        public_overlap >= MIN_LAND_INTRUSION_AREA
        and
        public_pct >= MIN_LAND_INTRUSION_PERCENT
    )

    if significant_public_overlap:

        if primary_category == "PRIVATE":

            return (
                "Potential Public-Land "
                "Encroachment"
            )

    # ========================================================
    # 4. INCOMPLETE CADASTRAL COVERAGE
    #
    # If the change cannot be sufficiently explained by
    # cadastral parcels, do not invent an ownership conclusion.
    # ========================================================

    if not has_primary_parcel:

        return "Requires Verification"

    if (
        parcel_coverage_pct
        < MIN_PARCEL_COVERAGE_PERCENT
    ):

        return "Requires Verification"

    # ========================================================
    # 5. PARCEL-BOUNDARY ENCROACHMENT
    #
    # A private change crossing multiple parcels can indicate
    # possible boundary intrusion.
    # ========================================================

    if (
        primary_category == "PRIVATE"
        and
        parcel_count > 1
        and
        primary_parcel_overlap_pct
        < PRIMARY_PARCEL_THRESHOLD
    ):

        return (
            "Potential Parcel-Boundary "
            "Encroachment"
        )

    # ========================================================
    # 6. NORMAL BUILDING CHANGE
    #
    # Building overlap alone does NOT mean encroachment.
    # ========================================================

    if (
        building_overlap
        >= MIN_BUILDING_OVERLAP_AREA
    ):

        if primary_category == "PRIVATE":

            return "Normal Building Change"

        if primary_category == "GOVERNMENT":

            return "Change on Government Land"

        if primary_category == "PUBLIC":

            return "Change on Public Land"

    # ========================================================
    # 7. CHANGE ON GOVERNMENT LAND
    # ========================================================

    if primary_category == "GOVERNMENT":

        return (
            "Change on Government Land"
        )

    # ========================================================
    # 8. CHANGE ON PUBLIC LAND
    # ========================================================

    if primary_category == "PUBLIC":

        return (
            "Change on Public Land"
        )

    # ========================================================
    # 9. PRIVATE CHANGE WITH NO ENCROACHMENT EVIDENCE
    # ========================================================

    if primary_category == "PRIVATE":

        return (
            "Change Detected, "
            "No Encroachment Evidence"
        )

    # ========================================================
    # 10. FALLBACK
    # ========================================================

    return "Requires Verification"


# ============================================================
# EVIDENCE SUMMARY
# ============================================================

def generate_evidence_summary(row):

    classification = row[
        "classification"
    ]

    evidence = []

    road_pct = safe_float(
        row.get(
            "road_overlap_pct",
            0
        )
    )

    government_pct = safe_float(
        row.get(
            "government_overlap_pct",
            0
        )
    )

    public_pct = safe_float(
        row.get(
            "public_overlap_pct",
            0
        )
    )

    building_pct = safe_float(
        row.get(
            "building_overlap_pct",
            0
        )
    )

    parcel_count = int(
        safe_float(
            row.get(
                "parcel_count",
                0
            )
        )
    )

    primary_category = clean_category(
        row.get(
            "primary_land_category",
            ""
        )
    )

    if road_pct > 0:
        evidence.append(
            f"road overlap {road_pct:.1f}%"
        )

    if government_pct > 0:
        evidence.append(
            f"government land overlap "
            f"{government_pct:.1f}%"
        )

    if public_pct > 0:
        evidence.append(
            f"public land overlap "
            f"{public_pct:.1f}%"
        )

    if building_pct > 0:
        evidence.append(
            f"building overlap "
            f"{building_pct:.1f}%"
        )

    if parcel_count > 1:
        evidence.append(
            f"{parcel_count} parcels intersected"
        )

    if primary_category:
        evidence.append(
            f"primary land category "
            f"{primary_category}"
        )

    if not evidence:
        evidence.append(
            "insufficient spatial evidence"
        )

    evidence_text = "; ".join(
        evidence
    )

    if classification in ENCROACHMENT_CLASSES:

        return (
            f"{classification}. "
            f"Spatial evidence: "
            f"{evidence_text}. "
            f"Requires field/legal verification."
        )

    if classification == "Requires Verification":

        return (
            "Insufficient or ambiguous "
            "spatial evidence. "
            f"Observed: {evidence_text}."
        )

    return (
        f"{classification}. "
        f"Observed: {evidence_text}."
    )


# ============================================================
# COMBINE RESULTS
# ============================================================

def combine_analysis(
    change,
    parcel_results,
    road_results,
    building_results
):

    print_header(
        "Combining spatial evidence"
    )

    # --------------------------------------------------------
    # Reset indexes to guarantee one-to-one alignment.
    # --------------------------------------------------------

    change = change.reset_index(
        drop=True
    )

    parcel_results = parcel_results.reset_index(
        drop=True
    )

    road_results = road_results.reset_index(
        drop=True
    )

    building_results = building_results.reset_index(
        drop=True
    )

    if not (
        len(change)
        ==
        len(parcel_results)
        ==
        len(road_results)
        ==
        len(building_results)
    ):
        raise ValueError(
            "Spatial analysis result lengths "
            "do not match."
        )

    # --------------------------------------------------------
    # Start with change polygons.
    # --------------------------------------------------------

    result = change.copy()

    # --------------------------------------------------------
    # Calculate exact change area.
    # --------------------------------------------------------

    result[
        "change_area_m2"
    ] = result.geometry.area

    # --------------------------------------------------------
    # Merge parcel evidence.
    # --------------------------------------------------------

    result = pd.concat(
        [
            result.reset_index(drop=True),
            parcel_results,
            road_results,
            building_results
        ],
        axis=1
    )

    # --------------------------------------------------------
    # Calculate percentages.
    # --------------------------------------------------------

    result[
        "road_overlap_pct"
    ] = result.apply(
        lambda row: calculate_percentage(
            safe_float(
                row["road_overlap_m2"]
            ),
            safe_float(
                row["change_area_m2"]
            )
        ),
        axis=1
    )

    result[
        "government_overlap_pct"
    ] = result.apply(
        lambda row: calculate_percentage(
            safe_float(
                row["government_overlap_m2"]
            ),
            safe_float(
                row["change_area_m2"]
            )
        ),
        axis=1
    )

    result[
        "public_overlap_pct"
    ] = result.apply(
        lambda row: calculate_percentage(
            safe_float(
                row["public_overlap_m2"]
            ),
            safe_float(
                row["change_area_m2"]
            )
        ),
        axis=1
    )

    result[
        "building_overlap_pct"
    ] = result.apply(
        lambda row: calculate_percentage(
            safe_float(
                row["building_overlap_m2"]
            ),
            safe_float(
                row["change_area_m2"]
            )
        ),
        axis=1
    )

    # --------------------------------------------------------
    # Classification.
    # --------------------------------------------------------

    result[
        "classification"
    ] = result.apply(
        classify_change,
        axis=1
    )

    # --------------------------------------------------------
    # Candidate flag.
    # --------------------------------------------------------

    result[
        "encroachment_candidate"
    ] = result[
        "classification"
    ].isin(
        ENCROACHMENT_CLASSES
    )

    # --------------------------------------------------------
    # Evidence summary.
    # --------------------------------------------------------

    result[
        "evidence_summary"
    ] = result.apply(
        generate_evidence_summary,
        axis=1
    )

    return result


# ============================================================
# OUTPUT
# ============================================================

def save_results(
    result,
    output_dir=OUTPUT_DIR,
    output_gpkg=OUTPUT_GPKG,
    output_csv=OUTPUT_CSV,
):

    print_header(
        "Saving spatial analysis"
    )

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Remove old GeoPackage so stale layers cannot survive.
    # --------------------------------------------------------

    if os.path.exists(
        output_gpkg
    ):

        try:
            os.remove(
                output_gpkg
            )

        except PermissionError:

            raise PermissionError(
                "\nCould not replace the existing "
                "GeoPackage.\n"
                "Close AOI10_spatial_analysis.gpkg "
                "in QGIS and run the script again."
            )

    # --------------------------------------------------------
    # Save GeoPackage.
    # --------------------------------------------------------

    result.to_file(
        output_gpkg,
        layer="spatial_analysis",
        driver="GPKG"
    )

    # --------------------------------------------------------
    # Save CSV.
    #
    # Geometry is removed because CSV does not preserve
    # GeoPackage geometry properly.
    # --------------------------------------------------------

    csv_result = result.drop(
        columns=["geometry"],
        errors="ignore"
    ).copy()

    csv_result.to_csv(
        output_csv,
        index=False
    )

    print(
        f"\nGeoPackage:\n{output_gpkg}"
    )

    print(
        f"\nCSV:\n{output_csv}"
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

def print_summary(result):

    print_header(
        "URBANEYE SPATIAL ANALYSIS SUMMARY"
    )

    total_changes = len(
        result
    )

    total_area = result[
        "change_area_m2"
    ].sum()

    road_count = (
        result[
            "road_overlap_m2"
        ] >= MIN_ROAD_INTRUSION_AREA
    ).sum()

    building_count = (
        result[
            "building_overlap_m2"
        ] >= MIN_BUILDING_OVERLAP_AREA
    ).sum()

    government_count = (
        result[
            "government_overlap_m2"
        ] >= MIN_LAND_INTRUSION_AREA
    ).sum()

    public_count = (
        result[
            "public_overlap_m2"
        ] >= MIN_LAND_INTRUSION_AREA
    ).sum()

    encroachment_count = (
        result[
            "encroachment_candidate"
        ]
    ).sum()

    verification_count = (
        result[
            "classification"
        ]
        ==
        "Requires Verification"
    ).sum()

    non_encroachment_count = (
        result[
            "classification"
        ].isin(
            NON_ENCROACHMENT_CLASSES
        )
    ).sum()

    print(
        f"\nTotal detected change regions: "
        f"{total_changes}"
    )

    print(
        f"Total detected change area: "
        f"{total_area:.2f} m²"
    )

    print(
        f"\nRegions with meaningful road overlap: "
        f"{road_count}"
    )

    print(
        f"Regions with meaningful building overlap: "
        f"{building_count}"
    )

    print(
        f"Regions overlapping government land: "
        f"{government_count}"
    )

    print(
        f"Regions overlapping public land: "
        f"{public_count}"
    )

    print(
        f"\nPotential encroachment candidates: "
        f"{encroachment_count}"
    )

    print(
        f"Non-encroachment / ordinary changes: "
        f"{non_encroachment_count}"
    )

    print(
        f"Requires verification: "
        f"{verification_count}"
    )

    # --------------------------------------------------------
    # Classification distribution
    # --------------------------------------------------------

    print(
        "\nClassification distribution:"
    )

    distribution = (
        result[
            "classification"
        ]
        .value_counts()
    )

    print(
        distribution.to_string()
    )

    # --------------------------------------------------------
    # Candidate table
    # --------------------------------------------------------

    candidates = result[
        result[
            "encroachment_candidate"
        ]
    ].copy()

    print(
        "\nPotential encroachment candidates:"
    )

    if candidates.empty:

        print(
            "No potential encroachment "
            "candidates identified."
        )

    else:

        display_columns = [
            "change_id",
            "change_area_m2",
            "primary_parcel_id",
            "primary_land_category",
            "parcel_count",
            "primary_parcel_overlap_pct",
            "road_overlap_m2",
            "government_overlap_m2",
            "public_overlap_m2",
            "building_overlap_m2",
            "classification"
        ]

        display_columns = [
            col
            for col in display_columns
            if col in candidates.columns
        ]

        print(
            candidates[
                display_columns
            ].to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # Verification cases
    # --------------------------------------------------------

    verification = result[
        result[
            "classification"
        ]
        ==
        "Requires Verification"
    ].copy()

    print(
        "\nRequires verification:"
    )

    if verification.empty:

        print(
            "No ambiguous cases identified "
            "under the current thresholds."
        )

    else:

        display_columns = [
            "change_id",
            "change_area_m2",
            "primary_parcel_id",
            "primary_land_category",
            "parcel_count",
            "parcel_coverage_pct",
            "road_overlap_m2",
            "government_overlap_m2",
            "public_overlap_m2",
            "building_overlap_m2",
            "classification"
        ]

        display_columns = [
            col
            for col in display_columns
            if col in verification.columns
        ]

        print(
            verification[
                display_columns
            ].to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # Data quality checks
    # --------------------------------------------------------

    print(
        "\nSpatial analysis data-quality checks:"
    )

    invalid_geometries = (
        ~result.geometry.is_valid
    ).sum()

    empty_geometries = (
        result.geometry.is_empty
    ).sum()

    zero_area = (
        result[
            "change_area_m2"
        ]
        <= 0
    ).sum()

    print(
        f"Invalid output geometries: "
        f"{invalid_geometries}"
    )

    print(
        f"Empty output geometries: "
        f"{empty_geometries}"
    )

    print(
        f"Zero-area change regions: "
        f"{zero_area}"
    )

    # --------------------------------------------------------
    # Final interpretation
    # --------------------------------------------------------

    print(
        "\nInterpretation:"
    )

    print(
        "Satellite-detected change is treated separately "
        "from encroachment."
    )

    print(
        "Only changes with meaningful spatial evidence "
        "of intrusion are classified as potential "
        "encroachment."
    )

    print(
        "Changes without sufficient evidence are retained "
        "as normal changes or Requires Verification."
    )

    print(
        "All potential encroachment results require "
        "human/legal verification."
    )


# ============================================================
# MAIN
# ============================================================

def run_spatial_analysis(
    change_file,
    parcel_file,
    road_file,
    building_file,
    output_gpkg,
    output_csv,
):
    """Run spatial analysis without mutating module-level path settings."""
    (
        change,
        parcels,
        roads,
        buildings
    ) = load_all_data(
        change_file=change_file,
        parcel_file=parcel_file,
        road_file=road_file,
        building_file=building_file,
    )

    parcel_results = analyze_parcels(change, parcels)
    road_results = analyze_roads(change, roads)
    building_results = analyze_buildings(change, buildings)
    result = combine_analysis(
        change,
        parcel_results,
        road_results,
        building_results,
    )
    save_results(
        result,
        output_dir=os.path.dirname(str(output_gpkg)),
        output_gpkg=output_gpkg,
        output_csv=output_csv,
    )
    print_summary(result)
    return result


def main():

    warnings.filterwarnings(
        "ignore",
        category=UserWarning
    )

    print()
    print("=" * 60)
    print("UrbanEye Spatial Analysis")
    print("=" * 60)

    # --------------------------------------------------------
    # Load datasets
    # --------------------------------------------------------

    (
        change,
        parcels,
        roads,
        buildings
    ) = load_all_data()

    # --------------------------------------------------------
    # Analyze parcels
    # --------------------------------------------------------

    parcel_results = analyze_parcels(
        change,
        parcels
    )

    # --------------------------------------------------------
    # Analyze roads
    # --------------------------------------------------------

    road_results = analyze_roads(
        change,
        roads
    )

    # --------------------------------------------------------
    # Analyze buildings
    # --------------------------------------------------------

    building_results = analyze_buildings(
        change,
        buildings
    )

    # --------------------------------------------------------
    # Combine evidence
    # --------------------------------------------------------

    result = combine_analysis(
        change,
        parcel_results,
        road_results,
        building_results
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_results(
        result
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print_summary(
        result
    )

    print()
    print("=" * 60)
    print("Spatial analysis completed successfully.")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
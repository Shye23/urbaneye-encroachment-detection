from pathlib import Path
import random
import math

import numpy as np
import geopandas as gpd
import rasterio

from shapely.geometry import (
    box,
    LineString,
    Polygon,
    Point
)
from shapely.ops import unary_union, split
from shapely import affinity


# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(r"E:\UrbanEye")

POSTPROCESSED_MASK = (
    ROOT / "outputs" / "postprocessed" / "AOI10_postprocessed.npy"
)

REFERENCE_TIF = (
    ROOT / "processed_data" / "patches" / "test" /
    "2024" / "AOI10_y000_x000.tif"
)

OUTPUT_DIR = ROOT / "processed_data" / "cadastral"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CADASTRAL_OUTPUT = OUTPUT_DIR / "synthetic_cadastral.gpkg"
ROADS_OUTPUT = OUTPUT_DIR / "synthetic_roads.gpkg"
BUILDINGS_OUTPUT = OUTPUT_DIR / "synthetic_buildings.gpkg"

SEED = 42
random.seed(SEED)
np.random.seed(SEED)


# ============================================================
# REALISTIC SCALE PARAMETERS
# ============================================================

# Road widths based broadly on Maharashtra urban layout
# conventions. These are synthetic, not legal survey values.

MAIN_ROAD_WIDTH = 15.0
COLLECTOR_ROAD_WIDTH = 12.0
LOCAL_ROAD_WIDTH = 9.0

# Target individual parcel areas
MIN_PARCEL_AREA = 80.0
TARGET_PARCEL_AREA = 300.0
MAX_PARCEL_AREA = 650.0

# Building footprint range
MIN_BUILDING_AREA = 50.0
MAX_BUILDING_AREA = 220.0

# Maximum building coverage inside a parcel
MAX_BUILDING_COVERAGE = 0.45


# ============================================================
# HELPERS
# ============================================================

def clean_geometry(geom):
    """Repair minor geometry problems."""
    if geom is None or geom.is_empty:
        return None

    try:
        geom = geom.buffer(0)
    except Exception:
        return None

    if geom.is_empty:
        return None

    return geom


def get_aoi_from_reference():
    """
    Construct the full stitched AOI polygon.

    The stitched prediction is 206 x 206 pixels.
    Each pixel is 5 m x 5 m.
    """

    mask = np.load(POSTPROCESSED_MASK)

    height, width = mask.shape

    with rasterio.open(REFERENCE_TIF) as src:
        transform = src.transform
        crs = src.crs

    pixel_width = transform.a
    pixel_height = abs(transform.e)

    xmin = transform.c
    ymax = transform.f

    xmax = xmin + width * pixel_width
    ymin = ymax - height * pixel_height

    aoi = box(xmin, ymin, xmax, ymax)

    print(f"AOI size: {width} x {height} pixels")
    print(
        f"AOI dimensions: "
        f"{width * pixel_width:.1f} m x "
        f"{height * pixel_height:.1f} m"
    )
    print(f"CRS: {crs}")

    return aoi, crs


# ============================================================
# ROAD NETWORK
# ============================================================

def create_roads(aoi):
    """
    Create a realistic hierarchical urban road network.

    Instead of giant bands, roads are narrow linear corridors:
        - 1 main horizontal road
        - 1 main vertical road
        - several collector roads
        - several local roads
    """

    minx, miny, maxx, maxy = aoi.bounds

    width = maxx - minx
    height = maxy - miny

    road_records = []

    road_id = 1

    def add_road(
        x1, y1, x2, y2,
        road_type,
        road_width
    ):
        nonlocal road_id

        centerline = LineString([
            (x1, y1),
            (x2, y2)
        ])

        polygon = centerline.buffer(
            road_width / 2.0,
            cap_style=2,
            join_style=2
        )

        polygon = polygon.intersection(aoi)

        if polygon.is_empty:
            return

        road_records.append({
            "road_id": f"R{road_id:03d}",
            "road_type": road_type,
            "width_m": road_width,
            "source": "SYNTHETIC",
            "source_year": 2024,
            "geometry": polygon
        })

        road_id += 1

    # --------------------------------------------------------
    # MAIN ROADS
    # --------------------------------------------------------

    # Main east-west road
    y = miny + height * 0.34

    add_road(
        minx - 50,
        y,
        maxx + 50,
        y,
        "MAIN_ROAD",
        MAIN_ROAD_WIDTH
    )

    # Main north-south road
    x = minx + width * 0.63

    add_road(
        x,
        miny - 50,
        x,
        maxy + 50,
        "MAIN_ROAD",
        MAIN_ROAD_WIDTH
    )

    # --------------------------------------------------------
    # COLLECTOR ROADS
    # --------------------------------------------------------

    # Horizontal collectors
    for frac in [0.16, 0.55, 0.78]:

        y = miny + height * frac

        add_road(
            minx - 30,
            y,
            maxx + 30,
            y,
            "COLLECTOR",
            COLLECTOR_ROAD_WIDTH
        )

    # Vertical collectors
    for frac in [0.22, 0.82]:

        x = minx + width * frac

        add_road(
            x,
            miny - 30,
            x,
            maxy + 30,
            "COLLECTOR",
            COLLECTOR_ROAD_WIDTH
        )

    # --------------------------------------------------------
    # LOCAL ROADS
    # --------------------------------------------------------

    local_vertical = [0.43, 0.92]

    for frac in local_vertical:

        x = minx + width * frac

        add_road(
            x,
            miny - 20,
            x,
            maxy + 20,
            "LOCAL_ROAD",
            LOCAL_ROAD_WIDTH
        )

    local_horizontal = [0.91]

    for frac in local_horizontal:

        y = miny + height * frac

        add_road(
            minx - 20,
            y,
            maxx + 20,
            y,
            "LOCAL_ROAD",
            LOCAL_ROAD_WIDTH
        )

    roads = gpd.GeoDataFrame(
        road_records,
        crs="EPSG:32643"
    )

    print(f"Road features created: {len(roads)}")

    return roads


# ============================================================
# CREATE BLOCKS BETWEEN ROADS
# ============================================================

def create_blocks(aoi, roads):
    """
    Derive urban blocks from the road network.

    Parcels will be generated inside these blocks.
    """

    road_union = unary_union(
        [clean_geometry(g) for g in roads.geometry]
    )

    road_union = clean_geometry(road_union)

    available_land = aoi.difference(road_union)

    available_land = clean_geometry(available_land)

    if available_land is None:
        raise RuntimeError("Could not create land area outside roads.")

    # Individual polygons created by road boundaries
    if available_land.geom_type == "Polygon":
        blocks = [available_land]

    else:
        blocks = list(available_land.geoms)

    # Remove tiny fragments
    blocks = [
        b for b in blocks
        if b.area >= 500
    ]

    print(f"Urban blocks created: {len(blocks)}")

    return blocks, road_union


# ============================================================
# SPLIT A BLOCK INTO SMALLER PARCELS
# ============================================================

def split_polygon_once(poly):
    """
    Split a polygon through its longest dimension.

    Slight random offset prevents a completely mechanical grid.
    """

    minx, miny, maxx, maxy = poly.bounds

    width = maxx - minx
    height = maxy - miny

    if width >= height:

        # Vertical cut
        ratio = random.uniform(0.42, 0.58)
        x = minx + width * ratio

        cut = LineString([
            (x, miny - 100),
            (x, maxy + 100)
        ])

    else:

        # Horizontal cut
        ratio = random.uniform(0.42, 0.58)
        y = miny + height * ratio

        cut = LineString([
            (minx - 100, y),
            (maxx + 100, y)
        ])

    try:
        result = split(poly, cut)

        parts = [
            clean_geometry(g)
            for g in result.geoms
            if g.area >= MIN_PARCEL_AREA
        ]

        if len(parts) >= 2:
            return parts

    except Exception:
        pass

    return [poly]


def subdivide_block(block):
    """
    Recursively divide an urban block until parcels reach
    realistic individual-plot sizes.
    """

    parcels = [block]

    # Avoid pathological infinite splitting
    for _ in range(10):

        new_parcels = []
        changed = False

        for parcel in parcels:

            if parcel.area > MAX_PARCEL_AREA:

                parts = split_polygon_once(parcel)

                if len(parts) > 1:
                    new_parcels.extend(parts)
                    changed = True
                else:
                    new_parcels.append(parcel)

            else:
                new_parcels.append(parcel)

        parcels = new_parcels

        if not changed:
            break

    return parcels


# ============================================================
# CREATE CADASTRAL PARCELS
# ============================================================

def create_parcels(blocks):
    """
    Generate individual cadastral-style parcels.

    Parcel sizes are deliberately much smaller than the
    previous 6 x 6 grid.
    """

    parcel_geometries = []

    for block in blocks:

        block_parcels = subdivide_block(block)

        parcel_geometries.extend(block_parcels)

    # Remove very small leftovers
    parcel_geometries = [
        p for p in parcel_geometries
        if MIN_PARCEL_AREA <= p.area <= MAX_PARCEL_AREA * 1.8
    ]

    print(f"Individual parcels created: {len(parcel_geometries)}")

    return parcel_geometries


# ============================================================
# ASSIGN LAND INFORMATION
# ============================================================

def assign_land_attributes(parcel_geometries):
    """
    Assign synthetic cadastral attributes.

    These are explicitly synthetic and should never be
    represented as actual land records.
    """

    records = []

    categories = [
        "PRIVATE",
        "PRIVATE",
        "PRIVATE",
        "PRIVATE",
        "GOVERNMENT",
        "PUBLIC"
    ]

    land_uses = {
        "PRIVATE": [
            "RESIDENTIAL",
            "RESIDENTIAL",
            "RESIDENTIAL",
            "COMMERCIAL",
            "MIXED_USE"
        ],
        "GOVERNMENT": [
            "GOVERNMENT_LAND",
            "PUBLIC_AMENITY",
            "INSTITUTIONAL"
        ],
        "PUBLIC": [
            "OPEN_SPACE",
            "PUBLIC_AMENITY",
            "PUBLIC_UTILITY"
        ]
    }

    for i, geom in enumerate(parcel_geometries, start=1):

        category = random.choice(categories)

        land_use = random.choice(
            land_uses[category]
        )

        area = geom.area

        # Synthetic survey/gat-style numbering
        survey_no = (
            f"{random.randint(1, 450)}/"
            f"{random.randint(1, 9)}"
        )

        owner_type = {
            "PRIVATE": "PRIVATE_HOLDER",
            "GOVERNMENT": random.choice([
                "MUNICIPAL",
                "STATE",
                "REVENUE_DEPARTMENT"
            ]),
            "PUBLIC": random.choice([
                "MUNICIPAL",
                "LOCAL_AUTHORITY"
            ])
        }[category]

        records.append({
            "parcel_id": f"P{ i:04d}",
            "survey_no": survey_no,
            "area_sqm": round(area, 2),
            "land_category": category,
            "land_use": land_use,
            "owner_type": owner_type,
            "authority": "SYNTHETIC_AUTHORITY",
            "source": "SYNTHETIC",
            "source_year": 2024,
            "record_status": "SIMULATED",
            "geometry": geom
        })

    return records


# ============================================================
# BUILDINGS
# ============================================================

def create_building_for_parcel(parcel, parcel_record):
    """
    Generate one or occasionally two small building footprints
    inside a sufficiently large parcel.
    """

    if parcel.area < 150:
        return []

    category = parcel_record["land_category"]
    land_use = parcel_record["land_use"]

    if land_use in [
        "OPEN_SPACE",
        "PUBLIC_UTILITY"
    ]:
        return []

    # Most residential parcels get one building.
    # Larger parcels may get two smaller structures.
    building_count = 1

    if parcel.area > 450 and random.random() < 0.25:
        building_count = 2

    minx, miny, maxx, maxy = parcel.bounds

    buildings = []

    for _ in range(building_count):

        parcel_width = maxx - minx
        parcel_height = maxy - miny

        # Keep a meaningful setback from parcel boundary
        setback = random.uniform(2.0, 4.5)

        usable_width = parcel_width - 2 * setback
        usable_height = parcel_height - 2 * setback

        if usable_width < 7 or usable_height < 7:
            continue

        # Typical small urban building footprints
        building_width = random.uniform(
            7.0,
            min(16.0, usable_width)
        )

        building_height = random.uniform(
            6.0,
            min(14.0, usable_height)
        )

        area = building_width * building_height

        if area < MIN_BUILDING_AREA:
            continue

        if area > MAX_BUILDING_AREA:
            continue

        # Start with rectangle
        cx = (
            minx +
            setback +
            usable_width / 2
        )

        cy = (
            miny +
            setback +
            usable_height / 2
        )

        building = box(
            cx - building_width / 2,
            cy - building_height / 2,
            cx + building_width / 2,
            cy + building_height / 2
        )

        # Rotate some buildings slightly
        angle = random.choice([
            0,
            0,
            0,
            90,
            random.uniform(-5, 5)
        ])

        building = affinity.rotate(
            building,
            angle,
            origin="centroid"
        )

        # Make absolutely sure it remains inside parcel
        building = building.intersection(
            parcel.buffer(-1.0)
        )

        building = clean_geometry(building)

        if building is None:
            continue

        if building.area < MIN_BUILDING_AREA:
            continue

        if building.area > MAX_BUILDING_AREA:
            continue

        buildings.append(building)

    return buildings


def create_buildings(parcel_records):
    """
    Generate realistic building footprints inside parcels.
    """

    building_records = []

    building_id = 1

    for parcel_record in parcel_records:

        parcel = parcel_record["geometry"]

        buildings = create_building_for_parcel(
            parcel,
            parcel_record
        )

        for building in buildings:

            if building.geom_type != "Polygon":
                continue

            land_use = parcel_record["land_use"]

            if land_use == "RESIDENTIAL":
                building_type = random.choice([
                    "RESIDENTIAL_HOUSE",
                    "RESIDENTIAL_HOUSE",
                    "ROW_HOUSE",
                    "SMALL_APARTMENT"
                ])

            elif land_use == "COMMERCIAL":
                building_type = random.choice([
                    "SHOP",
                    "COMMERCIAL_BUILDING"
                ])

            elif land_use == "MIXED_USE":
                building_type = "MIXED_USE_BUILDING"

            elif land_use == "INSTITUTIONAL":
                building_type = "INSTITUTIONAL_BUILDING"

            elif land_use == "PUBLIC_AMENITY":
                building_type = "PUBLIC_BUILDING"

            else:
                building_type = "OTHER"

            # Synthetic approval status
            if building_type in [
                "RESIDENTIAL_HOUSE",
                "ROW_HOUSE",
                "SMALL_APARTMENT"
            ]:
                approval_status = random.choices(
                    ["APPROVED", "UNKNOWN"],
                    weights=[0.85, 0.15]
                )[0]
            else:
                approval_status = random.choices(
                    ["APPROVED", "UNKNOWN"],
                    weights=[0.75, 0.25]
                )[0]

            building_records.append({
                "building_id": f"B{building_id:04d}",
                "parcel_id": parcel_record["parcel_id"],
                "building_type": building_type,
                "footprint_sqm": round(
                    building.area,
                    2
                ),
                "approval_status": approval_status,
                "source": "SYNTHETIC",
                "source_year": 2024,
                "record_status": "SIMULATED",
                "geometry": building
            })

            building_id += 1

    print(
        f"Building footprints created: "
        f"{len(building_records)}"
    )

    return building_records


# ============================================================
# SAVE
# ============================================================

def save_layers(
    parcel_records,
    roads,
    building_records,
    crs
):

    parcels_gdf = gpd.GeoDataFrame(
        parcel_records,
        geometry="geometry",
        crs=crs
    )

    buildings_gdf = gpd.GeoDataFrame(
        building_records,
        geometry="geometry",
        crs=crs
    )

    roads_gdf = roads.to_crs(crs)

    # --------------------------------------------------------
    # Save parcels
    # --------------------------------------------------------

    parcels_gdf.to_file(
        CADASTRAL_OUTPUT,
        layer="parcels",
        driver="GPKG"
    )

    # --------------------------------------------------------
    # Save roads
    # --------------------------------------------------------

    roads_gdf.to_file(
        ROADS_OUTPUT,
        layer="roads",
        driver="GPKG"
    )

    # --------------------------------------------------------
    # Save buildings
    # --------------------------------------------------------

    buildings_gdf.to_file(
        BUILDINGS_OUTPUT,
        layer="buildings",
        driver="GPKG"
    )

    print()
    print("==============================================")
    print("Synthetic cadastral data generated")
    print("==============================================")
    print()
    print(f"Parcels   : {len(parcels_gdf)}")
    print(f"Buildings : {len(buildings_gdf)}")
    print(f"Roads     : {len(roads_gdf)}")
    print()
    print(f"Parcels   : {CADASTRAL_OUTPUT}")
    print(f"Roads     : {ROADS_OUTPUT}")
    print(f"Buildings : {BUILDINGS_OUTPUT}")
    print()
    print(
        "Average parcel area:",
        round(parcels_gdf.area.mean(), 2),
        "m²"
    )

    print(
        "Min parcel area:",
        round(parcels_gdf.area.min(), 2),
        "m²"
    )

    print(
        "Max parcel area:",
        round(parcels_gdf.area.max(), 2),
        "m²"
    )

    print()
    print("Land category distribution:")
    print(
        parcels_gdf["land_category"]
        .value_counts()
    )

    print()
    print("Land use distribution:")
    print(
        parcels_gdf["land_use"]
        .value_counts()
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("==============================================")
    print("UrbanEye Synthetic Cadastral Generator")
    print("==============================================")
    print()

    # 1. AOI
    aoi, crs = get_aoi_from_reference()

    # 2. Roads
    roads = create_roads(aoi)

    # 3. Urban blocks
    blocks, road_union = create_blocks(
        aoi,
        roads
    )

    # 4. Parcels
    parcel_geometries = create_parcels(
        blocks
    )

    # 5. Parcel attributes
    parcel_records = assign_land_attributes(
        parcel_geometries
    )

    # 6. Buildings
    building_records = create_buildings(
        parcel_records
    )

    # 7. Save
    save_layers(
        parcel_records,
        roads,
        building_records,
        crs
    )

    print()
    print("Done.")
    print()


if __name__ == "__main__":
    main()
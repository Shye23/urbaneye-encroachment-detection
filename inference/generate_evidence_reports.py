"""
UrbanEye Evidence Report Generator

Converts spatial analysis results into:
1. Human-readable CSV
2. Detailed JSON evidence records
3. Individual TXT reports for potential encroachment cases
4. Summary report

Input:
    outputs/gis/AOI10_spatial_analysis.gpkg
    outputs/gis/AOI10_spatial_analysis.csv

Output:
    outputs/reports/
"""

from pathlib import Path
import json
import pandas as pd
import geopandas as gpd
import sys


# ============================================================
# PATHS
# ============================================================
sys.path.insert(0,r"E:\UrbanEye")
ROOT = Path(r"E:\UrbanEye")

INPUT_GPKG = ROOT / "outputs" / "gis" / "AOI10_spatial_analysis.gpkg"
INPUT_CSV = ROOT / "outputs" / "gis" / "AOI10_spatial_analysis.csv"

OUTPUT_DIR = ROOT / "outputs" / "reports"

EVIDENCE_CSV = OUTPUT_DIR / "AOI10_evidence_report.csv"
EVIDENCE_JSON = OUTPUT_DIR / "AOI10_evidence_records.json"
SUMMARY_TXT = OUTPUT_DIR / "AOI10_summary_report.txt"


# ============================================================
# CONFIGURATION
# ============================================================

ENCROACHMENT_CLASSES = {
    "Potential Public-Space Encroachment",
    "Potential Government-Land Encroachment",
    "Potential Public-Land Encroachment",
    "Potential Parcel-Boundary Encroachment",
    "Change on Government Land",
    "Change on Public Land",
}

VERIFICATION_CLASS = "Requires Verification"

NORMAL_CLASSES = {
    "Normal Building Change",
}


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def safe_number(value, default=0.0):
    """Convert a value to float safely."""
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_string(value, default="Unknown"):
    """Convert a value to string safely."""
    if pd.isna(value):
        return default

    value = str(value).strip()

    if not value:
        return default

    return value


def percentage(value):
    """Format a percentage."""
    return f"{safe_number(value):.2f}%"


def area(value):
    """Format an area in square metres."""
    return f"{safe_number(value):,.2f} m²"


def classify_status(
    classification,
    encroachment_classes=ENCROACHMENT_CLASSES,
):
    """
    Convert detailed classification into a broader system status.
    """

    classification = safe_string(classification)

    if classification in encroachment_classes:
        return "POTENTIAL_ENCROACHMENT"

    if classification == VERIFICATION_CLASS:
        return "REQUIRES_VERIFICATION"

    if classification in NORMAL_CLASSES:
        return "NORMAL_CHANGE"

    return "UNCLASSIFIED"


def generate_interpretation(
    row,
    normal_classes=NORMAL_CLASSES,
):
    """
    Generate a human-readable interpretation
    based on spatial evidence.
    """

    classification = safe_string(row.get("classification"))

    road = safe_number(row.get("road_overlap_m2"))
    government = safe_number(row.get("government_overlap_m2"))
    public = safe_number(row.get("public_overlap_m2"))
    building = safe_number(row.get("building_overlap_m2"))

    parcel_count = int(
        safe_number(row.get("parcel_count"), 0)
    )

    parcel_coverage = safe_number(
        row.get("parcel_coverage_pct")
    )

    reasons = []

    if road > 0:
        reasons.append(
            f"overlaps mapped road/public-space area by {area(road)}"
        )

    if government > 0:
        reasons.append(
            f"overlaps government land by {area(government)}"
        )

    if public > 0:
        reasons.append(
            f"overlaps public land by {area(public)}"
        )

    if building > 0:
        reasons.append(
            f"overlaps mapped building footprint by {area(building)}"
        )

    if parcel_count > 1:
        reasons.append(
            f"intersects {parcel_count} cadastral parcels"
        )

    if parcel_coverage < 90 and parcel_count > 1:
        reasons.append(
            f"only {percentage(parcel_coverage)} of the "
            f"change lies within the primary parcel"
        )

    if classification == VERIFICATION_CLASS:
        return (
            "Spatial evidence is mixed or ambiguous. "
            "The detected change intersects multiple mapped "
            "features and cannot be reliably classified "
            "without additional verification."
        )

    if classification in {
        "Change on Government Land",
        "Change on Public Land",
    }:
        land_type = (
            "government land"
            if classification == "Change on Government Land"
            else "public land"
        )
        return (
            f"Detected change is mapped on {land_type}, but the spatial-analysis "
            "rules did not classify it as a potential encroachment candidate. "
            "Verify the authoritative land records and site context."
        )

    if classification == "Change Detected, No Encroachment Evidence":
        return (
            "Satellite change was detected, but the available spatial evidence "
            "does not meet the project's criteria for potential encroachment."
        )

    if classification in normal_classes:
        if building > 0:
            return (
                "Detected change overlaps a mapped building "
                "footprint without sufficient evidence of "
                "public, government, or cadastral intrusion."
            )

        return (
            "Detected change does not contain sufficient "
            "spatial evidence to classify it as encroachment."
        )

    if reasons:
        return (
            "Detected change " +
            ", ".join(reasons) +
            ". These spatial relationships indicate a "
            "potential encroachment scenario and require "
            "human/legal verification."
        )

    return (
        "Detected change has insufficient spatial evidence "
        "for encroachment classification."
    )


def generate_recommended_action(
    row,
    encroachment_classes=ENCROACHMENT_CLASSES,
    normal_classes=NORMAL_CLASSES,
):
    """
    Generate a practical next action.
    """

    classification = safe_string(row.get("classification"))

    if classification in encroachment_classes:
        return (
            "Review satellite imagery, cadastral records and "
            "field evidence before taking administrative action."
        )

    if classification == VERIFICATION_CLASS:
        return (
            "Perform manual GIS review and field verification "
            "before classification."
        )

    if classification in {
        "Change on Government Land",
        "Change on Public Land",
        "Change Detected, No Encroachment Evidence",
    }:
        return (
            "Record the detected change and verify it against authoritative GIS "
            "layers if needed. Do not treat this classification alone as proof "
            "of encroachment."
        )

    if classification in normal_classes:
        return (
            "Record as ordinary detected change. "
            "No encroachment action indicated by current evidence."
        )

    return (
        "Perform manual GIS review."
    )


# ============================================================
# LOAD DATA
# ============================================================

def load_data(input_gpkg=INPUT_GPKG, input_csv=INPUT_CSV):

    print("=" * 60)
    print("UrbanEye Evidence Report Generator")
    print("=" * 60)

    input_gpkg = Path(input_gpkg)
    input_csv = Path(input_csv)

    if not input_gpkg.exists():
        raise FileNotFoundError(
            f"Input GeoPackage not found:\n{input_gpkg}"
        )

    if not input_csv.exists():
        raise FileNotFoundError(
            f"Input CSV not found:\n{input_csv}"
        )

    print("\nLoading spatial analysis GeoPackage...")

    layers = gpd.list_layers(input_gpkg)

    if len(layers) == 0:
        raise RuntimeError(
            "No layers found in spatial analysis GeoPackage."
        )

    layer_name = layers.iloc[0]["name"]

    gdf = gpd.read_file(
        input_gpkg,
        layer=layer_name
    )

    print(f"Layer: {layer_name}")
    print(f"Records: {len(gdf)}")
    print(f"CRS: {gdf.crs}")

    print("\nLoading CSV attributes...")

    df = pd.read_csv(input_csv)

    print(f"CSV records: {len(df)}")

    if "candidate_id" not in df.columns:
        raise ValueError(
            "Required column 'candidate_id' missing from CSV."
        )

    return gdf, df


# ============================================================
# CREATE EVIDENCE TABLE
# ============================================================

def create_evidence_table(
    df,
    encroachment_classes=ENCROACHMENT_CLASSES,
    normal_classes=NORMAL_CLASSES,
):

    print("\nCreating evidence records...")

    records = []

    for _, row in df.iterrows():

        candidate_id = safe_string(row.get("candidate_id"))

        classification = safe_string(
            row.get("classification")
        )

        status = classify_status(
            classification,
            encroachment_classes=encroachment_classes,
        )

        change_area = safe_number(
            row.get("change_area_m2")
        )

        record = {
            "candidate_id": candidate_id,

            "status": status,

            "classification": classification,

            "change_area_m2": round(
                change_area,
                2
            ),

            "primary_parcel_id": safe_string(
                row.get("primary_parcel_id"),
                "None"
            ),

            "primary_land_category": safe_string(
                row.get("primary_land_category"),
                "Unknown"
            ),

            "parcel_count": int(
                safe_number(
                    row.get("parcel_count"),
                    0
                )
            ),

            "parcel_coverage_pct": round(
                safe_number(
                    row.get("parcel_coverage_pct")
                ),
                2
            ),

            "road_overlap_m2": round(
                safe_number(
                    row.get("road_overlap_m2")
                ),
                2
            ),

            "government_overlap_m2": round(
                safe_number(
                    row.get("government_overlap_m2")
                ),
                2
            ),

            "public_overlap_m2": round(
                safe_number(
                    row.get("public_overlap_m2")
                ),
                2
            ),

            "building_overlap_m2": round(
                safe_number(
                    row.get("building_overlap_m2")
                ),
                2
            ),

            "interpretation": generate_interpretation(
                row,
                normal_classes=normal_classes,
            ),

            "recommended_action":
                generate_recommended_action(
                    row,
                    encroachment_classes=encroachment_classes,
                    normal_classes=normal_classes,
                ),

            "data_source": "SYNTHETIC_CADASTRAL_DATA",

            "requires_human_verification": True,
        }

        records.append(record)

    evidence_df = pd.DataFrame(records)

    return evidence_df


# ============================================================
# CREATE JSON RECORDS
# ============================================================

def create_json_records(evidence_df):

    records = []

    for _, row in evidence_df.iterrows():

        record = {
            "candidate_id":
                row["candidate_id"],

            "status":
                row["status"],

            "classification":
                row["classification"],

            "detected_change": {
                "area_m2":
                    float(row["change_area_m2"])
            },

            "cadastral_evidence": {
                "primary_parcel_id":
                    row["primary_parcel_id"],

                "land_category":
                    row["primary_land_category"],

                "intersecting_parcels":
                    int(row["parcel_count"]),

                "primary_parcel_coverage_pct":
                    float(row["parcel_coverage_pct"])
            },

            "spatial_evidence": {
                "road_overlap_m2":
                    float(row["road_overlap_m2"]),

                "government_land_overlap_m2":
                    float(
                        row["government_overlap_m2"]
                    ),

                "public_land_overlap_m2":
                    float(
                        row["public_overlap_m2"]
                    ),

                "building_overlap_m2":
                    float(
                        row["building_overlap_m2"]
                    )
            },

            "interpretation":
                row["interpretation"],

            "recommended_action":
                row["recommended_action"],

            "data_source":
                row["data_source"],

            "requires_human_verification":
                bool(
                    row["requires_human_verification"]
                )
        }

        records.append(record)

    return records


# ============================================================
# INDIVIDUAL REPORTS
# ============================================================

def create_individual_reports(evidence_df, output_dir=OUTPUT_DIR):

    print("\nCreating individual evidence reports...")

    individual_dir = Path(output_dir) / "cases"

    individual_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    for _, row in evidence_df.iterrows():

        candidate_id = row["candidate_id"]

        report_path = (
            individual_dir /
            f"{candidate_id}_evidence.txt"
        )

        report = f"""
============================================================
URBANEYE CHANGE EVIDENCE REPORT
============================================================

Change ID:
{candidate_id}

STATUS
------------------------------------------------------------
{row["status"]}

CLASSIFICATION
------------------------------------------------------------
{row["classification"]}

DETECTED CHANGE
------------------------------------------------------------
Area:
{area(row["change_area_m2"])}

CADASTRAL INFORMATION
------------------------------------------------------------
Primary Parcel:
{row["primary_parcel_id"]}

Land Category:
{row["primary_land_category"]}

Intersecting Parcels:
{row["parcel_count"]}

Primary Parcel Coverage:
{percentage(row["parcel_coverage_pct"])}

SPATIAL EVIDENCE
------------------------------------------------------------
Road Overlap:
{area(row["road_overlap_m2"])}

Government Land Overlap:
{area(row["government_overlap_m2"])}

Public Land Overlap:
{area(row["public_overlap_m2"])}

Building Footprint Overlap:
{area(row["building_overlap_m2"])}

INTERPRETATION
------------------------------------------------------------
{row["interpretation"]}

RECOMMENDED ACTION
------------------------------------------------------------
{row["recommended_action"]}

DATA SOURCE
------------------------------------------------------------
{row["data_source"]}

IMPORTANT
------------------------------------------------------------
This report represents automated spatial analysis.

A satellite-detected change does not by itself establish
legal encroachment.

All potential encroachment cases require human and/or
legal verification using authoritative cadastral,
ownership and field-survey information.

============================================================
"""

        report_path.write_text(
            report.strip(),
            encoding="utf-8"
        )


# ============================================================
# SUMMARY REPORT
# ============================================================

def create_summary_report(evidence_df, summary_path=SUMMARY_TXT):

    total = len(evidence_df)

    encroachment = (
        evidence_df["status"]
        == "POTENTIAL_ENCROACHMENT"
    ).sum()

    normal = (
        evidence_df["status"]
        == "NORMAL_CHANGE"
    ).sum()

    verification = (
        evidence_df["status"]
        == "REQUIRES_VERIFICATION"
    ).sum()

    total_area = (
        evidence_df["change_area_m2"]
        .sum()
    )

    summary = f"""
============================================================
URBANEYE SPATIAL EVIDENCE SUMMARY
============================================================

Total detected change regions:
{total}

Total detected change area:
{total_area:,.2f} m²

------------------------------------------------------------
CLASSIFICATION SUMMARY
------------------------------------------------------------

Potential encroachment:
{encroachment}

Normal / non-encroachment changes:
{normal}

Requires verification:
{verification}

------------------------------------------------------------
CLASSIFICATION DISTRIBUTION
------------------------------------------------------------

"""

    classification_counts = (
        evidence_df["classification"]
        .value_counts()
    )

    for classification, count in classification_counts.items():

        summary += (
            f"{classification}: {count}\n"
        )

    summary += """

------------------------------------------------------------
IMPORTANT INTERPRETATION
------------------------------------------------------------

UrbanEye performs automated satellite change detection
followed by spatial evidence analysis.

A detected change is NOT automatically considered
encroachment.

Encroachment classification is based on relationships
between detected change and available spatial evidence,
including:

• cadastral parcels
• government/public land
• roads
• building footprints
• parcel boundaries

Synthetic cadastral data is currently being used for
pipeline validation.

Real cadastral and ownership records should replace the
synthetic layers before operational deployment.

All potential encroachment cases require human/legal
verification.

============================================================
"""

    Path(summary_path).write_text(
        summary.strip(),
        encoding="utf-8"
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_results(evidence_df):

    print("\nRunning evidence validation...")

    required_columns = [
        "candidate_id",
        "status",
        "classification",
        "change_area_m2",
        "primary_parcel_id",
        "parcel_count",
        "road_overlap_m2",
        "government_overlap_m2",
        "public_overlap_m2",
        "building_overlap_m2",
    ]

    missing = [
        col
        for col in required_columns
        if col not in evidence_df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    if evidence_df["candidate_id"].duplicated().any():
        raise ValueError(
            "Duplicate change IDs detected."
        )

    if (
        evidence_df["change_area_m2"] < 0
    ).any():
        raise ValueError(
            "Negative change areas detected."
        )

    numeric_columns = [
        "road_overlap_m2",
        "government_overlap_m2",
        "public_overlap_m2",
        "building_overlap_m2",
    ]

    for column in numeric_columns:

        if (
            evidence_df[column] < 0
        ).any():

            raise ValueError(
                f"Negative values found in {column}."
            )

    print("Evidence validation: PASSED")


# ============================================================
# MAIN
# ============================================================

def run_evidence_report(
    input_gpkg,
    input_csv,
    output_dir,
    evidence_csv,
    evidence_json,
    summary_txt,
    encroachment_classes=ENCROACHMENT_CLASSES,
    normal_classes=NORMAL_CLASSES,
):
    """Generate evidence outputs without mutating module-level paths."""
    output_dir = Path(output_dir)
    evidence_csv = Path(evidence_csv)
    evidence_json = Path(evidence_json)
    summary_txt = Path(summary_txt)
    output_dir.mkdir(parents=True, exist_ok=True)

    _, spatial_df = load_data(
        input_gpkg=input_gpkg,
        input_csv=input_csv,
    )
    evidence_df = create_evidence_table(
        spatial_df,
        encroachment_classes=encroachment_classes,
        normal_classes=normal_classes,
    )
    validate_results(evidence_df)
    evidence_df.to_csv(evidence_csv, index=False)

    json_records = create_json_records(evidence_df)
    with evidence_json.open("w", encoding="utf-8") as file:
        json.dump(json_records, file, indent=4)

    create_individual_reports(evidence_df, output_dir=output_dir)
    create_summary_report(evidence_df, summary_path=summary_txt)
    return evidence_df


def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    gdf, spatial_df = load_data()

    # --------------------------------------------------------
    # CREATE EVIDENCE TABLE
    # --------------------------------------------------------

    evidence_df = create_evidence_table(
        spatial_df
    )

    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    validate_results(
        evidence_df
    )

    # --------------------------------------------------------
    # SAVE CSV
    # --------------------------------------------------------

    evidence_df.to_csv(
        EVIDENCE_CSV,
        index=False
    )

    print(
        f"\nEvidence CSV:\n{EVIDENCE_CSV}"
    )

    # --------------------------------------------------------
    # SAVE JSON
    # --------------------------------------------------------

    json_records = create_json_records(
        evidence_df
    )

    with open(
        EVIDENCE_JSON,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            json_records,
            f,
            indent=4
        )

    print(
        f"Evidence JSON:\n{EVIDENCE_JSON}"
    )

    # --------------------------------------------------------
    # INDIVIDUAL CASE REPORTS
    # --------------------------------------------------------

    create_individual_reports(
        evidence_df
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    create_summary_report(
        evidence_df
    )

    print(
        f"\nSummary report:\n{SUMMARY_TXT}"
    )

    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("URBANEYE EVIDENCE GENERATION SUMMARY")
    print("=" * 60)

    print(
        f"\nTotal cases: "
        f"{len(evidence_df)}"
    )

    print(
        f"Potential encroachment: "
        f"{(
            evidence_df['status']
            == 'POTENTIAL_ENCROACHMENT'
        ).sum()}"
    )

    print(
        f"Normal changes: "
        f"{(
            evidence_df['status']
            == 'NORMAL_CHANGE'
        ).sum()}"
    )

    print(
        f"Requires verification: "
        f"{(
            evidence_df['status']
            == 'REQUIRES_VERIFICATION'
        ).sum()}"
    )

    print("\nClassification distribution:")

    print(
        evidence_df[
            "classification"
        ].value_counts()
    )

    print("\nEvidence generation completed successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()
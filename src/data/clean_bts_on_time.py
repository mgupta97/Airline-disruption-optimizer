from pathlib import Path
import zipfile
import pandas as pd


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
OUTPUT_FILE = PROCESSED_DIR / "flights_clean.parquet"


COLUMN_ALIASES = {
    "FL_DATE": "flight_date",
    "FlightDate": "flight_date",

    "OP_UNIQUE_CARRIER": "carrier",
    "Reporting_Airline": "carrier",
    "IATA_CODE_Reporting_Airline": "carrier",

    "TAIL_NUM": "tail_num",
    "Tail_Number": "tail_num",

    "OP_CARRIER_FL_NUM": "flight_num",
    "Flight_Number_Reporting_Airline": "flight_num",

    "ORIGIN": "origin",
    "Origin": "origin",

    "DEST": "dest",
    "Dest": "dest",

    "ORIGIN_CITY_NAME": "origin_city",
    "OriginCityName": "origin_city",

    "DEST_CITY_NAME": "dest_city",
    "DestCityName": "dest_city",

    "CRS_DEP_TIME": "crs_dep_time",
    "CRSDepTime": "crs_dep_time",

    "DEP_TIME": "dep_time",
    "DepTime": "dep_time",

    "DEP_DELAY": "dep_delay",
    "DepDelay": "dep_delay",

    "DEP_DELAY_NEW": "dep_delay_minutes",
    "DepDelayMinutes": "dep_delay_minutes",

    "CRS_ARR_TIME": "crs_arr_time",
    "CRSArrTime": "crs_arr_time",

    "ARR_TIME": "arr_time",
    "ArrTime": "arr_time",

    "ARR_DELAY": "arr_delay",
    "ArrDelay": "arr_delay",

    "ARR_DELAY_NEW": "arr_delay_minutes",
    "ArrDelayMinutes": "arr_delay_minutes",

    "CANCELLED": "cancelled",
    "Cancelled": "cancelled",

    "CANCELLATION_CODE": "cancellation_code",
    "CancellationCode": "cancellation_code",

    "DIVERTED": "diverted",
    "Diverted": "diverted",

    "CRS_ELAPSED_TIME": "scheduled_elapsed_time",
    "CRSElapsedTime": "scheduled_elapsed_time",

    "ACTUAL_ELAPSED_TIME": "actual_elapsed_time",
    "ActualElapsedTime": "actual_elapsed_time",

    "AIR_TIME": "air_time",
    "AirTime": "air_time",

    "DISTANCE": "distance",
    "Distance": "distance",

    "CARRIER_DELAY": "carrier_delay",
    "CarrierDelay": "carrier_delay",

    "WEATHER_DELAY": "weather_delay",
    "WeatherDelay": "weather_delay",

    "NAS_DELAY": "nas_delay",
    "NASDelay": "nas_delay",

    "SECURITY_DELAY": "security_delay",
    "SecurityDelay": "security_delay",

    "LATE_AIRCRAFT_DELAY": "late_aircraft_delay",
    "LateAircraftDelay": "late_aircraft_delay",
}


def find_raw_files() -> list[Path]:
    files = []
    for pattern in ["*.csv", "*.zip"]:
        files.extend(RAW_DIR.glob(pattern))
    return sorted(files)


def read_raw_file(path: Path) -> pd.DataFrame:
    print(f"Reading: {path}")

    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, low_memory=False)

    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            csv_files = [name for name in z.namelist() if name.lower().endswith(".csv")]
            if not csv_files:
                raise ValueError(f"No CSV found inside {path}")
            with z.open(csv_files[0]) as f:
                return pd.read_csv(f, low_memory=False)

    raise ValueError(f"Unsupported file type: {path}")


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    available_aliases = {
        old: new for old, new in COLUMN_ALIASES.items()
        if old in df.columns
    }

    df = df.rename(columns=available_aliases)

    # BTS files sometimes include multiple versions of the same field.
    # Example: OP_UNIQUE_CARRIER and IATA_CODE_Reporting_Airline can both
    # map to "carrier". Parquet cannot save duplicate column names, so we
    # merge duplicate columns by taking the first non-null value across them.
    if df.columns.duplicated().any():
        merged_columns = {}
        for col in dict.fromkeys(df.columns):
            matching_cols = df.loc[:, df.columns == col]

            if matching_cols.shape[1] == 1:
                merged_columns[col] = matching_cols.iloc[:, 0]
            else:
                merged_columns[col] = matching_cols.bfill(axis=1).iloc[:, 0]

        df = pd.DataFrame(merged_columns)

    keep_cols = sorted(set(available_aliases.values()))
    df = df[[col for col in keep_cols if col in df.columns]].copy()

    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    if "flight_date" in df.columns:
        df["flight_date"] = pd.to_datetime(df["flight_date"], errors="coerce")
        df["year"] = df["flight_date"].dt.year
        df["month"] = df["flight_date"].dt.month
        df["day_of_week"] = df["flight_date"].dt.dayofweek

    numeric_cols = [
        "crs_dep_time", "dep_time", "dep_delay", "dep_delay_minutes",
        "crs_arr_time", "arr_time", "arr_delay", "arr_delay_minutes",
        "cancelled", "diverted", "scheduled_elapsed_time",
        "actual_elapsed_time", "air_time", "distance",
        "carrier_delay", "weather_delay", "nas_delay",
        "security_delay", "late_aircraft_delay",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "arr_delay_minutes" in df.columns:
        df["arrival_delay_15"] = (df["arr_delay_minutes"] >= 15).astype(int)
        df["arrival_delay_60"] = (df["arr_delay_minutes"] >= 60).astype(int)

    if "dep_delay_minutes" in df.columns:
        df["departure_delay_15"] = (df["dep_delay_minutes"] >= 15).astype(int)

    if "cancelled" in df.columns:
        df["cancelled"] = df["cancelled"].fillna(0).astype(int)

    if "diverted" in df.columns:
        df["diverted"] = df["diverted"].fillna(0).astype(int)

    return df


def main() -> None:
    raw_files = find_raw_files()

    if not raw_files:
        raise FileNotFoundError(
            "No raw BTS files found. Put a BTS .csv or .zip file inside data/raw/"
        )

    frames = []
    for file in raw_files:
        raw = read_raw_file(file)
        clean = clean_columns(raw)
        clean = engineer_features(clean)
        frames.append(clean)

    final_df = pd.concat(frames, ignore_index=True)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    final_df.to_parquet(OUTPUT_FILE, index=False)

    print("\nSaved cleaned data:")
    print(OUTPUT_FILE)
    print("\nRows:", len(final_df))
    print("Columns:", len(final_df.columns))
    print("\nColumn names:")
    print(list(final_df.columns))

    if "arrival_delay_15" in final_df.columns:
        print("\nArrival delay >= 15 min rate:")
        print(round(final_df["arrival_delay_15"].mean() * 100, 2), "%")

    if "cancelled" in final_df.columns:
        print("\nCancellation rate:")
        print(round(final_df["cancelled"].mean() * 100, 2), "%")


if __name__ == "__main__":
    main()

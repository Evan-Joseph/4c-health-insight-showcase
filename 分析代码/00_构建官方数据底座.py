from __future__ import annotations

import csv
import io
import json
import tarfile
from pathlib import Path

import duckdb
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "比赛数据集" / "官方基础数据集_20260322.tar.gz"
EXTRACT_DIR = ROOT / "比赛数据集" / "官方基础数据_20260322"
OUTPUT_DIR = ROOT / "分析输出" / "官方数据底座"

GBD_DIR = "input/GBDData33943394/全球主要国家死亡原因估算数据/全球主要国家死亡原因"
RISK_DIR = "input/DBD_CRA47594759/全球各国健康风险因素估算数据/全球各国健康风险因素数据"
WDI_CSV = "input/WDI_SE35873587/WDI_CSV/WDI_CSV/WDICSV.csv"
WDI_SERIES = "input/WDI_SE35873587/WDI_CSV/WDI_CSV/WDISeries.csv"
WDI_COUNTRY = "input/WDI_SE35873587/WDI_CSV/WDI_CSV/WDICountry.csv"
HNP_CSV = "input/WB_HNP22122212/全球各国健康营养和人口统计数据/全球各国健康营养和人口统计数据/WB_HNP.csv"
HNP_GLOSSARY = "input/WB_HNP22122212/全球各国健康营养和人口统计数据/全球各国健康营养和人口统计数据/Glossary-健康营养与人口统计.csv"


def ensure_dirs() -> None:
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def extract_archive() -> None:
    if any(EXTRACT_DIR.iterdir()):
        return
    with tarfile.open(ARCHIVE, "r:gz") as tar:
        tar.extractall(EXTRACT_DIR)


def build_long_wdi(con: duckdb.DuckDBPyConnection) -> Path:
    years = ", ".join(f"'{y}'" for y in range(2000, 2024))
    out = OUTPUT_DIR / "wdi_long.parquet"
    con.execute(
        f"""
        COPY (
          WITH raw AS (
            SELECT
              "Country Name" AS country_name,
              "Country Code" AS country_code,
              "Indicator Name" AS indicator_name,
              "Indicator Code" AS indicator_code,
              year,
              value AS raw_value
            FROM read_csv_auto('{(EXTRACT_DIR / WDI_CSV).as_posix()}', HEADER=TRUE)
            UNPIVOT (value FOR year IN ({years}))
          )
          SELECT
            country_name,
            country_code,
            indicator_name,
            indicator_code,
            CAST(year AS INTEGER) AS year,
            TRY_CAST(NULLIF(raw_value, '') AS DOUBLE) AS value
          FROM raw
          WHERE raw_value IS NOT NULL
            AND raw_value NOT IN ('', '..')
        ) TO '{out.as_posix()}' (FORMAT PARQUET)
        """
    )
    return out


def build_hnp_filtered(con: duckdb.DuckDBPyConnection) -> Path:
    out = OUTPUT_DIR / "hnp_2000_2023.parquet"
    con.execute(
        f"""
        COPY (
          SELECT
            REF_AREA AS country_code,
            REF_AREA_LABEL AS country_name,
            INDICATOR AS indicator_code,
            INDICATOR_LABEL AS indicator_name,
            SEX,
            SEX_LABEL,
            AGE,
            AGE_LABEL,
            URBANISATION,
            URBANISATION_LABEL,
            CAST(TIME_PERIOD AS INTEGER) AS year,
            TRY_CAST(OBS_VALUE AS DOUBLE) AS value,
            OBS_VALUE
          FROM read_csv_auto('{(EXTRACT_DIR / HNP_CSV).as_posix()}', HEADER=TRUE)
          WHERE TRY_CAST(TIME_PERIOD AS INTEGER) BETWEEN 2000 AND 2023
        ) TO '{out.as_posix()}' (FORMAT PARQUET)
        """
    )
    return out


def build_gbd_long(con: duckdb.DuckDBPyConnection) -> Path:
    out = OUTPUT_DIR / "gbd_death_long.parquet"
    frames = []
    for csv_path in sorted((EXTRACT_DIR / GBD_DIR).glob("*.csv")):
        df = pd.read_csv(csv_path)
        df["source_file"] = csv_path.name
        frames.append(df)
    combined = pd.concat(frames, ignore_index=True)
    combined = combined.rename(
        columns={
            "Population": "population",
            "地理位置": "country_name_cn",
            "年份": "year",
            "年龄": "age_group",
            "性别": "sex",
            "死亡或受伤原因": "cause_name",
            "测量": "measure",
            "数值": "value",
            "下限": "lower",
            "上限": "upper",
        }
    )
    for col in ["year", "value", "lower", "upper"]:
        combined[col] = pd.to_numeric(combined[col], errors="coerce")
    combined.to_parquet(out, index=False)
    return out


def build_risk_long(con: duckdb.DuckDBPyConnection) -> Path:
    out = OUTPUT_DIR / "gbd_risk_long.parquet"
    frames = []
    for csv_path in sorted((EXTRACT_DIR / RISK_DIR).glob("*.csv")):
        df = pd.read_csv(csv_path)
        df["source_file"] = csv_path.name
        frames.append(df)
    combined = pd.concat(frames, ignore_index=True)
    combined = combined.rename(
        columns={
            "Population": "population",
            "地理位置": "country_name_cn",
            "年份": "year",
            "年龄": "age_group",
            "性别": "sex",
            "死亡或受伤原因": "outcome_scope",
            "风险因素": "risk_name",
            "测量": "measure",
            "数值": "value",
            "下限": "lower",
            "上限": "upper",
        }
    )
    for col in ["year", "value", "lower", "upper"]:
        combined[col] = pd.to_numeric(combined[col], errors="coerce")
    combined.to_parquet(out, index=False)
    return out


def load_csv_from_tar(path_in_tar: str) -> list[dict[str, str]]:
    with tarfile.open(ARCHIVE, "r:gz") as tar:
        extracted = tar.extractfile(path_in_tar)
        if extracted is None:
            raise FileNotFoundError(path_in_tar)
        reader = csv.DictReader(io.TextIOWrapper(extracted, encoding="utf-8-sig", newline=""))
        return list(reader)


def build_inventory() -> None:
    gbd_2023 = load_csv_from_tar(
        "input/GBDData33943394/全球主要国家死亡原因估算数据/全球主要国家死亡原因/2023.csv"
    )
    risk_2023 = load_csv_from_tar(
        "input/DBD_CRA47594759/全球各国健康风险因素估算数据/全球各国健康风险因素数据/2023.csv"
    )
    inventory = {
        "gbd_2023": {
            "rows": len(gbd_2023),
            "countries": len({r["地理位置"] for r in gbd_2023 if r["Population"] == "全人口"}),
            "causes": sorted({r["死亡或受伤原因"] for r in gbd_2023 if r["死亡或受伤原因"]}),
            "measures": sorted({r["测量"] for r in gbd_2023 if r["测量"]}),
        },
        "risk_2023": {
            "rows": len(risk_2023),
            "countries": len({r["地理位置"] for r in risk_2023 if r["Population"] == "全人口"}),
            "risks": sorted({r["风险因素"] for r in risk_2023 if r["风险因素"]}),
            "measures": sorted({r["测量"] for r in risk_2023 if r["测量"]}),
        },
    }
    (OUTPUT_DIR / "官方数据结构速览.json").write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def build_priority_indicator_matrix() -> None:
    priority_codes = [
        "SH_UHC_SCI",
        "SH_UHC_SCI_NCD",
        "SH_UHC_SCI_CAPACITY",
        "SH.XPD.OOPC.CH.ZS",
        "SH.XPD.CHEX.PC.CD",
        "SH.XPD.GHED.CH.ZS",
        "EN.ATM.PM25.MC.M3",
        "SP.POP.65UP.TO.ZS",
        "SP.URB.TOTL.IN.ZS",
        "SH.MED.PHYS.ZS",
        "SH.MED.NUMW.P3",
        "SH.MED.BEDS.ZS",
        "SH.PRV.SMOK",
        "SH.STA.DIAB.ZS",
        "SH.DYN.NCOM.ZS",
    ]
    con = duckdb.connect()
    wdi_long = OUTPUT_DIR / "wdi_long.parquet"
    query = f"""
    WITH base AS (
      SELECT indicator_code, indicator_name, year, country_code
      FROM read_parquet('{wdi_long.as_posix()}')
      WHERE indicator_code IN ({", ".join(repr(code) for code in priority_codes)})
    )
    SELECT
      indicator_code,
      MIN(indicator_name) AS indicator_name,
      COUNT(*) AS country_years,
      COUNT(DISTINCT country_code) AS countries,
      MIN(year) AS min_year,
      MAX(year) AS max_year
    FROM base
    GROUP BY 1
    ORDER BY 1
    """
    df = con.execute(query).df()
    df.to_csv(OUTPUT_DIR / "优先指标可用性矩阵.csv", index=False)


def main() -> None:
    ensure_dirs()
    extract_archive()
    con = duckdb.connect()
    build_gbd_long(con)
    build_risk_long(con)
    build_long_wdi(con)
    build_hnp_filtered(con)
    build_inventory()
    build_priority_indicator_matrix()
    print("official data base built:", OUTPUT_DIR)


if __name__ == "__main__":
    main()

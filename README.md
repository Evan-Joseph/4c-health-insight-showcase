# 4C Health Insight Showcase / 从治得上到治得起

Public showcase repository for a China Collegiate Computing Contest health-data insight project.

The project studies global health transition from 2000 to 2023, with scenario projections toward 2026 and 2030. It focuses on chronic-disease transition, health-system capacity, financial protection, country typology, and intervention priorities.

This public version keeps the reproducible analysis skeleton, environment setup, and final research plan. Competition-private notes, source archives, personal information, recommendation letters, and large datasets are intentionally excluded.

## Project Highlights

- Built a research narrative around the gap between global chronic-disease transition and uneven health-system response.
- Designed an analysis pipeline covering disease-spectrum transition, risk-spectrum transition, health-system capacity, financial protection, country typology, and future pressure.
- Prepared a reproducible data-base construction script for official competition data.
- Used public health indicators such as GBD-style mortality/risk estimates, WDI, HNP, UHC service coverage, health expenditure, PM2.5, urbanization, and aging indicators.
- Framed country groups with a "transition pressure × system capacity" typology, supporting interpretable policy recommendations.

## My Role

- Led the research planning, analysis-route design, code organization, and competition presentation preparation.
- Built the initial official-data ingestion pipeline and reproducible environment setup.
- Organized the final research narrative, indicator system, country-typing framework, and forecasting plan.

## Repository Structure

```text
.
├── 分析代码/
│   └── 00_构建官方数据底座.py
├── 环境配置/
│   ├── conda-4c-health.yml
│   └── .env.local.example
├── 最终参赛方案.md
└── README.md
```

## Quick Start

```bash
conda env create -f 环境配置/conda-4c-health.yml
conda activate 4c-health
python 分析代码/00_构建官方数据底座.py
```

The script expects the official competition archive at:

```text
比赛数据集/官方基础数据集_20260322.tar.gz
```

Generated files are written to:

```text
分析输出/官方数据底座/
```

## Data And Privacy Boundary

- Official competition datasets and generated outputs are not included in this public repository.
- Private work logs, raw prompt traces, personal information, recommendation materials, and local archives are not included.
- Environment files are examples only. Real API keys should be stored locally and never committed.

## Status

This is a showcase and reproducibility skeleton, not a complete public release of all competition materials.

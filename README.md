# BurnWise

**A geospatial dashboard for exploring satellite-derived burn signals and reviewing agricultural plot data in Tha Tako, Nakhon Sawan, Thailand.**

BurnWise brings plot-level screening results, imagery coverage, monthly summaries and preliminary satellite-product comparisons into a Streamlit application. It helps users identify what the observations support and which plots need further review before field or policy decisions.

## Project highlights

- Includes **47,311 agricultural plot records** in the bundled REVIEWED(4) assessment.
- Separates burn signals, plots not meeting the burn-signal criterion and insufficient imagery.
- Provides plot search, subdistrict filters, interactive charts, maps and CSV/Excel exports.
- Checks the bundled master file against a SHA-256 hash recorded in its run manifest.
- Includes a demonstration of access-related prioritization, with simulated inputs explicitly labelled.
- **Competition achievement:** the BurnWise team advanced to the final 12 teams from 80 entrants.

## My contribution

**Rattanatham Saopha — third-year undergraduate student, Chiang Mai University**

My responsibilities in the BurnWise team included:

- Coordinating project work and implementation tasks.
- Writing Python code for the project and dashboard.
- Retrieving and processing satellite imagery in the upstream Google Earth Engine workflow.

BurnWise is a team project. These responsibilities describe my contribution rather than claiming sole authorship of the entire system.

## What users can explore

| View | Purpose |
| --- | --- |
| From red plots to measures | Explore an illustrative prioritization workflow and clearly labelled simulated access and household inputs. |
| Overview | Review plot counts, imagery sufficiency and monthly screening summaries. |
| Explore plots | Search plot IDs, inspect plot details and locations, and export filtered records. |
| Data quality | Review observation coverage, exclusions and records requiring verification. |
| Evaluation | Inspect preliminary agreement with the GISTDA reference product and table/raster discrepancies. |
| About | Read project context, methodology and interpretation limits. |

The application includes an offline English display adapter. Source identifiers and exported data retain their original values.

## Workflow and repository scope

The broader project retrieves and processes satellite imagery upstream using Google Earth Engine. This repository contains the **dashboard and exported assessment data**, rather than the complete upstream image-processing notebook.

1. The upstream workflow prepares burn-signal and observation-coverage results.
2. Results are summarized into plot-level tables and monthly audit outputs.
3. A run manifest records the assessment settings and master-file hash.
4. The dashboard loads the exported files for filtering, visualization and review.

Running this dashboard **does not call Earth Engine or require Earth Engine credentials**. It displays precomputed results; it does not recalculate the satellite assessment.

## Included assessment snapshot

The following figures describe the bundled REVIEWED(4) export, rather than a live monitoring feed.

| Item | Bundled value |
| --- | --- |
| Pilot area | Tha Tako District, Nakhon Sawan, Thailand |
| Total plot records | 47,311 |
| Plots eligible for analysis | 42,190 |
| Plots with insufficient imagery | 5,121 |
| Plots with a burn signal | 3,403 |
| Plots not meeting the burn-signal criterion | 38,787 |
| Pre-period | October 1–December 31, 2025 |
| Post-period | January 1–31, 2026 |
| dNBR threshold | 0.20999151812466055 |
| Threshold method | Positive-dNBR Otsu experimental baseline |

Assessment settings come from [`data/burnwise_run_manifest.json`](data/burnwise_run_manifest.json). Monthly summaries also cover February–May 2026 and must be interpreted with their coverage and method-review flags.

## Technology

| Layer | Tools |
| --- | --- |
| Dashboard | Python, Streamlit |
| Tabular processing | pandas, NumPy |
| Interactive visualization | Plotly |
| Data exports | CSV, gzip-compressed CSV, JSON, XlsxWriter |
| Upstream satellite processing | Google Earth Engine, outside the dashboard runtime |

## Run locally

Clone this repository and install the dependencies in a Python environment:

```bash
git clone https://github.com/670510747/burnwise-dashboard.git
cd burnwise-dashboard
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Keep the supplied `data/`, `assets/` and `.streamlit/` directories alongside the Python files. The included assessment files are loaded automatically. A CSV upload can override the main plot table for the current session.

## Repository guide

| File or directory | Role |
| --- | --- |
| `app.py` | Streamlit application, data loading, charts and navigation |
| `burnwise_policy.py` | Prioritization demonstration and simulated-input handling |
| `english_ui.py` | Offline English display adapter |
| `requirements.txt` | Dashboard dependencies |
| `data/` | Exported plot data, assessment metadata and audit tables |
| `assets/` | Local font asset and its license notice |
| `.streamlit/config.toml` | Streamlit theme configuration |
| `export_web_bundle.py` | Helper for exporting results from an existing completed notebook kernel |

`export_web_bundle.py` is not needed to launch the included dashboard. It requires the completed REVIEWED(4) notebook state and is not a standalone satellite-processing pipeline. The upstream notebook is not included in this repository.

## Interpretation and limitations

- **Screening is not field confirmation.** A burn signal is not proof that a particular person burned a plot. A plot below the criterion is not proof of no burning or of tillage.
- **Insufficient imagery is a separate outcome.** Missing or inadequate observations must not be counted as confirmed no-burn cases.
- **GISTDA agreement is preliminary.** Comparison metrics describe agreement with a satellite reference product, not accuracy established through independent field ground truth. Product lineage remains pending review.
- **Coverage varies by month.** The bundled May baseline has 7.52% coverage, so its result must not be interpreted as complete monthly burned area.
- **Method checks remain open.** The dashboard reports table/raster discrepancies and method-review flags rather than treating all results as validated.
- **Access prioritization is partly simulated.** Collection facilities are unconfirmed, some socioeconomic inputs are simulated, and distance estimates must not be presented as verified road routes. The manifest reports zero plots ready for access analysis in this assessment.

These limitations are part of the project results and should remain visible when presenting BurnWise as a portfolio project.

## Further documentation

- [Thai assessment and export notes](README_TH.md) — historical REVIEWED(4) handoff notes; some packaging-status statements predate the currently included master file.
- [English UI update notes](README_EN_UPDATE.txt).

The repository documents an academic team project. Reuse of code and data is subject to the applicable permissions and source terms; no new license is granted by this README.

# Data Ingestion

This document defines the initial data-ingestion workflow for the Football Match Result Predictor. The first supported source is historical Football-Data-style CSV data. A future API provider can be added through a separate source adapter without changing the downstream validation and feature-engineering contracts.

## 1. Purpose and scope

The ingestion layer is responsible for importing historical match records, normalizing their structure, validating data quality, preserving source provenance, and making reliable records available to feature engineering and model training.

The project predicts the **full-time result** using three classes:

- `H` — home win
- `D` — draw
- `A` — away win

The supplied Football-Data reference says its data are CSV and spreadsheet-ready. It also notes that some abbreviations—particularly bookmaker odds—are no longer in use and that some fields relate to earlier seasons. Therefore, ingestion must inspect the actual file schema rather than assume every documented field is present.

## 2. Supported input

### Initial source: CSV

The initial importer should accept a configurable CSV path. The project notebook has previously been configured to read `epl_2024_2025.csv`, but that file's exact schema and contents must be verified when it is available.

### Future source: API

When an API provider is selected, implement a separate adapter that maps its response into the same normalized match-record structure used by the CSV importer. API credentials, rate limits, update cadence, historical coverage, and licensing remain provider-specific decisions and should be documented when the provider is chosen.

## 3. Ingestion workflow

1. **Locate and identify the source.** Resolve the configured path and record the source name, file name, import timestamp, league/division, and season where known.
2. **Read the file.** Load the CSV while preserving the original file. Detect encoding or delimiter issues explicitly rather than silently accepting a malformed import.
3. **Inspect the header.** Compare the actual columns with the expected Football-Data fields documented in [`data-dictionary.md`](data-dictionary.md). Optional fields vary by league and season.
4. **Normalize column names.** Remove accidental leading/trailing whitespace and map documented aliases only where their meaning is equivalent. For example, `HG` may be an alias for `FTHG`, `AG` for `FTAG`, and `Res` for `FTR`. Keep a record of any alias mapping applied.
5. **Normalize dates and times.** The source documents `Date` as `dd/mm/yy` and `Time` as kickoff time. Parse using the declared format where possible; flag invalid or ambiguous values. Do not assume a timezone when the source does not provide one.
6. **Normalize team and competition identifiers.** Trim team-name whitespace and apply an explicit, reviewable mapping for known name variations. Preserve the original names for traceability. Do not merge similarly named teams without confirmation.
7. **Validate types and values.** Check numeric fields, target labels, scores, missing values, duplicates, and consistency rules described below.
8. **Assign league and season.** `Div` is the league-division field, not necessarily a complete season identifier. Use trusted file metadata or explicit import configuration to assign the season; do not infer it solely from `Div`.
9. **Handle duplicates and corrections.** Detect likely duplicate fixtures and report them. Do not silently drop records or overwrite previously imported results without a documented rule.
10. **Persist normalized data and an import report.** Record accepted, rejected, duplicate, and warning counts, along with the schema and normalization decisions.

## 4. Required and optional fields

For a completed match used to train the full-time-result model, the core logical fields are:

| Logical field | Source field(s) | Ingestion treatment |
|---|---|---|
| League/division | `Div` | Required when the dataset contains multiple competitions or competition identity is not supplied separately. |
| Match date | `Date` | Required for chronological splitting and historical feature construction. |
| Home team | `HomeTeam` | Required. |
| Away team | `AwayTeam` | Required. |
| Full-time result | `FTR` or `Res` | Required training target for a completed match. |
| Full-time home goals | `FTHG` or `HG` | Recommended for validation and historical goal-based features. |
| Full-time away goals | `FTAG` or `AG` | Recommended for validation and historical goal-based features. |

`Time`, half-time fields, match statistics, bookmaker odds, total-goals odds, and Asian-handicap fields are optional at ingestion. Their presence does not mean they are safe model inputs. Refer to the data dictionary for the source's definitions and coverage notes.

## 5. Validation rules

### Structural validation

- Confirm the CSV can be read and contains the required logical columns.
- Report missing optional columns without treating them as errors by default.
- Detect duplicate column names and unsupported or conflicting aliases.
- Record the row count and column list before transformations.

### Match validation

- Parse `Date` using the source's documented `dd/mm/yy` format where applicable.
- Confirm `HomeTeam` and `AwayTeam` are non-empty and do not identify the same team unless a valid source-specific reason is documented.
- For completed results, allow only `H`, `D`, and `A` in `FTR`/`Res` after normalization.
- Where both full-time scores and the result are present, check consistency: home goals greater than away goals implies `H`; equal goals implies `D`; home goals fewer than away goals implies `A`.
- Scores and count statistics should be numeric when present. Flag invalid values for review rather than coercing them silently.
- Treat missing statistics as missing, not as zero. The source explicitly indicates that match-statistic availability varies.
- Check that dates fall within the configured competition season when season boundaries are known.

Validation should produce a clear report. Decide explicitly whether each failure is fatal, causes a row to be quarantined, or is a non-blocking warning. Preserve rejected rows and reasons where practical so the import can be audited.

## 6. Leakage prevention and prediction-time eligibility

The intended prediction is made **before kickoff**. Ingestion should preserve fields needed for historical analysis, but downstream feature selection must distinguish source data from prediction-time features.

### Target and post-match fields

- `FTR` / `Res` is the target, not an input feature.
- `FTHG` / `HG` and `FTAG` / `AG` are final scores. They may validate the result and support features for *later* fixtures, but must not be used as inputs for predicting the same match.
- `HTR`, `HTHG`, and `HTAG` describe the half-time state and are not available before kickoff.
- Match statistics such as shots, shots on target, corners, fouls, offsides, cards, attendance as recorded at the match, and referee or other fields must be assessed for availability and timing. Statistics collected during or after the target match must not be used as pre-match inputs.

### Odds

The supplied reference describes the listed bookmaker odds as **pre-closing odds** and notes that closing odds use a `C` suffix after the bookmaker abbreviation, `Max`, or `Avg` (for example, `B365CH`). Do not assume that any odds column is available at the model's prediction cutoff merely because it appears in a historical CSV. Confirm the collection timing and define a consistent cutoff before using odds as predictors.

### Historical features

Past match outcomes and statistics can contribute to rolling form, league position, goal difference, goals-for/against averages, rest days, or head-to-head summaries for a future fixture only when the information was available before that fixture. For matches on the same date where kickoff ordering is unavailable, compute their pre-match features from the same pre-date state before applying any results from that date.

## 7. Duplicate handling and re-imports

A match can appear more than once due to repeated downloads, merged files, or corrected records. Use a candidate match identity based on competition, season, date/time when reliable, home team, and away team. This is a detection aid, not proof that two records are identical.

- Report exact duplicates separately from possible duplicates.
- Do not automatically discard conflicting records with different scores or results.
- Keep source provenance so conflicting values can be traced to their input file.
- Make imports repeatable: importing the same unchanged file twice should not create duplicate canonical match records.
- If a source corrects a historical result, record the correction or update according to a documented policy and mark dependent engineered features as stale for rebuilding.

## 8. Provenance and import report

For each import, retain as available:

- source/provider name and original file name;
- file checksum or another stable source fingerprint;
- import timestamp;
- league/division and season assignment, including how they were determined;
- original column names and normalized column mappings;
- accepted, rejected, duplicate, and warning counts;
- date parsing and team-name normalization decisions;
- data corrections or manual overrides;
- data dictionary and feature-schema version used by downstream processing.

The supplied reference lists these source notes:

- Full-time and half-time results: XScores (`http://www.xscores.com`).
- Match statistics: BBC, Flashscore, ESPN Soccer, Bundesliga.de, Gazzetta.it, and Football.fr.
- Betting odds: Betbrain.com, Oddsportal.com, and individual bookmakers.
- Weekend odds were collected on Friday afternoons; midweek odds on Tuesday afternoons.
- Additional statistics for the 2000/01 and 2001/02 English, Scottish, and German leagues were sourced from Sports.com, which the reference says is no longer available under its former ownership.

These notes describe the supplied reference and do not independently verify current availability, licensing, or the provenance of any particular file. Verify the metadata and terms associated with the actual dataset being imported.

## 9. Processed output and downstream contract

The normalized output should use consistent field names and types and preserve a link to the raw source record. At minimum, downstream processing needs stable match identity, competition/season, date, home team, away team, and (for completed historical matches) full-time result. Scores and optional statistics should remain available for validation and historical feature calculation.

A practical separation is:

- **Raw:** source file exactly as received.
- **Normalized:** consistent names, parsed dates, standardized team/competition identifiers, validated result values, and provenance.
- **Features:** derived pre-match features generated without using information from the target match's future.

Do not overwrite raw files with normalized data. Do not calculate or freeze feature values during ingestion if their correctness depends on chronological history; feature generation belongs in the feature-engineering stage.

## 10. Testing checklist

- [ ] Valid CSV imports with the expected core columns.
- [ ] Missing required columns produce a clear error.
- [ ] Missing optional columns are reported without inventing values.
- [ ] `FTHG`/`HG`, `FTAG`/`AG`, and `FTR`/`Res` aliases are handled consistently.
- [ ] Dates in `dd/mm/yy` format parse correctly; invalid dates are reported.
- [ ] Unexpected result labels and score/result contradictions are detected.
- [ ] Blank team names, invalid numeric values, and possible duplicate fixtures are reported.
- [ ] Missing statistics remain missing rather than becoming zero automatically.
- [ ] Season assignment is explicit and repeatable.
- [ ] Re-importing the same file does not duplicate canonical matches.
- [ ] Conflicting corrected results are surfaced for review.
- [ ] Target-match outcome and post-match fields are excluded from pre-match predictors.
- [ ] Import provenance and summary counts are recorded.

## Related documentation

- [Data Dictionary](data-dictionary.md) — source field definitions and source-specific notes.
- [Project README](../README.md) — project overview and setup instructions, when maintained in the repository root.

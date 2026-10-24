# Database Design

This document defines a proposed persistence model for the Football Match Result Predictor. It supports historical match ingestion, multi-league and multi-season standings, leakage-safe feature generation, model versioning, and future prediction APIs.

**Status:** design specification, not a claim that a database or API has already been implemented. SQLite is the recommended starting point for local development; PostgreSQL can be adopted later without changing the logical model substantially.

## 1. Goals and design principles

The database should:

- distinguish leagues, seasons, teams, and individual fixtures;
- preserve source provenance and import history;
- store completed results separately from pre-match features;
- calculate standings and features from information available before kickoff;
- prevent records from different leagues or seasons from being mixed accidentally;
- support repeatable imports and explicit corrections to historical results;
- identify which feature schema, data revision, and model version produced a prediction;
- enforce integrity through primary keys, foreign keys, uniqueness constraints, and validation.

Store normalized source records as the source of truth. Treat standings snapshots and engineered features as derived data that can be regenerated when source data or feature definitions change.

## 2. Entity relationship overview

```text
League 1 ─── * Season
Season * ─── * Team            (through SeasonTeam)
Season 1 ─── * Match
Team   1 ─── * Match           (home team and away team)
Match  1 ─── * MatchFeature
Season 1 ─── * StandingSnapshot / StandingRow
ModelVersion 1 ─── * Prediction
Match 0..1 ─── * Prediction   (a prediction may refer to a known fixture)
ImportBatch 1 ─── * SourceRecord / Match provenance
```

A season belongs to one league. Teams can participate in many seasons. A match belongs to one season and references two teams registered for that season.

## 3. Tables

The columns below are the recommended logical schema. Adapt types and generated-key syntax to the selected database engine.

### 3.1 `leagues`

Stores competition identity and configurable standings rules.

| Column | Suggested type | Rules / purpose |
|---|---|---|
| `id` | integer / UUID | Primary key. |
| `code` | text | Stable internal code; unique. |
| `name` | text | Human-readable competition name. |
| `country` | text, nullable | Optional competition country/region. |
| `points_for_win` | integer | Default `3`. |
| `points_for_draw` | integer | Default `1`. |
| `points_for_loss` | integer | Default `0`. |
| `standings_rules` | JSON/text, nullable | Competition-specific tie-break configuration. |
| `created_at` | timestamp | Record creation time. |
| `updated_at` | timestamp | Last metadata update. |

Do not assume that a source field such as `Div` uniquely identifies a league and season. Map source values to stable internal league codes during import.

### 3.2 `seasons`

Represents one league's season.

| Column | Suggested type | Rules / purpose |
|---|---|---|
| `id` | integer / UUID | Primary key. |
| `league_id` | FK | References `leagues.id`. |
| `name` | text | For example, `2024-2025`; unique within a league. |
| `start_date` | date, nullable | Configured season start. |
| `end_date` | date, nullable | Configured season end. |
| `status` | text | For example, `planned`, `active`, `completed`; constrain allowed values. |
| `created_at` | timestamp | Record creation time. |

**Constraint:** `UNIQUE(league_id, name)`. A season ID must not be inferred solely from a division abbreviation; it should be assigned from import configuration or reliable source metadata.

### 3.3 `teams`

Stores a stable identity for each club/team.

| Column | Suggested type | Rules / purpose |
|---|---|---|
| `id` | integer / UUID | Primary key. |
| `name` | text | Canonical display name. |
| `normalized_name` | text | Normalized name used for matching; index it. |
| `external_id` | text, nullable | Provider identifier if available. |
| `created_at` | timestamp | Record creation time. |
| `updated_at` | timestamp | Last metadata update. |

A team may be known by different names in different sources or seasons. Use a separate alias/mapping table if necessary rather than silently creating duplicate teams or rewriting historical identity.

### 3.4 `season_teams`

Registers the complete set of teams expected to participate in a league-season. This is important for showing all teams before any matches have been played.

| Column | Suggested type | Rules / purpose |
|---|---|---|
| `season_id` | FK | References `seasons.id`. |
| `team_id` | FK | References `teams.id`. |
| `registration_source` | text, nullable | How the registration was established. |
| `created_at` | timestamp | Registration timestamp. |

**Primary key:** `(season_id, team_id)`. Initialize standings for each registered team with zero matches, points, goals for, and goals against. If no matches have been played, alphabetical ordering is a deterministic display default, not a claim about official competition ranking.

### 3.5 `import_batches`

Tracks each source-file or provider import for auditability and safe re-runs.

| Column | Suggested type | Rules / purpose |
|---|---|---|
| `id` | integer / UUID | Primary key. |
| `source_name` | text | Source/provider or file family. |
| `source_location` | text, nullable | File name or source identifier; avoid storing secrets. |
| `file_checksum` | text, nullable | Hash of the imported file where applicable. |
| `started_at` | timestamp | Import start time. |
| `completed_at` | timestamp, nullable | Import completion time. |
| `status` | text | `running`, `completed`, `completed_with_warnings`, `failed`. |
| `rows_seen` | integer | Total input rows. |
| `rows_inserted` | integer | New records created. |
| `rows_updated` | integer | Existing records changed under an explicit correction policy. |
| `rows_rejected` | integer | Invalid rows rejected/quarantined. |
| `rows_duplicate` | integer | Duplicate rows detected. |
| `report` | JSON/text, nullable | Validation messages and summary counts. |

Do not use the import-batch ID as the identity of a match. The same fixture may be seen in more than one import.

### 3.6 `matches`

Stores normalized fixture information and completed results. One row represents one fixture, including a scheduled fixture whose result is not yet known.

| Column | Suggested type | Rules / purpose |
|---|---|---|
| `id` | integer / UUID | Primary key. |
| `season_id` | FK | References `seasons.id`. |
| `home_team_id` | FK | References `teams.id`. |
| `away_team_id` | FK | References `teams.id`; must differ from home team. |
| `kickoff_at` | timestamp, nullable | Use timezone-aware timestamps where supported and trustworthy. |
| `match_date` | date | Competition-local date used for date-batched processing. |
| `status` | text | For example, `scheduled`, `completed`, `postponed`, `cancelled`; constrain values. |
| `home_goals` | integer, nullable | Full-time home goals; non-negative when present. |
| `away_goals` | integer, nullable | Full-time away goals; non-negative when present. |
| `full_time_result` | text, nullable | `H`, `D`, or `A`; populated for completed matches. |
| `half_time_home_goals` | integer, nullable | Historical/source field only; not a same-match pre-kickoff feature. |
| `half_time_away_goals` | integer, nullable | Historical/source field only. |
| `half_time_result` | text, nullable | Historical/source field only. |
| `source_match_id` | text, nullable | Source's fixture ID when provided. |
| `source_name` | text, nullable | Primary source label, if useful. |
| `first_import_batch_id` | FK, nullable | References `import_batches.id`. |
| `last_import_batch_id` | FK, nullable | References the latest import that changed this row. |
| `created_at` | timestamp | Record creation time. |
| `updated_at` | timestamp | Last modification time. |

Recommended constraints and indexes:

- `CHECK(home_team_id <> away_team_id)`.
- Goal counts must be non-negative when present.
- If `status = 'completed'`, require full-time goals and a valid full-time result.
- Validate that the stored result agrees with the scores: higher home score = `H`, equal scores = `D`, higher away score = `A`.
- Add an index on `(season_id, match_date, kickoff_at)` for chronological processing.
- Add indexes on `(home_team_id, match_date)` and `(away_team_id, match_date)` for team history queries.
- Where a reliable source fixture ID exists, enforce an appropriate uniqueness rule for it within its source/competition scope.

A universal uniqueness constraint on date + home team + away team may be too restrictive for some sources or unusual rescheduling histories. Define the match identity policy explicitly, using source IDs when reliable and otherwise a documented composite key plus duplicate review.

Detailed match statistics and odds can either be stored as typed columns in related tables or in a separate source-data table. Do not force unavailable statistics to zero. Their absence usually means the value was not supplied or collected.

### 3.7 `match_statistics` (optional)

Stores match statistics separately from core fixture identity. This separation helps make their post-kickoff timing explicit.

| Column | Suggested type | Rules / purpose |
|---|---|---|
| `match_id` | FK | References `matches.id`; unique for one row per match if using a wide table. |
| `home_shots`, `away_shots` | integer, nullable | Historical match statistics. |
| `home_shots_on_target`, `away_shots_on_target` | integer, nullable | Historical match statistics. |
| `home_corners`, `away_corners` | integer, nullable | Historical match statistics. |
| `home_fouls`, `away_fouls` | integer, nullable | Historical match statistics. |
| `home_yellow_cards`, `away_yellow_cards` | integer, nullable | Historical match statistics. |
| `home_red_cards`, `away_red_cards` | integer, nullable | Historical match statistics. |
| `raw_fields` | JSON/text, nullable | Additional source-specific fields where appropriate. |
| `source_name` | text, nullable | Provenance for the statistics. |
| `import_batch_id` | FK, nullable | Import that supplied the values. |

These fields must not be used as predictors for the same fixture in a pre-match model. Historical values may contribute to features for a later fixture only when they were available by that later fixture's cutoff.

### 3.8 `match_odds` (optional)

Use a separate table if multiple bookmakers, odds snapshots, or capture times must be retained.

| Column | Suggested type | Rules / purpose |
|---|---|---|
| `id` | integer / UUID | Primary key. |
| `match_id` | FK | References `matches.id`. |
| `bookmaker` | text | Bookmaker or market source. |
| `market` | text | For example, `1X2`. |
| `home_odds` | numeric, nullable | Positive decimal odds when valid. |
| `draw_odds` | numeric, nullable | Positive decimal odds when valid. |
| `away_odds` | numeric, nullable | Positive decimal odds when valid. |
| `captured_at` | timestamp, nullable | Time odds were captured, if known. |
| `odds_type` | text, nullable | For example, opening, snapshot, closing. |
| `source_name` | text, nullable | Provenance. |
| `import_batch_id` | FK, nullable | Import that supplied the record. |

Index `(match_id, bookmaker, market, captured_at)`. Preserve multiple snapshots rather than overwriting them if the project needs to compare prediction cutoffs. Use odds as model inputs only when the selected snapshot is demonstrably available before the prediction cutoff.

### 3.9 `standings_snapshots` and `standing_rows` (optional cache)

Standings can be calculated from completed matches, but persisted snapshots can speed up API reads and make historical state auditable. They are derived data and must be reproducible.

`standings_snapshots`:

| Column | Suggested type | Rules / purpose |
|---|---|---|
| `id` | integer / UUID | Primary key. |
| `season_id` | FK | References `seasons.id`. |
| `as_of_date` | date | Date before which results are included, defined consistently. |
| `generated_at` | timestamp | Snapshot creation time. |
| `data_revision` | text/integer | Revision of source match data used. |
| `rules_version` | text | Standings calculation rules version. |

`standing_rows`:

| Column | Suggested type | Rules / purpose |
|---|---|---|
| `snapshot_id` | FK | References `standings_snapshots.id`. |
| `team_id` | FK | References `teams.id`. |
| `position` | integer | Rank in this snapshot. |
| `played` | integer | Matches counted. |
| `won`, `drawn`, `lost` | integer | Outcome counts. |
| `goals_for`, `goals_against` | integer | Goals accumulated. |
| `goal_difference` | integer | Goals for minus goals against. |
| `points` | integer | Points accumulated. |

**Primary key:** `(snapshot_id, team_id)`. Consider `UNIQUE(snapshot_id, position)` if each rank is unique under the configured display ordering. When no matches have been played, include all `season_teams` with zero values and alphabetical display order.

If a snapshot is used for pre-match features, it must represent only results eligible before the fixture cutoff. For multiple fixtures on a date with unknown or unreliable kickoff order, generate all same-date pre-match features from the same pre-date state before applying any results from that date.

### 3.10 `match_features`

Stores engineered feature rows for training and prediction. A wide typed table is appropriate when the feature schema is stable; a versioned JSON representation can be useful while the schema is evolving. Avoid mixing incompatible schemas in one unversioned table.

| Column | Suggested type | Rules / purpose |
|---|---|---|
| `id` | integer / UUID | Primary key. |
| `match_id` | FK | References `matches.id`. |
| `feature_schema_version` | text | Exact feature definition/version. |
| `data_revision` | text/integer | Historical data revision used to generate the row. |
| `generated_at` | timestamp | Feature generation timestamp. |
| `prediction_cutoff_at` | timestamp, nullable | Information cutoff represented by the row. |
| `features` | JSON/text or typed columns | Feature values in a documented schema. |
| `feature_hash` | text, nullable | Optional hash for change detection. |

For a single current row per fixture and schema, use `UNIQUE(match_id, feature_schema_version, data_revision)` or another explicitly chosen key. If retaining multiple regenerated versions, keep the history and mark which row is current rather than overwriting without traceability.

Feature generation should be idempotent for the same match data revision, cutoff, schema version, and configuration. A corrected earlier result can change features for many later fixtures, so invalidation must cover all affected future rows in the relevant league-season/history scope.

### 3.11 `model_versions`

Records model artifacts and their compatibility metadata.

| Column | Suggested type | Rules / purpose |
|---|---|---|
| `id` | integer / UUID | Primary key. |
| `name` | text | Human-readable model name. |
| `version` | text | Version label; unique within a model name. |
| `algorithm` | text | For example, Random Forest, Logistic Regression, or XGBoost. |
| `artifact_uri` | text | File path or storage key for the serialized model bundle. |
| `feature_schema_version` | text | Required feature schema. |
| `training_data_revision` | text, nullable | Dataset revision used for training. |
| `trained_at` | timestamp | Training completion time. |
| `metrics` | JSON/text, nullable | Metrics computed from real validation/test predictions. |
| `parameters` | JSON/text, nullable | Training configuration. |
| `library_versions` | JSON/text, nullable | Relevant package versions. |
| `status` | text | For example, `candidate`, `active`, `retired`; constrain values. |

The artifact bundle should include the fitted model, preprocessing pipeline, class mapping, feature names/order, feature schema, training-data revision, and package versions. Do not assume the current notebook exports every model that it can train; the persistence workflow should validate the selected model bundle before marking it active.

### 3.12 `predictions` (optional future API table)

Stores prediction requests and results for auditability. It is not required for notebook-only experiments.

| Column | Suggested type | Rules / purpose |
|---|---|---|
| `id` | integer / UUID | Primary key. |
| `match_id` | FK, nullable | Known fixture, if one exists. |
| `model_version_id` | FK | References `model_versions.id`. |
| `requested_at` | timestamp | Prediction request time. |
| `prediction_cutoff_at` | timestamp | Time represented by the inputs. |
| `predicted_result` | text | `H`, `D`, or `A`. |
| `prob_home`, `prob_draw`, `prob_away` | numeric, nullable | Optional class probabilities; validate finite values in `[0, 1]` and sum approximately to one when all are present. |
| `input_features` | JSON/text | Exact input feature values or a secure reference to them. |
| `feature_schema_version` | text | Schema used for inference. |
| `status` | text | For example, `success`, `rejected`, `failed`. |
| `validation_message` | text, nullable | Explanation for rejected or failed requests. |

Avoid storing sensitive user data that is not needed. If prediction requests are stored, define retention and access policies. Never silently fill missing required inputs with arbitrary training medians and return the result as if the fixture were fully specified.

## 4. Key relationships and integrity rules

- A match belongs to exactly one season and references two distinct teams.
- Both teams should be registered in `season_teams` for the match's season, unless a documented import exception is under review.
- A completed match must have a valid full-time score and a result consistent with that score.
- Match statistics and odds may be missing; absence must not be interpreted as zero.
- All standings calculations must be scoped by league and season.
- Feature rows must reference a match and identify their feature schema and source-data revision.
- Model versions must declare the feature schema expected at inference.
- Predictions must identify the model version and prediction cutoff used.
- Use database transactions for a match import plus its associated provenance changes, so partial imports do not leave inconsistent state.

## 5. Import, correction, and rebuild workflow

1. Create an `import_batches` record and record the source identity/checksum where available.
2. Parse and validate the source file before changing canonical records.
3. Resolve league, season, and team mappings; quarantine ambiguous team matches for review.
4. Insert or update fixtures using the documented match-identity and correction policy.
5. Record the import batch and provenance for changed rows.
6. Validate result/score consistency and report accepted, rejected, duplicate, and updated counts.
7. If new or corrected results affect history, mark standings snapshots and feature rows stale from the earliest affected date onward in the relevant scope.
8. Regenerate derived standings/features and record the data revision, rules version, and feature schema version.
9. Run consistency checks before making refreshed data available to prediction or API consumers.

Repeat imports should be idempotent: importing an unchanged file twice should not create duplicate matches. A corrected result should be treated as a traceable update, not as an unrelated new fixture.

## 6. Indexing and query patterns

Recommended initial indexes:

- `seasons(league_id, name)` unique;
- `season_teams(season_id, team_id)` primary key;
- `matches(season_id, match_date, kickoff_at)`;
- `matches(home_team_id, match_date)` and `matches(away_team_id, match_date)`;
- unique or indexed source match identity within its source scope;
- `match_features(match_id, feature_schema_version, data_revision)`;
- `standings_snapshots(season_id, as_of_date, data_revision)`;
- `predictions(model_version_id, requested_at)` if predictions are persisted.

Useful query patterns include loading all fixtures for a league-season in chronological order, retrieving a team's previous completed matches, getting a standings snapshot as of a date, and fetching the feature row compatible with an active model version.

Avoid premature optimization. Start with indexes supporting known access patterns and verify them against actual queries as the application grows.

## 7. SQLite and PostgreSQL considerations

### SQLite for the first version

- Suitable for local development and a single-user or low-concurrency prototype.
- Enable foreign-key enforcement for every connection.
- Use transactions for imports and feature rebuild operations.
- Store timestamps in a consistent documented format; use UTC for absolute timestamps and preserve the competition-local match date separately.
- SQLite JSON support and type enforcement differ from PostgreSQL, so validate JSON and numeric inputs in the application as well.

### PostgreSQL later

- Offers stronger concurrent-write behavior and richer operational options for a deployed multi-user service.
- Consider native JSONB for flexible raw metadata, but keep frequently queried fields typed and indexed.
- Use timezone-aware timestamps for kickoff/capture events where exact times are known.
- Preserve the same logical constraints and migration tests during the database transition.

Use schema migrations from the beginning if the project will evolve beyond a disposable prototype. Do not depend on manually editing a production database schema.

## 8. Data retention and provenance

Retain enough information to explain where a match or feature came from and how it was transformed. At minimum, record source/provider or file identity, import timestamp, validation outcome, data revision, feature schema version, and model version. Store raw source rows or an auditable rejected-row report when practical, subject to file size and licensing constraints.

Do not treat a source's missing statistics as observed zeros. Do not overwrite historical odds snapshots if the application needs to reconstruct what was known at an earlier prediction cutoff.

## 9. Testing checklist

- Foreign keys reject references to missing leagues, seasons, or teams.
- A team cannot play itself in a fixture.
- Duplicate imports do not create duplicate fixtures.
- Conflicting source aliases and ambiguous team names are reported.
- Completed results agree with full-time scores.
- Scheduled/postponed fixtures can exist without a result.
- Every registered season team appears in the initial standings with zero totals.
- Standings do not mix league-seasons and apply configured tie-break rules.
- Same-date features do not use results from fixtures with unknown ordering.
- A corrected historical result invalidates affected later features and snapshots.
- Feature rows and model versions with incompatible schemas cannot be used together silently.
- Prediction probabilities and result labels are validated.
- Failed imports roll back canonical changes or leave an explicit recoverable import status.

## 10. Initial implementation recommendation

For the first database-backed iteration, implement `leagues`, `seasons`, `teams`, `season_teams`, `import_batches`, and `matches`. Add `match_statistics` and `match_odds` when their ingestion and timing rules are clear. Implement standings and feature generation as deterministic services first; persist `standings_snapshots` and `match_features` when caching or audit requirements justify it. Add `model_versions` and `predictions` when model serving or a prediction API is introduced.

This phased approach keeps the initial schema manageable while preserving the identifiers and provenance needed for a future API and multi-league workflow.

## Related documentation

- [`data-ingestion.md`](data-ingestion.md) — CSV normalization, validation, duplicates, and import reports.
- [`data-dictionary.md`](data-dictionary.md) — Football-Data source field definitions.
- [`feature-engineering.md`](feature-engineering.md) — leakage-safe standings, form, odds, and feature refresh rules.
- [`model-training.md`](model-training.md) — model evaluation and artifact versioning.
- [`prediction-api.md`](prediction-api.md) — planned prediction and standings endpoints.

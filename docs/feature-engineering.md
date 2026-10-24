# Feature Engineering

This document defines how historical match records are transformed into features for the Football Match Result Predictor. The intended task is **pre-match prediction** of the full-time result: `H` (home win), `D` (draw), or `A` (away win).

Feature engineering must be reproducible and time-aware. Every value supplied to a prediction must be calculable from information available before that fixture's kickoff. A feature that looks predictive but uses information from the target match or from the future is invalid for this task.

## 1. Objectives

The feature-engineering layer should:

- create consistent home-team and away-team features from normalized match records;
- derive standings, recent form, scoring, defensive, and rest features using past results only;
- support multiple leagues and seasons without mixing their histories;
- handle missing or incomplete historical data explicitly;
- produce the same feature names, order, types, and definitions during training and inference;
- record a feature schema/version so stored features and trained models can be checked for compatibility.

## 2. Processing principles

1. Start from validated, normalized records produced by the ingestion layer.
2. Identify each fixture by its competition, season, date, home team, and away team; use a stable match ID when available.
3. Sort completed matches by date and, when trustworthy, kickoff time. Do not assume that row order is chronological.
4. Build each fixture's features from a snapshot of history that ends strictly before the fixture.
5. Calculate features for all fixtures sharing a date from the same pre-date snapshot when kickoff ordering is unavailable or unreliable. Apply that date's results only after features for every fixture on that date have been generated.
6. Keep the target (`FTR`/`Res`) separate from the feature matrix.
7. Fit learned preprocessing—such as imputation and scaling—on training data only, preferably inside a scikit-learn `Pipeline`.
8. Persist the feature schema and generation metadata alongside processed data and model artifacts.

## 3. Feature groups

The following are recommended initial feature groups. They are a design specification, not a claim that every feature is already implemented in the notebook. Add a feature only when its source data and availability can be verified.

### 3.1 Fixture and competition context

| Feature | Meaning | Notes |
|---|---|---|
| `league_id` or encoded league | Competition identity | Use a stable competition identifier; avoid confusing `Div` with a season identifier. |
| `season_id` | Competition season | Assign during ingestion/import configuration where needed. |
| `home_team_id` | Home team identity | Prefer stable IDs or a controlled mapping over ad hoc label encoding. |
| `away_team_id` | Away team identity | Must use the same team mapping as training. |
| `days_from_season_start` | Days elapsed since season start | Optional; requires configured season start date. |

Team identities can be useful, but an encoder trained on historical teams may fail for a new or renamed team. Define an explicit unknown-team strategy and test it. Do not encode an unseen team by silently assigning an arbitrary existing class.

### 3.2 League standings before kickoff

Compute standings separately for each league and season. At season initialization, include all teams registered for that season with zero matches played, zero points, zero goals for, and zero goals against. When no matches have been played, order teams alphabetically for a deterministic initial table unless the competition has a documented alternative rule.

Recommended features:

| Feature | Definition |
|---|---|
| `home_league_position`, `away_league_position` | Rank of each team in the pre-match standings snapshot. |
| `home_league_points`, `away_league_points` | League points accumulated before the fixture. |
| `home_league_goal_difference`, `away_league_goal_difference` | Goals for minus goals against before the fixture. |
| `home_league_matches_played`, `away_league_matches_played` | Completed league matches counted before the fixture. |
| `home_league_goals_for`, `away_league_goals_for` | Total league goals scored before the fixture. |
| `home_league_goals_against`, `away_league_goals_against` | Total league goals conceded before the fixture. |
| `league_position_difference` | Home position minus away position, using one consistent sign convention. |
| `league_points_difference` | Home points minus away points. |
| `league_goal_difference_difference` | Home goal difference minus away goal difference. |

A typical default ordering is points descending, goal difference descending, goals scored descending, then team name alphabetically. Real competitions may use different tie-break rules; make the ordering configurable by competition when accurate official standings are required. Position features must be computed from the pre-match table, not the final table for the season.

If multiple fixtures occur on the same date and their kickoff order cannot be trusted, calculate all their standings features before applying any result from that date. This prevents a result from one fixture being used to predict another fixture played on the same date.

### 3.3 Recent form

Recent form summarizes each team's previous completed matches. For a configurable window of the last `N` matches, candidate features include:

- `home_form_points_avg` and `away_form_points_avg`;
- `home_form_goals_scored_avg` and `away_form_goals_scored_avg`;
- `home_form_goals_conceded_avg` and `away_form_goals_conceded_avg`;
- `home_form_goal_difference_avg` and `away_form_goal_difference_avg`;
- `home_form_win_rate` and `away_form_win_rate`;
- `home_form_draw_rate` and `away_form_draw_rate`;
- `home_form_loss_rate` and `away_form_loss_rate`;
- differences between home-team and away-team form values.

For each past match, derive points from its result (win = 3, draw = 1, loss = 0) and goals for/against from its completed score. Use a clearly documented window, such as the previous five matches, and keep the window length in the feature schema/configuration. If a team has fewer than `N` prior matches, use the available history and include a count such as `home_form_matches_available` or `away_form_matches_available` so the model can distinguish a short history from a full window.

**Important:** rolling features must be shifted so the current fixture's result and scores never contribute to its own features. Avoid calculating rolling statistics over a team's rows and then using unshifted values for the same row.

### 3.4 Venue-specific form

Home and away performance can differ by venue. Optional features can use prior matches in the relevant venue context:

- home team's average points/goals in its previous home matches;
- away team's average points/goals in its previous away matches;
- number of prior home matches for the home team and prior away matches for the away team.

Use only matches before the target fixture. Document the window length and behavior when the relevant venue history is short or absent. Avoid assuming that a team has played a fixed number of home or away fixtures at the start of a season.

### 3.5 Head-to-head history

Optional head-to-head features may summarize previous meetings between the two teams, for example:

- prior head-to-head match count;
- home-side wins, draws, and losses in those past meetings;
- average goals scored by each side in prior meetings.

Define the perspective consistently (for example, features are always expressed from the perspective of the current home and away teams), and include only meetings completed before the target kickoff. Consider a configurable lookback window. If there is no history, represent the absence explicitly with a zero count and a documented missing/default policy rather than inventing prior results.

### 3.6 Rest and schedule features

Where dates and kickoff times are reliable, candidate features include:

- `home_rest_days` and `away_rest_days` since each team's previous completed match;
- `rest_days_difference`;
- optional indicators for whether rest-day values are known.

Calculate rest from the last match that occurred before the target fixture. If timestamps or time zones are incomplete, do not fabricate precision: use date-level rest consistently or mark the value unknown. Decide how to handle season boundaries and postponed fixtures, and test those rules.

### 3.7 Odds-derived features (optional)

Bookmaker odds can provide a useful baseline or model input only when the selected odds snapshot was available before the prediction cutoff. The Football-Data reference distinguishes some closing odds with a `C` suffix and notes that collection times vary. Confirm the actual timing and meaning of each odds column before using it.

If a complete home/draw/away odds triplet is available and valid, decimal odds can be converted to raw implied probabilities:

\[
p_H^*=1/o_H,\quad p_D^*=1/o_D,\quad p_A^*=1/o_A
\]

Normalize the three values to sum to one to obtain a simple overround-adjusted probability representation:

\[
p_i = \frac{p_i^*}{p_H^*+p_D^*+p_A^*}
\]

Validate that odds are positive and finite. Do not fill a missing outcome's odds with zero, and do not create a probability triplet from an incomplete set unless a documented method explicitly supports it. Keep odds-derived features optional so the model can also be evaluated without them. Report performance against an odds-implied baseline when comparable odds are available.

## 4. Fields that must not be used for same-match pre-match prediction

The following fields are targets, final outcomes, or match-time/post-match information and must not be predictors for the same fixture:

- `FTR` / `Res` — the full-time result target;
- `FTHG` / `HG` and `FTAG` / `AG` — the target fixture's final scores;
- `HTR`, `HTHG`, and `HTAG` — half-time result and scores;
- same-match shots, shots on target, corners, fouls, cards, offsides, and other statistics recorded during or after the match;
- any final-season standings, or rolling values that accidentally include the target fixture or future fixtures.

Historical scores and statistics are not universally forbidden: they may be used to construct features for a *later* fixture after the historical result would have been known. The rule is about timing and information availability, not just column names.

Attendance, referee, or other contextual fields should be evaluated individually. Use them only if their values would genuinely be known at the chosen prediction cutoff and are available consistently enough for the intended use.

## 5. Missing values and early-season behavior

Missing values can mean different things: a statistic was not collected, a team has not played enough matches, a kickoff time is unknown, or an optional odds market was unavailable. Preserve these distinctions where practical.

- Do not replace missing match statistics with zero unless zero is the true observed value.
- For form features, calculate from available prior matches and include history counts where helpful.
- For standings, a registered team with no completed matches has zero matches, points, goals for, and goals against; this is a real initial state, not missing data.
- For optional odds, leave incomplete triplets unavailable and apply a documented policy.
- Fit imputation values on training data only. Reuse the fitted imputer at inference; never recalculate medians using the full dataset or a prediction batch.
- If required prediction inputs are absent, reject the request or return a clear validation message rather than silently manufacturing an unrealistic fixture from training medians.

The exact imputation strategy should be evaluated empirically and documented in the model configuration. If missingness indicators are added, they must be generated consistently in both training and inference.

## 6. Leakage-safe generation algorithm

A reliable first implementation can use a date-batched walk-forward process:

1. Partition records by league and season, while retaining any explicitly supported cross-season history policy.
2. Sort fixtures by date and reliable kickoff time.
3. For each date, take a snapshot containing only results from earlier dates (and earlier kickoff times only when ordering is reliable and the product's cutoff permits it).
4. Generate standings, form, venue, head-to-head, and rest features for every fixture in that date batch using the snapshot.
5. Save the generated feature rows with their fixture identifiers and feature version.
6. Only after the feature rows are generated, add that date's completed results to the history used for later dates.
7. Verify that no feature's source records occur after the fixture's prediction cutoff.

If a fixture's kickoff time is known and the application explicitly predicts at a later same-day time, a more granular event-time process may be appropriate. The cutoff and time-zone policy must be explicit rather than inferred.

## 7. Training and inference consistency

Training and production prediction must call the same feature definitions, with the same configuration and ordering. Do not maintain one set of feature calculations in a notebook and a separate, drifting implementation in an API.

Persist or record at least:

- feature names and order;
- feature schema/version;
- rolling window sizes and tie-break configuration;
- team and competition mappings;
- missing-value and unknown-team policies;
- data snapshot/revision and generation timestamp;
- model artifact identifier and compatible preprocessing pipeline version.

At inference, validate that the model's required features are present and correctly typed. If the schema does not match the model artifact, fail clearly or route through an explicitly supported compatibility process. Do not silently reorder or invent columns without validation.

## 8. Feature storage and refresh

If engineered features are persisted, store enough metadata to know which fixture, historical data revision, and feature definition produced each row. Recompute affected future features when:

- a new result or fixture is imported;
- an existing result is corrected or a fixture is rescheduled;
- team/season mappings or competition tie-break rules change;
- a feature definition or window configuration changes.

A correction to an earlier result can affect standings, rolling form, head-to-head values, and rest calculations for subsequent fixtures. Rebuilding only the corrected match's feature row is therefore insufficient. Use a documented rebuild boundary or recompute the affected league-season history.

## 9. Validation and tests

At minimum, test the following cases:

- no-match season initialization and alphabetical ordering;
- points, goal difference, goals scored, and position tie-breaks;
- league and season isolation;
- a team's first match and a team with fewer than the configured form window;
- rolling values that exclude the target match;
- multiple fixtures on one date with unknown kickoff ordering;
- head-to-head features with no prior meetings;
- missing or invalid kickoff times and rest-day features;
- incomplete, invalid, and valid odds triplets;
- postponed fixtures and corrected historical results;
- new or renamed teams;
- identical feature names, order, and types between training and inference;
- feature regeneration after an earlier match result changes.

Use small, hand-checkable fixture histories for unit tests. Add integration tests that generate features across an entire season and assert that each row only depends on eligible past data.

## 10. Acceptance criteria

Feature engineering is ready for model training when:

- every feature has a documented definition, source, and availability cutoff;
- the target result and same-match post-kickoff information are excluded from predictors;
- standings and rolling statistics are generated without future leakage;
- multiple leagues and seasons remain isolated according to the configured history policy;
- missing values and unseen teams have explicit behavior;
- the feature schema is stable and versioned;
- training and inference share the same transformations;
- unit tests cover temporal boundaries, tie-breaks, and refresh behavior.

## Related documentation

- [`data-ingestion.md`](data-ingestion.md) — source loading, normalization, and validation.
- [`data-dictionary.md`](data-dictionary.md) — Football-Data field definitions and availability notes.
- [`database-design.md`](database-design.md) — planned persistence for matches, standings, and engineered features.
- [`model-training.md`](model-training.md) — training, validation, and evaluation strategy.

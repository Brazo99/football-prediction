# League Standings

This document specifies how league tables should be initialized, updated, displayed, and used as pre-match features in the Football Match Result Predictor. It covers completed league matches and season-specific tables; it does not assume that a live data provider or standings service has already been implemented.

## 1. Purpose and scope

The standings component should:

- maintain a separate table for each league and season;
- include every team registered for that season, including teams that have not played yet;
- calculate standings from completed matches only;
- apply configurable points and tie-break rules;
- expose a reproducible standings snapshot for a fixture's pre-match prediction;
- avoid using future results when generating historical standings or model features.

Standings are both a user-facing league table and a potential source of model features. Those uses share the same underlying calculations, but historical feature generation must preserve the table as it existed before each fixture.

## 2. Core concepts

- **League:** a competition, identified by a stable internal ID.
- **Season:** one edition of a league, such as `2024-2025`.
- **Season team:** a team registered to participate in a particular league-season.
- **Completed match:** a fixture with a validated final score and result that is eligible to affect standings.
- **Standings snapshot:** the table calculated from all eligible results up to a defined cutoff.
- **Pre-match snapshot:** standings immediately before the target fixture's prediction cutoff.

Do not use a source division abbreviation such as Football-Data's `Div` as a season identifier. Map source values to a stable league and assign the season from import configuration or reliable source metadata.

## 3. Season initialization

Before the first match of a season, register the complete expected team list. The standings calculation must begin with one row per registered team, with these initial values:

| Statistic | Initial value |
|---|---:|
| Matches played (`MP`) | 0 |
| Wins (`W`) | 0 |
| Draws (`D`) | 0 |
| Losses (`L`) | 0 |
| Goals for (`GF`) | 0 |
| Goals against (`GA`) | 0 |
| Goal difference (`GD`) | 0 |
| Points (`Pts`) | 0 |

If no matches have been played, display teams alphabetically by canonical team name as a deterministic default. This is a display convention, not a claim that alphabetical order is an official competition ranking. Do not omit registered teams merely because they have no match records yet.

A season's team registrations should be stored explicitly, for example in `season_teams`. Do not infer the full season roster solely from completed match rows: that would omit teams before their first match and can omit teams with missing fixture data.

## 4. Standings statistics

For each team, calculate the following from completed matches belonging to the same league-season:

| Field | Definition |
|---|---|
| `played` | Number of eligible completed matches played by the team. |
| `won` | Number of wins. |
| `drawn` | Number of draws. |
| `lost` | Number of losses. |
| `goals_for` | Total goals scored by the team. |
| `goals_against` | Total goals conceded by the team. |
| `goal_difference` | `goals_for - goals_against`. |
| `points` | `wins × points_for_win + draws × points_for_draw + losses × points_for_loss`. |

Default football scoring is three points for a win, one for a draw, and zero for a loss. Store these values as league configuration rather than hard-coding them throughout the application. A competition with different scoring rules must be represented by its configured values.

For a validated match with home goals `HG` and away goals `AG`:

- If `HG > AG`, the home team wins and the away team loses.
- If `HG = AG`, both teams draw.
- If `HG < AG`, the away team wins and the home team loses.

Update both teams from the same completed match exactly once. Reject or quarantine inconsistent records when the recorded full-time result conflicts with the score, according to the ingestion policy. Postponed, abandoned, cancelled, or otherwise incomplete fixtures must not affect standings unless an explicit competition-specific rule defines how they count.

## 5. Ranking and tie-break rules

Use the configured rules for the league when they are known. A recommended default for an initial implementation is:

1. Points, descending.
2. Goal difference, descending.
3. Goals scored, descending.
4. Canonical team name, alphabetical, for deterministic output when the sporting criteria remain tied.

The alphabetical fallback is for stable display and ordering. It must not be presented as an official sporting tie-break unless the competition's regulations say so.

Tie-break rules differ between competitions and can include head-to-head records, fair-play measures, play-offs, or other criteria. Keep the rule configuration explicit and versioned. If the project does not yet implement an official tie-break criterion, document that limitation rather than silently claiming official table equivalence.

**Position numbering:** after sorting the table, assign displayed positions from 1 to the number of registered teams. Decide whether tied teams share a sporting rank or receive sequential display positions; make this behavior explicit. For model features, use one consistent ranking method across training and inference and record it in the feature configuration.

## 6. Updating standings after a result

When a completed result is accepted:

1. Resolve the match to its league, season, home team, and away team.
2. Confirm both teams are registered for that league-season, or apply a documented correction process.
3. Validate the final score and result consistency.
4. Ensure the result has not already been applied to the standings.
5. Update both teams' played, W/D/L, GF, GA, GD, and points values.
6. Recalculate the table order and positions using the configured rules.
7. Persist the updated state and the relevant data revision in a transaction.

Imports must be safe to rerun. Use a stable match identifier or a documented composite key and idempotent upsert/correction logic so re-importing a match does not add its goals or points twice. If an earlier score is corrected, reverse or rebuild the affected standings from the corrected source of truth; do not simply add the new result on top of the old result.

A straightforward and auditable first implementation can recalculate standings from the season's accepted completed matches. Incremental updates may be added later, but they should be tested against a full recalculation to ensure both approaches produce identical tables.

## 7. Historical snapshots and prediction cutoffs

The current league table is not a valid substitute for the table that existed before a historical fixture. When creating training examples or historical predictions, generate standings as of each fixture's prediction cutoff.

Recommended date-batched procedure:

1. Partition matches by league and season.
2. Sort by date and by kickoff time only when kickoff ordering is trustworthy and the prediction cutoff is defined precisely.
3. For each date, compute a standings snapshot using results from earlier dates only when same-day ordering is unknown or unreliable.
4. Generate pre-match features for every fixture in that date batch from the same snapshot.
5. Add the date's completed results to the history only after all features for that date have been generated.
6. Continue to the next date.

This prevents one match's result from leaking into the features for another match on the same date. If reliable timestamps are available and the system explicitly predicts after an earlier same-day match has finished, a more granular event-time snapshot can be used, but the cutoff and timezone policy must be recorded.

Store or derive enough metadata to reproduce a snapshot, including league ID, season ID, cutoff timestamp or date, source data revision, and standings-rule version. If standings snapshots are persisted, distinguish them from the latest current table.

## 8. Standings features for the prediction model

The following are recommended pre-match features. Their values must be calculated from the snapshot strictly before the target fixture.

| Feature | Meaning |
|---|---|
| `home_league_position` | Home team's pre-match position. |
| `away_league_position` | Away team's pre-match position. |
| `home_league_points` / `away_league_points` | Points accumulated before kickoff. |
| `home_league_matches_played` / `away_league_matches_played` | Completed league matches counted before kickoff. |
| `home_league_goals_for` / `away_league_goals_for` | Goals scored before kickoff. |
| `home_league_goals_against` / `away_league_goals_against` | Goals conceded before kickoff. |
| `home_league_goal_difference` / `away_league_goal_difference` | Goal difference before kickoff. |
| `league_position_difference` | Home position minus away position. |
| `league_points_difference` | Home points minus away points. |
| `league_goal_difference_difference` | Home goal difference minus away goal difference. |

Use a documented sign convention for every difference feature. With the conventions above, a negative `league_position_difference` means the home team has a numerically smaller (higher) table position than the away team.

At the start of a season, teams may have no prior results. Their initial zero statistics are valid, while position follows the configured initial ordering. The model should also receive matches-played or history-availability features so that a team with no history can be distinguished from a team whose history is missing due to data-quality issues.

Never use final-season standings to represent a past fixture. Do not calculate a team's position from a table that includes the target match or future matches.

## 9. Data model and persistence

The database design should support at least:

- `leagues`: competition identity, points configuration, and tie-break configuration;
- `seasons`: league-season identity and optional start/end dates;
- `teams`: stable team identities and canonical names;
- `season_teams`: registration of each team in a season;
- `matches`: fixtures, status, kickoff, full-time scores, result, and source provenance;
- optionally `standings_snapshots` and snapshot rows: historical table state, cutoff, source revision, and rules version.

A current standings table may be calculated on demand from matches or maintained as a cache. If it is cached, define how it is rebuilt and make the accepted matches the source of truth. A historical snapshot should not be overwritten by the current table if it is needed to reproduce earlier predictions.

Useful integrity rules include:

- unique registration of each `(season_id, team_id)` pair;
- each match belongs to one league-season and references valid teams;
- home and away teams are different;
- score values are non-negative integers when present;
- completed match results are consistent with full-time scores;
- duplicate imports cannot count a match more than once;
- standings rows cannot mix leagues or seasons.

See [`database-design.md`](database-design.md) for the broader proposed relational schema.

## 10. Missing data, corrections, and season boundaries

- **Missing team registration:** do not silently omit a known season participant. Correct the registration list or flag the season configuration as incomplete.
- **Missing or invalid score:** do not update standings from an unvalidated final score.
- **Corrected result:** rebuild affected standings and historical feature snapshots from the corrected match onwards, or recalculate the entire league-season.
- **Postponed match:** apply its result when it is completed, using the actual match date/time for chronological feature generation when known.
- **Team rename:** preserve stable team identity and maintain aliases or source mappings where needed.
- **Promotion/relegation:** treat each league-season registration separately; do not carry league points from one season into another.
- **Cross-season model history:** historical matches from earlier seasons may be used for form only if the feature policy explicitly allows it. Current-season standings must reset at the season boundary.
- **Competition rule changes:** version the rule configuration and regenerate any affected standings snapshots and features.

## 11. Testing requirements

Test standings logic using small, hand-checkable datasets before running it against a full season.

- All registered teams appear before the first match, with zero initial statistics.
- Initial ordering is alphabetical and deterministic when no official ordering is configured.
- Wins, draws, losses, goals for/against, goal difference, and points are correct.
- The configured points system is respected.
- Ranking by points, goal difference, and goals scored is correct.
- Fully tied teams use the configured final tie-break/display policy.
- Competition-specific tie-break configuration is applied when implemented.
- Different leagues and seasons never share points or standings rows.
- A match is applied exactly once, including when imports are rerun.
- Correcting a score yields the same result as rebuilding from the corrected match history.
- Incomplete fixtures do not affect the table.
- Same-day fixtures with unknown kickoff ordering use a pre-date snapshot.
- Historical positions do not change retroactively in stored snapshots unless deliberately regenerated from corrected source data.
- Standings features generated for training match the values produced by the inference feature pipeline for the same cutoff.

## 12. Acceptance criteria

The standings component is ready for use when:

- every registered team is represented in the correct league-season;
- initial zero-match standings are supported;
- points and ranking rules are explicit and configurable;
- results update both teams accurately and idempotently;
- corrections and rebuilds are supported;
- historical pre-match snapshots do not include future or same-day results with unknown ordering;
- the standings features have stable definitions and tests;
- any difference between the default table and official competition regulations is documented.

## Related documentation

- [`database-design.md`](database-design.md) — persistence model for leagues, seasons, teams, matches, and snapshots.
- [`feature-engineering.md`](feature-engineering.md) — use of pre-match standings as model inputs and leakage-safe feature generation.
- [`data-ingestion.md`](data-ingestion.md) — match validation, duplicate handling, and correction provenance.
- [`data-dictionary.md`](data-dictionary.md) — Football-Data CSV field definitions and data availability notes.

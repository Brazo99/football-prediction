# Football-Data CSV Data Dictionary

This document incorporates the supplied **“Notes for Football Data”** reference into the Football Match Result Predictor project. The source states that data are supplied in CSV format and are spreadsheet-ready. Some abbreviations are no longer in use, particularly bookmaker odds, and some fields refer to data collected in earlier seasons. Field availability varies by league and season; validate each actual CSV header before ingestion.

## 1. Match identity and results

| Field(s) | Meaning in the supplied reference |
|---|---|
| `Div` | League Division |
| `Date` | Match Date (`dd/mm/yy`) |
| `Time` | Time of match kick off |
| `HomeTeam` | Home Team |
| `AwayTeam` | Away Team |
| `FTHG`, `HG` | Full Time Home Team Goals |
| `FTAG`, `AG` | Full Time Away Team Goals |
| `FTR`, `Res` | Full Time Result (`H` = Home Win, `D` = Draw, `A` = Away Win) |
| `HTHG` | Half Time Home Team Goals |
| `HTAG` | Half Time Away Team Goals |
| `HTR` | Half Time Result (`H` = Home Win, `D` = Draw, `A` = Away Win) |

## 2. Match statistics (where available)

| Field | Meaning in the supplied reference |
|---|---|
| `Attendance` | Crowd Attendance |
| `Referee` | Match Referee |
| `HS`, `AS` | Home / Away Team Shots |
| `HST`, `AST` | Home / Away Team Shots on Target |
| `HHW`, `AHW` | Home / Away Team Hit Woodwork |
| `HC`, `AC` | Home / Away Team Corners |
| `HF`, `AF` | Home / Away Team Fouls Committed |
| `HFKC`, `AFKC` | Home / Away Team Free Kicks Conceded |
| `HO`, `AO` | Home / Away Team Offsides |
| `HY`, `AY` | Home / Away Team Yellow Cards |
| `HR`, `AR` | Home / Away Team Red Cards |
| `HBP`, `ABP` | Home / Away Team Bookings Points (10 = yellow, 25 = red) |

### Source notes on statistics

- Free Kicks Conceded includes fouls, offsides and any other offense committed, and will always be equal to or higher than fouls. Fouls make up the vast majority of Free Kicks Conceded.
- Free Kicks Conceded are shown when specific foul data are not available (France 2nd, Belgium 1st and Greece 1st divisions).
- English and Scottish yellow cards do not include the initial yellow card when a second is shown to a player converting it into a red, but this is included as a yellow (plus red) for European games.

## 3. Match-result bookmaker odds

The source describes these as **pre-closing odds**. Closing odds have an additional `C` after the bookmaker abbreviation, `Max`, or `Avg` (for example, `B365CH` is closing Bet365 home-win odds). Some bookmaker abbreviations are no longer in use.

| Field(s) | Meaning in the supplied reference |
|---|---|
| `1XBH`, `1XBD`, `1XBA` | 1XBet home win, draw, away |
| `B365H`, `B365D`, `B365A` | Bet365 home, draw, away |
| `BFH`, `BFD`, `BFA` | Betfair home, draw, away |
| `BFDH`, `BFDD`, `BFDA` | Betfred home, draw, away |
| `BMGMH`, `BMGMD`, `BMGMA` | BetMGM home, draw, away |
| `BVH`, `BVD`, `BVA` | Betvictor home, draw, away |
| `BSH`, `BSD`, `BSA` | Blue Square home, draw, away |
| `BWH`, `BWD`, `BWA` | Bet&Win home, draw, away |
| `CLH`, `CLD`, `CLA` | Coral home, draw, away |
| `GBH`, `GBD`, `GBA` | Gamebookers home, draw, away |
| `IWH`, `IWD`, `IWA` | Interwetten home, draw, away |
| `LBH`, `LBD`, `LBA` | Ladbrokes home, draw, away |
| `PPH`, `PPD`, `PPA` | Paddy Power home, draw, away |
| `PSH` / `PH`, `PSD` / `PD`, `PSA` / `PA` | Pinnacle home, draw, away |
| `SKH`, `SKD`, `SKA` | Skybet home, draw, away |
| `SOH`, `SOD`, `SOA` | Sporting Odds home, draw, away |
| `SBH`, `SBD`, `SBA` | Sportingbet home, draw, away |
| `SJH`, `SJD`, `SJA` | Stan James home, draw, away |
| `SYH`, `SYD`, `SYA` | Stanleybet home, draw, away |
| `VCH`, `VCD`, `VCA` | VC Bet home, draw, away (now BetVictor, see above) |
| `WHH`, `WHD`, `WHA` | William Hill home, draw, away |
| `Bb1X2` | Number of BetBrain bookmakers used to calculate match odds averages and maximums |
| `BbMxH`, `BbMxD`, `BbMxA` | BetBrain maximum home, draw, away odds |
| `BbAvH`, `BbAvD`, `BbAvA` | BetBrain average home, draw, away odds |
| `MaxH`, `MaxD`, `MaxA` | Market maximum home, draw, away odds |
| `AvgH`, `AvgD`, `AvgA` | Market average home, draw, away odds |
| `BFEH`, `BFED`, `BFEA` | Betfair Exchange home, draw, away odds |

## 4. Total-goals betting odds

| Field(s) | Meaning in the supplied reference |
|---|---|
| `BbOU` | Number of BetBrain bookmakers used to calculate over/under 2.5 goals averages and maximums |
| `BbMx>2.5` | BetBrain maximum over 2.5 |
| `BbAv>2.5` | BetBrain average over 2.5 |
| `BbMx<2.5` | BetBrain maximum under 2.5 |
| `BbAv<2.5` | BetBrain average under 2.5 |
| `GB>2.5`, `GB<2.5` | Gamebookers over / under |
| `B365>2.5`, `B365<2.5` | Bet365 over / under |
| `P>2.5`, `P<2.5` | Pinnacle over / under |
| `Max>2.5`, `Max<2.5` | Market maximum over / under |
| `Avg>2.5`, `Avg<2.5` | Market average over / under |

## 5. Asian handicap odds

| Field | Meaning in the supplied reference |
|---|---|
| `BbAH` | Number of BetBrain bookmakers used to calculate Asian handicap averages and maximums |
| `BbAHh` | BetBrain size of handicap (home team) |
| `AHh` | Market size of handicap (home team), since 2019/2020 |
| `BbMxAHH` | BetBrain maximum Asian handicap home odds |
| `BbAvAHH` | BetBrain average Asian handicap home odds |
| `BbMxAHA` | BetBrain maximum Asian handicap away odds |
| `BbAvAHA` | BetBrain average Asian handicap away odds |
| `GBAHH`, `GBAHA` | Gamebookers Asian handicap home / away odds |
| `GBAH` | Gamebookers size of handicap (home team) |
| `LBAHH`, `LBAHA` | Ladbrokes Asian handicap home / away odds |
| `LBAH` | Ladbrokes size of handicap (home team) |
| `B365AHH`, `B365AHA` | Bet365 Asian handicap home / away odds |
| `B365AH` | Bet365 size of handicap (home team) |
| `PAHH`, `PAHA` | Pinnacle Asian handicap home / away odds |
| `MaxAHH`, `MaxAHA` | Market maximum Asian handicap home / away odds |
| `AvgAHH`, `AvgAHA` | Market average Asian handicap home / away odds |

## 6. Sources and collection notes

- **Current full-time and half-time results:** XScores (`http://www.xscores.com`).
- **Match statistics:** BBC, Flashscore, ESPN Soccer, Bundesliga.de, Gazzetta.it, and Football.fr.
- **Betting odds:** Betbrain.com, Oddsportal.com, and individual bookmakers.
- Weekend betting odds were collected on Friday afternoons; midweek odds were collected on Tuesday afternoons.
- Additional statistics (corners, shots, bookings, referee, etc.) for the 2000/01 and 2001/02 English, Scottish, and German leagues came from Sports.com, which the source notes is under new ownership and no longer available.

## 7. Rules for use in this project

This project is intended to make **pre-match** full-time result predictions (`H`, `D`, `A`). The source field definitions describe the data; they do not guarantee that each column exists in every CSV or that a field is available at prediction time.

1. **Validate schema first.** Check required columns, data types, date parsing, allowed result values, missingness, duplicates, and field coverage by league and season. The `Div` field identifies the league division; season assignment may require separate configuration or source metadata.
2. **Target:** use `FTR` (or `Res` when that alias is present) as the target class. Where full-time goals are present, check that the result is consistent with `FTHG`/`HG` and `FTAG`/`AG`.
3. **Prevent target leakage.** Do not use `FTR`/`Res`, `FTHG`/`HG`, `FTAG`/`AG`, `HTR`, `HTHG`, `HTAG`, or target-match statistics collected during or after the match as inputs to a pre-match prediction model.
4. **Use only eligible odds.** Use bookmaker odds only when their collection timestamp/procedure confirms they were available before the prediction cutoff. The reference describes the listed odds as pre-closing odds and separately identifies closing odds with a `C` suffix.
5. **Construct historical features carefully.** Prior matches' results and statistics can be used to calculate rolling form for a future fixture only if those values were available before that fixture. Never populate a fixture's pre-match features with its eventual match statistics.
6. **Preserve provenance.** Retain the raw file and record its source, retrieval/import date, league, season, and any transformations or team-name mappings. Document missing-value handling, duplicate resolution, date/time normalization, and odds conversion.
7. **Account for coverage differences.** Missing statistics can reflect differences in league, season, or collection source; do not automatically interpret an absent value as zero.

## 8. Related project fields and engineered features

The CSV reference describes source fields. The project may also create derived features from earlier matches, such as home/away points, league position, goal difference, goals scored/conceded averages, rolling form, rest days, and head-to-head summaries. These are **engineered fields**, not source columns in this reference, and must be calculated using only information available before the fixture being predicted.

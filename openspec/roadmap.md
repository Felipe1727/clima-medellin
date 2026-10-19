# Roadmap

## Objectives

Build "Clima Medellín" as designed in `docs/`: a single-user Python CLI that downloads one rolling
year of hourly weather (ERA5) and PM2.5 (CAMS global) for Medellín from Open-Meteo, validates it,
persists it in ObjectDB through a Java JAR, and analyses it (coverage, time-of-day bands,
descriptive statistics, linear regression, charts). Every spec also keeps `docs/` in sync and grows
`docs/implementacion.md`, a technical guide with real, test-verified excerpts of the project's code.

Second iteration (exploration 2026-10-19): make the CLI attractive and understandable for
non-technical users (colours, formatted tables, plain-language explanations) and add three
calendar models that predict the typical temperature, humidity and PM2.5 for any hour, day or
range of up to 31 days, evaluated honestly against a baseline.

## Guidelines

### Stack (locked)
- Java 25, Maven, ObjectDB 2.9.5 `com.objectdb:objectdb-jk` (jakarta.persistence) from
  `https://m2.objectdb.com`, Jackson for JSON, JUnit 5, maven-shade -> `java/target/clima-medellin.jar`.
- Python 3.14 managed with uv (`python/pyproject.toml`), pandas, scikit-learn, statsmodels (VIF,
  Durbin-Watson), matplotlib, requests; pytest; ruff.
- `rich` (Python) for the terminal UI: colours, tables, panels, progress bars; respects `NO_COLOR`.
- GitHub Actions CI (`.github/workflows/ci.yml`) on pull_request and push to main: sets up Java 25 and
  uv, runs Install, Test and Lint. No branch protection.

### Project commands (also written into the local, gitignored `.claude/CLAUDE.md`)
- Install: `cd java && mvn -q -DskipTests package && cd ../python && uv sync`
- Test: `cd java && mvn -q verify && cd ../python && uv run pytest`
- Lint: `cd python && uv run ruff check .`
- Build: `cd java && mvn -q -DskipTests package`

### Layout
- `java/` Maven project, base package `co.climamedellin` (`entities`, `cli`, `persistence`).
- `python/` with package `python/src/clima_medellin/`, tests in `python/tests/`, scripts in
  `python/scripts/`, console script `clima-medellin`.
- Runtime folders (gitignored): `data/` (default DB `data/clima.odb`), `staging/`, `exchange/`, `outputs/`.
  `samples/` is versioned.
- Every JAR subcommand accepts `--db <path>`, so tests always use a temporary `.odb`.

### Language
- English: identifiers, JSON fields, test names, commits, PR descriptions.
- Spanish: code comments, CLI messages, chart text, `docs/`, README, OpenSpec artifacts.
- Enum values as in docs: `COMPLETA`, `PARCIAL`, `SIN_DATOS`, `NORMAL`.

### Testing
- No test touches the network; HTTP is tested against `samples/` and mocks.
- Java tests use a fresh `.odb` in a temp directory. Python bridge tests run the real JAR (built by
  `mvn verify` in the Test command) against a temp `.odb`.
- Matplotlib tests use the Agg backend.

### Documentation rules (every spec)
- Update the `docs/` file(s) for its phase: resolve the `[Por verificar]` points it touches (or justify
  them), move decisions to their final state, mark its phase in `docs/fases.md`.
- Add its section to `docs/implementacion.md`. Per topic: Concepto (2-4 sentences), Sintaxis básica
  (minimal standalone example), En este proyecto (real excerpt + line-by-line explanation), Cuidado
  (pitfall avoided).
- Real excerpts are fenced code blocks preceded by `<!-- fragmento: <repo-relative path> -->`; they are
  verbatim contiguous code (no elisions). A pytest test fails if any marked excerpt no longer appears
  verbatim (ignoring trailing whitespace) in its file.

### Locked decisions (from Phase 1 exploration, 2026-10-18)
- Location: code `MED-CENTRO`, name "Medellín – Centro", 6.2447, -75.5748, fixed elevation 1495 m sent
  as `elevation=1495`, timezone America/Bogota.
- API params: ERA5 via `models=era5`, `wind_speed_unit=ms`; PM2.5 via `domains=cams_global`; GMT timestamps.
- Window (D-016): D = today in America/Bogota; [same day previous year 00:00 local, D 00:00 local);
  Feb 29 -> Feb 28 of previous year (DP-09); expected steps always computed from the real window.
- Effective end: ERA5 = min(window end, 00:00 UTC of D-4 days) (D-5 is the last full UTC day);
  CAMS = window end. Nothing at or after the effective end is ever stored.
- ERA5T (recent preliminary ERA5) is treated as definitive; one factual line in fuentes-y-datos.md.
- PM2.5 is hourly (24 values/day, verified): hourly expected steps for coverage (DP-03); same band rule
  as other variables (DP-01); all hourly values in regression (DP-02). The 00/12 UTC forecast-run
  seams are documented and charted, never corrected.
- Insert-only, no corrections (DP-04 = A): `IngestionBatch.type` is always `NORMAL`.
- Rows with all variables null are never stored (DP-12); partial nulls are stored as null (D-012).
- Unique key (location, source, timestampUtc) enforced in ObjectDB; if the relation can't be indexed,
  a plain `locationCode` field is indexed instead. Import pre-loads existing keys for the batch range
  and commits in blocks of 500.
- Exit codes (DP-05): 0 OK, 1 usage, 2 data, 3 database, 4 unexpected. stdout = exactly one JSON
  object always (also on errors); logs on stderr.
- `coverage`: stdout summary (counts per variable, first/last timestamp) + `exchange/coverage-<source>.jsonl`
  (one line per stored timestamp with its non-null variables); all coverage maths in Python.
- Staging file deleted after successful import, kept (path printed) on failure; exports overwrite a
  fixed file name per source; exit deletes nothing. Java stderr hidden unless `--verbose`.
- HTTP: one request per missing interval, no chunking; 3 retries with backoff on timeouts/5xx.
- Coverage states (D-014): COMPLETA if every variable >= 98 % and max gap <= 6 h; PARCIAL; SIN_DATOS.
- Bands (D-009): 07-09, 13-15, 19-21 local, mean of non-null values, NaN if < 2 valid, grouped by local
  civil day, not persisted (D-021).
- Split (D-018): train = [window start, window start + 9 calendar months), 24 h gap, test = rest; exact
  dates printed. Diurnal profile uses train only.
- Regression: Pipeline(StandardScaler, LinearRegression) fitted on train; baseline = train mean of
  PM2.5; MAE, RMSE, R² for both; coefficients standardized and in original units; VIF on train;
  Durbin-Watson on test residuals; no p-values; original scale, no log (DP-08).
- Charts (D-023, DP-10): ask window or PNG each time; PNG automatically (with notice) when no display.
  PNG to `outputs/<chart>_<YYYYmmdd-HHMMSS>.png`. Each chart has title, units, period and
  "Datos: Open-Meteo.com (ERA5, CAMS)".
- CLI: interactive 7-option menu as a thin layer over plain functions; `[s/N]` confirmation before
  downloads.

### Locked decisions (second exploration, 2026-10-19)
- Calendar models: three separate linear regressions (temperature, humidity, PM2.5) whose only
  inputs are the local datetime: 23 hour-of-day indicators (00:00 is the reference) plus the
  seasonal wave sin/cos(2*pi*day_of_year/365.25). No scaler (coefficients read directly in
  units), original scale, no day-of-week effects.
- Window stays one year (D-016); no 5-year extension. Backtest evidence (11 quarters, 2024-2026):
  12 months of training beats 9 months and beats 4-5 years (interannual regime changes; CAMS
  has no PM2.5 before 2022-08).
- Evaluation: the existing temporal split (D-018) against the baseline (training mean), MAE,
  RMSE and R²; the test MAE is shown to users as "error típico". Predictions use the same model
  refitted on the full window. Models are retrained from the database on each use and never
  stored (no new entities).
- The existing PM2.5 <- weather regression (D-017..D-020) is unchanged.
- Prediction requests: local time; inputs "Desde" and "Hasta" (Enter = only that date/hour);
  formats AAAA-MM-DD, AAAA-MM-DD HH, AAAA-MM-DD HH:MM; a date without hour = the whole day
  (00:00..23:00). Allowed from the window start to today + 365 days, at most 31 days per request.
  The three variables are shown side by side; hours with stored data show prediction, real value
  and difference, otherwise the prediction labelled "valor típico". Ranges over 2 days show a
  daily summary (mean, min, max) with the hourly table on request, plus a chart (prediction line,
  band of +/- typical error, real values when they exist) using the window/PNG choice.
- Menu (Spanish, grouped): DATOS 1 Ver qué datos hay guardados, 2 Descargar los datos que faltan,
  3 Consultar registros por fecha; ANÁLISIS 4 Resumen estadístico, 5 Evaluar los modelos (qué tan
  bien predicen); PREDICCIONES 6 Predecir temperatura, humedad o PM2.5 para una fecha u hora,
  7 Generar gráficas; 0 Salir. Header with location, window and coloured database state.
- Plain language: every result screen ends with a "Qué significa" panel (2-3 everyday
  sentences); jargon is translated on first use ("error típico (MAE)", "qué tanto explica el
  modelo (R²)"); colour never carries meaning alone (always with a word); inputs show an example
  and invalid input explains what was expected; long operations show a progress bar.
- The menu receives a `rich` Console; tests use a recording console with colours off and check
  the plain text.
- New decisions D-024 (calendar models) and D-025 (rich CLI and plain language); new Phase 10 in
  `docs/fases.md`.

## Out of scope
- Production concerns: multi-user, concurrent runs, servers, deployment, availability guarantees.
- Weather forecasts from external sources (the calendar models' typical-value predictions are in
  scope), station/measured data, multiple locations (the model allows it; not implemented),
  non-linear or neural models, log-transformed models, storing trained models, windows longer
  than one year, day-of-week effects.
- Value corrections or updates (`CORRECCION` batches), distinguishing ERA5T from final ERA5,
  deleting data that leaves the window.
- Correcting the CAMS forecast-run seams.
- Branch protection, packaging beyond the fat JAR + uv.
- Oral-defence script and study material beyond `docs/` (understanding was built in Phase 1).

## Specs (execute in order)

- [x] `project-scaffold` — Maven + uv projects, CI, implementation guide skeleton and excerpt check
  - Acceptance:
    - `java/` builds with `mvn verify` into `java/target/clima-medellin.jar` (deps above); running it
      with no/unknown subcommand prints one JSON error object to stdout and exits 1 (JUnit test).
    - `python/` installs with `uv sync`; package `clima_medellin` with console script `clima-medellin`;
      pytest and ruff configured; a smoke test passes.
    - CI workflow runs Install, Test and Lint and is green on this spec's PR.
    - `docs/implementacion.md` exists (purpose, index, excerpt convention, build/run commands).
    - The excerpt-check test exists and is exercised by at least one real excerpt.
    - README folder tree and documentation table updated; `.gitignore` covers any runtime artifact
      produced by the build or ObjectDB.
    - Project commands written into local `.claude/CLAUDE.md`.
  - Depends on: none

- [x] `api-validation` — Committed API samples and documentation of all Phase 1 findings and decisions
  - Acceptance:
    - `python/scripts/fetch_samples.py` downloads, with the locked params: ERA5 one year, ERA5 recent
      month (including trailing nulls), PM2.5 one year, PM2.5 last week; files committed in `samples/`
      with `samples/README.md` (URL, params, download date).
    - Offline tests on the samples assert: hourly GMT timestamps, expected units, ERA5 year has 8,760
      (or 8,784) steps, PM2.5 has 24 values/day and no nulls in the year sample, the recent ERA5 sample
      has trailing nulls after D-5.
    - `fuentes-y-datos.md`: Phase 1 findings (models=era5, D-5 latency with trailing nulls, PM2.5 hourly,
      00/12 UTC seams with their measured magnitude, model grid cells, elevation, units, ERA5T line,
      CAMS global attribution text); PV-01..PV-12 resolved or justified.
    - `decisiones.md` and `fases.md`: D-005, D-006, D-007, D-009, D-013, D-018, D-022, D-023 and
      DP-01..DP-12 updated to the locked decisions; D-006 and D-009 no longer "pendiente de revisión".
    - `cobertura-y-franjas.md`: PM2.5 section rewritten (hourly, same band rule, seam warning on the
      morning and night bands); DP-12 rule updated.
  - Depends on: project-scaffold

- [x] `persistence` — ObjectDB entities, unique natural key, insert-only batch insertion, queries
  - Acceptance:
    - Entities Location, WeatherRecord, AirQualityRecord, IngestionBatch per `arquitectura.md`, nullable
      wrapper types, units in field names.
    - JUnit tests (temp `.odb`): duplicate (location, source, timestamp) in the same and in another
      batch is skipped and counted without aborting other records; counts equal after close/reopen;
      null round-trips as null; UTC timestamp round-trips exactly; JPQL query with JOIN on Location
      filtered by code and range returns records ordered by time; blocks of 500 commits.
    - PV-13 and PV-14 resolved in `arquitectura.md`.
    - `implementacion.md`: ObjectDB section (EntityManagerFactory, annotations, @Unique, transactions,
      persist, JPQL select, JOIN, aggregations, nulls).
  - Depends on: project-scaffold

- [x] `ingest` — Open-Meteo client and normalization to validated DataFrames
  - Acceptance:
    - Client builds requests with the locked params; retries 3 times with backoff on timeouts/5xx
      (tested with mocks).
    - Normalization: tz-aware UTC index, canonical unit-suffixed columns, plausible ranges
      (T -20..50 °C, RH 0..100 %, wind 0..75 m/s, PM2.5 0..1000 µg/m³) with out-of-range -> null and
      counted, in-batch duplicates removed, values at/after the effective end removed, all-null rows
      dropped.
    - Tests on samples: expected row counts, no duplicate timestamps, partial nulls preserved, an
      injected out-of-range value detected, trailing nulls removed; America/Bogota is UTC-5 all year
      (PV-16).
    - `implementacion.md`: HTTP request, JSON -> DataFrame, UTC handling, validation.
  - Depends on: api-validation

- [x] `bridge` — JAR subcommands coverage/import/export and the Python bridge module
  - Acceptance:
    - Subcommands with documented arguments (`--db`, plus location, source, range, file/out as needed);
      `import` creates the Location if absent from the metadata passed by Python and records an
      IngestionBatch (endpoint, params, requested range, counts received/inserted/duplicates/rejected).
    - JSON Lines format per `arquitectura.md` (UTF-8, ISO 8601 `Z`, null, unit-suffixed fields, one
      source per file).
    - stdout is exactly one JSON object in every case including errors; exit codes 0-4.
    - Python module runs the JAR, parses stdout, maps exit codes to Spanish messages, applies the
      staging/exchange rules, `--verbose` shows stderr.
    - Tests with the real JAR and a temp `.odb`: DataFrame -> staging -> import -> export -> DataFrame
      is identical (values, nulls, timestamps); importing the same file twice inserts 0 the second
      time; a corrupt line gives exit 2 and a clear Spanish message; unknown subcommand gives exit 1;
      coverage writes the summary and the jsonl file.
    - DP-05, PV-15 (documented single-process assumption) and PV-19 resolved in `arquitectura.md`.
    - `implementacion.md`: subprocess call, JSON Lines, stdout/stderr contract, exit codes, the full
      ObjectDB -> Python path.
  - Depends on: persistence, ingest

- [x] `coverage` — Rolling window, coverage metrics and incremental update flow
  - Acceptance:
    - Pure functions: window (tests for D = 2026-10-09, 2028-02-29, 2028-03-01, 2029-03-01 giving
      365/366/366/365 days), effective end per source, expected/missing steps, interval grouping and
      conversion to UTC dates with merging (the docs example yields two one-day requests).
    - Per-variable metrics (expected, valid, %, max gap, number of gaps) and states with the D-014
      thresholds.
    - Update function: coverage -> plan -> fetch -> normalize -> stage -> import -> re-coverage; an
      empty API result records an IngestionBatch with 0 inserted.
    - Tests with a fake HTTP layer serving samples and the real JAR: initial load reaches COMPLETA or
      PARCIAL with a known cause; an immediate second update plans 0 requests; a hole in the DB causes
      only that day to be requested; nothing at/after the effective end is stored.
    - `cobertura-y-franjas.md` updated; D-014 definitive.
    - `implementacion.md`: expected vs existing sets, interval grouping, window and Feb 29.
  - Depends on: bridge

- [x] `bands-stats` — Time-of-day bands, diurnal profile and descriptive statistics
  - Acceptance:
    - Bands per local day and variable with the locked rule; night band (00-02 UTC next day) assigned
      to the correct local day.
    - Diurnal profile per local hour from the train period only, with valid counts per hour.
    - Descriptive stats per variable (n, nulls, mean, median, std, min, max, p5, p25, p75, p95) and per
      band (mean, valid days).
    - Tests: a hand-computed fixture day including a NaN band and the night band; the docs example
      (17.8, missing, 19.6 -> 18.7).
    - `cobertura-y-franjas.md` final; `implementacion.md`: tz conversion, groupby by local day, NaN
      handling, percentiles.
  - Depends on: coverage

- [x] `regression` — Joined dataset, temporal split, Pipeline, baseline, metrics and diagnostics
  - Acceptance:
    - Inner join of PM2.5 and weather on timestamp, rows with any null dropped; split per the locked
      rule with exact dates reported.
    - Pipeline fitted on train only; baseline; MAE, RMSE, R² for model and baseline; coefficients
      standardized and in original units; VIF; Durbin-Watson; no p-values.
    - Tests: known coefficients recovered on synthetic data; scaler mean equals train mean; no overlap
      and a 24 h gap between train and test; identical results on re-run; baseline uses train mean.
    - `regresion.md` final (decisions, interpretation template, seam limitation);
      `implementacion.md`: pandas merge/join, split, Pipeline, metrics, VIF, DW.
  - Depends on: bands-stats

- [x] `visualizations` — The 9 charts with window/PNG output
  - Acceptance:
    - Time series per variable (gaps as line breaks), diurnal profile with shaded bands, band
      comparison box plots with valid days, PM2.5-vs-predictor scatter, correlation matrix, actual vs
      predicted, residuals, coverage map per source, PM2.5 seam chart (mean hourly jump by UTC hour).
    - Output per the locked rule; headless -> PNG with notice (PV-18).
    - Tests (Agg): every chart builds from fixture data with title, unit-labelled axes, period and
      attribution; PNG written to outputs/ naming pattern; a series with a gap is not connected.
    - `cli-y-visualizaciones.md` updated; `implementacion.md`: figure anatomy, gaps, backends, PNG.
  - Depends on: regression

- [x] `cli-integration` — 7-option menu, end-to-end flow and final docs
  - Acceptance:
    - Menu per `cli-y-visualizaciones.md` with header (location, window), `[OK]`/`[…]`/`[AVISO]`/`[ERROR]`
      messages, non-COMPLETA warnings, empty-DB suggestion, download confirmation, option 3 paginated
      table (local + UTC time, `—` for null, batch id), `--verbose`.
    - End-to-end test with scripted input, a temp `.odb` and a fake HTTP layer serving samples: empty DB
      -> coverage -> update -> query -> stats -> regression -> charts (PNG) without errors.
    - README: install and run instructions, requirements with real versions, attribution.
    - `docs/fases.md` all phases updated; every remaining `[Por verificar]` resolved or justified;
      `implementacion.md` final consistency pass (index complete, all excerpts verified).
  - Depends on: visualizations

- [x] `calendar-models` — Three calendar models (temperature, humidity, PM2.5) with evaluation and predictions
  - Acceptance:
    - Feature builder: for local datetimes, 23 hour indicators + seasonal sin/cos; 00:00 is all zeros.
    - Per variable: fit on the training split, evaluate on the test split against the baseline
      (MAE, RMSE, R²), refit on the full window; coefficients exposed in original units (hour
      effects vs midnight and the seasonal wave).
    - Prediction for a single hour, a whole day (24 hours) or a range (each hour, both ends
      included), in local time, with validation of the allowed range (window start .. today + 365
      days, at most 31 days) and Spanish error messages.
    - Joins stored real values when they exist (prediction, real, difference).
    - Tests: known synthetic hour effects and seasonal wave are recovered; date-only input yields
      24 hours; range limits rejected; evaluation uses only training rows to fit; deterministic;
      on the samples, the temperature model's test MAE beats its baseline.
    - Docs: calendar-models section in `regresion.md` (idea, features, recipe with real
      coefficients, evaluation results with the samples, limits), D-024 in `decisiones.md`, Phase 10
      in `fases.md`, `implementacion.md` section on one-hot and cyclic features with real excerpts.
  - Depends on: cli-integration

- [x] `cli-ux` — rich look and plain-language layer for the existing menu
  - Acceptance:
    - Menu regrouped as locked (DATOS / ANÁLISIS / PREDICCIONES, 0 = Salir; option 6 may show
      "próximamente" until `prediction-menu`), header with location, window and coloured state.
    - All existing screens use rich tables and panels; downloads and chart generation show progress.
    - Every result screen ends with a "Qué significa" panel; jargon translated on first use;
      colour always paired with a word; inputs show an example; invalid input explains the format.
    - `NO_COLOR` and non-terminal output produce plain text.
    - Existing menu tests adapted to the recording console; end-to-end test still passes.
    - Docs: D-025, `cli-y-visualizaciones.md` (new menu and screens), `implementacion.md` section on rich.
  - Depends on: calendar-models

- [x] `prediction-menu` — Prediction option, model evaluation screen and new chart
  - Acceptance:
    - Option 6: "Desde"/"Hasta" prompts with the locked formats and limits; single hour, day and
      range; three variables side by side with "error típico"; real + difference for stored hours,
      "valor típico" otherwise; ranges over 2 days show the daily summary, the hourly table on
      request and a chart (window/PNG).
    - Option 5: one table with the three calendar models and the PM2.5 <- weather model, each
      against its baseline, followed by the weather-model detail; "Qué significa" panel.
    - Option 7 adds the "efecto de cada hora" chart (3 panels), 14 charts in total.
    - End-to-end test extended: predict a past day (real values shown), a future date and a
      3-day range (summary + PNG chart); invalid dates and limits explained.
    - Docs: `cli-y-visualizaciones.md`, `implementacion.md` (prediction screen), README usage,
      `fases.md` Phase 10 completed.
  - Depends on: cli-ux

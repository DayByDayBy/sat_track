---
type: execution-plan
created: 2025-12-03T00:17:00Z
source:
  kind: description
  value: "Satellite Tracker with Polars, Skyfield, and CesiumJS"
strategy: segmented
estimated_tasks: 24
estimated_time: 32
---

<objective>
Implement a full-stack real-time satellite tracking system with:
- FastAPI + Skyfield + Polars + APScheduler backend
- React + CesiumJS + Plotly frontend

The system must ingest TLEs to Parquet, rebuild Skyfield satellites on startup, continuously compute satellite positions, and expose them via HTTP and WebSocket APIs for a 3D globe and observer-pass visualizations.
</objective>

<execution_context>
Files/inputs to consider when executing this plan:
- `./prompts/001-satellite-tracker-full-stack.md` - Detailed implementation prompt
- Repository root: `./` - Existing structure and files, if any

Execution should be conservative about overwriting; prefer extending existing structure when present.
</execution_context>

<context>
Domain:
- Satellite orbit propagation using TLEs and SGP4 via Skyfield
- Global real-time visualization on a CesiumJS globe
- Observer-based pass and ground-track predictions for arbitrary locations

Codebase assumptions:
- This repo is dedicated to the satellite tracker project.
- Backend and frontend directories may not yet exist and should be created in a conventional, minimal way.
- Deployment targets: typical PaaS (Fly.io/Railway for backend, Vercel/Netlify for frontend).

Architecture goals:
- Clear separation between TLE ingestion, orbit propagation, APIs, and scheduling on the backend.
- Clean React component structure on the frontend for globe view, observer controls, and pass/ground-track visualizations.
- Design choices should keep the door open for Redis-based scaling and periodic cloud TLE refresh jobs.
</context>

<tasks>

<task id="01" type="auto">
  <title>Scan repository and confirm high-level architecture approach</title>
  <description>
  Inspect the current repository layout and files to understand what (if anything) already exists.
  Confirm that the planned architecture (FastAPI backend + React/Cesium frontend) fits cleanly into the existing structure or define a minimal structure if starting from scratch.
  </description>
  <requirements>
  - Identify any existing backend/frontend code that should be preserved or integrated.
  - Decide on top-level directories (e.g., `backend/`, `frontend/`, `data/`).
  - Note any constraints (Python version, package managers) from existing files (e.g., `pyproject.toml`, `requirements.txt`, `package.json`).
  </requirements>
  <files>
  - `./` - Root listing and any existing config files.
  </files>
  <verification>
  - A short written note (in comments or README scratch area) of the chosen high-level layout.
  - No files are broken or removed during this step.
  </verification>
</task>

<task id="02" type="auto">
  <title>Establish backend skeleton and dependencies</title>
  <description>
  Create the initial FastAPI backend skeleton, including an application entrypoint, minimal configuration, and a health endpoint. Define Python dependencies for TLE processing, scheduling, and serving (FastAPI, Skyfield, Polars, APScheduler, uvicorn).
  </description>
  <requirements>
  - Create a `backend/` directory if one does not already exist.
  - Add `backend/app/main.py` with a FastAPI app and at least one health route (e.g., `/health`).
  - Define backend dependencies in `backend/requirements.txt` or equivalent.
  - Add minimal backend README with setup/run instructions.
  </requirements>
  <files>
  - `./backend/app/main.py`
  - `./backend/requirements.txt`
  - `./backend/README.md`
  </files>
  <verification>
  - `uvicorn backend.app.main:app --reload` starts successfully.
  - `GET /health` responds with a simple JSON payload indicating the service is alive.
  </verification>
</task>

<task id="03" type="checkpoint:human-verify">
  <title>Checkpoint: Verify backend skeleton</title>
  <description>
  Pause to confirm that the backend skeleton and dependencies are sound before layering in TLE logic and scheduling.
  </description>
  <verification_question>
  Does the backend skeleton start cleanly and follow the intended directory structure and dependency setup?
  </verification_question>
  <verification_criteria>
  - FastAPI app runs locally without errors.
  - Directory structure matches expectations (e.g., `backend/app/...`).
  - Dependencies are reasonable and minimal at this stage.
  </verification_criteria>
</task>

<task id="04" type="auto">
  <title>Implement TLE fetch and Parquet write pipeline</title>
  <description>
  Build a TLE ingestion module that fetches active satellite TLEs from Celestrak, parses them via Skyfield, and saves cleaned data (name, line1, line2, and any IDs) to a Parquet file using Polars.
  </description>
  <requirements>
  - Implement a function similar to `load_and_store_tles(url, parquet_path)`.
  - Support configuration of the TLE URL and output Parquet path (e.g., via environment variables or a simple settings module).
  - Ensure the Parquet schema is stable and documented (e.g., columns: `name`, `line1`, `line2`, maybe `norad_id`).
  - Provide an easy way to run the pipeline manually (CLI entry point or simple script).
  </requirements>
  <files>
  - `./backend/app/tle_pipeline.py`
  - `./data/` (for `tles.parquet` or similar output path)
  </files>
  <verification>
  - Running the TLE pipeline produces a Parquet file in the expected location.
  - Parquet file contains multiple satellites with correct columns and non-empty values.
  - TLE fetch handles network errors gracefully (logging, not crashing the app).
  </verification>
</task>

<task id="05" type="auto">
  <title>Implement TLE loader and Skyfield satellite reconstruction</title>
  <description>
  Implement logic to load TLE data from Parquet on startup and reconstruct Skyfield `EarthSatellite` objects using a shared `Timescale` instance.
  </description>
  <requirements>
  - Create a loader that reads the Parquet file into a Polars DataFrame.
  - For each row, construct a Skyfield `EarthSatellite` using a single `ts = load.timescale()`.
  - Store the satellites in an efficient structure (e.g., dict keyed by name or NORAD ID) for later lookup.
  - Integrate this loader into FastAPI startup events so satellites are available at runtime.
  </requirements>
  <files>
  - `./backend/app/orbits.py` (or similar helper module)
  - Modifications to `./backend/app/main.py` to hook into startup events
  </files>
  <verification>
  - On app startup, logs indicate successful loading of satellites from Parquet.
  - A small internal test (or temporary route) can list the count of loaded satellites.
  - No significant startup performance issues when loading the full active satellite set.
  </verification>
</task>

<task id="06" type="checkpoint:human-verify">
  <title>Checkpoint: Verify TLE pipeline and satellite reconstruction</title>
  <description>
  Confirm that TLE ingestion and satellite reconstruction form a solid foundation before adding continuous propagation and APIs.
  </description>
  <verification_question>
  Can the system reliably fetch, store, and reload TLEs into Skyfield satellite objects on startup?
  </verification_question>
  <verification_criteria>
  - Parquet file exists and is not corrupted.
  - Startup consistently loads a reasonable number of satellites.
  - Error handling is acceptable for missing/invalid TLE files.
  </verification_criteria>
</task>

<task id="07" type="auto">
  <title>Implement global position computation helpers</title>
  <description>
  Implement helper functions to compute subpoints (lat, lon, alt) for satellites at a given time using Skyfield and WGS84.
  </description>
  <requirements>
  - Provide a function that, given an `EarthSatellite` and a `Time`, returns a struct/dict with latitude, longitude, and altitude in km.
  - Provide a function that computes positions for all tracked satellites at "now".
  - Ensure computations use a shared `Timescale` and Earth model (e.g., `wgs84.subpoint`).
  </requirements>
  <files>
  - `./backend/app/orbits.py` (extended with position helpers)
  </files>
  <verification>
  - A small internal test or utility prints positions for a few satellites.
  - Lat/lon values are within valid ranges and change over time as expected.
  </verification>
</task>

<task id="08" type="auto">
  <title>Integrate APScheduler for 5-second global position updates</title>
  <description>
  Integrate APScheduler with FastAPI to run a background job every ~5 seconds that recomputes global satellite positions and stores them in a thread-safe global structure.
  </description>
  <requirements>
  - Configure an APScheduler background scheduler that starts and stops with the FastAPI app.
  - Implement a job that:
    - Computes positions for all satellites at the current time.
    - Stores them in a global dictionary keyed by satellite name/ID.
    - Uses a lock or other concurrency mechanism to avoid race conditions.
  - Design the store in a way that could later be replaced by Redis (clear abstraction boundary).
  </requirements>
  <files>
  - `./backend/app/scheduler.py`
  - Modifications to `./backend/app/main.py` to initialize the scheduler.
  </files>
  <verification>
  - Logs show the scheduler running every few seconds without errors.
  - A temporary or final API route can read from the global positions store and return plausible values.
  </verification>
</task>

<task id="09" type="checkpoint:human-verify">
  <title>Checkpoint: Verify scheduler and global positions store</title>
  <description>
  Ensure the continuous update loop is stable and that the global positions store is safe to expose via APIs.
  </description>
  <verification_question>
  Is the 5-second scheduler reliably updating satellite positions without race conditions or performance issues?
  </verification_question>
  <verification_criteria>
  - Scheduler runs without unhandled exceptions over several minutes.
  - Global positions dictionary remains consistent and readable from the API layer.
  - CPU and memory usage appear reasonable for the satellite set size.
  </verification_criteria>
</task>

<task id="10" type="auto">
  <title>Implement /api/satellites endpoint</title>
  <description>
  Expose a REST endpoint returning the latest global satellite positions from the in-memory store.
  </description>
  <requirements>
  - Create a route `GET /api/satellites` in a dedicated router module.
  - Return a JSON structure like `{ "satellites": { [id_or_name]: {"lat": float, "lon": float, "alt_km": float} } }`.
  - Handle the case where no positions are yet available with a clear response.
  </requirements>
  <files>
  - `./backend/app/routes/satellites.py`
  - Modifications to `./backend/app/main.py` to include the router.
  </files>
  <verification>
  - `GET /api/satellites` returns HTTP 200 with a non-empty `satellites` mapping once the scheduler has run.
  - Response structure matches the documented format.
  </verification>
</task>

<task id="11" type="auto">
  <title>Implement /api/passes endpoint</title>
  <description>
  Implement a pass prediction endpoint that, given an observer lat/lon and satellite ID, returns rise/culmination/set events over the next 24 hours.
  </description>
  <requirements>
  - Route: `GET /api/passes?lat=...&lon=...&sat_id=...` (optionally alt).
  - Use `wgs84.latlon` to construct the observer location.
  - Use Skyfield event-finding utilities (e.g., `find_events`) to compute passes between `now` and `now + 24h`.
  - Return structured data including start time, end time, max elevation, and any useful metadata.
  - Validate input and return helpful error messages for invalid parameters or unknown satellites.
  </requirements>
  <files>
  - `./backend/app/routes/passes.py`
  - Possible helpers in `./backend/app/orbits.py`
  </files>
  <verification>
  - For a known satellite and observer, endpoint returns a list of passes covering the next day.
  - Times and elevations appear plausible (e.g., no negative durations).
  </verification>
</task>

<task id="12" type="auto">
  <title>Implement /api/groundtrack endpoint</title>
  <description>
  Provide a ground track endpoint that returns ~60 sampled subpoints over the next N hours for a given satellite.
  </description>
  <requirements>
  - Route: `GET /api/groundtrack?sat_id=...&hours=1` (default `hours=1`).
  - Sample times evenly over the requested window.
  - Return an ordered list of points with time, lat, lon, alt.
  - Ensure performance is acceptable even for many satellites (only one satellite queried at a time).
  </requirements>
  <files>
  - `./backend/app/routes/groundtrack.py`
  - Possible helpers in `./backend/app/orbits.py`
  </files>
  <verification>
  - For a chosen satellite, endpoint returns ~60 points over 1 hour.
  - Plotting these points shows a smooth path consistent with the satellite’s orbit.
  </verification>
</task>

<task id="13" type="checkpoint:human-verify">
  <title>Checkpoint: Verify REST API surface</title>
  <description>
  Review the REST endpoints (`/api/satellites`, `/api/passes`, `/api/groundtrack`) for correctness, consistency, and usability before building the frontend against them.
  </description>
  <verification_question>
  Are the REST endpoints stable, well-structured, and sufficiently documented for frontend consumption?
  </verification_question>
  <verification_criteria>
  - All three endpoints respond correctly under normal conditions.
  - Input validation and error responses are clear.
  - Output formats are documented (e.g., in backend README or OpenAPI schema).
  </verification_criteria>
</task>

<task id="14" type="auto">
  <title>Implement /ws/satellites WebSocket streaming</title>
  <description>
  Implement a WebSocket endpoint that streams the current global positions every ~5 seconds to connected clients.
  </description>
  <requirements>
  - Route: `/ws/satellites` using FastAPI’s WebSocket support.
  - On connect, accept and then loop: read from the global positions store and send JSON payloads similar to `/api/satellites`.
  - Handle client disconnects and errors gracefully.
  - Ensure the update interval is configurable or at least centralized.
  </requirements>
  <files>
  - `./backend/app/routes/ws.py` (or similar)
  - Modifications to `./backend/app/main.py` to include WebSocket route.
  </files>
  <verification>
  - Using a WebSocket client, receive position updates every ~5 seconds.
  - Message format matches the REST satellites payload.
  - No unhandled exceptions when clients disconnect or network issues occur.
  </verification>
</task>

<task id="15" type="checkpoint:human-verify">
  <title>Checkpoint: Verify WebSocket streaming behavior</title>
  <description>
  Confirm that the WebSocket stream is reliable and that its payload format is suitable for the frontend.
  </description>
  <verification_question>
  Does the WebSocket endpoint provide stable, correctly formatted satellite updates at the expected cadence?
  </verification_question>
  <verification_criteria>
  - Continuous updates observed over several minutes.
  - Payload size and frequency are reasonable for expected satellite counts.
  - Behavior under multiple concurrent clients is acceptable (or at least understood).
  </verification_criteria>
</task>

<task id="16" type="auto">
  <title>Scaffold frontend with React, Vite, CesiumJS, and Plotly</title>
  <description>
  Create the initial frontend application using Vite + React + TypeScript, integrating CesiumJS and Plotly dependencies.
  </description>
  <requirements>
  - Create `frontend/` directory with a Vite React TypeScript template.
  - Install CesiumJS and Plotly (and any minimal UI library if desired).
  - Configure Vite to work with Cesium (asset handling, if needed).
  - Add a basic app shell layout with areas for globe, satellite list, and details.
  </requirements>
  <files>
  - `./frontend/package.json`
  - `./frontend/vite.config.ts`
  - `./frontend/src/main.tsx`
  - `./frontend/src/App.tsx` (or similar)
  </files>
  <verification>
  - `npm install` (or equivalent) succeeds in `frontend/`.
  - `npm run dev` starts the app and shows a placeholder UI in the browser.
  </verification>
</task>

<task id="17" type="auto">
  <title>Implement WebSocket client and basic satellite visualization</title>
  <description>
  Implement a frontend WebSocket client for `/ws/satellites` and render satellite positions on a Cesium globe as billboards.
  </description>
  <requirements>
  - Implement a reusable hook or service to connect to `/ws/satellites` and maintain satellite state.
  - Render satellite markers on the Cesium globe using the streaming positions.
  - Implement click handling to select a satellite and display summary details.
  </requirements>
  <files>
  - `./frontend/src/components/GlobeView.tsx`
  - `./frontend/src/hooks/useSatelliteStream.ts` (or similar)
  </files>
  <verification>
  - With backend running, satellites appear and move over time on the globe.
  - Clicking a satellite shows its current details in a side panel or overlay.
  </verification>
</task>

<task id="18" type="checkpoint:human-verify">
  <title>Checkpoint: Verify real-time globe visualization</title>
  <description>
  Confirm that the frontend can reliably consume the WebSocket stream and present a clear, performant 3D view of satellites.
  </description>
  <verification_question>
  Does the globe visualization accurately reflect the streaming data and remain responsive?
  </verification_question>
  <verification_criteria>
  - Satellite positions update smoothly without excessive jitter.
  - UI remains responsive with a realistic number of satellites.
  - Satellite selection works as intended.
  </verification_criteria>
</task>

<task id="19" type="auto">
  <title>Implement observer controls and API integration</title>
  <description>
  Add UI controls for specifying an observer location and integrate with `/api/passes` and `/api/groundtrack` for a selected satellite.
  </description>
  <requirements>
  - Create `ObserverControls` component with inputs for lat/lon (and optional altitude).
  - Wire it to trigger requests to `/api/passes` and `/api/groundtrack` for the currently selected satellite.
  - Handle loading/error states gracefully.
  </requirements>
  <files>
  - `./frontend/src/components/ObserverControls.tsx`
  - Any necessary API client helpers (e.g., `./frontend/src/api/client.ts`).
  </files>
  <verification>
  - User can input coordinates and request data.
  - Network calls to `/api/passes` and `/api/groundtrack` succeed and return data.
  </verification>
</task>

<task id="20" type="auto">
  <title>Implement Plotly pass visualization</title>
  <description>
  Visualize passes as altitude vs. time using Plotly, highlighting peaks of visibility.
  </description>
  <requirements>
  - Create a `PassPlot` component that accepts pass data and renders a time-series chart.
  - Show altitude (y-axis) vs. time (x-axis), grouped by pass.
  - Visually highlight max elevation points (e.g., markers or annotations).
  </requirements>
  <files>
  - `./frontend/src/components/PassPlot.tsx`
  </files>
  <verification>
  - For sample passes, chart renders correctly and is readable.
  - Hover/tooltip behavior provides useful detail (time, elevation).
  </verification>
</task>

<task id="21" type="auto">
  <title>Implement ground track visualization on Cesium</title>
  <description>
  Draw the satellite’s projected ground track on the Cesium globe using data from `/api/groundtrack`.
  </description>
  <requirements>
  - Extend `GlobeView` (or a related component) to render a polyline for the ground track.
  - Ensure ground track updates when the selected satellite or observer window changes.
  - Keep rendering performant and visually distinct from live satellite markers.
  </requirements>
  <files>
  - Modifications to `./frontend/src/components/GlobeView.tsx`
  </files>
  <verification>
  - Ground track appears as a smooth curve aligned with the satellite’s orbit.
  - Track updates appropriately when the user changes selection or time window.
  </verification>
</task>

<task id="22" type="checkpoint:human-verify">
  <title>Checkpoint: Verify observer mode and visualizations</title>
  <description>
  Validate that the observer flow (select satellite, enter location, view passes and ground track) works end-to-end.
  </description>
  <verification_question>
  Can a user reliably use observer mode to understand when and where a satellite will be visible?
  </verification_question>
  <verification_criteria>
  - Changing observer location meaningfully affects pass predictions.
  - Pass chart and ground track are consistent with each other.
  - Errors and edge cases (no passes, invalid input) are handled gracefully.
  </verification_criteria>
</task>

<task id="23" type="auto">
  <title>Harden configuration, CORS, and documentation</title>
  <description>
  Finalize backend and frontend configuration for typical deployment scenarios and improve documentation for developers.
  </description>
  <requirements>
  - Centralize configuration (e.g., environment variables) for TLE URLs, scheduler intervals, and allowed origins.
  - Configure CORS so the frontend can communicate with the backend in dev and production.
  - Update backend and frontend READMEs with clear setup, run, and deployment instructions.
  </requirements>
  <files>
  - `./backend/app/config.py` (or equivalent)
  - `./backend/README.md`
  - `./frontend/README.md`
  - `./README.md` (root overview)
  </files>
  <verification>
  - Local dev setup is reproducible via a small number of documented commands.
  - CORS issues are not encountered during normal frontend/backend interaction.
  - Configuration values can be adjusted without code changes where reasonable.
  </verification>
</task>

<task id="24" type="checkpoint:human-verify">
  <title>Final checkpoint: End-to-end validation</title>
  <description>
  Perform a holistic review and test of the full system, from TLE ingestion through real-time globe visualization and observer-mode analysis.
  </description>
  <verification_question>
  Does the system meet the original objectives for real-time satellite tracking, visualization, and pass prediction?
  </verification_question>
  <verification_criteria>
  - A new developer can follow the READMEs to run backend and frontend locally.
  - Real-time satellite positions appear on the globe and update over time.
  - Passes and ground tracks are available and consistent for selected satellites and observer locations.
  - No major UX or stability issues block practical use.
  </verification_criteria>
</task>

</tasks>

<verification>
Before marking this plan complete, verify:
- TLE ingestion, storage, and reconstruction work reliably over repeated runs.
- Backend APIs and WebSocket behave correctly under normal and error conditions.
- Frontend provides a coherent and responsive user experience for both global and observer views.
- Documentation is sufficient for another developer to understand, run, and extend the system.
</verification>

<success_criteria>
This plan is successful when:
- The system can display real-time satellite positions on a Cesium globe from live TLE data.
- Users can select satellites and observer locations to view upcoming passes and ground tracks.
- The codebase is modular and documented enough to support future enhancements (e.g., Redis, sky-dome views, additional APIs).
</success_criteria>

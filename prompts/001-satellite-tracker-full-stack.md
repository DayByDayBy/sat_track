<objective>
Build a production-ready, real-time satellite tracking web application with a FastAPI backend (Skyfield + Polars + APScheduler) and a CesiumJS + React frontend. The system should ingest TLE data, compute satellite positions continuously, and serve them via HTTP and WebSocket APIs for 3D visualization and pass prediction.
</objective>

<context>
This project lives in the `sat_track` repository. You are free to create new folders and files as needed, but keep the structure simple and conventional.

Backend:
- Python 3.x
- Framework: FastAPI
- Libraries: Skyfield, Polars, APScheduler, uvicorn, (optional) Redis client
- Purpose: Provide a clean API for satellite state, passes, and ground tracks, powered by Skyfield-based propagation and a fast TLE data pipeline that uses Parquet.

Frontend:
- Framework: React (TypeScript) with Vite
- Libraries: CesiumJS (3D globe), Plotly (pass visualizations), a lightweight UI toolkit (e.g., Tailwind or similar) if helpful
- Purpose: Visualize satellites in real time on a 3D globe, allow selecting a satellite, and show passes/ground tracks for a user-specified observer location.

Assume deployment will target typical platforms (e.g., Fly.io/Railway for backend, Vercel/Netlify for frontend), so structure things in a way that makes deployment straightforward.
</context>

<requirements>
- Implement a daily TLE ingestion pipeline that:
  - **Fetches** TLEs from a Celestrak source (e.g., `/NORAD/elements/active.txt`).
  - **Parses** them into Skyfield `EarthSatellite` objects.
  - **Stores** clean TLE data (name, line1, line2) in a Parquet file using Polars.
  - Can be run manually (CLI or script) and is suitable to be scheduled via a cron/CI job.

- On FastAPI startup:
  - Load the latest Parquet TLE file.
  - Rebuild `EarthSatellite` objects using a single Skyfield `Timescale` (`ts = load.timescale()`).
  - Prepare any data structures needed for fast propagation (e.g., list or dict of satellites).

- Implement a background scheduler for real-time global position updates:
  - Use APScheduler (or equivalent) to run every ~5 seconds.
  - For every satellite, compute its subpoint (lat, lon, alt) in WGS84 using Skyfield and `wgs84.subpoint`.
  - Store results in a thread-safe global structure (e.g., a dictionary protected by a lock) with keys like satellite name or NORAD ID.
  - Structure the code in a way that can later swap this in-memory store for Redis.

- FastAPI HTTP API endpoints:
  - `GET /api/satellites`
    - Returns the latest global positions for all satellites from the in-memory store.
    - Response structure: `{ "satellites": { [id_or_name]: {"lat": float, "lon": float, "alt_km": float} } }`.
  - `GET /api/passes?lat=...&lon=...&sat_id=...`
    - Treat the observer as a fixed point on Earth (optionally accept altitude).
    - Use Skyfield’s event-finding utilities (e.g., `find_events`) to compute rise / culmination / set events over the next 24 hours.
    - Return a list of passes with start/end times, max elevation, and any auxiliary fields useful for the frontend.
  - `GET /api/groundtrack?sat_id=...&hours=1`
    - Compute a ground track for the selected satellite over the next `hours` (default 1 hour), with ~60 sampling points.
    - Return a time-ordered list of lat/lon/alt samples suitable for drawing a line on the globe.

- WebSocket API:
  - `GET /ws/satellites` (WebSocket endpoint)
    - After accepting the connection, send an update every 5 seconds.
    - Each message should contain the same structure as `/api/satellites` for easy reuse on the frontend.
    - Handle disconnects gracefully.

- Frontend features (React + CesiumJS + Plotly):
  - **Global 3D View**
    - Render a CesiumJS globe.
    - Show all satellites as billboards/points using the latest WebSocket data.
    - Update positions smoothly as new WebSocket messages arrive.
    - Clicking a satellite selects it and displays key details (name, NORAD ID, current lat/lon/alt, maybe velocity).

  - **Observer/Local Mode**
    - UI for entering observer latitude and longitude (and optionally altitude).
    - Once an observer and satellite are selected, fetch:
      - `/api/passes` for that satellite and observer.
      - `/api/groundtrack` for that satellite.

  - **Pass Visualization**
    - Use Plotly to plot altitude vs. time over the next 24 hours of passes.
    - Highlight peaks of visibility (max elevation in each pass).

  - **Ground Track Visualization**
    - Draw the ground track line for the selected satellite on the Cesium globe using the ground track API data.

- Deployment/operational considerations:
  - Provide basic configuration for CORS so the React frontend can talk to the FastAPI backend in development and production.
  - Make it straightforward to:
    - Run the backend locally with `uvicorn`.
    - Run the frontend locally with `npm/yarn/pnpm` dev script.
  - (Optional but encouraged) Design backend state in a way that can later use Redis for shared state when scaling beyond one instance.

- Quality requirements:
  - Clear, small, focused modules for TLE ingestion, satellite propagation, API routing, and scheduling.
  - Reasonable error handling and logging (e.g., failed TLE download, bad user inputs).
  - Clean, modern frontend UX with a simple layout: 3D globe, selection panel, and pass/ground-track views.
</requirements>

<implementation>
Backend structure:
- Use a `backend/` directory (or similar) with:
  - `backend/app/main.py` as the FastAPI entrypoint.
  - Separate modules for:
    - TLE fetching/parsing and Parquet I/O (e.g., `backend/app/tle_pipeline.py`).
    - Satellite propagation and position helpers (e.g., `backend/app/orbits.py`).
    - API routers (e.g., `backend/app/routes/satellites.py`).
    - Scheduler setup for APScheduler and background jobs (e.g., `backend/app/scheduler.py`).

- Follow patterns similar to the conceptual code examples in the description:
  - One global `Timescale` object per process.
  - A central list/dict of `EarthSatellite` objects built at startup.
  - A global positions store protected by a lock.

- For the TLE pipeline:
  - Write a function to fetch TLE text from Celestrak and parse it via Skyfield.
  - Convert to a Polars DataFrame with columns like `name`, `line1`, `line2`, and optionally an ID.
  - Write to a Parquet file in a deterministic path (e.g., `data/tles.parquet`).
  - Provide a small CLI (e.g., `python -m backend.app.tle_pipeline refresh`) or script entrypoint to run the downloader.

- For the scheduler and global positions:
  - Use APScheduler’s background scheduler integrated with FastAPI’s lifespan/startup events.
  - In the scheduled job, compute subpoints for all satellites at the current time.
  - Swap the global dictionary atomically (under a lock) for predictable reads.

- For passes and ground tracks:
  - Use Skyfield’s `wgs84.latlon` for the observer.
  - Use event-finding (`find_events` or equivalent) to derive rise/culmination/set events over a 24-hour window.
  - For ground tracks, sample time steps evenly over the requested window and compute each subpoint.

- WebSocket implementation:
  - Define a FastAPI WebSocket endpoint that continually sends JSON messages every 5 seconds.
  - Reuse the same data structure as the `/api/satellites` REST endpoint.

Frontend structure:
- Create a `frontend/` directory with a Vite + React + TypeScript app.
  - `frontend/src/main.tsx` as the React entrypoint.
  - Components organized roughly as:
    - `GlobeView` (CesiumJS globe + satellite markers).
    - `SatelliteList` / selection panel.
    - `ObserverControls` for lat/lon input.
    - `PassPlot` (Plotly-based chart).

- WebSocket client:
  - Implement a small hook or service for managing the WebSocket connection to `/ws/satellites`.
  - Maintain client-side state of satellites and update leaflet/markers in Cesium accordingly.

- Cesium integration:
  - Initialize a Cesium viewer and add entities for each satellite.
  - Update entity positions on each WebSocket update.
  - Handle click events on entities to select a satellite.

- Pass and ground track fetching:
  - On satellite + observer selection, call `/api/passes` and `/api/groundtrack`.
  - Render the passes in Plotly (altitude vs. time).
  - Draw the ground track polyline on the Cesium globe.

General guidelines:
- Prefer clear, well-named functions and modules over large monolithic files.
- Keep configuration (e.g., TLE URL, update interval) in a central settings module or environment variables to make deployment easier.
- Go beyond just getting it to work: aim for a structure that will be maintainable as the number of satellites and users grows.
</implementation>

<output>
- `./backend/app/main.py` - FastAPI application entrypoint with routes and WebSocket wiring.
- `./backend/app/tle_pipeline.py` - TLE fetching, parsing, and Parquet read/write utilities (and optional CLI entrypoint).
- `./backend/app/orbits.py` - Skyfield helpers for positions, passes, and ground tracks.
- `./backend/app/scheduler.py` - APScheduler configuration and global positions update job.
- `./backend/requirements.txt` - Python dependency list for the backend.
- `./backend/README.md` - Instructions for setting up, running, and deploying the backend.

- `./frontend/package.json` - Frontend dependencies and scripts (Vite + React + TypeScript + Cesium + Plotly).
- `./frontend/vite.config.ts` - Vite configuration.
- `./frontend/src/main.tsx` - React entrypoint, app shell, and router/wiring.
- `./frontend/src/components/GlobeView.tsx` - Cesium globe and satellite visualization.
- `./frontend/src/components/ObserverControls.tsx` - Observer location input and controls.
- `./frontend/src/components/PassPlot.tsx` - Plotly-based pass visualization component.
- `./frontend/README.md` - Instructions for setting up, running, and deploying the frontend.

- `./README.md` - High-level project overview, including how backend and frontend fit together and how to run both locally.
</output>

<verification>
- Backend:
  - Install backend dependencies and run the FastAPI app (e.g., via `uvicorn backend.app.main:app --reload`).
  - Run the TLE pipeline script to fetch and save a Parquet file.
  - Confirm on startup that the app loads satellites from the Parquet file (via logs or a health endpoint).
  - Call `GET /api/satellites` and ensure it returns multiple satellites with plausible positions.
  - Call `GET /api/passes` with a sample observer location and satellite; verify a list of passes is returned for the next 24 hours.
  - Call `GET /api/groundtrack` and verify it returns a time-ordered list of lat/lon/alt points.
  - Connect to `/ws/satellites` via a WebSocket client and confirm updates arrive every ~5 seconds.

- Frontend:
  - Run the Vite dev server and open the app in a browser.
  - Confirm that satellites appear on the Cesium globe and move over time.
  - Click a satellite and ensure details appear.
  - Enter an observer location and verify that pass and ground-track visualizations render correctly via Plotly and Cesium.

- End-to-end:
  - With both backend and frontend running, verify that real-time updates flow end-to-end: TLE → backend propagation → WebSocket → Cesium globe, and that passes and ground tracks match expectations.
</verification>

<success_criteria>
- A developer can clone the repo, run a small number of clear setup commands, and:
  - Start the backend and frontend locally.
  - See real-time satellite positions on a Cesium globe.
  - Select a satellite, specify an observer location, and view upcoming passes and a ground track.
- The backend structure is modular (pipeline, propagation, API, scheduler) and ready to scale with more satellites and instances.
- The codebase is organized and documented well enough that adding new APIs (e.g., filtering by satellite groups) or new frontend views (e.g., sky-dome visualization) is straightforward.
</success_criteria>

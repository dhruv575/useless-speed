# Deploying Useless Speed

The app fits one Node service. It serves the frontend, bundled data and a small API; simulation computation stays in each user's browser. The research corpus is a developer/research download and is not part of the production image.

## Railway

Connect the repository root to a Railway service. The included Dockerfile builds the npm workspace and copies only the built frontend, server and app data into the runtime image. It uses Node 24 and runs as the `node` user. `.dockerignore` excludes the full research corpus, development environments, route caches and test output.

Use these settings:

| Setting | Value |
|---|---|
| Build | Repository-root `Dockerfile` |
| Start | Dockerfile's default: `node app/server.mjs` |
| Host | `0.0.0.0` (already set by Dockerfile) |
| Port | Railway-injected `PORT`; Docker default is 8080 |
| Healthcheck path | `/api/health` |
| Replicas | One initially; current rate-spacing state is per process |
| Public networking | Generate a Railway domain or attach your domain |

The app's localhost default is appropriate for local work; deployed services must accept incoming container connections. See [Railway host/port guidance](https://docs.railway.com/networking/troubleshooting/application-failed-to-respond), [Dockerfile builds](https://docs.railway.com/builds/dockerfiles), and [healthchecks](https://docs.railway.com/deployments/healthchecks).

A healthcheck verifies that the process and address directory loaded. It does not test external map/routing availability. The app does not require a database or a separate worker service. No Railway service is created by the files in this folder alone.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `PORT` | 8788 locally; 8080 in Docker | HTTP port |
| `HOST` | `127.0.0.1` locally; `0.0.0.0` in Docker | Listening interface |
| `CACHE_DIR` | `app/cache` next to the server | Writable route-cache directory |
| `ROUTER_URL` | `https://router.project-osrm.org` | Base URL of an OSRM-compatible routing service |

The server reads process environment variables; it does not automatically load a `.env` file. Railway injects variables directly. Set them in your shell for local overrides. The Vite development proxy expects the API on 8788, so changing the development API port also requires updating `app/vite.config.ts`.

An optional volume can retain cached routes across deployments. Mount it at the chosen `CACHE_DIR`, keep the directory writable by the runtime user, and do not mount it over `app/data` or the application itself. The cache is disposable; losing it means routes must be fetched again. [Railway volumes](https://docs.railway.com/volumes)

## External services and growth

The current OSRM demo endpoint allows reasonable noncommercial use, limits requests to one per second and provides no uptime guarantees. The server spaces new requests 1.1 seconds apart and reuses cached/in-flight routes. Multiple replicas would each have independent spacing; do not add replicas and assume the same global request limit is maintained. For sustained traffic or commercial use, supply an appropriate routing service through `ROUTER_URL`. [OSRM demo policy](https://github.com/Project-OSRM/osrm-backend/wiki/Demo-server)

MapLibre loads the locally customized style in `app/src/map-style.json` and fetches OpenFreeMap tiles/fonts/sprites directly from the browser. Keep map attribution and upstream style notices. Local street geometry is the fallback when the tile source fails.

This is currently a small-demo server: address search scans an in-memory directory, file serving is basic, and uncached routing has a shared queue. Measure memory, latency and traffic before making capacity or cost promises.

## Local production smoke test

```sh
npm ci
npm run build
npm start
```

Visit `http://127.0.0.1:8788/api/health` and the app at `http://127.0.0.1:8788/`. Then try an address search and a simulation, because a successful healthcheck alone does not test those paths.

With Docker installed:

```sh
docker build -t useless-speed .
docker run --rm -p 8080:8080 useless-speed
```

Visit `http://127.0.0.1:8080/`. A public deployment still needs its own build, startup and browser verification.

# OSRM Motorcycle Router — Bojonegoro & Tuban

Self-hosted motorcycle-oriented routing built on OpenStreetMap data and Project OSRM. The Docker image downloads a pinned Geofabrik extract, verifies its MD5 checksum, clips the configured region, builds the routing graph, and copies only the graph and runtime into the final image. Raw `.osm.pbf` files and build tools are not included in the final image or source repository.

## Routing policy

- Prioritizes OSM access tags for `motorcycle`, then `motor_vehicle`, `vehicle`, and `access`.
- Excludes ways tagged `toll=yes`, `highway=motorway`, and `highway=motorway_link`.
- Uses a custom Lua profile derived from Project OSRM's `car.lua`; see `LICENSE.OSRM` and `THIRD_PARTY_NOTICES.md`.
- OSRM has no native motorcycle API enum. The route endpoint remains `/route/v1/driving/`; the motor-specific behavior is encoded in the preprocessed graph. Duration estimates use OSRM's default road-speed table and are not calibrated to local motorcycle traffic.

The default dataset is a Java extract clipped to a buffered bounding box around Bojonegoro and Tuban, not exact administrative polygons:

```text
111.25,-7.65,112.55,-6.45
```

## Run the prebuilt GHCR image (no build)

The workflow at `.github/workflows/publish-image.yml` builds the image and publishes it to GHCR with GitHub Actions when code is pushed to `main` or a `v*` tag. It uses the workflow's `GITHUB_TOKEN` with `packages: write`; no personal access token or local build is needed. The first run downloads the OSM extract and builds the route graph, so it can take several minutes.

After the workflow succeeds, make the GHCR package public in GitHub: **Packages → osrm-motorcycle-router → Package settings → Change visibility → Public**. Then pull and run it directly on the server:

```bash
docker pull ghcr.io/nuralan/osrm-motorcycle-router:latest
docker run -d --name osrm-motorcycle --restart unless-stopped \
  -p 5000:5000 ghcr.io/nuralan/osrm-motorcycle-router:latest
```

Test the server:

```bash
curl 'http://localhost:5000/route/v1/driving/111.882,-7.150;112.064,-6.897?overview=false&steps=true'
```

The package is not yet published. It will become available after these commits are pushed to the intended `NurAlan/osrm-motorcycle-router` repository, the Action completes successfully, and package visibility is set to public. Anonymous pulls then need no `docker login`.

## Quick start from source (build locally)

Requirements: Docker with BuildKit/Buildx and internet access. The first build downloads the pinned Java PBF (currently about 900 MB), verifies its `.md5` sidecar, then preprocesses the regional extract. Build time and temporary disk usage are significantly higher than runtime requirements.

```bash
docker compose -f compose.yaml up --build -d
```

The API is available on host port `5001` (container port `5000`):

```bash
curl 'http://localhost:5001/route/v1/driving/111.882,-7.150;112.064,-6.897?overview=false&steps=true'
```

Expected response includes `"code":"Ok"`. With OrbStack, the service may also be reachable through its generated `.orb.local` hostname.

Stop the service:

```bash
docker compose -f compose.yaml down
```

## Build a portable one-image deployment

Build for the architecture of the destination server. For a typical x86_64 Linux VPS:

```bash
docker buildx build --platform linux/amd64 --load \
  -t osrm-motorcycle-router:latest .
```

Export, copy the archive to the server, then load and run it:

```bash
docker save osrm-motorcycle-router:latest -o osrm-motorcycle-router-linux-amd64.tar
# On the server:
docker load -i osrm-motorcycle-router-linux-amd64.tar
docker run -d --name osrm-motorcycle --restart unless-stopped \
  -p 5000:5000 osrm-motorcycle-router:latest
```

For ARM64 servers, build with `--platform linux/arm64`. The final image contains the OSRM runtime and preprocessed routing graph; the source PBF and intermediate extract stage are not copied into it.

## Customize the data region

The build uses Docker build arguments. Provide an OSM PBF URL, its matching Geofabrik MD5 sidecar, the source filename, and a bounding box in `min_lon,min_lat,max_lon,max_lat` order:

```bash
docker buildx build --platform linux/amd64 --load \
  --build-arg OSM_PBF_URL=https://download.geofabrik.de/asia/indonesia/java-261029.osm.pbf \
  --build-arg OSM_PBF_MD5_URL=https://download.geofabrik.de/asia/indonesia/java-261029.osm.pbf.md5 \
  --build-arg OSM_PBF_FILENAME=java-261029.osm.pbf \
  --build-arg REGION_BBOX=111.25,-7.65,112.55,-6.45 \
  -t osrm-motorcycle-router:latest .
```

Do not commit raw OSM extracts or generated `.osrm*` graph files. They are ignored by `.gitignore` and excluded from the Docker build context.

## Development checks

```bash
python3 -m unittest discover -s tests -v
docker compose -f compose.yaml config --quiet
```

## Data attribution and licensing

Display this attribution in applications/maps using the routing data:

> © OpenStreetMap contributors. Data available under the Open Database License (ODbL) at <https://www.openstreetmap.org/copyright>.

The routing graph is derived from OSM data; review ODbL attribution and share-alike obligations before redistributing derived databases. Source and third-party notices are in `LICENSE`, `LICENSE.OSRM`, and `THIRD_PARTY_NOTICES.md`.

## Community standards

See [`CONTRIBUTING.md`](CONTRIBUTING.md), [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md), and [`SECURITY.md`](SECURITY.md). Please report security vulnerabilities privately through GitHub rather than in a public issue.

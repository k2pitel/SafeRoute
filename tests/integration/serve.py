"""Start one Backend API instance for the integration test (kapitel 6, figur 6.1).

    python tests/integration/serve.py --port 8001
    python tests/integration/serve.py --port 8002 --osrm-url http://127.0.0.1:9   # OSRM "down" (NF7)

Each instance gets its own throwaway Datalag folder, so test data never
lands in backend/data, and runs the real Async Worker (news + crime stats),
so zones and news are real. Run with the backend's virtualenv Python.
"""
import argparse
import os
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--osrm-url", help="override OSRM_SERVER_URL (e.g. a closed port to simulate an outage)")
    args = parser.parse_args()

    # Settings are read at import time, so the environment must be set first.
    os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix=f"saferoute-it-{args.port}-")
    os.environ["ASYNC_WORKER"] = "background"
    if args.osrm_url:
        os.environ["OSRM_SERVER_URL"] = args.osrm_url
    os.chdir(BACKEND_DIR)  # so backend/.env is picked up
    sys.path.insert(0, str(BACKEND_DIR))

    import uvicorn

    print(f"Backend API on :{args.port}, Datalag in {os.environ['DATA_DIR']}", flush=True)
    uvicorn.run("app.main:app", host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()

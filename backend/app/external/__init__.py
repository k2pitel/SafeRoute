"""Adapters for the external systems SafeRoute does not control (afsnit 4.1).

Each module wraps exactly one external relation behind a small function
API, so protocol details (URLs, coordinate order, CSV/RSS/CDX parsing) live
in one place and the services above only see plain Python data:

- ``osrm``               — OSRM Route service (rutemotor)
- ``statistics_denmark`` — Danmarks Statistik + DAGI municipality boundaries
                           (offentlige datakilder)
- ``news_sources``       — Danish outlets' RSS feeds + article pages (nyhedskilder)
- ``wayback``            — Internet Archive CDX index (historical news backfill)
"""

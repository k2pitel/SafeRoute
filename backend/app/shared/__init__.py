"""Shared kernel: value objects every server-side subsystem uses.

Kept outside the subsystems so the Datalag and the Async Worker never have
to import from the Backend API (dependencies only point downwards, figur 4.2).

- ``geo``  — BBox and LatLon, the coordinate types in tabel 4.1's query strings
- ``news`` — NewsItem, produced by the Async Worker, stored by the Datalag,
             served by the Backend API
"""

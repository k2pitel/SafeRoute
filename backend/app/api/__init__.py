"""Delsystem Backend API (figur 4.2, afsnit 5.2).

One package per bounded context, named after the domain model (afsnit 3.4)
and the endpoints in tabel 4.1. Every context has the same three roles as
afsnit 5.2.1.1 describes:

- ``router.py``  — boundary: HTTP in and out, no domain logic, no SQL
- ``service.py`` — control: domain logic, shared with the Async Worker,
                   never sees HTTP; data only via app.datalag, external
                   systems only via app.external
- ``schemas.py`` — contract: the Pydantic models FastAPI validates against

Contexts: auth (Bruger), routes (Rute/Ruteforslag, UC1), reports
(Hændelsesrapport, UC2), zones (Zone, F7/F5), news (Nyhedsartikel, F9),
crime_index (By/CrimeIndex, F4), segments (Vejsegment, NF8), incidents.
No context imports another context's router. Cross-cutting request concerns
live in ``dependencies.py``; the list of routers in ``routers.py``.
"""

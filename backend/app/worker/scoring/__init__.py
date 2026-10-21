"""Scoring pipeline of the Async Worker (afsnit 4.2.1, 4.2.4, 5.3.3).

Segment tryghedsscores are computed here, outside the request path, and
written to the Datalag with differential-privacy noise applied once, at
write time.

- ``features`` — feature vector per road segment
- ``train``    — offline training: python -m app.worker.scoring.train
- ``serving``  — model inference + SHAP explanation (NF8)
- ``laplace``  — Laplace mechanism for NF11
"""

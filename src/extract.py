"""
Extraction layer: talks to the Open-Meteo API only. Nothing in this
module knows about pandas or the database — it just returns validated
Python objects, which keeps the pipeline stages testable in isolation.
"""


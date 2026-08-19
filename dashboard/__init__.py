"""Dashboard visualisation/export layer (V12.3 — see CLAUDE.md Roadmap).

Consumes an already-built core.services.dashboard_data.DashboardDataset.
Never reads Heroes, Legends, historical datasets, or any Registry
directly — that remains the exclusive responsibility of the callers that
assemble a DashboardDataset in the first place.
"""

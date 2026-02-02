"""Plotting utilities for events and summaries."""

from .generator import (
    MATPLOTLIB_AVAILABLE,
    PlotError,
    PlotPaths,
    check_matplotlib,
    generate_all_plots,
    generate_summary_table,
    plot_all_events,
    plot_event,
    plot_event_price,
    plot_event_spread,
    plot_event_volume,
    plot_ordering_by_symbol,
    plot_ordering_distribution,
)

__all__ = [
    "MATPLOTLIB_AVAILABLE",
    "PlotError",
    "PlotPaths",
    "check_matplotlib",
    "generate_all_plots",
    "generate_summary_table",
    "plot_all_events",
    "plot_event",
    "plot_event_price",
    "plot_event_spread",
    "plot_event_volume",
    "plot_ordering_by_symbol",
    "plot_ordering_distribution",
]

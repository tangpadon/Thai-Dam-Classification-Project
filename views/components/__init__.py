"""Dashboard UI components package."""

from views.components.sidebar import render_sidebar
from views.components.header import render_header
from views.components.dam_selector import render_dam_selector
from views.components.current_overview import render_current_overview
from views.components.forecast_cards import render_forecast_cards
from views.components.trend_and_details import render_trend_and_details
from views.components.history_and_summary import render_history_and_summary
from views.components.footer import render_footer

__all__ = [
    "render_sidebar",
    "render_header",
    "render_dam_selector",
    "render_current_overview",
    "render_forecast_cards",
    "render_trend_and_details",
    "render_history_and_summary",
    "render_footer",
]


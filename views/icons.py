"""SVG Icons and rendering helpers for the dashboard."""

SVG_PATHS = {
    "water": '<path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path>',
    "home": '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline>',
    "search": '<circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>',
    "dam-menu": '<path d="M4 21V9l5-5h6l5 5v12"></path><path d="M9 4v17"></path><path d="M15 4v17"></path><line x1="2" y1="21" x2="22" y2="21"></line>',
    "chart": '<line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line>',
    "clock": '<circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>',
    "info": '<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line>',
    "shield-check": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><polyline points="9 12 11 14 15 10"></polyline>',
    "drop-waves": '<path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path><path d="M4 19c1.5-1 3.5-1 5 0s3.5 1 5 0 3.5-1 5 0" stroke-width="1.8"></path>',
    "inflow-waves": '<line x1="12" y1="4" x2="12" y2="16"></line><polyline points="7 11 12 16 17 11"></polyline><path d="M3 20c2-1 4-1 6 0s4 1 6 0 4-1 6 0" stroke-width="1.8"></path>',
    "outflow-waves": '<line x1="12" y1="16" x2="12" y2="4"></line><polyline points="7 9 12 4 17 9"></polyline><path d="M3 20c2-1 4-1 6 0s4 1 6 0 4-1 6 0" stroke-width="1.8"></path>',
    "document-check": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline>',
    "map-pin": '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle>',
}


def svg_icon(name: str, size: int = 18, color: str = "currentColor") -> str:
    """Render an SVG icon inline with given name, size, and stroke color."""
    paths = SVG_PATHS.get(name, "")
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        f'style="display:inline-block; vertical-align:middle; flex-shrink:0;">{paths}</svg>'
    )


# Alias for backward compatibility
_svg_icon = svg_icon


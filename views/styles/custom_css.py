"""Custom CSS stylesheet for the Thai Dam Classification dashboard."""


def get_custom_css() -> str:
    """Return the complete CSS string for Dashboard layout, sidebar, badges, and components."""
    return """
        <style>
        html, body, [data-testid="stAppViewContainer"], section.main {
            scroll-behavior: smooth;
        }
        .stApp {
            background-color: #f8fafc;
        }

        /* 1. Sidebar Navigation: light blue vertical column throughout */
        [data-testid="stSidebar"],
        [data-testid="stSidebar"] > div:first-child,
        [data-testid="stSidebarContent"] {
            background-color: #f0f7ff !important;
            border-right: 1px solid #e0eefd;
        }

        /* Badge Numbers for Sections (1, 2, 3, 4, 5, 6, 7) */
        .badge-num {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background-color: #0284c7;
            color: white;
            border-radius: 50%;
            width: 22px;
            height: 22px;
            font-size: 13px;
            font-weight: bold;
            margin-right: 8px;
            flex-shrink: 0;
        }
        .section-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #0f172a;
            display: flex;
            align-items: center;
            margin-bottom: 14px;
            scroll-margin-top: 80px;
        }
        .section-title:target {
            animation: highlight-section 1.5s ease-out;
        }
        @keyframes highlight-section {
            0% { background-color: rgba(2, 132, 199, 0.15); border-radius: 6px; }
            100% { background-color: transparent; }
        }

        /* Flashing highlight animation for section titles and containers (Single pulse) */
        @keyframes section-flash-highlight {
            0% {
                background-color: rgba(2, 132, 199, 0.28);
                box-shadow: 0 0 0 4px rgba(2, 132, 199, 0.3);
            }
            100% {
                background-color: transparent;
                box-shadow: none;
            }
        }

        .section-flash {
            animation: section-flash-highlight 1.2s ease-out forwards !important;
            border-radius: 6px !important;
            padding: 2px 6px !important;
            margin-left: -6px !important;
        }

        @keyframes container-border-flash {
            0% {
                border-color: #0284c7 !important;
                box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.3), 0 1px 3px rgba(0, 0, 0, 0.04) !important;
            }
            100% {
                border-color: #e2e8f0 !important;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
            }
        }

        .container-flash {
            animation: container-border-flash 1.2s ease-out forwards !important;
        }

        /* Main Area White Cards (Sections 1 to 7) */
        .st-key-sec_dam_select,
        .st-key-sec_overview,
        .st-key-sec_forecast,
        .st-key-sec_trend,
        .st-key-sec_history,
        .st-key-sec_summary {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 10px !important;
            padding: 20px 22px 26px 22px !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
            margin-bottom: 22px !important;
            transition: all 0.2s ease;
        }

        /* Sidebar Navigation Links */
        .sidebar-nav {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .sidebar-nav .nav-link {
            color: #475569 !important;
            padding: 9px 12px;
            border-radius: 8px;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 12px;
            transition: all 0.2s ease-in-out;
            cursor: pointer !important;
            user-select: none;
        }
        .sidebar-nav .nav-link:hover {
            background-color: #e0f2fe !important;
            color: #0284c7 !important;
        }
        .sidebar-nav .nav-link:hover svg {
            stroke: #0284c7 !important;
        }
        .sidebar-nav .nav-link.active {
            background-color: #e0f2fe !important;
            color: #0284c7 !important;
            font-weight: 600;
        }
        .sidebar-nav .nav-link.active svg {
            stroke: #0284c7 !important;
        }

        /* Header Date Box */
        .header-date-box {
            text-align: right;
            font-size: 0.85rem;
            color: #64748b;
            margin-top: 8px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 6px;
        }

        /* Responsive Metric Cards (Section 2) */
        .overview-metric-card {
            display: flex;
            align-items: center;
            gap: 8px;
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 10px 8px;
            height: 100%;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
            box-sizing: border-box;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        .overview-metric-card:hover {
            box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        }

        /* Responsive Forecast Cards (Section 3) */
        .forecast-card {
            border-radius: 8px;
            padding: 18px;
            text-align: center;
            height: 100%;
            box-sizing: border-box;
            transition: transform 0.15s ease;
        }

        /* Responsive Specifications Table (Section 5) */
        .dam-details-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.83rem;
            background: white;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }

        /* Responsive Table Container (Section 6) */
        .table-responsive {
            width: 100%;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            border-radius: 8px;
        }
        .table-responsive table {
            min-width: 540px;
        }

        /* Replace Selectbox downward arrow with Search icon ONLY for Section 1 (dam_select) */
        .st-key-dam_select [aria-label="Open"] svg path,
        .st-key-dam_select [data-baseweb="select"] svg path {
            display: none !important;
        }
        .st-key-dam_select [aria-label="Open"] svg,
        .st-key-dam_select [data-baseweb="select"] svg {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23475569' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='8'%3E%3C/circle%3E%3Cline x1='21' y1='21' x2='16.65' y2='16.65'%3E%3C/line%3E%3C/svg%3E") !important;
            background-repeat: no-repeat !important;
            background-position: center !important;
            background-size: 18px 18px !important;
            width: 20px !important;
            height: 20px !important;
            transition: all 0.2s ease;
        }
        .st-key-dam_select [aria-label="Open"]:hover svg,
        .st-key-dam_select [data-baseweb="select"]:hover svg {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%230284c7' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='8'%3E%3C/circle%3E%3Cline x1='21' y1='21' x2='16.65' y2='16.65'%3E%3C/line%3E%3C/svg%3E") !important;
        }

        /* Streamlit components iframe hidden styling */
        iframe[title="streamlit.components.v1.html"],
        [data-testid="stCustomComponentV1"] {
            position: fixed !important;
            width: 0 !important;
            height: 0 !important;
            opacity: 0 !important;
            pointer-events: none !important;
            border: none !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        /* ========================================================= */
        /* RESPONSIVE MEDIA QUERIES (Tablet & Mobile)                */
        /* ========================================================= */

        /* Tablet View (<= 992px) */
        @media (max-width: 992px) {
            .overview-metric-card {
                padding: 10px 6px !important;
            }
            .overview-metric-card .metric-title-text {
                font-size: 0.65rem !important;
            }
        }

        /* Mobile & Small Tablet View (<= 768px) */
        @media (max-width: 768px) {
            /* Compact Section Padding */
            .st-key-sec_dam_select,
            .st-key-sec_overview,
            .st-key-sec_forecast,
            .st-key-sec_trend,
            .st-key-sec_history,
            .st-key-sec_summary {
                padding: 16px 14px 22px 14px !important;
                margin-bottom: 16px !important;
                border-radius: 8px !important;
            }

            /* Section Titles & Badges */
            .section-title {
                font-size: 0.96rem !important;
                margin-bottom: 10px !important;
                scroll-margin-top: 70px !important;
            }
            .badge-num {
                width: 20px !important;
                height: 20px !important;
                font-size: 11px !important;
                margin-right: 6px !important;
            }

            /* Header Adjustments */
            .header-title {
                font-size: 1.25rem !important;
            }
            .header-date-box {
                justify-content: flex-start !important;
                text-align: left !important;
                margin-top: 2px !important;
                margin-bottom: 8px !important;
            }

            /* Overview Cards Stack Spacing */
            .overview-metric-card {
                padding: 12px 14px !important;
                margin-bottom: 6px !important;
            }

            /* Forecast Cards Spacing & Typography */
            .forecast-card {
                padding: 14px 10px !important;
                margin-bottom: 8px !important;
            }
            .forecast-risk-title {
                font-size: 1.25rem !important;
            }

            /* Details Table Spacing */
            .dam-details-table {
                font-size: 0.78rem !important;
            }
            .dam-details-table td {
                padding: 6px 8px !important;
            }
        }

        /* Small Phone View (<= 480px) */
        @media (max-width: 480px) {
            .st-key-sec_dam_select,
            .st-key-sec_overview,
            .st-key-sec_forecast,
            .st-key-sec_trend,
            .st-key-sec_history,
            .st-key-sec_summary {
                padding: 14px 10px 18px 10px !important;
                margin-bottom: 14px !important;
            }
            .header-title {
                font-size: 1.15rem !important;
            }
        }
        </style>
    """


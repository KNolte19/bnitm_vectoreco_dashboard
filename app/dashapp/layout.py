"""Dash application layout."""
import dash_mantine_components as dmc
from dash import dcc, html, dash_table
from datetime import datetime, timedelta

# Constants
TABLE_PAGE_SIZE = 10


def create_layout():
    """Create the Dash application layout.

    Returns:
        Dash layout component
    """
    # Default date range: last 24 hours
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)

    layout = dmc.Container(
        size="xl",
        p="md",
        children=[
            # ── Sticky warning banner (hidden when no issues) ────────────────
            dmc.Alert(
                id="warning-banner",
                title="",
                color="yellow",
                style={
                    "display": "none",
                    "zIndex": 999,
                    "fontSize": 15,
                    "fontWeight": "bold",
                    "marginBottom": 16,
                },
            ),

            # ── Page title ───────────────────────────────────────────────────
            dmc.Title(
                "Mirrormere 🌊",
                order=1,
                style={"textAlign": "center", "marginBottom": 24},
            ),

            # ── Warning notification subscription panel ───────────────────────
            dmc.Accordion(
                style={"marginBottom": 24},
                children=[
                    dmc.AccordionItem(
                        value="notifications",
                        children=[
                            dmc.AccordionControl("🔔 Warning Notifications"),
                            dmc.AccordionPanel(
                                dmc.Stack(
                                    children=[
                                        dmc.TextInput(
                                            id="email-input",
                                            label="Your email address",
                                            placeholder="user@example.com",
                                        ),
                                        dmc.Checkbox(
                                            id="temp-warning-checkbox",
                                            label="Temperature warnings",
                                            checked=False,
                                        ),
                                        html.Div(
                                            id="temp-threshold-container",
                                            style={"display": "none"},
                                            children=[
                                                dmc.NumberInput(
                                                    id="temp-threshold-input",
                                                    label="Temperature deviation threshold (°C)",
                                                    value=2.5,
                                                    min=0.1,
                                                    step=0.1,
                                                ),
                                            ],
                                        ),
                                        dmc.Checkbox(
                                            id="conn-warning-checkbox",
                                            label="Connectivity warnings",
                                            checked=False,
                                        ),
                                        dmc.NumberInput(
                                            id="grace-period-input",
                                            label="Grace period before sending alert (hours)",
                                            value=24,
                                            min=1,
                                            step=1,
                                        ),
                                        dmc.Button(
                                            "Save Notification Settings",
                                            id="btn-subscribe",
                                            n_clicks=0,
                                        ),
                                        dmc.Text(id="notification-feedback", children=""),
                                    ],
                                ),
                            ),
                        ],
                    )
                ],
            ),

            # ── Filters panel ─────────────────────────────────────────────────
            dmc.Paper(
                shadow="sm",
                p="md",
                radius="md",
                style={"marginBottom": 24},
                children=[
                    dmc.Title("Filters", order=4, style={"marginBottom": 12}),
                    dmc.Stack(
                        children=[
                            # Date range picker
                            html.Div([
                                html.Label(
                                    "Date/Time Range:",
                                    style={"fontWeight": "bold", "display": "block", "marginBottom": 5},
                                ),
                                dcc.DatePickerRange(
                                    id="date-range-picker",
                                    start_date=start_date.date(),
                                    end_date=end_date.date(),
                                    display_format="YYYY-MM-DD",
                                    style={"width": "100%"},
                                ),
                            ]),

                            # Location filter
                            dmc.MultiSelect(
                                id="location-dropdown",
                                label="Locations",
                                data=[],
                                value=[],
                                placeholder="Select locations (all if empty)",
                            ),

                            # Sensor filter
                            dmc.MultiSelect(
                                id="sensor-dropdown",
                                label="Sensor IDs",
                                data=[],
                                value=[],
                                placeholder="Select sensors (all if empty)",
                            ),

                            # Treatment filter
                            dmc.MultiSelect(
                                id="treatment-dropdown",
                                label="Treatments",
                                data=[],
                                value=[],
                                placeholder="Select treatments (all if empty)",
                            ),

                            # Temperature view selection
                            dmc.RadioGroup(
                                id="temp-mode-radio",
                                label="Temperature View",
                                value="absolute",
                                children=dmc.Group([
                                    dmc.Radio(label="Absolute Temperature", value="absolute"),
                                    dmc.Radio(
                                        label="Temperature Difference (ΔT from Control)",
                                        value="delta",
                                    ),
                                ]),
                            ),
                        ],
                    ),
                ],
            ),

            # ── Data export panel ─────────────────────────────────────────────
            dmc.Paper(
                shadow="sm",
                p="md",
                radius="md",
                style={"marginBottom": 24},
                children=[
                    dmc.Title("Data Export", order=4, style={"marginBottom": 12}),
                    dmc.Button(
                        "⬇ Download All Data as CSV",
                        id="btn-download-csv",
                        n_clicks=0,
                    ),
                    dcc.Download(id="download-csv"),
                ],
            ),

            # ── Time series plot ──────────────────────────────────────────────
            dmc.Paper(
                shadow="sm",
                p="md",
                radius="md",
                style={"marginBottom": 24},
                children=[
                    dmc.Title("Temperature Over Time", order=4, style={"marginBottom": 12}),
                    dcc.Graph(
                        id="timeseries-plot",
                        config={"displayModeBar": True, "displaylogo": False},
                    ),
                ],
            ),

            # ── Latest status table ───────────────────────────────────────────
            dmc.Paper(
                shadow="sm",
                p="md",
                radius="md",
                style={"marginBottom": 24},
                children=[
                    dmc.Title("Latest Status", order=4, style={"marginBottom": 12}),
                    dash_table.DataTable(
                        id="latest-status-table",
                        columns=[],
                        data=[],
                        style_table={"overflowX": "auto"},
                        style_cell={
                            "textAlign": "left",
                            "padding": "12px",
                            "fontSize": 13,
                            "fontFamily": "Arial, sans-serif",
                        },
                        style_header={
                            "backgroundColor": "#3498db",
                            "color": "white",
                            "fontWeight": "bold",
                            "border": "1px solid #2980b9",
                        },
                        style_data_conditional=[
                            {"if": {"row_index": "odd"}, "backgroundColor": "#f8f9fa"}
                        ],
                        page_size=TABLE_PAGE_SIZE,
                    ),
                ],
            ),

            # ── Network connectivity ──────────────────────────────────────────
            dmc.Paper(
                shadow="sm",
                p="md",
                radius="md",
                style={"marginBottom": 24},
                children=[
                    dmc.Title("Network Connectivity", order=4, style={"marginBottom": 12}),
                    dcc.Graph(
                        id="connectivity-chart",
                        config={"displayModeBar": True, "displaylogo": False},
                    ),
                    dash_table.DataTable(
                        id="gap-stats-table",
                        columns=[],
                        data=[],
                        style_table={"overflowX": "auto", "marginTop": 20},
                        style_cell={
                            "textAlign": "left",
                            "padding": "12px",
                            "fontSize": 13,
                            "fontFamily": "Arial, sans-serif",
                        },
                        style_header={
                            "backgroundColor": "#27ae60",
                            "color": "white",
                            "fontWeight": "bold",
                            "border": "1px solid #229954",
                        },
                        style_data_conditional=[
                            {"if": {"row_index": "odd"}, "backgroundColor": "#f8f9fa"}
                        ],
                        page_size=TABLE_PAGE_SIZE,
                    ),
                ],
            ),
        ],
        style={"backgroundColor": "#f5f6fa", "minHeight": "100vh", "paddingBottom": 40},
    )

    return layout

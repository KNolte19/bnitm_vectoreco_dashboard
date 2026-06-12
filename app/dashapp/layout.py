"""Dash application layout."""
import dash_mantine_components as dmc
from dash import dcc, html, dash_table
from datetime import datetime, timedelta

# Constants
TABLE_PAGE_SIZE = 10


def _felix_tab_content():
    """Build the content panel for Felix's data tab (original dashboard)."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)

    return dmc.Stack(
        gap="md",
        children=[
            # ── Warning notification subscription panel ──────────────────────
            dmc.Accordion(
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

            # ── Filters panel ────────────────────────────────────────────────
            dmc.Paper(
                shadow="sm",
                p="md",
                radius="md",
                children=[
                    dmc.Title("Filters", order=4, style={"marginBottom": 12}),
                    dmc.Stack(
                        children=[
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
                            dmc.MultiSelect(
                                id="location-dropdown",
                                label="Locations",
                                data=[],
                                value=[],
                                placeholder="Select locations (all if empty)",
                            ),
                            dmc.MultiSelect(
                                id="sensor-dropdown",
                                label="Sensor IDs",
                                data=[],
                                value=[],
                                placeholder="Select sensors (all if empty)",
                            ),
                            dmc.MultiSelect(
                                id="treatment-dropdown",
                                label="Treatments",
                                data=[],
                                value=[],
                                placeholder="Select treatments (all if empty)",
                            ),
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

            # ── Data export panel ────────────────────────────────────────────
            dmc.Paper(
                shadow="sm",
                p="md",
                radius="md",
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

            # ── Time series plot ─────────────────────────────────────────────
            dmc.Paper(
                shadow="sm",
                p="md",
                radius="md",
                children=[
                    dmc.Title("Temperature Over Time", order=4, style={"marginBottom": 12}),
                    dcc.Graph(
                        id="timeseries-plot",
                        config={"displayModeBar": True, "displaylogo": False},
                    ),
                ],
            ),

            # ── Latest status table ──────────────────────────────────────────
            dmc.Paper(
                shadow="sm",
                p="md",
                radius="md",
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

            # ── Network connectivity ─────────────────────────────────────────
            dmc.Paper(
                shadow="sm",
                p="md",
                radius="md",
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
    )


def _leif_tab_content():
    """Build the content panel for Leif's sensor data tab (BS and RS)."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)

    common_table_kwargs = dict(
        style_table={"overflowX": "auto"},
        style_cell={
            "textAlign": "left",
            "padding": "10px",
            "fontSize": 13,
            "fontFamily": "Arial, sans-serif",
        },
        style_header={
            "backgroundColor": "#2e7d32",
            "color": "white",
            "fontWeight": "bold",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#f8f9fa"}
        ],
        page_size=TABLE_PAGE_SIZE,
    )

    # ── Shared filters ───────────────────────────────────────────────────────
    filters = dmc.Paper(
        shadow="sm",
        p="md",
        radius="md",
        children=[
            dmc.Title("Filters", order=4, style={"marginBottom": 12}),
            dmc.Stack(
                children=[
                    html.Div([
                        html.Label(
                            "Date/Time Range:",
                            style={"fontWeight": "bold", "display": "block", "marginBottom": 5},
                        ),
                        dcc.DatePickerRange(
                            id="leif-date-range-picker",
                            start_date=start_date.date(),
                            end_date=end_date.date(),
                            display_format="YYYY-MM-DD",
                            style={"width": "100%"},
                        ),
                    ]),
                    dmc.MultiSelect(
                        id="leif-replica-dropdown",
                        label="Replicas",
                        data=[
                            {'label': 'Replica 1', 'value': 1},
                            {'label': 'Replica 2', 'value': 2},
                            {'label': 'Replica 3', 'value': 3},
                        ],
                        value=[],
                        placeholder="Select replicas (all if empty)",
                    ),
                ],
            ),
        ],
    )

    # ── Breeding Site section ────────────────────────────────────────────────
    bs_section = dmc.Stack(
        gap="md",
        children=[
            dmc.Title("🦟 Breeding Sites (BS) – Site 3", order=3, style={"marginTop": 8}),

            dmc.Paper(
                shadow="sm",
                p="md",
                radius="md",
                children=[
                    dmc.Title("Water Temperature", order=4, style={"marginBottom": 8}),
                    dcc.Graph(
                        id="leif-bs-water-temp-plot",
                        config={"displayModeBar": True, "displaylogo": False},
                    ),
                ],
            ),

            dmc.Paper(
                shadow="sm",
                p="md",
                radius="md",
                children=[
                    dmc.Title("Distance to Water Surface", order=4, style={"marginBottom": 8}),
                    dcc.Graph(
                        id="leif-bs-water-level-plot",
                        config={"displayModeBar": True, "displaylogo": False},
                    ),
                ],
            ),

            dmc.Paper(
                shadow="sm",
                p="md",
                radius="md",
                children=[
                    dmc.Title("Latest BS Readings", order=4, style={"marginBottom": 8}),
                    dmc.Group(
                        children=[
                            dmc.Button(
                                "⬇ Download BS Data as CSV",
                                id="leif-btn-download-csv-bs",
                                n_clicks=0,
                                color="green",
                                size="sm",
                            ),
                        ],
                        style={"marginBottom": 10},
                    ),
                    dcc.Download(id="leif-download-csv"),
                    dash_table.DataTable(
                        id="leif-bs-latest-table",
                        columns=[],
                        data=[],
                        **common_table_kwargs,
                    ),
                ],
            ),
        ],
    )

    # ── Resting Site section ─────────────────────────────────────────────────
    rs_section = dmc.Stack(
        gap="md",
        children=[
            dmc.Title("🌿 Resting Sites (RS) – Site 3", order=3, style={"marginTop": 8}),

            dmc.SimpleGrid(
                cols={"base": 1, "md": 2},
                spacing="md",
                children=[
                    dmc.Paper(
                        shadow="sm",
                        p="md",
                        radius="md",
                        children=[
                            dmc.Title("Air Temperature", order=4, style={"marginBottom": 8}),
                            dcc.Graph(
                                id="leif-rs-temperature-plot",
                                config={"displayModeBar": True, "displaylogo": False},
                            ),
                        ],
                    ),
                    dmc.Paper(
                        shadow="sm",
                        p="md",
                        radius="md",
                        children=[
                            dmc.Title("Relative Humidity", order=4, style={"marginBottom": 8}),
                            dcc.Graph(
                                id="leif-rs-humidity-plot",
                                config={"displayModeBar": True, "displaylogo": False},
                            ),
                        ],
                    ),
                    dmc.Paper(
                        shadow="sm",
                        p="md",
                        radius="md",
                        children=[
                            dmc.Title("Air Pressure", order=4, style={"marginBottom": 8}),
                            dcc.Graph(
                                id="leif-rs-pressure-plot",
                                config={"displayModeBar": True, "displaylogo": False},
                            ),
                        ],
                    ),
                    dmc.Paper(
                        shadow="sm",
                        p="md",
                        radius="md",
                        children=[
                            dmc.Title("Light Spectrum", order=4, style={"marginBottom": 8}),
                            dcc.Graph(
                                id="leif-rs-spectrum-plot",
                                config={"displayModeBar": True, "displaylogo": False},
                            ),
                        ],
                    ),
                ],
            ),

            dmc.Paper(
                shadow="sm",
                p="md",
                radius="md",
                children=[
                    dmc.Title("Latest RS Readings", order=4, style={"marginBottom": 8}),
                    dmc.Group(
                        children=[
                            dmc.Button(
                                "⬇ Download RS Data as CSV",
                                id="leif-btn-download-csv-rs",
                                n_clicks=0,
                                color="green",
                                size="sm",
                            ),
                        ],
                        style={"marginBottom": 10},
                    ),
                    dcc.Download(id="leif-download-rs-csv"),
                    dash_table.DataTable(
                        id="leif-rs-latest-table",
                        columns=[],
                        data=[],
                        **common_table_kwargs,
                    ),
                ],
            ),
        ],
    )

    return dmc.Stack(
        gap="md",
        children=[filters, bs_section, rs_section],
    )


def create_layout():
    """Create the Dash application layout with Felix and Leif tabs.

    Returns:
        Dash layout component.
    """
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

            # ── Dataset selector tabs ────────────────────────────────────────
            dmc.Tabs(
                value="felix",
                children=[
                    dmc.TabsList(
                        [
                            dmc.TabsTab("📊 Felix's Data", value="felix"),
                            dmc.TabsTab("🌿 Leif's Data", value="leif"),
                        ],
                        style={"marginBottom": 24},
                    ),

                    dmc.TabsPanel(
                        value="felix",
                        children=_felix_tab_content(),
                    ),

                    dmc.TabsPanel(
                        value="leif",
                        children=_leif_tab_content(),
                    ),
                ],
            ),
        ],
        style={"backgroundColor": "#f5f6fa", "minHeight": "100vh", "paddingBottom": 40},
    )

    return layout

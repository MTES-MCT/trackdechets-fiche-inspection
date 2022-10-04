import plotly.graph_objects as go
import plotly.io as pio

# Override the 'none' template
pio.templates["gouv"] = go.layout.Template(
    layout=dict(
        font=dict(family="Marianne"),
        title=dict(x=0.01, font=dict(size=24, color="black", family="Marianne-Bold")),
        legend=dict(
            xanchor="center", x=0.4, y=-0.1, bgcolor="rgba(0,0,0,0)", orientation="h"
        ),
        paper_bgcolor="white",
        margin=dict(l=40, r=20, t=60, b=40),
        autosize=True,
        colorway=["#2F4077", "#a94645", "#8D533E", "#417DC4"],
        yaxis=dict(tickformat=",2", separatethousands=True, gridcolor="#ddd"),
        xaxis=dict(gridcolor="#ddd"),
    ),
)

# Customize the sequence and size of symbols used in line graphs
symbol_sequence = [
    "circle-dot",
    "square",
    "hexagram",
    "diamond",
    "hourglass",
    "bowtie",
    "star",
]
pio.templates["gouv"].data.scatter = [
    go.Scatter(marker=dict(symbol=s, size=10)) for s in symbol_sequence
]

# Enable my template
pio.templates.default = "gouv"

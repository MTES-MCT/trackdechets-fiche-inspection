import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go

import app.data

# Override the 'none' template
pio.templates["gouv"] = go.layout.Template(
    layout=dict(
        font=dict(family="Marianne"),
        title=dict(
            x=0.01,
            font=dict(
                size=24,
                color="black",
                family="Marianne-Bold"
            )
        ),
        legend=dict(
            xanchor="center",
            x=0.4,
            y=-0.1,
            bgcolor='rgba(0,0,0,0)',
            orientation='h'
        ),
        paper_bgcolor='white',
        margin=dict(l=30, r=20, t=60, b=20),
        autosize=True,
        colorway=['#2F4077', '#a94645', '#8D533E', '#417DC4'],
        yaxis=dict(
            tickformat=',2',
            separatethousands=True,
            gridcolor='#ddd'
        ),
        xaxis=dict(
            gridcolor="#ddd"
        )
    ),
)

# Customize the sequence and size of symbols used in line graphs
symbol_sequence = ['circle-dot', 'square', 'hexagram', 'diamond', 'hourglass', 'bowtie', 'star']
pio.templates["gouv"].data.scatter = [
    go.Scatter(marker=dict(symbol=s, size=10)) for s in symbol_sequence
]

# Enable my template
pio.templates.default = "none+gouv"

bsdd_emis_acceptation_mois = px.bar(
    app.data.df_bsdd_acceptation_mois,
    title="BSDD émis par mois et par acceptation",
    y="id",
    x="mois",
    color="acceptation",
    text="id",
    labels={
        "mois": "",
        "id": "",
    },
).update_traces(textangle=0)

dechets_recus_emis_poids_mois = px.line(
    app.data.bsdd_grouped_poids_mois,
    y="poids",
    x="mois",
    color="origine",
    symbol="origine",
    title="Déchets entrant et sortant, en tonnes",
    labels={"poids": "", "mois": "", "type": ""},
    markers=True,
    text="poids"
).update_traces(textposition="top center")

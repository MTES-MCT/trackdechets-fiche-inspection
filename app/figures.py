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
                size=22,
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
        paper_bgcolor='rgb(238, 238, 238)',
        colorway=['#2F4077', '#a94645', '#8D533E', '#417DC4'],
        yaxis=dict(
            tickformat=',2',
            separatethousands=True,
        )
    ),
)

pio.templates.default = "none+gouv"

bsdd_emis_mois = px.bar(
    app.data.df_bsdd_grouped_nb_mois,
    title="BSDD émis par mois",
    y="id",
    x="mois",
    text="id",
    labels={
        "mois": "",
        "id": "",
    },
)


dechets_recus_emis_mois = px.line(
    app.data.bsdd_grouped_poids_mois,
    y="poids",
    x="mois",
    color="origine",
    title="Déchets entrant et sortant, en tonnes",
    labels={"poids": "", "mois": "", "type": ""},
    markers=True,
    text="poids"
).update_traces(textposition="top center")




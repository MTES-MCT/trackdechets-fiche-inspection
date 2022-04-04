import plotly.express as px

import app.data

dechets_recus_emis_mois = px.line(
    app.data.bsdd_grouped_nb_mois,
    y="id",
    x="mois",
    color="origine",
    title="Déchets entrant et sortant, en tonnes",
    labels={"id": "", "mois": "", "type": ""},
    markers=True,
    text="id"
).update_traces(textposition="top center")

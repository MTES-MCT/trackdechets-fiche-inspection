"""
Data gathering and processing
"""
import pandas as pd
import sqlalchemy
from datetime import datetime as dt
import locale
from dash import Input, Output, html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px

from .time_config import *
from .utils import *
from app.app import dash_app, extra_config

# postgresql://admin:admin@localhost:5432/ibnse
engine = sqlalchemy.create_engine(getenv("DATABASE_URL"))

locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

departements = pd.read_csv(getenv('DEPARTEMENT_CSV'), index_col='DEP')


# ******************************************************
# BSDD
# ******************************************************

@dash_app.callback(
    Output('query-result', 'data'),
    Input('siret', 'value'))
def get_data(value: str) -> str:
    """
    Queries the configured database for the BSDD data for a given company.
    :return: dataframe of bsdds for a given period of time and a given company
    """
    if len(value) == 14:
        df_bsdd_query = pd.read_sql_query(
            'SELECT "id", date_trunc(\'month\', "sentAt") as mois, "emitterCompanyAddress", '
            '"emitterWorkSitePostalCode",'
            '"quantityReceived" as poids, \'émis\' as origine, "wasteAcceptationStatus" as acceptation '
            'FROM "default$default"."Form" '
            f'WHERE "emitterCompanySiret" = \'{value}\' '
            'AND "default$default"."Form"."sentAt" >= date_trunc(\'month\','
            f"CAST((CAST(now() AS timestamp) + (INTERVAL '-{str(time_delta_m)} month')) AS timestamp)) "
            'AND "default$default"."Form"."isDeleted" = FALSE '
            'UNION ALL '
            'SELECT "id", date_trunc(\'month\', "receivedAt") as mois, "emitterCompanyAddress", '
            '"emitterWorkSitePostalCode", '
            '"quantityReceived" as poids, \'reçus\' as origine, '
            '"wasteAcceptationStatus" as acceptation '
            'FROM "default$default"."Form" '
            f'WHERE "recipientCompanySiret" = \'{value}\' '
            'AND "default$default"."Form"."receivedAt" >= date_trunc(\'month\','
            f"CAST((CAST(now() AS timestamp) + (INTERVAL '-{str(time_delta_m)} month')) AS timestamp)) "
            'AND "default$default"."Form"."isDeleted" = FALSE ',
            con=engine,
        )

        return df_bsdd_query.to_json(orient='split', date_format='iso')


@dash_app.callback(
    Input('query-result', 'data'),
    Input('siret', 'value'),
    output=dict(
        bsdd_graphiques_col=Output('bsdd_graphiques_col', 'children'),
        poids_departement_recus=Output('poids_departement_recus_col', 'children'),
    )
)
def get_bsdd_figures(json_data: str, siret: str):
    # Is SIRET 14 char long?
    if len(siret) != 14:
        return {
            "bsdd_graphiques_col": [
                dbc.Col([], width={'size': 4, 'offset': 4})
            ],
            "poids_departement_recus": ""
        }
    df: pd.DataFrame = pd.read_json(json_data, orient='split', convert_dates=['mois'])

    # Are there any BSDD in the dataframe?
    if df.index.size == 0:
        return {
            "bsdd_graphiques_col": [
                dbc.Col([
                    "Pas de bordereaux entrés dans Trackdéchets pour cet établissement sur la période, "
                    "ni comme émetteur, "
                    "ni comme destinataire."
                ], width={'size': 4, 'offset': 4})
            ],
            "poids_departement_recus": ""
        }

    emis = df.query('origine == "émis"')
    recus = df.query('origine == "reçus"')

    #
    # BSDD / acceptation / mois
    #

    acceptation: dict = {
        'ACCEPTED': 'Accepté',
        'REFUSED': 'Refusé',
        'PARTIALLY_REFUSED': 'Part. refusé'
    }

    df_bsdd_acceptation_mois: pd.DataFrame = emis[['id', 'mois', 'acceptation']].copy()
    df_bsdd_acceptation_mois = df_bsdd_acceptation_mois.groupby(by=['mois', 'acceptation'], as_index=False,
                                                                dropna=False). \
        count()
    df_bsdd_acceptation_mois['mois'] = [dt.strftime(date, "%b/%y")
                                        for date in df_bsdd_acceptation_mois['mois']]
    df_bsdd_acceptation_mois['acceptation'] = [acceptation[val] if isinstance(val, str) else "non réceptionné"
                                               for val in df_bsdd_acceptation_mois['acceptation']]
    #
    # BSDD / origine / poids / mois
    #
    bsdd_grouped_poids_mois = df[['poids', 'origine', 'mois']].groupby(by=['mois', 'origine'],
                                                                       as_index=False).sum()
    bsdd_grouped_poids_mois['mois'] = [dt.strftime(date, "%b/%y") for date in bsdd_grouped_poids_mois['mois']]
    bsdd_grouped_poids_mois['poids'] = bsdd_grouped_poids_mois['poids'].apply(round)

    #
    # BSDD / reçus / département
    #

    df_bsdd_origine_poids: pd.DataFrame = recus[['emitterCompanyAddress', 'poids']].copy()
    df_bsdd_origine_poids['departement_origine'] = df_bsdd_origine_poids['emitterCompanyAddress'].str. \
        extract(r"(\d{2})\d{3}")
    df_bsdd_origine_poids = df_bsdd_origine_poids[['departement_origine', 'poids']]. \
        groupby(by='departement_origine', as_index=False).sum()
    df_bsdd_origine_poids['poids'] = df_bsdd_origine_poids['poids'].apply(round)
    df_bsdd_origine_poids.sort_values(by='poids', ascending=True, inplace=True)
    df_bsdd_origine_poids = df_bsdd_origine_poids.tail(10)
    df_bsdd_origine_poids = df_bsdd_origine_poids.merge(departements, left_on='departement_origine',
                                                        right_index=True)
    df_bsdd_origine_poids['LIBELLE'] = df_bsdd_origine_poids['LIBELLE'] + ' (' \
                                       + df_bsdd_origine_poids['poids'].astype(str) + ' t)'

    bsdd_emis_acceptation_mois = px.bar(
        df_bsdd_acceptation_mois,
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
        bsdd_grouped_poids_mois,
        y="poids",
        x="mois",
        color="origine",
        symbol="origine",
        title="Déchets entrant et sortant, en tonnes",
        labels={"poids": "", "mois": "", "type": ""},
        markers=True,
        text="poids"
    ).update_traces(textposition="top center")

    dechets_recus_poids_departement = px.bar(
        df_bsdd_origine_poids,
        title="Origine des déchets dangereux reçus (top 10)",
        y="departement_origine",
        x="poids",
        text="LIBELLE",
        labels={
            "departement_origine": "Département d'origine",
            "poids": "Poids (tonnes)",
        },
        # So that departements are not treated as numbers
    ).update_yaxes(autotypenumbers='strict')

    return {
        "bsdd_graphiques_col": [
            dbc.Col(
                [
                    dcc.Graph(id='mois_quantités', config=extra_config, figure=dechets_recus_emis_poids_mois)
                ], width=6, lg=6),
            dbc.Col(
                [
                    dcc.Graph(id='mois_emis', config=extra_config, figure=bsdd_emis_acceptation_mois)
                ], width=6, lg=6
            )
        ],
        "poids_departement_recus": dcc.Graph(id='poids_departement_recus', config=extra_config,
                                             figure=dechets_recus_poids_departement)
    }


@dash_app.callback(
    Output('bsdd_summary', 'children'),
    Input('query-result', 'data'),
    Input('siret', 'value')
)
def get_bsdd_summary(json_data: str, siret: str) -> list:
    if len(siret) != 14:
        return []

    df: pd.DataFrame = pd.read_json(json_data, orient='split', dtype={'poids': float})

    if df.index.size == 0:
        return []

    emis = df.query('origine == "émis"')
    recus = df.query('origine == "reçus"')
    poids_emis_float = emis["poids"].sum()
    poids_recu_float = recus["poids"].sum()

    bsdd_summary_data = {
        'Poids émis': format_number_str(poids_emis_float) + ' t',
        'Poids reçu': format_number_str(poids_recu_float) + ' t',
        'Stock théorique sur la période' : format_number_str(poids_recu_float - poids_emis_float)+ ' t',
        'BSDD émis': format_number_str(emis.index.size),
        'BSDD reçus': format_number_str(recus.index.size),
    }

    return [
        html.H4('BSD dangereux sur la période'),
        dbc.Table(
            html.Tbody(
                [
                    html.Tr(
                        [html.Td(key), html.Td(el)]
                    ) for key, el in bsdd_summary_data.items()
                ]
            ), className='bsd_summary'
        ),
    ]


# ******************************************************
# Établissmenet, récépissés et agréments
# ******************************************************

@dash_app.callback(
    Input('siret', 'value'),
    output=dict(
        company_details=Output('company_details', 'children'),
        company_name=Output('company_name', 'children')),
)
def get_company_data(siret: str) -> dict:
    # The entered SIRET is not 14 char long
    if len(siret) != 14:
        return {
            'company_details': dbc.Col(
                html.Div([html.Strong("Le numéro SIRET doit comporter 14 chiffres")])
            ),
            'company_name': ""
        }

    df_company_query = pd.read_sql_query(
        'SELECT "Company"."siret", "Company"."name", "Company"."createdAt", "Company"."address",'
        '"Company"."contactPhone", "Company"."companyTypes", "Company"."contactEmail",'
        ' "Company"."website", '
        'installation."codeS3ic" '
        'FROM "default$default"."Company" '
        'LEFT JOIN'
        '"default$default"."Installation" as installation '
        'on "siret" = installation."s3icNumeroSiret" '
        f'WHERE "siret" = \'{siret}\'', con=engine,
    )

    # Dataframe has no record, établissement is not in Trackdéchets
    if df_company_query.index.size == 0:
        return {
            'company_details': dbc.Col([]),
            'company_name': "Établissement non inscrit dans Trackdéchets"
        }

    def make_agreement_list(df: pd.DataFrame) -> list[html.Li]:
        agreement_list = []

        for i, nom, number, department, validityLimit in df.itertuples():
            if number is not None:
                validity = ", valide jusqu'au " + dt.strftime(validityLimit, '%d %b %Y') \
                    if validityLimit is not None else ''
                agreement = html.Li(nom + number + f' (préf. {department})' + validity)
                agreement_list.append(agreement)
        if len(agreement_list) == 0:
            agreement_list = [html.Li('néant')]
        return agreement_list

    etab = df_company_query.iloc[0].to_dict()

    # Make company types human readable
    company_type_mapping = {
        'COLLECTOR': 'Tri Transit Regroupement (TTR)',
        'WASTEPROCESSOR': 'Usine de traitement',
        'WASTE_CENTER': 'Déchetterie',
        'BROKER': 'Courtier',
        'TRADER': 'Négociant',
        'TRANSPORTER': 'Transporteur',
        'ECO_ORGANISM': 'Éco-organisme',
        'PRODUCER': 'Producteur',
        'WASTE_VEHICLES': 'Centre Véhicules Hors d\'Usage'
    }
    etab['companyTypes'] = etab['companyTypes'][1:-1].split(',')
    etab['companyTypes'] = [company_type_mapping[ctype] for ctype in etab['companyTypes']]

    df_agreement_query = pd.read_sql_query(
        'SELECT \'Agré. démolisseur VHU n°\' as "nom", agrement."agrementNumber" as "number", '
        'agrement."department",'
        'CAST(NULL AS timestamp) as "validityLimit" from "default$default"."VhuAgrement" agrement '
        'RIGHT JOIN "default$default"."Company" company '
        'ON agrement."id" = company."vhuAgrementDemolisseurId" '
        f'WHERE company."siret" = \'{siret}\' '
        'union '
        'SELECT \'Agré. broyeur VHU n°\' as "nom", agrement."agrementNumber" as "number", '
        'agrement."department",'
        ' CAST(NULL AS timestamp) as "validityLimit" from "default$default"."VhuAgrement" agrement '
        'RIGHT JOIN "default$default"."Company" company '
        'ON agrement."id" = company."vhuAgrementBroyeurId" '
        f'WHERE company."siret" = \'{siret}\' '
        'union '
        'SELECT \'Récep. transporteur n°\' as "nom", agrement."receiptNumber" as "number", '
        'agrement."department",'
        ' agrement."validityLimit" as "validityLimit" from "default$default"."TransporterReceipt" agrement '
        'RIGHT JOIN "default$default"."Company" company '
        'ON agrement."id" = company."transporterReceiptId"'
        f'WHERE company."siret" = \'{siret}\' '
        'union '
        'SELECT \'Récep. négociant n°\' as "nom", agrement."receiptNumber" as "number", agrement."department",'
        ' agrement."validityLimit" as "validityLimit" from "default$default"."TraderReceipt" agrement '
        'RIGHT JOIN "default$default"."Company" company '
        'ON agrement."id" = company."traderReceiptId" '
        f'WHERE company."siret" = \'{siret}\' '
        'union '
        'SELECT \'Récep. courtier n°\' as "nom", agrement."receiptNumber" as "number", agrement."department",'
        ' agrement."validityLimit" as "validityLimit" from "default$default"."BrokerReceipt" agrement '
        'RIGHT JOIN "default$default"."Company" company '
        'ON agrement."id" = company."brokerReceiptId" '
        f'WHERE company."siret" = \'{siret}\'',
        con=engine)

    # Dataframe has records, return information
    return {
        'company_details': [
            dbc.Col([
                html.P(f'le {dt.strftime(today, "%d %b %Y à %H:%M")}'),
                html.P(["SIRET : " + etab['siret'],
                        html.Br(),
                        "S3IC/GUN : " + (etab['codeS3ic'] or "inconnu")]),
                html.P(etab['address']),
                html.P('Inscrit sur Trackdéchets depuis le '
                       f'{dt.strftime(etab["createdAt"], "%d %b %Y")}'),

                dbc.Row([
                    dbc.Row([
                        dbc.Col(html.H4("Informations déclarées sur Trackdechets"),
                        )
                    ]),
                    dbc.Col([
                        html.P('Activités', className='bold'),
                        html.Ul([html.Li(profil) for profil in etab['companyTypes']]),
                    ]),
                    dbc.Col([
                        html.P('Agréments et récépissés', className='bold'),
                        html.Ul(make_agreement_list(df_agreement_query)),
                    ]),
                ], className='framed'),
                html.P('Données pour la période du ' +
                       dt.strftime(date_n_days_ago, "%d %b %Y")
                       + ' à aujourd\'hui (' + getenv("TIME_PERIOD_M") + ' derniers mois).',
                       className='bold')
            ], width=6
            ),
            dbc.Col(
                [
                    html.P(
                        'Les données pour cet établissement peuvent être consultées sur '
                        'Trackdéchets.'),
                    html.P(
                        'Elles comprennent les bordereaux de suivi de déchets (BSD) '
                        'dématérialisés,'
                        ' mais ne comprennent pas :'),
                    html.Ul([
                        html.Li('les éventuels BSD papiers non dématérialisés'),
                        html.Li('les bons d\'enlèvement (huiles usagées, pneus)'),
                        html.Li('les annexes 1 (petites quantités)')
                    ])
                ], width=6
            )
        ],
        'company_name': etab['name']
    }

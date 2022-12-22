select
    code_s3ic,
    id_nomenclature,
    date_debut_exploitation,
    date_fin_validite,
    volume,
    unite,
    rubrique,
    alinea,
    libelle_court_activite
from
    refined_zone_icpe.icpe_siretise
where siret_clean = '{siret}'
AND en_vigueur
and id_regime in ('E','DC','D','A')
-- Ce trigger est créé afin de palier à une problématique DB.
-- Les champ title_fr, title_en et acronym sont dupliqués entre base_educationgroupyear & education_group_groupyear.
-- Et ce, dans le cadre des formations & mini formations.
-- Dans education_group_groupyear, ces champs sont pertinents uniquement pour les groupements.

-- Afin d éviter une incohérence de ces champs (ceux-ci sont non versionnés) entre les deux tables,
-- ce trigger recopie ceux de la version standard dans toutes les autres versions
-- en cas de modification base_educationgroupyear

CREATE OR REPLACE FUNCTION repercute_educationgroupyear_unversioned_fields_to_groupyears() RETURNS TRIGGER AS
$$
BEGIN
    WITH offer_fields AS (
        SELECT egy.acronym, egy.title, egy.title_english, gy.id as group_id
        FROM public.base_educationgroupyear egy
                 JOIN public.program_management_educationgroupversion egv
                      ON egv.offer_id = egy.id AND egv.offer_id = NEW.id
                 JOIN public.education_group_groupyear gy ON gy.id = egv.root_group_id
    )
    UPDATE public.education_group_groupyear gy
    SET (title_fr, title_en, acronym) = (SELECT title, title_english, acronym FROM offer_fields LIMIT 1)
    WHERE id IN (SELECT group_id FROM offer_fields);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS UPDATED_BASE_EDUCATIONGROUPYEAR ON public.base_educationgroupyear;
CREATE TRIGGER UPDATED_BASE_EDUCATIONGROUPYEAR
    AFTER UPDATE OR INSERT
    ON public.base_educationgroupyear
    FOR EACH ROW
    -- To avoid that the trigger is fired by itself or other trigger
    WHEN (pg_trigger_depth() < 1)
EXECUTE PROCEDURE repercute_educationgroupyear_unversioned_fields_to_groupyears();

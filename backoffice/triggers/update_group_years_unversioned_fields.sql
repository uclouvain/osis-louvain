-- Ce trigger est créé afin de palier à une problématique DB.
-- Les champ title_fr, title_en et acronym sont dupliqués entre base_educationgroupyear & education_group_groupyear.
-- Et ce, dans le cadre des formations & mini formations.
-- Dans education_group_groupyear, ces champs sont pertinents uniquement pour les groupements.

-- Afin d éviter une incohérence de ces champs (ceux-ci sont non versionnés) entre les deux tables,
-- ce trigger recopie ceux de la version standard dans toutes les autres versions
-- en cas de modification education_group_groupyear

CREATE OR REPLACE FUNCTION update_unversioned_fields_of_group_years() RETURNS TRIGGER AS
$$
BEGIN
    -- Check if it is a root group => having a reference into program_management_educationgroupversion
    IF EXISTS(
            SELECT *
            FROM public.program_management_educationgroupversion
            WHERE root_group_id = NEW.id
        ) THEN
        WITH offer_fields AS (
            SELECT egy.acronym, egy.title, egy.title_english, gy.id as group_id
            FROM public.base_educationgroupyear egy
                     JOIN public.program_management_educationgroupversion egv
                          ON egv.offer_id = egy.id AND egv.root_group_id = NEW.id
                     JOIN public.program_management_educationgroupversion other_versions
                          ON other_versions.offer_id = egy.id
                     JOIN public.education_group_groupyear gy ON gy.id = other_versions.root_group_id
        )
        UPDATE public.education_group_groupyear gy
        SET (title_fr, title_en, acronym) = (SELECT title, title_english, acronym FROM offer_fields LIMIT 1)
        WHERE id IN (SELECT group_id FROM offer_fields);
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS UPDATED_EDUCATION_GROUP_GROUPYEAR ON public.education_group_groupyear;
CREATE TRIGGER UPDATED_EDUCATION_GROUP_GROUPYEAR
    AFTER UPDATE OR INSERT
    ON public.education_group_groupyear
    FOR EACH ROW
    -- To avoid that the trigger is fired by itself or other trigger
    WHEN (pg_trigger_depth() < 1)
EXECUTE PROCEDURE update_unversioned_fields_of_group_years();

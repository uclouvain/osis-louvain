from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories
from base.models.learning_unit_year import LearningUnitYear
from cms.models.translated_text import TranslatedText
from education_group.models.group_year import GroupYear
from osis_common.utils.models import get_object_or_none

# Update attributes for generic fk --- Learning Unit Year
to_update = []
luy_cms = TranslatedText.objects.filter(
    entity='learning_unit_year',
    reference_type__isnull=True
)
fk_type = ContentType.objects.get_for_model(LearningUnitYear)
for cms in luy_cms:
    luy = LearningUnitYear.objects.get(id=cms.reference)
    cms.reference_type_id = fk_type.id
    cms.reference_object = luy
    cms.save()
    to_update.append(cms)
# TranslatedText.objects.bulk_update(to_update, ['reference_type_id', 'reference_object'])

# Update attributes for generic fk --- Trainings & Mini trainings
to_update = []
offers_cms = TranslatedText.objects.filter(
    entity='offer_year',
    reference_type__isnull=True,
)
fk_type = ContentType.objects.get_for_model(EducationGroupYear)
for cms in offers_cms:
    egy = get_object_or_none(
        EducationGroupYear,
        id=cms.reference,
        education_group_type__category__in=[
            education_group_categories.MINI_TRAINING, education_group_categories.TRAINING
        ]
    )
    # if old data
    # egy = EducationGroupYear.objects.get(
    #   id=cms.reference,
    #   education_group_type__category__in = [
    #       education_group_categories.MINI_TRAINING, education_group_categories.TRAINING
    #   ]
    # )
    if egy:
        cms.reference_type_id = fk_type.id
        cms.reference_object = egy
        cms.save()
        to_update.append(cms)
# TranslatedText.objects.bulk_update(to_update, ['reference_type_id', 'reference_object'], batch_size=1000)

# Update attributes for generic fk --- Groups
to_update = []
groups_cms = TranslatedText.objects.filter(
    entity='offer_year',
    reference_type__isnull=True
)
fk_type = ContentType.objects.get_for_model(GroupYear)
for cms in groups_cms:
    group = GroupYear.objects.filter(
        # HOW TO GET CORRECT GROUP_YEAR ???
    )
    # If old data
    # group = GroupYear.objects.filter(
    #   educationgroupversion__offer__id=cms.reference
    # )
    cms.reference = group.id
    cms.reference_type_id = fk_type.id
    cms.reference_object = group
    cms.save()
    to_update.append(cms)
# TranslatedText.objects.bulk_update(to_update, ['reference_type_id', 'reference_object'], batch_size=1000)

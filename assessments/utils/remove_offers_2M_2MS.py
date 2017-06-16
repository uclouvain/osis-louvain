#!/usr/bin/env python
def _set_parent_foreign_key_to_null():
    from base.models.offer_year import OfferYear
    for off in list(OfferYear.objects.all()):
        off.parent_id = None
        off.save()


def _remove_2M_2MS_offers():
    from django.db.models import Q
    from base.models.offer_year import OfferYear
    cpt = 0
    for off in OfferYear.objects.filter(Q(acronym__endswith='2MS') | Q(acronym__endswith='2M'))\
                                .exclude(acronym__icontains='/')\
                                .order_by('academic_year__year')\
                                .select_related('academic_year'):
        off.delete()
        cpt += 1
        print('{} ({}) was removed'.format(off.acronym, off.academic_year))
    print("{} OfferYear records were deleted.".format(cpt))


def execute():
    _set_parent_foreign_key_to_null()
    _remove_2M_2MS_offers()


if __name__ == '__main__':
    execute()

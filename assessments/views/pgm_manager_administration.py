##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.contrib.auth.decorators import login_required, user_passes_test
from base import models as mdl
from base.views import layout
from django.http import HttpResponse
from rest_framework import serializers
from rest_framework.renderers import JSONRenderer
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
import json
from base.models.entity_manager import is_entity_manager, has_perm_entity_manager

ALL_OPTION_VALUE = "-"
ALL_OPTION_VALUE_ENTITY = "all_"


@login_required
@user_passes_test(has_perm_entity_manager)
def pgm_manager_administration(request):
    administrator_entities = get_administrator_entities(request.user)
    current_academic_yr = mdl.academic_year.current_academic_year()
    return layout.render(request, "admin/pgm_manager.html", {
        'academic_year': current_academic_yr,
        'administrator_entities_string': _get_administrator_entities_acronym_list(administrator_entities),
        'entities_managed_root': administrator_entities,
        'offer_types': _get_offer_types(),
        'managers': _get_entity_program_managers(administrator_entities, current_academic_yr),
        'init': '1'})


@login_required
def pgm_manager_search(request):
    person_id = get_filter_value(request, 'person')
    person = None
    if person_id:
        person = mdl.person.find_by_id(person_id)
    return pgm_manager_form(None, None, request, person)


def pgm_manager_form(offers_on, error_messages, request, manager_person):
    entity_selected = get_filter_value(request, 'entity')  # if an acronym is selected this value is not none
    entity_root_selected = None                            # if an 'all hierarchy of' is selected this value is not none

    if entity_selected is None:
        entity_root_selected = get_entity_root_selected(request)

    pgm_offer_type = get_filter_value(request, 'offer_type')

    administrator_entities = get_administrator_entities(request.user)

    current_academic_yr = mdl.academic_year.current_academic_year()

    data = {'academic_year': current_academic_yr,
            'person': manager_person,
            'administrator_entities_string': _get_administrator_entities_acronym_list(administrator_entities),
            'entities_managed_root': administrator_entities,
            'entity_selected': entity_selected,
            'entity_root_selected': entity_root_selected,
            'offer_types': _get_offer_types(),
            'pgms': _get_programs(current_academic_yr,
                                  get_entity_list(entity_selected, get_entity_root(entity_root_selected)),
                                  manager_person,
                                  pgm_offer_type),
            'managers': _get_entity_program_managers(administrator_entities, current_academic_yr),
            'offers_on': offers_on,
            'offer_type': pgm_offer_type,
            'add_errors': error_messages}
    return layout.render(request, "admin/pgm_manager.html", data)


def get_entity_root(entity_selected):
    if entity_selected:
        return mdl.structure.find_by_id(entity_selected)
    return None


def get_entity_root_selected(request):
    entity_root_selected = get_filter_value_entity(request, 'entity')
    if entity_root_selected is None:
        entity_root_selected = request.POST.get('entity_root', None)
    return entity_root_selected


def _filter_by_entity_offer_type(academic_yr, entity_list, pgm_offer_type):
    return mdl.offer_year.search_offers(entity_list, academic_yr, pgm_offer_type)


def get_managed_entities(entity_managed_list):
    if entity_managed_list:
        structures = []
        for entity_managed in entity_managed_list:
            children_acronyms = find_values('acronym', json.dumps(entity_managed['root'].serializable_object()))
            structures.extend(mdl.structure.find_by_acronyms(children_acronyms))
        return sorted(structures, key=lambda a_structure: a_structure.acronym)

    return None


def get_entity_list(entity, entity_managed_structure):
    if entity:
        entity_found = mdl.structure.find_by_id(entity)
        if entity_found:
            return [entity_found]
    else:
        children_acronyms = find_values('acronym', json.dumps(entity_managed_structure.serializable_object()))
        return mdl.structure.find_by_acronyms(children_acronyms)

    return None


@login_required
def get_filter_value(request, value_name):
    value = _get_request_value(request, value_name)

    if value == ALL_OPTION_VALUE or value == '' or value.startswith(ALL_OPTION_VALUE_ENTITY):
        return None
    return value


def _filter_by_person(person, entity_list, academic_yr, an_offer_type):
    program_managers = mdl.program_manager.find_by_person_academic_year(person,
                                                                        academic_yr,
                                                                        entity_list,
                                                                        an_offer_type)
    offer_years = []
    for manager in program_managers.distinct('offer_year'):
        offer_years.append(manager.offer_year)
    return offer_years


@login_required
@user_passes_test(is_entity_manager)
def delete_manager(request):
    pgms_to_be_removed = request.GET['pgms']  # offers_id are stock in inputbox in a list format (ex = "id1, id2")
    id_person_to_be_removed = request.GET['person']

    if id_person_to_be_removed:
        manager_person_to_be_removed = mdl.person.find_by_id(id_person_to_be_removed)
        if manager_person_to_be_removed:
            list_pgms_concerned = pgms_to_be_removed.split(",")
            offers = mdl.offer_year.find_by_id_list(list_pgms_concerned)
            remove_program_mgr_from_offers(offers, manager_person_to_be_removed)

    return HttpResponse(status=204)


def remove_program_mgr_from_offers(offers, person_to_be_removed):
    pgm_managers_to_delete = mdl.program_manager.find_by_offer_year_list_person(person_to_be_removed, offers)
    for p in pgm_managers_to_delete:
        mdl.program_manager.delete_by_id(p.id)


@login_required
@user_passes_test(is_entity_manager)
def person_list_search(request):
    fullname = request.GET['fullname']
    employees = None
    if fullname:
        employees = mdl.person.search_employee(fullname)
    serializer = PersonSerializer(employees, many=True)
    return JSONResponse(serializer.data)


@login_required
@user_passes_test(is_entity_manager)
def create_manager(request):

    person_selected = get_filter_selected_person(request)

    person_id = request.POST['person_id']
    pgms_id = request.POST['pgms_id']
    
    list_offer_id = _convert_to_int_list(pgms_id)
    error_messages = ""
    person = mdl.person.find_by_id(person_id)

    offers_on = None
    if person:
        offers_on = mdl.offer_year.find_by_id_list(list_offer_id)
        error_messages = add_program_managers(offers_on, person)

    return pgm_manager_form(offers_on, error_messages, request, person_selected)


def get_administrator_entities(a_user):
    structures = []
    for entity_managed in mdl.entity_manager.find_by_user(a_user):
        children_acronyms = find_values('acronym', json.dumps(entity_managed.structure.serializable_object()))
        structures.append({'root': entity_managed.structure,
                           'structures': mdl.structure.find_by_acronyms(children_acronyms)})
    return structures


def is_already_program_manager(person, offer_yr):
    if mdl.program_manager.find_by_offer_year_person(person, offer_yr):
        return True
    return False


def add_program_managers(offers, person):
    error_messages = []
    for offer_yr in offers:
        if not add_offer_program_manager(offer_yr, person):
            error_messages.append("{0} {1} {2}".format(person, _('is already program manager for'), offer_yr.acronym))
    return error_messages


def add_offer_program_manager(offer_yr, person):
    if offer_yr:
        if is_already_program_manager(person, offer_yr):
            return False
        else:
            add_save_program_manager(offer_yr, person)
            return True


def add_save_program_manager(offer_yr, person):
    pgm_manage = mdl.program_manager.ProgramManager(person=person,
                                                    offer_year=offer_yr)
    pgm_manage.save()


def _convert_to_int_list(pgms_id):
    if pgms_id:
        return list(map(int, pgms_id.split(",")))
    return []

@login_required
def manager_pgm_list(request):
    manager_id = request.GET['manager_id']
    manager = mdl.program_manager.find_by_id(int(manager_id))
    offers = []
    if manager:
        pgm_managers = mdl.program_manager.find_by_person(manager.person)
        for p in pgm_managers:
            if p.offer_year not in offers:
                offers.append(p.offer_year)
    serializer = OfferYearSerializer(offers, many=True)
    return JSONResponse(serializer.data)


class JSONResponse(HttpResponse):
    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', )


class PersonSerializer(serializers.ModelSerializer):
    user = UserSerializer(many=False)

    class Meta:
        model = mdl.person.Person
        fields = ('id', 'last_name', 'first_name', 'email', 'middle_name', 'user')


class OfferYearSerializer(serializers.ModelSerializer):

    class Meta:
        model = mdl.offer_year.OfferYear
        fields = '__all__'


class PgmManager(object):
    # Needed to display the confirmation modal dialog while deleting
    def __init__(self, person_id, person_last_name, person_first_name, programs, offer_year_acronyms_on=None,
                 offer_year_acronyms_off=None):
        self.person_id = person_id
        self.person_last_name = person_last_name
        self.person_first_name = person_first_name
        self.offer_year_acronyms_on = offer_year_acronyms_on  # acronyms of the offers the pgm manager will keep
        self.offer_year_acronyms_off = offer_year_acronyms_off  # acronyms of the offers the pgm manager will be removed from
        self.programs = programs


class PgmManagerSerializer(serializers.Serializer):
    # Needed to display the confirmation modal dialog while deleting
    person_id = serializers.IntegerField()
    person_last_name = serializers.CharField()
    person_first_name = serializers.CharField()
    offer_year_acronyms_on = serializers.ListField(
       child=serializers.CharField()
    )
    offer_year_acronyms_off = serializers.ListField(
       child=serializers.CharField()
    )
    programs = serializers.ListField(
       child=serializers.IntegerField()
    )


@login_required
def update_managers_list(request):
    # Update the manager's list after add/delete/check
    list_id_offers_selected = _convert_to_int_list(request.GET['pgm_ids'])
    program_manager_list = _get_program_manager_list(list_id_offers_selected)
    serializer = PgmManagerSerializer(program_manager_list, read_only=True, many=True)
    return JSONResponse(serializer.data)


def _get_program_manager_list(offer_year_ids, person=None, delete=False):
    program_managers_related = mdl.program_manager.find_by_offer_year_list(offer_year_ids) \
        .select_related('offer_year') \
        .distinct('person__id', 'person__last_name', 'person__first_name')
    if person:
        program_managers_related = program_managers_related.filter(person=person)

    # Get all offer id for all program managers related
    person_related_ids = program_managers_related.values_list('person_id', flat=True)
    offer_years_grouped = _get_all_offer_years_grouped_by_person(person_related_ids)

    list = []
    for program_manager in program_managers_related:
        person = program_manager.person
        all_offer_years_managed = offer_years_grouped.get(person.id, [])
        pgms = [str(offer_year.id) for offer_year in all_offer_years_managed]

        if delete:
            to_delete = [offer_year.acronym for offer_year in all_offer_years_managed if offer_year.id in offer_year_ids]
            to_keep = [offer_year.acronym for offer_year in all_offer_years_managed if offer_year.id not in offer_year_ids]

            pgm = PgmManager(person_id=person.id,
                             person_last_name=person.last_name,
                             person_first_name=person.first_name,
                             programs=pgms,
                             offer_year_acronyms_off=to_delete,
                             offer_year_acronyms_on=to_keep)
        else:
            pgm = PgmManager(person_id=person.id,
                             person_last_name=person.last_name,
                             person_first_name=person.first_name,
                             programs=pgms)
        list.append(pgm)
    return list


def _get_all_offer_years_grouped_by_person(person_ids):
    offer_years = {}
    program_managers = mdl.program_manager.find_by_person_list(person_ids)
    for program_manager in program_managers:
        key = program_manager.person.id
        offer_years.setdefault(key, []).append(program_manager.offer_year)
    return offer_years


def _get_programs(academic_yr, entity_list, manager_person, an_offer_type):
    if manager_person:
        pgms = _filter_by_person(manager_person, entity_list, academic_yr, an_offer_type)
    else:
        pgms = _filter_by_entity_offer_type(academic_yr, entity_list, an_offer_type)
    return pgms


def _get_entity_program_managers(entity, academic_yr):
    entities = get_managed_entities(entity)
    return mdl.program_manager.find_by_management_entity(entities, academic_yr)


def find_values(key_value, json_repr):
    results = []

    def _decode_dict(a_dict):
        try:
            results.append(a_dict[key_value])
        except KeyError:
            pass
        return a_dict

    json.loads(json_repr, object_hook=_decode_dict)  # return value ignored
    return results


def get_filter_selected_person(request):
    person_selected_id = get_filter_value(request, 'person')
    if person_selected_id:
        return mdl.person.find_by_id(int(person_selected_id))
    return None


def _get_offer_types():
    return mdl.offer_type.find_all()


@login_required
def delete_manager_information(request):
    # Update the manager's list after add/delete
    list_id_offers_selected = _convert_to_int_list(request.GET['pgm_ids'])
    a_person = mdl.person.find_by_id(int(request.GET['person_id']))
    program_manager_list = _get_program_manager_list(list_id_offers_selected, person=a_person, delete=True)
    serializer = PgmManagerSerializer(program_manager_list, many=True)
    return JSONResponse(serializer.data)


@login_required
def get_filter_value_entity(request, value_name):
    value = _get_request_value(request, value_name)
    if value != '' and value.startswith(ALL_OPTION_VALUE_ENTITY):
        return value.replace(ALL_OPTION_VALUE_ENTITY, "")

    return None


def _get_request_value(request, value_name):
    if request.method == 'POST':
        value = request.POST.get(value_name, None)
    else:
        value = request.GET.get(value_name, None)
    return value


def _get_administrator_entities_acronym_list(administrator_entities):
    """
    Return a list of acronyms separated by comma.  List of the acronyms administrate by the user
    :param administrator_entities:
    :return:
    """
    return ', '.join(str(entity_manager['root'].acronym) for entity_manager in administrator_entities)


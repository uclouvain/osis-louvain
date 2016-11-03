##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib.auth.decorators import login_required, permission_required
from base import models as mdl
from base.forms.organization import OrganizationForm
from . import layout
from reference import models as mdlref


@login_required
@permission_required('base.can_access_organization', raise_exception=True)
def organizations(request):
    return layout.render(request, "organizations.html", {'types': mdl.organization.ORGANIZATION_TYPE})


@login_required
@permission_required('base.can_access_organization', raise_exception=True)
def organizations_search(request):
    organizations = mdl.organization.search(acronym=request.GET['acronym'],
                                            name=request.GET['name'],
                                            type=request.GET['type_choices'])

    return layout.render(request, "organizations.html", {'organizations': organizations,
                                                         'types': mdl.organization.ORGANIZATION_TYPE})


@login_required
@permission_required('base.can_access_organization', raise_exception=True)
def organization_read(request, organization_id):
    organization = mdl.organization.find_by_id(organization_id)
    structures = mdl.structure.find_by_organization(organization)
    organization_addresses = mdl.organization_address.find_by_organization(organization)
    return layout.render(request, "organization.html", {'organization': organization,
                                                        'organization_addresses': organization_addresses,
                                                        'structures': structures})


@login_required
@permission_required('base.can_access_organization', raise_exception=True)
def organization_new(request):
    return organization_save(request, None)


@login_required
@permission_required('base.can_access_organization', raise_exception=True)
def organization_save(request, organization_id):
    form = OrganizationForm(data=request.POST)
    if organization_id:
        organization = mdl.organization.find_by_id(organization_id)
    else:
        organization = mdl.organization.Organization()

    # get the screen modifications
    if request.POST['acronym']:
        organization.acronym = request.POST['acronym']
    else:
        organization.acronym = None

    if request.POST['name']:
        organization.name = request.POST['name']
    else:
        organization.name = None

    if request.POST['website']:
        organization.website = request.POST['website']
    else:
        organization.website = None

    if request.POST['reference']:
        organization.reference = request.POST['reference']
    else:
        organization.reference = None

    if request.POST['type_choices']:
        organization.type = request.POST['type_choices']
    else:
        organization.type = None

    if form.is_valid():
        organization.save()
        return organization_read(request, organization.id)
    else:

        return layout.render(request, "organization_form.html", {'organization': organization,
                                                                 'form': form})


@login_required
@permission_required('base.can_access_organization', raise_exception=True)
def organization_edit(request, organization_id):
    organization = mdl.organization.find_by_id(organization_id)
    return layout.render(request, "organization_form.html", {'organization': organization,
                                                             'types': mdl.organization.ORGANIZATION_TYPE})


@login_required
@permission_required('base.can_access_organization', raise_exception=True)
def organization_create(request):
    organization = mdl.organization.Organization()
    return layout.render(request, "organization_form.html", {'organization': organization,
                                                             'types': mdl.organization.ORGANIZATION_TYPE})


@login_required
@permission_required('base.can_access_organization', raise_exception=True)
def organization_address_read(request, organization_address_id):
    organization_address = mdl.organization_address.find_by_id(organization_address_id)
    organization_id = organization_address.organization.id
    return layout.render(request, "organization_address.html", {'organization_address': organization_address,
                                                                'organization_id':      organization_id})


@login_required
@permission_required('base.can_access_organization', raise_exception=True)
def organization_address_edit(request, organization_address_id):
    organization_address = mdl.organization_address.find_by_id(organization_address_id)
    organization_id = organization_address.organization.id
    countries = mdlref.country.find_all()
    return layout.render(request, "organization_address_form.html", {'organization_address': organization_address,
                                                                     'organization_id':      organization_id,
                                                                     'countries': countries})


@login_required
@permission_required('base.can_access_organization', raise_exception=True)
def organization_address_save(request, organization_address_id):
    if organization_address_id:
        organization_address = mdl.organization_address.find_by_id(organization_address_id)
    else:
        organization_address = mdl.organization_address.OrganizationAddress()

    if request.POST['organization_address_label']:
        organization_address.label = request.POST['organization_address_label']
    else:
        organization_address.label = None

    if request.POST['organization_address_location']:
        organization_address.location = request.POST['organization_address_location']
    else:
        organization_address.location = None

    if request.POST['organization_address_postal_code']:
        organization_address.postal_code = request.POST['organization_address_postal_code']
    else:
        organization_address.postal_code = None

    if request.POST['organization_address_city']:
        organization_address.city = request.POST['organization_address_city']
    else:
        organization_address.city = None

    if request.POST['country']:
        organization_address.country = mdlref.country.find_by_id(int(request.POST['country']))
    else:
        organization_address.country = None

    if request.POST['organization_id']:
        organization_address.organization = mdl.organization.find_by_id(int(request.POST['organization_id']))

    organization_address.save()

    return organization_read(request, organization_address.organization.id)


@login_required
@permission_required('base.can_access_organization', raise_exception=True)
def organization_address_new(request):
    return organization_address_save(request, None)


@login_required
@permission_required('base.can_access_organization', raise_exception=True)
def organization_address_create(request, organization_id):
    organization_address = mdl.organization_address.OrganizationAddress()
    organization = mdl.organization.find_by_id(organization_id)
    countries = mdlref.country.find_all()
    return layout.render(request, "organization_address_form.html", {'organization_address': organization_address,
                                                                     'organization_id': organization.id,
                                                                     'countries': countries})


@login_required
@permission_required('base.can_access_organization', raise_exception=True)
def organization_address_delete(request, organization_address_id):
    organization_address = mdl.organization_address.find_by_id(organization_address_id)
    organization = organization_address.organization
    organization_address.delete()
    return organization_read(request, organization.id)
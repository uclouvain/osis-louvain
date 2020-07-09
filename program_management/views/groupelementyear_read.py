# ##################################################################################################
#  OSIS stands for Open Student Information System. It's an application                            #
#  designed to manage the core business of higher education institutions,                          #
#  such as universities, faculties, institutes and professional schools.                           #
#  The core business involves the administration of students, teachers,                            #
#  courses, programs and so on.                                                                    #
#                                                                                                  #
#  Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)              #
#                                                                                                  #
#  This program is free software: you can redistribute it and/or modify                            #
#  it under the terms of the GNU General Public License as published by                            #
#  the Free Software Foundation, either version 3 of the License, or                               #
#  (at your option) any later version.                                                             #
#                                                                                                  #
#  This program is distributed in the hope that it will be useful,                                 #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of                                  #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                                   #
#  GNU General Public License for more details.                                                    #
#                                                                                                  #
#  A copy of this license - GNU General Public License - is available                              #
#  at the root of the source code of this program.  If not,                                        #
#  see http://www.gnu.org/licenses/.                                                               #
# ##################################################################################################
import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import translation
from django.views.generic import FormView
from waffle.decorators import waffle_switch

from base.forms.education_group.common import SelectLanguage
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import GroupType, AllTypes
from base.views.mixins import FlagMixin, AjaxTemplateMixin
from osis_common.document.pdf_build import render_pdf
from program_management.business.group_element_years.group_element_year_tree import EducationGroupHierarchy
from program_management.ddd.repositories import load_tree

CURRENT_SIZE_FOR_ANNUAL_COLUMN = 15
MAIN_PART_INIT_SIZE = 650
PADDING = 10
USUAL_NUMBER_OF_BLOCKS = 3


@login_required
@waffle_switch('education_group_year_generate_pdf')
def pdf_content(request, root_id, education_group_year_id, language):
    education_group_year = get_object_or_404(EducationGroupYear, pk=education_group_year_id)
    tree = load_tree.load(education_group_year.id)
    tree = tree.prune(ignore_children_from={GroupType.MINOR_LIST_CHOICE})
    context = {
        'root': education_group_year,
        'tree': tree.root_node.children,
        'language': language,
        'created': datetime.datetime.now(),
        'max_block': tree.get_greater_block_value(),
        'main_part_col_length': get_main_part_col_length(tree.get_greater_block_value()),
    }
    with translation.override(language):
        return render_pdf(
            request,
            context=context,
            filename=education_group_year.acronym,
            template='pdf_content.html',
        )


class ReadEducationGroupTypeView(FlagMixin, AjaxTemplateMixin, FormView):
    flag = "pdf_content"
    template_name = "group_element_year/pdf_content.html"
    form_class = SelectLanguage

    def form_valid(self, form):
        self.kwargs['language'] = form.cleaned_data['language']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(pdf_content, kwargs=self.kwargs)


def get_main_part_col_length(max_block):
    if max_block <= USUAL_NUMBER_OF_BLOCKS:
        return MAIN_PART_INIT_SIZE
    else:
        return MAIN_PART_INIT_SIZE - ((max_block-USUAL_NUMBER_OF_BLOCKS) * (CURRENT_SIZE_FOR_ANNUAL_COLUMN + PADDING))

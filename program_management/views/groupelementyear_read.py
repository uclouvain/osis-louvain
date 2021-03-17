# ##################################################################################################
#  OSIS stands for Open Student Information System. It's an application                            #
#  designed to manage the core business of higher education institutions,                          #
#  such as universities, faculties, institutes and professional schools.                           #
#  The core business involves the administration of students, teachers,                            #
#  courses, programs and so on.                                                                    #
#                                                                                                  #
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)              #
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
from django.urls import reverse
from django.utils import translation
from django.views.generic import FormView
from waffle.decorators import waffle_switch

from backoffice.settings.base import LANGUAGE_CODE_EN
from base.models.enums.education_group_types import GroupType
from base.views.mixins import FlagMixin, AjaxTemplateMixin
from osis_common.document.pdf_build import render_pdf
from program_management.ddd.domain import exception
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.domain.program_tree_version import version_label
from program_management.ddd.domain.service.identity_search import ProgramTreeVersionIdentitySearch, \
    ProgramTreeIdentitySearch
from program_management.ddd.repositories.program_tree import ProgramTreeRepository
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository
from program_management.forms.pdf_select_language import PDFSelectLanguage

CURRENT_SIZE_FOR_ANNUAL_COLUMN = 15
MAIN_PART_INIT_SIZE = 650
PADDING = 10
USUAL_NUMBER_OF_BLOCKS = 3


@login_required
@waffle_switch('education_group_year_generate_pdf')
def pdf_content(request, year, code, language):
    node_id = NodeIdentity(code=code, year=year)

    program_tree_id = ProgramTreeVersionIdentitySearch().get_from_node_identity(node_id)
    try:
        program_tree_version = ProgramTreeVersionRepository.get(program_tree_id)
    except exception.ProgramTreeVersionNotFoundException:
        program_tree_version = None
    if program_tree_version:
        tree = program_tree_version.get_tree()
    else:
        tree = ProgramTreeRepository.get(
            ProgramTreeIdentitySearch().get_from_node_identity(node_id)
        )
    tree = tree.prune(ignore_children_from={GroupType.MINOR_LIST_CHOICE})
    if tree.root_node.is_finality():
        title = tree.root_node.offer_partial_title_en \
            if language == LANGUAGE_CODE_EN and tree.root_node.offer_partial_title_en \
            else tree.root_node.offer_partial_title_fr
    else:
        title = tree.root_node.group_title_en if language == LANGUAGE_CODE_EN and tree.root_node.group_title_en \
            else tree.root_node.group_title_fr

    version_str = version_label(program_tree_version) if program_tree_version else ''
    if version_str:
        version_title = program_tree_version.title_en \
            if language == LANGUAGE_CODE_EN and program_tree_version.title_en else program_tree_version.title_fr
        title = "{} - {}{}".format(title, version_title, version_str)

    context = {
        'root': tree.root_node,
        'tree': tree,
        'language': language,
        'created': datetime.datetime.now(),
        'max_block': tree.get_greater_block_value(),
        'main_part_col_length': get_main_part_col_length(tree.get_greater_block_value()),
        'title': title.strip()
    }

    with translation.override(language):
        return render_pdf(
            request,
            context=context,
            filename="{}{}".format(
                tree.root_node.title,
                version_str if version_str else ''
            ),
            template='pdf_content.html',
        )


class ReadEducationGroupTypeView(FlagMixin, AjaxTemplateMixin, FormView):
    flag = "pdf_content"
    template_name = "group_element_year/pdf_content.html"
    form_class = PDFSelectLanguage

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

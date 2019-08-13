# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from behave import *
from selenium.webdriver.common.by import By
import re

use_step_matcher("parse")


@then(u'Vérifier le contenu des messages de warning affichés.')
def step_impl(context):
    warnings = context.current_page.find_element(By.ID, 'CollapseWarnings').text
    context.test.assertIn('LAGRE2020Q', warnings)
    context.test.assertIsNone(re.search('LAGRE2020[a-pA-Pr-zR-Z]', warnings))

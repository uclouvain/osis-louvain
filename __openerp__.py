# -*- coding: utf-8 -*-
{
    'name': "osis-louvain",

    'summary': """
        OSIS is an application designed to manage the core business of higher education institutions, such as universities, faculties, institutes and professional schools.
    """,

    'description': """
        The core business involves the administration of students, teachers, courses, programs and so on.
    """,

    'author': "Université catholique de Louvain",
    'website': "http://www.uclouvain.be",

    'category': 'Education',
    'version': '15.11.2.0',

    #'depends': ['base','board','website','web'],
    #'depends': ['base','web','website',],
    'depends': ['base',],

    'data': [
        # 'security/ir.model.access.csv',
        # 'views/osis-louvain.xml',
        'templates.xml',
        'views/menu.xml',
        'views/person.xml',
        'views/student.xml',
        'views/tutor.xml',
        'views/offer.xml',
        'views/attribution.xml',
        'views/academic_year.xml',
        'views/learning_unit.xml',
        'views/session_exam.xml',
        'views/structure.xml',
        'views/offer_year.xml',
        'views/offer_enrollment.xml',
        'views/learning_unit_year.xml',
        'views/learning_unit_enrollment.xml',
        'views/exam_enrollment.xml',
        'reports/student.xml',
        'views/student_notes.xml',
        'views/resultWizard.xml',
        #'views/test.xml',
        'views/student_notes_display.xml',
        'reports/learning_unit_enrollment.xml',
        'reports/student_notes.xml',
        'templates.xml',


    ],

    'demo': [
        # 'demo.xml',
    ],
    # 'css': ['static/src/css/mycss.css'],
    # 'js': ['static/src/js/resource.js'],
    # 'qweb': ['static/src/xml/resource.xml'],
}

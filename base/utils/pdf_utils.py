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
from io import BytesIO
from django.http import HttpResponse
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_JUSTIFY, TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from django.utils.translation import ugettext_lazy as _

from base import models as mdl


PAGE_SIZE = A4
MARGIN_SIZE = 20 * mm
COLS_WIDTH = [25*mm,35*mm,30*mm,25*mm,25*mm,27*mm]


def add_header_footer(canvas, doc):
    """
    Add the page number
    """
    styles = getSampleStyleSheet()
    # Save the state of our canvas so we can draw on it
    canvas.saveState()

    # Header
    header_building(canvas, doc, styles)

    # Footer
    footer_building(canvas, doc, styles)

    # Release the canvas
    canvas.restoreState()


def print_notes(request, tutor, academic_year, session_exam, learning_unit_year_id):
    """
    Create a multi-page document
    :param request:
    :param tutor:
    :param academic_year:
    :param session_exam:
    :param learning_unit_year_id:
    """

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="feuillesNotes.pdf"'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer,
                            pagesize=PAGE_SIZE,
                            rightMargin=MARGIN_SIZE,
                            leftMargin=MARGIN_SIZE,
                            topMargin=85,
                            bottomMargin=18)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

    content = []
    is_fac = mdl.program_manager.is_programme_manager(request.user,session_exam.offer_year_calendar.offer_year)
    sessions_list=[]
    if learning_unit_year_id != -1 :
        #par cours
        list_exam_enrollment = mdl.exam_enrollment.find_exam_enrollments_by_session(session_exam)
    else:
        if tutor:
            sessions = mdl.session_exam.find_sessions_by_tutor(tutor, academic_year)
            sessions_list.append(sessions)
        # In case the user is not a tutor we check whether it is member of a faculty.
        elif is_fac:
            program_mgr_list = mdl.program_manager.find_by_user(request.user)
            for program_mgr in program_mgr_list:
                if program_mgr.offer_year:
                    sessions = mdl.session_exam.find_sessions_by_offer(program_mgr.offer_year, academic_year)
                    sessions_list.append(sessions)

        # Calculate the progress of all courses of the tutor.
        list_exam_enrollment = []
        for sessions in sessions_list:
            for session in sessions:
                enrollments = list(mdl.exam_enrollment.find_exam_enrollments_by_session(session))
                if enrollments:
                    list_exam_enrollment = list_exam_enrollment + enrollments

    list_notes_building(session_exam, learning_unit_year_id, academic_year, list_exam_enrollment, styles, is_fac, content)

    doc.build(content, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    # doc.build(content)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


def header_building(canvas, doc, styles):
    a = Image("base"+ settings.STATIC_URL +"img/logo_institution.jpg")

    p = Paragraph('''
                    <para align=center>
                        <font size=16>%s</font>
                    </para>''' % (_('Scores transcript')), styles["BodyText"])

    data_header = [[a, '%s' % _('University Catholic Louvain\nLouvain-la-Neuve\nBelgium'), p], ]

    t_header=Table(data_header, [30*mm, 100*mm,50*mm])

    t_header.setStyle(TableStyle([
                       ]))

    w, h = t_header.wrap(doc.width, doc.topMargin)
    t_header.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h)


def footer_building(canvas, doc, styles):
    pageinfo = _('Scores sheet')
    footer = Paragraph(''' <para align=right>Page %d - %s </para>''' % (doc.page, pageinfo), styles['Normal'])
    w, h = footer.wrap(doc.width, doc.bottomMargin)
    footer.drawOn(canvas, doc.leftMargin, h)


def list_notes_building(session_exam, learning_unit_year_id, academic_year, list_exam_enrollment, styles,
                        is_fac, content):

    content.append(Paragraph('''
                            <para spaceb=5>
                                &nbsp;
                            </para>
                            ''' , ParagraphStyle('normal')))
    data = headers_table(styles)

    old_pgm = None
    current_learning_unit_year= None
    cpt = 1
    for rec_exam_enrollment in list_exam_enrollment:
        if (int(rec_exam_enrollment.learning_unit_enrollment.learning_unit_year.id) == int(learning_unit_year_id)) \
                or int(learning_unit_year_id) == -1:
            student = rec_exam_enrollment.learning_unit_enrollment.student
            o = rec_exam_enrollment.learning_unit_enrollment.offer
            if old_pgm is None:
                old_pgm = o
                current_learning_unit_year = rec_exam_enrollment.learning_unit_enrollment.learning_unit_year
            if o != old_pgm:
                #Autre programme - 1. mettre les critères
                main_data(academic_year, session_exam, styles, current_learning_unit_year,old_pgm, content)
                #Autre programme - 2. il faut écrire le tableau

                t=Table(data, COLS_WIDTH, repeatRows=1)
                t.setStyle(TableStyle([
                                   ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                                   ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                                   ('VALIGN',(0,0), (-1,-1), 'TOP')
                                   ]))

                content.append(t)
                #Autre programme - 3. Imprimer légende
                end_page_infos_building(content)
                legend_building(current_learning_unit_year, is_fac, content)
                #Autre programme - 4. il faut faire un saut de page
                content.append(PageBreak())
                data = headers_table(styles)
                old_pgm =o
                current_learning_unit_year = rec_exam_enrollment.learning_unit_enrollment.learning_unit_year

            person = mdl.person.find_by_id(student.person.id)
            score = None
            if not (rec_exam_enrollment.score_final is None):
                if rec_exam_enrollment.session_exam.learning_unit_year.decimal_scores :
                    score = "{0:.2f}".format(rec_exam_enrollment.score_final)
                else:
                    score = "{0:.0f}".format(rec_exam_enrollment.score_final)
            justification = ""
            if rec_exam_enrollment.justification_final:
                justification = dict(mdl.exam_enrollment.JUSTIFICATION_TYPES)[rec_exam_enrollment.justification_final]
            data.append([student.registration_id,
                         person.last_name,
                         person.first_name,
                         score,
                         justification,
                         session_exam.offer_year_calendar.end_date.strftime('%d/%m/%Y')])
        cpt = cpt + 1

    if not old_pgm is None:
        main_data(academic_year, session_exam, styles, current_learning_unit_year, old_pgm, content)
        t = Table(data,COLS_WIDTH)
        t.setStyle(TableStyle([('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                               ('BOX', (0, 0), (-1,-1), 0.25, colors.black),
                               ('VALIGN', (0, 0), (-1, -1), 'TOP')]))

        content.append(t)
        end_page_infos_building(content)
        legend_building(current_learning_unit_year, is_fac, content)


def legend_building(learning_unit_year, is_fac, content):

    p = ParagraphStyle('legend')
    p.textColor = 'grey'
    p.borderColor = 'grey'
    p.borderWidth = 1
    p.alignment = TA_CENTER
    p.fontSize =8
    p.borderPadding = 5
    content.append(Paragraph('''
                        <para spaceb=5>
                            &nbsp;
                        </para>
                        ''' , ParagraphStyle('normal')))
    legend_text = "%s : %s" % (_('Other score legend'), mdl.exam_enrollment.justification_label_authorized(is_fac))
    if not learning_unit_year.decimal_scores:
        legend_text += "<br/><font color=red>%s</font>" % _('UnAuthorized decimal for this activity')

    content.append(Paragraph('''
                            <para>
                                %s
                            </para>
                            ''' % legend_text, p))


def headers_table(styles):
    data = []
    data.append([Paragraph('''%s''' % _('Registration number'), styles['BodyText']),
                 Paragraph('''%s''' % _('Last name'), styles['BodyText']),
                 Paragraph('''%s''' % _('First name'), styles['BodyText']),
                 Paragraph('''%s''' % _('Numbered score'), styles['BodyText']),
                 Paragraph('''%s''' % _('Other score'), styles['BodyText']),
                 Paragraph('''%s''' % _('End date'), styles['BodyText'])])
    return data


def main_data(academic_year, session_exam, styles, learning_unit_year, pgm, content):
    p_structure = ParagraphStyle('entete_structure')
    p_structure.alignment = TA_LEFT
    p_structure.fontSize = 10

    p = ParagraphStyle('entete_droite')
    p.alignment = TA_RIGHT
    p.fontSize = 10

    content.append(Paragraph('''
                            <para spaceb=5>
                                &nbsp;
                            </para>
                            ''' , ParagraphStyle('normal')))
    content.append(Paragraph('%s : %s' % (_('Academic year'), str(academic_year)), p))
    content.append(Paragraph('Session : %d' % session_exam.number_session, p))
    content.append(Paragraph('''
                            <para spaceb=10>
                                &nbsp;
                            </para>
                            ''',  ParagraphStyle('normal')))

    if pgm.structure is not None:
        content.append(Paragraph('%s' % pgm.structure, p_structure))
        content.append(Paragraph('''
                                <para spaceb=5>
                                    &nbsp;
                                </para>
                                ''',  ParagraphStyle('normal')))

    content.append(Paragraph("<strong>%s : %s</strong>" % (learning_unit_year.acronym,learning_unit_year.title)
                              , styles["Normal"]) )
    content.append(Paragraph('''
                            <para spaceb=5>
                                &nbsp;
                            </para>
                            ''',  ParagraphStyle('normal')))

    tutor = None
    if tutor is None:
        p_tutor = Paragraph(''' ''', styles["Normal"])
    else:
        p_tutor = Paragraph('''<b>%s %s</b>''' % (tutor.person.last_name, tutor.person.first_name), styles["Normal"])

    data_tutor = [[p_tutor],
                  [''],
                  [''],
                  ['']]
    table_tutor=Table(data_tutor)
    p_pgm = Paragraph('''<b>%s : %s</b>''' % (_('Program'), pgm.acronym), styles["Normal"])
    data_pgm= [[p_pgm],
               [_('Deliberation date') + ' : '],
               [_('Chair of the exam board') + ' : '],
               [_('Exam board secretary') + ' : '],
              ]
    table_pgm=Table(data_pgm)
    table_pgm.setStyle(TableStyle([
    ('LEFTPADDING', (0,0), (-1,-1), 0),
                         ('RIGHTPADDING', (0,0), (-1,-1), 0),
                         ('VALIGN', (0,0), (-1,-1), 'TOP')
                       ]))
    data_header = [[table_pgm,table_tutor]]

    tt = Table(data_header, colWidths='*')
    tt.setStyle(TableStyle([('LEFTPADDING', (0,0), (-1,-1), 0),
                            ('RIGHTPADDING', (0,0), (-1,-1), 0),
                            ('VALIGN', (0,0), (-1,-1), 'TOP')
                           ]))
    content.append(tt)
    content.append(Spacer(1, 12))


def end_page_infos_building(content):
    content.append(Paragraph('''
                            <para spaceb=5>
                                &nbsp;
                            </para>
                            ''', ParagraphStyle('normal')))
    p = ParagraphStyle('info')
    p.fontSize = 10
    p.alignment = TA_LEFT
    content.append(Paragraph("Please return this document to the administrative office of the program administrator"
                             , p))
    content.append(Paragraph('''
                            <para spaceb=10>
                                &nbsp;
                            </para>
                            ''', ParagraphStyle('normal')))
    p_signature = ParagraphStyle('info')
    p_signature.fontSize = 10
    p_signature.leftIndent = 330
    paragraph_signature = Paragraph('''
                    <font size=10>%s ....................................</font>
                    <br/>
                    <font size=10>%s ..../..../........</font>
                    <br/>
                    <font size=10>%s</font>
                   ''' % (_('Done at'), _('The'), _('Signature')), p_signature)
    content.append(paragraph_signature)

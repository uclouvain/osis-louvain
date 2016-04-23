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


def print_notes(user, academic_year, learning_unit_id, is_programme_manager, sessions_list):
    """
    Create a multi-page document
    :param user: The user who's asking for printing the notes sheet
    :param academic_year: An object AcademicYear
    :param learning_unit_id: The id of the learning unit (from which to create the PDF notes sheet)
    :param is_programme_manager : True only if it is a program_manager.
    :param sessions_list: List of obejcts from the model SessionExam.
    """
    filename = "%s.pdf" % _('scores_sheet')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename

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

    list_exam_enrollment = []
    for sessions in sessions_list:
        for session in sessions:
            enrollments = list(mdl.exam_enrollment.find_exam_enrollments_by_session(session))
            if enrollments:
                list_exam_enrollment = list_exam_enrollment + enrollments

    list_notes_building(learning_unit_id, academic_year, list_exam_enrollment, styles, is_programme_manager, content, user)

    doc.build(content, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


def header_building(canvas, doc, styles):
    a = Image(settings.LOGO_INSTITUTION_URL, width=15*mm, height=20*mm)

    p = Paragraph('''
                    <para align=center>
                        <font size=16>%s</font>
                    </para>''' % (_('scores_transcript')), styles["BodyText"])

    data_header = [[a, '%s' % _('ucl_denom_location'), p], ]

    t_header=Table(data_header, [30*mm, 100*mm, 50*mm])

    t_header.setStyle(TableStyle([]))

    w, h = t_header.wrap(doc.width, doc.topMargin)
    t_header.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h)


def footer_building(canvas, doc, styles):
    pageinfo = _('scores_sheet')
    footer = Paragraph(''' <para align=right>Page %d - %s </para>''' % (doc.page, pageinfo), styles['Normal'])
    w, h = footer.wrap(doc.width, doc.bottomMargin)
    footer.drawOn(canvas, doc.leftMargin, h)


def list_notes_building(learning_unit_id, academic_year, list_exam_enrollment, styles, is_programme_manager, content, user):

    content.append(Paragraph('''
                            <para spaceb=5>
                                &nbsp;
                            </para>
                            ''', ParagraphStyle('normal')))
    data = headers_table()

    old_offer_programme = None
    current_learning_unit_year = None
    cpt = 1
    for rec_exam_enrollment in list_exam_enrollment:
        if (int(rec_exam_enrollment.learning_unit_enrollment.learning_unit_year.id) == int(learning_unit_id)) \
                or int(learning_unit_id) == -1:

            student = rec_exam_enrollment.learning_unit_enrollment.student
            offer_programme = rec_exam_enrollment.learning_unit_enrollment.offer
            if old_offer_programme is None:
                old_offer_programme = offer_programme
                current_learning_unit_year = rec_exam_enrollment.learning_unit_enrollment.learning_unit_year

            if offer_programme != old_offer_programme:
                # Other programme - 1. manage criteria
                main_data(academic_year,
                          rec_exam_enrollment.session_exam,
                          styles,
                          current_learning_unit_year,
                          old_offer_programme, content, user, is_programme_manager)
                # Other programme - 2. write table

                t = Table(data, COLS_WIDTH, repeatRows=1)
                t.setStyle(TableStyle([
                                   ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                                   ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                                   ('VALIGN',(0,0), (-1,-1), 'TOP'),
                                   ('BACKGROUND', (0, 0), (-1, 0), colors.grey)]))

                content.append(t)
                # Other programme - 3. Write legend
                end_page_infos_building(content)
                legend_building(current_learning_unit_year, is_programme_manager, content)
                # Other programme - 4. page break
                content.append(PageBreak())
                data = headers_table()
                old_offer_programme = offer_programme
                current_learning_unit_year = rec_exam_enrollment.learning_unit_enrollment.learning_unit_year

            person = mdl.person.find_by_id(student.person.id)
            score = None
            if not (rec_exam_enrollment.score_final is None):
                if rec_exam_enrollment.session_exam.learning_unit_year.decimal_scores:
                    score = "{0:.2f}".format(rec_exam_enrollment.score_final)
                else:
                    score = "{0:.0f}".format(rec_exam_enrollment.score_final)
            justification = ""
            if rec_exam_enrollment.justification_final:
                justification = dict(mdl.exam_enrollment.JUSTIFICATION_TYPES)[rec_exam_enrollment.justification_final]
            end_date = ""
            if rec_exam_enrollment.session_exam.offer_year_calendar.end_date:
                end_date = rec_exam_enrollment.session_exam.offer_year_calendar.end_date.strftime('%d/%m/%Y')
            sc = ""
            if score:
                sc = "%s" % score
            data.append([student.registration_id,
                         Paragraph(person.last_name, styles['Normal']),
                         Paragraph(person.first_name, styles['Normal']),
                         sc,
                         justification,
                         end_date])
        cpt += 1

    if not old_offer_programme is None:
        main_data(academic_year, rec_exam_enrollment.session_exam, styles, current_learning_unit_year, old_offer_programme, content, user, is_programme_manager)
        t = Table(data,COLS_WIDTH)
        t.setStyle(TableStyle([('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                               ('BOX', (0, 0), (-1,-1), 0.25, colors.black),
                               ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                               ('BACKGROUND', (0, 0), (-1, 0), colors.grey)]))

        content.append(t)
        end_page_infos_building(content)
        legend_building(current_learning_unit_year, is_programme_manager, content)


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
    legend_text = "%s : %s" % (_('other_score_legend'), mdl.exam_enrollment.justification_label_authorized(is_fac))
    if not learning_unit_year.decimal_scores:
        legend_text += "<br/><font color=red>%s</font>" % _('unauthorized_decimal_for_this_activity')

    content.append(Paragraph('''
                            <para>
                                %s
                            </para>
                            ''' % legend_text, p))


def headers_table():
    data = [['''%s''' % _('registration_number'),
             '''%s''' % _('lastname'),
             '''%s''' % _('firstname'),
             '''%s''' % _('numbered_score'),
             '''%s''' % _('other_score'),
             '''%s''' % _('end_date')]]
    return data


def main_data(academic_year, session_exam, styles, learning_unit_year, offer, content, user, is_programme_manager):
    faculty_paragraph_style = ParagraphStyle('structure_header')
    faculty_paragraph_style.alignment = TA_LEFT
    faculty_paragraph_style.fontSize = 10

    p = ParagraphStyle('right_page_header')
    p.alignment = TA_RIGHT
    p.fontSize = 10

    content.append(Paragraph('''
                            <para spaceb=5>
                                &nbsp;
                            </para>
                            ''' , ParagraphStyle('normal')))
    content.append(Paragraph('%s : %s' % (_('academic_year'), str(academic_year)), p))
    content.append(Paragraph('Session : %d' % session_exam.number_session, p))
    content.append(Paragraph('''
                            <para spaceb=10>
                                &nbsp;
                            </para>
                            ''',  ParagraphStyle('normal')))

    if offer.structure is not None:
        structure_display = offer.structure
        faculty = mdl.structure.find_faculty(offer.structure)
        if faculty:
            structure_display = faculty

        structure_address = mdl.structure_address.find_structure_address(structure_display)

        content.append(Paragraph('%s' % structure_display, faculty_paragraph_style))

        if structure_address:
            if structure_address.location:
                content.append(Paragraph('%s' % structure_address.location, faculty_paragraph_style))
            if structure_address.postal_code and structure_address.city:
                content.append(Paragraph('%s %s' % (structure_address.postal_code, structure_address.city),
                                         faculty_paragraph_style))
            phone_fax_data = ""
            if structure_address.phone:
                phone_fax_data += _('phone') + " : " + structure_address.phone
            if structure_address.fax:
                if structure_address.phone:
                    phone_fax_data += " - "
                phone_fax_data += _('fax') + " : " + structure_address.fax
            if len(phone_fax_data) > 0:
                content.append(Paragraph('%s' % phone_fax_data,
                                         faculty_paragraph_style))
    content.append(Paragraph('''
                    <para spaceb=5>
                        &nbsp;
                    </para>
                    ''',  ParagraphStyle('normal')))

    learning_unit_paragraph = Paragraph("<strong>%s : %s</strong>" % (learning_unit_year.acronym,
                                                                      learning_unit_year.title), styles["Normal"])

    if mdl.program_manager.is_programme_manager(user, offer):
        tutor = mdl.tutor.find_responsible(learning_unit_year.learning_unit)
    else:
        tutor = mdl.tutor.find_by_user(user)
    if tutor is None:
        tutor = mdl.tutor.find_responsible(learning_unit_year.learning_unit)

    tutor_location = ""
    tutor_city_data = ""

    if tutor:
        p_tutor = Paragraph('''<b>%s %s</b>''' % (tutor.person.last_name, tutor.person.first_name), styles["Normal"])
        tutor_address = mdl.person_address.find_by_person_label(tutor.person, 'PROFESSIONAL')
        if tutor_address:
            tutor_location = Paragraph('''<b>%s</b>''' % tutor_address.location, styles["Normal"])
            if tutor_address.postal_code or tutor_address.city:
                tutor_city_data = Paragraph('''<b>%s %s</b>''' % (tutor_address.postal_code, tutor_address.city),
                                            styles["Normal"])
    else:
        p_tutor = Paragraph(''' ''', styles["Normal"])

    data_tutor = [[p_tutor],
                  [tutor_location],
                  [tutor_city_data]]
    table_tutor = Table(data_tutor)
    p_pgm = Paragraph('''<b>%s : %s</b>''' % (_('program'), offer.acronym), styles["Normal"])
    data_pgm = [[learning_unit_paragraph],
                [p_pgm]
              ]
    table_pgm = Table(data_pgm)
    table_pgm.setStyle(TableStyle([
                                ('LEFTPADDING', (0,0), (-1,-1), 0),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                                ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))

    data_header = [[table_pgm, table_tutor]]

    data_session = [
               [_('deliberation_date') + ' : '],
              ]
    table_session = Table(data_session, colWidths='*')
    table_session.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0)]))

    tt = Table(data_header, colWidths='*')
    tt.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP')
                           ]))
    content.append(tt)
    content.append(table_session)
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
    content.append(Paragraph(_("return_doc_to_administrator")
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
                   ''' % (_('done_at'), _('the'), _('signature')), p_signature)
    content.append(paragraph_signature)

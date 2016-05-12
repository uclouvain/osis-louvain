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
COLS_WIDTH = [25*mm,45*mm,45*mm,25*mm,25*mm]
STUDENTS_PER_PAGE=24


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


def print_notes(academic_year, learning_unit_id, list_exam_enrollment):
    """
    Create a multi-page document
    :param academic_year: An object AcademicYear
    :param learning_unit_id: The id of the learning unit (from which to create the PDF notes sheet)
    :param list_exam_enrollment: List of examEnrollments to print on the PDF.
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

    list_notes_building(learning_unit_id, academic_year, list_exam_enrollment, styles, content)

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


def list_notes_building(learning_unit_id, academic_year, list_exam_enrollment, styles, content):

    content.append(Paragraph('''
                            <para spaceb=5>
                                &nbsp;
                            </para>
                            ''', ParagraphStyle('normal')))
    data = headers_table()

    old_offer_programme = None
    # current_learning_unit_year = None
    students_printed = 0
    for rec_exam_enrollment in list_exam_enrollment:
        offer_programme = rec_exam_enrollment.learning_unit_enrollment.offer
        current_learning_unit_year = rec_exam_enrollment.learning_unit_enrollment.learning_unit_year
        if not old_offer_programme:
            # Case it is the very first sheet
            # data = headers_table()
            t = Table(data, COLS_WIDTH, repeatRows=1)
            t.setStyle(TableStyle([
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey)]))

            content.append(t)
            old_offer_programme = offer_programme
            main_data(academic_year,
                      rec_exam_enrollment.session_exam,
                      styles,
                      current_learning_unit_year,
                      offer_programme, content)

        # if not learning_unit_year_id or \
        #    (int(rec_exam_enrollment.learning_unit_enrollment.learning_unit_year.id) == int(learning_unit_year_id)):
        # data = headers_table()

        student = rec_exam_enrollment.learning_unit_enrollment.student

        # if old_offer_programme is None:
        #     old_offer_programme = offer_programme
        #     current_learning_unit_year = rec_exam_enrollment.learning_unit_enrollment.learning_unit_year

        # if offer_programme != old_offer_programme or students_printed == STUDENTS_PER_PAGE:
        #     students_printed = 0
        # Other programme - 1. manage criteria
        person = mdl.person.find_by_id(student.person.id)
        score = None
        if not (rec_exam_enrollment.score_final is None):
            if rec_exam_enrollment.session_exam.learning_unit_year.decimal_scores:
                score = "{0:.2f}".format(rec_exam_enrollment.score_final)
            else:
                score = "{0:.0f}".format(rec_exam_enrollment.score_final)
        justification = ""
        if rec_exam_enrollment.justification_final:
            justification = mdl.exam_enrollment.get_letter_justication_type(
                rec_exam_enrollment.justification_final)
        sc = ""
        if score:
            sc = "%s" % score
        data.append([student.registration_id,
                     Paragraph(person.last_name, styles['Normal']),
                     Paragraph(person.first_name, styles['Normal']),
                     sc,
                     Paragraph(justification, styles['Normal'])])

        # t = Table(data, COLS_WIDTH, repeatRows=1)
        # t.setStyle(TableStyle([
        #                    ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
        #                    ('BOX', (0,0), (-1,-1), 0.25, colors.black),
        #                    ('VALIGN',(0,0), (-1,-1), 'TOP'),
        #                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey)]))
        #
        # content.append(t)
            # Other programme - 3. Write legend
            # end_date = ""
            # if rec_exam_enrollment.session_exam.offer_year_calendar.end_date:
            #     end_date = rec_exam_enrollment.session_exam.offer_year_calendar.end_date.strftime('%d/%m/%Y')
            # end_page_infos_building(content, end_date)
            # legend_building(current_learning_unit_year, content)
                # Other programme - 4. page break
        if offer_programme != old_offer_programme or students_printed == STUDENTS_PER_PAGE:
            t = Table(data, COLS_WIDTH, repeatRows=1)
            t.setStyle(TableStyle([
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey)]))
            content.append(t)

            # Write Legend
            end_date = ""
            if rec_exam_enrollment.session_exam.offer_year_calendar.end_date:
                end_date = rec_exam_enrollment.session_exam.offer_year_calendar.end_date.strftime('%d/%m/%Y')
            end_page_infos_building(content, end_date)
            legend_building(current_learning_unit_year, content)

            # New Page
            content.append(PageBreak())

            # New table with headers (noma, firstname, lastname...)
            data = headers_table()

            # Write header
            main_data(academic_year,
                      rec_exam_enrollment.session_exam,
                      styles,
                      current_learning_unit_year,
                      offer_programme, content)
            old_offer_programme = offer_programme
            students_printed = 0
                # data = headers_table()
                # old_offer_programme = offer_programme
                # current_learning_unit_year = rec_exam_enrollment.learning_unit_enrollment.learning_unit_year
        students_printed += 1
            # if old_offer_programme is None:
            #     old_offer_programme = offer_programme
            #     current_learning_unit_year = rec_exam_enrollment.learning_unit_enrollment.learning_unit_year

            # person = mdl.person.find_by_id(student.person.id)
            # score = None
            # if not (rec_exam_enrollment.score_final is None):
            #     if rec_exam_enrollment.session_exam.learning_unit_year.decimal_scores:
            #         score = "{0:.2f}".format(rec_exam_enrollment.score_final)
            #     else:
            #         score = "{0:.0f}".format(rec_exam_enrollment.score_final)
            # justification = ""
            # if rec_exam_enrollment.justification_final:
            #     justification = mdl.exam_enrollment.get_letter_justication_type(rec_exam_enrollment.justification_final)
            # sc = ""
            # if score:
            #     sc = "%s" % score
            # data.append([student.registration_id,
            #              Paragraph(person.last_name, styles['Normal']),
            #              Paragraph(person.first_name, styles['Normal']),
            #              sc,
            #              Paragraph(justification, styles['Normal'])])

    # if old_offer_programme:
    #     main_data(academic_year, rec_exam_enrollment.session_exam, styles, current_learning_unit_year, old_offer_programme, content)
    #     t = Table(data,COLS_WIDTH)
    #     t.setStyle(TableStyle([('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
    #                            ('BOX', (0, 0), (-1,-1), 0.25, colors.black),
    #                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    #                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey)]))
    #
    #     content.append(t)
    #     end_date = ""
    #     if rec_exam_enrollment.session_exam.offer_year_calendar.end_date:
    #         end_date = rec_exam_enrollment.session_exam.offer_year_calendar.end_date.strftime('%d/%m/%Y')
    #     end_page_infos_building(content, end_date)
    #     legend_building(current_learning_unit_year, content)


def legend_building(learning_unit_year, content):
    p = ParagraphStyle('legend')
    p.textColor = 'grey'
    p.borderColor = 'grey'
    p.borderWidth = 1
    p.alignment = TA_CENTER
    p.fontSize = 8
    p.borderPadding = 5
    content.append(Paragraph('''
                        <para spaceb=5>
                            &nbsp;
                        </para>
                        ''' , ParagraphStyle('normal')))
    legend_text = _('justification_legend') % mdl.exam_enrollment.justification_label_authorized()
    legend_text += "<br/>%s" % (str(_('score_legend') % mdl.exam_enrollment.score_label_authorized()))
    if not learning_unit_year.decimal_scores:
        legend_text += "<br/><font color=red>%s</font>" % _('unauthorized_decimal_for_this_activity')

    legend_text += '''<br/> %s : <a href="%s"><font color=blue><u>%s</u></font></a>''' \
                   % (_("in_accordance_to_regulation"), _("link_to_RGEE"), _("link_to_RGEE"))
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
             '''%s''' % _('justification')]]
    return data


def get_data_coordinator(learning_unit_year, styles):
    coordinator = mdl.tutor.find_responsible(learning_unit_year.learning_unit)
    p_coord_location = Paragraph('''''', styles["Normal"])
    p_coord_address = Paragraph('''''', styles["Normal"])
    p_responsible = Paragraph('<b>%s :</b>' % _('learning_unit_responsible'), styles["Normal"])
    if coordinator:
        p_coord_name = Paragraph(
            '%s %s' % (coordinator.person.last_name, coordinator.person.first_name),
            styles["Normal"])
        coordinator_address = mdl.person_address.find_by_person_label(coordinator.person, 'PROFESSIONAL')
        if coordinator_address:
            p_coord_location = Paragraph('''%s''' % coordinator_address.location, styles["Normal"])
            if coordinator_address.postal_code or coordinator_address.city:
                p_coord_address = Paragraph(
                    '''%s %s''' % (coordinator_address.postal_code, coordinator_address.city),
                    styles["Normal"])
    else:
        p_coord_name = Paragraph('%s' % _('none'), styles["Normal"])

    return [[p_responsible], [p_coord_name], [p_coord_location], [p_coord_address]]


def main_data(academic_year, session_exam, styles, learning_unit_year, offer, content):
    # We add first a blank line
    content.append(Paragraph('''
        <para spaceb=10>
            &nbsp;
        </para>
        ''', ParagraphStyle('normal')))

    text_left_style = ParagraphStyle('structure_header')
    text_left_style.alignment = TA_LEFT
    text_left_style.fontSize = 10
    p_struct_name = Paragraph('''''', styles["Normal"])
    p_struct_location = Paragraph('''''', styles["Normal"])
    p_struct_address = Paragraph('''''', styles["Normal"])
    p_phone_fax_data = Paragraph('''''', styles["Normal"])
    if offer.structure:
        structure_display = offer.structure
        faculty = mdl.structure.find_faculty(offer.structure)
        if faculty:
            structure_display = faculty

        structure_address = mdl.structure_address.find_structure_address(structure_display)

        p_struct_name = Paragraph('%s' % structure_display, styles["Normal"])

        if structure_address:
            if structure_address.location:
                p_struct_location = Paragraph('%s' % structure_address.location, styles["Normal"])
            if structure_address.postal_code and structure_address.city:
                p_struct_address = Paragraph('%s %s' % (structure_address.postal_code, structure_address.city),
                                             styles["Normal"])
            phone_fax_data = ""
            if structure_address.phone:
                phone_fax_data += _('phone') + " : " + structure_address.phone
            if structure_address.fax:
                if structure_address.phone:
                    phone_fax_data += " - "
                phone_fax_data += _('fax') + " : " + structure_address.fax
            if len(phone_fax_data) > 0:
                p_phone_fax_data = Paragraph('%s' % phone_fax_data,
                                             styles["Normal"])

    data_structure = [[p_struct_name],
                  [p_struct_location],
                  [p_struct_address],
                  [p_phone_fax_data]]

    header_coordinator_structure = [[get_data_coordinator(learning_unit_year, styles), data_structure]]
    table_header = Table(header_coordinator_structure, colWidths='*')
    table_header.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))

    content.append(table_header)

    p = ParagraphStyle('right_page_header')
    p.alignment = TA_RIGHT
    p.fontSize = 10

    deliberation_date = mdl.offer_year_calendar.find_deliberation_date(offer, session_exam.number_session)
    if deliberation_date:
        deliberation_date = deliberation_date.strftime("%d/%m/%Y")
    else:
        deliberation_date = '-'
    content.append(Paragraph('%s : %s' % (_('deliberation_date'), deliberation_date), styles["Normal"]))
    content.append(Paragraph('%s : %s' % (_('academic_year'), str(academic_year)), text_left_style))
    content.append(Paragraph('Session : %d' % session_exam.number_session, text_left_style))
    content.append(Paragraph("<strong>%s : %s</strong>" % (learning_unit_year.acronym, learning_unit_year.title),
                             styles["Normal"]))
    content.append(Paragraph('''<b>%s : %s</b>''' % (_('program'), offer.acronym), styles["Normal"]))
    content.append(Spacer(1, 12))


def end_page_infos_building(content, end_date):
    content.append(Paragraph('''
                            <para spaceb=5>
                                &nbsp;
                            </para>
                            ''', ParagraphStyle('normal')))
    p = ParagraphStyle('info')
    p.fontSize = 10
    p.alignment = TA_LEFT
    content.append(Paragraph(_("return_doc_to_administrator") % end_date
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
<<<<<<< Updated upstream
                    <font size=10>%s ....................................</font>
                    <br/>
                    <font size=10>%s ..../..../........</font>
                    <br/>
=======
                    <font size=10>%s ...................................... , </font>
                    <font size=10><pre>%s ..../..../..........                      </pre></font>
>>>>>>> Stashed changes
                    <font size=10>%s</font>
                   ''' % (_('done_at'), _('the'), _('signature')), p_signature)
    content.append(paragraph_signature)

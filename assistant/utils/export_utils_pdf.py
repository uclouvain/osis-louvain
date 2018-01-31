##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
import time
import datetime
from io import BytesIO
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.db.models.query import QuerySet
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.colors import black, HexColor
from reportlab.graphics.charts.legends import Legend
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from base.models.entity import find_versions_from_entites
from base.models import academic_year, entity_version
from assistant.utils import manager_access
from assistant.models import assistant_mandate, review, tutoring_learning_unit_year
from assistant.models.enums import review_status, assistant_type

PAGE_SIZE = A4
MARGIN_SIZE = 15 * mm
COLS_WIDTH = [35*mm, 20*mm, 70*mm, 30*mm, 30*mm]
COLS_TUTORING_WIDTH = [40*mm, 15*mm, 15*mm, 15*mm, 15*mm, 15*mm, 15*mm, 15*mm, 40*mm]


def add_header_footer(canvas, doc):
    styles = getSampleStyleSheet()
    canvas.saveState()
    header_building(canvas, doc)
    footer_building(canvas, doc, styles)
    canvas.restoreState()


@user_passes_test(manager_access.user_is_manager, login_url='assistants_home')
def export_mandates(mandates=None):
    if not isinstance(mandates, QuerySet):
        mandates = assistant_mandate.find_by_academic_year(academic_year.current_academic_year())
    filename = ('%s_%s.pdf' % (_('assistants_mandates'), time.strftime("%Y%m%d_%H%M")))
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=PAGE_SIZE, rightMargin=MARGIN_SIZE, leftMargin=MARGIN_SIZE, topMargin=70,
                            bottomMargin=25)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Tiny', fontSize=6, font='Helvetica', leading=8, leftIndent=0, rightIndent=0,
                              firstLineIndent=0, alignment=TA_LEFT, spaceBefore=0, spaceAfter=0, splitLongWords=1,))
    styles.add(ParagraphStyle(name='StandardWithBorder', font='Helvetica', leading=18, leftIndent=10, rightIndent=10,
                              firstLineIndent=0, alignment=TA_JUSTIFY, spaceBefore=25, spaceAfter=5, splitLongWords=1,
                              borderColor='#000000', borderWidth=1, borderPadding=10,))
    content = []
    for mandate in mandates:
        add_mandate_content(content, mandate, styles)
    doc.build(content, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


def add_mandate_content(content, mandate, styles):
    content.append(create_paragraph(mandate.assistant.person.first_name + " " + mandate.assistant.person.last_name,
                                    get_administrative_data(mandate), styles['StandardWithBorder']))
    content.append(create_paragraph("%s" % (_('entities')), get_entities(mandate), styles['StandardWithBorder']))
    content.append(create_paragraph("<strong>%s</strong>" % (_('absences')), get_absences(mandate),
                                    styles['StandardWithBorder']))
    content.append(create_paragraph("<strong>%s</strong>" % (_('comment')), get_comment(mandate),
                                    styles['StandardWithBorder']))
    content.append(PageBreak())
    if mandate.assistant_type == assistant_type.ASSISTANT:
        content.append(create_paragraph("%s" % (_('doctorate')), get_phd_data(mandate.assistant),
                                        styles['StandardWithBorder']))
        content.append(create_paragraph("%s" % (_('research')), get_research_data(mandate),
                                        styles['StandardWithBorder']))
        content.append(PageBreak())
    content.append(create_paragraph("%s<br />" % (_('tutoring_learning_units')), '', styles["BodyText"]))
    _write_table_of_tutoring_learning_units_year(content, get_tutoring_learning_unit_year(mandate, styles['Tiny']))
    content.append(PageBreak())
    content.append(create_paragraph("%s" % (_('representation_activities')), get_representation_activities(mandate),
                                    styles['StandardWithBorder'], " (%s)" % (_('hours_per_year'))))
    content.append(create_paragraph("%s" % (_('service_activities')), get_service_activities(mandate),
                                    styles['StandardWithBorder'], " (%s)" % (_('hours_per_year'))))
    content.append(create_paragraph("%s" % (_('formation_activities')), get_formation_activities(mandate),
                                    styles['StandardWithBorder']))
    content.append(PageBreak())
    content.append(create_paragraph("%s" % (_('summary')), get_summary(mandate), styles['StandardWithBorder']))
    content += [draw_time_repartition(mandate)]
    content.append(PageBreak())
    content.append(create_paragraph("%s<br />" % (_('reviews')), '', styles["BodyText"]))
    _write_table_of_reviews(content, get_reviews_for_mandate(mandate, styles['Tiny']))
    content.append(PageBreak())


def format_data(data, title):
    if isinstance(data, datetime.date):
        data = data.strftime("%d-%m-%Y")
    return "<strong>%s :</strong> %s<br />" % (_(title), data) \
        if data and data != 'None' else "<strong>%s :</strong><br />" % (_(title))


def create_paragraph(title, data, style, subtitle=''):
    paragraph = Paragraph("<font size=14><strong>" + title + "</strong></font>" +
                          subtitle + "<br />" + data, style)
    return paragraph


def get_summary(mandate):
    report_remark = format_data(mandate.activities_report_remark, 'activities_report_remark')
    return report_remark


def get_administrative_data(mandate):
    assistant_type = format_data(_(mandate.assistant_type), 'assistant_type')
    matricule = format_data(mandate.sap_id, 'matricule_number')
    entry_date = format_data(mandate.entry_date, 'entry_date_contract')
    end_date = format_data(mandate.end_date, 'end_date_contract')
    contract_duration = format_data(mandate.contract_duration, 'contract_duration')
    contract_duration_fte = format_data(mandate.contract_duration_fte, 'contract_duration_fte')
    fulltime_equivalent = format_data(int(mandate.fulltime_equivalent * 100), 'fulltime_equivalent_percentage')
    other_status = format_data(mandate.other_status, 'other_status')
    renewal_type = format_data(_(mandate.renewal_type), 'renewal_type')
    justification = format_data(mandate.justification, 'exceptional_justification')
    external_contract = format_data(mandate.external_contract, 'external_post')
    external_functions = format_data(mandate.external_functions, 'function_outside_university')
    data = assistant_type + matricule + entry_date + end_date + contract_duration + contract_duration_fte \
           + fulltime_equivalent + other_status + renewal_type + justification + external_contract + external_functions
    return data


def get_entities(mandate):
    start_date = academic_year.current_academic_year().start_date
    entities_id = mandate.mandateentity_set.all().order_by('id').values_list('entity', flat=True)
    entities = find_versions_from_entites(entities_id, start_date)
    entities_data = ""
    for entity in entities:
        type = "%s" % (_(entity.entity_type))
        entities_data += "<strong>" + type + " :</strong>" + entity.acronym + "<br />"
    return entities_data


def get_absences(mandate):
    return mandate.absences if mandate.absences and mandate.absences != 'None' else ""


def get_comment(mandate):
    return mandate.comment if mandate.comment and mandate.comment != 'None' else ""


def get_phd_data(assistant):
    thesis_title = format_data(assistant.thesis_title, 'thesis_title')
    phd_inscription_date = format_data(assistant.phd_inscription_date, 'phd_inscription_date')
    confirmation_test_date = format_data(assistant.confirmation_test_date, 'confirmatory_test_date')
    thesis_date = format_data(assistant.thesis_date, 'thesis_defence_date')
    expected_phd_date = format_data(assistant.expected_phd_date, 'expected_registering_date')
    inscription = format_data(_(assistant.inscription) if assistant.inscription else None, 'registered_phd')
    remark = format_data(assistant.remark, 'remark')
    return inscription + phd_inscription_date + expected_phd_date + confirmation_test_date \
           + thesis_title + thesis_date + remark


def get_research_data(mandate):
    internships = format_data(mandate.internships, 'scientific_internships')
    conferences = format_data(mandate.conferences, 'conferences_contributor')
    publications = format_data(mandate.publications, 'publications_in_progress')
    awards = format_data(mandate.awards, 'awards')
    framing = format_data(mandate.framing, 'framing_participation')
    remark = format_data(mandate.remark, 'remark')
    return internships + conferences + publications + awards + framing + remark


def get_tutoring_learning_unit_year(mandate, style):
    data = generate_headers([
        'tutoring_learning_units', 'academic_year', 'sessions_number', 'sessions_duration', 'series_number',
        'face_to_face_duration', 'attendees', 'exams_supervision_duration', 'others_delivery'
    ], style)
    tutoring_learning_units_year = tutoring_learning_unit_year.find_by_mandate(mandate)
    for this_tutoring_learning_unit_year in tutoring_learning_units_year:
        academic_year = str(this_tutoring_learning_unit_year.learning_unit_year.academic_year)
        data.append([Paragraph(this_tutoring_learning_unit_year.learning_unit_year.title + " (" +
                               this_tutoring_learning_unit_year.learning_unit_year.acronym + ")", style),
                     Paragraph(academic_year, style),
                     Paragraph(str(this_tutoring_learning_unit_year.sessions_number), style),
                     Paragraph(str(this_tutoring_learning_unit_year.sessions_duration), style),
                     Paragraph(str(this_tutoring_learning_unit_year.series_number), style),
                     Paragraph(str(this_tutoring_learning_unit_year.face_to_face_duration), style),
                     Paragraph(str(this_tutoring_learning_unit_year.attendees), style),
                     Paragraph(str(this_tutoring_learning_unit_year.exams_supervision_duration), style),
                     Paragraph(this_tutoring_learning_unit_year.others_delivery or '', style)
                     ])
    return data


def generate_headers(titles, style):
    data = []
    for title in titles:
        data.append(Paragraph('''%s''' % _(title), style))
    return [data]


def _write_table_of_tutoring_learning_units_year(content, data):
    t = Table(data, COLS_TUTORING_WIDTH, repeatRows=1)
    t.setStyle(TableStyle([
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), HexColor("#f6f6f6"))]))
    content.append(t)


def get_representation_activities(mandate):
    faculty_representation = format_data(str(mandate.faculty_representation), 'faculty_representation')
    institute_representation = format_data(str(mandate.institute_representation), 'institute_representation')
    sector_representation = format_data(str(mandate.sector_representation), 'sector_representation')
    governing_body_representation = format_data(str(mandate.governing_body_representation),
                                                'governing_body_representation')
    corsci_representation = format_data(str(mandate.corsci_representation), 'corsci_representation')
    data = faculty_representation + institute_representation + sector_representation + governing_body_representation \
           + corsci_representation
    return data

def get_service_activities(mandate):
    students_service = format_data(str(mandate.students_service), 'students_service')
    infrastructure_mgmt_service = format_data(str(mandate.infrastructure_mgmt_service), 'infrastructure_mgmt_service')
    events_organisation_service = format_data(str(mandate.events_organisation_service), 'events_organisation_service')
    publishing_field_service = format_data(str(mandate.publishing_field_service), 'publishing_field_service')
    scientific_jury_service = format_data(str(mandate.scientific_jury_service), 'scientific_jury_service')
    data = students_service + infrastructure_mgmt_service + events_organisation_service + publishing_field_service \
           + scientific_jury_service
    return data


def get_formation_activities(mandate):
    formations = format_data(mandate.formations, 'formations')
    return formations


def get_reviews_for_mandate(mandate, style):
    data = generate_headers([
        'reviewer', 'review', 'remark', 'justification', 'confidential'], style)
    reviews = review.find_by_mandate(mandate.id)
    for rev in reviews:
        if rev.status == review_status.IN_PROGRESS:
            break
        if rev.reviewer is None:
            supervisor = "<br/>(%s)" % (str(_('supervisor')))
            person = mandate.assistant.supervisor.first_name + " " + mandate.assistant.supervisor.last_name + supervisor
        else:
            entity = entity_version.get_last_version(rev.reviewer.entity).acronym
            person = rev.reviewer.person.first_name + " " + rev.reviewer.person.last_name + "<br/>(" + entity + ")"
        data.append([Paragraph(person, style),
                     Paragraph(_(rev.advice), style),
                     Paragraph(rev.remark or '', style),
                     Paragraph(rev.justification or '', style),
                     Paragraph(rev.confidential or '', style)])
    return data


def _write_table_of_reviews(content, data):
    t = Table(data, COLS_WIDTH, repeatRows=1)
    t.setStyle(TableStyle([
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), HexColor("#f6f6f6"))]))
    content.append(t)


def set_items(n, obj, attr, values):
    m = len(values)
    i = m // n
    for j in range(n):
        setattr(obj[j], attr, values[j*i % m])


def draw_time_repartition(mandate):
    pdf_chart_colors = [
        HexColor("#fa9d00"),
        HexColor("#006884"),
        HexColor("#00909e"),
        HexColor("#ffd08d"),
    ]
    d = Drawing(width=180*mm, height=120*mm)
    pc = Pie()
    pc.x = 60*mm
    pc.y = 35*mm
    pc.width = 60*mm
    pc.height = 60*mm
    pc.data = []
    pc.labels = []
    titles = []
    if mandate.research_percent != 0:
        pc.data.append(mandate.research_percent)
        pc.labels.append(str(mandate.research_percent) + "%")
        titles.append(_('research_percent'))
    if mandate.tutoring_percent != 0:
        pc.data.append(mandate.tutoring_percent)
        pc.labels.append(str(mandate.tutoring_percent) + "%")
        titles.append(_('tutoring_percent'))
    if mandate.service_activities_percent != 0:
        pc.data.append(mandate.service_activities_percent)
        pc.labels.append(str(mandate.service_activities_percent) + "%")
        titles.append(_('service_activities_percent'))
    if mandate.formation_activities_percent != 0:
        pc.data.append(mandate.formation_activities_percent)
        pc.labels.append(str(mandate.formation_activities_percent) + "%")
        titles.append(_('formation_activities_percent'))
    pc.slices.strokeWidth = 0.5
    pc.slices.fontName = 'Helvetica'
    pc.slices.fontSize = 8
    if len(pc.data) > 0:
        d.add(pc)
        d.add(Legend(), name='legend')
        d.legend.x = 90
        d.legend.y = 50
        d.legend.dx = 8
        d.legend.dy = 8
        d.legend.fontName = 'Helvetica'
        d.legend.fontSize = 8
        d.legend.boxAnchor = 'w'
        d.legend.columnMaximum = 10
        d.legend.strokeWidth = 1
        d.legend.strokeColor = black
        d.legend.deltax = 75
        d.legend.deltay = 10
        d.legend.autoXPadding = 5
        d.legend.yGap = 0
        d.legend.dxTextSpace = 5
        d.legend.alignment = 'right'
        d.legend.dividerOffsY = 5
        d.legend.subCols.rpad = 30
        n = len(pc.data)
        set_items(n, pc.slices, 'fillColor', pdf_chart_colors)
        d.legend.colorNamePairs = [(pc.slices[i].fillColor, (titles[i], '%0.f' % pc.data[i]+'%')) for i in range(n)]
    return d


def header_building(canvas, doc):
    canvas.line(doc.leftMargin, 790, doc.width+doc.leftMargin, 790)
    canvas.drawString(80, 800, "%s %s" % (_('assistant_mandates_renewals'), academic_year.current_academic_year()))


def footer_building(canvas, doc, styles):
    printing_date = timezone.now()
    printing_date = printing_date.strftime("%d/%m/%Y")
    pageinfo = "%s : %s" % (_('printing_date'), printing_date)
    footer = Paragraph(''' <para align=right>Page %d - %s </para>''' % (doc.page, pageinfo), styles['Normal'])
    w, h = footer.wrap(doc.width, doc.bottomMargin)
    footer.drawOn(canvas, doc.leftMargin, h)


def end_page_infos_building(content, end_date):
    p = ParagraphStyle('info')
    p.fontSize = 10
    p.alignment = TA_LEFT
    if not end_date:
        end_date = '(%s)' % _('date_not_passed')
    content.append(Paragraph(_("return_doc_to_administrator") % end_date, p))
    content.append(Paragraph('''<para spaceb=5>&nbsp;</para>''', ParagraphStyle('normal')))
    p_signature = ParagraphStyle('info')
    p_signature.fontSize = 10
    paragraph_signature = Paragraph('''
                    <font size=10>%s ...................................... , </font>
                    <font size=10>%s ..../..../.......... &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                    y&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</font>
                    <font size=10>%s</font>
                   ''' % (_('done_at'), _('the'), _('signature')), p_signature)
    content.append(paragraph_signature)
    content.append(Paragraph('''<para spaceb=2>&nbsp;</para>''', ParagraphStyle('normal')))

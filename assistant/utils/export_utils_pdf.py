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

from django.contrib.auth.decorators import user_passes_test, login_required
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.views.decorators.http import require_http_methods

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

from base.models.entity import find_versions_from_entites
from base.models import academic_year, entity_version

from assistant.utils import assistant_access, manager_access
from assistant.models import assistant_mandate, review, tutoring_learning_unit_year
from assistant.models.enums import review_status, assistant_type

PAGE_SIZE = A4
MARGIN_SIZE = 15 * mm
COLS_WIDTH_FOR_REVIEWS = [35*mm, 20*mm, 70*mm, 30*mm, 30*mm]
COLS_WIDTH_FOR_TUTORING = [40*mm, 15*mm, 15*mm, 15*mm, 15*mm, 15*mm, 15*mm, 15*mm, 40*mm]


@login_required
def build_doc(request, mandates, show_reviews):
    year = mandates[0].academic_year
    filename = ('%s_%s_%s.pdf' % (_('assistants_mandates'), year, time.strftime("%Y%m%d_%H%M")))
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=PAGE_SIZE, rightMargin=MARGIN_SIZE, leftMargin=MARGIN_SIZE, topMargin=70,
                            bottomMargin=25)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Tiny', fontSize=6, font='Helvetica', leading=8, leftIndent=0, rightIndent=0,
                              firstLineIndent=0, alignment=TA_LEFT, spaceBefore=0, spaceAfter=0, splitLongWords=1, ))
    styles.add(ParagraphStyle(name='StandardWithBorder', font='Helvetica', leading=18, leftIndent=10, rightIndent=10,
                              firstLineIndent=0, alignment=TA_JUSTIFY, spaceBefore=25, spaceAfter=5, splitLongWords=1,
                              borderColor='#000000', borderWidth=1, borderPadding=10, ))
    content = []
    for mandate in mandates:
        add_mandate_content(content, mandate, styles, show_reviews)
    doc.build(content, add_header_footer)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


@require_http_methods(["POST"])
@user_passes_test(assistant_access.user_is_assistant_and_procedure_is_open, login_url='access_denied')
def export_mandate(request):
    mandate_id = request.POST.get("mandate_id")
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    return build_doc(request, mandates=[mandate], show_reviews=False)


@user_passes_test(manager_access.user_is_manager, login_url='access_denied')
def export_mandates(request):
    mandates = assistant_mandate.find_by_academic_year_by_excluding_declined(academic_year.current_academic_year())
    return build_doc(request, mandates, show_reviews=True)


def add_mandate_content(content, mandate, styles, show_reviews):
    content.append(
        create_paragraph(
            "%s (%s)" % (mandate.assistant.person, mandate.academic_year),
            get_administrative_data(mandate),
            styles['StandardWithBorder']
        )
    )
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
    write_table(content, get_tutoring_learning_unit_year(mandate, styles['Tiny']), COLS_WIDTH_FOR_TUTORING)
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
    if show_reviews:
        content.append(create_paragraph("%s<br />" % (_('reviews')), '', styles["BodyText"]))
        write_table(content, get_reviews_for_mandate(mandate, styles['Tiny']), COLS_WIDTH_FOR_REVIEWS)
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
    return assistant_type + matricule + entry_date + end_date + contract_duration + contract_duration_fte \
           + fulltime_equivalent + other_status + renewal_type + justification + external_contract + external_functions


def get_entities(mandate):
    start_date = academic_year.current_academic_year().start_date
    entities_id = mandate.mandateentity_set.all().order_by('id').values_list('entity', flat=True)
    entities = find_versions_from_entites(entities_id, start_date)
    entities_data = ""
    for entity in entities:
        entities_data += "<strong>{} : </strong>{}<br />".format(_(entity.entity_type), entity.acronym)
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
        data.append([Paragraph(this_tutoring_learning_unit_year.learning_unit_year.complete_title + " (" +
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
        data.append(Paragraph("%s" % _(title), style))
    return [data]


def get_representation_activities(mandate):
    faculty_representation = format_data(str(mandate.faculty_representation), 'faculty_representation')
    institute_representation = format_data(str(mandate.institute_representation), 'institute_representation')
    sector_representation = format_data(str(mandate.sector_representation), 'sector_representation')
    governing_body_representation = format_data(str(mandate.governing_body_representation),
                                                'governing_body_representation')
    corsci_representation = format_data(str(mandate.corsci_representation), 'corsci_representation')
    return faculty_representation + institute_representation + sector_representation + governing_body_representation \
           + corsci_representation


def get_service_activities(mandate):
    students_service = format_data(str(mandate.students_service), 'students_service')
    infrastructure_mgmt_service = format_data(str(mandate.infrastructure_mgmt_service), 'infrastructure_mgmt_service')
    events_organisation_service = format_data(str(mandate.events_organisation_service), 'events_organisation_service')
    publishing_field_service = format_data(str(mandate.publishing_field_service), 'publishing_field_service')
    scientific_jury_service = format_data(str(mandate.scientific_jury_service), 'scientific_jury_service')
    return students_service + infrastructure_mgmt_service + events_organisation_service + publishing_field_service \
           + scientific_jury_service


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
            person = "{} {}<br/>({})".format(
                mandate.assistant.supervisor.first_name,
                mandate.assistant.supervisor.last_name,
                str(_('supervisor'))
            )
        else:
            person = "{} {}<br/>({})".format(
                rev.reviewer.person.first_name,
                rev.reviewer.person.last_name,
                entity_version.get_last_version(rev.reviewer.entity).acronym
            )
        data.append([Paragraph(person, style),
                     Paragraph(_(rev.advice), style),
                     Paragraph(rev.remark or '', style),
                     Paragraph(rev.justification or '', style),
                     Paragraph(rev.confidential or '', style)])
    return data


def write_table(content, data, cols_width):
    t = Table(data, cols_width, repeatRows=1)
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
    drawing = Drawing(width=180*mm, height=120*mm)
    pdf_chart_colors = [HexColor("#fa9d00"), HexColor("#006884"), HexColor("#00909e"), HexColor("#ffd08d"), ]
    pie = Pie()
    pie.x = 60*mm
    pie.y = 35*mm
    pie.width = 60*mm
    pie.height = 60*mm
    pie.slices.strokeWidth = 0.5
    pie.slices.fontName = 'Helvetica'
    pie.slices.fontSize = 8
    pie.data = []
    pie.labels = []
    titles = []
    add_data_and_titles_to_pie(pie, titles, mandate.research_percent, 'research_percent')
    add_data_and_titles_to_pie(pie, titles, mandate.tutoring_percent, 'tutoring_percent')
    add_data_and_titles_to_pie(pie, titles, mandate.service_activities_percent, 'service_activities_percent')
    add_data_and_titles_to_pie(pie, titles, mandate.formation_activities_percent, 'formation_activities_percent')
    if len(pie.data) > 0:
        drawing.add(pie)
        add_legend_to_pie(drawing)
        n = len(pie.data)
        set_items(n, pie.slices, 'fillColor', pdf_chart_colors)
        drawing.legend.colorNamePairs = \
            [(pie.slices[i].fillColor, (titles[i], '%0.f' % pie.data[i] + '%')) for i in range(n)]
    return drawing


def add_legend_to_pie(drawing):
    drawing.add(Legend(), name='legend')
    drawing.legend.x = 90
    drawing.legend.y = 50
    drawing.legend.dx = 8
    drawing.legend.dy = 8
    drawing.legend.fontName = 'Helvetica'
    drawing.legend.fontSize = 8
    drawing.legend.boxAnchor = 'w'
    drawing.legend.columnMaximum = 10
    drawing.legend.strokeWidth = 1
    drawing.legend.strokeColor = black
    drawing.legend.deltax = 75
    drawing.legend.deltay = 10
    drawing.legend.autoXPadding = 5
    drawing.legend.yGap = 0
    drawing.legend.dxTextSpace = 5
    drawing.legend.alignment = 'right'
    drawing.legend.dividerOffsY = 5
    drawing.legend.subCols.rpad = 30


def add_data_and_titles_to_pie(pie, titles, data, title):
    if data != 0:
        pie.data.append(data)
        pie.labels.append(str(data) + "%")
        titles.append(_(title))


def add_header_footer(canvas, doc):
    styles = getSampleStyleSheet()
    canvas.saveState()
    header_building(canvas, doc)
    footer_building(canvas, doc, styles)
    canvas.restoreState()


def header_building(canvas, doc):
    canvas.line(doc.leftMargin, 790, doc.width+doc.leftMargin, 790)
    canvas.drawString(110, 800, "%s" % (_('assistant_mandates_renewals')))


def footer_building(canvas, doc, styles):
    printing_date = timezone.now()
    printing_date = printing_date.strftime("%d/%m/%Y")
    pageinfo = "%s : %s" % (_('printing_date'), printing_date)
    footer = Paragraph(''' <para align=right>Page %d - %s </para>''' % (doc.page, pageinfo), styles['Normal'])
    w, h = footer.wrap(doc.width, doc.bottomMargin)
    footer.drawOn(canvas, doc.leftMargin, h)

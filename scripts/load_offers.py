# retrieve the data from json
import collections
import json
import pathlib
from functools import partial
from itertools import chain

import sys
from django.conf import settings
from lxml.builder import E

import prettyprinter
from lxml import etree
from lxml import html

from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.tests.factories.education_group_year import EducationGroupYearFactory
from cms.models.text_label import TextLabel
from cms.models.translated_text import TranslatedText
from cms.models.translated_text_label import TranslatedTextLabel


def new_div(html_content, class_name):
    """
    Crée un div avec le nom d'une classe et le contenu HTML donné
    """
    node = etree.Element('div', **{'class': class_name})
    node.append(html.fromstring(html_content))
    return etree.tostring(node, pretty_print=True, encoding=str)


def append_if_content(content, info, key, class_name=None):
    """
    Si la clé se trouve dans le dictionnaire et que la valeur de celle-ci est utilisable
    alors on crée un nouveau contenu
    """
    class_name = class_name or key

    part = info.get(key)
    if part:
        content.append(new_div(part, class_name))


def generate_html_two_parts(info):
    """
    Génere le HTML pour les éléments qui sont en deux parties
    <div class="reddot_part1">
    </div>
    <div class="reddot_part2">
    </div>
    """
    return generate_html_for_multiparts(
        info,
        [('part1', 'reddot_part1'),
         ('part2', 'reddot_part2')]
    )


def generate_html_for_program(info):
    """
    Génère le HTML pour les programmes
    <div class="reddot_intro">
    </div>
    <div class="reddot_body">
    </div>
    """
    return generate_html_for_multiparts(
        info,
        [('intro', 'reddot_intro'),
         ('programme_detaille', 'reddot_body')]
    )


def generate_html_for_multiparts(info, parts):
    content = []
    for part_name, class_name in parts:
        append_if_content(content, info, part_name, class_name)
    return ''.join(content)


def generate_html_from_comp_acquis(competences):
    """
    Génere le code HTML pour les Compétences et Acquis
    <div class="reddot_body">
    </div>
    Si il y a des composants, alors on cree des tags supplementaires.
    <div class="reddot_intro">
    </div>
    <div class="reddot_teaser">
    </div>
    <div class="reddot_collapse">
    </div>

    <div class="reddot_teaser">
    </div>
    <div class="reddot_collapse">
    </div>

    et eventuellement un div avec un extra
    <div class="reddot_extra">
    </div>
    """
    content = []

    append_if_content(content, competences, 'body', 'reddot_body')

    # competences
    components = competences.get('components')
    if components:
        append_if_content(content, components, 'intro', 'reddot_intro')

        for item in components['items']:
            append_if_content(content, item, 'intro', 'reddot_teaser')
            append_if_content(content, item, 'body', 'reddot_collapse')

    append_if_content(content, competences, 'extra', 'reddot_extra')

    return ''.join(content)


def CLASS(*args):
    return {'class': ' '.join(args)}


def generate_html_for_contacts(contacts):
    """Generate l'HTML pour la page des contacts"""
    calls = (
        render_entity_code,
        render_responsible,
        partial(render_members, section='other_responsibles', class_name='responsibles'),
        partial(render_members, section='jury'),
        partial(render_members, section='contact'),
    )

    node_rendering = (call(contacts) for call in calls)
    nodes = (node for node in node_rendering if node is not None)
    tostring = partial(etree.tostring, pretty_print=True, encoding=str)
    return ''.join(map(tostring, nodes))


def render_responsible(contacts):
    """
    Genere un HTML de la forme suivante
    <div class="contacts_responsible">
        <ul>
            <li><a href="{{ responsible.url }}">{{ responsible.name }} </a></li>
        </ul>
    </div>
    """
    responsible = contacts.get('responsible')
    if responsible:
        title = responsible.get('title', '')
        mbox = responsible['metadata']['foaf:mbox'].replace('mailto:', '')
        contact = "#contact:{0}:{1}#".format(title, mbox)
        return E.div(
            E.ul(E.li(contact)),
            CLASS('contacts_responsible')
        )
    return None


def render_entity_code(contacts):
    entity_code = contacts.get('entity_code')
    if entity_code:
        return E.div(
            entity_code,
            CLASS('contacts_entity_code')
        )
    return None


def render_members(contacts, section, class_name=None):
    """
    Genere un HTML de la forme suivante

    <div class="{{ class_name }}">
        <ul>
            {% for member in members %}
            <li>{{ member.title }} <a href="{{ member.url }}">{{ member.name }}</a></li>
            {% endfor %}
        </ul>
    </div>
    """
    members = contacts.get(section)

    class_name = section if class_name is None else class_name

    def apply(member):
        title = member.get('title', '')
        mbox = member['metadata']['foaf:mbox'].replace('mailto:', '')
        contact = "#contact:{0}:{1}#".format(title, mbox)
        return E.li(contact)

    if members:
        return E.div(
            E.ul(
                *tuple(map(apply, members))
            ),
            CLASS('contacts_{class_name}'.format(class_name=class_name))
        )

    return None


def get_text_label(entity, label):
    """
    Essaie de recuperer un label d'une entité ou simplement la crée si celle-ci n'existe pas.
    """
    text_label, created = TextLabel.objects.get_or_create(
        entity=entity,
        label=label,
        published=True
    )
    return text_label


def debugger(func):
    """
    Decorateur qui permet de lancer le debugger de python en mode post mortem
    Il s'utilise de la maniere suivante

    @debugger
    def run():
        pass
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            import pdb
            pdb.post_mortem()

    return wrapper


def convert_to_html(item, label, value):
    if item['type'] != 'offer':
        return value

    MAPPING = {
        'comp_acquis': generate_html_from_comp_acquis,
        'caap': generate_html_two_parts,
        'prerequis': generate_html_two_parts,
        'programme': generate_html_for_program,
        'contacts': generate_html_for_contacts,
    }

    if label in MAPPING:
        value = MAPPING[label](value)

    return value.strip()


def import_offer_and_items(item, education_group_year, mapping_label_text_label, context):
    for label, value in item['info'].items():
        value = convert_to_html(item, label, value)

        if not value:
            continue

        translated_text, created = TranslatedText.objects.get_or_create(
            entity=context.entity,
            reference=education_group_year.id,
            text_label=mapping_label_text_label[label],
            language=context.language,
            defaults={
                'text': value
            }
        )

        if not created:
            translated_text.text = value
            translated_text.save()


def find_education_group_year_for_group(item):
    qs = EducationGroupYear.objects.filter(
        academic_year__year=item['year'],
        partial_acronym__iexact=item['acronym']
    )

    if not qs.exists():
        return

    return qs.first()


def find_education_group_year_for_offer(item):
    qs = EducationGroupYear.objects.filter(
        academic_year__year=item['year'],
        acronym__iexact=item['acronym']
    )

    if not qs.exists():
        return

    return qs.first()


def find_education_group_year_for_common(item):
    records = EducationGroupYear.objects.filter(
        academic_year__year=item['year'],
        acronym__iexact=item['acronym']
    )

    if not records:
        academic_year = AcademicYear.objects.get(year=item['year'])
        education_group_year = EducationGroupYearFactory(
            acronym=item['acronym'],
            academic_year=academic_year
        )
    else:
        education_group_year = records.first()

    return education_group_year


LABEL_TEXTUALS = [
    (settings.LANGUAGE_CODE_FR, 'comp_acquis', 'Compétences et Acquis'),
    (settings.LANGUAGE_CODE_FR, 'pedagogie', 'Pédagogie'),
    (settings.LANGUAGE_CODE_FR, 'contacts', 'Contacts'),
    (settings.LANGUAGE_CODE_FR, 'mobilite', 'Mobilité'),
    (settings.LANGUAGE_CODE_FR, 'formations_accessibles', 'Formations Accessibles'),
    (settings.LANGUAGE_CODE_FR, 'certificats', 'Certificats'),
    (settings.LANGUAGE_CODE_FR, 'module_complementaire', 'Module Complémentaire'),
    (settings.LANGUAGE_CODE_FR, 'evaluation', 'Évaluation'),
    (settings.LANGUAGE_CODE_FR, 'structure', 'Structure'),
]

MAPPING_LABEL_TEXTUAL = collections.defaultdict(dict)

for language, key, term in LABEL_TEXTUALS:
    MAPPING_LABEL_TEXTUAL[language][key] = term


def find_translated_label(language, label):
    if language in MAPPING_LABEL_TEXTUAL and label in MAPPING_LABEL_TEXTUAL[language]:
        return MAPPING_LABEL_TEXTUAL[language][label]
    else:
        return label.title()


def run(filename, language='fr-be'):
    """
    Import the json file,

    Load the items from the json file and will import each item in the database
    Kind of items:
    * offer
    * common
    * group
    """
    path = check_parameters(filename, language)

    entity = 'offer_year'

    items = json.loads(path.read_text())

    labels = set(chain.from_iterable(o.get('info', {}).keys() for o in items))

    Context = collections.namedtuple('Context', 'entity language')
    context = Context(entity=entity, language=language)

    mapping_label_text_label = get_mapping_label_texts(context, labels)

    create_offers(context, items, mapping_label_text_label)


def check_parameters(filename, language):
    languages = {x[0] for x in settings.LANGUAGES}
    if language not in languages:
        print('The language must to be one item of these languages {0}'.format(languages))
        sys.exit(0)
    path = pathlib.Path(filename)
    if not path.exists():
        print('The file must to exist')
        sys.exit(0)
    return path


def get_mapping_label_texts(context, labels):
    mapping_label_text_label = {}
    for label in labels:
        text_label = get_text_label(context.entity, label)

        TranslatedTextLabel.objects.get_or_create(
            text_label=text_label,
            language=context.language,
            label=find_translated_label(context.language, label)
        )

        mapping_label_text_label[label] = text_label
    return mapping_label_text_label


def create_offers(context, offers, mapping_label_text_label):
    for offer in offers:
        import_offer(context, offer, mapping_label_text_label)


def import_offer(context, offer, mapping_label_text_label):
    if 'info' not in offer:
        return None

    function = {
        'group': find_education_group_year_for_group,
        'common': find_education_group_year_for_common,
        'offer': find_education_group_year_for_offer,
    }.get(offer['type'])

    if not function:
        return None

    egy = function(offer)
    if not egy:
        return None

    import_offer_and_items(offer, egy, mapping_label_text_label, context)

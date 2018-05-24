import textwrap

from django.test import TestCase

from webservices.views import normalize_module_complementaire, normalize_program, normalize_caap_or_prerequis


class NormalizationTestCase(TestCase):
    def test_normalize_module_complementaire(self):
        common_terms = {'module_compl': 'Information'}
        has_section = {}
        content = normalize_module_complementaire(
            common_terms,
            'Message',
            has_section,
            'section'
        )
        self.assertEqual(
            content,
            textwrap.dedent('<div class="info">Information</div>Message')
        )

        self.assertIn('section', has_section)

    def test_normalize_module_complementaire_no_term(self):
        content = normalize_module_complementaire(
            {}, 'Message',
            {}, 'section'
        )

        self.assertEqual(
            content,
            textwrap.dedent('Message')
        )


    def test_normalize_program(self):
        common_terms = {'agregations': 'Agregation'}
        has_section = {}
        content = normalize_program(
            common_terms,
            'Message',
            has_section,
            'section'
        )
        self.assertEqual(
            content,
            textwrap.dedent('AgregationMessage')
        )

        self.assertIn('section', has_section)

    def test_normalize_program_no_term(self):
        content = normalize_program(
            {}, 'Message',
            {}, 'section'
        )

        self.assertEqual(
            content,
            textwrap.dedent('Message')
        )


    def test_normalize_caap_or_prerequis(self):
        common_terms = {'section': 'Caap'}
        has_section = {}
        content = normalize_caap_or_prerequis(
            common_terms,
            'Message<div class="part2">Hello</div>',
            has_section,
            'section'
        )
        self.assertEqual(
            content,
            textwrap.dedent('MessageCaap<div class="part2">Hello</div>')
        )

        self.assertIn('section', has_section)

    def test_normalize_caap_or_prerequis_no_term(self):
        common_terms = {'section': 'Caap'}
        has_section = {}
        content = normalize_caap_or_prerequis(
            common_terms,
            'Message<div class="part2">Hello</div>',
            has_section,
            ''
        )
        self.assertEqual(
            content,
            textwrap.dedent('Message<div class="part2">Hello</div>')
        )
"""
Django Unused Templates
by Alexander Meng
Generates a list of unused templates in your current directory and subdirectories
by searching all .html and .py files for the names of your templates.
IF YOU OVERRIDE DJANGO TEMPLATES, THEY MAY APPEAR IN THE LIST AS UNUSED.
"""

import os
import sys

MODULES = [
    'all', 'osis', 'internship', 'continuing_education', 'osis_common', 'partnership', 'dissertation', 'assistant'
]
OSIS_MODULES = ['assessments', 'attribution', 'backoffice', 'base', 'cms', 'education_group', 'learning_unit',
                'program_management', 'reference', 'rules_management', 'webservices']
DJANGO_EXCLUDED = ['migrations/', 'apps.py']
GIT_EXCLUDED = ['.githooks/', '.github/']
VENV_EXCLUDED = ['env/', 'venv/']

TEST_IGNORED = ['setUp', 'setUpTestData', 'mock_*', 'tearDown']
MODEL_LIST_IGNORED = ['Meta', 'ordering', 'raw_id_fields', 'model', 'changed', 'search_fields', 'list_filter',
                      'list_display', 'filter_fields', 'ordering_fields', 'paginate_by', 'filter_backends',
                      'group_by', 'unique_together', 'actions']
MEDIA_IGNORED = ['Media', 'css', 'widgets']
CLASS_IGNORED = ['template_name', 'fieldsets', '*_classes', 'get_content']


def _should_analyze_file(f, submodules, features=False):
    if __is_outside_file(f, features):
        return False
    for folder in submodules:
        if '\\' + folder + '\\' in f:
            return True
    return False


def __is_outside_file(f, features=False):
    if '\\venv' in f or '\\tests' in f or '\\Lib' in f:
        return True
    if not features and '\\features' in f:
        return False


def _get_files_of_extension(file_extension, filter):
    return [
        f[2:-1]
        for f in os.popen('dir /b /s "*.' + file_extension + '" | sort').readlines()
        if _should_analyze_file(f, filter)
    ]


def _get_templates(html_files):
    # Templates will only be returned if they are located in a
    # /templates/ directory
    template_list = []
    for html_file in html_files:
        if html_file.find("/templates") != 0:
            try:
                template_list.append(html_file.rsplit("templates\\")[1])
            except IndexError:
                # The html file is not in a template directory...
                # don't count it as a template
                template_list.append("html")

    return template_list


def get_unused_templates(module):
    print("Start searching unused templates in %s module(s)" % (module))
    modules_to_keep = {
        module: '.' if module == 'all' else (OSIS_MODULES if module == 'osis' else [module])
        for module in MODULES
    }[module if module else 'all']
    print(modules_to_keep)
    html_files = _get_files_of_extension('html', modules_to_keep)
    templates = _get_templates(html_files)
    py_files = _get_files_of_extension('py', modules_to_keep)
    files = py_files + html_files  # List of all files
    tl_count = [0 for _ in templates]

    unused_templates = 0
    for file in files:
        f = open(file)
        text = f.read()
        for count, template in enumerate(templates):
            if template.replace('\\', '/') in text:
                tl_count[count] = 1
        f.close()

    for count, template in enumerate(templates):
        if tl_count[count] == 0:
            print("Unused template : ", html_files[count])
            unused_templates += 1
    print("# Unused templates : ", unused_templates)


def main(argv):
    to_clean = argv[0] if argv else None
    module = argv[1] if to_clean and len(argv) > 1 else 'all'
    if not to_clean or module not in MODULES:
        print("First parameter should be :")
        print("\t\t'template' to get unused templates or")
        print("\t\t'vulture' to check unused code (to verify).")
        print("Second parameter (if set) should be:")
        print("\t\ta valid OSIS module or")
        print("\t\t'osis' to exclude submodules")
        print("\t\tDEFAULT : 'all' = osis + submodules")
        sys.exit()
    if 'template' == to_clean:
        get_unused_templates(module)
    if 'vulture' == to_clean:
        get_unused_with_vulture(module)


def get_unused_with_vulture(module):
    ignored_names = ['urlpatterns'] + TEST_IGNORED + CLASS_IGNORED + MEDIA_IGNORED + MODEL_LIST_IGNORED
    excluded_patterns = DJANGO_EXCLUDED + GIT_EXCLUDED + VENV_EXCLUDED
    vulture_osis_modules = OSIS_MODULES + ['templates']
    module_to_check = ' .' if module == 'all' else (' '.join(vulture_osis_modules) if module == 'osis' else module)
    os.system(
        'vulture ' + module_to_check + ' --ignore-names ' + ','.join(ignored_names) + ' --exclude ' + ','.join(
            excluded_patterns)
    )


if __name__ == "__main__":
    main(sys.argv[1:])

import fnmatch
import logging
import os
import pyclbr
import re

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """Rough check for unused methods in our apps. Scans models, views, utils, api, forms and signals
files for what look like methods calls, then looks at all of our classes' methods to ensure each
is called. Do not trust this blindly but it's a good way to get leads on what may be dead code.

TODO: look for classes that are never referenced - mainly to find dead form types"""

    def handle(self, **options):
        called_methods = self._get_list_of_called_methods()
        for app in settings.LOCAL_APPS:
            for f in ["models", "views", "utils", "api", "signals", "forms"]:
                path = ".".join([app, f])
                try:
                    classdict = pyclbr.readmodule(path)
                    logger.debug("Reading %s", path)
                except (ImportError, AttributeError):
                    continue
                for name, klass in classdict.items():
                    logger.debug("Getting methods for %s", name)
                    for m in klass.methods:
                        # ignore form clean_ methods which are called implicitly
                        if re.match(r"^clean_", m):
                            continue
                        if m not in called_methods:
                            logger.warning("No calls of %s.%s", name, m)

    def _get_list_of_called_methods(self):
        """
        Naively open all Python files that we're interested in and get a list of unique method
        calls by looking for things like function_name( preceded by either a period or space,
        but not "def ". Also includes wrapped API methods like 'method_name'
        """
        files = []
        ignored_files = ["__init__.py", "urls.py", "tests.py"]
        for root, _, filenames in os.walk("."):
            if root.find("migrations") > -1 or root.find("settings") > -1 or root.find("tests") > -1:
                continue
            for filename in fnmatch.filter(filenames, "*.py"):
                if filename in ignored_files or filename.find("wsgi") > -1:
                    continue
                files.append(os.path.join(root, filename))
        logger.info("Found %d Python files", len(files))

        method_matcher = re.compile(r"""['".]([a-zA-Z_]+)[('",]""")
        # prepopulate with known methods to ignore
        methods = {"__unicode__", "prepend_urls", "detail_uri_kwargs", "__hash__", "create_list", "read_list",
                   "update_list", "delete_list", "delete_detail", "create_detail", "update_detail", "read_detail"}
        for name in files:
            with open(name, encoding="utf8") as f:
                for match in method_matcher.finditer(f.read()):
                    methods.add(match.group(1))
        logger.info("Found %d unique methods", len(methods))
        return methods

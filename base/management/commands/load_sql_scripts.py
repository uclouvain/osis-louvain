import logging
import os
import re
import sys
from typing import Dict, List

import attr
from django.conf import settings
from django.db import connection

logger = logging.getLogger(settings.DEFAULT_LOGGER)

LOCK_TEMPLATE = """
    BEGIN WORK;
    LOCK TABLE {table_to_lock} IN {lock_mode} MODE;
    {sql_script}
    COMMIT WORK;
"""


@attr.s(frozen=True, slots=True)
class SQLLockStatement:
    lock_template = attr.ib(type=str, default=LOCK_TEMPLATE)
    lock_mode = attr.ib(type=str, default=None)


@attr.s(frozen=True, slots=True)
class LoadSQLFilesToExecute:
    subfolder = attr.ib(type=str, default=None)
    backoffice = attr.ib(type=str, default='backoffice/')
    scripts_path = attr.ib(type=str)
    tablename_regex = attr.ib(type=str, default=None)

    @scripts_path.default
    def _scripts_path(self):
        return self.backoffice + self.subfolder

    def _get_scripts_files(self):
        return os.listdir(self.scripts_path)

    def _get_sql_string_from_file(self, file: str) -> str:
        file_extension = file.split(".")[-1].lower()
        if file_extension != 'sql':
            logger.error("##### Should load sql file but it is a {} extension".format(file_extension))
            sys.exit()

        file = open(self.scripts_path + file)
        return file.read()

    def load_scripts(self) -> List[Dict[str, str]]:
        script_filenames = self._get_scripts_files()
        script_strings = []
        for script_filename in script_filenames:
            script_string = self._get_sql_string_from_file(file=script_filename)
            script_strings.append(
                {'script_string': script_string, 'filename': script_filename}
            )
        return script_strings

    def get_table_name(self, sql_string: str):
        table_match = re.search(self.tablename_regex, sql_string, re.IGNORECASE)
        try:
            match = table_match.group(1)
            if match:
                return match
        except Exception:
            logger.error("#### Unable to get table name from sql file ####")
            sys.exit()


@attr.s(frozen=True, slots=True)
class LoadSQL:
    cursor = attr.ib()

    @cursor.default
    def _cursor(self):
        return connection.cursor()

    def execute(self, script: str):
        self.cursor.execute(script)


@attr.s(frozen=True, slots=True)
class LoadSQLTriggers:
    loadSQL = attr.ib(type=LoadSQL, default=LoadSQL())
    loadSQLFile = attr.ib(
        type=LoadSQLFilesToExecute,
        default=LoadSQLFilesToExecute(
            subfolder='triggers/', tablename_regex=r'CREATE TRIGGER[\S\s]*(public..*)'
        )
    )
    SQLLock = attr.ib(type=SQLLockStatement, default=SQLLockStatement(lock_mode='SHARE ROW EXCLUSIVE'))

    def load_triggers(self):
        trigger_strings = self.loadSQLFile.load_scripts()
        logger.info("## Loading triggers from {} ##".format(self.loadSQLFile.scripts_path))
        for trigger in trigger_strings:
            self.load_trigger(trigger)
        logger.info("## Loading triggers finished ##")

    def load_trigger(self, trigger: Dict[str, str]):
        table_name = self.loadSQLFile.get_table_name(trigger['script_string'])
        sql_script = self.SQLLock.lock_template.format(
            table_to_lock=table_name,
            sql_script=trigger['script_string'],
            lock_mode=self.SQLLock.lock_mode
        )
        logger.info("# Load trigger from {filename} #".format(filename=trigger['filename']))
        logger.info("# Table {tablename} LOCKED #".format(tablename=table_name))
        self.loadSQL.execute(sql_script)
        logger.info("# Table {tablename} UNLOCKED #".format(tablename=table_name))

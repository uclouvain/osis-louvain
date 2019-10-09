#!/usr/bin/env python
import logging
import os
import sys
import dotenv

if __name__ == "__main__":
    if 'test' in sys.argv:
        os.environ.setdefault('TESTING', 'True')
        if '--no-logs' in sys.argv:
            print('> Disabling logging levels of ERROR and below.')
            sys.argv.remove('--no-logs')
            logging.disable(logging.ERROR)

    dotenv.read_dotenv()

    SETTINGS_FILE = os.environ.get('DJANGO_SETTINGS_MODULE', 'backoffice.settings.local')
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", SETTINGS_FILE)

    from django.core.management import execute_from_command_line

    try:
        execute_from_command_line(sys.argv)
    except KeyError as ke:
        print("Error loading application.")
        print("The following environment var is not defined : {}".format(str(ke)))
        print("Check the following possible causes :")
        print(" - You don't have a .env file. You can copy .env.example to .env to use default")
        print(" - Mandatory variables are not defined in your .env file.")
        sys.exit("SettingsKeyError")
    except ImportError as ie:
        print("Error loading application : {}".format(str(ie)))
        print("Check the following possible causes :")
        print(" - The DJANGO_SETTINGS_MODULE defined in your .env doesn't exist")
        print(" - No DJANGO_SETTINGS_MODULE is defined and the default 'backoffice.settings.local' doesn't exist ")
        sys.exit("DjangoSettingsError")

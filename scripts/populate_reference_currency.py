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

from reference.models import currency


list_currency = [
    {'code': 'ARS', 'name': 'Argentine peso', 'symbol': '$'},
    {'code': 'BRL', 'name': 'Brazilian real', 'symbol': '‎R$'},
    {'code': 'CHF', 'name': 'Swiss franc', 'symbol': 'CHF'},
    {'code': 'EUR', 'name': 'Euro', 'symbol': '€'},
    {'code': 'GBP', 'name': 'Pound Sterling', 'symbol': '£'},
    {'code': 'JPY', 'name': 'Japanese Yen', 'symbol': '¥'},
    {'code': 'JPY', 'name': 'Japanese Yen', 'symbol': '¥'},
    {'code': 'NGN', 'name': 'Nigerian naira', 'symbol': '₦'},
    {'code': 'USD', 'name': 'United States Dollar', 'symbol': '$'},
    {'code': 'USD', 'name': 'United States Dollar', 'symbol': '$'}
]


def create_currency(name, code=None, symbol=None):
    """
    Create a currency
    :param name: name of the currency
    :param code: code of the currency (2 charaters)
    :param symbol: symbol of the currency
    :return:
    """
    if currency_exists(name):
        return None

    c = currency.Currency(name=name, code=code, symbol=symbol)
    c.save()
    return c


def currency_exists(name):
    """
    Check if a currency already exists.
    :param name: name of the currency
    :return: true if the currency already exists.
    """
    if currency.Currency.objects.filter(name=name).exists():
        return True
    return False


def add_currencies():
    """
    Add currencies to the database.
    :return:
    """
    for c in list_currency:
        create_currency(c['name'], code=c['code'], symbol=c['symbol'])




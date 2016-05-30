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

import pika
from backoffice.settings import QUEUE_URL, QUEUE_USER, QUEUE_PASSWORD, QUEUE_PORT, QUEUE_CONTEXT_ROOT
import json


def send_message(queue_name, message):
    """
    Send the message in the queue passed in parameter.

    :param queue_name: the name of the queue in which we have to send the JSON message.
    :param message: Must be a dictionnary !
    """
    credentials = pika.PlainCredentials(QUEUE_USER, QUEUE_PASSWORD)
    connection = pika.BlockingConnection(pika.ConnectionParameters(QUEUE_URL, QUEUE_PORT, QUEUE_CONTEXT_ROOT, credentials))
    channel = connection.channel()
    channel.basic_publish(exchange=queue_name,
                          routing_key='',
                          body=json.dumps(message),
                          properties=pika.BasicProperties(content_type='application/json'))
    connection.close()


def paper_sheet_queue():
    QUEUE_NAME = 'paper_sheet_queue'

    credentials = pika.PlainCredentials(QUEUE_USER, QUEUE_PASSWORD)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(QUEUE_URL, QUEUE_PORT, QUEUE_CONTEXT_ROOT, credentials))

    channel = connection.channel()

    channel.queue_declare(queue=QUEUE_NAME)


# -*- coding: utf-8 -*-
"""
Created on 2017/08/07.

Author: lasyrebel


"""

import sqlite3

import xml.dom.minidom


class TextMessage:
    """Create text object."""

    def __init__(self, **kwargs):
        """Initialize object."""
        required_fields = ['num', 'date', 'incoming', 'body']
        none_default_fields = ['chatroom', 'members']

        for key, value in kwargs.iteritems():
            print "%s = %s" % (key, value)

        for field in required_fields:
            if field not in kwargs:
                raise Exception("Required argument '%s' missing" % field)
        vars(self).update(kwargs)
        for field in none_default_fields:
            if field not in vars(self):
                vars(self)[field] = None


class SMSExporter:
    """Read SMS from Itunes backup and write them in XML file."""

    def __init__(self, connection):
        """Init method."""
        self.connection = connection

    def clean_number(self, number):
        """Test with ad."""
        if not number:
            return False
        if '@' in number:
            return number
            # allow email addresses
        stripped = ''.join(ch for ch in number if ch.isalnum())
        if not stripped.isdigit():
            return False
        return stripped[-10:]

    def export_to_disk(self):
        """Parse the db!!."""
        print ("Exporting SMS data")
        self.connection.row_factory = sqlite3.Row

        cursor = self.connection.cursor()
        handles = {}
        query = cursor.execute('SELECT ROWID, id, country FROM handle')
        for row in query:
            handles[row[0]] = (row[1], row[2], self.clean_number(row[1]))

        chats = {}
        query = cursor.execute(
            "SELECT chat.room_name, handle.id FROM chat " +
            "LEFT OUTER JOIN chat_handle_join ON " +
            "chat_handle_join.chat_id = chat.ROWID " +
            "JOIN handle ON chat_handle_join.handle_id = handle.ROWID " +
            "WHERE chat.room_name <> \"\" ")
        for row in query:
            if not row[0] in chats:
                chats[row[0]] = []
                chats[row[0]].append(row[1])
        texts = []
        query = cursor.execute(
            "SELECT message.handle_id, message.date, message.is_from_me," +
            " message.text, chat.room_name FROM message LEFT OUTER JOIN " +
            "chat_message_join ON message.ROWID = " +
            "chat_message_join.message_id " +
            "LEFT OUTER JOIN chat ON chat_message_join.chat_id = chat.ROWID " +
            "ORDER BY message.ROWID ASC")
        for row in query:
            number = handles[row[0]][0] if row[0] in handles else "unknown"
            text = TextMessage(num=number,
                               date=long((row[1] + 978307200) * 1000),
                               incoming=row[2] == 0,
                               body=row[3],
                               chatroom=row[4],
                               members=(chats[row[4]] if row[4] else None))
            # print text
            texts.append(text)

        self.write_xml(texts, "sms_backup.xml")
        return texts

    def write_xml(self, texts, outfilepath):
        """Write a Text[] to XML file."""
        doc = xml.dom.minidom.Document()
        doc.encoding = "UTF-8"
        smses = doc.createElement("smses")
        smses.setAttribute("count", str(len(texts)))
        doc.appendChild(smses)
        for txt in texts:
            sms = doc.createElement("sms")
            # toa="null" sc_toa="null" service_center="null" read="1" status="-
            # 1" locked="0" date_sent="0" readable_date="Aug 25, 2016 11:56:35
            # AM" contact_name="First Last"
            sms.setAttribute("address", str(txt.num))
            sms.setAttribute("date", str(txt.date))
            sms.setAttribute("type", str(txt.incoming + 1))
            sms.setAttribute("body", txt.body)
            # useless things:
            sms.setAttribute("read", "1")
            sms.setAttribute("protocol", "0")
            sms.setAttribute("status", "-1")
            sms.setAttribute("locked", "0")
            smses.appendChild(sms)
        print "generating xml output"
        xmlout = doc.toprettyxml(indent="  ", encoding="UTF-8")
        with open(outfilepath, 'w') as outfile:
            outfile.write(xmlout)

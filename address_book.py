#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on 2017/07/27.

Author: lasyrebel

Address book exporter in VCF file format.
"""

import datetime

import sqlite3

import vobject


class AddressBookExporter:
    """Address book exporter."""

    def __init__(self, connection):
        """Initialize the class."""
        self.connection = connection
        self.time_correction = 978310800

    def calc_birthday(self, time):
        """Calculate birthday."""
        actual_time = float(time)
        adjusted_bd = actual_time + self.correction_time

        date = datetime.date.fromtimestamp(adjusted_bd)

        return date

    def id_to_name(self, id):
        """Use phone id."""
        if id is None:
            return ''
        if id == 1 | id == 11:
            return 'Iphone'
        if id == 3:
            return 'Festnetz'
        if id == 2:
            return 'Mobil'
        if id == 4:
            return 'Arbeit'
        return ''

    def export_to_vcard(self):
        """Export to vcard."""
        print ("Exporting Address book")
        self.connection.row_factory = sqlite3.Row

        f = open('contacts.vcf', 'w')

        a_contact = self.connection.cursor()
        a_contact.execute("SELECT * FROM ABPerson ORDER BY Last,First")

        for contact in a_contact:
            last = contact['Last'] if contact['Last'] is not None else ''
            first = contact['First'] if contact['First'] is not None else ''

            v = vobject.vCard()

            v.add('n')
            v.n.value = vobject.vcard.Name(family=last, given=first)
            v.add('fn')
            v.fn.value = first + ' ' + last

            if contact['Birthday'] is not None:
                birthday = self.calc_birthday(contact['Birthday'])
                v.add('bday')
                birth_year = str(birthday.year)
                birth_month = str(birthday.month)
                birth_dat = str(birthday.day)
                v.bday.value = birth_year + '-' + birth_month + '-' + birth_dat

            email_address = self.connection.cursor()
            email_address.execute("SELECT value,label FROM ABMultiValue " +
                                  "WHERE record_id=? AND property=4 ORDER " +
                                  "BY label", (contact["ROWID"],))

            for p in email_address:
                if p['value'].find('@') > 2:
                    e = v.add('email')
                    e.value = p['value']

            # get phone numbers
            phone_info = self.connection.cursor()
            phone_info.execute("SELECT value,label FROM ABMultiValue " +
                               "WHERE record_id=? AND property" +
                               "=3 ORDER BY label", (contact["ROWID"],))
            for p in phone_info:
                t = v.add('tel')
                t.value = p['value']
                t.type_param = self.id_to_name(p['label'])

            # get addresse
            address_info = self.connection.cursor()
            address_info.execute("SELECT UID,value,label FROM ABMultiValue " +
                                 " WHERE record_id=? AND property=5 ORDER BY" +
                                 " label", (contact["ROWID"],))
            for p in address_info:
                value_entry = self.connection.cursor()
                value_entry.execute("SELECT key,value FROM ABMultiValueEntry" +
                                    " WHERE parent_id=? " +
                                    " ORDER BY key", (p["UID"],))
                addr = {0: '', 1: '', 2: '', 3: '', 4: '', 5: ''}
                for vs in value_entry:
                    addr[vs["key"]] = vs["value"]

                a = v.add('adr')
                a.value = vobject.vcard.Address(street=addr[1], code=addr[2], city=addr[3], country=addr[5])

            f.write(v.serialize())

        f.close()

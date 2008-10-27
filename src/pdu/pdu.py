# -*- coding: utf-8 -*-
# Copyright (C) 2004 Paul Hardwick paul@peck.org.uk
# Copyright (C) 2008 Warp Networks S.L.
# Copyright (C) 2008 Telefonica I+D
#
# Imported for the wader project on 5 June 2008 by Pablo Martí
# Imported for the mobile-manager on 1 Oct 2008 by Roberto Majadas
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import gsm0338

SEVENBIT_FORMAT = 0x00
EIGHTBIT_FORMAT = 0x04
UNICODE_FORMAT  = 0x08

from random import randint

class PDU :
    def __init__(self):
        self.random_id_list = range(0,255)

        i = randint(0,255)
        for x in range(0,i):
            item = self.random_id_list.pop()
            self.random_id_list.insert(0, item)
            
    #Public methods

    def encode_pdu(self, number, text, csca='', request_status=False,
                   msgref=0, msgvp=0xaa):
        """
        Returns a list of messages in PDU format

        csca = SMSC number
        request_status = True, False
        msgref = currently ignored integer 0-255
        msgvp = relative validity period as per ETSI (0xff == no validity)
        Message Encoding format defined by pduformat attribute
        SMSC can be ommited if phone can use internal defaults
        """
    
        smsc_pdu = self.__get_smsc_pdu(csca)
        sms_submit_pdu = self.__get_sms_submit_pdu(request_status, msgvp)
        tpmessref_pdu = self.__get_tpmessref_pdu(msgref)
        sms_phone_pdu = self.__get_phone_pdu(number)
        tppid_pdu = self.__get_tppid_pdu()
        sms_msg_pdu = self.__get_msg_pdu(text, msgvp)

        if len(sms_msg_pdu) == 1 :
            print "smsc_pdu : %s" % smsc_pdu
            print "sms_submit_pdu : %s" % sms_submit_pdu
            print "tpmessref_pdu : %s" % tpmessref_pdu
            print "sms_phone_pdu : %s" % sms_phone_pdu
            print "tppid_pdu : %s" % tppid_pdu
            print "sms_msg_pdu : %s" % sms_msg_pdu
            print "--------------------------------------------"
            pdu = smsc_pdu
            len_smsc = len(smsc_pdu)/2
            pdu += sms_submit_pdu
            pdu += tpmessref_pdu
            pdu += sms_phone_pdu
            pdu += tppid_pdu
            pdu += sms_msg_pdu[0]
            print pdu
            print "--------------------------------------------"
            return [((len(pdu)/2)-len_smsc, pdu.upper())]
        else:
            sms_submit_pdu = self.__get_sms_submit_pdu(request_status, msgvp, udh=True)
            pdu_list = []
            for sms_msg_pdu_item in sms_msg_pdu :
                print "smsc_pdu : %s" % smsc_pdu
                print "sms_submit_pdu : %s" % sms_submit_pdu
                print "tpmessref_pdu : %s" % tpmessref_pdu
                print "sms_phone_pdu : %s" % sms_phone_pdu
                print "tppid_pdu : %s" % tppid_pdu
                print "sms_msg_pdu : %s" % sms_msg_pdu_item
                print "--------------------------------------------"
                pdu = smsc_pdu
                len_smsc = len(smsc_pdu)/2
                pdu += sms_submit_pdu
                pdu += tpmessref_pdu
                pdu += sms_phone_pdu
                pdu += tppid_pdu
                pdu += sms_msg_pdu_item
                print pdu
                print "--------------------------------------------"
                pdu_list.append(((len(pdu)/2)-len_smsc, pdu.upper()))
            return pdu_list


    def decode_pdu(self, pdu):
        """
        Decodes a complete SMS pdu and returns a tuple strings
        sender,  # Senders number
        datestr, # GSM format date string
        msg,     # The actual msg less any header in UCS2 format
        ref,     # Msg reference  (from SMSC)
        cnt,     # Number of msg in the sequence (concat msgs)
        seq      # Sequence number of the msg (concat msgs)
        fmt      # Format of recieved msg
        """
        pdu = pdu.upper()
        ptr = 0
        #Service centre address
        smscl = int(pdu[ptr:ptr+2], 16) * 2 # number of digits
        smscertype = pdu[ptr+2:ptr+4]
        smscer = pdu[ptr+4:ptr+smscl+2]
        smscer = smscer.replace('F', '')
        smscer = list(smscer)
        for n in range(1, len(smscer), 2):
            smscer[n-1], smscer[n] = smscer[n], smscer[n-1]

        smscer = ''.join(smscer)
        if smscertype == '91':
            smscer = '+' + smscer
        csca = smscer

        ptr = ptr + 2 + smscl
        #1 byte(octet) == 2 char
        #Message type TP-MTI bits 0,1
        #More messages to send/deliver bit 2
        #Status report request indicated bit 5
        #User Data Header Indicator bit 6
        #Reply path set bit 7
        #1st octet position == smscerlen+4

        FO = int(pdu[ptr:ptr+2], 16)
        #is this a concatenated msg?
        if (FO & 0x40):
            testheader = True
        else:
            testheader = False

        ptr = ptr + 2
        sndlen = int(pdu[ptr:ptr+2], 16)
        if sndlen % 2:
            sndlen += 1
        sndtype = pdu[ptr+2:ptr+4]
        # Extract Phone number of sender
        sender = pdu[ptr+4:ptr+4+sndlen]
        sender = sender.replace('F', '')
        sender = list(sender)
        for n in range(1, len(sender), 2):
            sender[n-1], sender[n] = sender[n], sender[n-1]
        sender = ''.join(sender)
        sender = sender.strip()
        if sndtype == '91':
            sender = '+' + sender

        ptr = ptr + 4 + sndlen
        # 1byte (octet) = 2 char
        # 1 byte TP-PID (Protocol Identtifier
        PID = int(pdu[ptr:ptr+2], 16)
        ptr = ptr + 2
        # 1 byte TP-DCS (Data Coding Scheme)
        DCS = int(pdu[ptr:ptr+2], 16)
        fmt = SEVENBIT_FORMAT
        if DCS & (EIGHTBIT_FORMAT|UNICODE_FORMAT) == 0:
            fmt = SEVENBIT_FORMAT
        elif DCS & EIGHTBIT_FORMAT:
            fmt = EIGHTBIT_FORMAT
        elif DCS & UNICODE_FORMAT:
            fmt = UNICODE_FORMAT

        # Get date stamp
        ptr = ptr + 2
        date = list(pdu[ptr:ptr+14])
        for n in range(1, len(date), 2):
            date[n-1], date[n] = date[n], date[n-1]
            datestr = "%s%s/%s%s/%s%s %s%s:%s%s:%s%s" % tuple(date[0:12])

        # Now get message body
        ptr = ptr + 14
        msgl = int(pdu[ptr:ptr+2], 16)
        msg = pdu[ptr+2:]
        # check for header
        cnt = 0
        seq = 0
        ref = 0
        headlen = 0
        if testheader:
            if msg[2:4] == "00": # found header for concat message
                headlen = (int(msg[0:2], 16) + 1) * 8
                subheadlen = int(msg[4:6], 16)
                ref = int(msg[6:8], 16)
                cnt = int(msg[8:10], 16)
                seq = int(msg[10:12], 16)
                if fmt == SEVENBIT_FORMAT:
                    while headlen % 7:
                        headlen += 1
                    headlen = headlen / 7

        if fmt == SEVENBIT_FORMAT:
            msg = self.__unpack_msg(msg)[headlen:msgl]
            msg = msg.decode("gsm0338")

        elif fmt == EIGHTBIT_FORMAT:
            msg = ''.join([chr(int(msg[x:x+2], 16))
                                    for x in range(0, len(msg), 2)])
            msg = unicode(msg[headlen:], 'latin-1')

        elif fmt == UNICODE_FORMAT:
            msg = u''.join([unichr(int(msg[x:x+4], 16))
                            for x in range(0, len(msg), 4)])

        return sender, datestr, msg.strip(), csca, ref, cnt, seq, fmt

    #Private methods

    def __get_smsc_pdu (self, number):
        if not len(number.strip()):
            return chr(0)
        number = self.__clean_number(number)
        ptype = 129
        if number[0] == '+':
            number = number[1:]
            ptype = 145
        if len(number) % 2:
            number = number + 'F'
        ps = chr(ptype)
        for n in range(0, len(number), 2):
            num = number[n+1] + number[n]
            ps = ps + chr(int(num, 16))
        pl = len(ps)
        ps = chr(pl) + ps

        ret_ps = ''.join(["%02x" % ord(n) for n in ps])
        return ret_ps

    def __get_tpmessref_pdu(self, msgref):
        tpmessref = msgref & 0xFF
        ret_tpmessref = ''.join(["%02x" % ord(n) for n in chr(tpmessref)])
        return ret_tpmessref

    def __get_phone_pdu(self, number):
        number = self.__clean_number(number)
        ptype = 129
        if number[0] == '+':
            number = number[1:]
            ptype = 145
        pl = len(number)
        if len(number) % 2:
            number = number + 'F'
        ps = chr(ptype)
        for n in range(0, len(number), 2):
            num = number[n+1] + number[n]
            ps = ps + chr(int(num, 16))

        ps = chr(pl) + ps

        ret_ps = ''.join(["%02x" % ord(n) for n in ps])
        return ret_ps
    

    def __clean_number(self, number):
        number = number.strip()
        number = number.replace(' ', '')
        return number

    def __get_tppid_pdu(self):
        tppid = 0x00
        ret_tppid = ''.join(["%02x" % ord(n) for n in chr(tppid)])
        return ret_tppid

    def __get_sms_submit_pdu(self, request_status, msgvp, udh=False):
        sms_submit = None
        if not request_status:
            sms_submit = 0x01
        else:
            sms_submit = 0x21
        
        if msgvp != 0xFF:
            sms_submit = sms_submit | 0x10

        if udh :
            sms_submit = sms_submit | 0x40
            
        ret_sms_submit = ''.join(["%02x" % ord(n) for n in chr(sms_submit)])
        return ret_sms_submit
        

    def __get_msg_pdu(self, text, msgvp):        
        #Data coding Scheme
        data_coding_scheme = ""
        if gsm0338.is_valid_gsm_text(text):
            text_format = SEVENBIT_FORMAT
            data_coding_scheme = 0x00 | SEVENBIT_FORMAT
        else:
            text_format = UNICODE_FORMAT
            data_coding_scheme = 0x00 | UNICODE_FORMAT

        data_coding_scheme_pdu = ''.join(["%02x" % ord(n) for n in chr(data_coding_scheme)])

        #Validity period
        valid_period = msgvp & 0xFF
        valid_period_pdu = ''.join(["%02x" % ord(n) for n in chr(valid_period)])

        #UDL + UD
        message_pdu = ""
        
        if text_format == SEVENBIT_FORMAT :
            if len(text) <= 160 :
                print "GSM0338 (len %s)" % len(text)
                message_pdu = [self.__pack_8bits_to_7bits(text)]
            else:
                print "GSM0338 (len %s multipart)" % len(text)
                message_pdu = self.__split_sms_message(text, encoding=SEVENBIT_FORMAT,
                                                       limit=160)
        else:
            if len(text) <= 70 :
                print "UNICODE (len %s)" % len(text)
                message_pdu = [self.__pack_8bits_to_ucs2(text)]
                
            else:
                print "UNICODE (len %s)" % len(text)
                message_pdu = self.__split_sms_message(text, encoding=UNICODE_FORMAT,
                                                       limit=70)

        ret_msgs_list = []

        for msg in message_pdu :
            ret_msgs_list.append(data_coding_scheme_pdu + valid_period_pdu + msg)

        return ret_msgs_list
    
    def __pack_8bits_to_ucs2(self, message, udh=None):
        #FIXME : ESTO NO CONTROLA EN TAMAÑO EN BASE AL UDH        
        text = message
        nmesg = ''
        for n in text:
            nmesg += chr(ord(n) >> 8) + chr(ord(n) & 0xFF)
        mlen = len(text) * 2
        if udh == None:
            message= chr(mlen) + nmesg
        else:
            message= chr(mlen) + udh + nmesg
            
        message_pdu = ''.join(["%02x" % ord(n) for n in message])
        return message_pdu
    
    def __pack_8bits_to_7bits(self, message, udh=None):
        pdu = ""
        txt = message.encode("gsm0338")
        
        if udh == None:
            tl = len(txt)
            txt += '\x00'
            msgl = len(txt)*7/8
            op = [-1] * msgl
            c = 0
            shift = 0
            for n in range(msgl):
                if shift == 6:
                    c = c + 1        

                shift = n % 7
                lb = ord(txt[c]) >> shift
                hb = (ord(txt[c+1]) << (7-shift) & 255)
                op[n] = lb + hb
                c += 1
            pdu = chr(tl) + ''.join([chr(x) for x in op])
        else:
            txt = "\x00\x00\x00\x00\x00\x00" + txt
            tl = len(txt)

            txt += '\x00'
            msgl = len(txt)*7/8
            op = [-1] * msgl
            c = 0
            shift = 0
            for n in range(msgl):
                if shift == 6:
                    c = c + 1        

                shift = n % 7
                lb = ord(txt[c]) >> shift
                hb = (ord(txt[c+1]) << (7-shift) & 255)
                op[n] = lb + hb
                c += 1

            i=0
            for char in udh :
                op[i] = ord(char)
                i = i + 1

            pdu = chr(tl) + ''.join([chr(x) for x in op])
            
            
        ret_pdu = ''.join(["%02x" % ord(n) for n in pdu])
        return ret_pdu
                

    def __split_sms_message(self, text, encoding=SEVENBIT_FORMAT, limit=160):
        len_without_udh = limit - 7
        msgs = []
        total_len = len(text)
        pi=0
        pe=len_without_udh
        while pi < total_len :
            msgs.append(text[pi:pe])
            pi=pe
            pe=pe+len_without_udh

        packing_func = None
        if encoding == SEVENBIT_FORMAT:
            packing_func = self.__pack_8bits_to_7bits
        else:
            packing_func = self.__pack_8bits_to_ucs2

        pdu_msgs = []

        i = 1
        udh_len = 0x05
        mid = 0x00
        data_len = 0x03
        csms_ref = self.__get_rand_id()
        
        for msg in msgs :
            total_parts = len(msgs)            
            udh = chr(udh_len) + chr(mid) + chr(data_len) + chr(csms_ref) + chr(total_parts) + chr(i)
            pdu_msgs.append(packing_func(" "+msg, udh))
            i=i+1
            
        return pdu_msgs

    def __unpack_msg(self, pdu, limit=160):
        """
        Unpacks C{pdu} into 7-bit characters and returns the decoded string
        """
        # Taken/modified from Dave Berkeley's pysms package
        count = 0
        last = 0
        result = []
        for i in range(0, len(pdu), 2):
            byte = int(pdu[i:i+2], 16)
            mask = 0x7F >> count
            out = ((byte & mask) << count) + last
            last = byte >> (7 - count)
            result.append(chr(out))
            if limit and (len(result) >= limit):
                break
            if count == 6:
                result.append(chr(last))
                last = 0

            count = (count + 1) % 7
        return ''.join(result)

    def __get_rand_id(self):
        rid = self.random_id_list.pop()
        self.random_id_list.insert(0, rid)
        return rid

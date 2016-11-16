#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import random
import string
from Crypto.Cipher import AES

from loki.app import settings


def AES_encrypt(value):
    cipher = AES.new(settings.AUTH_AES_KEY, AES.MODE_CFB, settings.AUTH_AES_IV)
    return cipher.encrypt(value)


def AES_decrypt(ciphertext):
    cipher = AES.new(settings.AUTH_AES_KEY, AES.MODE_CFB, settings.AUTH_AES_IV)
    return cipher.decrypt(ciphertext)


def random_padding(value, digit):
    return value + ''.join(
        random.choice(string.ascii_letters)
        for i in xrange(digit - len(value)))


_inner_prefix = 'TK'


def encrypt_token(value):
    token = random_padding("{}{}_".format(_inner_prefix, value), 15)
    signed_token = base64.b64encode(AES_encrypt(token))
    prefixed_token = "%s%s" % (settings.AUTH_TOKEN_PREFIX, signed_token)
    return prefixed_token


def decrypt_token(token, prefix):
    if token and token.startswith(prefix):
        signed_token = token.replace(prefix, '')
        decrypted_value = AES_decrypt(base64.b64decode(signed_token))
        if decrypted_value.startswith(_inner_prefix):
            return decrypted_value
        else:
            return None
    else:
        return None

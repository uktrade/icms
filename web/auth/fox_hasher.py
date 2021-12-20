"""
Customised password hasher to match legacy icms password encryption for
migrated users.

Hashing algorith is PBKDF2 with SHA1 digest, but salt generation is altered to
match legacy applications salt geheration.
"""
import binascii
import hmac
import os
import struct

from django.contrib.auth.hashers import PBKDF2SHA1PasswordHasher


class FOXPBKDF2SHA1Hasher(PBKDF2SHA1PasswordHasher):
    """
    A subclass of PBKDF2SHA1PasswordHasher that iterates 10000 times as legacy
    ICMS app
    """

    algorithm = "fox_pbkdf2_sha1"
    iterations = 10000

    def encrypt(self, password, salt, iters, keylen, digestmod):
        """Run the PBKDF2 (Password-Based Key Derivation Function 2) algorithm
        and return the derived key. The arguments are:

        password (bytes or bytearray) -- the input password
        salt (bytes or bytearray) -- a cryptographic salt
        iters (int) -- number of iterations
        keylen (int) -- length of key to derive
        digestmod -- a cryptographic hash function: either a module
            supporting PEP 247, a hashlib constructor, or (in Python 3.4
            or later) the name of a hash function.

        For example:

        >>> import hashlib
        >>> from binascii import hexlify, unhexlify
        >>> password = b'Squeamish Ossifrage'
        >>> salt = unhexlify(b'1234567878563412')
        >>> hexlify(pbkdf2(password, salt, 500, 16, hashlib.sha1))
        b'9e8f1072bdf5ef042bd988c7da83e43b' # /PS-IGNORE

        """
        h = hmac.new(password, digestmod=digestmod)

        def prf(data):
            hm = h.copy()
            hm.update(data)
            return bytearray(hm.digest())

        key = bytearray()
        i = 1
        while len(key) < keylen:
            T = U = prf(salt + struct.pack(">i", i))
            for _ in range(iters - 1):
                U = prf(U)
                T = bytearray(x ^ y for x, y in zip(T, U))
            key += T
            i += 1

        return key[:keylen].hex().upper()

    def salt(self):
        """
        Generate an 8 byte salt value and return as hex string
        """
        return binascii.hexlify(os.urandom(8)).decode().upper()

    def encode(self, password, salt, iterations=None):
        assert password is not None
        iterations = iterations or self.iterations
        id_salt_pair = salt.split(":")
        id = id_salt_pair[0]
        base_salt = id_salt_pair[1]
        password_bytes = bytearray(id + password, "utf-8")
        salt_bytes = bytearray.fromhex(base_salt)
        hash = self.encrypt(password_bytes, salt_bytes, iterations, 16, "sha1")
        return "%s$%d$%s$%s" % (self.algorithm, iterations, salt, hash)

    def harden_runtime(self, password, encoded):
        pass

from struct import pack
from jawa.attribute import Attribute
from jawa.constants import UTF8


class SignatureAttribute(Attribute):
    ADDED_IN = '5.0.0'
    MINIMUM_CLASS_VERSION = (49, 0)

    def __init__(self, table, name_index=None):
        super(SignatureAttribute, self).__init__(
            table,
            name_index or UTF8(
                pool=table.cf.constants,
                value='Signature'
            ).index
        )
        self._signature_index = None

    def unpack(self, info):
        self._signature_index = info.u2()

    def pack(self):
        return pack('>H', self._signature_index)

    @property
    def signature(self):
        return self.cf.constants[self._signature_index]

    @signature.setter
    def signature(self, value):
        self._signature_index = value.index

"""
ClassFile reader & writer.

The :mod:`lawu.cf` module provides tools for working with JVM ``.class``
ClassFiles.
"""
from itertools import repeat
from typing import BinaryIO, Callable, Iterator, Optional
from struct import unpack

from lawu import ast
from lawu import constants as consts
from lawu.attribute import read_attribute_table


class MethodTable:
    def __init__(self, root):
        """Proxy over the ClassFile's methods to add some convience methods.
        """
        self._root = root

    def find(self, *, name: str = None, args: str = None, returns: str = None,
             f: Callable = None) -> Iterator[ast.Method]:
        """
        Iterates over the methods table, yielding each matching method. Calling
        without any arguments is equivalent to iterating over the table. For
        example, to get all methods that take three integers and return void::

            for method in cf.methods.find(args='III', returns='V'):
                print(method.name.value)

        Or to get all private methods::

            is_private = lambda m: m.access_flags.acc_private
            for method in cf.methods.find(f=is_private):
                print(method.name.value)

        :param name: The name of the method(s) to find.
        :param args: The arguments descriptor (ex: ``III``)
        :param returns: The returns descriptor (Ex: ``V``)
        :param f: Any callable which takes one argument (the method).
        """
        for method in self._root.find(name='method'):
            if name is not None and method.name != name:
                continue

            descriptor = method.descriptor
            end_para = descriptor.find(')')

            m_args = descriptor[1:end_para]
            if args is not None and args != m_args:
                continue

            m_returns = descriptor[end_para + 1:]
            if returns is not None and returns != m_returns:
                continue

            if f is not None and not f(method):
                continue

            yield method

    def find_one(self, **kwargs) -> Optional[ast.Method]:
        """
        Same as ``find()`` but returns only the first result.
        """
        return next(self.find(**kwargs), None)


class ClassFile:
    #: The JVM ClassFile magic number.
    MAGIC = 0xCAFEBABE

    def __init__(self, source: BinaryIO = None, *, loader=None):
        self.node = ast.Class(
            descriptor=None,
            access_flags=ast.Class.AccessFlags.PUBLIC,
            children=[
                ast.Bytecode(major=0x33, minor=0x00),
                ast.Super(descriptor='java/lang/Object')
            ]
        )

        if source:
            self._load_from_io(source)

        self.methods = MethodTable(self.node)

    def _load_from_io(self, source: BinaryIO):
        """Given a file-like object parse a binary JVM ClassFile into the Lawu
        internal AST model.

        :param source: Any file-like object implementing `read()`.
        """
        read = source.read

        if unpack('>I', read(4))[0] != ClassFile.MAGIC:
            raise ValueError('invalid magic number')

        version = unpack('>HH', read(4))
        v = self.node.find_one(name='bytecode')
        v.major = version[1]
        v.minor = version[0]

        pool = consts.ConstantPool()
        pool.unpack(source)

        flags, this, super_, if_count = unpack('>HHHH', read(8))
        self.access_flags = ast.Class.AccessFlags(flags)
        self.this = pool[this].name.value
        self.super_ = pool[super_].name.value

        self.node.extend(
            ast.Implements(
                descriptor=pool[if_idx].name.value
            )
            for if_idx in unpack(f'>{if_count}H', read(2 * if_count))
        )

        for _ in repeat(None, unpack('>H', read(2))[0]):
            flags, name, descriptor = unpack('>HHH', read(6))
            self.node += ast.Field(
                name=pool[name].value,
                descriptor=pool[descriptor].value,
                access_flags=ast.Field.AccessFlags(flags),
                children=list(read_attribute_table(pool, source))
            )

        for _ in repeat(None, unpack('>H', read(2))[0]):
            flags, name, descriptor = unpack('>HHH', read(6))
            self.node += ast.Method(
                name=pool[name].value,
                descriptor=pool[descriptor].value,
                access_flags=ast.Method.AccessFlags(flags),
                children=list(read_attribute_table(pool, source))
            )

    @property
    def this(self):
        return self.node.descriptor

    @this.setter
    def this(self, value):
        self.node.descriptor = value

    @property
    def super_(self):
        return self.node.find_one(name='super').descriptor

    @super_.setter
    def super_(self, value):
        self.node.find_one(name='super').descriptor = value

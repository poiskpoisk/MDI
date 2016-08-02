# -*- coding: utf-8 -*-#
__author__ = 'AMA'

import myABC
from mixin import ParseMixin

# Композитные классы объединяющие в себе интерфейсы, через АБС и инструментарий через вкрапления

class ReadWriteECU( ParseMixin.ReadWriteECU, myABC.ReadWriteECUcal ):
    pass

class ReadECU ( ParseMixin.ReadECU, myABC.ReadECUcal ):
    pass

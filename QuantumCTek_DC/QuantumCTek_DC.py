#!/usr/bin/env python

import InstrumentDriver
import numpy as np
import sys
from pathlib import Path
sys.path.append(str((Path(__file__).parents[1]/'QuantumCTek'/'lib').resolve()))
import device_interface

dev = device_interface.DeviceInterface()
PORT = 5000

class Driver(InstrumentDriver.InstrumentWorker):
    """ This class implements the QuantumCTek AWG driver"""

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        pass

    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        pass

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        n = int(quant.name[-1])
        ret = dev.dc_set(self.comCfg.name, self.comCfg.address, PORT, n, ('VOLT', value))
        if ret != 0:
            raise Exception(f"Error setting value. dc board:[{self.comCfg.name}], ret:[{ret}]")
        return value

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        n = int(quant.name[-1])
        ret, value = dev.dc_query(self.comCfg.name, self.comCfg.address, PORT, n, 'VOLT')
        if ret != 0:
            raise Exception(f"Error getting value. dc board:[{self.comCfg.name}], ret:[{ret}]")
        return value

    
if __name__ == '__main__':
    pass

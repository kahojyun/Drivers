#!/usr/bin/env python

import InstrumentDriver
import numpy as np
import sys
sys.path.append(r'C:\Users\universe\Labber\Drivers\QuantumCTek\lib')
import device_interface
import write_configuration as CONST

dev = device_interface.DeviceInterface()

class Driver(InstrumentDriver.InstrumentWorker):
    """ This class implements the QuantumCTek AWG driver"""

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        server_mac = self.getValue('Host MAC address')
        ad_mac = self.comCfg.address
        ret = 0
        self.log(f'host: {server_mac}, ad: {ad_mac}')
        ret |= dev.ad_connect_device(self.comCfg.name, server_mac, ad_mac)
        ret |= dev.ad_init_device(self.comCfg.name)
        if ret != 0:
            raise Exception(f'ad board:[{self.comCfg.name}] connect or init failure, ret:[{ret}]')
        self.signal_index = {'Averaged wave I': 1, 'Averaged wave Q': 2}
        for i in range(CONST.MAX_FREQS):
            self.signal_index[f'Result Vector #{i+1}'] = i
            self.signal_index[f'Averaged #{i+1}'] = i

    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        # close VISA connection
        _ = dev.ad_disconnect_device(self.comCfg.name)


    def _setValue(self, _func, *args):
        """Call API and check returned value"""
        ret = _func(*args)
        if isinstance(ret, tuple):
            code = ret[0]
        else:
            code = ret
        if code != 0:
            raise Exception(f'Error when calling {_func}: da board:[{self.comCfg.name}], ret:[{code}]')
        return ret


    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        if (quant.name in ('Sample depth', 'Trigger count') or
            quant.name.startswith('Window start') or
            quant.name.startswith('Window width')):
            value = int(value)
        return value

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        if quant.name in self.signal_index.keys():
            if self.isFirstCall(options):
                self.data = self._setValue(dev.ad_receive_data, self.comCfg.name)
                self.log(f'data: {self.data}')
            if quant.name == 'Averaged wave I':
                value = quant.getTraceDict(self.normalize_AD_value(np.mean(self.data[1], axis=0)), dx=1e-9)
            elif quant.name == 'Averaged wave Q':
                value = quant.getTraceDict(self.normalize_AD_value(np.mean(self.data[2], axis=0)), dx=1e-9)
            else:
                if self.getValue('Uniform window setting'):
                    window_len = self.getValue('Window width')
                else:
                    window_len = self.getValue(f'Window width #{quant.name[-1]}')
                i = self.signal_index[quant.name]
                if quant.name.startswith('Result Vector'):
                    value = quant.getTraceDict((self.normalize_AD_value(self.data[1][:,i])+1j*self.normalize_AD_value(self.data[2][:,i]))/window_len)
                elif quant.name.startswith('Averaged #'):
                    value = np.mean(self.normalize_AD_value(self.data[1][:,i])+1j*self.normalize_AD_value(self.data[2][:,i]))/window_len
        else:
            # Unable to get configuaration from board. Return stored values.
            value = quant.getValue()
        return value

    def performArm(self, quant_names, options={}):
        """Perform the instrument arm operation"""
        if not np.any([name in self.signal_index.keys() for name in quant_names]):
            return
        mode = int(self.getValue('Demodulation'))
        self._setValue(dev.ad_clear_wincap_data, self.comCfg.name)
        self._setValue(dev.ad_set_mode, self.comCfg.name, mode)
        self._setValue(dev.ad_set_sample_depth, self.comCfg.name, int(self.getValue('Sample depth')))
        self._setValue(dev.ad_set_trigger_count, self.comCfg.name, int(self.getValue('Trigger count')))
        if self.getValue('Demodulation'):
            n = int(self.getValue('Number of freqs'))
            for i in range(n):
                if self.getValue('Uniform window setting'):
                    self._setValue(dev.ad_set_window_start, self.comCfg.name, int(self.getValue('Window start')))
                    self._setValue(dev.ad_set_window_width, self.comCfg.name, int(self.getValue('Window width')))
                else:
                    self._setValue(dev.ad_set_window_start, self.comCfg.name, int(self.getValue(f'Window start #{i+1}')))
                    self._setValue(dev.ad_set_window_width, self.comCfg.name, int(self.getValue(f'Window width #{i+1}')))
                self._setValue(dev.ad_set_demod_freq, self.comCfg.name, self.getValue(f'Demod freq #{i+1}'))
                self._setValue(dev.ad_commit_demod_set, self.comCfg.name, i)
        self._setValue(dev.ad_enable_adc, self.comCfg.name)

    def normalize_AD_value(self,raw_value):
        return (raw_value-127.5)/127.5*0.25

if __name__ == '__main__':
    pass

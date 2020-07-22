#!/usr/bin/env python

import time

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
        gains = [
            int(self.getValue(f'Channel gain #{i+1}'))
            for i in range(CONST.MAX_CHANNELS)]
        offsets = [
            int(self.getValue(f'Channel default voltage #{i+1}'))
            for i in range(CONST.MAX_CHANNELS)]
        ret = 0
        ret |= dev.da_connect_device(self.comCfg.name, self.comCfg.address, gains, offsets)
        ret |= dev.da_init_device(self.comCfg.name)
        if ret != 0:
            raise Exception(f'da board:[{self.comCfg.name}] connect or init failure, ret:[{ret}]')
        self.initSetConfig()

    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        _ = dev.da_disconnect_device(self.comCfg.name)


    def initSetConfig(self):
        """This function is run before setting values in Set Config"""
        self.old_waveform = [None] * CONST.MAX_CHANNELS
        self.update_waveform = [False] * CONST.MAX_CHANNELS
        # Clear old waveforms
        for i in range(CONST.MAX_CHANNELS):
            mode = 0
            self._setValue(dev.da_write_wave, [0], self.comCfg.name, f'Z{i+1}', 'i', mode, 0)

    def _setValue(self, _func, *args):
        """Call API and check returned value"""
        ret = _func(*args)
        if ret != 0:
            raise Exception(f'Error when calling {_func}: da board:[{self.comCfg.name}], ret:[{ret}]')

    def _rescale(self, n, waveform):
        """Rescale and clip waveform for channel n, raise an error if clipping is not allowed."""
        offset1 = int(self.getValue(f'Channel default voltage #{n}'))
        offset2 = int(self.getValue(f'Data offset #{n}'))
        code_max = 32767 - offset1 - offset2
        code_min = -32768 - offset1 - offset2
        scaled_v = np.array(np.round(65535/2*waveform), dtype=int)
        if not self.getValue(f'Allow clipping #{n}'):
            if np.any(scaled_v > code_max) or np.any(scaled_v < code_min):
                raise Exception(f'Waveform #{n} overflows. Input range is {code_min/65535*2:f} -- {code_max/65535*2:f}.')
        else:
            scaled_v = np.clip(scaled_v, code_min, code_max)
        return scaled_v

    def _upload_waveform(self):
        """Upload waveform and enable output"""
        self._setValue(dev.da_stop_output_wave, self.comCfg.name, 0)
        for i in range(CONST.MAX_CHANNELS):
            if self.update_waveform[i] and (self.old_waveform[i] is not None):
                scaled_v = self._rescale(i+1, self.old_waveform[i])
                mode = 1 if self.getValue(f'Continuous output #{i+1}') else 0
                self._setValue(dev.da_write_wave, scaled_v, self.comCfg.name, f'Z{i+1}', 'i', mode, 0)
            self.update_waveform[i] = False
        self._setValue(dev.da_start_output_wave, self.comCfg.name, 0)

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        # if self.isFirstCall(options):
        #     # if not self.isHardwareTrig(options):
        #     #     # single board mode
        #     #     self._setValue(dev.set_multi_board, self.comCfg.name, 0)
        #     # else:
        #     # multi board mode
        #     # self._setValue(dev.set_multi_board, self.comCfg.name, 0)
        if quant.name == 'Trigger delay':
            self._setValue(dev.da_set_trigger_delay, self.comCfg.name, value)
        elif quant.name == 'Output delay':
            self._setValue(dev.da_set_da_output_delay, self.comCfg.name, value)
        elif quant.name == 'Trigger interval':
            self._setValue(dev.da_set_trigger_interval_l1, self.comCfg.name, value)
        elif quant.name == 'Trigger count':
            value = int(round(value))
            self._setValue(dev.da_set_trigger_count_l1, self.comCfg.name, value)
        elif quant.name == 'Run AWG':
            if value:
                interval = self.getValue('Trigger interval')
                n = self.getValue('Trigger count')
                self._setValue(dev.da_trigger_enable, self.comCfg.name)
                # Wait output before receiving data
                time.sleep(n*interval + 0.001)
            # else:
            #     # stop all channel
            #     self._setValue(dev.da_stop_output_wave, self.comCfg.name, 0)
        elif quant.name.startswith('Channel default voltage'):
            # n = int(quant.name[-1])
            # self._setValue(dev.da_set_channel_default_voltage, self.comCfg.name, f'Z{n}', 32768-value)
            value = quant.getValue()
        elif quant.name.startswith('Channel gain'):
            # n = int(quant.name[-1])
            # self._setValue(dev.da_set_channel_gain, self.comCfg.name, f'Z{n}', value)
            value = quant.getValue()
        elif quant.name.startswith('Data offset'):
            n = int(quant.name[-1])
            # self._setValue(dev.da_set_data_offset, self.comCfg.name, f'Z{n}', int(round(value*32768)))
            self._setValue(dev.da_set_channel_default_voltage, self.comCfg.name, f'Z{n}', 32767-value)
            if self.old_waveform[n-1] is not None:
                self.update_waveform[n-1] = True
        elif quant.name.startswith('Waveform'):
            n = int(quant.name[-1])
            if ((self.old_waveform[n-1] is None) or
                (len(self.old_waveform[n-1]) != len(value['y'])) or
                np.any(self.old_waveform[n-1] != value['y'])):
                    self.old_waveform[n-1] = value['y']
                    self.update_waveform[n-1] = True
        elif quant.name.startswith('Continuous output'):
            n = int(quant.name[-1])
            if self.old_waveform[n-1] is not None:
                self.update_waveform[n-1] = True
        if self.isFinalCall(options):
            if np.any(self.update_waveform):
                self._upload_waveform()
            # run awg if not hardware triggered
            # if not self.isHardwareTrig(options):
            #     self._setValue(dev.da_trigger_enable, self.comCfg.name)
        return value

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        value = quant.getValue()
        return value

    
if __name__ == '__main__':
    pass

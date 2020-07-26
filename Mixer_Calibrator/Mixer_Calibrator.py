import InstrumentDriver
import numpy as np
from scipy import signal

import write_configuration as CONST

class Driver(InstrumentDriver.InstrumentWorker):
    """ This class implements an IQ calibrator driver"""
    

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        pass


    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        pass


    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        if quant.name == 'Number of points':
            value = int(round(value))
        quant.setValue(value)
        if self.isFinalCall(options):
            # validate input
            freq = self.getValue('Frequency')
            n_pts = self.getValue('Number of points')
            freq_res = freq / n_pts
            freq = round(freq/freq_res)*freq_res
            self.setValue('Frequency', freq)
        return value


    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        # proceed depending on quantity
        if quant.name.startswith('Waveform out'):
            if self.isFirstCall(options):
                # calculate waveform
                i, q, q_delayed = self._get_waveform()
                # apply calibration
                ratio = 10**(self.getValue('Gain imbalance')/20)
                skew = self.getValue('Phase skew') * np.pi/180
                self.waveform_i = ratio*(i + q*np.tan(skew))
                self.waveform_q = q_delayed / np.cos(skew)
                if self.getValue('Calibrate offset'):
                    self.waveform_i += self.getValue('I offset')
                    self.waveform_q += self.getValue('Q offset')
            sample_rate = self.getValue('Sample rate')
            if quant.name[-1] == 'I':
                trace = quant.getTraceDict(self.waveform_i, t0=0.0, dt=1/sample_rate)
            else:
                trace = quant.getTraceDict(self.waveform_q, t0=0.0, dt=1/sample_rate)
            return trace
        else:
            return quant.getValue()

    def _get_waveform(self):
        """Get waveform and apply time shift.
        
        Return
        ------
        (i, q, q_delayed)
        """
        sample_rate = self.getValue('Sample rate')
        delay = self.getValue('Q delay')
        mode = self.getValue('Mode')
        if mode == CONST.MODE_GEN:
            # generate continous waveform
            freq = self.getValue('Frequency')
            amp = self.getValue('Amplitude')
            n_pts = int(round(self.getValue('Number of points')))
            t = np.arange(n_pts) / sample_rate
            if self.getValue('Swap IQ'):
                i = amp*np.cos(2*np.pi*freq*t)
                q = amp*np.sin(2*np.pi*freq*t)
                q_delayed = amp*np.sin(2*np.pi*freq*(t-delay))
            else:
                i = amp*np.sin(2*np.pi*freq*t)
                q = amp*np.cos(2*np.pi*freq*t)
                q_delayed = amp*np.cos(2*np.pi*freq*(t-delay))
        else:
            i = self.getValueArray('Waveform in - I')
            q = self.getValueArray('Waveform in - Q')
            if len(i)==0 or len(q)==0:
                q_delayed = np.array([])
            else:
                # ssb_freq = self.getValue('Sideband frequency')
                # if ssb_freq != 0:
                #     iq = i + 1j*q
                #     iq *= np.exp(-1j*)
                # interpolation
                c_coef = signal.cspline1d(q)
                x = np.arange(len(q))
                q_delayed = signal.cspline1d_eval(c_coef, x-delay*sample_rate)
        return (i, q, q_delayed)


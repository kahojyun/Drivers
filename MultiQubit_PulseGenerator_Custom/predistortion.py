#!/usr/bin/env python3

# Note from/to Dan. This driver appears to take a premade transfer function for
# each mixer. The trick is then to load in the transfer function and perform the
# actual predistortion. We therefore need to find the correct transfer function
# and save this transfer function to file. These transfer functions need to be
# saved as Transfer function #1, etc.

# The predistoriton program as it stands only produces the transfer function of
# one mixer at a time. A challenge will be finding a good way to add the
# transfer functions to a common file in a convenient way.

import cmath


import numpy as np
from numpy.fft import fft, fftfreq, fftshift, ifft, ifftshift
from scipy.interpolate import interp1d
import scipy.signal as signal


import write_configuration as CONST


class Predistortion(object):
    """This class is used to predistort I/Q waveforms for qubit XY control."""

    def __init__(self, waveform_number=0):
        # define variables
        self.transfer_path = ''
        # keep track of which Labber waveform this predistortion refers to
        self.waveform_number = waveform_number
        # TODO(dan): define variables for predistortion algorithm

    def set_parameters(self, config={}):
        """Set base parameters using config from from Labber driver.

        Parameters
        ----------
        config : dict
            Configuration as defined by Labber driver configuration window

        """
        # Labber configuration contains multiple predistortions, get right one
        path = config.get('Transfer function #%d' % (self.waveform_number + 1))
        # only reload tranfser function if file changed
        if path != self.transfer_path:
            self.import_transfer_function(path)

        self.dt = 1 / config.get('Sample rate')

    def import_transfer_function(self, path):
        """Import transfer function data.

        Parameters
        ----------
        path : str
            Path to file containing transfer function data

        """
        # store new path
        self.transfer_path = path

        # return directly if not in use, look for both '' and '.'
        if self.transfer_path.strip() in ('', '.'):
            return
        import Labber
        f = Labber.LogFile(self.transfer_path)
        self.vResponse_freqs, self.vFilteredResponse_FFT_I = f.getTraceXY(
            y_channel=0)
        self.vResponse_freqs, self.vFilteredResponse_FFT_Q = f.getTraceXY(
            y_channel=1)
        # TODO(dan): load transfer function data

    def predistort(self, waveform):
        """Predistort input waveform.

        Parameters
        ----------
        waveform : complex numpy array
            Waveform data to be pre-distorted

        Returns
        -------
        waveform : complex numpy array
            Pre-distorted waveform

        """
        # find timespan of waveform
        self.tvals = np.arange(0, self.dt * len(waveform), self.dt)

        response_I = ifft(ifftshift(self.vFilteredResponse_FFT_I))
        response_FFT_I_r = fftshift(fft(complex(1, 0) * response_I.real))
        response_FFT_I_i = fftshift(fft(complex(1, 0) * response_I.imag))

        response_Q = ifft(ifftshift(self.vFilteredResponse_FFT_Q))
        response_FFT_Q_r = fftshift(fft(complex(1, 0) * response_Q.real))
        response_FFT_Q_i = fftshift(fft(complex(1, 0) * response_Q.imag))

        # {{a, b},{c, d}}, determinant is ad-bc, plus sign comes from
        # additional i tacked on to the Q by the IQ mixer.
        # I removed this factor of i from the FFT of the response function.
        determinant = response_FFT_I_r * response_FFT_Q_i - \
            response_FFT_Q_r * response_FFT_I_i

        Za = response_FFT_Q_i / determinant
        Zb = -response_FFT_Q_r / determinant
        Zc = -response_FFT_I_i / determinant
        Zd = response_FFT_I_r / determinant

        Inverse_A = interp1d(self.vResponse_freqs, Za)
        Inverse_B = interp1d(self.vResponse_freqs, Zb)
        Inverse_C = interp1d(self.vResponse_freqs, Zc)
        Inverse_D = interp1d(self.vResponse_freqs, Zd)

        # applies the interpolated inverse function to the AWG signal

        fft_vals, fft_signal_r = self.apply_FFT(
            self.tvals, complex(1, 0) * waveform.real)
        fft_vals, fft_signal_i = self.apply_FFT(
            self.tvals, complex(1, 0) * waveform.imag)

        fft_signal = (fft_signal_r * Inverse_A(fft_vals) + fft_signal_i *
                      Inverse_B(fft_vals) + 1j *
                      (fft_signal_r * Inverse_C(fft_vals) +
                       fft_signal_i * Inverse_D(fft_vals)))
        corr_signal = ifft(ifftshift(fft_signal))

        vI = np.array(corr_signal.real, dtype='float64')
        vQ = np.array(corr_signal.imag, dtype='float64')

        return vI + 1j * vQ

    def apply_FFT(self, tvals, signal):
        fft_signal = fftshift(fft(signal))
        fft_vals = fftshift(fftfreq(len(signal), tvals[1] - tvals[0]))
        return fft_vals, fft_signal


class Filter:
    r"""Filter signal with an IIR filters and a FIR filter.
    
    The IIR filter is constucted from continous time transfer function in
    zero-pole-gain form.

    Parameters
    ----------
    fs : float
        Sample rate
    z : array_like
    p : array_like
    k : float
        zeros, poles and gain of the IIR filter
    F : array_like, optional
        Coefficients for FIR filter
    gain : :obj:`float`, optional
    offset : :obj:`float`, optional
        Gain and offset of input signal. The signal actually input to filter is
        `(data-offset)/gain`
    """
    F = None
    gain = 1
    offset = 0
    
    def __init__(self, fs, z, p, k, F=None, gain=1, offset=0):
        self.fs = fs
        self.z = np.array(z)
        self.p = np.array(p)
        self.k = k
        if F is not None:
            self.F = np.array(F, dtype='f8')
        self.gain = gain
        self.offset = offset
        self._cache_sos()
        
    def _cache_sos(self):
        """Converts continuous time zpk filter to discrete time sos filter."""
        z = self.z
        p = self.p
        k = self.k
        self._sos = signal.zpk2sos(*signal.bilinear_zpk(z, p, k, self.fs))
        
    def lfilter(self, data):
        """Applys filter to data.
        
        Parameters
        ----------
        data：array_like
            Waveform to apply filter
        
        Returns
        -------
        waveform: ndarray
            Filtered waveform
        """
        data = (data-self.offset)/self.gain
        data = signal.sosfilt(self._sos, data)
        if self.F is not None:
            data = signal.lfilter(self.F, [1.], data)
        return data
    
    def get_response_time(self):
        p = self.p
        p = p[p!=0]
        return 6 * (1/np.abs(p)).max()
    
    def __repr__(self):
        return (
            f'Filter(fs={self.fs}, z={self.z!r}, p={self.p!r}, k={self.k}, '
            f'F={self.F!r}, gain={self.gain}, offset={self.offset})'
        )


def _convert_parameters_to_list(params, n_real, n_comp):
    """Extracts IIR filter parameters from dict."""
    zeros = []
    poles = []
    # First order, zero z<0
    for i in range(n_real):
        tauB = params[f'tauB{i+1}']
        B = params[f'B{i+1}']
        zeros.append(-1/tauB/(1+B))
        poles.append(-1/tauB)
    # Second order
    for i in range(n_comp):
        tauA = params[f'tauA{i+1}']
        A = params[f'A{i+1}']
        T = params[f'TA{i+1}']
        phi = params[f'phiA{i+1}']
        poles.extend([-1/tauA-2j*np.pi/T, -1/tauA+2j*np.pi/T])
        # solve for zeros
        a = 1 + A*np.cos(phi)
        b = (1+a)/tauA - 2*np.pi*A*np.sin(phi)/T
        c = 1/tauA**2 + (2*np.pi/T)**2
        d = cmath.sqrt(b**2 - 4*a*c)
        zeros.extend([(-b-d)/(2*a), (-b+d)/(2*a)])
    return zeros, poles


def get_invfilter_by_parameters(params, fs, n_real, n_comp, block_DC):
    """Construct inverse IIR filter from dict."""
    z, p = _convert_parameters_to_list(params, n_real, n_comp)
    k = np.real(np.prod(p) / np.prod(z))
    F = None
    try:
        gain = params['gain']
        offset = params['offset']
    except:
        gain = 1
        offset = 0
    if block_DC:
        tauC = params['tauC']
        leakC = params['leakC']
        z.append(-leakC/tauC)
        p.append(-1/tauC)
    # exchange zeros and poles to get inverse filter
    return Filter(fs, p, z, 1/k, F, gain, offset)


class ExponentialPredistortion:
    """Implement predistortion on the Z waveforms.

    Parameters
    ----------
    waveform_number : int
        The waveform number to predistort.

    Attributes
    ----------
    A1 : float
        Amplitude for the first pole.
    tau1 : float
        Time constant for the first pole.
    A2 : float
        Amplitude for the second pole.
    tau2 : float
        Time constant for the second pole.
    A3 : float
        Amplitude for the third pole.
    tau3 : float
        Time constant for the third pole.
    A4 : float
        Amplitude for the fourth pole.
    tau4 : float
        Time constant for the fourth pole.
    tauC : float
        Time constant for capacitor.
    from_str : bool
        If true, use ``filter_str`` to construct :obj:`Filter`.
    filter_str: str
        String representation of :obj:`Filter`.
    fs : float
        Sample rate for the waveform.
    """

    def __init__(self, waveform_number):
        self.fs = 1
        self.n = int(waveform_number)

    def set_parameters(self, config={}):
        """Set base parameters using config from from Labber driver.

        Parameters
        ----------
        config : dict
            Configuration as defined by Labber driver configuration window

        """
        if bool(config.get('Uniform predistort Z')):
            m=''
        else:
            m = self.n + 1
        self.fs = config.get('Sample rate')
        use_str = bool(config.get(f'Predistort Z{m} - from string'))
        if use_str:
            filter_str = config.get(f'Predistort Z{m} - string')
            from numpy import array
            try:
                self._filter = eval(filter_str)
            except:
                self._filter = Filter(self.fs, [], [], 1)
        else:
            params = dict()
            n_comp = 0
            n_real = 0
            for i in range(CONST.Z_PREDISTORTION_TERMS_COMP):
                Ai = config.get(f'Predistort Z{m} - A{i+1}')
                tauAi = config.get(f'Predistort Z{m} - tauA{i+1}')
                TAi = config.get(f'Predistort Z{m} - TA{i+1}')
                phiAi = config.get(f'Predistort Z{m} - phiA{i+1}')
                if Ai != 0 and tauAi > 0 and TAi > 0:
                    n_comp += 1
                    params[f'A{n_comp}'] = Ai
                    params[f'tauA{n_comp}'] = tauAi
                    params[f'TA{n_comp}'] = TAi
                    params[f'phiA{n_comp}'] = phiAi * np.pi/180
            for i in range(CONST.Z_PREDISTORTION_TERMS):
                Bi = config.get(f'Predistort Z{m} - B{i+1}')
                tauBi = config.get(f'Predistort Z{m} - tauB{i+1}')
                if Bi != 0 and tauBi > 0:
                    n_real += 1
                    params[f'B{n_real}'] = Bi
                    params[f'tauB{n_real}'] = tauBi
            tauC = config.get(f'Predistort Z{m} - tauC')
            block_DC = False
            if tauC > 0:
                params[f'tauC'] = tauC
                block_DC = True
            self._filter = get_invfilter_by_parameters(params, self.fs, n_real, n_comp, block_DC)


    def predistort(self, waveform):
        """Predistort input waveform.

        Parameters
        ----------
        waveform : complex numpy array
            Waveform data to be pre-distorted

        Returns
        -------
        waveform : complex numpy array
            Pre-distorted waveform

        """
        # # pad with zeros at end to make sure response has time to go to zero
        # pad_time = self._filter.get_response_time()
        # padded = np.pad(
        #     waveform,
        #     (0, round(pad_time * self.fs)),
        #     mode='constant'
        #     constant_values=0,
        # )
        return self._filter.lfilter(waveform)


if __name__ == '__main__':
    pass

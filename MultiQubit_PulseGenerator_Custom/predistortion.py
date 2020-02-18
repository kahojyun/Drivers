#!/usr/bin/env python3

# Note from/to Dan. This driver appears to take a premade transfer function for
# each mixer. The trick is then to load in the transfer function and perform the
# actual predistortion. We therefore need to find the correct transfer function
# and save this transfer function to file. These transfer functions need to be
# saved as Transfer function #1, etc.

# The predistoriton program as it stands only produces the transfer function of
# one mixer at a time. A challenge will be finding a good way to add the
# transfer functions to a common file in a convenient way.

import numpy as np
from numpy.fft import fft, fftfreq, fftshift, ifft, ifftshift
from scipy.interpolate import interp1d
import scipy.signal as signal


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
    r"""Filter signal with cascaded IIR filters and a FIR filter.
    
    All IIR filters are first order, aiming to compensate distortion
    in signal.

    Transfer function of normal IIR filter:
    .. math::
        H(s) = 1 + \frac{A s}{s + B}
    
    Transfer function of IIR filter for compensating DC block effect:
    .. math::
        H(s) = 1 + \frac{s}{s + C}

    Parameters
    ----------
    fs : float
        Sample rate
    A : array_like
        Coefficients for IIR filter
    B : array_like
        Coefficients for IIR filter
    F : array_like, optional
        Coefficients for FIR filter
    gain : :obj:`float`, optional
    offset : :obj:`float`, optional
    C : :obj:`float`, optional
        If set, use an IIR filter to compensate DC block effect of capacitor.
    """

    def __init__(self, fs, A, B, F=None, gain=1, offset=0, C=None):
        self.fs = fs
        self.A = np.array(A, dtype='f8')
        self.B = np.array(B, dtype='f8')
        self.F = np.array(F, dtype='f8') if F is not None else None
        self.gain = gain
        self.offset = offset
        self.C = C
        
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
        if len(self.A) != len(self.B):
            raise Exception('len(A) != len(B)')
        if self.C is not None:
            z, p = signal.bilinear([1., 0.], [1., self.C], self.fs)
            data = signal.lfilter(p, z, data)
        for i in range(len(self.A)):
            z, p = signal.bilinear([1+self.A[i], self.B[i]], [1, self.B[i]], self.fs)
            data = signal.lfilter(p, z, data)
        if self.F is not None:
            data = signal.lfilter(self.F, [1.], data)
        return data*self.gain + self.offset
    
    def get_response_time(self):
        return 6 * (1/self.B).max()
    
    def __repr__(self):
        return (
            f'Filter(fs={self.fs}, A={self.A!r}, B={self.B!r}, '
            f'F={self.F!r}, gain={self.gain}, offset={self.offset}, '
            f'C={self.C})'
        )


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
        self.A1 = 0
        self.tau1 = 0
        self.A2 = 0
        self.tau2 = 0
        self.A3 = 0
        self.tau3 = 0
        self.A4 = 0
        self.tau4 = 0
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
        self.use_str = bool(config.get(f'Predistort Z{m} - from string'))
        if self.use_str:
            self.filter_str = config.get(f'Predistort Z{m} - string')
            from numpy import array
            try:
                self._filter = eval(self.filter_str)
            except:
                self._filter = Filter(self.fs, [], [])
        else:
            A = []
            B = []
            for i in range(4):
                Ai = config.get(f'Predistort Z{m} - A{i+1}')
                taui = config.get(f'Predistort Z{m} - tau{i+1}')
                if Ai != 0 and taui > 0:
                    A.append(Ai)
                    B.append(1/taui)
            tauC = config.get(f'Predistort Z{m} - tauC')
            if tauC > 0:
                C = 1/tauC
            else:
                C = None
            self._filter = Filter(self.fs, A, B, C=C)


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

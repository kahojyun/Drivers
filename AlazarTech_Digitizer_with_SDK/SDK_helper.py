import atsapi as ats
import numpy as np

# hardware specific constants
HARDWARE_SPEC = {
    # minimum record size
    'MIN_REC_SIZE': {
        'ATS9870': 256,
        'ATS9360': 256
    },
    # minimum record size resolution
    'REC_SIZE_RES': {
        'ATS9870': 64,
        'ATS9360': 128
    },
    # external trigger range
    'EXT_TRIG_RANGE': {
        'ATS9870': 'ETR_5V',
        'ATS9360': 'ETR_2V5'
    },
    # internal sample rate
    'SAMPLE_RATE': {
        'ATS9870': [
            'SAMPLE_RATE_1KSPS',
            'SAMPLE_RATE_2KSPS',
            'SAMPLE_RATE_5KSPS',
            'SAMPLE_RATE_10KSPS',
            'SAMPLE_RATE_20KSPS',
            'SAMPLE_RATE_50KSPS',
            'SAMPLE_RATE_100KSPS',
            'SAMPLE_RATE_200KSPS',
            'SAMPLE_RATE_500KSPS',
            'SAMPLE_RATE_1MSPS',
            'SAMPLE_RATE_2MSPS',
            'SAMPLE_RATE_5MSPS',
            'SAMPLE_RATE_10MSPS',
            'SAMPLE_RATE_20MSPS',
            'SAMPLE_RATE_50MSPS',
            'SAMPLE_RATE_100MSPS',
            'SAMPLE_RATE_200MSPS',
            'SAMPLE_RATE_500MSPS',
            'SAMPLE_RATE_1000MSPS'
        ],
        'ATS9360': [
            'SAMPLE_RATE_1KSPS',
            'SAMPLE_RATE_2KSPS',
            'SAMPLE_RATE_5KSPS',
            'SAMPLE_RATE_10KSPS',
            'SAMPLE_RATE_20KSPS',
            'SAMPLE_RATE_50KSPS',
            'SAMPLE_RATE_100KSPS',
            'SAMPLE_RATE_200KSPS',
            'SAMPLE_RATE_500KSPS',
            'SAMPLE_RATE_1MSPS',
            'SAMPLE_RATE_2MSPS',
            'SAMPLE_RATE_5MSPS',
            'SAMPLE_RATE_10MSPS',
            'SAMPLE_RATE_20MSPS',
            'SAMPLE_RATE_50MSPS',
            'SAMPLE_RATE_100MSPS',
            'SAMPLE_RATE_200MSPS',
            'SAMPLE_RATE_500MSPS',
            'SAMPLE_RATE_800MSPS',
            'SAMPLE_RATE_1000MSPS',
            'SAMPLE_RATE_1200MSPS',
            'SAMPLE_RATE_1500MSPS',
            'SAMPLE_RATE_1800MSPS'
        ]
    }
}

SAMPLE_RATE_VALUE = {
    'SAMPLE_RATE_1KSPS': 1e3,
    'SAMPLE_RATE_2KSPS': 2e3,
    'SAMPLE_RATE_5KSPS': 5e3,
    'SAMPLE_RATE_10KSPS': 10e3,
    'SAMPLE_RATE_20KSPS': 20e3,
    'SAMPLE_RATE_50KSPS': 50e3,
    'SAMPLE_RATE_100KSPS': 100e3,
    'SAMPLE_RATE_200KSPS': 200e3,
    'SAMPLE_RATE_500KSPS': 500e3,
    'SAMPLE_RATE_1MSPS': 1e6,
    'SAMPLE_RATE_2MSPS': 2e6,
    'SAMPLE_RATE_5MSPS': 5e6,
    'SAMPLE_RATE_10MSPS': 10e6,
    'SAMPLE_RATE_20MSPS': 20e6,
    'SAMPLE_RATE_25MSPS': 25e6,
    'SAMPLE_RATE_50MSPS': 50e6,
    'SAMPLE_RATE_100MSPS': 100e6,
    'SAMPLE_RATE_125MSPS': 125e6,
    'SAMPLE_RATE_160MSPS': 160e6,
    'SAMPLE_RATE_180MSPS': 180e6,
    'SAMPLE_RATE_200MSPS': 200e6,
    'SAMPLE_RATE_250MSPS': 250e6,
    'SAMPLE_RATE_400MSPS': 400e6,
    'SAMPLE_RATE_500MSPS': 500e6,
    'SAMPLE_RATE_800MSPS': 800e6,
    'SAMPLE_RATE_1000MSPS': 1000e6,
    'SAMPLE_RATE_1200MSPS': 1200e6,
    'SAMPLE_RATE_1500MSPS': 1500e6,
    'SAMPLE_RATE_1600MSPS': 1600e6,
    'SAMPLE_RATE_1800MSPS': 1800e6,
    'SAMPLE_RATE_2000MSPS': 2000e6,
    'SAMPLE_RATE_2400MSPS': 2400e6,
    'SAMPLE_RATE_3000MSPS': 3000e6,
    'SAMPLE_RATE_3600MSPS': 3600e6,
    'SAMPLE_RATE_4000MSPS': 4000e6
}

INPUT_RANGE_VALUE = {
    'INPUT_RANGE_PM_20_MV': 20e-3,
    'INPUT_RANGE_PM_40_MV': 40e-3,
    'INPUT_RANGE_PM_50_MV': 50e-3,
    'INPUT_RANGE_PM_80_MV': 80e-3,
    'INPUT_RANGE_PM_100_MV': 100e-3,
    'INPUT_RANGE_PM_200_MV': 200e-3,
    'INPUT_RANGE_PM_400_MV': 400e-3,
    'INPUT_RANGE_PM_500_MV': 500e-3,
    'INPUT_RANGE_PM_800_MV': 800e-3,
    'INPUT_RANGE_PM_1_V': 1,
    'INPUT_RANGE_PM_2_V': 2,
    'INPUT_RANGE_PM_4_V': 4,
    'INPUT_RANGE_PM_5_V': 5,
    'INPUT_RANGE_PM_8_V': 8,
    'INPUT_RANGE_PM_10_V': 10,
    'INPUT_RANGE_PM_20_V': 20,
    'INPUT_RANGE_PM_40_V': 40,
    'INPUT_RANGE_PM_16_V': 16,
    'INPUT_RANGE_PM_1_V_25': 1.25,
    'INPUT_RANGE_PM_2_V_5': 2.5,
    'INPUT_RANGE_PM_125_MV': 125e-3,
    'INPUT_RANGE_PM_250_MV': 250e-3
}

IMPEDANCE_VALUE = {
    'IMPEDANCE_1M_OHM': 1e6,
    'IMPEDANCE_50_OHM': 50,
    'IMPEDANCE_75_OHM': 75,
    'IMPEDANCE_300_OHM': 300
}

EXT_TRIG_RANGE_VALUE = {
    'ETR_5V': 5,
    'ETR_1V': 1,
    'ETR_2V5': 2.5
}

def choose_internal_sample_rate(model, sample_rate):
    min_v = 1000
    target = np.log(sample_rate)
    for key in HARDWARE_SPEC['SAMPLE_RATE'][model]:
        if abs(np.log(SAMPLE_RATE_VALUE[key])-target) < min_v:
            min_v = abs(np.log(SAMPLE_RATE_VALUE[key])-target)
            mkey = key
    return mkey

def choose_external_sample_rate(model, target):
    """Return appropriate sample rate and decimation."""
    # ATS9870 only supports 1GS/s when using external 10MHz ref. Choose appropriate
    # decimation.
    if model == 'ATS9870':
        sample_rate = 1000000000
        deci = [1,2,4,10,20,40,100,200,400,1000,2000,4000,10000,20000,40000,100000]
        min_i = np.argmin(abs(np.log(sample_rate)-np.log(deci)-np.log(target)))
        return sample_rate, deci[min_i]
    # ATS9360 supports 300MS/s -- 1800MS/s, 1MS/s step
    if model == 'ATS9360':
        target = np.clip(target, 300e6, 1800e6)
        sample_rate = int(target/1e6)*1000000
        return sample_rate, 1
    raise Exception('Not implemented')

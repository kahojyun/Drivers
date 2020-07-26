MODE_GEN = 'Generate signal'
MODE_CAL = 'Calibrate signal'
if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parents[1]/'Helper_Lib'))

    from driver_config import (
        LDriverDefinition, LDouble, LBoolean, LButton, LVector, LCombo
    )
    dir_path = Path(__file__).parent
    f = LDriverDefinition(dir_path/'Mixer_Calibrator.ini')
    f.add_general_settings(
        name='Mixer Calibrator',
        version='0.1',
        driver_path='Mixer_Calibrator',
        signal_generator=True,
    )

    # f.add_section('Instr. Setting')
    f.add_group('General Settings')

    f.add_quantity(LCombo(
        'Mode',
        combo=[MODE_GEN, MODE_CAL],
        def_value=MODE_GEN,
        show_in_measurement_dlg=True,
    ))

    f.add_quantity(LDouble(
        'Sample rate',
        def_value=2e9,
        unit='Hz',
        show_in_measurement_dlg=True,
    ))




    f.add_group('IQ calibration')

    f.add_quantity(LDouble(
        'Q delay',
        unit='s',
        def_value=0,
        show_in_measurement_dlg=True,
    ))

    f.add_quantity(LDouble(
        'Phase skew',
        unit='deg',
        def_value=0,
        show_in_measurement_dlg=True,
    ))

    f.add_quantity(LDouble(
        'Gain imbalance',
        unit='dB',
        def_value=0,
        show_in_measurement_dlg=True,
    ))

    bool_offset = LBoolean(
        'Calibrate offset',
        def_value=False,
        tooltip='Not recommended. Should use hardware offset.'
    )
    f.add_quantity(bool_offset)

    for s in ['I', 'Q']:
        f.add_quantity(LDouble(
            f'{s} offset',
            unit='V',
            def_value=0,
            state_quant=bool_offset,
            states=True,
            show_in_measurement_dlg=True,
        ))

    

    f.add_group('Signal generation')
    f.add_quantity(LDouble(
        'Frequency',
        unit='Hz',
        def_value=100e6,
        show_in_measurement_dlg=True,
    ))
    f.add_quantity(LDouble(
        'Amplitude',
        unit='V',
        def_value=0.5,
        show_in_measurement_dlg=True,
    ))
    f.add_quantity(LDouble(
        'Number of points',
        def_value=10e3,
    ))
    f.add_quantity(LBoolean(
        'Swap IQ',
        def_value=False,
    ))



    # f.add_group('Signal calibration')
    # f.add_quantity(LDouble(
    #     'Sideband frequency',
    #     unit='Hz',
    #     def_value=0,
    #     tooltip='To achieve higher interpolation accuracy, it is recommended to convert signal to baseband first, interpolate and, finally, convert back to original frequency.',
    #     show_in_measurement_dlg=True,
    # ))

    f.add_group('Signal')
    for s in ['I', 'Q']:
        f.add_quantity(LVector(
            f'Waveform in - {s}',
            permission='WRITE',
            unit='V',
            x_name='Time',
            x_unit='s',
            show_in_measurement_dlg=True,
        ))
    for s in ['I', 'Q']:
        f.add_quantity(LVector(
            f'Waveform out - {s}',
            permission='READ',
            unit='V',
            x_name='Time',
            x_unit='s',
            show_in_measurement_dlg=True,
        ))
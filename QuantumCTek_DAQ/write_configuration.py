MAX_FREQS = 8

if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parents[1]/'Helper_Lib'))

    from driver_config import (
        LDriverDefinition, LDouble, LBoolean,
        LString, LVector, LCombo, LVectorComplex, LComplex
    )
    dir_path = Path(__file__).parent
    f = LDriverDefinition(dir_path/'QuantumCTek_DAQ.ini')
    f.add_general_settings(
        name='QuantumCTek_DAQ',
        version='0.0.2',
        driver_path='QuantumCTek_DAQ',
        interface='Other',
        support_arm=True,
        support_hardware_loop=False,
    )



    # f.add_section('Instr. Setting')
    f.add_group('Communication')
    f.add_quantity(LString(
        'Host MAC address',
        tooltip='MAC address of host computer'
    ))

    

    f.add_group('Aquisition')
    f.add_quantity(LDouble(
        'Sample depth',
        def_value=3000,
        low_lim=0,
        high_lim=18000,
        show_in_measurement_dlg=True,
    ))
    f.add_quantity(LDouble(
        'Trigger count',
        label='Trigger count',
        def_value=1000,
        low_lim=1,
        high_lim=100000,
        show_in_measurement_dlg=True,
    ))



    f.add_group('Demodulation')
    bool_demod = LBoolean(
        'Demodulation',
        def_value=True,
        show_in_measurement_dlg=True,
    )
    f.add_quantity(bool_demod)

    combo_freqs = LCombo(
        'Number of freqs',
        def_value=2,
        combo=list(range(1, MAX_FREQS+1)),
        state_quant=bool_demod,
        states=True,
    )
    f.add_quantity(combo_freqs)

    bool_uni_window = LBoolean(
        'Uniform window setting',
        def_value=True,
        state_quant=bool_demod,
        states=True,
    )
    f.add_quantity(bool_uni_window)

    f.add_quantity(LDouble(
        'Window start',
        def_value=500,
        low_lim=0,
        high_lim=18000,
        tooltip='Start of demodulation window. Should be smaller than `Sample depth`.',
        state_quant=bool_uni_window,
        states=True,
    ))
    f.add_quantity(LDouble(
        'Window width',
        def_value=1500,
        low_lim=8,
        high_lim=18000,
        tooltip='Width of demodulation window. Should be smaller than `Sample depth`-`Window start`.',
        state_quant=bool_uni_window,
        states=True,
    ))
    for i in range(MAX_FREQS):
        f.add_quantity(LDouble(
            f'Demod freq #{i+1}',
            def_value=10e6,
            unit='Hz',
            tooltip='Avoid multiples of 125M. Result might be distorted if absolute value is greater than 300M.',
            state_quant=bool_demod,
            states=True,
        ))
        f.add_quantity(LDouble(
            f'Window start #{i+1}',
            def_value=500,
            low_lim=0,
            high_lim=18000,
            tooltip='Start of demodulation window. Should be smaller than `Sample depth`.',
            state_quant=bool_uni_window,
            states=False,
        ))
        f.add_quantity(LDouble(
            f'Window width #{i+1}',
            def_value=1500,
            low_lim=8,
            high_lim=18000,
            tooltip='Width of demodulation window. Should be smaller than `Sample depth`-`Window start`.',
            state_quant=bool_uni_window,
            states=False,
        ))



    f.add_group('Result')
    f.add_quantity(LVector(
        'Averaged wave I',
        permission='READ',
        x_unit='s',
        x_name='Time',
        state_quant=bool_demod,
        states=False,
    ))
    f.add_quantity(LVector(
        'Averaged wave Q',
        permission='READ',
        x_unit='s',
        x_name='Time',
        state_quant=bool_demod,
        states=False,
    ))
    for i in range(MAX_FREQS):
        f.add_quantity(LVectorComplex(
            f'Result Vector #{i+1}',
            permission='READ',
            state_quant=combo_freqs,
            states=list(range(i+1, MAX_FREQS+1)),
        ))
        f.add_quantity(LComplex(
            f'Averaged #{i+1}',
            permission='READ',
            state_quant=combo_freqs,
            states=list(range(i+1, MAX_FREQS+1)),
        ))



    
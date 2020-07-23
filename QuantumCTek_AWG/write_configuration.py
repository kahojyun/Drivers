import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parents[1]/'Helper_Lib'))

from driver_config import (
    LDriverDefinition, LDouble, LBoolean, LButton, LVector
)

MAX_CHANNELS = 4

if __name__ == "__main__":
    dir_path = Path(__file__).parent
    f = LDriverDefinition(dir_path/'QuantumCTek_AWG.ini')
    f.add_general_settings(
        name='QuantumCTek_AWG',
        version='0.0.3',
        driver_path='QuantumCTek_AWG',
        interface='TCPIP',
        support_arm=True,
        support_hardware_loop=False,
    )



    # f.add_section('Instr. Setting')
    f.add_group('Delay')

    f.add_quantity(LDouble(
        'Trigger delay',
        label='Trigger delay',
        unit='s',
        def_value=0,
        tooltip='Minimum step is 4 ns.',
        low_lim=0,
        high_lim=2.56e-4,
        show_in_measurement_dlg=True,
    ))

    f.add_quantity(LDouble(
        'Output delay',
        label='Output delay',
        unit='s',
        def_value=0,
        tooltip='Minimum step is 4 ns.',
        low_lim=0,
        high_lim=2.56e-4,
        show_in_measurement_dlg=True,
    ))



    f.add_group('Trigger')

    f.add_quantity(LDouble(
        'Trigger interval',
        label='Trigger interval',
        unit='s',
        def_value=100e-6,
        low_lim=1e-7,
        high_lim=5e-3,
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

    f.add_quantity(LButton(
        'Run AWG',
        label='Run AWG',
        show_in_measurement_dlg=True,
    ))



    f.add_group('Calibration')

    for i in range(MAX_CHANNELS):
        f.add_quantity(LDouble(
            f'Channel gain #{i+1}',
            label=f'Channel gain #{i+1}',
            def_value=511,
            tooltip='Type: int.',
            low_lim=-512,
            high_lim=511,
        ))
    for i in range(MAX_CHANNELS):
        f.add_quantity(LDouble(
            f'Channel default voltage #{i+1}',
            label=f'Channel default voltage #{i+1}',
            def_value=0,
            tooltip='Type: int.',
        ))

    f.add_group('Output')
    for i in range(MAX_CHANNELS):
        f.add_quantity(LBoolean(
            f'Continuous output #{i+1}',
            label=f'Continuous output #{i+1}',
            def_value=False,
        ))
        f.add_quantity(LBoolean(
            f'Allow clipping #{i+1}',
            label=f'Allow clipping #{i+1}',
            def_value=False,
        ))
        f.add_quantity(LDouble(
            f'Data offset #{i+1}',
            label=f'Data offset #{i+1}',
            def_value=0,
            tooltip='Type: int.',
            show_in_measurement_dlg=True,
        ))
        
    
    f.add_group('Waveform')
    for i in range(MAX_CHANNELS):
        f.add_quantity(LVector(
            f'Waveform #{i+1}',
            show_in_measurement_dlg=True,
            permission='WRITE',
            x_name='Time',
            x_unit='s',
        ))
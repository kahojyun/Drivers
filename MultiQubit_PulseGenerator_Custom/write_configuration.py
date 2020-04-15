MAX_QUBITS = 9
MAX_GENERIC_PULSE = 7
MAX_GENERIC_PRE = 3
MAX_GENERIC_POST = 3
MAX_FOURIER_TERMS = 4
MAX_CT_QUBITS = MAX_QUBITS
Z_PREDISTORTION_TERMS_COMP = 1
Z_PREDISTORTION_TERMS = 4
MAX_READOUT_SECTION = 3
__version__ = '1.6.2'

# pulse timing options
TIMING_NONE = 'Default'
TIMING_ABS = 'Absolute'
TIMING_REL = 'Relative'

# pulse types
PULSE_GAUSSIAN = 'Gaussian'
PULSE_SQUARE = 'Square'
PULSE_RAMP = 'Ramp'
PULSE_COSINE = 'Cosine'
PULSES_1QB = [
    PULSE_GAUSSIAN,
    PULSE_SQUARE,
    PULSE_RAMP,
    PULSE_COSINE,
]
# 2qb
PULSE_CZ = 'CZ'
PULSE_NETZERO = 'NetZero'
PULSES_2QB = [
    PULSE_CZ,
    PULSE_NETZERO,
]

if __name__ == "__main__":
    from pathlib import Path
    from driver_config import *
    # General setting
    dir_path = Path(__file__).parent
    f = LDriverDefinition(dir_path/'MultiQubit_PulseGenerator_Custom.ini')
    f.add_general_settings(
        name='Multi-Qubit Pulse Generator Custom',
        version=__version__,
        driver_path='MultiQubit_PulseGenerator_Custom',
        signal_analyzer=True,
        signal_generator=True,
    )
    qubit_list = list(range(1, MAX_QUBITS+1))

    #region Section: Sequence
    f.add_section('Sequence')
    #region Group: Sequence
    f.add_group('Sequence')

    seq_rabi = 'Rabi'
    seq_cpmg = 'CP/CPMG'
    seq_ptrain = 'Pulse train'
    seq_1qrb = '1-QB Randomized Benchmarking'
    seq_2qrb = '2-QB Randomized Benchmarking'
    seq_slock = 'Spin-locking'
    seq_rtrain = 'Readout training'
    seq_custom = 'Custom'
    seq_gen = 'Generic'
    seq_2xeb = '2-QB XEB'
    combo_seq = LCombo(
        'Sequence',
        combo=[
            seq_rabi,
            seq_cpmg,
            seq_ptrain,
            seq_1qrb,
            seq_2qrb,
            seq_slock,
            seq_rtrain,
            seq_custom,
            seq_gen,
            seq_2xeb,
        ],
        show_in_measurement_dlg=True,
    )
    f.add_quantity(combo_seq)

    f.add_quantity(LPath(
        'Custom Python file',
        tooltip=(
            'Python file with custom Sequence class. The class must be named '
            '"CustomSequence"'
        ),
        state_quant=combo_seq,
        states=[seq_custom],
    ))

    combo_qubits = LCombo(
        'Number of qubits',
        combo=qubit_list,
        def_value=qubit_list[1],
    )
    f.add_quantity(combo_qubits)

    f.add_quantity(LDouble(
        'Pulse spacing',
        def_value=20e-9,
        low_lim=0,
        unit='s',
        show_in_measurement_dlg=True,
    ))

    f.add_quantity(LBoolean(
        'Local XY control',
        def_value=True,
    ))
    #endregion Group: Sequence

    #region Group: Pulse train
    f.add_group('Pulse train')
    
    f.add_quantity(LCombo(
        'Pulse',
        state_quant=combo_seq,
        states=[
            seq_ptrain,
        ],
        combo=[
            'Xp',
            'X2p',
            'Yp',
            'Y2p',
            'Zp',
            'Z2p',
            'CPh',
        ],
    ))

    f.add_quantity(LDouble(
        '# of pulses',
        def_value=1,
        low_lim=0,
        state_quant=combo_seq,
        states=[
            seq_ptrain,
        ],
    ))

    f.add_quantity(LBoolean(
        'Alternate pulse direction',
        def_value=False,
        state_quant=combo_seq,
        states=[
            seq_ptrain,
        ],
    ))
    #endregion Group: Pulse train

    #region Group: CPMG
    f.add_group('CPMG')

    f.add_quantity(LDouble(
        '# of pi pulses',
        tooltip=(
            'Number of refocusing pulses. Set to -1 for generating pulse '
            'sequences for T1 experiments'
        ),
        def_value=1,
        low_lim=-1,
        state_quant=combo_seq,
        states=[
            seq_cpmg,
        ],
    ))

    f.add_quantity(LDouble(
        'Sequence duration',
        def_value=1e-6,
        low_lim=0,
        unit='s',
        state_quant=combo_seq,
        states=[
            seq_cpmg,
        ],
    ))

    f.add_quantity(LBoolean(
        'Add pi pulses to Q',
        def_value=True,
        state_quant=combo_seq,
        states=[
            seq_cpmg,
        ],
    ))

    f.add_quantity(LBoolean(
        'Edge-to-edge pulses',
        def_value=False,
        state_quant=combo_seq,
        states=[
            seq_cpmg,
        ],
    ))

    f.add_quantity(LBoolean(
        'Add last pi/2 pulse to Q',
        def_value=False,
        state_quant=combo_seq,
        states=[
            seq_cpmg,
        ],
    ))
    #endregion Group: CPMG

    #region Group: Spin-locking
    f.add_group('Spin-locking')

    f.add_quantity(LDouble(
        'Drive pulse duration',
        def_value=1e-6,
        low_lim=0,
        unit='s',
        state_quant=combo_seq,
        states=[
            seq_slock,
        ],
    ))

    f.add_quantity(LDouble(
        'Drive pulse phase',
        def_value=0,
        unit='deg',
        state_quant=combo_seq,
        states=[
            seq_slock,
        ],
    ))

    f.add_quantity(LCombo(
        'Pulse sequence',
        combo=[
            'SL-3',
            'SL-5a',
            'SL-5b',
        ],
        def_value='SL-3',
        state_quant=combo_seq,
        states=[
            seq_slock,
        ],
    ))

    for i in range(MAX_QUBITS):
        qubit = i+1

        f.add_quantity(LDouble(
            f'Drive pulse amplitude #{qubit}',
            def_value=0,
            unit='V',
            tooltip=f'Drive pulse amplitude for qubit #{qubit}',
            state_quant=combo_seq,
            states=[
                seq_slock,
            ],
        ))
    #endregion Group: Spin-locking

    #region Group: Randomized Benchmarking
    f.add_group('Randomized Benchmarking')

    f.add_quantity(LCombo(
        'Native 2-QB gate',
        def_value='CZ',
        combo=[
            'CZ',
            'iSWAP',
        ],
        state_quant=combo_seq,
        states=[
            seq_2qrb,
        ],
        show_in_measurement_dlg=True,
    ))

    f.add_quantity(LDouble(
        'Number of cycles',
        def_value=17,
        low_lim=0,
        state_quant=combo_seq,
        states=[
            seq_1qrb,
            seq_2qrb,
            seq_2xeb,
        ],
        show_in_measurement_dlg=True,
    ))

    f.add_quantity(LDouble(
        'Randomize',
        def_value=0,
        tooltip=(
            'Randomize gate sequence only if "Randomize" value changes or '
            '"Number of cycles" changes'
        ),
        state_quant=combo_seq,
        states=[
            seq_1qrb,
            seq_2qrb,
            seq_2xeb,
        ],
        show_in_measurement_dlg=True,
    ))

    f.add_quantity(LBoolean(
        'Write sequence as txt file',
        def_value=False,
        tooltip='Save txt file for the sequence generated',
        state_quant=combo_seq,
        states=[
            seq_1qrb,
            seq_2qrb,
            seq_2xeb,
        ],
    ))

    bool_output_multi_seq = LBoolean(
        'Output multiple sequences',
        def_value=False,
        tooltip='Output multiple randomized gate sequences.',
        state_quant=combo_seq,
        states=[
            seq_1qrb,
            seq_2qrb,
            seq_2xeb,
        ],
        show_in_measurement_dlg=True,
    )
    f.add_quantity(bool_output_multi_seq)

    f.add_quantity(LDouble(
        'Number of multiple sequences',
        def_value=1,
        low_lim=1,
        tooltip='Number of multiple randomize gate sequences to output.',
        state_quant=bool_output_multi_seq,
        states=True,
        show_in_measurement_dlg=True,
    ))

    f.add_quantity(LBoolean(
        'Align RB waveforms to end',
        def_value=True,
        state_quant=bool_output_multi_seq,
        states=True,
        show_in_measurement_dlg=True,
    ))

    f.add_quantity(LBoolean(
        'Simultaneous pulses',
        def_value=True,
        tooltip='If False, all pulses are separated in time.',
        state_quant=combo_seq,
        states=[
            seq_1qrb,
            seq_2qrb,
            seq_2xeb,
        ],
    ))

    f.add_quantity(LCombo(
        'Qubits to Benchmark',
        combo=[f'{i+1}-{i+2}' for i in range(MAX_QUBITS-1)],
        state_quant=combo_seq,
        states=[
            seq_2qrb,
            seq_2xeb,
        ],
        show_in_measurement_dlg=True,
    ))

    bool_interleave_1qb_gate = LBoolean(
        'Interleave 1-QB Gate',
        def_value=False,
        state_quant=combo_seq,
        states=[
            seq_1qrb,
        ],
        show_in_measurement_dlg=True,
    )
    f.add_quantity(bool_interleave_1qb_gate)

    f.add_quantity(LCombo(
        'Interleaved 1-QB Gate',
        combo=[
            'Ref',
            'I',
            'Xp',
            'Xm',
            'X2p',
            'X2m',
            'Yp',
            'Ym',
            'Y2p',
            'Y2m',
            'VZp',
            'Zp',
            'Ilong',
        ],
        state_quant=bool_interleave_1qb_gate,
        states=True,
        show_in_measurement_dlg=True,
    ))

    bool_interleave_2qb_gate = LBoolean(
        'Interleave 2-QB Gate',
        def_value=False,
        state_quant=combo_seq,
        states=[
            seq_2qrb,
        ],
        show_in_measurement_dlg=True,
    )
    f.add_quantity(bool_interleave_2qb_gate)

    f.add_quantity(LCombo(
        'Interleaved 2-QB Gate',
        combo=[
            'CZ',
            'CZEcho',
            'iSWAP',
            'I',
        ],
        state_quant=bool_interleave_2qb_gate,
        states=True,
        show_in_measurement_dlg=True,
    ))

    bool_find_clifford = LBoolean(
        'Find the cheapest recovery Clifford',
        def_value=True,
        state_quant=combo_seq,
        states=[
            seq_2qrb,
        ],
        show_in_measurement_dlg=True,
    )
    f.add_quantity(bool_find_clifford)

    bool_use_table = LBoolean(
        'Use a look-up table',
        def_value=True,
        state_quant=bool_find_clifford,
        states=True,
        show_in_measurement_dlg=True,
    )
    f.add_quantity(bool_use_table)

    f.add_quantity(LPath(
        'File path of the look-up table',
        state_quant=bool_use_table,
        states=True,
        show_in_measurement_dlg=True,
    ))
    #endregion Group: Randomized Benchmarking

    # Readout discriminator training
    #region Group: Readout training
    f.add_group('Readout training')

    train_specific = 'Specific qubit'
    train_all_once = 'All qubits at once'
    train_all_combi = 'All combinations'
    combo_train_type = LCombo(
        'Training type',
        def_value=train_all_combi,
        combo=[
            train_specific,
            train_all_once,
            train_all_combi,
        ],
        tooltip=(
            'For "All combinations", (Number of states)^(Number of qubits) '
            'training data sets are required.  For other options, (Number of '
            'states) training sets are required'
        ),
        state_quant=combo_seq,
        states=[
            seq_rtrain,
        ],
        show_in_measurement_dlg=True,
    )
    f.add_quantity(combo_train_type)

    f.add_quantity(LDouble(
        'Training, qubit',
        def_value=1,
        low_lim=-1,
        state_quant=combo_train_type,
        states=[
            train_specific,
        ],
        show_in_measurement_dlg=True,
    ))

    f.add_quantity(LDouble(
        'Training, input state',
        def_value=0,
        low_lim=-1,
        state_quant=combo_seq,
        states=[
            seq_rtrain,
        ],
        show_in_measurement_dlg=True,
    ))

    f.add_quantity(LBoolean(
        'Train all states at once',
        def_value=False,
        tooltip=(
            'If checked, the driver will create training waveforms for all '
            'possible states'
        ),
        state_quant=combo_seq,
        states=[
            seq_rtrain,
        ],
        show_in_measurement_dlg=True,
    ))
    #endregion Group: Readout training

    # Custom sequence parameters
    #region Group: Custom
    f.add_group('Custom')

    for i in range(10):
        f.add_quantity(LDouble(
            f'Parameter #{i+1}',
            def_value=0,
            state_quant=combo_seq,
            states=[
                seq_custom,
            ],
        ))
    #endregion Group: Custom
    #endregion Section: Sequence

    #region Section: Generic sequence
    f.add_section('Generic sequence')
    f.add_group('Generic sequence')

    f.add_quantity(LDouble(
        'Generic - Number of cycles',
        label='Number of cycles',
        def_value=1,
        low_lim=0,
    ))

    f.add_quantity(LDouble(
        'Generic - Number of pulses',
        label='Number of cycled pulses',
        def_value=1,
        low_lim=0,
        high_lim=MAX_GENERIC_PULSE,
    ))

    f.add_quantity(LDouble(
        'Generic - Number of pre-pulse',
        label='Number of pre-pulse',
        def_value=0,
        low_lim=0,
        high_lim=MAX_GENERIC_PRE,
    ))

    f.add_quantity(LDouble(
        'Generic - Number of post-pulse',
        label='Number of post-pulse',
        def_value=0,
        low_lim=0,
        high_lim=MAX_GENERIC_POST,
    ))

    f.add_quantity(LCombo(
        'Generic - Pre-cycle spacing type',
        label='Pre-cycle spacing type',
        combo=['Start-Start', 'End-Start'],
    ))
    
    f.add_quantity(LDouble(
        'Generic - Pre-cycle spacing',
        label='Pre-cycle spacing',
        tooltip='Time between end of pre-pulse and first cycled pulse',
        def_value=100e-9,
        unit='s',
    ))

    f.add_quantity(LCombo(
        'Generic - Cycle spacing type',
        label='Cycle spacing type',
        combo=['Start-Start', 'End-Start'],
    ))

    f.add_quantity(LDouble(
        'Generic - Cycle spacing',
        label='Cycle spacing',
        tooltip='Time between cycled pulse sequence',
        def_value=100e-9,
        unit='s',
    ))

    f.add_quantity(LCombo(
        'Generic - Post-cycle spacing type',
        label='Post-cycle spacing type',
        combo=['Start-Start', 'End-Start'],
    ))

    f.add_quantity(LDouble(
        'Generic - Post-cycle spacing',
        label='Post-cycle spacing',
        tooltip='Time between end of last cycled pulse and post-pulse',
        def_value=100e-9,
        unit='s',
    ))

    def write_custom_pulse(section, group):
        f.add_group(group)

        f.add_quantity(LButton(
            f'{section} - {group} - Copy',
            label='Copy as template',
        ))

        f.add_quantity(LButton(
            f'{section} - {group} - Paste',
            label='Use template',
        ))

        f.add_quantity(LCombo(
            f'{section} - {group} - Add to qubit',
            label='Add to qubit',
            combo=qubit_list,
        ))

        combo_line = LCombo(
            f'{section} - {group} - Add to line',
            label='Add to line',
            combo=[
                'XY',
                'Z',
            ],
        )
        f.add_quantity(combo_line)
        
        combo_step_timing = LCombo(
            f'{section} - {group} - Pulse timing',
            label='Pulse timing',
            combo=[
                TIMING_NONE,
                TIMING_ABS,
                TIMING_REL,
            ],
        )
        f.add_quantity(combo_step_timing)

        f.add_quantity(LCombo(
            f'{section} - {group} - Pulse timing reference',
            label="Relative to previous pulse's",
            combo=[
                'Start',
                'Center',
                'End',
            ],
            state_quant=combo_step_timing,
            states=[
                TIMING_REL,
            ],
        ))

        f.add_quantity(LCombo(
            f'{section} - {group} - Pulse timing locate',
            label="Set this pulse's",
            combo=[
                'Start',
                'Center',
                'End',
            ],
            state_quant=combo_step_timing,
            states=[
                TIMING_ABS,
                TIMING_REL,
            ],
        ))

        f.add_quantity(LDouble(
            f'{section} - {group} - Pulse timing time',
            label='Time',
            tooltip='Absolute or relative time',
            def_value=100e-9,
            unit='s',
            state_quant=combo_step_timing,
            states=[
                TIMING_ABS,
                TIMING_REL,
            ],
        ))

        combo_pulse_type = LCombo(
            f'{section} - {group} - Pulse type',
            label='Pulse type',
            combo=PULSES_1QB,
        )
        f.add_quantity(combo_pulse_type)

        f.add_quantity(LDouble(
            f'{section} - {group} - Truncation range',
            label='Truncation range',
            tooltip='Truncate at ? σ',
            def_value=3,
            state_quant=combo_pulse_type,
            states=[
                PULSE_GAUSSIAN,
            ],
        ))

        f.add_quantity(LBoolean(
            f'{section} - {group} - Half cosine',
            label='Half cosine',
            def_value=False,
            state_quant=combo_pulse_type,
            states=[
                PULSE_COSINE,
            ],
        ))

        f.add_quantity(LBoolean(
            f'{section} - {group} - Start at zero',
            label='Start at zero',
            def_value=False,
            state_quant=combo_pulse_type,
            states=[
                PULSE_GAUSSIAN,
            ],
        ))

        bool_use_drag = LBoolean(
            f'{section} - {group} - Use DRAG',
            label='Use DRAG',
            def_value=False,
            state_quant=combo_line,
            states=[
                'XY',
            ],
        )
        f.add_quantity(bool_use_drag)

        f.add_quantity(LDouble(
            f'{section} - {group} - Amplitude',
            label='Amplitude',
            def_value=1,
            unit='V',
        ))

        f.add_quantity(LDouble(
            f'{section} - {group} - Phase',
            label='Phase',
            def_value=0,
            unit='deg',
        ))

        f.add_quantity(LDouble(
            f'{section} - {group} - Width',
            label='Width',
            def_value=10e-9,
            low_lim=0,
            unit='s',
        ))

        f.add_quantity(LDouble(
            f'{section} - {group} - Plateau',
            label='Plateau',
            def_value=0,
            low_lim=0,
            unit='s',
        ))

        f.add_quantity(LDouble(
            f'{section} - {group} - Frequency',
            label='Frequency',
            unit='Hz',
        ))

        f.add_quantity(LDouble(
            f'{section} - {group} - DRAG scaling',
            label='DRAG scaling',
            def_value=0.25e-9,
            unit='s',
            state_quant=bool_use_drag,
            states=True,
        ))

        f.add_quantity(LDouble(
            f'{section} - {group} - DRAG frequency detuning',
            label='DRAG frequency detuning',
            def_value=0,
            unit='Hz',
            state_quant=bool_use_drag,
            states=True,
        ))


    #region Group: Cycled pulse
    for i in range(MAX_GENERIC_PULSE):
        write_custom_pulse('Generic', f'Cycled pulse #{i+1}')
    #endregion Group: Cycled pulse

    #region Group: Pre pulse
    for i in range(MAX_GENERIC_PRE):
        write_custom_pulse('Generic', f'Pre pulse #{i+1}')
    #endregion Group: Pre pulse

    #region Group: Post pulse
    for i in range(MAX_GENERIC_POST):
        write_custom_pulse('Generic', f'Post pulse #{i+1}')
    #endregion Group: Post pulse
    #endregion Section: Generic sequence

    #region Section: Waveform
    f.add_section('Waveform')
    #region Group: Waveform
    f.add_group('Waveform')

    f.add_quantity(LDouble(
        'Sample rate',
        def_value=2.5e9,
        unit='Hz',
        show_in_measurement_dlg=True,
    ))

    bool_trim = LBoolean(
        'Trim waveform to sequence',
        label='Adjust waveform to sequence length',
        tooltip='Automatically adjusts the number of points in the waveform',
        def_value=True,
    )
    f.add_quantity(bool_trim)

    f.add_quantity(LDouble(
        'Number of points',
        def_value=240e3,
        state_quant=bool_trim,
        states=False,
        show_in_measurement_dlg=True,
    ))

    f.add_quantity(LBoolean(
        'Align pulses to end of waveform',
        state_quant=bool_trim,
        states=False,
        def_value=False,
    ))
    #endregion Group: Waveform

    #region Group: Delays
    f.add_group('Delays')

    f.add_quantity(LDouble(
        'First pulse delay',
        def_value=100e-9,
        unit='s',
    ))

    f.add_quantity(LBoolean(
        'Enable individual delay',
        def_value=True,
    ))

    for i in range(MAX_QUBITS):
        qubit = i+1
        for trace in ['XY', 'Z']:
            f.add_quantity(LDouble(
                f'Qubit {qubit} {trace} Delay',
                def_value=0,
                unit='s',
            ))
    #endregion Group: Delays
    #endregion Section: Waveform

    #region Section: 1-QB gates XY
    f.add_section('1-QB gates XY')
    #region Group: Pulse settings
    f.add_group('Pulse settings')

    combo_pulse_type = LCombo(
        'Pulse type',
        combo=PULSES_1QB,
    )
    f.add_quantity(combo_pulse_type)

    f.add_quantity(LDouble(
        'Truncation range',
        tooltip='Truncate at ? σ',
        def_value=3,
        state_quant=combo_pulse_type,
        states=[
            PULSE_GAUSSIAN,
        ],
    ))

    f.add_quantity(LBoolean(
        'Half cosine',
        def_value=False,
        state_quant=combo_pulse_type,
        states=[
            PULSE_COSINE,
        ],
    ))

    f.add_quantity(LBoolean(
        'Start at zero',
        def_value=False,
        state_quant=combo_pulse_type,
        states=[
            PULSE_GAUSSIAN,
        ],
    ))

    bool_use_drag = LBoolean(
        'Use DRAG',
        def_value=False,
    )
    f.add_quantity(bool_use_drag)

    bool_uni_amp = LBoolean(
        'Uniform amplitude',
        def_value=False,
    )
    f.add_quantity(bool_uni_amp)

    f.add_quantity(LDouble(
        'Amplitude',
        def_value=1,
        unit='V',
        state_quant=bool_uni_amp,
        states=True,
        show_in_measurement_dlg=True,
    ))

    bool_uni_shape = LBoolean(
        'Uniform pulse shape',
        def_value=True,
    )
    f.add_quantity(bool_uni_shape)

    f.add_quantity(LDouble(
        'Width',
        def_value=10e-9,
        low_lim=0,
        unit='s',
        state_quant=bool_uni_shape,
        states=True,
        show_in_measurement_dlg=True,
    ))

    f.add_quantity(LDouble(
        'Plateau',
        def_value=0,
        low_lim=0,
        unit='s',
        state_quant=bool_uni_shape,
        states=True,
        show_in_measurement_dlg=True,
    ))
    #endregion Group: Pulse settings

    # Pulse for individual qubit
    #region Group: Qubit #
    for i in range(MAX_QUBITS):
        qubit = i+1
        f.add_group(f'Qubit #{qubit}')
        f.add_quantity(LDouble(
            f'Amplitude #{qubit}',
            label='Amplitude',
            def_value=1,
            unit='V',
            state_quant=bool_uni_amp,
            states=False,
            show_in_measurement_dlg=True,
        ))

        f.add_quantity(LDouble(
            f'Width #{qubit}',
            label='Width',
            def_value=10e-9,
            low_lim=0,
            unit='s',
            state_quant=bool_uni_shape,
            states=False,
        ))

        f.add_quantity(LDouble(
            f'Plateau #{qubit}',
            label='Plateau',
            def_value=0,
            low_lim=0,
            unit='s',
            state_quant=bool_uni_shape,
            states=False,
        ))

        f.add_quantity(LDouble(
            f'Frequency #{qubit}',
            label='Frequency',
            unit='Hz',
        ))

        f.add_quantity(LDouble(
            f'DRAG scaling #{qubit}',
            label='DRAG scaling',
            def_value=0.25e-9,
            unit='s',
            state_quant=bool_use_drag,
            states=True,
        ))

        f.add_quantity(LDouble(
            f'DRAG frequency detuning #{qubit}',
            label='DRAG frequency detuning',
            def_value=0,
            unit='Hz',
            state_quant=bool_use_drag,
            states=True,
        ))
    #endregion Group: Qubit #
    #endregion Section: 1-QB gates XY

    #region Section: 1-QB gates Z
    f.add_section('1-QB gates Z')
    #region Group: Pulse settings
    f.add_group('Pulse settings')

    combo_pulse_type = LCombo(
        'Pulse type, Z',
        label='Pulse type',
        combo=PULSES_1QB,
    )
    f.add_quantity(combo_pulse_type)

    f.add_quantity(LDouble(
        'Truncation range, Z',
        label='Truncation range',
        tooltip='Truncate at ? σ',
        def_value=3,
        state_quant=combo_pulse_type,
        states=[
            PULSE_GAUSSIAN,
        ],
    ))

    f.add_quantity(LBoolean(
        'Half cosine, Z',
        label='Half cosine',
        def_value=False,
        state_quant=combo_pulse_type,
        states=[
            PULSE_COSINE,
        ],
    ))

    f.add_quantity(LBoolean(
        'Start at zero, Z',
        label='Start at zero',
        def_value=False,
        state_quant=combo_pulse_type,
        states=[
            PULSE_GAUSSIAN,
        ],
    ))

    bool_uni_amp = LBoolean(
        'Uniform amplitude, Z',
        label='Uniform amplitude',
        def_value=False,
    )
    f.add_quantity(bool_uni_amp)

    f.add_quantity(LDouble(
        'Amplitude, Z',
        label='Amplitude',
        def_value=1,
        unit='V',
        state_quant=bool_uni_amp,
        states=True,
        show_in_measurement_dlg=True,
    ))

    bool_uni_shape = LBoolean(
        'Uniform pulse shape, Z',
        label='Uniform pulse shape',
        def_value=True,
    )
    f.add_quantity(bool_uni_shape)

    f.add_quantity(LDouble(
        'Width, Z',
        label='Width',
        def_value=10e-9,
        low_lim=0,
        unit='s',
        state_quant=bool_uni_shape,
        states=True,
        show_in_measurement_dlg=True,
    ))

    f.add_quantity(LDouble(
        'Plateau, Z',
        label='Plateau',
        def_value=0,
        low_lim=0,
        unit='s',
        state_quant=bool_uni_shape,
        states=True,
        show_in_measurement_dlg=True,
    ))
    #endregion Group: Pulse settings
    
    # Pulse for individual qubit
    #region Group: Qubit #
    for i in range(MAX_QUBITS):
        qubit = i+1
        f.add_group(f'Qubit #{qubit}')
        f.add_quantity(LDouble(
            f'Amplitude #{qubit}, Z',
            label='Amplitude',
            def_value=1,
            unit='V',
            state_quant=bool_uni_amp,
            states=False,
            show_in_measurement_dlg=True,
        ))

        f.add_quantity(LDouble(
            f'Width #{qubit}, Z',
            label='Width',
            def_value=10e-9,
            low_lim=0,
            unit='s',
            state_quant=bool_uni_shape,
            states=False,
        ))

        f.add_quantity(LDouble(
            f'Plateau #{qubit}, Z',
            label='Plateau',
            def_value=0,
            low_lim=0,
            unit='s',
            state_quant=bool_uni_shape,
            states=False,
        ))
    #endregion Group: Qubit #
    #endregion Section: 1-QB gates Z
    
    #region Section: Readout Z shift
    f.add_section('Readout Z shift')
    #region Group: Readout Z shift
    f.add_group('Readout Z shift')
    f.add_quantity(LBoolean(
        'Use readout Z shift',
        label='Activate',
        def_value=False,
    ))

    for s in ['before', 'after']:
        f.add_quantity(LDouble(
            f'Time {s} readout, readout Z shift',
            label=f'Time {s} readout',
            unit='s',
            def_value=10e-9,
        ))
    #endregion Group: Readout Z shift

    #region Group: Cosine pulse settings
    f.add_group('Cosine pulse settings')

    f.add_quantity(LDouble(
        'Ringup, readout Z shift',
        label='Ring-up time',
        def_value=0,
        unit='s',
    ))
    #endregion Group: Cosine pulse settings

    #region Group: readout Z shift amplitude
    f.add_group('readout Z shift amplitude')

    for i in range(MAX_QUBITS):
        qubit = i+1
        f.add_quantity(LDouble(
            f'Amplitude #{qubit}, readout Z shift',
            label=f'Amplitude #{qubit}',
            def_value=0,
            unit='V',
        ))
    #endregion Group: readout Z shift amplitude
    #endregion Section: Readout Z shift
    
    #region Section: Global Z offset
    f.add_section('Global Z offset')
    #region Group: Global Z offset
    f.add_group('Global Z offset')

    bool_use_global_Z_offset = LBoolean(
        'Use global Z offset',
        label='Activate',
        def_value=False,
    )
    f.add_quantity(bool_use_global_Z_offset)

    bool_extend_to_readout = LBoolean(
        'Extend Z offset to readout',
        label='Extend Z offset to readout',
        def_value=True,
    )
    f.add_quantity(bool_extend_to_readout)

    f.add_quantity(LDouble(
        'Time after readout, Z global',
        label='Time after readout',
        def_value=10e-9,
        unit='s',
        state_quant=bool_extend_to_readout,
        states=True,
    ))
    #endregion Group: Global Z offset

    #region Group: Cosine pulse settings
    f.add_group('Cosine pulse settings')

    f.add_quantity(LDouble(
        'Ringup, Z global',
        label='Ring-up time',
        def_value=20e-9,
        unit='s',
    ))
    #endregion Group: Cosine pulse settings

    #region Group: Z offset amplitudes
    f.add_group('Z offset amplitudes')

    for i in range(MAX_QUBITS):
        qubit = i+1
        f.add_quantity(LDouble(
            f'Amplitude #{qubit}, Z global',
            label=f'Amplitude #{qubit}',
            def_value=0,
            unit='V',
        ))
    #endregion Group: Z offset amplitudes
    #endregion Section: Global Z offset

    #region Section: QB spectra
    f.add_section('QB spectra')
    for i in range(MAX_QUBITS):
        qubit = i+1
        f.add_group(f'Qubit #{qubit}')

        f.add_quantity(LDouble(
            f'Ec #{qubit}',
            label='Ec',
            unit='Hz',
            def_value=200e6,
        ))

        f.add_quantity(LDouble(
            f'f01 max #{qubit}',
            label='f01 max',
            unit='Hz',
            def_value=5e9,
        ))

        f.add_quantity(LDouble(
            f'f01 min #{qubit}',
            label='f01 min',
            unit='Hz',
            def_value=4e9,
        ))

        f.add_quantity(LDouble(
            f'Vperiod #{qubit}',
            label='Voltage period',
            unit='V',
            def_value=1,
        ))

        f.add_quantity(LDouble(
            f'Voffset #{qubit}',
            label='Voltage offset',
            unit='V',
            def_value=0,
        ))

        f.add_quantity(LDouble(
            f'V0 #{qubit}',
            label='Voltage operating point',
            unit='V',
            def_value=0,
        ))
    #endregion Section: QB spectra

    #region Section: 2-QB gates
    f.add_section('2-QB gates')
    #region Group: 2-QB pulses
    f.add_group('2-QB pulses')

    combo_pulse_type = LCombo(
        'Pulse type, 2QB',
        label='Pulse type',
        combo=PULSES_1QB + PULSES_2QB,
        def_value=PULSE_CZ,
    )
    f.add_quantity(combo_pulse_type)

    f.add_quantity(LDouble(
        'Truncation range, 2QB',
        label='Truncation range',
        tooltip='Truncate at ? σ',
        def_value=3,
        state_quant=combo_pulse_type,
        states=[
            PULSE_GAUSSIAN,
        ],
    ))

    f.add_quantity(LBoolean(
        'Half cosine, 2QB',
        label='Half cosine',
        def_value=False,
        state_quant=combo_pulse_type,
        states=[
            PULSE_COSINE,
        ],
    ))

    f.add_quantity(LBoolean(
        'Start at zero, 2QB',
        label='Start at zero',
        def_value=False,
        state_quant=combo_pulse_type,
        states=[
            PULSE_GAUSSIAN,
        ],
    ))

    bool_uni = LBoolean(
        'Uniform 2QB pulses',
        def_value=True,
    )
    f.add_quantity(bool_uni)

    f.add_quantity(LDouble(
        'Width, 2QB',
        label='Width',
        def_value=50e-9,
        low_lim=0,
        unit='s',
        state_quant=bool_uni,
        states=True,
        show_in_measurement_dlg=True,
    ))

    f.add_quantity(LDouble(
        'Plateau, 2QB',
        label='Plateau',
        def_value=0,
        low_lim=0,
        unit='s',
        state_quant=bool_uni_shape,
        states=True,
        show_in_measurement_dlg=True,
    ))

    fourier_terms = list(range(1,MAX_FOURIER_TERMS+1))
    combo_fourier = LCombo(
        'Fourier terms, 2QB',
        label='Fourier Terms',
        combo=fourier_terms,
        def_value=fourier_terms[0],
        tooltip=(
            'Number of fourier terms used to define the pulseshape of the '
            'C-phase gate'
        ),
        state_quant=combo_pulse_type,
        states=[
            PULSE_CZ,
            PULSE_NETZERO,
        ],
    )
    f.add_quantity(combo_fourier)
    #endregion Group: 2-QB pulses

    #region Group: 2-QB pulse #
    for i in range(MAX_QUBITS-1):
        f.add_group(f'Qubit #{i+1}-#{i+2}')

        f.add_quantity(LDouble(
            f'Amplitude, 2QB #{i+1}{i+2}',
            label='Amplitude',
            def_value=1,
            unit='V',
            state_quant=combo_pulse_type,
            states=[
                PULSE_GAUSSIAN,
                PULSE_SQUARE,
                PULSE_RAMP,
                PULSE_COSINE,
            ],
            show_in_measurement_dlg=True,
        ))

        f.add_quantity(LDouble(
            f'Width, 2QB #{i+1}{i+2}',
            label='Width',
            def_value=50e-9,
            low_lim=0,
            unit='s',
            state_quant=bool_uni,
            states=False,
        ))

        f.add_quantity(LDouble(
            f'Plateau, 2QB #{i+1}{i+2}',
            label='Plateau',
            def_value=0,
            low_lim=0,
            unit='s',
            state_quant=bool_uni,
            states=False,
        ))

        f.add_quantity(LBoolean(
            f'Assume linear dependence #{i+1}{i+2}',
            label='Assume linear dependence',
            def_value=True,
            tooltip=(
                'Assumes a linear dependence between frequency and voltage. If '
                'false, use the qubit spectrum.'
            ),
            state_quant=combo_pulse_type,
            states=[
                PULSE_CZ,
                PULSE_NETZERO,
            ],
        ))

        f.add_quantity(LDouble(
            f'df/dV, 2QB #{i+1}{i+2}',
            label='df/dV',
            def_value=0.5e9,
            unit='Hz/V',
            tooltip=(
                'Translating pulseshape from frequency space to voltage '
                'assuming a linear dependence'
            ),
            state_quant=combo_pulse_type,
            states=[
                PULSE_CZ,
                PULSE_NETZERO,
            ],
        ))

        f.add_quantity(LDouble(
            f'f11-f20 initial, 2QB #{i+1}{i+2}',
            label='f11-f20 initial',
            def_value=0.3e9,
            unit='Hz',
            tooltip=(
                'Initial frequency splitting between the |11> state and the '
                '|02> state'
            ),
            state_quant=combo_pulse_type,
            states=[
                PULSE_CZ,
                PULSE_NETZERO,
            ],
        ))

        f.add_quantity(LDouble(
            f'f11-f20 final, 2QB #{i+1}{i+2}',
            label='f11-f20 final',
            def_value=0.05e9,
            unit='Hz',
            tooltip=(
                'Smallest frequency splitting between the |11> state and the '
                '|02> state during the C-phase gate'
            ),
            state_quant=combo_pulse_type,
            states=[
                PULSE_CZ,
                PULSE_NETZERO,
            ],
        ))

        f.add_quantity(LDouble(
            f'Coupling, 2QB #{i+1}{i+2}',
            label='Coupling',
            def_value=0.025e9,
            unit='Hz',
            tooltip='Coupling strength between |11> state and |02> state',
            state_quant=combo_pulse_type,
            states=[
                PULSE_CZ,
                PULSE_NETZERO,
            ],
        ))

        f.add_quantity(LDouble(
            f'L1, 2QB #{i+1}{i+2}',
            label='L1',
            def_value=1,
            tooltip=(
                'First fourier coefficient used to define the pulse shape of '
                'the C-phase gate.'
            ),
            state_quant=combo_fourier,
            states=fourier_terms,
        ))

        for j in range(2, MAX_FOURIER_TERMS+1):
            f.add_quantity(LDouble(
                f'L{j}, 2QB #{i+1}{i+2}',
                label=f'L{j}',
                def_value=0,
                state_quant=combo_fourier,
                states=fourier_terms[j-1:],
            ))
        
        for j in range(2):
            f.add_quantity(LDouble(
                f'QB{j+1} Phi 2QB #{i+1}{i+2}',
                label=f'QB{j+1} Phase shift',
                def_value=0,
            ))

        f.add_quantity(LBoolean(
            f'Negative amplitude #{i+1}{i+2}',
            label='Negative amplitude',
            def_value=False,
            tooltip='Flip the sign of the amplitude of the CZ pulse',
            state_quant=combo_pulse_type,
            states=[
                PULSE_CZ,
                PULSE_NETZERO,
            ],
        ))
    #endregion Group: 2-QB pulse #
    #endregion Section: 2-QB gates

    #region Section: Tomography
    f.add_section('Tomography')
    #region Group: Tomography
    f.add_group('Tomography')

    f.add_quantity(LBoolean(
        'Generate process tomography prepulse',
        def_value=False,
    ))

    f.add_quantity(LBoolean(
        'Generate state tomography postpulse',
        def_value=False,
    ))
    #endregion Group: Tomography

    #region Group: State tomography setup
    f.add_group('State tomography setup')

    tomo_1q = 'Single qubit'
    tomo_2q_9 = 'Two qubit (9 pulse set)'
    tomo_2q_30 = 'Two qubit (30 pulse set)'
    tomo_2q_36 = 'Two qubit (36 pulse set)'
    combo_tomo = LCombo(
        'Tomography scheme',
        def_value=tomo_1q,
        combo=[
            tomo_1q,
            tomo_2q_9,
            tomo_2q_30,
            tomo_2q_36,
        ],
    )
    f.add_quantity(combo_tomo)

    gate_1q = ['I', 'Xp', 'Y2p', 'X2m']
    gate_1q_sym = list(zip(['0', '1', 'X', 'Y'], gate_1q))
    f.add_quantity(LCombo(
        'Process tomography prepulse index 1-QB',
        label='Prepulse index 1-QB',
        combo=[f'{s}: {x}' for (s,x) in gate_1q_sym],
        state_quant=combo_tomo,
        states=[
            tomo_1q,
        ],
        show_in_measurement_dlg=True,
    ))

    f.add_quantity(LCombo(
        'Process tomography prepulse index 2-QB',
        label='Prepulse index 2-QB',
        combo=[
            f'{s1}{s2}: {x1}-{x2}'
            for (s1,x1) in gate_1q_sym
            for (s2,x2) in gate_1q_sym
        ],
        state_quant=combo_tomo,
        states=[
            tomo_2q_9,
            tomo_2q_30,
            tomo_2q_36,
        ],
        show_in_measurement_dlg=True,
    ))

    gate_1q = ['I', 'X2p', 'Y2m']
    gate_1q_sym = list(zip(['Z', 'Y', 'X'], gate_1q))
    f.add_quantity(LCombo(
        'Tomography pulse index 1-QB',
        label='Postpulse index 1-QB',
        combo=[f'{s}: {x}' for (s,x) in gate_1q_sym],
        state_quant=combo_tomo,
        states=[
            tomo_1q
        ],
        show_in_measurement_dlg=True,
    ))

    f.add_quantity(LCombo(
        'Tomography pulse index 2-QB (9 pulse set)',
        label='Postpulse index 2-QB',
        combo=[
            f'{s1}{s2}: {x1}-{x2}'
            for (s1,x1) in gate_1q_sym
            for (s2,x2) in gate_1q_sym
        ],
        state_quant=combo_tomo,
        states=[
            tomo_2q_9,
        ],
        show_in_measurement_dlg=True,
    ))

    f.add_quantity(LCombo(
        'Tomography pulse index 2-QB (30 pulse set)',
        label='Postpulse index 2-QB',
        combo=[
            f'{x1}-{x2}'
            for x1 in ['I', 'X2p', 'Y2p', 'Xp']
            for x2 in ['I', 'X2p', 'Y2p', 'Xp']
        ][:-1] + [
            f'{x1}-{x2}'
            for x1 in ['I', 'X2m', 'Y2m', 'Xm']
            for x2 in ['I', 'X2m', 'Y2m', 'Xm']
        ][1:-1],
        state_quant=combo_tomo,
        states=[
            tomo_2q_30,
        ],
        show_in_measurement_dlg=True,
    ))

    f.add_quantity(LCombo(
        'Tomography pulse index 2-QB (36 pulse set)',
        label='Postpulse index 2-QB',
        combo=[
            f'{x1}-{x2}'
            for x1 in ['I', 'Xp', 'X2p', 'X2m', 'Y2p', 'Y2m']
            for x2 in ['I', 'Xp', 'X2p', 'X2m', 'Y2p', 'Y2m']
        ],
        state_quant=combo_tomo,
        states=[
            tomo_2q_36,
        ],
        show_in_measurement_dlg=True,
    ))
    #endregion Group: State tomography setup

    #region Group: Qubits for tomography
    f.add_group('Qubits for tomography')

    f.add_quantity(LCombo(
        'Qubit for tomography',
        label='Qubit #',
        combo=qubit_list,
        state_quant=combo_tomo,
        states=[
            tomo_1q,
        ],
    ))

    for i in range(2):
        f.add_quantity(LCombo(
            f'Qubit {i+1} # tomography',
            label=f'Qubit {i+1} #',
            def_value=qubit_list[i],
            combo=qubit_list,
            state_quant=combo_tomo,
            states=[
                tomo_2q_9,
                tomo_2q_30,
                tomo_2q_36,
            ],
        ))
    #endregion Group: Qubits for tomography
    #endregion Section: Tomography

    #region Section: Predistortion
    f.add_section('Predistortion')
    #region Group: XY Predistortion
    f.add_group('XY Predistortion')
    
    f.add_quantity(LBoolean(
        'Predistort waveforms',
        def_value=False,
    ))

    for i in range(MAX_QUBITS):
        qubit = i+1
        f.add_quantity(LPath(
            f'Transfer function #{qubit}',
        ))
    #endregion Group: XY Predistortion

    #region Group: Z Predistorion
    f.add_group('Z Predistorion')
    
    f.add_quantity(LBoolean(
        'Predistort Z',
        def_value=False,
    ))

    bool_uni = LBoolean(
        'Uniform predistort Z',
        def_value=False,
    )
    f.add_quantity(bool_uni)
    
    #endregion Group: Z Predistortion

    #region Group: Z
    for i in range(-1, MAX_QUBITS):
        if i == -1:
            qubit = ''
            f.add_group('Uniform predistort Z')
        else:
            qubit = i+1
            f.add_group(f'Qubit #{qubit}')

        bool_from_str = LBoolean(
            f'Predistort Z{qubit} - from string',
            label='From representation string',
            def_value=False,
        )
        f.add_quantity(bool_from_str)

        for j in range(Z_PREDISTORTION_TERMS_COMP):
            f.add_quantity(LDouble(
                f'Predistort Z{qubit} - A{j+1}',
                label=f'A{j+1}',
                tooltip='Amplitude of second-order IIR filter',
            ))
            f.add_quantity(LDouble(
                f'Predistort Z{qubit} - tauA{j+1}',
                label=f'tau A{j+1}',
                tooltip='Decay time of second-order IIR filter',
                low_lim=0,
                unit='s',
            ))
            f.add_quantity(LDouble(
                f'Predistort Z{qubit} - TA{j+1}',
                label=f'T A{j+1}',
                tooltip='Oscillation period of second-order IIR filter',
                low_lim=0,
                unit='s',
            ))
            f.add_quantity(LDouble(
                f'Predistort Z{qubit} - phiA{j+1}',
                label=f'phi A{j+1}',
                tooltip='Initial phase of second-order IIR filter',
                unit='deg',
            ))

        for j in range(Z_PREDISTORTION_TERMS):
            f.add_quantity(LDouble(
                f'Predistort Z{qubit} - B{j+1}',
                label=f'B{j+1}',
                tooltip='Amplitude of first-order IIR filter',
            ))
            f.add_quantity(LDouble(
                f'Predistort Z{qubit} - tauB{j+1}',
                label=f'tau B{j+1}',
                tooltip='Decay time of first-order IIR filter',
                low_lim=0,
                unit='s',
            ))

        f.add_quantity(LDouble(
            f'Predistort Z{qubit} - tauC',
            label=f'tau C',
            tooltip='Time constant for capacitor.',
            low_lim=0,
            unit='s',
        ))

        f.add_quantity(LDouble(
            f'Predistort Z{qubit} - leakC',
            label=f'leak C',
            tooltip='leak voltage of capacitor.',
            def_value=0,
            low_lim=0,
            high_lim=1,
        ))

        f.add_quantity(LString(
            f'Predistort Z{qubit} - string',
            label=f'Representation string',
            tooltip='String representation for `Filter`',
        ))
    #endregion Group: Z
    #endregion Section: Predistortion

    #region Section: Cross-talk
    f.add_section('Cross-talk')
    #region Group: Cross-talk
    f.add_group('Cross-talk')

    f.add_quantity(LBoolean(
        'Compensate cross-talk',
        def_value=False,
    ))

    f.add_quantity(LPath(
        'Cross-talk (CT) matrix',
    ))

    f.add_quantity(LBoolean(
        '1-1 QB <--> Crosstalk matrix',
        tooltip='One-to-one QB to Cross-talk matrix element correspondence',
        def_value=True,
    ))

    for i in range(MAX_CT_QUBITS):
        f.add_quantity(LCombo(
            f'CT-matrix element #{i+1}',
            tooltip=(
                'Which QB/output corresponds to which element of the cross-talk '
                'matrix'
            ),
            def_value='None',
            combo=qubit_list + ['None'],
            state_quant=combo_qubits,
            states=qubit_list[i:MAX_CT_QUBITS],
        ))
    #endregion Group: Cross-talk
    #endregion Section: Cross-talk

    #region Section: Readout
    f.add_section('Readout')
    #region Group: Readout
    f.add_group('Readout')

    bool_uni_amp = LBoolean(
        'Uniform readout amplitude',
        label='Uniform amplitude',
        def_value=True,
    )
    f.add_quantity(bool_uni_amp)

    f.add_quantity(LDouble(
        'Readout amplitude',
        label='Amplitude',
        def_value=0.1,
        unit='V',
        state_quant=bool_uni_amp,
        states=True,
        show_in_measurement_dlg=True,
    ))

    for i in range(MAX_READOUT_SECTION):
        f.add_quantity(LDouble(
            f'Readout relative amplitude {i+1}',
            label=f'Relative amplitude {i+1}',
            def_value=1,
            state_quant=bool_uni_amp,
            states=True,
            show_in_measurement_dlg=True,
        ))

    bool_uni_shape = LBoolean(
        'Uniform readout pulse shape',
        label='Uniform pulse shape',
        def_value=True,
    )
    f.add_quantity(bool_uni_shape)

    for i in range(MAX_READOUT_SECTION):
        f.add_quantity(LDouble(
            f'Readout duration {i+1}',
            label=f'Duration {i+1}',
            def_value=2e-6,
            low_lim=0,
            unit='s',
            state_quant=bool_uni_shape,
            states=True,
        ))

    f.add_quantity(LBoolean(
        'Match main sequence waveform size',
        tooltip=(
            'If checked, the readout waveform will have the same number of '
            'point as the main pulse waveforms'
        ),
        def_value=False,
    ))

    f.add_quantity(LBoolean(
        'Distribute readout phases',
        tooltip=(
            'If checked, the readout tone phases will be distributed to avoid '
            'large peak-to-peak voltages'
        ),
        def_value=False,
    ))

    f.add_quantity(LDouble(
        'Readout delay',
        unit='s',
        show_in_measurement_dlg=True,
    ))

    f.add_quantity(LDouble(
        'Readout I/Q ratio',
        def_value=1,
        tooltip=(
            'Ratio of I/Q voltages to compensate for I/Q mixer arm imbalance.'
        ),
    ))

    for s in ['I', 'Q']:
        f.add_quantity(LDouble(
            f'Readout offset - {s}',
            label=f'Offset {s}',
            tooltip=f'Readout mixer {s} offset',
            def_value=0,
            unit='V',
        ))

    f.add_quantity(LDouble(
        'Readout IQ skew',
        label='IQ skew',
        def_value=0,
        unit='deg',
        tooltip='Readout IQ mixer phase skew',
    ))
    #endregion Group: Readout

    # Pulse for individual qubit
    #region Group: Qubit #
    for i in range(MAX_QUBITS):
        qubit = i+1
        f.add_group(f'Qubit #{qubit}')

        f.add_quantity(LBoolean(
            f'Readout enabled #{qubit}',
            label='Enabled',
            def_value=True,
        ))
        
        f.add_quantity(LDouble(
            f'Readout amplitude #{qubit}',
            label='Amplitude',
            def_value=0.1,
            unit='V',
            state_quant=bool_uni_amp,
            states=False,
        ))

        for j in range(MAX_READOUT_SECTION):
            f.add_quantity(LDouble(
                f'Readout relative amplitude {j+1} # {qubit}',
                label=f'Relative amplitude {j+1}',
                def_value=1,
                state_quant=bool_uni_amp,
                states=False,
            ))

        for j in range(MAX_READOUT_SECTION):
            f.add_quantity(LDouble(
                f'Readout duration {j+1} #{qubit}',
                label=f'Duration {j+1}',
                def_value=2e-6,
                low_lim=0,
                unit='s',
                state_quant=bool_uni_shape,
                states=False,
            ))

        f.add_quantity(LDouble(
            f'Readout frequency #{qubit}',
            label='Frequency',
            def_value=0,
            unit='Hz',
        ))
    #endregion Group: Qubit #

    #region Group: Readout predistortion
    f.add_group('Readout predistortion')
    
    bool_predistort_readout = LBoolean(
        'Predistort readout waveform',
        tooltip=(
            'If checked, the readout waveform will be predistorted to increase '
            'the rise time'
        ),
        def_value=False,
    )
    f.add_quantity(bool_predistort_readout)

    f.add_quantity(LDouble(
        'Resonator linewidth',
        tooltip='Measured resonator linewidth',
        def_value=1e6,
        unit='Hz',
        state_quant=bool_predistort_readout,
        states=True,
    ))

    f.add_quantity(LDouble(
        'Target rise time',
        tooltip='Intended resonator ring-up time',
        def_value=50e-9,
        unit='s',
        state_quant=bool_predistort_readout,
        states=True,
    ))
    #endregion Group: Readout predistortion

    #region Group: Readout trig
    f.add_group('Readout trig')
    
    f.add_quantity(LBoolean(
        'Generate readout trig',
    ))

    f.add_quantity(LDouble(
        'Readout trig amplitude',
        def_value=1,
        unit='V',
    ))

    f.add_quantity(LDouble(
        'Readout trig duration',
        def_value=20e-9,
        unit='s',
    ))
    #endregion Group: Readout trig
    #endregion Section: Readout

    #region Section: Output
    f.add_section('Output')
    #region Group: Output
    f.add_group('Output')

    f.add_quantity(LBoolean(
        'Swap IQ',
    ))
    #endregion Group: Output

    # Gate settings
    #region Group: Microwave gate switch
    f.add_group('Microwave gate switch')

    bool_gen_gate = LBoolean(
        'Generate gate',
        def_value=True,
    )
    f.add_quantity(bool_gen_gate)

    f.add_quantity(LBoolean(
        'Uniform gate',
        def_value=False,
        state_quant=bool_gen_gate,
        states=True,
    ))

    f.add_quantity(LDouble(
        'Gate delay',
        unit='s',
        def_value=-60e-9,
        low_lim=-1e-6,
        high_lim=1e-6,
    ))

    f.add_quantity(LDouble(
        'Gate overlap',
        unit='s',
        def_value=20e-9,
    ))

    f.add_quantity(LDouble(
        'Minimal gate time',
        unit='s',
        def_value=20e-9,
    ))
    #endregion Group: Microwave gate switch

    #region Group: Output filters
    f.add_group('Output filters')

    fil_rec = 'Rectangular'
    fil_bar = 'Bartlett'
    fil_bla = 'Blackman'
    fil_ham = 'Hamming'
    fil_han = 'Hanning'
    fil_kai = 'Kaiser'
    for s in ['Gate', 'Z']:
        if s=='Gate':
            bool_filter = LBoolean(
                f'Filter gate waveforms',
                def_value=False,
            )
        else:
            bool_filter = LBoolean(
                f'Filter Z waveforms',
                def_value=False,
            )
        f.add_quantity(bool_filter)

        combo_filter = LCombo(
            f'{s} filter',
            def_value=fil_han,
            combo=[
                fil_rec,
                fil_bar,
                fil_bla,
                fil_ham,
                fil_han,
                fil_kai,
            ],
            state_quant=bool_filter,
            states=True,
        )
        f.add_quantity(combo_filter)

        f.add_quantity(LDouble(
            f'{s} - Filter size',
            label='Filter size',
            def_value=5,
            low_lim=1,
            state_quant=bool_filter,
            states=True,
        ))

        f.add_quantity(LDouble(
            f'{s} - Kaiser beta',
            label='Kaiser beta parameter',
            def_value=14,
            state_quant=combo_filter,
            states=[
                fil_kai,
            ],
        ))
    #endregion Group: Output filters

    #region Group: Traces
    f.add_group('Traces')
    for i in range(MAX_QUBITS):
        qubit = i+1
        if i>0:
            state_quant = combo_qubits
            states = qubit_list[i:]
        else:
            state_quant = None
            states = None
        for trace in ['I','Q','G','Z']:
            f.add_quantity(LVector(
                f'Trace - {trace}{qubit}',
                unit='V',
                x_name='Time',
                x_unit='s',
                permission='READ',
                state_quant=state_quant,
                states=states,
                show_in_measurement_dlg=True,
            ))
    
    for trace in ['trig', 'I', 'Q']:
        f.add_quantity(LVector(
            f'Trace - Readout {trace}',
            unit='V',
            x_name='Time',
            x_unit='s',
            permission='READ',
            show_in_measurement_dlg=True,
        ))
    #endregion Group: Traces
    #endregion Section: Output

    #region Section: Demodulation
    f.add_section('Demodulation')
    #region Group: Demodulation
    f.add_group('Demodulation')

    f.add_quantity(LDouble(
        'Demodulation - Skip',
        label='Skip start',
        def_value=0,
        unit='s',
    ))

    f.add_quantity(LDouble(
        'Demodulation - Length',
        label='Length',
        def_value=1e-6,
        unit='s',
    ))

    f.add_quantity(LDouble(
        'Demodulation - Frequency offset',
        label='Frequency offset',
        def_value=0,
        unit='Hz',
        tooltip=(
            'Frequency difference between LO used for up- and downconversion, '
            'f_down - f_up'
        ),
    ))

    f.add_quantity(LDouble(
        'Demodulation - Number of records',
        label='Number of records',
        def_value=1,
        low_lim=1,
        tooltip=(
            'NB!  This will be removed in future versions, records should be '
            'set by input waveform'
        ),
    ))

    f.add_quantity(LBoolean(
        'Use phase reference signal',
        def_value=True,
    ))

    bool_demo_IQ = LBoolean(
        'Demodulation - IQ',
        def_value=False,
    )
    f.add_quantity(bool_demo_IQ)

    f.add_quantity(LVector(
        'Demodulation - Input',
        unit='V',
        x_name='Time',
        x_unit='s',
        permission='WRITE',
        state_quant=bool_demo_IQ,
        states=False,
        show_in_measurement_dlg=True,
    ))

    for trace in ['I', 'Q']:
        f.add_quantity(LVector(
            f'Demodulation - Input {trace}',
            unit='V',
            x_name='Time',
            x_unit='s',
            permission='WRITE',
            state_quant=bool_demo_IQ,
            states=True,
            show_in_measurement_dlg=True,
        ))

    f.add_quantity(LVector(
        'Demodulation - Reference',
        unit='V',
        x_name='Time',
        x_unit='s',
        permission='WRITE',
        show_in_measurement_dlg=True,
    ))

    for i in range(MAX_QUBITS):
        qubit = i+1
        if i>0:
            state_quant = combo_qubits
            states = qubit_list[i:]
        else:
            state_quant = None
            states = None
        f.add_quantity(LComplex(
            f'Voltage, QB{qubit}',
            unit='V',
            permission='READ',
            state_quant=state_quant,
            states=states,
            show_in_measurement_dlg=True,
        ))
    
    for i in range(MAX_QUBITS):
        qubit = i+1
        if i>0:
            state_quant = combo_qubits
            states = qubit_list[i:]
        else:
            state_quant = None
            states = None
        f.add_quantity(LVectorComplex(
            f'Single-shot, QB{qubit}',
            unit='V',
            permission='READ',
            state_quant=state_quant,
            states=states,
            show_in_measurement_dlg=True,
        ))
    #endregion Group: Demodulation
    #endregion Section: Demodulation
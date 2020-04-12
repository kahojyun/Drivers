# Multi-Qubit Pulse Generator
The mult-qubit pulse generator creates baseband pulses for applying X/Y and Z rotations to systems with superconducting qubits.

The driver uses a library for generating the sequences, which are organized in the following modules and classes:

## sequence.py

Classes for defining gate sequences.  To create a new sequence, subclass the **Sequence** class and implement the gate sequence in the function *generate_sequence*.  The built-in sequences are defined in the file *sequence_builtin.py*

## pulse.py

Classes and code related to creating pulses for driving qubits.

## predistortion.py

Classes and code related to predistorting waveforms to fix pulse imperfections.

## crosstalk.py

Classes and code related to minimizing and compensating for signal crosstalk.

## readout.py

Classes and code for generating waveforms for reading out superconducting qubits.

## docs
Run make html or make latexpdf to create the documentation for the driver.


## Change log

### v 1.6.1
- Support multiple section readout pulses

### v 1.6.0
- Support second order IIR filter predistortion.

### v 1.5.2
- Use `round` to get integer value from Labber config.
- Use double datatype to store number of pulses in generic sequence section.

### v 1.5.1
- Generic sequence support custom pre/post pulse and cycling sequence.

### v 1.5.0
- Improve custom sequence pulse timing setting.

### v 1.4.1
Merge with YF edition.
- Enable `readout_delay` to be <0.
- Remove high/low limit on global Z offset amplitudes.
- Add `readout Z shift` function.
- Z gate definition.
- Add support for readout IQ balance.
- Unified pulse duration definition. 

### v 1.4.0
- Add 2QB XEB sequence.

### v 1.3.0
- Add generic sequence.
- Add control for individual qubit's readout output.

### v 1.2.0
- Change definition of gaussian pulse truncation range.
- Support predistortion of capacitor response.
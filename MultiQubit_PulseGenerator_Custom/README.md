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


## Change 

### v 1.9.0
- Add `1-QB XEB`
- Add `W` gates for `XEB`

### v 1.8.0
- Add `Test pulse` section
- 2QRB: interleaved `Ref`
- Copy & paste for single qubit XY and test pulse

### v 1.7.1
- Fix typo in configuration `Readout relative amplitude`

### v 1.7.0
- Support virtual Z gate when using custom sequence in 2QRB/XEB.
- Virtual Z gate also applies to iSWAP.

### v 1.6.5
- Add `Net zero` option to all pulse shape
- Support choosing qubit on which 2QB pulse apply.

### v 1.6.4
- Increase maximum number of pre/post/cycled pulses.
- Crosstalk matrix input.

### v 1.6.3
- Fix 2Q uniform plateau
- Support using custom pulse in 2QRB

### v 1.6.2
- Fix additional spacing between readout pulse and gate sequence in Generic or XEB sequence.
- Add copy & paste functions for generic sequence.

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
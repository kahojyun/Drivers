#!/usr/bin/env python3
# add logger, to allow logging to Labber's instrument log
import logging
import numpy as np

import gates
import pulses
from sequence import Sequence

import write_configuration as CONST

log = logging.getLogger('LabberDriver')


class Rabi(Sequence):
    """Sequence for driving Rabi oscillations in multiple qubits."""

    def generate_sequence(self, config):
        """Generate sequence by adding gates/pulses to waveforms."""
        # just add pi-pulses for the number of available qubits
        self.add_gate_to_all(gates.Xp, align='right')


class CPMG(Sequence):
    """Sequence for multi-qubit Ramsey/Echo/CMPG experiments."""

    def generate_sequence(self, config):
        """Generate sequence by adding gates/pulses to waveforms."""
        # get parameters
        n_pulse = round(config['# of pi pulses'])
        pi_to_q = config['Add pi pulses to Q']
        duration = config['Sequence duration']
        edge_to_edge = config['Edge-to-edge pulses']
        if config['Add last pi/2 pulse to Q']:
            pi2_final = gates.Y2p
        else:
            pi2_final = gates.X2p

        # select type of refocusing pi pulse
        gate_pi = gates.Yp if pi_to_q else gates.Xp

        # always do T1 same way, regardless if edge-to-edge or center-center
        if n_pulse < 0:
            self.add_gate_to_all(gate_pi)
            self.add_gate_to_all(gates.IdentityGate(width=duration), dt=0)

        elif edge_to_edge:
            # edge-to-edge pulsing, set pulse separations
            self.add_gate_to_all(gates.X2p)
            # for ramsey, just add final pulse
            if n_pulse == 0:
                self.add_gate_to_all(gates.X2p, dt=duration)
            else:
                dt = duration / n_pulse
                # add first pi pulse after half duration
                self.add_gate_to_all(gate_pi, dt=dt/2)
                # add rest of pi pulses
                for i in range(n_pulse - 1):
                    self.add_gate_to_all(gate_pi, dt=dt)
                # add final pi/2 pulse
                self.add_gate_to_all(pi2_final, dt=dt/2)

        else:
            # center-to-center spacing, set absolute pulse positions
            self.add_gate_to_all(gates.X2p, t0=0)
            # add pi pulses at right position
            for i in range(n_pulse):
                self.add_gate_to_all(gate_pi,
                                     t0=(i + 0.5) * (duration / n_pulse))
            # add final pi/2 pulse
            self.add_gate_to_all(pi2_final, t0=duration)


class PulseTrain(Sequence):
    """Sequence for multi-qubit pulse trains, for pulse calibrations."""

    def generate_sequence(self, config):
        """Generate sequence by adding gates/pulses to waveforms."""
        # get parameters
        n_pulse = round(config['# of pulses'])
        alternate = config['Alternate pulse direction']

        if n_pulse == 0:
            self.add_gate_to_all(gates.I)
        for n in range(n_pulse):
            pulse_type = config['Pulse']
            if pulse_type == 'CPh':
                for i in range(self.n_qubit-1):
                    self.add_gate([i, i+1], gates.CPh)
            else:
                if alternate and (n % 2) == 1:
                    pulse_type = pulse_type.replace('p', 'm')
                gate = getattr(gates, pulse_type)
                self.add_gate_to_all(gate)


class SpinLocking(Sequence):
    """ Sequence for spin-locking experiment.

    """

    def generate_sequence(self, config):
        """Generate sequence by adding gates/pulses to waveforms."""

        pulse_amps = []
        for ii in range(9):
            pulse_amps.append(
                float(config['Drive pulse amplitude #' + str(ii + 1)]))
        pulse_duration = float(config['Drive pulse duration'])
        pulse_phase = float(config['Drive pulse phase']) / 180.0 * np.pi
        pulse_sequence = config['Pulse sequence']

        if pulse_sequence == 'SL-3':
            self.add_gate_to_all(gates.Y2p)
        if pulse_sequence == 'SL-5a':
            self.add_gate_to_all(gates.Y2m)
        if pulse_sequence == 'SL-5b':
            self.add_gate_to_all(gates.Y2p)

        if pulse_sequence != 'SL-3':
            self.add_gate_to_all(gates.Xp)

        rabi_gates = []
        for ii in range(self.n_qubit):
            rabi_gates.append(
                gates.RabiGate(pulse_amps[ii], pulse_duration, pulse_phase))
        self.add_gate(list(range(self.n_qubit)), rabi_gates)
        if pulse_sequence != 'SL-3':
            self.add_gate_to_all(gates.Xp)

        if pulse_sequence == 'SL-3':
            self.add_gate_to_all(gates.Y2p)
        if pulse_sequence == 'SL-5a':
            self.add_gate_to_all(gates.Y2m)
        if pulse_sequence == 'SL-5b':
            self.add_gate_to_all(gates.Y2p)

        return


class ReadoutTraining(Sequence):
    """Sequence for training readout state discriminator.

    """

    def generate_sequence(self, config):
        """Generate sequence by adding gates/pulses to waveforms."""

        training_type = config['Training type']
        state = round(config['Training, input state'])
        # currently only supports two states
        n_state = 2

        if training_type == 'Specific qubit':
            # specific qubit, just add gate
            qubit = round(config['Training, qubit']) - 1
            if state:
                self.add_gate(qubit, gates.Xp)

        elif training_type == 'All qubits at once':
            # add to all qubits
            if state:
                self.add_gate_to_all(gates.Xp)

        elif training_type == 'All combinations':
            # get bitstring for current state
            bitstring = np.base_repr(state, n_state, self.n_qubit)
            bitstring = bitstring[::-1][:self.n_qubit]
            qubit_list = []
            gate_list = []
            for n in range(self.n_qubit):
                if int(bitstring[n]):
                    qubit_list.append(n)
                    gate_list.append(gates.Xp)

            self.add_gate(qubit_list, gate_list)

def get_custom_pulse(section, group, prev_duration, config):
    qubit = int(config[f'{section} - {group} - Add to qubit'])-1
    line = config[f'{section} - {group} - Add to line']

    # Construct pulse
    pulse_type = config[f'{section} - {group} - Pulse type']
    if line == 'XY':
        pulse = getattr(pulses, pulse_type)(complex=True)
        pulse.use_drag = config[f'{section} - {group} - Use DRAG']
        if pulse.use_drag:
            pulse.drag_coefficient = config[f'{section} - {group} - DRAG scaling']
            pulse.drag_detuning = config[f'{section} - {group} - DRAG frequency detuning']
    else: # line == 'Z'
        pulse = getattr(pulses, pulse_type)(complex=False)
    pulse.amplitude = config[f'{section} - {group} - Amplitude']
    pulse.width = config[f'{section} - {group} - Width']
    pulse.plateau = config[f'{section} - {group} - Plateau']
    pulse.frequency = config[f'{section} - {group} - Frequency']
    pulse.phase = config[f'{section} - {group} - Phase'] * np.pi / 180
    pulse.start_at_zero = config.get(f'{section} - {group} - Start at zero')
    if pulse_type == CONST.PULSE_GAUSSIAN:
        pulse.truncation_range = config[f'{section} - {group} - Truncation range']
    elif pulse_type == CONST.PULSE_COSINE:
        pulse.half_cosine = config[f'{section} - {group} - Half cosine']
    if config.get(f'{section} - {group} - Net zero'):
        pulse = pulses.NetZero(pulse)
        pulse.net_zero_delay = config.get(f'{section} - {group} - Net zero delay')

    # Pulse timing
    t0 = None
    dt = None
    timing = config[f'{section} - {group} - Pulse timing']
    duration = pulse.total_duration()
    if timing == CONST.TIMING_ABS:
        this_ref = config[f'{section} - {group} - Pulse timing locate']
        t0 = config[f'{section} - {group} - Pulse timing time']
        if this_ref == 'Start':
            t0 += duration / 2
        elif this_ref == 'End':
            t0 -= duration / 2
    elif timing == CONST.TIMING_REL:
        dt = config[f'{section} - {group} - Pulse timing time']
        prev_ref = config[f'{section} - {group} - Pulse timing reference']
        if prev_ref == 'Start':
            dt -= prev_duration
        elif prev_ref == 'Center':
            dt -= prev_duration / 2
        this_ref = config[f'{section} - {group} - Pulse timing locate']
        if this_ref == 'Center':
            dt -= duration / 2
        elif this_ref == 'End':
            dt -= duration
    
    return (qubit, line, t0, dt, pulse)

def get_custom_sequence(section, group, config):
    if len(group) == 0:
        return dict(lqubit=[], lpulse=[], lline=[], ldt=[], dt_before=0, dt_after=0, duration=0)
    t_start = 0
    min_t_start = np.inf
    max_t_end = -np.inf
    lqubit = []
    lpulse = []
    lline = []
    ldt = []
    prev_duration = 0
    for i in range(len(group)):
        (qubit, line, t0, dt, pulse) = get_custom_pulse(section, group[i], prev_duration, config)
        duration = prev_duration = pulse.total_duration()

        # calculate relative spacing dt
        if dt is None and t0 is None:
            # Use global pulse spacing
            dt = config.get('Pulse spacing')
        if dt is None:
            dt = t0 - duration / 2 - t_start
        # Shift pulse if minimum pulse start time < 0
        min_t_start = min(min_t_start, t_start+dt)
        # Avoid double spacing for steps with 0 duration
        if duration != 0:
            t_start = t_start + dt + duration
        max_t_end = max(max_t_end, t_start)
        lqubit.append(qubit)
        lpulse.append(pulse)
        lline.append(line)
        ldt.append(dt)
    dt_before = -min_t_start
    dt_after = max_t_end - t_start
    return dict(lqubit=lqubit, lpulse=lpulse, lline=lline, ldt=ldt, dt_before=dt_before, dt_after=dt_after, duration=max_t_end-min_t_start)

class GenericSequence(Sequence):
    """Generic sequence supporting custom pulse.

    """

    def add_custom_sequence(self, extra_dt, seq):
        lqubit = seq['lqubit']
        lpulse = seq['lpulse']
        lline = seq['lline']
        ldt = seq['ldt']
        dt_before = seq['dt_before']
        dt_after = seq['dt_after']
        extra_dt += dt_before
        for i in range(len(lpulse)):
            self.add_single_pulse(lqubit[i], lpulse[i], lline[i], dt=ldt[i]+extra_dt)
            extra_dt = 0
        return dt_after

    def generate_sequence(self, config):
        """Generate sequence by adding gates/pulses to waveforms."""

        # prepare generic sequence
        pulse_n = round(config['Generic - Number of pulses'])
        pre_n = round(config['Generic - Number of pre-pulse'])
        post_n = round(config['Generic - Number of post-pulse'])
        cycle_n = round(config['Generic - Number of cycles'])
        section = 'Generic'
        pre_seq = get_custom_sequence(section, [f'Pre pulse #{i+1}' for i in range(pre_n)], config)
        cycled_seq = get_custom_sequence(section, [f'Cycled pulse #{i+1}' for i in range(pulse_n)], config)
        post_seq = get_custom_sequence(section, [f'Post pulse #{i+1}' for i in range(post_n)], config)

        extra_dt = 0

        spacing_type = config['Generic - Pre-cycle spacing type']
        pre_cycle_dt = config['Generic - Pre-cycle spacing']
        if spacing_type == 'Start-Start':
            pre_cycle_dt -= pre_seq['duration']
        
        spacing_type = config['Generic - Post-cycle spacing type']
        post_cycle_dt = config['Generic - Post-cycle spacing']
        if spacing_type == 'Start-Start':
            post_cycle_dt -= cycled_seq['duration']

        spacing_type = config['Generic - Cycle spacing type']
        cycle_dt = config['Generic - Cycle spacing']
        if spacing_type == 'Start-Start':
            cycle_dt -= cycled_seq['duration']
        
        cycle_n = round(config['Generic - Number of cycles'])
        # Pre-pulse
        if pre_n > 0:
            extra_dt = self.add_custom_sequence(extra_dt, pre_seq)
            extra_dt += pre_cycle_dt
        # Cycled pulse
        for _ in range(cycle_n):
            extra_dt = self.add_custom_sequence(extra_dt, cycled_seq)
            extra_dt += cycle_dt
        extra_dt -= cycle_dt
        # Post-pulse
        if post_n > 0:
            extra_dt += post_cycle_dt
            extra_dt = self.add_custom_sequence(extra_dt, post_seq)
        self.add_gate_to_all(gates.I0, dt=extra_dt)


if __name__ == '__main__':
    pass

from typing import Optional, Union, Any, Tuple, Sequence, NewType
Pair = Tuple[Union[str, float], Union[None, str, float]]


def _zip_with_none(seq):
    if seq is not None:
        seq = [(x, None) if not isinstance(x, tuple) else x for x in seq]
    return seq


class LItem:
    def __init__(self, item_name: str, **kwargs: Union[None, str, complex, bool]) -> None:
        self.item_name = item_name
        self.settings = kwargs

    def setValue(self, **kwargs):
        self.settings.update(kwargs)

    def getValue(self, key):
        return self.settings.get(key)

    def __str__(self) -> str:
        s = f'[{self.item_name}]\n'
        for (k, v) in self.settings.items():
            if v is not None:
                s += f'{k}: {v}\n'
        return s

class LQuantity(LItem):
    def __init__(
        self,
        quant_name: str,
        datatype: str,
        label: Optional[str] = None,
        unit: Optional[str] = None,
        def_value: Union[None, str, complex, bool] = None,
        tooltip: Optional[str] = None,
        low_lim: Optional[float] = None,
        high_lim: Optional[float] = None,
        x_name: Optional[str] = None,
        x_unit: Optional[str] = None,
        group: Optional[str] = None,
        section: Optional[str] = None,
        state_quant: Union[None, "LCombo", "LBoolean"] = None,
        states: Union[None, bool, Sequence[Union[str, float, Pair]]] = None,
        models: Optional[Sequence[Union[str, float, Pair]]] = None,
        options: Optional[Sequence[Union[str, float, Pair]]] = None,
        combo: Optional[Sequence[Union[str, float, Pair]]] = None,
        permission: Optional[str] = None,
        show_in_measurement_dlg: Optional[bool] = None,
        set_cmd: Optional[str] = None,
        get_cmd: Optional[str] = None,
        sweep_cmd: Optional[str] = None,
        sweep_check_cmd: Optional[str] = None,
        sweep_res: Optional[float] = None,
        stop_cmd: Optional[str] = None,
        sweep_rate: Optional[float] = None,
        sweep_minute: Optional[bool] = None,
        sweep_rate_low: Optional[float] = None,
        sweep_rate_high: Optional[float] = None) -> None:
        super().__init__(
            quant_name,
            datatype=datatype,
            label=label,
            unit=unit,
            def_value=def_value,
            tooltip=tooltip,
            low_lim=low_lim,
            high_lim=high_lim,
            x_name=x_name,
            x_unit=x_unit,
            group=group,
            section=section,
            permission=permission,
            show_in_measurement_dlg=show_in_measurement_dlg,
            set_cmd=set_cmd,
            get_cmd=get_cmd,
            sweep_cmd=sweep_cmd,
            sweep_check_cmd=sweep_check_cmd,
            sweep_res=sweep_res,
            stop_cmd=stop_cmd,
            sweep_rate=sweep_rate,
            sweep_minute=sweep_minute,
            sweep_rate_low=sweep_rate_low,
            sweep_rate_high=sweep_rate_high)
        self.state_quant = state_quant
        if isinstance(state_quant, LBoolean):
            self.states = states
        else:
            if (states is not None) and (not isinstance(states, list)):
                states = [states]
            self.states = _zip_with_none(states)
        self.models = _zip_with_none(models)
        self.options = _zip_with_none(options)
        self.combo = _zip_with_none(combo)
    
    def __str__(self) -> str:
        s = super().__str__()
        if self.states is not None:
            s += f'state_quant: {self.state_quant.item_name}\n'
            if isinstance(self.state_quant, LBoolean):
                s += f'state_value: {self.states}\n'
            else:
                for (i, (k, _)) in enumerate(self.states):
                    s += f'state_value_{i+1}: {k}\n'
        if self.models is not None:
            for (i, (k, _)) in enumerate(self.models):
                s += f'model_value_{i+1}: {k}\n'
        if self.options is not None:
            for (i, (k, _)) in enumerate(self.options):
                s += f'option_value_{i+1}: {k}\n'
        if self.combo is not None:
            for (i, (k, v)) in enumerate(self.combo):
                s += f'combo_def_{i+1}: {k}\n'
                if v is not None:
                    s += f'cmd_def_{i+1}: {v}\n'
        return s


class ModelOptionsSetting(LItem):
    def __init__(
        self,
        models=None,
        check_model=None,
        model_cmd=None,
        options=None,
        check_options=None,
        option_cmd=None):
        super().__init__(
            'Model and options',
            check_model=check_model,
            model_cmd=model_cmd,
            check_options=check_options,
            option_cmd=option_cmd)
        self.models = _zip_with_none(models)
        self.options = _zip_with_none(options)

    def __str__(self):
        s = super().__str__()
        if self.models is not None:
            for (i, (k, v)) in enumerate(self.models):
                s += f'model_str_{i+1}: {k}\n'
                if v is not None:
                    s += f'model_id_{i+1}: {v}\n'
        if self.options is not None:
            for (i, (k, v)) in enumerate(self.options):
                s += f'option_str_{i+1}: {k}\n'
                if v is not None:
                    s += f'option_id_{i+1}: {v}\n'
        return s

class LDouble(LQuantity):
    def __init__(
        self,
        quant_name: str,
        label: Optional[str] = None,
        unit: Optional[str] = None,
        def_value: Optional[float] = None,
        tooltip: Optional[str] = None,
        low_lim: Optional[float] = None,
        high_lim: Optional[float] = None,
        group: Optional[str] = None,
        section: Optional[str] = None,
        state_quant: Union[None, "LCombo", "LBoolean"] = None,
        states: Union[None, bool, Sequence[Union[str, float, Pair]]] = None,
        models: Optional[Sequence[Union[str, float, Pair]]] = None,
        options: Optional[Sequence[Union[str, float, Pair]]] = None,
        permission: Optional[str] = None,
        show_in_measurement_dlg: Optional[bool] = None,
        set_cmd: Optional[str] = None,
        get_cmd: Optional[str] = None,
        sweep_cmd: Optional[str] = None,
        sweep_check_cmd: Optional[str] = None,
        sweep_res: Optional[float] = None,
        stop_cmd: Optional[str] = None,
        sweep_rate: Optional[float] = None,
        sweep_minute: Optional[bool] = None,
        sweep_rate_low: Optional[float] = None,
        sweep_rate_high: Optional[float] = None) -> None:
        super().__init__(
            quant_name,
            datatype='DOUBLE',
            label=label,
            unit=unit,
            def_value=def_value,
            tooltip=tooltip,
            low_lim=low_lim,
            high_lim=high_lim,
            group=group,
            section=section,
            state_quant=state_quant,
            states=states,
            models=models,
            options=options,
            permission=permission,
            show_in_measurement_dlg=show_in_measurement_dlg,
            set_cmd=set_cmd,
            get_cmd=get_cmd,
            sweep_cmd=sweep_cmd,
            sweep_check_cmd=sweep_check_cmd,
            sweep_res=sweep_res,
            stop_cmd=stop_cmd,
            sweep_rate=sweep_rate,
            sweep_minute=sweep_minute,
            sweep_rate_low=sweep_rate_low,
            sweep_rate_high=sweep_rate_high)

class LBoolean(LQuantity):
    def __init__(
        self,
        quant_name: str,
        label: Optional[str] = None,
        def_value: Optional[bool] = None,
        tooltip: Optional[str] = None,
        group: Optional[str] = None,
        section: Optional[str] = None,
        state_quant: Union[None, "LCombo", "LBoolean"] = None,
        states: Union[None, bool, Sequence[Union[str, float, Pair]]] = None,
        models: Optional[Sequence[Union[str, float, Pair]]] = None,
        options: Optional[Sequence[Union[str, float, Pair]]] = None,
        permission: Optional[str] = None,
        show_in_measurement_dlg: Optional[bool] = None,
        set_cmd: Optional[str] = None,
        get_cmd: Optional[str] = None) -> None:
        super().__init__(
            quant_name,
            datatype='BOOLEAN',
            label=label,
            def_value=def_value,
            tooltip=tooltip,
            group=group,
            section=section,
            state_quant=state_quant,
            states=states,
            models=models,
            options=options,
            permission=permission,
            show_in_measurement_dlg=show_in_measurement_dlg,
            set_cmd=set_cmd,
            get_cmd=get_cmd)

class LCombo(LQuantity):
    def __init__(
        self,
        quant_name: str,
        label: Optional[str] = None,
        def_value: Optional[Pair] = None,
        tooltip: Optional[str] = None,
        group: Optional[str] = None,
        section: Optional[str] = None,
        state_quant: Union[None, "LCombo", "LBoolean"] = None,
        states: Union[None, bool, Sequence[Union[str, float, Pair]]] = None,
        models: Optional[Sequence[Union[str, float, Pair]]] = None,
        options: Optional[Sequence[Union[str, float, Pair]]] = None,
        combo: Optional[Sequence[Union[str, float, Pair]]] = None,
        permission: Optional[str] = None,
        show_in_measurement_dlg: Optional[bool] = None,
        set_cmd: Optional[str] = None,
        get_cmd: Optional[str] = None) -> None:
        if isinstance(def_value, tuple):
            def_value = def_value[0]
        super().__init__(
            quant_name,
            datatype='COMBO',
            label=label,
            def_value=def_value,
            tooltip=tooltip,
            group=group,
            section=section,
            state_quant=state_quant,
            states=states,
            models=models,
            options=options,
            combo=combo,
            permission=permission,
            show_in_measurement_dlg=show_in_measurement_dlg,
            set_cmd=set_cmd,
            get_cmd=get_cmd)

class LString(LQuantity):
    def __init__(
        self,
        quant_name: str,
        label: Optional[str] = None,
        def_value: Optional[str] = None,
        tooltip: Optional[str] = None,
        group: Optional[str] = None,
        section: Optional[str] = None,
        state_quant: Union[None, "LCombo", "LBoolean"] = None,
        states: Union[None, bool, Sequence[Union[str, float, Pair]]] = None,
        models: Optional[Sequence[Union[str, float, Pair]]] = None,
        options: Optional[Sequence[Union[str, float, Pair]]] = None,
        permission: Optional[str] = None,
        show_in_measurement_dlg: Optional[bool] = None,
        set_cmd: Optional[str] = None,
        get_cmd: Optional[str] = None) -> None:
        super().__init__(
            quant_name,
            datatype='STRING',
            label=label,
            def_value=def_value,
            tooltip=tooltip,
            group=group,
            section=section,
            state_quant=state_quant,
            states=states,
            models=models,
            options=options,
            permission=permission,
            show_in_measurement_dlg=show_in_measurement_dlg,
            set_cmd=set_cmd,
            get_cmd=get_cmd)

class LComplex(LQuantity):
    def __init__(
        self,
        quant_name: str,
        label: Optional[str] = None,
        unit: Optional[str] = None,
        def_value: Optional[complex] = None,
        tooltip: Optional[str] = None,
        group: Optional[str] = None,
        section: Optional[str] = None,
        state_quant: Union[None, "LCombo", "LBoolean"] = None,
        states: Union[None, bool, Sequence[Union[str, float, Pair]]] = None,
        models: Optional[Sequence[Union[str, float, Pair]]] = None,
        options: Optional[Sequence[Union[str, float, Pair]]] = None,
        permission: Optional[str] = None,
        show_in_measurement_dlg: Optional[bool] = None,
        set_cmd: Optional[str] = None,
        get_cmd: Optional[str] = None) -> None:
        super().__init__(
            quant_name,
            datatype='COMPLEX',
            label=label,
            unit=unit,
            def_value=def_value,
            tooltip=tooltip,
            group=group,
            section=section,
            state_quant=state_quant,
            states=states,
            models=models,
            options=options,
            permission=permission,
            show_in_measurement_dlg=show_in_measurement_dlg,
            set_cmd=set_cmd,
            get_cmd=get_cmd)

class LVector(LQuantity):
    def __init__(
        self,
        quant_name: str,
        label: Optional[str] = None,
        unit: Optional[str] = None,
        tooltip: Optional[str] = None,
        x_name: Optional[str] = None,
        x_unit: Optional[str] = None,
        group: Optional[str] = None,
        section: Optional[str] = None,
        state_quant: Union[None, "LCombo", "LBoolean"] = None,
        states: Union[None, bool, Sequence[Union[str, float, Pair]]] = None,
        models: Optional[Sequence[Union[str, float, Pair]]] = None,
        options: Optional[Sequence[Union[str, float, Pair]]] = None,
        permission: Optional[str] = None,
        show_in_measurement_dlg: Optional[bool] = None) -> None:
        super().__init__(
            quant_name,
            datatype='VECTOR',
            label=label,
            unit=unit,
            tooltip=tooltip,
            x_name=x_name,
            x_unit=x_unit,
            group=group,
            section=section,
            state_quant=state_quant,
            states=states,
            models=models,
            options=options,
            permission=permission,
            show_in_measurement_dlg=show_in_measurement_dlg)

class LVectorComplex(LQuantity):
    def __init__(
        self,
        quant_name: str,
        label: Optional[str] = None,
        unit: Optional[str] = None,
        tooltip: Optional[str] = None,
        x_name: Optional[str] = None,
        x_unit: Optional[str] = None,
        group: Optional[str] = None,
        section: Optional[str] = None,
        state_quant: Union[None, "LCombo", "LBoolean"] = None,
        states: Union[None, bool, Sequence[Union[str, float, Pair]]] = None,
        models: Optional[Sequence[Union[str, float, Pair]]] = None,
        options: Optional[Sequence[Union[str, float, Pair]]] = None,
        permission: Optional[str] = None,
        show_in_measurement_dlg: Optional[bool] = None) -> None:
        super().__init__(
            quant_name,
            datatype='VECTOR_COMPLEX',
            label=label,
            unit=unit,
            tooltip=tooltip,
            x_name=x_name,
            x_unit=x_unit,
            group=group,
            section=section,
            state_quant=state_quant,
            states=states,
            models=models,
            options=options,
            permission=permission,
            show_in_measurement_dlg=show_in_measurement_dlg)

class LPath(LQuantity):
    def __init__(
        self,
        quant_name: str,
        label: Optional[str] = None,
        def_value: Optional[str] = None,
        tooltip: Optional[str] = None,
        group: Optional[str] = None,
        section: Optional[str] = None,
        state_quant: Union[None, "LCombo", "LBoolean"] = None,
        states: Union[None, bool, Sequence[Union[str, float, Pair]]] = None,
        models: Optional[Sequence[Union[str, float, Pair]]] = None,
        options: Optional[Sequence[Union[str, float, Pair]]] = None,
        permission: Optional[str] = None,
        show_in_measurement_dlg: Optional[bool] = None) -> None:
        super().__init__(
            quant_name,
            datatype='PATH',
            label=label,
            def_value=def_value,
            tooltip=tooltip,
            group=group,
            section=section,
            state_quant=state_quant,
            states=states,
            models=models,
            options=options,
            permission=permission,
            show_in_measurement_dlg=show_in_measurement_dlg)

class LButton(LQuantity):
    def __init__(
        self,
        quant_name: str,
        label: Optional[str] = None,
        tooltip: Optional[str] = None,
        group: Optional[str] = None,
        section: Optional[str] = None,
        state_quant: Union[None, "LCombo", "LBoolean"] = None,
        states: Union[None, bool, Sequence[Union[str, float, Pair]]] = None,
        models: Optional[Sequence[Union[str, float, Pair]]] = None,
        options: Optional[Sequence[Union[str, float, Pair]]] = None,
        set_cmd: Optional[str] = None) -> None:
        super().__init__(
            quant_name,
            datatype='BUTTON',
            label=label,
            tooltip=tooltip,
            group=group,
            section=section,
            state_quant=state_quant,
            states=states,
            models=models,
            options=options,
            set_cmd=set_cmd)

class LDriverDefinition:
    def __init__(self, filename):
        self.file = open(filename, 'w')
        self.section = None
        self.group = None
    
    def add_general_settings(
        self,
        name,
        version=None,
        driver_path=None,
        interface=None,
        address=None,
        startup=None,
        signal_generator=None,
        signal_analyzer=None,
        controller=None,
        support_hardware_loop=None,
        support_arm=None,
        use_32bit_mode=None):
        self.file.write(str(LItem(
            'General settings',
            name=name,
            version=version,
            driver_path=driver_path,
            interface=interface,
            address=address,
            startup=startup,
            signal_generator=signal_generator,
            signal_analyzer=signal_analyzer,
            controller=controller,
            support_hardware_loop=support_hardware_loop,
            support_arm=support_arm,
            use_32bit_mode=use_32bit_mode)) + '\n')

    def add_models_and_options(
        self,
        models=None,
        check_model=None,
        model_cmd=None,
        options=None,
        check_options=None,
        option_cmd=None):
        self.models = _zip_with_none(models)
        self.options = _zip_with_none(options)
        s = str(LItem(
            'Model and options',
            check_model=check_model,
            model_cmd=model_cmd,
            check_options=check_options,
            option_cmd=option_cmd))
        if self.models is not None:
            for (i, (k, v)) in enumerate(self.models):
                s += f'model_str_{i+1}: {k}\n'
                if v is not None:
                    s += f'model_id_{i+1}: {v}\n'
        if self.options is not None:
            for (i, (k, v)) in enumerate(self.options):
                s += f'option_str_{i+1}: {k}\n'
                if v is not None:
                    s += f'option_id_{i+1}: {v}\n'
        self.file.write(s + '\n')
    
    def add_VISA_settings(
        self,
        use_visa=None,
        reset=None,
        query_instr_errors=None,
        error_bit_mask=None,
        error_cmd=None,
        init=None,
        final=None,
        str_true=None,
        str_false=None,
        str_value_out=None,
        str_value_strip_start=None,
        str_value_strip_end=None,
        always_read_after_write=None,
        timeout=None,
        term_char=None,
        send_end_on_write=None,
        suppress_end_on_read=None,
        baud_rate=None,
        data_bits=None,
        stop_bits=None,
        parity=None,
        gpib_board=None,
        gpib_go_to_local=None,
        tcpip_specify_port=None,
        tcpip_port=None):
        self.file.write(str(LItem(
            'VISA settings',
            use_visa=use_visa,
            reset=reset,
            query_instr_errors=query_instr_errors,
            error_bit_mask=error_bit_mask,
            error_cmd=error_cmd,
            init=init,
            final=final,
            str_true=str_true,
            str_false=str_false,
            str_value_out=str_value_out,
            str_value_strip_start=str_value_strip_start,
            str_value_strip_end=str_value_strip_end,
            always_read_after_write=always_read_after_write,
            timeout=timeout,
            term_char=term_char,
            send_end_on_write=send_end_on_write,
            suppress_end_on_read=suppress_end_on_read,
            baud_rate=baud_rate,
            data_bits=data_bits,
            stop_bits=stop_bits,
            parity=parity,
            gpib_board=gpib_board,
            gpib_go_to_local=gpib_go_to_local,
            tcpip_specify_port=tcpip_specify_port,
            tcpip_port=tcpip_port)) + '\n')
    
    def add_section(self, section):
        self.section = section

    def add_group(self, group):
        self.group = group
    
    def add_quantity(self, quant):
        self.file.write(str(quant))
        if (quant.getValue('section') is None) and (self.section is not None):
            self.file.write(f'section: {self.section}\n')
        if (quant.getValue('group') is None) and (self.group is not None):
            self.file.write(f'group: {self.group}\n')
        self.file.write('\n')

    def __del__(self):
        self.file.close()

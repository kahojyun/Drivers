import sys
from pathlib import Path

sys.path.append(str(Path('../Helper_Lib').resolve()))

from driver_config import (
    LDriverDefinition, LDouble
)

MAX_CHANNELS = 4

if __name__ == "__main__":
    dir_path = Path(__file__).parent
    f = LDriverDefinition(dir_path/'QuantumCTek_DC.ini')
    f.add_general_settings(
        name='QuantumCTek_DC',
        version='0.0.1',
        driver_path='QuantumCTek_DC',
        interface='TCPIP',
        support_arm=False,
        support_hardware_loop=False,
    )


    for i in range(MAX_CHANNELS):
        f.add_quantity(LDouble(
            f'Voltage #{i+1}',
            unit='V',
            def_value=0,
            low_lim=-7,
            high_lim=7,
            show_in_measurement_dlg=True,
        ))
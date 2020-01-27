from pathlib import Path
import datetime

def remove_line(str):
    """Remove empty lines and comments"""
    line = [l.rstrip() for l in str.split('\n') if l.strip() and l.strip()[0]!='#']
    return '\n'.join(line)

def write_configuration():
    dir_path = Path(__file__).parent
    with (dir_path/'marker_setting.yml').open('r') as f:
        marker_str = f.read()+'\n'
    def marker_setting(channel, marker):
        return marker_str.format(channel=channel, marker=marker)

    with (dir_path/'channel_setting.yml').open('r') as f:
        channel_str = f.read()+'\n'
    def channel_setting(channel):
        s = channel_str
        for marker in range(1,5):
            s += marker_setting(channel, marker)
        return s.format(channel=channel)

    with (dir_path/'trigger_setting.yml').open('r') as f:
        trigger_str = f.read()+'\n'
    def trigger_setting(source):
        return trigger_str.format(source=source)

    with (dir_path/'general_setting.yml').open('r') as f:
        general_str = f.read()+'\n'
    with (dir_path/'Tektronix_AWG5200.ini').open('w') as f:
        notification = (
            "#\n"
            "#\n"
            "#\n"
            "#\n"
            "# This file is generated with write_configuration.py\n"
            "# Please don't edit this file directly!\n"
            f"# Timestamp: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n"
            "#\n"
            "#\n"
            "#\n"
            "#\n"
            "###############################################################\n")
        s = general_str
        for source in ['A','B']:
            s += trigger_setting(source)
        for channel in range(1,9):
            s += channel_setting(channel)
        f.write(notification + remove_line(s))

if __name__ == "__main__":
    write_configuration()
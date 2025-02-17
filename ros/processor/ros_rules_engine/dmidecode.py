"""
DmiDecode - Combiner
====================
Combiner for getting the required values from DMIDecode

"""
from insights import SkipComponent
from insights.core.plugins import combiner
from insights.parsers.dmidecode import DMIDecode


@combiner(DMIDecode)
class DmiDecode(object):
    """
    Get required values from DMIDecode

    Attributes:
        RAM_B (int): The total physical RAM in unit `Byte`.
        RAM_KB (int): The total physical RAM in unit `KB`.
        RAM_MB (int): The total physical RAM in unit `MB`.
        RAM_GB (int or float): The total physical RAM in unit `GB`.


    Raises:
        SkipComponent: When no such values.
    """
    def __init__(self, dmidecode):
        self.RAM_MB = self.RAM_GB = self.RAM_KB = self.RAM_B = 0
        for md in dmidecode.data.get('memory_device', []):
            size = md.get('size')
            if size:
                num, _, unit = size.partition(' ')
                if unit == 'GB':
                    self.RAM_GB += int(num)
                    self.RAM_MB += int(num) * 1024
                    self.RAM_KB += int(num) * 1024 * 1024
                    self.RAM_B += int(num) * 1024 * 1024 * 1024
                elif unit == 'MB':
                    self.RAM_GB += round(int(num) / 1024, 2)
                    self.RAM_MB += int(num)
                    self.RAM_KB += int(num) * 1024
                    self.RAM_B += int(num) * 1024 * 1024
        if self.RAM_MB <= 0:
            raise SkipComponent


class PmLogSummaryBase(dict):
    """
    Base Parser to parse the output of the ``pmlogsummary`` command

    Sample output of the command is::

        mem.util.used  3133919.812 Kbyte
        mem.physmem  3997600.000 Kbyte
        kernel.all.cpu.user  0.003 none
        kernel.all.cpu.sys  0.004 none
        kernel.all.cpu.nice  0.000 none
        kernel.all.cpu.steal  0.000 none
        kernel.all.cpu.idle  3.986 none
        kernel.all.pressure.io.full.avg ["10 second"] 0.001 none
        kernel.all.pressure.cpu.some.avg ["1 minute"] 14.942 none
        kernel.all.pressure.memory.full.avg ["5 minute"] 0.002 none
        disk.all.total  0.252 count / sec
        disk.dev.total ["vda"] 0.016 count / sec
        disk.dev.total ["vdb"] 0.445 count / sec
        disk.dev.total ["vdc"] 2.339 count / sec

    Output is parsed and stored as a dictionary.  Each value is
    stored as a dict in the form ``{'val': number or string, 'units': string}``.
    Keys are a hierarchy of the input key value split on the "." character.

    For instance::

        1. Input line "mem.util.used  3133919.812 Kbyte" is parsed as:
            {
                'mem': {
                    'util': {
                        'used': {
                            'val': 3133919.812,
                            'units': 'Kbyte'
                        }
                    }
                }
            }
        2. Input line "disk.dev.total ["vdc"] 2.339 count / sec" is parsed as:
            {
                'disk': {
                    'dev': {
                        'total': {
                            'vdc': {
                                'val': 2.339
                                'units': 'count / sec'
                            }
                        }
                    }
                }
            }

    Example:
        >>> type(pmlog_summary)
        <class 'insights.parsers.pmlog_summary.PmLogSummary'>
        >>> 'mem' in pmlog_summary
        True
        >>> pmlog_summary['disk']['all']['total'] == {'val': 0.252, 'units': 'count / sec'}
        True
        >>> pmlog_summary['disk']['dev']['total']['vdc'] == {'val': 2.339, 'units': 'count / sec'}
        True
        >>> pmlog_summary['kernel']['all']['pressure']['memory']['full']['avg']['5 minute'] == {'val': 0.002, 'units': 'none'}
        True
    """

    def parse_content(self, content):
        data = parse(content)

        if len(data) == 0:
            raise SkipComponent()

        self.update(data)

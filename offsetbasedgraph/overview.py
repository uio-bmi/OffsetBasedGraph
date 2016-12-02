from collections import defaultdict


def takes(*targs):
    def dec(func):
        def new_func(*args, **kwargs):
            for arg in zip(args, targs):
                assert isinstance(arg, targs)
            return func(*args, **kwargs)
        return new_func
    return dec


class Position(object):
    """
    Represents a position  in the graph
    """
    region_path_id = None
    offset = None


class Interval(object):
    start_position = None
    end_position = None
    region_paths = None

    def length(self):
        pass


class Translation(object):
    _a_to_b = {}
    _b_to_a = {}

    def __init__(self, translate_dict, reverse_dict):
        pass

    @takes(Interval)
    def translate_interval(self, interval, inverse=False):
        '''
        Return the interval representation of @interval in
        coordinate system b
        '''
        for region_path in interval.region_paths:
            pass

    @takes(Position)
    def translate_position(self, position, inverse=False):
        pass

    def __add__(self, other):
        """Combine to translations"""


class Graph(object):
    region_paths = {}
    edge_list = defaultdict(list)
    reverse_edge_list = defaultdict(list)

    # Graph alterations
    def __init__(self, region_paths, edge_list):
        self.region_paths = region_paths
        self.edge_list = edge_list

    @takes(Interval, Interval)
    def merge_intervals(self, interval_a, interval_b):
        '''
        Merge the two intervals in the graph and return
        a translation object
        '''
        assert interval_a.length() == interval_b.length()

    @takes(Interval, Interval)
    def connect_intervals(self, interval_a, interval_b):
        pass

from itertools import chain
from .interval import Interval


class MultiPathInterval(object):

    def get_single_path_intervals(self):
        raise NotImplementedError()


class SingleMultiPathInterval(MultiPathInterval):
    def __init__(self, interval):
        self.interval = interval
        rps = interval.region_paths
        if len(rps) > 1 and rps[-1] == rps[0]:
            self.interval.region_paths = rps[:-1]

    def get_single_path_intervals(self):
        return [self.interval]


class SimpleMultipathInterval(object):

    def __init__(self, intervals):
        self._intervals = intervals

    def get_single_path_intervals(self):
        return self._intervals


class GeneralMultiPathInterval(MultiPathInterval):
    """
    Holds a general multipath interval by representing all possible start
    positions, end positions and all possible region paths within the interval.

    A method can return (in some cases) a trivial set of single path
    intervals contained by this multi path interval
    """

    def __init__(self, start_positions, end_positions, region_paths, graph):
        self.start_positions = start_positions
        self.end_positions = end_positions
        self.region_paths = region_paths
        self.end_region_paths = {pos.region_path_id: pos
                                 for pos in self.end_positions}
        self.graph = graph

    def is_single_path(self):
        pass

    def _find_end_region_path(self, start_position, region_paths):
        """Generate all valid intervals starting at start_position
        going through region_paths

        :param start_position: start position of the intervals
        :param region_paths: list of region paths
        :returns: generator of valid intervals
        :rtype: generator

        """
        cur_region_path = region_paths[-1]
        if cur_region_path in self.end_region_paths:
            yield Interval(start_position,
                           self.end_region_paths[cur_region_path],
                           region_paths, self.graph)

        next_level = (
            rp
            for rp in self.graph.adj_list[cur_region_path]
            if rp in self.region_paths)

        for rp in next_level:
            yield from self._find_end_region_path(
                start_position, region_paths + [rp])

    def _get_single_path_intervals(self, start_position):
        """Generate all valid intervals starting from start position

        :param start_position: Position
        :returns: Interval generator
        :rtype: generator

        """
        yield from self._find_end_region_path(start_position,
                                              [start_position.region_path_id])

    def get_single_path_intervals(self):
        """
        Generate all single path intervals.
        :return: generator
        """
        intervals = []
        for start_position in self.start_positions:
            # yield from self._get_single_path_intervals(start_position)
            intervals.extend(self._get_single_path_intervals(start_position))
        return intervals

    def __str__(self):
        return "Start pos: %s\n end pos: %s\n region paths: %s\n" % \
               (str(self.start_positions), str(self.end_positions), str(self.region_paths))

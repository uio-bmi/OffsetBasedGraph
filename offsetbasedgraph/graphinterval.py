
class GraphInterval(object):

    def __init__(self, block_list, start, end):
        self.block_list = block_list
        self.start = start
        self.end = end

    def __str__(self):
        return "%s: %s :%s" % (
            self.start, " ".join([block for block in self.block_list]), self.end)

    @classmethod
    def linear_coordinate_to_graph(cls, graph, chr_id, coordinate):
        """ Maps the linear coordinate to a coordinate in the block graph.
        graph_block_index should be sent as a parameter, and can be obtained
        by calling create_block_index()
        """
        # Our coordinate can be in any of these blocks
        potential_blocks = graph.block_index[chr_id]

        for potential_block in potential_blocks:
            # Get start and end position of this block in linear genome,
            # check whether this is the correct block
            # assume always only one linear refernce, i.e. only one species
            linear_references = potential_block.linear_references.values()
            for lr in linear_references:
                start = lr.start
                end = lr.end
                if start <= coordinate and end >= coordinate:
                    return (potential_block.id, coordinate - start)


        raise Exception("No block found for chr_id %s, coordinate %d" % (chr_id, coordinate))

    @classmethod
    def linear_segment_to_graph(cls, graph,  chr_id, start, end):
        """
        Takes a linear segment on hg38 and returns a ChainSegment object
        """
        block_list = []
        start_pos = 0
        end_pos = 0

        start_block, start_pos = cls.linear_coordinate_to_graph(
            graph, chr_id, start)
        end_block, end_pos = cls.linear_coordinate_to_graph(
            graph, chr_id, end)
        print graph.blocks[end_block]

        block_list.append(start_block)
        current_block = start_block
        print graph.blocks.keys()
        while True:
            print current_block
            if current_block == end_block:
                break
            prev_block = current_block
            edges = graph.block_edges[current_block]
            for edge in edges:
                if chr_id in graph.blocks[edge].linear_references:
                    current_block = edge

            if current_block == prev_block:
                raise Exception("Error while traversing block. Did not find " +\
                                "next block for block %s, %s" % (current_block,edges))
            block_list.append(current_block)

        return cls(block_list, start_pos, end_pos)

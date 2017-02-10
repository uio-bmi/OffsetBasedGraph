from __future__ import absolute_import
from __future__ import division
#import matplotlib.pyplot as plt
import numpy as np
import six
#from matplotlib import colors
from gendatafetcher.ucscdb import DbWrapper

DEBUG = False

class VisualizeHtml(object):
    """
    Attempt to make a simple html visualization
    """

    def __init__(self, graph, minOffset, maxOffset, id, levels, description='', width=800, genes=[]):


        self.padding = 50  # Gap between blocks
        self.gap_pixels = 0  # Extra gap pixels that are added
        self.graph = graph
        self.color_counter = 4
        self.colors = ["#0000aa", "#5F96C5", "#C58E8E", "#cccccc", "purple", "orange", "indigo"]
        self.gene_colors = ["darkorange", "#D9EDF7", "#aaaaaa", "pink", "black", "black", "black", "black", "black", "black", "black", "black", "black", "black", "black", "black", "black", "black", "black", "black", "black", "black", "black", "black"]
        self.gene_counter = 0
        self.genes_plotted_heights = {} # Dict of heights for genes
        self.offset_positions = {}  # Dict of offset pos for each alt loci/chrom
        self.offset_counter = 0
        self.lowest_offset = 0
        self.vis_id = id
        self.genes = genes #list(reversed(intervals))
        self.levels = levels

        self.width = width
        self.maxOffset = maxOffset
        self.minOffset = minOffset
        self.width_ratio = float(self.width) / (self.maxOffset - self.minOffset)

        self.width_used = self.width

        self.gene_height = 10
        self.block_height = 35
        self.exon_height = 6

        self.exon_cnt = 0

        self.svg_lines = ""
        self.html_arrows = ""
        self.html = ""
        self.html += """
        <div class='row'>
            <div class='col-md-8'>
                <h4>%s</h4>
            </div>
            <div class='col-md-4'>
				<div class='options'>
					<p><label><input type='checkbox' onclick="$('.exon').toggle();"> Click to show exons <span id='exon_cnt'></span></label></p>
				</div>
			</div>
        """ % description

        self.html += """
            <div class='col-md-12'>
                <div class='visualization'>
                    <div style='position: relative;
                                float: right;
                                width: 150px;
                                background-color: white;
                                height: 20px; margin-top: 5px;'>
                        <p style='font-size: 0.8em;'>
                            <span style='background-color: %s; width: 30px; height: 12px; display: inline-block'></span> <font color='black'>Main path (GRCh38)</font><br>
                            <span style='background-color: %s; width: 30px; height: 12px; display: inline-block'></span> <font color='black'>Flanking regions </font><br>
                            <span style='background-color: %s; width: 30px; height: 12px; display: inline-block'></span> <font color='black'>Alternative locus</font>
                        </p>
                    </div>
        """ % (self.colors[3], self.colors[2], self.colors[1])


        # Gene labels
        self.html += """
        <div style='position: relative;
                    float: left;
                    width: 400px;
                    background-color: white;
                    height: 20px; margin-top: 5px; margin-left: 10px'>
            <p style='font-size: 0.8em;'>
        """
        i = 0

        for gene in genes:
            self.html += """
                <span style='background-color: %s; width: 30px; height: 12px; display: inline-block'></span>
                 <font color='black'>%s</font><br>
                """ % (self.gene_colors[i%len(self.gene_colors)], "Gene: " + gene.name + " (" + gene.name + ")")
            i += 1

        self.html += """
            </p>
        </div>
        """


        self.visualize_v2()
        self.visualize_genes()
        self.html += self.html_arrows

        # Write js to set number of exons
        if id == 0:
            self.html += """
            <script>
                $(document).ready(function(){
                    $('#exon_cnt').html('(%d)');
                });
            </script>""" % self.exon_cnt

        self.html += "</div></div></div>"

    def _plot_interval(self, interval, name, is_exon = False):

        if is_exon:
            print("<p><b>Plotting exon: %s</b></p>" % interval)

        for block in interval.region_paths:
            if not block in self.block_positions:
                if DEBUG: print("Warning. Block %s not found in offset_positions when visualizing interval" % (block))
                continue

            #plot_info = self.offset_positions[block]
            pos = self.block_positions[block]
            start = pos[0]
            #print("<p>Start pos is %d</p>" % start)
            end = pos[0] + pos[2]
            if block == interval.region_paths[0]:
                start += interval.start_position.offset * self.width_ratio
                #print("<p>Setting exon start to %d after adding %d</p>" % (start, interval.start_position.offset * self.width_ratio))
            if block == interval.end_position.region_path_id:
                end = pos[0] + interval.end_position.offset * self.width_ratio
                #print("<p>Fixing exon end: %d (offset: %d)</p>" % (end, interval.end_position.offset))
            if is_exon:
                #self._plot_exon(start, end, pos[1], interval, name)
                self._plot_interval_in_block(start, end, pos[1], interval, name, True)
            else:
                self._plot_interval_in_block(start, end, pos[1], interval, name)


    def visualize_genes(self):
        """
        Visualizes genes
        :param intervals: A list of Genes (of type offsetbasedgraph.graphutils.Gene)
        """
        for gene in self.genes:
            #print("<p>Visualizing gene</p>")
            #print("gene")

            interval = gene.transcription_region
            self._plot_interval(interval, gene.name)
            for exon in gene.exons:
                self._plot_interval(exon, gene.name, True)


            self.color_counter += 1
            self.gene_counter += 1

    def visualize_intervals(self):
        """
        Visualizes intervals
        :param intervals: A list of intervals (of type Segment)
        """
        for interval in self.intervals:

            for block in interval.region_paths:

                if not block in self.offset_positions:
                    if DEBUG: print("Warning. Block %s not found in offset_positions when visualizing interval" % (block))
                    continue

                plot_info = self.offset_positions[block]
                start = plot_info[0]
                end = plot_info[0] + plot_info[2]
                if block == interval.start_block:
                    start += interval.start_pos * self.width_ratio
                if block == interval.end_block:
                    end = plot_info[0] + interval.end_pos * self.width_ratio

                if interval.is_exon:
                    self._plot_exon(start, end, plot_info[1], interval)
                else:
                    self._plot_interval_in_block(start, end, plot_info[1], interval)

            self.color_counter += 1
            self.gene_counter += 1

    def _interval_js_css(self):
        self.html += """
        <style type='text/css'>
            .interval_%d:hover .interval_%d{
                border: 1px solid white;
            }
        </style>
        """ % (self.gene_counter, self.gene_counter)

    def _plot_exon(self, start, end, level, interval_obj, gene_name):
        image = "exon_start"
        top = level + 1 + self.gene_height * self.genes_plotted_heights[gene_name]

        self.html += "<div class='exon exon_%d'" % self.gene_counter
        self.html += " style='z-index: 12; position: absolute;"
        self.html += "left: %.2fpx;" % (start)
        self.html += "width: %.2fpx;" % (max(2, end - start))
        self.html += "top: %.2fpx;" % (top + (self.gene_height - self.exon_height) /  2.0)
        self.html += "height: %dpx;" % (self.exon_height)
        self.html += "background-color: black;"
        self.html += "' "
        self.html += "data-interval-id='%d'" % self.gene_counter
        self.html += "data-notation='%s'" % str(interval_obj)
        self.html += "data-gene-name='%s'" % gene_name
        self.html += "data-gene-name2='%s'" % gene_name
        self.html += "data-graph-id='%d'>" % self.vis_id
        #self.html += "<img src='%s.png'>" % image
        self.html += "</div>"

        if start < 900:
            self.exon_cnt += 1


    def _plot_interval_in_block(self, start, end, level, interval_obj, name = "", is_exon = False):
        #level += 0.3 + 0.3 * (self.color_counter - 4)
        #print "=
        if end - start == 0:
            return

        top = level + 1 + self.gene_height * self.gene_counter

        if is_exon:
            top = (top + (self.gene_height - self.exon_height) /  2.0)

        if not is_exon:
            color = self.gene_colors[self.gene_counter]
        else:
            color = "black"

        height = self.gene_height
        if is_exon:
            height = self.exon_height

        self.html += "<div class='interval interval_%d'" % self.gene_counter

        self.html += " style='z-index: 10; position: absolute;"
        self.html += "left: %.2fpx;" % start
        self.html += "width: %.2fpx;" % (end - start)
        self.html += "top: %.2fpx;" % (top)
        self.html += "height: %dpx;" % (height)
        self.html += "background-color: %s;" % color
        self.html += "' "
        self.html += "data-interval-id='%d'" % self.gene_counter
        self.html += "data-notation='%s'" % str(interval_obj)
        self.html += "data-gene-name='%s'" % name
        self.html += "data-gene-name2='%s'" % name
        self.html += "data-graph-id='%d'></div>" % self.vis_id

        self.genes_plotted_heights[name] = self.gene_counter

        #print "%d, %d, %d" % (start, end, level)



        #plt.plot([start, end], [level, level],
        #            self.colors[self.color_counter],
        #            linestyle = '-',
        #            linewidth=2, solid_capstyle="butt")

    def _coordinate(self, rp):
        """
        Returns the hierarhcial and sequential coordinates of a region path
        """


        return (rp, 0, rp, 0, rp.length())

        # Sequential coordinates are always id and the first offset is 0
        seqID = rp.id
        seqOf = 0
        # Hierarchical coordinates is same as sequential if this is alternative
        # block. Else, it is the same as on hg38
        if len(rp.linear_references) == 1 and \
                not "alt" in list(rp.linear_references.values())[0].chromosome:
            hierID = list(rp.linear_references.values())[0].chromosome
            hierOf = list(rp.linear_references.values())[0].start
        elif len(rp.linear_references) == 2 and \
            "alt" in list(rp.linear_references.values())[0].chromosome:
            hierID = list(rp.linear_references.values())[1].chromosome
            hierOf = list(rp.linear_references.values())[1].start
        elif len(rp.linear_references) == 2 and \
            "alt" in list(rp.linear_references.values())[1].chromosome:
            hierID = list(rp.linear_references.values())[0].chromosome
            hierOf = list(rp.linear_references.values())[0].start
        else:
            hierID = seqID
            hierOf = seqOf

        # Also get size of region path
        size = max(l.end - l.start for l in list(rp.linear_references.values()))

        return (self._pretty_alt_loci_name(seqID), str(seqOf),\
                self._pretty_alt_loci_name(hierID), str(hierOf), str(size))


    def _plot(self, xstart, xend, level, color, rp):

        y = self.block_height * 2 * ( level + 1)
        x = self.gap_pixels + (xstart - self.minOffset) * self.width_ratio
        width = (xend - xstart) * self.width_ratio

        self.html += "<div class='block' style='position: absolute;"
        self.html += "left: %.2fpx;" % x
        self.html += "width: %.2fpx;" % width
        self.html += "top: %.2fpx;" % (y)
        self.html += "height: %dpx;" % (self.block_height)
        self.html += "background-color: %s;" % color
        self.html += "' "
        self.html += " data-rpid='%s'" % ("test") #(rp.id)
        self.html += " data-rpname='%s'" % "tmp" #(self._pretty_alt_loci_name(rp.id))
        self.html += " data-graph-id='%d'" % (self.vis_id)
        self.html += " data-coordinate='%s'" % "," #','.join(self._coordinate(rp))
        self.html += ">"
        self.html += "<font color='white'>%s</font></div>" % ""

        return x + width, y, width, x

    def _plot_region_path(self, rp_id, level=0):
        """
        :return:
        """
        rp = self.graph.blocks[rp_id]
        start = self.offset_counter
        #lr = list(rp.linear_references.values())[0]
        #length = self._scale(lr.end - lr.start)
        length = rp.length()
        if DEBUG: print("<p>PLotting " + str(rp_id) + "  on level %.2f, %.2f to %.2f</p>" % (level, start, start + length))
        xend, y, width, xstart = self._plot(start, start + length, level , self.colors[level + 1], rp)

        self.offset_positions[rp_id] = [xstart, y, width]

        return start + length, xend , y, width

    def _plot_level(self, block):
        # Finds the level. Rule: if block contains more than one linea reference
        # it is shared, else, find out whether it is alt or consensus

        return self.levels[block]

        """
        if len(list(block.linear_references.values())) > 1:
            #if DEBUG: print "MOre than one linear reference ::::::::"
            return 1
        else:
            if "alt" in list(block.linear_references.values())[0].chromosome:
                return 0
            else:
                return 2
        """

    def _pretty_alt_loci_name(self, id):
        return self.graph.pretty_alt_loci_name(id)



    def _scale(self, n):
        return n
        return np.log(n+1)

    def _plot_arrow(self, xstart, ystart, xend, yend):
        """ Plots and arrow
        """
        #print "Plot from %d,%d to %d,%d" % (xstart, ystart, xend, yend)
        self.html_arrows += "<div style='position: absolute;"

        if yend < ystart:
            arrow = "short"
            if ystart - yend >= self.block_height * 4:
                arrow = "long"
            self.html_arrows += "left: %dpx;" % xstart
            self.html_arrows += "top: %dpx;" % (ystart - (ystart - yend) + self.block_height/2)
            self.html_arrows += "'>"
            self.html_arrows += "<img src='arrow_up_%s.png' style='" % arrow
            self.html_arrows += "height: %dpx;" % (ystart - yend)
            self.html_arrows += "width: %dpx;" % (xend - xstart)
            self.html_arrows += "'>"
        elif yend == ystart:
            self.html_arrows += "left: %dpx;" % xstart
            self.html_arrows += "top: %dpx;" % (ystart + self.block_height/2)
            self.html_arrows += "'>"
            self.html_arrows += "<img src='arrow.png' style='"
            self.html_arrows += "height: %dpx;" % (self.block_height/4)
            self.html_arrows += "width: %dpx;" % (xend - xstart)
            self.html_arrows += "'>"
        else:
            arrow = "short"
            if ystart - yend >=  + self.block_height * 4:
                arrow = "long"
            self.html_arrows += "left: %dpx;" % xstart
            self.html_arrows += "top: %dpx;" % (ystart + self.block_height/2)
            self.html_arrows += "'>"
            self.html_arrows += "<img src='arrow_down_%s.png' style='" % arrow
            self.html_arrows += "height: %dpx;" % (yend-ystart)
            self.html_arrows += "width: %dpx;" % (xend - xstart)
            self.html_arrows += "'>"

        self.html_arrows += "</div>"

    def _distance_to_start(self, b):
        # Find distance back to start
        g = self.graph

        if b == g.start_block:
            return 0
        print("Start block: %s" % g.start_block)
        print("Finding back for %s" % b)

        back_block = g.reverse_adj_list[b][0]
        #print("Finding back for %s" % b)
        distance = 0
        while True:
            block_size = self._scale(g.blocks[back_block].length())
            distance += self.padding / self.width_ratio + block_size
            if back_block == g.start_block:
                break
            print(back_block)
            print(g.reverse_adj_list[back_block])
            back_block = g.reverse_adj_list[back_block][0]
        return distance

    def visualize_v2(self):
        # Try to visualize more complex graphs
        block = self.graph.start_block #self.graph.blocks[self.graph.start_block]
        #self.offset_counter = self._scale(list(block.linear_references.values())[0].start)
        self.offset_counter = self._scale(0)


        # Find x position of all blocks
        self.block_positions = {}
        for b in self.graph.blocks:
            start = self._distance_to_start(b)
            end = start + self._scale(self.graph.blocks[b].length())

            # Plot rp
            xend, y, width, xstart = self._plot(start, end, self.levels[b], self.colors[self.levels[b] + 1], b)

            self.block_positions[b] = (xstart, y, width)
            print("<p>PLotted %s at %d,%d with width %d, ending at %d</p>" % (b, xstart, y, width, xend))

        print(self.block_positions)

        # Plot arrows using all edges
        g = self.graph
        for b in g.blocks:
            for edge in self.graph.adj_list[b]:
                length = g.blocks[b].length()
                xstart = self.block_positions[b][0] + self._scale(length) * self.width_ratio
                ystart = self.block_positions[b][1]
                xend = self.block_positions[edge][0]
                yend = self.block_positions[edge][1]
                self._plot_arrow(xstart, ystart, xend, yend)
                print("Plotted arrow")


        return
        self.offset_counter, x_coord, y_coord, width = self._plot_region_path(self.graph.start_block,
                                                    self._plot_level(self.graph.start_block))

        prevEnds = [(x_coord, y_coord, width)]

        while True:
            self.gap_pixels += 20
            if DEBUG: print("<p>Iteration: " + str(block.id) + "</p>")
            # Plot the next blocks (will never be more than two blocks)
            offsets = []

            ends = []

            for next in self.graph.adj_list[block]:
                level = self._plot_level(next)
                #next_block = self.graph.blocks[next]
                o, x, y, width = self._plot_region_path(next, level)
                block = next
                offsets.append(o)
                ends.append((x, y, width))
                self.width_used = max(self.width_used, y + width)

            # Hack
            # if width < 1:
            #    continue

            # PLot arrows from previous end positions (there are 1 or 2),
            # to these end positions (there are 1 or 2)
            for end1 in prevEnds:
                for end2 in ends:
                    self._plot_arrow(end1[0], end1[1], \
                        end2[0]-end2[2], end2[1])

            prevEnds = ends

            if block not in self.graph.adj_list:
                return
            if len(list(self.graph.adj_list[block])) == 0:
                return




            self.offset_counter = max(offsets)

    def visualize(self):
        block = self.graph.start_block #self.graph.blocks[self.graph.start_block]
        #self.offset_counter = self._scale(list(block.linear_references.values())[0].start)
        self.offset_counter = self._scale(0)
        self.offset_counter, x_coord, y_coord, width = self._plot_region_path(self.graph.start_block,
                                                    self._plot_level(self.graph.start_block))

        prevEnds = [(x_coord, y_coord, width)]

        while True:
            self.gap_pixels += 20
            if DEBUG: print("<p>Iteration: " + str(block.id) + "</p>")
            # Plot the next blocks (will never be more than two blocks)
            offsets = []

            ends = []

            for next in self.graph.adj_list[block]:
                level = self._plot_level(next)
                #next_block = self.graph.blocks[next]
                o, x, y, width = self._plot_region_path(next, level)
                block = next
                offsets.append(o)
                ends.append((x, y, width))
                self.width_used = max(self.width_used, y + width)

            # Hack
            if width < 1:
                continue

            # PLot arrows from previous end positions (there are 1 or 2),
            # to these end positions (there are 1 or 2)
            for end1 in prevEnds:
                for end2 in ends:
                    self._plot_arrow(end1[0], end1[1], \
                        end2[0]-end2[2], end2[1])

            prevEnds = ends

            if block not in self.graph.adj_list:
                return
            if len(list(self.graph.adj_list[block])) == 0:
                return




            self.offset_counter = max(offsets)


    def __str__(self):
        return self.html

    def get_wrapped_html(self):
        # Html wrapped with js includes etc
        html = """
        <html>
        <head>
            <script   src="https://code.jquery.com/jquery-2.2.4.min.js"   integrity="sha256-BbhdlvQf/xTY9gja0Dq3HiwQF8LaCRTXxZKRutelT44="   crossorigin="anonymous"></script>
            <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css" integrity="sha384-1q8mTJOASx8j1Au+a5WDVnPi2lkFfwwEAa8hDDdjZlpLegxhjVME1fgjWPGmkzs7" crossorigin="anonymous">

            <!--<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap-theme.min.css" integrity="sha384-fLW2N01lMqjakBkx3l/M9EahuwpSfeNvV63J5ezn3uZzapT0u7EYsXMjQV+0En5r" crossorigin="anonymous">-->

            <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/js/bootstrap.min.js" integrity="sha384-0mSbJDEHialfmuBBQP6A4Qrprq5OVfW37PRR3j5ELqxss1yVqOtnepnHVP9aJ7xS" crossorigin="anonymous"></script>
        </head>
        <body>
            <div class="container" style='min-height: 800px;'>
        """
        html += self.__str__()
        html += "<br><br><br><br><br><br><br></div></body></html>"

        return html

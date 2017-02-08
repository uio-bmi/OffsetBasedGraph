"""
Creates a graph from GRCh38, represents genes on this graph and outputs some information about the genes

Usage example:
$ python3 gene_experiment.py grch38.chrom.sizes grch38_alt_loci.txt genes_chr1_GL383518v1_alt.txt

With only two alt loci:
python3 gene_experiment.py grch38.chrom.sizes-small grch38_alt_loci_small.txt genes_chr1_GL383518v1_alt.txt

"""

from collections import defaultdict
import sys
import argparse
import csv
from offsetbasedgraph import Graph, Block, Translation, Interval, Position
from offsetbasedgraph.graphutils import MultiPathGene
from offsetbasedgraph.graphutils import merge_alt_using_cigar, grch38_graph_to_numeric

from offsetbasedgraph.graphutils import Gene, convert_to_numeric_graph, connect_without_flanks, \
    convert_to_text_graph, merge_flanks, connect_without_flanks, parse_genes_file, \
    get_genes_as_intervals, get_gene_objects_as_intervals, find_exon_duplicates, \
    create_initial_grch38_graph, blast_test, convert_cigar_graph_to_text


def create_graph(args):
    graph = create_initial_grch38_graph(args.chrom_sizes_file_name)
    n_starts = len([b for b in graph.blocks if not graph.reverse_adj_list[b]])
    numeric_graph, name_translation = convert_to_numeric_graph(graph)
    n_starts2 = len([b for b in numeric_graph.blocks if not numeric_graph.reverse_adj_list[b]])
    assert n_starts == n_starts2
    new_numeric_graph, numeric_translation = connect_without_flanks(
        numeric_graph, args.alt_locations_file_name, name_translation)
    n_starts3 = len([b for b in new_numeric_graph.blocks if not new_numeric_graph.reverse_adj_list[b]])
    print("################", n_starts2-n_starts3)
    name_graph, new_name_translation = convert_to_text_graph(
        new_numeric_graph, name_translation, numeric_translation)
    n_starts4 = len([b for b in name_graph.blocks if not name_graph.reverse_adj_list[b]])
    for k, v in name_graph.adj_list.items():
        print(k, v)
    assert n_starts3 == n_starts4
    final_translation = name_translation + numeric_translation + new_name_translation
    final_translation.graph2 = name_graph
    n_starts5 = len([b for b in final_translation.graph2.blocks if not final_translation.graph2.reverse_adj_list[b]])

    assert n_starts5 == n_starts4
    final_translation.to_file(args.out_file_name)
    print("Graph and translation object stored in %s" % (args.out_file_name))


def check_duplicate_genes(args):
    genes_file_name = args.genes_file_name
    final_trans = Translation.from_file(args.translation_file_name)
    genes = get_gene_objects_as_intervals(genes_file_name, final_trans.graph1)
    find_exon_duplicates(genes, final_trans)
    # print(genes_file_name)


def merge_alignment(args):
    trans = Translation.from_file(args.translation_file_name)
    graph = trans.graph1
    graph, trans = grch38_graph_to_numeric(graph)
    merge_alt_using_cigar(graph, trans, args.alt_locus_id)


def merge_all_alignments(args):
    from offsetbasedgraph.graphutils import merge_alt_using_cigar, grch38_graph_to_numeric
    # Text ids (chrom names and alt names)
    text_graph = create_initial_grch38_graph(args.chrom_sizes_file_name)
    graph, name_trans = grch38_graph_to_numeric(text_graph)

    # Go through all alts in this graph
    new_graph = graph.copy()
    i = 0
    #for b in text_graph.blocks:
    for b in ['chr8_KI270818v1_alt']: #['chr8_KI270812v1_alt']: #text_graph.blocks: # chr6_GL000251v2_alt

        if "alt" in b:
            print("Merging %s" % b)
            numeric_trans, new_graph = merge_alt_using_cigar(
                new_graph, name_trans, b)
            i += 1
            if i >= 1:
                break

    final_graph, trans2 = convert_cigar_graph_to_text(
        new_graph,
        name_trans,
        numeric_trans)


    trans_a = name_trans + numeric_trans
    full_trans = trans_a + trans2

    # full_trans = name_trans + numeric_trans + trans2
    full_trans.set_graph2(final_graph)
    print("To file")
    full_trans.to_file(args.out_file_name)


def visualize_genes(args):
    trans = Translation.from_file(args.translation_file_name)
    graph = trans.graph2

    # Find blocks that genes cover, create subgraph using them
    from offsetbasedgraph.graphutils import GeneList
    genes = GeneList.from_file(args.genes_file_name).gene_list

    trans_regions = [g.transcription_region for g in genes]
    subgraph, trans = graph.create_subgraph_from_intervals(trans_regions, 20)

    # Translate genes using trans
    for g in genes:
        g.transcription_region = trans.translate(g.transcription_region)
        for exon in g.exons:
            exon = trans.translate(exon)

    levels = Graph.level_dict(subgraph.blocks)

    # Find start block by choosing a block having no edges in
    start = None
    for b in subgraph.blocks:
        if len(subgraph.reverse_adj_list[b]) == 0:
            start = b
            break

    print("== Subgraph ==")
    print(subgraph)

    assert start is not None

    from offsetbasedgraph import VisualizeHtml
    subgraph.start_block = start
    max_offset = sum([subgraph.blocks[b].length() for b in subgraph.blocks])
    v = VisualizeHtml(subgraph, 0, max_offset, 0, levels, "", 800, genes)
    print(v.get_wrapped_html())


def translate_genes_to_aligned_graph(args):
    trans = Translation.from_file(args.merged_graph_file_name)

    # Creat critical path multipath intervals of genes by translating
    # to complex graph.
    # Represent by txStart, txEnd as start,end and exons as critical intervals
    from offsetbasedgraph.graphutils import GeneList, translate_single_gene_to_aligned_graph
    genes = GeneList(get_gene_objects_as_intervals(args.genes, trans.graph1))
    gene_name = args.gene_name
    mpgenes = []
    mpgene_objects = []
    spgenes = []  # Also store single path for debugging
    n = 1
    for gene in genes.gene_list:
        n += 1
        if gene.name != gene_name:
            continue

        print("Found gene %s" % gene.name)
        print(gene)

        mpgene = translate_single_gene_to_aligned_graph(gene, trans)
        mpgene_objects.append(mpgene)
        #mpgenes.append(mpinterval)
        #mpgene_objects = MultiPathGene(gene.name, mpinterval)

        #spgenes.append(Gene(gene.name,
        #                    trans.translate(gene.transcription_region),
        #                    critical_intervals
        #                    )
        #               )


    import pickle

    mpgenes_list = GeneList(mpgene_objects)
    mpgenes_list.to_file(args.out_file_name)
    """
    with open("%s" % args.out_file_name, "wb") as f:
        pickle.dump(mpgenes, f)
    """

    for gene in spgenes:
        print("--------------")
        for exon in gene.exons:
            print(exon)

    gene_list = GeneList(spgenes)
    gene_list.to_file("%s_gene_list" % args.out_file_name)

    print(spgenes[0])
    print(spgenes[1])

    print("Genes written")


def _analyse_multipath_genes_on_graph(genes_list, genes_against, graph):
    # Takes a list of mp genes and a graph
    # Returns number of equal exons and equal genes
    equal = 0
    equal_exons = 0
    n = 1
    for g in genes_list:
        if n % 1000 == 0:
            print("Checked %d genes" % n)
        n += 1

        for g2 in genes_against:
            if g is g2:
                continue

            if g == g2:
                equal += 1

            if g.faster_equal_critical_intervals(g2):
                equal_exons += 1

    return equal, equal_exons

def analyse_multipath_genes2(args):
    import pickle

    from offsetbasedgraph.graphutils import GeneList, create_gene_dicts, translate_single_gene_to_aligned_graph
    print("Reading in genes")
    genes = GeneList(get_gene_objects_as_intervals(args.genes_file_name)).gene_list

    alt_loci_genes, gene_name_dict, main_genes = create_gene_dicts(genes)

    # alt loci genes are only genes on alt loci (nothing on main)
    # exon_dict contains only genes on main, index by offset of first exon

    # For every alt loci, create complex graph, translate genes and analyse them
    text_graph = create_initial_grch38_graph(args.chrom_sizes_file_name)
    graph, name_trans = grch38_graph_to_numeric(text_graph)


    equal_total = 0
    equal_exons_total = 0
    for b in text_graph.blocks:
        if "alt" in b:

            #if b != "chr1_KI270762v1_alt":
            #    continue

            print("Analysing genes on alt locus %s" % b)
            genes_here = alt_loci_genes[b]

            trans, complex_graph = merge_alt_using_cigar(graph, name_trans, b)

            #print("Addign translation")
            full_trans = name_trans + trans
            #print(trans)

            # Find candidates on main path to check against:
            genes_against = main_genes[b]
            genes_against_translated = []
            #print(len(genes_against))
            n = 0
            for mg in genes_against:
                #if n % 5 == 0 and n > 0:
                #    print("  Translated %d/%d genes" % (n, len(genes_against)))
                n += 1
                genes_against_translated.append(translate_single_gene_to_aligned_graph(mg, full_trans).interval)
                sys.stdout.write('\r  Translating main genes: ' + str(round(100 * n /len(genes_against)))  + ' % finished ' + ' ' * 20)
                sys.stdout.flush()

            print()
            #print(genes_against)
            #print("Genes here")

            genes_here_translated = []
            n = 0
            for mg in  genes_here:
                n += 1
                genes_here_translated.append(translate_single_gene_to_aligned_graph(mg, full_trans).interval)
                sys.stdout.write('\r  Translating alt genes: ' + str(round(100 * n /len(genes_here)))  + ' % finished ' + ' ' * 20)
                sys.stdout.flush()

            #print(genes_here)

            print("\n  Candidates to check against: %d" % len(genes_against))

            equal, equal_exons = _analyse_multipath_genes_on_graph(genes_here_translated,
                                                                   genes_against_translated,
                                                                   complex_graph)
            equal_total += equal
            equal_exons_total += equal_exons

            assert equal <= len(genes_here)

            print("  Equal: %d, equal exons: %d, total %d genes" % (equal, equal_exons, len(genes_here)))

    print("SUM:")
    print("Equal: %d, equal exons: %d" % (equal_total, equal_exons_total))


def analyse_multipath_genes(args):

    import pickle
    with open("%s" % args.multipath_genes_file_name, "rb") as f:
        genes = pickle.loads(f.read())

    # Create a simple dict index to speed up duplicate search
    genes_index = {}
    for g in genes:
        if g.start_pos.offset in genes_index:
            genes_index[g.start_pos.offset].append(g)
        else:
            genes_index[g.start_pos.offset] = [g]

    print(genes)

    # Exon index
    print("Creating exon index")
    exon_index = {}
    for g in genes:
        first_exon = g.critical_intervals[0]
        index = "%s,%s" % (first_exon.region_paths[0], first_exon.start_position.offset)
        if index in exon_index:
            exon_index[index].append(g)
        else:
            exon_index[index] = [g]

    print("Created exon index")


    equal = 0
    equal_exons = 0
    n = 1
    for g in genes:
        if n % 1000 == 0:
            print("Checked %d genes" % n)
        n += 1
        #if g.start_pos.region_path_id != g.end_pos.region_path_id:
        #    print(g)

        #for g2 in genes_index[g.start_pos.offset]:

        first_exon = g.critical_intervals[0]
        index = "%s,%s" % (first_exon.region_paths[0], first_exon.start_position.offset)
        for g2 in exon_index[index]:#genes_index[g.start_pos.offset]:
            if g is g2:
                continue

            if g == g2:
                #print("=== Equal ==")
                #print(g)
                #print(g2)
                equal += 1

            if g.faster_equal_critical_intervals(g2):
                #print("== Equal critical intervals ==")
                #print(g)
                #print(g2)
                equal_exons += 1

    print("Equal: %d" % (equal / 2))
    print("Equal exons: %d" % (equal_exons / 2))

if __name__ == "__main__":

    """
    args = lambda: None
    args.out_file_name = "profile_test"
    args.chrom_sizes_file_name = "grch38.chrom.sizes"

    import cProfile
    import re
    cProfile.run('merge_all_alignments(args)')
    sys.exit()
    """

    parser = argparse.ArgumentParser(
        description='Interact with a graph created from GRCh38')
    subparsers = parser.add_subparsers(help='Subcommands')

    # Subcommand for create graph
    parser_create_graph = subparsers.add_parser(
        'create_graph', help='Create graph')
    parser_create_graph.add_argument(
        'chrom_sizes_file_name',
        help='Tabular file containing two columns, chrom/alt name and size')
    parser_create_graph.add_argument(
        'alt_locations_file_name',
        help='File containing alternative loci')
    parser_create_graph.add_argument(
        'out_file_name',
        help='Name of file to store graph and translation objects insize')

    parser_create_graph.set_defaults(func=create_graph)

    # Subcommand for genes
    parser_genes = subparsers.add_parser(
        'check_duplicate_genes', help='Check duplicate genes')
    parser_genes.add_argument(
        'translation_file_name',
        help='Translation file created by running create_graph')

    parser_genes.add_argument('genes_file_name', help='Genes')
    parser_genes.set_defaults(func=check_duplicate_genes)

    # Subcommand for merge alt loci using alignments
    parser_merge_alignments = subparsers.add_parser(
        'merge_alignment', help='Merge graph using alignments of alt locus')

    parser_merge_alignments.add_argument(
        'translation_file_name',
        help='Translation file created by running create_graph')
    parser_merge_alignments.add_argument(
        'alt_locus_id', help='Id of alt locus (e.g. chr2_KI270774v1_alt')

    # Subcommand for merge alt loci using alignments
    parser_merge_alignments.set_defaults(func=merge_alignment)

    # Merge all alignments
    parser_merge_all_alignments = subparsers.add_parser(
        'merge_all_alignments',
        help='Merge graph using alignments of ALL alt loci')

    parser_merge_all_alignments.add_argument(
        'chrom_sizes_file_name',
        help='Tabular file containing two columns, chrom/alt name and size')
    parser_merge_all_alignments.add_argument(
        'out_file_name',
        help='File name to store translation object for new graph')
    parser_merge_all_alignments.set_defaults(func=merge_all_alignments)

    # Translate genes to aligned graph
    parser_translate_genes_to_aligned_graph = subparsers.add_parser(
        'translate_genes_to_aligned_graph',
        help='Analyse genes on a merged graph, created by calling merge_all_alignments')

    parser_translate_genes_to_aligned_graph.add_argument(
        'merged_graph_file_name',
        help='Name of file created by running merge_all_alignments')
    parser_translate_genes_to_aligned_graph.add_argument(
        'genes',
        help='Tabular file containing genes')

    parser_translate_genes_to_aligned_graph.add_argument(
        'gene_name',
        help='Name of gene')

    parser_translate_genes_to_aligned_graph.add_argument(
        'out_file_name',
        help='Name of file to write genes to')

    parser_translate_genes_to_aligned_graph.set_defaults(
        func=translate_genes_to_aligned_graph)

    # Analyze multipaht_genes
    parser_analyse_multipath_genes = subparsers.add_parser(
        'analyse_multipath_genes',
        help='Analyse genes on a merged graph, created by calling merge_all_alignments')

    parser_analyse_multipath_genes.add_argument(
        'multipath_genes_file_name',
        help='Name of file generated by translate_genes_to_aligned_graph')
    parser_analyse_multipath_genes.set_defaults(func=analyse_multipath_genes)

    # Analyze multipaht_genes2
    parser_analyse_multipath_genes2 = subparsers.add_parser(
        'analyse_multipath_genes2',
        help='Analyse genes on a merged graph, created by calling merge_all_alignments')

    parser_analyse_multipath_genes2.add_argument(
        'genes_file_name',
        help='Name of gene file (e.g. genes_refseq.txt)')
    parser_analyse_multipath_genes2.add_argument(
        'chrom_sizes_file_name',
        help='Name of file with chrom sizes, used to build graph (e.g. grch38.chrom.sizes)')
    parser_analyse_multipath_genes2.set_defaults(func=analyse_multipath_genes2)

    # Visualize genes
    parser_visualize_genes = subparsers.add_parser(
        'visualize_genes',
        help='Produce html visualization (that can be saved and opened in a browser)')
    parser_visualize_genes.add_argument('translation_file_name',
                                        help='')
    parser_visualize_genes.add_argument('genes_file_name',
                                        help='Pickled genes file')
    parser_visualize_genes.set_defaults(func=visualize_genes)

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.help()

    sys.exit()

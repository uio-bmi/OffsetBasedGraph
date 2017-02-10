from collections import defaultdict


class GeneMatcher(object):

    categories = ["FLANK", "ALT", "BUBBLE", "START", "END"]

    def __init__(self, alt_gene, main_genes):
        self.alt_gene = alt_gene
        self.main_genes = [gene for gene in main_genes if
                           gene.strand == alt_gene.strand]
        self.category = self.classify_alt_gene(alt_gene)
        self.merged_rps = [rp for rp in
                           alt_gene.transcription_region.region_paths
                           if self.is_merged(rp)]

        self.func_dict = {"FLANK": self.compare_flank_gene,
                          "ALT": self.compare_var_gene,
                          "BUBBLE": self.compare_bubble,
                          "START": self.compare_crossing,
                          "END": self.compare_crossing}

        self.find_match()

    def find_match(self):
        if not self.main_genes:
            self.scores = []
            self.score = -1
            return
        comp_func = self.func_dict[self.category]
        self.scores = [comp_func(main_gene) for main_gene in self.main_genes]
        max_score = max(self.scores)
        if (max_score < 1) and self.category == "FLANK":
            print(max_score, self.alt_gene.name)
        self.score = max_score
        self.match_gene = self.main_genes[
            self.scores.index(max_score)]

    @staticmethod
    def is_merged(name):
        return name.count("chr") > 1

    @staticmethod
    def was_alt(name):
        return "alt" in name

    @staticmethod
    def is_varying(name):
        return GeneMatcher.was_alt(name) and not GeneMatcher.is_merged(name)

    @staticmethod
    def classify_alt_gene(gene):
        rps = gene.transcription_region.region_paths
        if not any(GeneMatcher.is_varying(rp) for rp in rps):
            return "FLANK"
        if GeneMatcher.is_merged(rps[0]) and GeneMatcher.is_merged(rps[-1]):
            return "BUBBLE"
        elif GeneMatcher.is_merged(rps[0]):
            return "START"
        elif GeneMatcher.is_merged(rps[-1]):
            return "END"
        if len(rps) == 1:
            return "ALT"
        else:
            raise Exception("Couldnt classify %s" % rps)

    def compare_flank_gene(self, main_gene):
        if main_gene == self.alt_gene:
            return 3
        if main_gene.approxEquals(self.alt_gene, tolerance=10):
            return 2
        if main_gene.contains(self.alt_gene):
            return 1.5
        if main_gene.contains(self.alt_gene, tolerance=10):
            return 1
        if any(rp == self.alt_gene.transcription_region.region_paths[0]
               for rp in main_gene.transcription_region.region_paths):
            return 0.5

        return 0

    def compare_var_gene(self, main_gene):
        exon_diffs = self.alt_gene.exon_diffs(main_gene)
        if exon_diffs is not None:
            if exon_diffs < 40:
                return 2
            else:
                return 1
        return 0

    def compare_bubble(self, main_gene):
        contained_pairs = main_gene.get_contained_pairs(self.alt_gene)
        main_exons = main_gene.exons
        alt_exons = self.alt_gene.exons
        if not contained_pairs:
            return 0
        if len(contained_pairs) == len(alt_exons):
            return 5
        alt_matches = [p[1] for p in contained_pairs]
        main_matches = [p[0] for p in contained_pairs]

        cur = True
        passed_mid = False
        for exon in alt_exons:
            new = exon in alt_matches
            if passed_mid and not new:
                return 1
            if (not cur) and new:
                passed_mid = True

            cur = new
        if not passed_mid:
            return 2

        mid_alt_exons = [exon for exon in alt_exons
                         if exon not in alt_matches]

        mid_main_exons = []
        passed_start = False
        passed_mid = False
        for exon in main_exons:
            match = exon in main_matches
            if match:
                if passed_mid:
                    break
                passed_start = True
                continue

            if not passed_start:
                continue
            mid_main_exons.append(exon)
            passed_mid = True
        if not len(mid_main_exons) == len(mid_alt_exons):
            return 3
        diffs = [a_e.length()-m_e.length() for a_e, m_e
                 in zip(mid_alt_exons, mid_main_exons)]
        diff_sum = sum(abs(diff) for diff in diffs)
        if diff_sum < 50:
            return 5
        return 4

    def compare_crossing(self, main_gene):
        contained_pairs = main_gene.get_contained_pairs(self.alt_gene)
        main_exons = main_gene.exons
        alt_exons = self.alt_gene.exons
        if not contained_pairs:
            return 0
        if len(contained_pairs) == len(alt_exons):
            return 5

        if self.category == "END":
            main_exons = main_exons[::-1]
            alt_exons = alt_exons[::-1]
            contained_pairs = contained_pairs[::-1]

        last_main, last_alt = contained_pairs[-1]

        i = self.alt_gene.exons.index(last_alt)
        j = main_gene.exons.index(last_main)
        if not len(alt_exons)-i == len(main_exons)-j:
            return 1

        diffs = [m_e.length()-a_e.length() for
                 m_e, a_e in zip(main_exons[j:], alt_exons[i:])]

        sum_diff = sum(abs(diff) for diff in diffs)
        if sum_diff < 50:
            return 4
        else:
            return 3


class GeneMatchings(object):

    def __init__(self, alt_genes, main_genes):
        self.alt_genes = alt_genes
        self.main_genes = main_genes
        self.matches = []
        self.find_matches()

    def find_matches(self):
        for name, alt_genes in self.alt_genes.lookup.items():
            main_genes = self.main_genes.lookup[name]
            for alt_gene in alt_genes:
                self.matches.append(GeneMatcher(alt_gene, main_genes))

    def __str__(self):
        lines = []
        for category in GeneMatcher.categories:
            lines.append(category)
            category_mathes = [m for m in self.matches
                               if m.category == category]
            score_dict = defaultdict(int)
            for match in category_mathes:
                score_dict[match.score] += 1
            lines.extend("\t%s: %s" % (k, v) for k, v in score_dict.items())
        return "\n".join(lines)

    def __repr__(self):
        return self.__str__()

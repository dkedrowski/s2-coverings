from __future__ import annotations

import os
import sys
import csv
from functools import partial
from multiprocessing import Pool
from pathlib import Path

from rdflib import Graph
from rdflib import URIRef
from shapely.wkt import loads

from ..geo.constrained_s2_region_converer import ConstrainedS2RegionCoverer
from ..geo.geometric_features import GeometricFeatures
from ..geo.geometric_feature import GeometricFeature
from ..rdf.kwg_ont import file_extensions
from ..rdf.s2_writer import S2Writer


class Integrator:
    """
    Abstraction over the process for integrating s2 cells together with spatial relations.
    """

    def __init__(
        self,
        compressed: bool,
        geometry_path: Path,
        output_path: Path,
        tolerance: float,
        min_level: int,
        max_level: int,
    ):
        """
        Creates a new Integrator

        :param compressed: Whether to use the S2 hierarchy to write a compressed collection of relations at various levels
        :param geometry_path: Path to the input triples TSV
        :param output_path: The path where the triples are written to
        :param tolerance: Unknown
        :param min_level: The lowest s2 level to create triples for
        :param max_level: The highest s2 level to create triples for
        """
        
        csv.field_size_limit(sys.maxsize)
        coverer = ConstrainedS2RegionCoverer(min_level, max_level)
        if not compressed:
            if min_level:
                coverer.set_min_level(min_level)
        else:
            coverer.set_min_level(0)
        with open(geometry_path, mode="r", encoding="utf-8") as input_file:
            reader = csv.reader(input_file, delimiter="\t")
            with open(output_path, mode="a", encoding="utf-8") as output_file:
                for row in reader:
                    iri = URIRef(row[0].strip())
                    geometry = loads(row[1].strip())
                    geometric_feature = GeometricFeature(geometry, iri, tolerance, min_level, max_level)
                    for s2_triple in geometric_feature.yield_s2_relations(coverer):
                        output_file.write(f"{s2_triple[0].n3()} {s2_triple[1].n3()} {s2_triple[2].n3()} .\n")

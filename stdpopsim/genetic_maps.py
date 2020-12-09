"""
Infrastructure for managing genetic maps.
"""
import warnings

import msprime

import stdpopsim


# TODO change this to use attrs
class GeneticMap:
    """
    Class representing a genetic map for a species. Provides functionality for
    downloading and cacheing recombination maps from a remote URL.

    .. todo: Document the attributes in this class

    :ivar url: The URL where the packed and compressed genetic map can be obtained.
    :vartype url: str
    """

    def __init__(
        self,
        species,
        id=None,
        url=None,
        sha256=None,
        file_pattern=None,
        description=None,
        long_description=None,
        citations=None,
    ):
        self.id = id
        self.species = species
        self.description = description
        self.long_description = long_description
        self.url = url
        self.sha256 = sha256
        self._file_pattern = file_pattern
        self.description = description
        self.citations = citations

        self._cache = stdpopsim.CachedData(
            namespace=f"genetic_maps/{self.species.id}/{id}",
            url=url,
            sha256=sha256,
            extract=True,
        )

    @property
    def map_cache_dir(self):
        """
        The path to the directory in which the files for this map are stored.
        Names for individual chromosome files within this directory can be obtained
        using :attr:`file_pattern`.

        :type: pathlib.Path
        """
        return self._cache.cache_path

    @property
    def file_pattern(self):
        """
        The pattern used to map individual chromosome id strings to files. To obtain
        the file names, you can use Python's :meth:`str.format` method, for example
        ``my_map.file_pattern.format(id=my_chromosome_id_string)``.

        :type: str
        """
        return self._file_pattern

    def __str__(self):
        s = "GeneticMap:\n"
        s += "\tspecies   = {}\n".format(self.species.name)
        s += "\tid        = {}\n".format(self.id)
        s += "\turl       = {}\n".format(self.url)
        s += "\tcached    = {}\n".format(self.is_cached())
        s += "\tcache_dir = {}\n".format(self.map_cache_dir)
        return s

    def is_cached(self):
        """
        Returns True if this map is cached.
        """
        return self._cache.is_valid()

    def download(self):
        """
        Download the genetic map to the cache.
        """
        self._cache.download()

    def get_chromosome_map(self, id):
        """
        Returns the genetic map for the chromosome with the specified ``id``.

        :param str id: The chromosome identifier.
             A complete list of chromosome IDs for each species can be found in the
             "Genome" subsection for the species in the :ref:`sec_catalog`.
        :rtype: :class:`msprime.RecombinationMap`
        :return: A :class:`msprime.RecombinationMap` object.
        """
        chrom = self.species.genome.get_chromosome(id)
        if not self.is_cached():
            self.download()
        # We assume that if the map file does not exist this is a property of the
        # map itself and not a download error. If a failure occurs reading the map
        # this is propagated to the user, as this indicates a corrupted map which
        # needs to be redownloaded.
        map_file = self.map_cache_dir / self.file_pattern.format(id=chrom.id)
        if map_file.exists():
            ret = msprime.RecombinationMap.read_hapmap(str(map_file))
        else:
            warnings.warn(
                "Warning: recombination map not found for chromosome: '{}'"
                " on map: '{}', substituting a flat map with chromosome "
                "recombination rate {}".format(id, self.id, chrom.recombination_rate)
            )
            ret = msprime.RecombinationMap.uniform_map(
                chrom.length, chrom.recombination_rate
            )
        return ret

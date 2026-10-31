# Data source

The original source is the National Highway Traffic Safety Administration (NHTSA) National Motor Vehicle Crash Causation Study (NMVCCS).

We use the NMVCCS extract published with Andreas Troxler and Jürg Schelldorfer's tutorial, [Actuarial Applications of Natural Language Processing Using Transformers](https://github.com/actuarial-data-science/Tutorials/tree/master/12%20-%20NLP%20Using%20Transformers).

## Adaptations

The 30 narratives in `batch-01` were selected from the tutorial's NMVCCS extract to form the assignment batch. This is a convenience sample, not a random or statistically representative sample. The cases were assembled to provide the required language mix and variation in narrative length and detail.

Twenty narratives are in English, five were translated into Swedish, and five combine English and Swedish. The batch includes narratives of different lengths and cases where some accident details are not stated. No synthetic typos were added; spelling and grammar were not standardized across the narratives.

The source data is de-identified. NHTSA's public data notes state that personal identifiers are removed from its files ([NHTSA data file change log](https://static.nhtsa.gov/nhtsa/downloads/NASS/Change_log.html)). The selected narratives contain no names or direct contact details.

Ten of the 30 narratives form the golden set. They were labeled by hand against the extraction schema. Values not stated in a narrative are labeled `null` or an empty list; they are not inferred.

The extract has no stated license.

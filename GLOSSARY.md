# Vehicle Accident Extraction

This project extracts structured accident facts from accident narratives and evaluates them against human-prepared labels.

## Language

**Accident narrative**:
A narrative account of one vehicle accident that serves as extraction input.
_Avoid_: document, raw claim

**Accident ID**:
An identifier for the accident represented by a narrative in a batch.
_Avoid_: document ID

**Batch**:
A named collection of accident narratives; golden labels may cover a subset for evaluation.
_Avoid_: dataset (when referring to the named collection)

**Golden set**:
The accident narratives in a batch that have human-prepared labels and are used to measure extraction accuracy.
_Avoid_: test set

**Golden label**:
The human-prepared structured accident facts for one narrative in the golden set.
_Avoid_: expected output, answer key

**Batch extraction**:
Processing accident narratives in a batch using one model profile and one extraction setup.

**Extraction setup**:
A prompt version combined with a sampling profile. A batch extraction applies one setup to one model profile.
_Avoid_: configuration, experiment

**Extraction run**:
The recorded instance of a batch extraction, including its settings and per-accident records.
_Avoid_: job, batch run

**Accident extraction record**:
The saved outcome for one accident narrative in one extraction run, including its extracted facts or failure.
_Avoid_: result (when referring to an individual extraction outcome)

**Extraction run comparison**:
A table with one row per extraction run of a batch, showing accuracy, validity, latency and cost against the golden set.
_Avoid_: report (that is REPORT.md), leaderboard

**Machine**:
The operating system, processor and logical CPU count recorded with an extraction run, so latency can be interpreted. It never includes the hostname.

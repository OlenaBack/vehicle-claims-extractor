# Vehicle Accident Extraction

This project extracts structured accident facts from accident narratives and evaluates them against human-prepared labels.

## Language

**Accident narrative**:
A narrative account of one vehicle accident that serves as extraction input.

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
Processing accident narratives in a batch using one model, prompt version, and sampling configuration.

**Extraction run**:
The recorded instance of a batch extraction, including its settings and per-accident records.
_Avoid_: job, batch run

**Accident extraction record**:
The saved outcome for one accident narrative in one extraction run, including its extracted facts or failure.
_Avoid_: result (when referring to an individual extraction outcome)

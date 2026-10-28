# Vehicle Accident Extraction

This project extracts structured accident facts from narrative descriptions and evaluates them against human-prepared labels.

## Language

**Accident description**:
A narrative account of one vehicle accident that serves as extraction input.
_Avoid_: document, raw claim

**Accident ID**:
An identifier for the accident represented by a description in a batch.
_Avoid_: document ID

**Batch**:
A named collection of accident descriptions; golden labels may cover a subset for evaluation.
_Avoid_: dataset (when referring to the named collection)

**Golden set**:
The accident descriptions in a batch that have human-prepared labels and are used to measure extraction accuracy.
_Avoid_: test set

**Golden label**:
The human-prepared structured accident facts for one description in the golden set.
_Avoid_: expected output, answer key

**Extraction run**:
One pass over a batch using one model, one prompt version, and one sampling configuration.
_Avoid_: job, batch run

**Accident extraction record**:
The saved outcome for one accident description in one extraction run, including its extracted facts or failure.
_Avoid_: result (when referring to an individual extraction outcome)

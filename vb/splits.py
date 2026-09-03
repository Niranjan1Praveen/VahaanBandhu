"""Leakage-safe train / validation / test splitting.

Random row splitting is wrong for this dataset in three independent ways, and
each needs its own defence:

* **Geographic leakage.** Neighbouring villages share road corridors and mandi
  catchments. A model trained on Karnal and tested on Karnal is not being tested
  on a new place. Whole districts are therefore held out.

* **Temporal leakage.** Requests carry dates and seasonal structure. Testing on
  a past month a model has already seen forward-looking information about is
  optimistic. A cutoff date is held out.

* **Template leakage.** An NLU test sentence that is a paraphrase of a training
  sentence measures memorisation. Whole template families are held out.

For route instances there is a fourth: two instances with the same structural
hash are the same problem, so they are kept together on one side of the split.
"""

from __future__ import annotations

import hashlib

import pandas as pd

SPLITS = ("train", "validation", "test")


def _stable_bucket(key: str, n_buckets: int = 100) -> int:
    """Deterministic hash bucket. Reproducible across runs and machines,
    unlike Python's salted builtin hash()."""
    return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16) % n_buckets


def split_requests(
    requests: pd.DataFrame,
    holdout_districts: tuple[str, ...],
    holdout_time_from: str,
    # One family only. Holding out two of six pushed the test share over 60%,
    # which starves training without measuring anything extra.
    holdout_template_families: tuple[str, ...] = ("TF_TERSE",),
) -> pd.DataFrame:
    """Assign a split to every request, with explicit leakage reasons recorded.

    Precedence matters: a row that is held out geographically stays held out
    even if its date is early, because the district is the stronger guarantee.
    """
    df = requests.copy()
    reason = pd.Series("random_bucket", index=df.index, dtype=object)
    split = pd.Series("train", index=df.index, dtype=object)

    # Base assignment is keyed on the utterance text, not the request ID, so two
    # requests that produced the identical sentence always land on the same side
    # of the split. Keying on the ID let short terse utterances appear verbatim
    # in both train and test.
    buckets = df["raw_utterance"].fillna("").map(lambda u: _stable_bucket(str(u)))
    split[buckets >= 90] = "test"
    split[(buckets >= 78) & (buckets < 90)] = "validation"

    # Template-family holdout (NLU generalisation).
    tf_mask = df["template_family"].isin(holdout_template_families)
    split[tf_mask] = "test"
    reason[tf_mask] = "holdout_template_family"

    # Temporal holdout.
    time_mask = pd.to_datetime(df["request_date"], errors="coerce") >= pd.Timestamp(holdout_time_from)
    split[time_mask] = "test"
    reason[time_mask] = "holdout_time"

    # Geographic holdout wins over everything.
    geo_mask = df["district"].isin(holdout_districts)
    split[geo_mask] = "test"
    reason[geo_mask] = "holdout_district"

    # Final pass: the district and time rules can pull one instance of a
    # repeated utterance into test while an identical sentence stays in train.
    # Any utterance that lands in test anywhere is promoted to test everywhere,
    # so a test sentence is never verbatim present during training.
    df["split"] = split
    df["split_reason"] = reason
    test_utterances = set(df.loc[df["split"] == "test", "raw_utterance"].dropna())
    promote = df["raw_utterance"].isin(test_utterances) & (df["split"] != "test")
    df.loc[promote, "split"] = "test"
    df.loc[promote, "split_reason"] = "duplicate_of_test_utterance"
    return df


def split_instances(
    instances: pd.DataFrame,
    holdout_districts: tuple[str, ...],
) -> pd.DataFrame:
    """Split route instances, keeping structurally identical problems together.

    Assignment is keyed on ``instance_hash``, not ``instance_id``, so two
    instances that are permutations of the same problem cannot land on opposite
    sides and manufacture an easy test set.
    """
    df = instances.copy()
    buckets = df["instance_hash"].map(lambda h: _stable_bucket(str(h)))
    split = pd.Series("train", index=df.index, dtype=object)
    split[buckets >= 85] = "test"
    split[(buckets >= 70) & (buckets < 85)] = "validation"

    reason = pd.Series("hash_bucket", index=df.index, dtype=object)
    geo_mask = df["district"].isin(holdout_districts)
    split[geo_mask] = "test"
    reason[geo_mask] = "holdout_district"

    df["split"] = split
    df["split_reason"] = reason
    return df


def check_leakage(
    requests: pd.DataFrame,
    instances: pd.DataFrame,
    holdout_districts: tuple[str, ...] = (),
    holdout_template_families: tuple[str, ...] = ("TF_TERSE",),
) -> dict[str, object]:
    """Return a leakage report. Every violation count here must be zero.

    Note what is *not* a violation: a template family appearing in both train
    and test is expected, because only the explicitly held-out families are
    reserved. The violation is a held-out family showing up in training.
    """
    report: dict[str, object] = {}

    train_ids = set(requests.loc[requests["split"] == "train", "request_id"])
    test_ids = set(requests.loc[requests["split"] == "test", "request_id"])
    report["request_id_overlap"] = len(train_ids & test_ids)

    train_tf = set(requests.loc[requests["split"] == "train", "template_family"])
    report["holdout_families_leaked_into_train"] = sorted(
        train_tf & set(holdout_template_families)
    )

    train_d = set(requests.loc[requests["split"] == "train", "district"])
    report["holdout_districts_leaked_into_train"] = sorted(
        train_d & set(holdout_districts)
    )
    inst_train_d = set(instances.loc[instances["split"] == "train", "district"])
    report["holdout_districts_in_train_instances"] = sorted(
        inst_train_d & set(holdout_districts)
    )

    train_h = set(instances.loc[instances["split"] == "train", "instance_hash"])
    test_h = set(instances.loc[instances["split"] == "test", "instance_hash"])
    report["instance_hash_overlap"] = len(train_h & test_h)

    # Exact duplicate utterances straddling the split.
    train_u = set(requests.loc[requests["split"] == "train", "raw_utterance"])
    test_u = set(requests.loc[requests["split"] == "test", "raw_utterance"])
    report["duplicate_utterances_across_split"] = len(train_u & test_u)

    report["passed"] = (
        report["request_id_overlap"] == 0
        and report["instance_hash_overlap"] == 0
        and not report["holdout_families_leaked_into_train"]
        and not report["holdout_districts_leaked_into_train"]
        and not report["holdout_districts_in_train_instances"]
        and report["duplicate_utterances_across_split"] == 0
    )
    return report

import numpy as np
import pytest
from ml.external_benchmark import feature_matrix, load_annotations, relevance


def test_best_to_worst_is_inverted_into_relevance():
    np.testing.assert_array_equal(relevance([5, 3, 1, 2, 4]), [2, 1, 3, 0, 4])
    with pytest.raises(ValueError):
        relevance([1, 1, 3, 4, 5])


def test_held_out_text_does_not_fit_vocabulary_and_replay_matches():
    resumes = ["Python developer SQL systems", "uniquetestword frontend React"]
    jobs = ["Python SQL engineer", "React frontend engineer"]
    matrix, fitted = feature_matrix(resumes, jobs, [0])
    assert "uniquetestword" not in fitted[0].vocabulary_
    replay, _ = feature_matrix(resumes, jobs, vectorizers=fitted)
    np.testing.assert_allclose(matrix, replay)


def test_annotation_loader_never_executes_source(tmp_path):
    path = tmp_path / "annotations.txt"
    path.write_text("ANNOTATOR_1_RANKINGS = __import__('os').getcwd()", encoding="utf-8")
    with pytest.raises(ValueError):
        load_annotations(path)

# How to Run Tests: `14_TESTING/how_to_run_tests.md`

[Back to Testing Overview](testing_overview.md) • [Back to Main Index](../README.md)

---

## 1. Prerequisites & Environment Setup

Ensure the active Python environment has all test dependencies installed (pytest):

```bash
# Verify pytest is available
pytest --version
```

All commands below should be executed from the project root directory:
```bash
cd "Indian Constitution Legal AI Assistant"
```

---

## 2. Command Cheatsheet

### 2.1 Run the Full Test Suite (All 319 Tests)
```bash
pytest
```
- Executes all 28 test modules.
- Takes approximately 20–35 seconds on CPU.
- Expected output: `319 passed in XX.XXs`.

---

### 2.2 Fast Quiet Mode (Recommended for Live Demo)
```bash
pytest -q --disable-warnings
```
- Suppresses deprecation warnings and prints a concise progress dot matrix followed by the summary line.

---

### 2.3 Run a Specific Subsystem Test File

```bash
# Test Legal Named Entity Recognition (14 tests)
pytest tests/test_ner.py -v

# Test Zero-Leakage Intent Classification (12 tests)
pytest tests/test_intent.py -v

# Test Hybrid Retrieval & RRF Fusion (22 tests)
pytest tests/test_retrieval.py -v

# Test Citation Validation & Hallucination Prevention (10 tests)
pytest tests/test_citation_validator.py -v

# Test Natural Language Inference (NLI) Verifier (14 tests)
pytest tests/test_nli_verifier.py -v

# Test Search Warrant Procedural Regression (6 tests)
pytest tests/test_search_warrant_qa_regression.py -v

# Test Streamlit UI Smoke Tests (4 tests)
pytest tests/test_streamlit_smoke.py -v
```

---

### 2.4 Run a Specific Test Class or Method

```bash
# Run only the clause chunking tests
pytest tests/test_chunking.py::TestConstitutionalArticleChunking -v

# Run only a specific test function
pytest tests/test_retrieval.py::TestReciprocalRankFusion::test_exact_mathematical_rrf_calculation -v
```

---

### 2.5 Run Tests by Keyword Expression (`-k`)

```bash
# Run all tests matching 'abstention'
pytest -k "abstention" -v

# Run all tests matching 'ner' or 'intent'
pytest -k "ner or intent" -v

# Run all tests except slow regression tests
pytest -k "not regression" -v
```

---

## 3. Useful Pytest Flags for Viva Demonstration

| Flag | Meaning | Best Use Case |
| :--- | :--- | :--- |
| `-v` / `--verbose` | Verbose mode; displays every test name individually. | When presenting a specific module (e.g. `test_citation_validator.py`) to the professor. |
| `-q` / `--quiet` | Quiet mode; displays minimal output. | Running the full 319 test suite quickly. |
| `-s` / `--capture=no` | Disables output capturing; shows live `print()` statements. | Debugging intermediate pipeline logging. |
| `--tb=short` | Short traceback formatting. | Shows concise error summaries if a test fails. |
| `--durations=10` | Profiles and lists the 10 slowest test functions. | Performance profiling and optimization. |
| `--collect-only` | Collects and counts tests without running them. | Instant verification of test count (319 tests in 2 seconds). |

---

## 4. Live Viva Demonstration Script

During your project viva, your professor may say:
> *"Show me that your automated test suite passes and verify that your citation validator works."*

### Step 1: Open Terminal in VS Code
```bash
pytest tests/test_citation_validator.py -v
```
**Explain to the Professor:**
> *"Here, we are executing `test_citation_validator.py`. You can see that it tests 10 distinct failure modes, including catching non-existent document IDs, rejecting unretrieved citations, and detecting ungrounded landmark case mentions in generated text."*

### Step 2: Run Full Suite Smoke Test
```bash
pytest tests/test_streamlit_smoke.py tests/test_benchmark_integrity.py -v
```
**Explain to the Professor:**
> *"These tests verify the integrity of our gold benchmark and ensure that our Streamlit user interface runs cleanly offline without making external network calls."*


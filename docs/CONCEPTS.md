# The Scout-Maker-Checker-Curator Pattern

This architecture delegates responsibilities to four specialized agents to ensure robust and reliable document processing. Each agent has a distinct role, similar to a human assembly line with quality control.

## The Workflow Stages

### 1. Scout Agent (The Surveyor) 🔍
**Role**: Exploration & Analysis
The Scout is the first to touch the document. It does not perform the main task (like summarization). Instead, it surveys the "terrain" to prepare downstream agents.
*   **Responsibilities**:
    *   Detects file type, language, and encoding.
    *   Analyzes document structure (headings, pages).
    *   Assesses document quality (is it blurry? is it text-heavy?).
    *   Extracts basic metadata (author, creation date).

### 2. Maker Agent (The Craftsman) ⚙️
**Role**: Execution & Generation
The Maker performs the core work. It takes the raw document and the Scout's intelligence to produce the desired output.
*   **Responsibilities**:
    *   **Summarization**: Reading text and producing a summary.
    *   **Extraction**: Parsing structured data (names, dates, amounts).
    *   **Classification**: Assigning categories or tags.
    *   **Translation**: Converting text between languages.

### 3. Checker Agent (The Inspector) ✅
**Role**: Validation & Quality Control
The Checker is a critic. It doesn't look at the original document as much as it looks at the *Maker's output*. It ensures the work meets specific quality rules.
*   **Responsibilities**:
    *   Validates format (is it valid JSON?).
    *   Checks constraints (is the summary less than 500 words?).
    *   Verifies content (does the extracted date exist in the text?).
    *   Calculates a confidence score.

### 4. Curator Agent (The Manager) 🎯
**Role**: Orchestration & Delivery
The Curator is the boss. It manages the lifecycle. It receives reports from everyone and decides the final outcome.
*   **Responsibilities**:
    *   **Orchestration**: Calls Scout, Maker, and Checker in order.
    *   **Decision Making**: If Checker fails, Curator can trigger a retry (e.g., asking Maker to try a different strategy) or flag for human review.
    *   **Packaging**: Formatting the final result for the API/User.

---

## Concrete Example: Invoice Data Extraction

Let's imagine the user uploads a file named `invoice_2024.pdf`.

#### Step 1: Scout
*   **Input**: `invoice_2024.pdf`
*   **Action**: Reads the byte stream. Detects it's a PDF. Counts 1 page. Detects English language. content is clean (no OCR needed).
*   **Output**:
    ```json
    { "type": "pdf", "pages": 1, "language": "en", "quality_score": 0.98 }
    ```

#### Step 2: Maker
*   **Input**: PDF Content + Scout's Output
*   **Task**: "Extract Invoice Number and Total Amount"
*   **Action**: Uses text analysis (or an LLM) to find patterns.
*   **Output**:
    ```json
    { "invoice_num": "INV-555", "amount": 1500.00, "currency": "USD" }
    ```

#### Step 3: Checker
*   **Input**: Maker's Output
*   **Rules**:
    1.  `amount` must be a positive number.
    2.  `currency` must be standard ISO code.
    3.  `invoice_num` must not be empty.
*   **Action**: Runs validation logic.
*   **Output**:
    ```json
    { "passed": true, "issues": [], "trust_score": 1.0 }
    ```
    *(If Maker had extracted -500.00, Checker would return `passed: false` and an error).*

#### Step 4: Curator
*   **Action**: Reviews Checker's report. Sees it passed.
*   **Decision**: Success.
*   **Output**: Returns the final JSON response to the user's dashboard.

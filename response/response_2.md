Excellent project brief. The core challenge you've identified—moving from a retrospective, confirmatory system to a prospective, real-time discovery engine—is the central problem in building truly intelligent monitoring systems. Your detailed breakdown of the limitations and research questions is spot on.

Here is a comprehensive approach to evolving FedSpeak to maximize its prospective value while maintaining high accuracy.

### Answering the Meta-Question: Is Prospective Detection Viable?

Yes, the fundamental approach is not only viable but also incredibly valuable. However, the objective must be framed correctly. The goal should not be to build a perfect, automated oracle that definitively predicts policy shifts with 100% precision and recall. That is likely impossible due to the inherent noise and ambiguity in human language.

Instead, the goal should be to build an **intelligent candidate generation and scoring system**. This system's purpose is to augment the expertise of a human analyst (a Fed watcher, economist, or trader) by systematically and empirically identifying potential language shifts that have a high probability of being significant. It sifts through the noise to surface the most important signals, allowing the expert to focus their attention where it matters most.

The theoretical best-case precision/recall will be a trade-off. A well-designed system could likely achieve high recall (catching most significant shifts) at the cost of moderate precision (flagging some minor or insignificant changes). The key is to provide enough contextual scoring so that the user can easily distinguish between a "critical alert" and a "low-confidence signal."

---

## Proposed System Architecture: A Hybrid, Multi-Layered Approach

I recommend evolving FedSpeak into a four-layer architecture. This directly builds on your "Hybrid Approach" suggestion, providing a robust framework for integrating known signals with new discoveries.

*   **Layer 1: Confirmed Signals Engine (Current System)**
    *   **Function:** High-precision monitoring of the 5+ manually curated and historically validated keywords.
    *   **Value:** Provides reliable, low-noise alerts on well-understood policy language. This is the bedrock of the system's credibility. It should be retained and expanded as new terms are validated.

*   **Layer 2: Anomaly Detection Engine (Prospective Candidate Generation)**
    *   **Function:** Unsupervised statistical monitoring of *all* meaningful phrases (n-grams) in a new document compared to a historical baseline. Its job is to answer: "What's new or different in this statement?"
    *   **Value:** This is the core of the prospective discovery system. It is designed for high recall, ensuring it captures potentially significant new terms like "transitory" the moment they appear.

*   **Layer 3: Significance & Context Engine (Signal Scoring)**
    *   **Function:** Takes the raw candidates from Layer 2 and enriches them with contextual and semantic data to score their likelihood of being policy-significant. It answers: "Of all the things that are new, what actually matters?"
    *   **Value:** This layer dramatically improves the system's precision, filtering out statistical noise and allowing the system to rank and prioritize alerts for the end-user.

*   **Layer 4: Validation & Promotion Loop (System Learning)**
    *   **Function:** A framework for validating candidates using external data (market reaction, media coverage) and expert feedback. Validated candidates can be "promoted" to the Layer 1 Confirmed Signals Engine.
    *   **Value:** Creates a learning loop, allowing the system to become smarter over time and continuously expand its set of high-confidence monitored terms.

---

## Task-Specific Methodologies and Implementations

Here is how to approach the specific evaluation requests you outlined, using the proposed architecture.

### Task 1: Retrospective Discovery Test (The "Transitory" Case)

**Objective:** Design a methodology that, using only data through 2020, would have identified "transitory" as significant in April 2021 and flagged its removal in December 2021.

This task is handled by **Layer 2 (Anomaly Detection)** and **Layer 3 (Significance Scoring)**.

#### **Proposed Algorithm:**

1.  **Corpus & Baseline:**
    *   Define a **dynamic baseline corpus** consisting of the text from all FOMC statements in the 24 months prior to the new statement.
    *   Define a **target document**: the newly released statement (e.g., April 28, 2021).

2.  **Feature Extraction (Layer 2):**
    *   Process both the baseline corpus and the target document by removing common stop words, converting to lowercase, and stemming/lemmatizing.
    *   Extract all unigrams, bigrams, and trigrams (n-grams) from both.

3.  **Statistical Anomaly Detection (Layer 2):**
    *   For every n-gram in the target document, calculate a statistical "novelty" score comparing its frequency in the target vs. the baseline. The **log-likelihood ratio (G-test)** is excellent for this, as it's better than Chi-squared for sparse data (i.e., new words).
    *   **Calculation:** Compare two frequency counts for each n-gram: (1) its count in the new statement vs. the word count of the new statement, and (2) its count in the 2-year baseline corpus vs. the total word count of that corpus. A high G-test score indicates the term's frequency is statistically unlikely given its historical usage.

4.  **Significance Scoring (Layer 3):**
    *   Rank all n-grams from the target document by their G-test score. "Transitory" would have scored very high in April 2021 because its count went from 0 in the baseline to a non-zero value.
    *   To distinguish it from noise, calculate a **Policy Relevance Score** for the top candidates:
        *   **Positional Weight:** Assign a higher score if the term appears in the first 25% of the statement (often where the main policy assessment resides).
        *   **Semantic Proximity:** Using a Word2Vec model trained on the full FOMC corpus, calculate the cosine similarity of the candidate term's vector to the average vector of a "policy seed" set (e.g., `['inflation', 'employment', 'growth', 'policy', 'rate', 'risk']`). "Transitory" would score high as it appeared directly alongside "inflation."
        *   **Persistence (Post-facto):** Track this score over time. When "transitory" reappeared in subsequent 2021 statements, its significance score would increase, confirming it wasn't a one-off variation.

#### **Expected Results:**

*   **April 2021 (Emergence):** The algorithm would have flagged "transitory" with a high G-test score (as it was new) and a high Policy Relevance Score (due to its proximity to "inflation" and position). It would have been presented as a top candidate for a significant emerging term.
*   **December 2021 (Removal):** The same process would be run. However, an n-gram that was previously persistent and had a high significance score but now has a count of 0 would trigger a "Removal Alert." The system would flag that "transitory," a previously significant term, has been explicitly removed, signaling a policy shift.

---

### Task 2: Synonym Validation and Discovery

**Objective:** Empirically validate, discover, and prune synonyms for the five core keywords.

This task utilizes **Layer 3 (Significance Engine)** by building a dedicated semantic model of the Fed's language.

#### **Proposed Methodology:**

1.  **Corpus-Specific Word Embeddings:**
    *   Train a **Word2Vec** (or a more advanced transformer like BERT) model exclusively on the entire 17+ year corpus of FOMC statements and minutes. This is critical. General-purpose English models won't capture the specific contextual nuances of Fedspeak.
    *   This creates a high-dimensional vector representation for every word, where words used in similar contexts are located close to each other in the vector space.

2.  **Empirical Synonym Discovery:**
    *   **Code-level detail:**
        ```python
        # Assuming `model` is a trained Gensim Word2Vec model
        keyword = 'accommodative'
        # The `most_similar` function finds the top N words by cosine similarity
        potential_synonyms = model.wv.most_similar(positive=[keyword], topn=10)
        print(potential_synonyms)
        # Output might be: [('supportive', 0.85), ('accommodating', 0.79), ...]
        ```
    *   For "accommodative," this method would empirically identify "supportive" as a strong synonym *if* the Fed has historically used it in similar grammatical and semantic contexts (e.g., describing the "stance of monetary policy").

3.  **Validation and Pruning:**
    *   **Validate Chosen Synonyms:** For each of your 15 current synonyms, check its cosine similarity to its parent keyword in your trained model. If the similarity is low (e.g., < 0.5), it may be a "false" synonym in the context of Fed usage.
    *   **Identify False Synonyms:** The term "easy" might be a conceptual synonym for "accommodative" to humans, but if the Fed rarely or never uses it to describe policy in your corpus, it will have a low similarity score and can be removed from the tracker to reduce noise.
    *   **Temporal Correlation:** Plot the frequency of a keyword ("patient") and a potential synonym ("gradual") over time. If they are true synonyms used interchangeably, you might see a negative correlation (as one replaces the other) or a tight positive correlation (if used together to reinforce a point). This provides a second layer of validation.

---

### Task 3: Real-Time Candidate Generation (September 2025)

**Objective:** For the latest statement, identify and score emerging candidate terms.

This is the live application of the **Layer 2/Layer 3 pipeline**.

#### **Proposed Methodology:**

1.  **Run Anomaly Detection (Layer 2):** On the day of the release, run the log-likelihood ratio algorithm described in Task 1 on the September 17, 2025 statement against the baseline corpus (statements from Sep 2023 - Aug 2025). This produces a raw, ranked list of statistically unusual n-grams.

2.  **Calculate Policy Relevance Score (Layer 3):** For the top ~50 candidates from Layer 2, compute a weighted score using features like:
    *   `G_test_score` (0-1, normalized)
    *   `is_in_first_25_percent` (binary: 1 or 0)
    *   `semantic_proximity_to_policy` (0-1, cosine similarity)
    *   `term_specificity` (0-1, ratio of term's frequency in FOMC corpus vs. a general English corpus)
    *   **Final Score = (w1 * G_test) + (w2 * Position) + (w3 * Proximity) + (w4 * Specificity)**

3.  **Escalation and Monitoring:**
    *   **Thresholds:** Any candidate with a Final Score above a set threshold (e.g., 0.75) is escalated as a **"High-Confidence Alert."** Candidates with a moderate score (e.g., 0.5-0.74) are flagged as **"Term to Watch."** These thresholds must be tuned via backtesting.
    *   **Action:** High-Confidence alerts are sent immediately. "Terms to Watch" are added to a probationary monitoring list. If they reappear in the next statement or minutes with a high score, they are automatically escalated. This prevents alerts on one-off, insignificant language variations while ensuring persistent new terms are captured.

---

### Task 4: A Comprehensive Validation Framework

**Objective:** Measure the system's prospective detection quality beyond accuracy on known shifts.

This task is the core of **Layer 4 (Validation & Promotion Loop)**.

1.  **Metrics Beyond Retrospective Accuracy:**
    *   **Precision and Recall on Held-Out Data:** As you proposed, perform backtesting. For example, train the system on data up to 2018. Then, run it on the 2019-2025 period and measure its Precision (what percentage of its alerts were actually significant?) and Recall (what percentage of known significant shifts did it catch?).
    *   **Mean Time to Detection:** For a known shift like "full range of tools" in March 2020, how quickly did the system flag it? On the day of emergence? Or after 2-3 occurrences? Shorter is better.
    *   **Expert-Reviewed Precision:** For all new alerts generated from 2025 onward, have a human expert classify them on a 3-point scale: 3=Critical Shift, 2=Minor/Interesting Change, 1=Insignificant Noise. This allows you to measure the quality of your alert pipeline.

2.  **Estimating the False Negative Rate (Missed Shifts):**
    *   This is the most challenging metric. The best approach is to use a high-quality external proxy for "ground truth."
    *   **Methodology:**
        1.  After each FOMC statement, scrape the first 10-20 articles from top financial news sources (Bloomberg, WSJ, Reuters, FT) that analyze the statement.
        2.  Use NLP techniques (e.g., Named Entity Recognition, phrase chunking) to extract the key terms and phrases that journalists identify as being new or important.
        3.  Compare this journalist-generated list of "significant shifts" to the list of alerts generated by your system.
        4.  Any term that is widely reported by journalists but was not flagged by your system is a potential **False Negative**. This provides a systematic, data-driven way to find what you missed.

3.  **Incorporating External Validation Sources:**
    *   **Market Reaction Correlation:** Create an automated process to measure market volatility in the 60 minutes following a statement release. A good source is the price volatility of short-term interest rate futures (e.g., Fed Funds Futures). When your system issues a High-Confidence Alert, does it correlate with a spike in market volatility? This provides a quantitative measure of the alert's market impact.
    *   **Media Attention Score:** For each alerted term, use a news API (like GDELT or commercial alternatives) to count the number of media mentions of that term alongside "Federal Reserve" or "FOMC" in the 24 hours post-release. A high media score validates the term's significance. This score can be integrated directly into the Layer 3 Significance Engine.

By implementing this framework, you can move beyond the circular validation of the current system and develop a robust, quantitative understanding of FedSpeak's true prospective value.
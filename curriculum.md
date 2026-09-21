# Revision Curriculum — Topics and Subtopics

**Scope:** Level 7 AI & Data Science apprenticeship EPA, plus professional discussion.

**Structure:** Area → Topic → Subtopic. Topic is the unit of scoring and scheduling. Subtopic is a tag on questions, used to ensure coverage within a topic.

**Status key:** ● existing (carried over from the v2 artefact) · ○ new (added for KSB coverage)

**Totals:** 14 areas · 53 topics · ~270 subtopics

---

## Part A — Core ML (existing)

Reconstructed from the v2 artefact. Nine areas, 30 topics. Primarily serves **K19** and **K22**.

### 1. Supervised Learning ●

| Topic | Subtopics |
|---|---|
| Linear Regression | OLS · cost function (MSE) · normal equation · gradient descent for regression · R² and adjusted R² · assumptions (linearity, homoscedasticity, independence) |
| Logistic Regression | Sigmoid function · log-likelihood · cross-entropy loss · decision boundary · multiclass (softmax) · odds ratios |
| Decision Trees | Gini impurity · information gain / entropy · pruning (pre/post) · CART · overfitting in trees |
| Random Forests | Bagging · feature randomness · out-of-bag error · feature importance · variance reduction |
| Support Vector Machines | Maximum margin classifier · support vectors · kernel trick · RBF / polynomial kernels · soft margin (C) · Lagrangian dual |
| K-Nearest Neighbours | Distance metrics (Euclidean, Manhattan, Minkowski) · choosing K · curse of dimensionality · weighted KNN · KD-trees |
| Naïve Bayes | Bayes' theorem · conditional independence assumption · Gaussian / multinomial / Bernoulli variants · Laplace smoothing · text classification use case |

### 2. Unsupervised Learning ●

| Topic | Subtopics |
|---|---|
| K-Means Clustering | Centroid initialisation · elbow method · K-means++ · inertia / WCSS · limitations (non-convex clusters) |
| Hierarchical Clustering | Agglomerative vs divisive · linkage methods (single, complete, average, Ward's) · dendrograms · cutting the dendrogram |
| DBSCAN | Core, border, noise points · epsilon and minPts · density-reachability · advantages over K-means |
| PCA & Dimensionality Reduction | Eigenvalues and eigenvectors · covariance matrix · explained variance ratio · scree plot · t-SNE (intuition) · UMAP (intuition) |

### 3. Neural Networks ●

| Topic | Subtopics |
|---|---|
| Perceptrons & Activation Functions | Single perceptron model · step function · sigmoid / tanh / ReLU / Leaky ReLU · vanishing gradient problem · why nonlinearity matters |
| Backpropagation | Chain rule · computational graph · forward vs backward pass · weight updates · gradient flow |
| Deep Neural Networks | Architecture design · hidden layers · universal approximation theorem · batch normalisation · weight initialisation (Xavier, He) |
| Convolutional Neural Networks | Convolution operation · filters/kernels · pooling (max, average) · stride and padding · feature maps · transfer learning |
| RNNs & LSTMs | Sequential data · hidden state · vanishing gradients in RNNs · LSTM gates (forget, input, output) · GRU simplification · bidirectional RNNs |
| Transformers & Attention | Self-attention · query/key/value · multi-head attention · positional encoding · encoder-decoder architecture · why transformers replaced RNNs |
| Large Language Models ○ | Next-token pretraining objective · Tokenization (BPE / subword units) · Fine-tuning vs prompting vs in-context learning · RLHF and alignment · Scaling laws · Context window limits and hallucination |

### 4. Ensemble Methods ●

| Topic | Subtopics |
|---|---|
| Bagging | Bootstrap sampling · variance reduction · parallel training · relationship to random forests |
| Boosting (AdaBoost, Gradient Boosting, XGBoost) | Sequential learning · weighted samples · AdaBoost algorithm · gradient boosting intuition · XGBoost regularisation · learning rate in boosting · LightGBM leaf-wise growth ○ · XGBoost vs LightGBM tradeoffs ○ |
| Stacking | Meta-learner concept · base learners vs meta-learner · cross-validated stacking · when to use stacking |

### 5. Model Evaluation ●

| Topic | Subtopics |
|---|---|
| Bias-Variance Tradeoff | Bias definition · variance definition · decomposition of error · underfitting vs overfitting · model complexity curve |
| Cross-Validation | K-fold CV · stratified CV · leave-one-out CV · nested CV · train/validation/test split rationale |
| Classification & Regression Metrics | Confusion matrix · precision, recall, F1 · ROC curve and AUC · MSE, RMSE, MAE, MAPE · when to use which metric · class imbalance strategies |

### 6. Regularisation & Optimisation ●

| Topic | Subtopics |
|---|---|
| Regularisation (L1, L2, Dropout) | L1 (Lasso) sparsity · L2 (Ridge) weight decay · Elastic Net · dropout mechanism · early stopping · lambda / alpha tuning |
| Optimisation & Gradient Descent | Batch / mini-batch / stochastic GD · learning rate schedules · momentum · Adam · loss functions (MSE, cross-entropy, hinge) · convexity and local minima |

### 7. Feature Engineering ●

| Topic | Subtopics |
|---|---|
| Feature Engineering & Selection | One-hot encoding · normalisation vs standardisation · feature scaling · mutual information · recursive feature elimination · multicollinearity / VIF |

### 8. Time Series ●

| Topic | Subtopics |
|---|---|
| Time Series Methods | Stationarity · autocorrelation / partial autocorrelation · ARIMA components (AR, I, MA) · seasonal decomposition · exponential smoothing · walk-forward validation |

### 9. Maths Foundations ●

| Topic | Subtopics |
|---|---|
| Linear Algebra Foundations | Vectors and matrices · matrix multiplication · transpose and inverse · eigendecomposition · dot product / cosine similarity · rank and linear independence |
| Calculus for ML | Derivatives and partial derivatives · chain rule · gradient (vector of partials) · Jacobian (intuition) · integral intuition for probability |
| Probability & Statistics | Bayes' theorem · distributions (normal, binomial, Poisson) · expected value and variance · maximum likelihood estimation · hypothesis testing basics · central limit theorem |
| Information Theory ○ | Entropy · cross-entropy · KL divergence · mutual information · why entropy appears in tree splits and in loss functions |

---

## Part B — New areas for KSB coverage

Five areas, 23 topics. This is the material the original curriculum missed entirely.

### 10. Computing Architecture & HPC ○
**Covers K16, S19**

| Topic | Subtopics |
|---|---|
| Processor architectures for ML | CPU vs GPU vs TPU · cores, threads, SIMD · memory hierarchy and cache · why matrix operations suit GPUs · VRAM as the binding constraint · mixed-precision and quantisation |
| Parallel & distributed computing | Data vs model vs pipeline parallelism · MapReduce model · Spark execution model (driver, executors, shuffles) · Amdahl's law · communication overhead · all-reduce intuition |
| Cloud service models | IaaS / PaaS / SaaS · public, private, hybrid, multi-cloud · regions and availability zones · managed ML platforms (SageMaker, Vertex, Azure ML) · shared responsibility model |
| Cloud compute & cost | Instance right-sizing · spot vs on-demand vs reserved · autoscaling · egress charges · cost per training run · FinOps basics · when cloud is the wrong answer |
| High-performance networking | Bandwidth vs latency · interconnects and RDMA (intuition) · data locality · why moving data dominates cost at scale · bottleneck analysis |

### 11. Data Engineering ○
**Covers K18, S16, S20**

| Topic | Subtopics |
|---|---|
| Storage architectures | OLTP vs OLAP · warehouse vs lake vs lakehouse · star and snowflake schemas · normalisation vs denormalisation · partitioning and bucketing · row vs columnar storage · file formats (Parquet, Avro, ORC) |
| SQL & query performance | Joins and join strategies · window functions · CTEs · indexing (B-tree, hash) · reading a query plan · predicate pushdown · cardinality and selectivity |
| Database types | Relational databases and ACID · Document stores · Key-value stores · Wide-column stores · Graph databases · Time series databases · Vector databases · CAP theorem and BASE · Scaling (replication, sharding) · Choosing a database for an ML workload |
| Pipelines & orchestration | ETL vs ELT · batch vs streaming · idempotency · DAGs and scheduling · Airflow/Dagster concepts · backfills · change data capture |
| APIs & data access | REST vs GraphQL · pagination · rate limiting · authentication (API keys, OAuth) · webhooks · retries and exponential backoff · SDKs vs raw HTTP |
| Algorithmic efficiency at scale | Big-O in time and space · hashing · sampling strategies · approximate algorithms (Bloom filters, HyperLogLog) · chunking and out-of-core processing · streaming aggregations |
| Data governance & quality | Lineage · cataloguing · PII identification and handling · GDPR essentials · retention policies · RBAC · data contracts · validation and testing of data |
| Knowledge Graphs ○ | Triples and RDF · Ontologies and schemas · Entity resolution / linking · Graph databases (e.g. Neo4j) · Knowledge graph embeddings · Use in retrieval-augmented generation |

### 12. MLOps & Deployment ○
**Covers S19**

| Topic | Subtopics |
|---|---|
| Model serving | Batch vs real-time vs streaming inference · latency budgets · REST endpoints · containerisation · Kubernetes concepts (pods, services, scaling) |
| Reproducibility & versioning | Environment pinning · data versioning · experiment tracking · model registry · random seeds · why reproducibility fails in practice |
| Monitoring & drift | Data drift vs concept drift · population stability index · KL divergence for drift · performance decay · alerting thresholds · shadow deployment |
| CI/CD for ML | Testing data as well as code · automated retraining triggers · canary and A/B rollout · rollback strategy |

### 13. Programming & Libraries ○
**Covers K18, K25**

| Topic | Subtopics |
|---|---|
| Python for data science | NumPy vectorisation · broadcasting · pandas vs Polars · memory profiling · generators and laziness · why Python loops are slow |
| ML libraries | scikit-learn API (fit / transform / predict) · pipelines and column transformers · PyTorch vs TensorFlow · eager vs graph execution · autograd · choosing between them |
| Languages in context | SQL · R and where it still wins · Scala/Java for Spark · C++ underneath the libraries · when to leave Python |
| Scientific computing & simulation | Monte Carlo methods · bootstrapping · discrete-event simulation · sensitivity analysis · numerical stability and floating point · random number generation |

### 14. Applied Practice & Business Context ○
**Covers K22, S26, S16**

| Topic | Subtopics |
|---|---|
| Problem framing | Business question to ML task · when not to use ML · defining success metrics · establishing a baseline · scoping and feasibility |
| Technique selection | Matching method to data shape, size and interpretability needs · asymmetric cost of errors · accuracy vs latency vs explainability trade-offs · build vs buy |
| Maths in organisational context | Expressing a loss function as a business cost · choosing a decision threshold · communicating uncertainty to non-specialists · explainability (SHAP, LIME) · translating statistical significance into decisions |
| Requirements & supervision | Eliciting infrastructure requirements · functional vs non-functional requirements · service levels · supervising implementation · vendor and platform evaluation |
| Responsible AI | Sources of bias · fairness metrics and their incompatibility · transparency and model cards · regulatory context · human oversight |

---

## Difficulty bands using objective question formats only

Since first iteration has no free-text answers, each band needs a format that still discriminates.

| Band | What it tests | Formats that work |
|---|---|---|
| **F1 · Vocab** | Recognise the term | MCQ term→definition · matching terms to definitions |
| **F2 · Describe** | Explain how it works | MCQ "which statement best describes…" · fill-in-the-blank within a sentence |
| **F3 · Maths intuition** | What the maths is doing | Matching formula components to their meaning · ordering the steps of an algorithm · MCQ on what a symbol controls |
| **INT · Apply & compare** | Choose and justify | Scenario MCQ ("given this data, which method…") · multi-select trade-offs · matching problems to methods |
| **ADV · Deep** | Derivation and failure modes | Numeric entry (compute a Gini, a precision, an entropy) · ordering the steps of a derivation · multi-select on subtle failure modes · spot-the-error in a code snippet or claim |

**Ordering and numeric entry are what carry the advanced band.** Sequencing the steps of backpropagation, or of a k-means iteration, or of an ARIMA workflow, tests procedural understanding that MCQ cannot reach. Numeric entry forces actual calculation.

---

## Weighting

Set `exam_weight` per topic. Suggested starting point:

| Area | Weight | Rationale |
|---|---|---|
| Maths Foundations | 1.5 | Underpins everything; K22 and K19 both lean on it |
| Supervised Learning | 1.4 | Core K19 territory |
| Model Evaluation | 1.3 | Heavily assessed, easy marks lost |
| Neural Networks | 1.2 | |
| Data Engineering | 1.2 | Three KSBs land here (K18, S16, S20) |
| Applied Practice | 1.2 | S26 and K22 |
| Computing & HPC | 1.1 | K16, S19 — previously zero coverage |
| Regularisation & Optimisation | 1.0 | |
| Unsupervised, Ensemble, Feature Eng., Time Series | 1.0 | |
| MLOps, Programming & Libraries | 0.9 | Important but shallower assessment |

Adjust once you've checked the assessment plan for how the EPA actually splits marks.

---

## Open items

1. **KSB coverage is partial.** This maps the nine KSBs you named. The full standard has considerably more. Worth mapping every K, S and B against a topic and finding the gaps systematically rather than one at a time.
2. **Behaviours (B) are unmapped.** These usually cannot be quizzed with objective questions. They may need a different mechanism — a reflection log, or simply excluding them from the tool.
3. **Curriculum size.** 53 topics is roughly double the original. Check this against your time to exam before committing; it may be better to mark some topics as awareness-only (F1–F2 ceiling) rather than driving everything to Advanced.

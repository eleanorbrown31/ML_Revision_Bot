"""Seed the area/topic/subtopic tree from curriculum.md into the database.

Run manually, after apply_migrations.py: python scripts/seed_curriculum.py

Idempotent by name-within-parent: re-running will not create duplicates.
It will not update an existing row's fields (e.g. a hand-edited exam_weight
is left alone) -- curriculum edits after the first seed belong in the
phase-7 curriculum editor, not this script.
"""

import pathlib
import sys
import tomllib

import psycopg

ROOT = pathlib.Path(__file__).resolve().parent.parent
SECRETS_PATH = ROOT / ".streamlit" / "secrets.toml"

# area name -> exam_weight, from curriculum.md's "Weighting" table.
AREA_WEIGHTS = {
    "Supervised Learning": 1.4,
    "Unsupervised Learning": 1.0,
    "Neural Networks": 1.2,
    "Ensemble Methods": 1.0,
    "Model Evaluation": 1.3,
    "Regularisation & Optimisation": 1.0,
    "Feature Engineering": 1.0,
    "Time Series": 1.0,
    "Maths Foundations": 1.5,
    "Computing Architecture & HPC": 1.1,
    "Data Engineering": 1.2,
    "MLOps & Deployment": 0.9,
    "Programming & Libraries": 0.9,
    "Applied Practice & Business Context": 1.2,
    # Part C -- vault coverage (Second Brain apprenticeship notes), added 2026-09-18.
    "AI Innovation & NLP Applications": 1.0,
    "Data-Driven Transformation & Leadership": 1.0,
    "EPA & Project Management": 1.2,
}

# area name -> [ (topic name, [subtopic name, ...]), ... ], in curriculum.md order.
CURRICULUM = [
    ("Supervised Learning", [
        ("Linear Regression", [
            "OLS", "cost function (MSE)", "normal equation",
            "gradient descent for regression", "R² and adjusted R²",
            "assumptions (linearity, homoscedasticity, independence)",
        ]),
        ("Logistic Regression", [
            "Sigmoid function", "log-likelihood", "cross-entropy loss",
            "decision boundary", "multiclass (softmax)", "odds ratios",
        ]),
        ("Decision Trees", [
            "Gini impurity", "information gain / entropy", "pruning (pre/post)",
            "CART", "overfitting in trees",
        ]),
        ("Random Forests", [
            "Bagging", "feature randomness", "out-of-bag error",
            "feature importance", "variance reduction",
        ]),
        ("Support Vector Machines", [
            "Maximum margin classifier", "support vectors", "kernel trick",
            "RBF / polynomial kernels", "soft margin (C)", "Lagrangian dual",
        ]),
        ("K-Nearest Neighbours", [
            "Distance metrics (Euclidean, Manhattan, Minkowski)", "choosing K",
            "curse of dimensionality", "weighted KNN", "KD-trees",
        ]),
        ("Naïve Bayes", [
            "Bayes' theorem", "conditional independence assumption",
            "Gaussian / multinomial / Bernoulli variants", "Laplace smoothing",
            "text classification use case",
        ]),
    ]),
    ("Unsupervised Learning", [
        ("K-Means Clustering", [
            "Centroid initialisation", "elbow method", "K-means++",
            "inertia / WCSS", "limitations (non-convex clusters)",
        ]),
        ("Hierarchical Clustering", [
            "Agglomerative vs divisive",
            "linkage methods (single, complete, average, Ward's)",
            "dendrograms", "cutting the dendrogram",
        ]),
        ("DBSCAN", [
            "Core, border, noise points", "epsilon and minPts",
            "density-reachability", "advantages over K-means",
        ]),
        ("PCA & Dimensionality Reduction", [
            "Eigenvalues and eigenvectors", "covariance matrix",
            "explained variance ratio", "scree plot", "t-SNE (intuition)",
            "UMAP (intuition)",
        ]),
    ]),
    ("Neural Networks", [
        ("Perceptrons & Activation Functions", [
            "Single perceptron model", "step function",
            "sigmoid / tanh / ReLU / Leaky ReLU", "vanishing gradient problem",
            "why nonlinearity matters",
        ]),
        ("Backpropagation", [
            "Chain rule", "computational graph", "forward vs backward pass",
            "weight updates", "gradient flow",
        ]),
        ("Deep Neural Networks", [
            "Architecture design", "hidden layers",
            "universal approximation theorem", "batch normalisation",
            "weight initialisation (Xavier, He)",
        ]),
        ("Convolutional Neural Networks", [
            "Convolution operation", "filters/kernels", "pooling (max, average)",
            "stride and padding", "feature maps", "transfer learning",
            "Biological roots (receptive field, spatial invariance)",
        ]),
        ("RNNs & LSTMs", [
            "Sequential data", "hidden state", "vanishing gradients in RNNs",
            "LSTM gates (forget, input, output)", "GRU simplification",
            "bidirectional RNNs",
        ]),
        ("Transformers & Attention", [
            "Self-attention", "query/key/value", "multi-head attention",
            "positional encoding", "encoder-decoder architecture",
            "why transformers replaced RNNs",
        ]),
        ("Large Language Models", [
            "Next-token pretraining objective", "Tokenization (BPE / subword units)",
            "Fine-tuning vs prompting vs in-context learning",
            "RLHF and alignment", "Scaling laws",
            "Context window limits and hallucination",
        ]),
        # ---- Part C additions (Second Brain, Term 1 topics 6-8 / Term 3 topics 6-8) ----
        ("Reinforcement learning", [
            "Agent, environment, states, actions and rewards", "Explore-exploit dilemma",
            "Discount factor", "Markov property and MDPs",
            "Policy, value and Q-value functions", "Bellman equation intuition",
            "Q-learning and Q-tables", "SARSA vs Q-learning", "Deep Q Networks",
            "Episodic vs continuous tasks",
        ]),
        ("Autoencoders and generative models", [
            "Encoder, decoder and latent space", "Uses of autoencoders",
            "Limitations of autoencoders", "Autoencoder types and topologies",
            "Sparse and denoising regularisation", "Latent variable models and concept vectors",
            "VAE and the continuous latent space", "VAE loss and the reparameterisation trick",
            "Bayes in the VAE", "GAN generator and discriminator", "GAN minimax objective",
            "Optimising GANs",
        ]),
        ("Transfer learning and data representation", [
            "Transfer learning concepts (domain, task)", "Transfer learning applications and negative transfer",
            "Types of data representation", "Representation heuristics (vectorisation, smoothing, sparsity, tuning)",
            "Limitations of deep learning", "GloVe and co-occurrence", "AGI and distributed representation",
        ]),
    ]),
    ("Ensemble Methods", [
        ("Bagging", [
            "Bootstrap sampling", "variance reduction", "parallel training",
            "relationship to random forests",
        ]),
        ("Boosting (AdaBoost, Gradient Boosting, XGBoost)", [
            "Sequential learning", "weighted samples", "AdaBoost algorithm",
            "gradient boosting intuition", "XGBoost regularisation",
            "learning rate in boosting", "LightGBM leaf-wise growth",
            "XGBoost vs LightGBM tradeoffs",
        ]),
        ("Stacking", [
            "Meta-learner concept", "base learners vs meta-learner",
            "cross-validated stacking", "when to use stacking",
        ]),
    ]),
    ("Model Evaluation", [
        ("Bias-Variance Tradeoff", [
            "Bias definition", "variance definition", "decomposition of error",
            "underfitting vs overfitting", "model complexity curve",
        ]),
        ("Cross-Validation", [
            "K-fold CV", "stratified CV", "leave-one-out CV", "nested CV",
            "train/validation/test split rationale",
        ]),
        ("Classification & Regression Metrics", [
            "Confusion matrix", "precision, recall, F1", "ROC curve and AUC",
            "MSE, RMSE, MAE, MAPE", "when to use which metric",
            "class imbalance strategies",
        ]),
    ]),
    ("Regularisation & Optimisation", [
        ("Regularisation (L1, L2, Dropout)", [
            "L1 (Lasso) sparsity", "L2 (Ridge) weight decay", "Elastic Net",
            "dropout mechanism", "early stopping", "lambda / alpha tuning",
        ]),
        ("Optimisation & Gradient Descent", [
            "Batch / mini-batch / stochastic GD", "learning rate schedules",
            "momentum", "Adam", "loss functions (MSE, cross-entropy, hinge)",
            "convexity and local minima",
        ]),
    ]),
    ("Feature Engineering", [
        ("Feature Engineering & Selection", [
            "One-hot encoding", "normalisation vs standardisation",
            "feature scaling", "mutual information",
            "recursive feature elimination", "multicollinearity / VIF",
        ]),
        # ---- Part C additions (Second Brain, Term 1 topic 2) ----
        ("Data preparation and cleaning", [
            "ETL stages", "Discretisation and binning", "Types of missing data (MCAR, MAR, MNAR)",
            "Deletion vs imputation", "Imputation methods", "Outliers and their detection",
            "Handling outliers", "Aggregation", "Domain-knowledge cleaning",
        ]),
    ]),
    ("Time Series", [
        ("Time Series Methods", [
            "Stationarity", "autocorrelation / partial autocorrelation",
            "ARIMA components (AR, I, MA)", "seasonal decomposition",
            "exponential smoothing", "walk-forward validation",
        ]),
    ]),
    ("Maths Foundations", [
        ("Linear Algebra Foundations", [
            "Vectors and matrices", "matrix multiplication",
            "transpose and inverse", "eigendecomposition",
            "dot product / cosine similarity", "rank and linear independence",
        ]),
        ("Calculus for ML", [
            "Derivatives and partial derivatives", "chain rule",
            "gradient (vector of partials)", "Jacobian (intuition)",
            "integral intuition for probability",
        ]),
        ("Probability & Statistics", [
            "Bayes' theorem", "distributions (normal, binomial, Poisson)",
            "expected value and variance", "maximum likelihood estimation",
            "hypothesis testing basics", "central limit theorem",
        ]),
        ("Information Theory", [
            "Entropy", "cross-entropy", "KL divergence", "mutual information",
            "why entropy appears in tree splits and in loss functions",
        ]),
        # ---- Part C additions (Second Brain, Term 1 topics 3-4) ----
        ("Descriptive statistics and distributions", [
            "Descriptive vs inferential statistics", "Choosing mean, median or mode",
            "Dispersion and Bessel's correction", "Empirical rule", "Frequency distribution shapes",
            "Skewness", "Kurtosis", "Central limit theorem in practice",
            "Correlation vs causation", "Dependent and independent variables",
        ]),
        ("Statistical testing", [
            "Parametric vs non-parametric tests", "Choosing a test", "Formulating H0 and H1",
            "One-tailed vs two-tailed", "Test statistic, p-value and alpha",
            "Type I error and confidence", "Critical values and rejection regions",
            "Z-test vs t-test", "Independent vs paired samples",
            "Equal vs unequal variance (Welch)", "ANOVA principles (F-ratio)",
            "Two-way ANOVA and interactions", "Chi-squared tests",
        ]),
    ]),
    ("Computing Architecture & HPC", [
        ("Processor architectures for ML", [
            "CPU vs GPU vs TPU", "cores, threads, SIMD",
            "memory hierarchy and cache", "why matrix operations suit GPUs",
            "VRAM as the binding constraint", "mixed-precision and quantisation",
        ]),
        ("Parallel & distributed computing", [
            "Data vs model vs pipeline parallelism", "MapReduce model",
            "Spark execution model (driver, executors, shuffles)",
            "Amdahl's law", "communication overhead", "all-reduce intuition",
        ]),
        ("Cloud service models", [
            "IaaS / PaaS / SaaS", "public, private, hybrid, multi-cloud",
            "regions and availability zones",
            "managed ML platforms (SageMaker, Vertex, Azure ML)",
            "shared responsibility model",
        ]),
        ("Cloud compute & cost", [
            "Instance right-sizing", "spot vs on-demand vs reserved",
            "autoscaling", "egress charges", "cost per training run",
            "FinOps basics", "when cloud is the wrong answer",
        ]),
        ("High-performance networking", [
            "Bandwidth vs latency", "interconnects and RDMA (intuition)",
            "data locality", "why moving data dominates cost at scale",
            "bottleneck analysis",
        ]),
        # ---- Part C additions (Second Brain, Term 1 topic 8) ----
        ("Quantum and energy-efficient AI", [
            "Qubits, superposition and entanglement", "Quantum gates and algorithms (Shor, Grover)",
            "Quantum challenges (decoherence, scaling)", "Quantum neural networks",
            "Energy metrics (kWh, PUE, TE, IE, CO2e)", "Reducing energy consumption",
            "Future priorities for AI",
        ]),
    ]),
    ("Data Engineering", [
        ("Storage architectures", [
            "OLTP vs OLAP", "warehouse vs lake vs lakehouse",
            "star and snowflake schemas", "normalisation vs denormalisation",
            "partitioning and bucketing", "row vs columnar storage",
            "file formats (Parquet, Avro, ORC)",
        ]),
        ("SQL & query performance", [
            "Joins and join strategies", "window functions", "CTEs",
            "indexing (B-tree, hash)", "reading a query plan",
            "predicate pushdown", "cardinality and selectivity",
        ]),
        ("Database types", [
            "Relational databases and ACID",
            "Document stores",
            "Key-value stores",
            "Wide-column stores",
            "Graph databases",
            "Time series databases",
            "Vector databases",
            "CAP theorem and BASE",
            "Scaling (replication, sharding)",
            "Choosing a database for an ML workload",
        ]),
        ("Pipelines & orchestration", [
            "ETL vs ELT", "batch vs streaming", "idempotency",
            "DAGs and scheduling", "Airflow/Dagster concepts", "backfills",
            "change data capture",
        ]),
        ("APIs & data access", [
            "REST vs GraphQL", "pagination", "rate limiting",
            "authentication (API keys, OAuth)", "webhooks",
            "retries and exponential backoff", "SDKs vs raw HTTP",
        ]),
        ("Algorithmic efficiency at scale", [
            "Big-O in time and space", "hashing", "sampling strategies",
            "approximate algorithms (Bloom filters, HyperLogLog)",
            "chunking and out-of-core processing", "streaming aggregations",
        ]),
        ("Data governance & quality", [
            "Lineage", "cataloguing", "PII identification and handling",
            "GDPR essentials", "retention policies", "RBAC", "data contracts",
            "validation and testing of data",
        ]),
        ("Knowledge Graphs", [
            "Triples and RDF", "Ontologies and schemas",
            "Entity resolution / linking", "Graph databases (e.g. Neo4j)",
            "Knowledge graph embeddings",
            "Use in retrieval-augmented generation",
        ]),
    ]),
    ("MLOps & Deployment", [
        ("Model serving", [
            "Batch vs real-time vs streaming inference", "latency budgets",
            "REST endpoints", "containerisation",
            "Kubernetes concepts (pods, services, scaling)",
        ]),
        ("Reproducibility & versioning", [
            "Environment pinning", "data versioning", "experiment tracking",
            "model registry", "random seeds",
            "why reproducibility fails in practice",
        ]),
        ("Monitoring & drift", [
            "Data drift vs concept drift", "population stability index",
            "KL divergence for drift", "performance decay",
            "alerting thresholds", "shadow deployment",
        ]),
        ("CI/CD for ML", [
            "Testing data as well as code", "automated retraining triggers",
            "canary and A/B rollout", "rollback strategy",
        ]),
    ]),
    ("Programming & Libraries", [
        ("Python for data science", [
            "NumPy vectorisation", "broadcasting", "pandas vs Polars",
            "memory profiling", "generators and laziness",
            "why Python loops are slow",
        ]),
        ("ML libraries", [
            "scikit-learn API (fit / transform / predict)",
            "pipelines and column transformers", "PyTorch vs TensorFlow",
            "eager vs graph execution", "autograd", "choosing between them",
        ]),
        ("Languages in context", [
            "SQL", "R and where it still wins", "Scala/Java for Spark",
            "C++ underneath the libraries", "when to leave Python",
        ]),
        ("Scientific computing & simulation", [
            "Monte Carlo methods", "bootstrapping",
            "discrete-event simulation", "sensitivity analysis",
            "numerical stability and floating point",
            "random number generation",
        ]),
        # ---- Part C additions (Second Brain, Term 1 topics 1-3) ----
        ("Power BI and DAX", [
            "Power BI components and views", "Power Query transformations", "Merge vs append",
            "Measures vs calculated columns", "CALCULATE and filter context", "SUM vs SUMX",
            "Time intelligence functions", "Semi-additive measures",
            "Data profiling and cardinality", "Resolving load errors",
        ]),
    ]),
    ("Applied Practice & Business Context", [
        ("Problem framing", [
            "Business question to ML task", "when not to use ML",
            "defining success metrics", "establishing a baseline",
            "scoping and feasibility",
        ]),
        ("Technique selection", [
            "Matching method to data shape, size and interpretability needs",
            "asymmetric cost of errors",
            "accuracy vs latency vs explainability trade-offs", "build vs buy",
        ]),
        ("Maths in organisational context", [
            "Expressing a loss function as a business cost",
            "choosing a decision threshold",
            "communicating uncertainty to non-specialists",
            "explainability (SHAP, LIME)",
            "translating statistical significance into decisions",
        ]),
        ("Requirements & supervision", [
            "Eliciting infrastructure requirements",
            "functional vs non-functional requirements", "service levels",
            "supervising implementation", "vendor and platform evaluation",
        ]),
        ("Responsible AI", [
            "Sources of bias", "fairness metrics and their incompatibility",
            "transparency and model cards", "regulatory context",
            "human oversight",
        ]),
        # ---- Part C additions (Second Brain, Term 1 topics 1-2) ----
        ("Data science foundations", [
            "Data science hierarchy of needs", "Data roles (scientist, analyst, engineer)",
            "Data science myths", "DIKW pyramid", "Entities, attributes and relationships",
            "Data modelling (conceptual, logical, physical)",
            "Structured, semi-structured and unstructured data",
            "Raw, derived, captured and exhaust data", "Abstraction and bias in data",
            "Data governance, architecture and trust", "CRISP-DM phases",
        ]),
        ("Data visualisation and dashboards", [
            "Four types of data question", "Matching question words to charts",
            "Comparison, relationship, distribution, composition",
            "Kirk's principles (trustworthy, accessible, elegant)", "Project vision and intention",
            "Explanatory, exhibitory and exploratory", "Dashboard design and interactivity",
            "Dashboard challenges",
        ]),
    ]),
    # ---- Part C: areas added so every Second Brain apprenticeship note has a home ----
    ("AI Innovation & NLP Applications", [
        ("Innovation theory & tech trends", [
            "Diffusion of innovations (Rogers)", "Creative destruction (Schumpeter)",
            "Four stages of the innovation process", "Global shifts changing organisations",
            "Ten important tech trends", "Sector innovations",
        ]),
        ("History and foundations of NLP", [
            "NLP timeline (Turing to transformers)", "Tokenisation",
            "Word embeddings (Word2Vec, GloVe)", "Options for using embeddings",
        ]),
        ("Transformer architecture in depth", [
            "Encoder and decoder stacks", "Positional encoding (sine/cosine)",
            "Query, key, value and scaled dot-product attention",
            "Multi-head attention dimensions (d_model, d_k)", "Post-layer normalisation",
            "Position-wise feedforward network (d_ff)", "Masked multi-head attention",
        ]),
        ("BERT, RoBERTa and fine-tuning", [
            "Bidirectionality", "Masked language modelling and next sentence prediction",
            "BERT model sizes", "Pretrain then fine-tune", "Contextual embeddings",
            "RoBERTa changes", "Downstream tasks",
        ]),
        ("NLU evaluation and machine translation", [
            "Accuracy, F1 and MCC", "GLUE and CoLA", "SuperGLUE tasks",
            "Transduction vs induction", "WMT 2014 and BLEU", "BLEU smoothing",
            "Encoder-only vs decoder-only vs encoder-decoder",
        ]),
        ("GPT models and LLM adaptation", [
            "GPT model evolution", "Parameter and architecture growth",
            "Fine-tuning vs few-shot vs zero-shot", "Mixture of Experts",
            "Prompt engineering techniques", "RAG vs fine-tuning", "LoRA",
        ]),
        ("Digital business models", [
            "Digital products and omnichannel", "Smart products and personalisation",
            "As-a-service models", "Intermediation and disintermediation",
            "Platform business model and sharing economy", "Blockchain, Web3 and crowdsourcing",
            "Experience economy",
        ]),
        ("Image transformers, agents and enabling technology", [
            "AI stack and AI as a service", "APIs in Industry 4.0", "LLM hosting options",
            "AI agents and agentic AI", "ViT, CLIP and DALL-E", "Diffusion and latent diffusion",
            "Cross-attention and DiT",
        ]),
        ("AI ethics and transformer futures", [
            "Ethical risk areas", "Ethics frameworks (Data Ethics Framework, Asilomar, BCS)",
            "Copilots", "Limitations of transformers", "Ownership of AI-generated content",
            "Research opportunities",
        ]),
    ]),
    ("Data-Driven Transformation & Leadership", [
        ("Digital transformation foundations", [
            "Industrial revolutions", "Digitisation, digitalisation and digital",
            "Drivers of data-driven transformation", "People, process, technology and data",
            "Governance, visionaries and data literacy", "Barriers to transformation",
        ]),
        ("Data maturity assessment", [
            "The 12 assessment areas", "Maturity levels 0-5", "Assessment questions by area",
            "Running the assessment", "Spider web reporting",
        ]),
        ("Data value", [
            "Data-driven vs value-driven", "Big data business model maturity index",
            "Design thinking", "Data science value engineering framework",
            "Prioritisation matrix",
        ]),
        ("Change management", [
            "Purpose, people, method, tools grouping", "Agile and Kanban for transformation",
            "IDS, TDS and UDS", "Why change is difficult",
            "Process-focused models (Lewin, Kotter, PDCA, 7S)",
            "People-focused models (ADKAR, nudge, Satir, Bridges, Kubler-Ross, Maurer)",
        ]),
        ("Culture change and leadership", [
            "Eight laws of digital transformation", "Three horizons", "Empowerment",
            "Design thinking and SCAMPER", "Evolution of leadership theory",
            "Leader vs manager", "Leadership styles (Lewin, Burns/Bass, servant, Goleman)",
        ]),
        ("DataOps and MLOps cultures", [
            "Dynamic transformation and Kaizen", "People barriers (inertia, doubt, cynicism)",
            "DevOps principles", "DataOps definition and manifesto",
            "MLOps principles and manifesto", "Data lake, lakehouse and data fabric",
            "Cloud vs on-premises for DataOps",
        ]),
        ("Data strategy and governance policy", [
            "Why a data strategy", "Sections of the data strategy",
            "Data architecture choices (mesh, cloud, vendor-neutral)", "Roles and the CDO",
            "Roadmap and KPIs", "Governance policy sections",
            "Data steward, custodian and owner", "Internal and external factors",
        ]),
        ("Error, bias and uncertainty", [
            "Data error vs model error", "Random vs systematic error",
            "Data bias vs model bias", "Stratified sampling",
            "Aleatoric vs epistemic uncertainty", "Sources of uncertainty",
            "Standard error and confidence intervals",
            "Monte Carlo dropout and ensembles", "Confidence and calibration",
        ]),
    ]),
    ("EPA & Project Management", [
        ("EPA assessment plan", [
            "Gateway requirements", "Project report format", "Presentation and questioning",
            "Professional discussion", "Technical test", "Grading and weighting",
            "Re-sits and re-takes", "Roles and responsibilities",
        ]),
        ("Project brief and pass criteria", [
            "Project brief requirements", "Pass criteria themes", "Distinction criteria",
            "KSB mapping by assessment method",
        ]),
        ("Project management methodologies", [
            "CRISP-DM", "TDSP", "KDD", "SEMMA",
            "Agile, Scrum, Kanban, Waterfall and SDLC", "Combining methodologies",
        ]),
    ]),
]


def load_db_uri() -> str:
    if not SECRETS_PATH.exists():
        sys.exit(f"Missing {SECRETS_PATH}. Copy .streamlit/secrets.toml.example and fill it in first.")
    with open(SECRETS_PATH, "rb") as f:
        secrets = tomllib.load(f)
    try:
        return secrets["supabase"]["db_uri"]
    except KeyError:
        sys.exit("secrets.toml is missing [supabase] db_uri.")


def get_or_create_area(cur, name: str, sort_order: int) -> str:
    cur.execute("select id from area where name = %s and is_active = true", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "insert into area (name, sort_order) values (%s, %s) returning id",
        (name, sort_order),
    )
    return cur.fetchone()[0]


def get_or_create_topic(cur, area_id: str, name: str, exam_weight: float) -> str:
    cur.execute(
        "select id from topic where area_id = %s and name = %s and is_active = true",
        (area_id, name),
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "insert into topic (area_id, name, exam_weight) values (%s, %s, %s) returning id",
        (area_id, name, exam_weight),
    )
    return cur.fetchone()[0]


def get_or_create_subtopic(cur, topic_id: str, name: str) -> str:
    cur.execute(
        "select id from subtopic where topic_id = %s and name = %s and is_active = true",
        (topic_id, name),
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "insert into subtopic (topic_id, name, learning_objectives) values (%s, %s, %s) returning id",
        (topic_id, name, psycopg.types.json.Json([])),
    )
    return cur.fetchone()[0]


def ensure_mastery_row(cur, topic_id: str) -> None:
    cur.execute(
        """
        insert into mastery (topic_id, next_due_at)
        values (%s, now())
        on conflict (topic_id) do nothing
        """,
        (topic_id,),
    )


def main() -> None:
    db_uri = load_db_uri()
    area_count = topic_count = subtopic_count = 0

    # prepare_threshold=None: the Supabase transaction pooler doesn't support
    # server-side prepared statements persisting across pooled connections.
    with psycopg.connect(db_uri, autocommit=False, prepare_threshold=None) as conn:
        with conn.cursor() as cur:
            for area_sort, (area_name, topics) in enumerate(CURRICULUM):
                weight = AREA_WEIGHTS[area_name]
                area_id = get_or_create_area(cur, area_name, area_sort)
                area_count += 1

                for topic_name, subtopics in topics:
                    topic_id = get_or_create_topic(cur, area_id, topic_name, weight)
                    topic_count += 1
                    ensure_mastery_row(cur, topic_id)

                    for subtopic_name in subtopics:
                        get_or_create_subtopic(cur, topic_id, subtopic_name)
                        subtopic_count += 1
        conn.commit()

    print(f"Seeded/verified {area_count} areas, {topic_count} topics, {subtopic_count} subtopics.")


if __name__ == "__main__":
    main()

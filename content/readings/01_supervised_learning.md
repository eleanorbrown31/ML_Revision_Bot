# Supervised Learning

## Linear Regression

Linear regression models a continuous target as a weighted sum of input features plus a bias term: ŷ = w₁x₁ + w₂x₂ + ... + b. Training means finding the weights that make predictions as close as possible to the true values, measured by Mean Squared Error (MSE) -- the average of the squared differences between predicted and actual values. Squaring matters: it punishes large errors far more than small ones, and keeps the loss smooth enough for gradient-based optimisation to work.

There are two common ways to find the best weights: the **normal equation**, a closed-form formula that solves for the optimal weights directly (fast for small datasets, but doesn't scale well to very many features), and **gradient descent**, which iteratively nudges the weights downhill along the loss surface (scales much better, and is what's used almost everywhere in practice once data gets large).

Once fitted, **R²** (and adjusted R², which penalises adding features that don't actually help) tells you what fraction of the variance in the target your model explains -- 1.0 is a perfect fit, 0 means your model does no better than just predicting the mean every time.

Linear regression's simplicity is also its main caveat: it assumes the relationship really is linear, that errors are roughly constant in spread across the range of predictions (homoscedasticity), and that observations are independent of each other. When those assumptions break down badly, the model's coefficients and confidence intervals become unreliable, even if the R² still looks reasonable.

## Logistic Regression

Despite the name, logistic regression is a classification method, not a regression one. It takes the same weighted-sum-plus-bias idea as linear regression, but passes the result through the **sigmoid function**, which squashes any real number into the (0, 1) range -- letting the output be read as a probability of belonging to the positive class.

Training doesn't use MSE. Instead it minimises **cross-entropy loss** (also called log loss), which grows very sharply when a confident prediction turns out wrong -- predicting 0.99 for the wrong class costs far more than predicting 0.6. This gives a much stronger training signal for a probability output than squared error would.

The model draws a **decision boundary**: the line (or hyperplane, in higher dimensions) where predicted probability crosses 0.5. Everything on one side is classified as one class, everything on the other as the other. For more than two classes, logistic regression generalises to **softmax regression**, which outputs a full probability distribution across all classes at once rather than a single 0-1 value.

One genuinely useful side effect of the linear-plus-sigmoid structure: the model's coefficients can be converted into **odds ratios**, giving a directly interpretable statement like "a one-unit increase in this feature multiplies the odds of the positive outcome by X" -- a big reason logistic regression remains popular in fields that need interpretable models, not just accurate ones.

## Decision Trees

A decision tree makes predictions by asking a sequence of yes/no questions about the features, splitting the data at each step into progressively purer groups, until it reaches a leaf that makes a final prediction. Two measures decide which question (split) to ask at each step: **Gini impurity** and **information gain / entropy**. Both quantify how "mixed" the classes are in a node -- Gini impurity is 0 when a node is perfectly pure (all one class), and near its maximum when classes are evenly split. CART, the algorithm behind scikit-learn's decision trees, picks whichever split reduces impurity the most at each step.

Left alone, a tree will happily keep splitting until every leaf is perfectly pure -- which usually means memorising the training data rather than learning a generalisable pattern. This is fought with **pruning**: either stopping growth early based on a rule like "don't split a node with fewer than N samples" (pre-pruning), or growing a full tree and then trimming back branches that don't earn their complexity afterward (post-pruning).

Trees are prized for being genuinely interpretable -- you can read the sequence of splits as a set of if/then rules -- but a single tree tends to have high variance: small changes in the training data can produce a quite different tree. That instability is exactly what ensemble methods like random forests and boosting are built to fix.

## Random Forests

A random forest is an ensemble of many decision trees, combined through **bagging** (bootstrap aggregating): each tree is trained on a different bootstrap sample (drawn with replacement) of the training data, and their predictions are averaged (regression) or voted (classification). Because each tree overfits its own sample slightly differently, averaging cancels out much of that noise -- reducing variance without necessarily changing each tree's own bias.

Random forests add one more trick beyond plain bagging: **feature randomness**. At each split, instead of considering every feature, each tree only considers a random subset. This decorrelates the trees further -- without it, if one feature is a strong predictor, almost every tree would split on it first, making the trees very similar to each other and undermining the variance-reduction benefit of averaging.

A useful side effect of bootstrap sampling: each tree only sees about 63% of the data (some points get selected more than once, others not at all), leaving roughly 37% "out-of-bag" per tree. Predicting each tree's out-of-bag points gives a built-in estimate of generalisation error, without needing a separate validation split. Random forests also naturally produce **feature importance** scores, based on how much each feature reduces impurity across all the trees' splits -- a handy, if imperfect, way to see what the model is actually paying attention to.

## Support Vector Machines

An SVM finds the decision boundary that maximises the **margin** -- the distance between the boundary and the nearest points of each class. Those nearest points are the **support vectors**; they're the only points that actually determine where the boundary sits, which is why SVMs can be memory-efficient at prediction time even with large training sets.

Real data is rarely perfectly separable, so a **soft margin** (controlled by a parameter C) allows some points to sit on the wrong side of the boundary, trading a bit of training error for a more robust boundary. A low C tolerates more violations (wider margin, simpler boundary); a high C insists on getting more training points right (narrower margin, more complex boundary, higher overfitting risk).

For data that isn't linearly separable at all, the **kernel trick** is what makes SVMs powerful: kernels like RBF or polynomial let the SVM behave as if it had mapped the data into a much higher-dimensional space where a linear boundary would separate it -- without ever actually computing that mapping explicitly. The maths behind this comes from the **Lagrangian dual** formulation of the optimisation problem, which expresses everything in terms of dot products between points, letting the kernel function substitute in cleanly.

## K-Nearest Neighbours

KNN is about as simple as supervised learning gets: to classify a new point, look at its K nearest neighbours in the training set (by some distance metric) and predict the majority class among them (or the average, for regression). There's no real "training" step -- KNN just stores the training data and does its work at prediction time, which is why it's called a **non-parametric** method: it doesn't commit to a fixed, small set of learned parameters the way logistic regression does.

**Choosing K** is the main design decision. A very small K (like 1) makes predictions highly sensitive to noise in individual points -- a classic overfitting setup. A large K smooths the decision boundary but can wash out genuinely local structure, trading variance for bias.

The choice of **distance metric** also matters: Euclidean distance (straight-line) is the default, but Manhattan distance (sum of absolute differences along each axis) can behave better in high-dimensional spaces, where the **curse of dimensionality** makes Euclidean distances between points increasingly similar to each other, weakening KNN's ability to discriminate. KD-trees are a common way to speed up the nearest-neighbour search itself, avoiding a full distance comparison against every training point for every prediction.

## Naïve Bayes

Naïve Bayes classifiers apply **Bayes' theorem** -- P(class | features) is proportional to P(features | class) × P(class) -- to estimate the probability of each class given the observed features, then pick the most likely one. The "naïve" part is the **conditional independence assumption**: it treats every feature as independently contributing to the class probability, ignoring any correlation between them. This is rarely exactly true in real data, but the classifier is often surprisingly effective anyway, particularly for text classification, where it's a long-standing baseline (e.g. spam filtering).

Different variants suit different feature types: **Gaussian** Naïve Bayes assumes continuous features follow a normal distribution within each class, **multinomial** suits count data (like word frequencies), and **Bernoulli** suits binary presence/absence features.

One practical wrinkle: if a feature value never appeared with a given class during training, its estimated probability would be exactly zero -- and multiplying by zero would wipe out the whole prediction regardless of other evidence. **Laplace smoothing** fixes this by adding a small pseudo-count to every feature-class combination, so no probability is ever exactly zero just because of a training-data gap.

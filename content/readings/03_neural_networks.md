# Neural Networks

## RNNs & LSTMs

A feedforward network treats each input on its own. It has no memory of what came before. That is a problem for **sequential data** such as text, speech and time series, where meaning depends on order. A **recurrent neural network (RNN)** fixes this. At each time step it takes the current input and its **hidden state** from the previous step, and produces a new hidden state and, optionally, an output. The same weights are reused at every step. The hidden state is the network's running summary of the sequence so far.

RNNs are used in several shapes. **Many-to-one** reads a whole sequence and gives one answer (sentiment of a review). **One-to-many** turns one input into a sequence (captioning an image). **Many-to-many** maps a sequence to a sequence (translation, or tagging every word).

**The vanishing gradient problem.** RNNs are trained with backpropagation through time. The gradient is multiplied by the same weights at every step it travels back. Over many steps it shrinks towards zero (vanishing) or grows without limit (exploding). When it vanishes, early steps get almost no learning signal, so the network cannot learn long-range links. In "The monkeys, which were in the tree near the river, ___ hungry", a plain RNN forgets that "monkeys" was plural by the time it reaches the gap. Exploding gradients are handled by **gradient clipping**. Vanishing gradients need a change in architecture.

**LSTM.** The **Long Short-Term Memory** network adds a **cell state**: a separate memory line that runs through the sequence with only small, controlled changes. Three **gates** control it. Each gate is a sigmoid layer that outputs a number between 0 (block) and 1 (let through) for each element of the memory.

| Gate | What it controls |
|---|---|
| **Forget gate** | How much of the old cell state to keep or erase |
| **Input gate** | How much of the new candidate information to write into the cell state |
| **Output gate** | How much of the cell state to expose as the hidden state at this step |

Because the cell state is updated mainly by addition, not repeated multiplication, gradients can flow back through many steps without vanishing. That is the main reason LSTMs handle long-range dependencies better than plain RNNs. **Peephole connections** are an extra: they let the gates look at the cell state directly.

**GRU.** The **Gated Recurrent Unit** is a simpler version. It merges the cell state and hidden state, and uses two gates (update and reset) instead of three. It has fewer parameters, trains faster, and often performs about as well as an LSTM.

**Bidirectional RNNs.** A bidirectional RNN runs one RNN forward and one backward over the sequence and combines them. Each position then sees both past and future context. This helps tasks where the whole sequence is available, such as named entity recognition. It cannot be used for real-time forecasting, because the future is not yet known.

**LSTMs for time series.** LSTMs are a popular deep-learning choice for forecasting, especially with a large amount of data, many related series, or several input variables at once. The setup:

1. **Scale** the data (for example to 0-1), fitting the scaler on training data only. LSTMs train badly on unscaled values.
2. **Build windows.** Each sample is the last *n* time steps of the inputs (shape: samples × time steps × features). The target is the next value, or the next few values for multi-step forecasts.
3. **Split by time**, not at random, and validate with walk-forward validation.
4. **Train** and compare against a simple baseline such as the last value, ARIMA or exponential smoothing.

An LSTM needs far more data than ARIMA and much more compute, and it is harder to interpret. On a single short series it often loses to a statistical model. Use it when the data and the problem justify the cost.

**Limits.** RNNs and LSTMs process steps one after another, so training cannot be parallelised across time. Very long sequences are still hard. **Transformers** replaced RNNs for most language tasks because attention lets every position look at every other position directly, and all positions are processed in parallel.

# Time Series

## Time Series Methods

A **time series** is a set of observations recorded in time order. The order carries information: today's value depends on yesterday's. This breaks the assumption behind most ML methods, that rows are independent. It is why time series has its own methods and its own way of testing.

**Components.** A series is usually described as a mix of four parts. The **trend** is the long-run direction. The **seasonality** is a pattern that repeats at a fixed period (every 12 months, every 7 days). The **cyclic** part is a rise and fall with no fixed period, such as a business cycle. The **residual** (noise) is what is left. In an **additive** model the parts are added, which suits seasonal swings of constant size. In a **multiplicative** model the parts are multiplied, which suits swings that grow with the level of the series. **Seasonal decomposition** splits a series into these parts. **STL** (Seasonal-Trend decomposition using Loess) is a common method. It handles any seasonal period and is robust to outliers.

**Stationarity.** A series is **stationary** if its mean, variance and autocorrelation do not change over time. A trend or a growing variance makes a series non-stationary. Classical models such as ARIMA need stationarity. The usual fix is **differencing**: replace each value with its change from the previous value. The **ADF test** has "not stationary" as its null hypothesis, so a small p-value suggests the series is stationary. The **KPSS test** has the opposite null ("stationary"), so a small p-value suggests it is not. Running both is good practice.

**ACF and PACF.** The **autocorrelation function (ACF)** shows the correlation between the series and itself at each lag. The **partial autocorrelation function (PACF)** shows the correlation at lag k after removing the effect of the lags in between. Use them to choose model orders. A PACF that cuts off after lag p suggests an AR(p) model. An ACF that cuts off after lag q suggests an MA(q) model. Spikes in the ACF at lag 12 in monthly data suggest yearly seasonality.

**ARIMA.** ARIMA(p, d, q) has three parts. **AR(p)** predicts the value from its own last p values. **I(d)** is the number of times the series is differenced to make it stationary. **MA(q)** predicts the value from the last q forecast errors. **SARIMA** adds seasonal versions of the same parts: (P, D, Q, s), where s is the season length. **Auto ARIMA** searches over many (p, d, q) combinations and keeps the one with the lowest AIC (a score that rewards fit and penalises complexity). After fitting, check that the residuals look like white noise. If they still show autocorrelation, the model has missed structure.

**Exponential smoothing.** A simple moving average weights the last k points equally and ignores the rest. Exponential smoothing weights all past points, with weights that shrink geometrically for older points. **Holt's method** adds a trend term. **Holt-Winters** adds a seasonal term too. Choose **additive** seasonality when swings stay the same size, and **multiplicative** when they grow with the level. Fitting a model with trend and seasonality both switched off, on data that has both, gives forecasts that are flat or miss the pattern.

**Machine learning for time series.** A standard ML model (linear regression, random forest, gradient boosting, SVR) cannot read a raw series. You first reframe it as a supervised table.

- **Lag features.** Use the value at time t-1, t-2, and so on as inputs, and the value at t as the target. The first rows have missing lags and are dropped.
- **Seasonal lag.** To capture seasonality, include a lag equal to the season length (12 for monthly data with a yearly cycle), not just lag 1.
- **Sliding window.** Use the last *window size* values as inputs. The *stride* is how far the window moves each time.
- **Exogenous variables.** These are outside inputs such as price, weather or holidays. You need their values for the forecast period too, so they must be known in advance or forecast themselves.
- **Calendar features.** Day of week, month and holiday flags help tree models, which have no built-in idea of time.

Tree models cannot extrapolate. A random forest never predicts above the largest value it saw in training, so a strong trend must be removed (by differencing or detrending) before using one.

**Statistical or ML?** Large forecasting competitions such as M4 (2018) found that statistical methods and their ensembles beat most pure ML methods. Later work showed a statistical ensemble came within a small margin of a deep-learning ensemble at a tiny fraction of the compute cost. The practical rule: start with a simple statistical baseline. Move to ML when you have a lot of data, many related series, many exogenous inputs, or non-linear patterns the baseline cannot capture. Keep the baseline as the benchmark, because a complex model that does not beat it is not worth its cost.

**Validation.** Never split a time series randomly. A random split puts future rows in the training set and past rows in the test set, so the model is tested on data it has effectively seen the future of. This is **leakage**. Hold out the **last** block of time as the test set. For more reliable estimates use **walk-forward validation** (also called time series cross-validation). Train on the first n points, predict the next step or block, then move the window forward and repeat. Each test point is always later than every training point. Scale, encode and select features using training data only, for every fold.

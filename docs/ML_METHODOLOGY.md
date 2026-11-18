# Machine Learning Methodology

Because the repository contained no data, the application uses a documented seeded synthetic dataset. It generates 1,200 rows and trains a Ridge regression model with an 80/20 split and random seed 42. The model predicts a score from 0 to 100.

The `/api/admin/models` endpoint exposes MAE, MSE, RMSE, R-squared, version, dataset, and row counts. A real dataset should replace the synthetic generator before high-stakes use.

Scores are categorized using these documented thresholds: Excellent (85–100), Good (70–84.9), Average (55–69.9), and Needs Improvement (0–54.9). These labels are descriptive demo bands, not official institutional grading rules.

Setup
  ↓
Baseline (initial N devices)
  ↓
WaitForConvergence() → while measuring [1–7]:
    - Step 1: Leader Election Phase
    - Step 4: Topology Convergence (depends on 1)
  ↓
MeasureBaselineMetrics(): [2, 3, 5, 6, 7]
  ↓
Repeat:
    - ScaleUp():
        Add node(s)
        → WaitForConvergence() [measure 1 & 4]
        → MeasureDynamicMetrics() [2, 3, 5, 6, 7]
  ↓
Then:
    - ScaleDown():
        Remove node(s) / RoleChange
        → WaitForConvergence() [measure 1 & 4]
        → MeasureDynamicMetrics() [2, 3, 5, 6, 7]

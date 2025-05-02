Setup
  ↓
Baseline (initial N devices)
  ↓
WaitForConvergence() & MeasureConvergence(MC) [1-4]
  ↓
MeasureRest(MR): [2, 3, 5, 6, 7]
  ↓
Repeat:
    - ScaleUp():
       - Add node(s)
            → WaitForConvergence() & MC
            → MR
  ↓
Repeat:
    - ScaleDown():
       -  Remove node(s) / RoleChange
            → WaitForConvergence() & MC
            → MR


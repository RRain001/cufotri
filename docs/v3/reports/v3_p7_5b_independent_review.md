# V3-P7.5B independent numerical coupling review

Verdict: `PASS_NUMERICAL_COUPLING_SEMANTICS_FROZEN`

Reviewed branch: `codex/v3-p7-5b-numerical-coupling-freeze`

Reviewed baseline: `8943ec2fa9f98f023ce6de4343e1892785521e47`

## Review answers

1. **Is operator ordering explicit?** Yes.  The executable order is soil
   deposition, leaf exchange/TFWT intermediate, OBT, root transfer, soil
   reconciliation, TFWT OBT-loss/root reconciliation, then food, intake, and
   dose readout.
2. **Which soil snapshot does root use?** The step-start `SoilState`, retained
   as the original input to `RootUptakeSolver`.
3. **What is the TFWT/OBT/root order?** OBT sees leaf-only TFWT.  OBT loss is
   subtracted first; root input is then added to final TFWT.
4. **What is forcing time semantics?** `AtmosphericHTOForcing.timestamp` is
   the interval-start `t_n` label for forcing representative of the entire
   interval; emitted endpoint states use `t_{n+1}`.
5. **Are continuous and event/readout states distinguished?** Yes.  Soil,
   TFWT, and OBT are continuous reservoirs; root and ledgers are transfer
   records; harvest, food, intake, and dose are non-mutating endpoint records.
6. **Does timestep refinement converge?** Yes for the synthetic non-trivial
   case: Soil, TFWT, and OBT all have finite non-negative inventories and
   `E2 < E1` from `dt` to `dt/2` to `dt/4`.
7. **Is conservation maintained under refinement?** Yes.  Existing soil,
   TFWT, OBT, root, and food ledger residuals remain finite and closed at all
   three step sizes.
8. **Is restart equivalent?** Yes.  The direct and JSON restart paths produce
   equal typed endpoint states and downstream readouts.
9. **Were subsystem physics changed?** No.  Only P7.5 pipeline comments,
   tests, ADR, reports, and status documentation were added or changed.
10. **Were UFOTRI or CTEAS-Atmos data introduced?** No.  The tests use only
    explicit synthetic typed inputs; no real atmospheric coupling or external
    parameter import is present.

## Audit disposition

The pipeline remains an explicit operator split rather than a fully implicit
coupled solve.  Refinement is a required numerical sensitivity check, not a
claim of physical accuracy.  Passing this review freezes software coupling
semantics and leaves the P7.6 parameter evidence/validation/calibration gate
blocked until its separate prerequisites are satisfied.

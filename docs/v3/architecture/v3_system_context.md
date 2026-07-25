# V3 system context

Status: `ARCHITECTURE_ONLY`

```mermaid
flowchart LR
    F["Forcing manifest"] --> A["Atmosphere and transport"]
    S["Source scenario"] --> A
    A --> D["Deposition and surface allocation"]
    D --> So["Soil media"]
    A --> P["Plant exchange"]
    So --> P
    P --> Fo["Food pathways"]
    Fo --> An["Animal pathways"]
    Fo --> Do["Dose"]
    An --> Do
    A --> Do
    U["Uncertainty specification"] -. parameters only .-> A
    U -. parameters only .-> D
    U -. parameters only .-> So
    U -. parameters only .-> P
    V["Validation evidence"] --> R["Validation and reporting"]
    A --> R
    D --> R
    So --> R
    P --> R
    Fo --> R
    An --> R
    Do --> R
    Pr["Provenance recorder"] -. observes .-> R
```

Forcing, source, validation evidence, and parameter packages are external
inputs with checksums. Raw external evidence stays outside Git; tracked
manifests contain provenance, licence status, schema version, and hashes.

The numerical chain owns states and transfers. Validation compares immutable
results against preregistered evidence. Reporting and provenance observe
calculations but do not alter inventories, fluxes, parameters, or time steps.

The dynamic-air, advanced re-emission, formal three-box soil, HT chemistry, and
broad food expansion candidates are outside the executable context in this
baseline.

# Facility inventory → hubs: skills, scripts and data

```mermaid
flowchart TB
    classDef raw fill:#f6e7c8,stroke:#9a7b3c,color:#222
    classDef cfg fill:#dfe9f7,stroke:#3b6ea5,color:#222
    classDef step fill:#ffffff,stroke:#555,color:#222
    classDef out fill:#e3f1e1,stroke:#4a8a44,color:#222
    classDef skill fill:#f3e3f5,stroke:#8a4a95,color:#222,stroke-dasharray: 4 3
    classDef human fill:#fde6e6,stroke:#b84a4a,color:#222

    RAW["AEA / DCRA download<br/>Utilities_Bulk_Fuel_Inventory.csv<br/>(contact columns never read)"]:::raw

    subgraph S1["skill: ingest-facility-inventory"]
        I01["01_ingest.py<br/>column_map.csv → clean schema<br/>+ diff vs previous release"]:::step
    end
    REL["inputs/raw_facility_data/&lt;year&gt;/<br/>aea_inventory_&lt;year&gt;.csv (tracked)"]:::out

    subgraph S2["skill: validate-facility-inventory  ·  validate_inventory.py [--publish]"]
        direction TB
        I02["02_apply_corrections.py<br/>approved rows, old_value-guarded"]:::step
        I03["03_normalise.py<br/>community_key, delivery flags"]:::step
        I04["04_detect.py<br/>detector registry: shared farm id,<br/>shared point, typos, copies…"]:::step
        I05["05_boundary_check.py<br/>label vs city/CDP boundary — verify only<br/>distance, located_in_place, relation"]:::step
        I06["06_review_queue.py<br/>open flags → owner sheet"]:::step
        I07["07_publish.py<br/>contract checks, qc_status"]:::step
        I02 --> I03 --> I04 --> I05 --> I06 --> I07
    end

    CORR["inputs/inventory_qc/<br/>corrections.csv · aliases.csv<br/>remote_sites.csv · thresholds.csv<br/>boundaries/*.zip · derived_columns.csv"]:::cfg

    QUEUE["review_queue.xlsx<br/>(61 open rows)"]:::out
    OWNER(["owner decides<br/>approve / reject / remote site /<br/>exclude / ask publisher"]):::human

    subgraph S3["skill: record-facility-corrections"]
        REC["record_corrections.py REVIEW.xlsx [--write]<br/>validates, asks instead of guessing"]:::step
    end

    CLEAN["outputs/00_inventory_qc/&lt;year&gt;/facilities_clean.csv<br/>community_name (service) · located_in_place ·<br/>community_relation · community_distance_km · qc_status"]:::out

    subgraph S4["skills: define-network-profile  →  build-and-verify-network"]
        direction TB
        PROF["profile.yaml (hubs knobs)<br/>group_by [community] · cannot_link_across_community<br/>remote_site_km 20 · max_snap_dist_m 25000<br/>withhold_pending_review on"]:::cfg
        N00["00_normalize_raw.py<br/>reads the published table, never the raw CSV"]:::step
        C01["consolidate<br/>withhold pending_review → 01_withheld.csv<br/>50 m merge with cannot-link → 01_site_members.csv"]:::step
        T01["tag<br/>place + borough; conflicts kept → 01b_conflicts.csv"]:::step
        H02["hubs<br/>one hub per corrected label; far site = own hub<br/>→ 02_hubs.gpkg + 02_hub_members.csv"]:::step
        A03["assemble<br/>snap cap + collision merge → 02_hub_snaps.csv<br/>→ 03_network nodes/edges"]:::step
        PROF --> N00 --> C01 --> T01 --> H02 --> A03
    end

    NET["network of record<br/>(one rebuild on the owner's machine)"]:::out

    RAW --> I01 --> REL --> I02
    CORR --> I02
    CORR --> I03
    CORR --> I04
    CORR --> I05
    I06 --> QUEUE --> OWNER --> REC --> CORR
    I07 --> CLEAN --> N00
    A03 --> NET
```

**Reading it.** Yellow is the untouched download. Blue is owner-controlled configuration, the only place anything is ever changed. White boxes are scripts, grouped by the skill that drives them. Green is a tracked or generated output. The red loop is the one human step: the queue goes out, decisions come back as rows of the configuration, and the next run applies them. Nothing moves, relabels or drops a record except an approved row in that configuration; the build withholds what is still undecided.

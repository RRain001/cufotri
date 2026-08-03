# D3 UFOTRI 手册数据映射独立复核失败报告

本报告是 fail-closed 复核结果。复核期间没有从其他 worktree 复制
validation/external_local、临时审计输出、未跟踪文件或人工笔记，也没有修改被审
映射 YAML、正式模板、H2/H3 参数、src/、正式根级 configs/、trusted registry
或 V3 tag。

~~~text
REVIEW_STATUS = FAIL_TARGET_NOT_REPRODUCIBLE
SECONDARY_FINDINGS = FAIL_SOURCE_ANCHOR_DEFECT; FAIL_TEMPLATE_INCONSISTENCY
REVIEW_TARGET = b88a251f08069329d53290ccf7510080199f0561
BASE_MAIN = f5d18886f3a635cd6c3a813d820b1f3b3e52dd3a
SOURCE_BRANCH = codex/v3-d3-ufotri-manual-data-mapping
REVIEW_BRANCH = codex/v3-d3-ufotri-manual-data-mapping-independent-review
REVIEW_WORKTREE = /Users/rain/Documents/Doctor/Topic/CETAS_ufotri_d3_manual_mapping_independent_review
REVIEW_METHOD = FRESH_WORKTREE_INDEPENDENT_RECOMPUTATION
MANUAL_SHA256 = 82c7c7f07975553a51e7ba1666a912f80096e5af4fc138aba6f45a120e6d3562
MERGE_RECOMMENDATION = DO_NOT_MERGE
~~~

## 1. 仓库身份与范围

初始化检查通过：

- main = origin/main = f5d18886f3a635cd6c3a813d820b1f3b3e52dd3a；
- 本地和远端源分支均为 b88a251f08069329d53290ccf7510080199f0561；
- 目标相对 BASE_MAIN 为 4 个提交，git diff --check 通过；
- 目标差异只涉及 D3 文档、映射/请求合同、模板和原映射测试；
- src/、正式根级 configs/、validation/v3/policy/trusted_external_evidence_registry.yaml
  的目标差异均为空；
- 创建复核 worktree 前，所有已有 worktree 均干净。

目标差异文件范围为 implementation_status、D3 commission/handoff/derived-data
文档、原映射测试、映射 YAML、requested_file_contract.yaml 和 D3 模板；没有
受保护的模型、正式配置或 registry 文件。

## 2. 目标复现门禁

映射定向测试通过：22 passed。其他定向集合也通过：

- tests/external_evidence_acquisition：42 passed；
- tests/prospective_experiment：33 passed；
- pytest --collect-only -q：693 项。

按实际发现的路径运行真重盲测试，结果为 50 passed, 1 skipped, 1 failed。
唯一失败为：

~~~text
tests/independent_review_d3_true_reblinding/test_d3_true_reblinding_independent_review.py::test_review_secret_is_untracked_and_commitment_matches
AssertionError: validation/external_local/d3_prospective_reblind_v3/
  sealed_generation_secret.json is not a file
~~~

该测试要求私有密钥保持 Git 未跟踪且与已提交 commitment 一致；目标提交树中
validation/external_local/ 只有 .gitignore 和 README，私有文件不存在。测试
断言位于 test_d3_true_reblinding_independent_review.py:158-160。按照本轮复核
边界，不能从其他 worktree 复制该文件，因此不能把环境缺失伪装成 PASS。

693 项收集通过，但全量运行不能通过；目标 implementation_status.md 中的
D3_FULL_PYTEST = PASS_693_OF_693 和 D3_ACCEPTANCE_AND_VERIFIERS =
PASS_WITH_PHYSICS_GATE_BLOCKED 不能由 fresh worktree 复现。

## 3. 手册身份

ufotri_manual.md 当前 worktree SHA、声明 source_commit 树中该文件的 SHA，以及
映射 YAML 的 source_sha256 均为：

~~~text
82c7c7f07975553a51e7ba1666a912f80096e5af4fc138aba6f45a120e6d3562
~~~

手册身份检查通过；本失败不是手册文件漂移造成的。

## 4. 字段与标签独立重算

从目标提交树中的
validation/external_evidence_acquisition/d3/d3_ufotri_manual_data_field_mapping.yaml
独立解析得到：

| 项目 | 重算结果 |
|---|---:|
| total fields | 100 |
| MANUAL_EXPLICIT | 36 |
| MANUAL_DERIVED | 10 |
| D3_DESIGN_SPECIFIC | 34 |
| MODERN_QA_REQUIRED | 17 |
| NOT_APPLICABLE_CONTROLLED_CHAMBER | 7 |
| UNRESOLVED_NO_SOURCE | 3 |
| duplicate field_id | 0 |
| field without category | 0 |
| invalid category/action/requirement | 0 |

六类标签是非互斥的；标签计数和为 107，不应与 100 个字段相加比较。
不存在自动注册、模型运行、参数更新或 trusted-registry promotion 动作。

## 5. 36 个 MANUAL_EXPLICIT 字段台账摘要

36 个字段全部有结构性 section/table/figure/equation 锚点；逐项语义、单位、
案例值边界和 OCR 边界复核结果为 34 PASS / 2 FAIL。

字段清单：

~~~text
tritium_chemical_form
air_moisture_hto_concentration
release_rate
total_released_activity
release_duration
release_height
source_geometry
wind_direction
wind_speed
stability_class
air_temperature
relative_humidity
net_solar_radiation
par_day_night_state
precipitation
measurement_height
plant_type
plant_water_mass
organic_plant_matter
leaf_area_index
daytime_stomatal_resistance
nighttime_epidermal_resistance
soil_type
soil_organic_content
volumetric_soil_water_content
soil_layer_depths
root_distribution
soil_hto_concentration
drainage_or_downward_flux
soil_reemission_rate
vegetation_water_hto_observation
plant_obt_observation
air_hto_observation
air_ht_observation
soil_ht_observation
soil_ht_deposited_inventory
~~~

两个失败字段：

1. release_rate 的 mapping reference 是 “5.2.2 Table 3; 5.3 Appendix B §1”。
   Table 3 有 release rate，但手册 Appendix B §1 只有 release quantity、
   chemical forms、release height 和 duration，没有 release rate。引用集合含
   错锚点，触发 FAIL_SOURCE_ANCHOR_DEFECT。
2. soil_layer_depths 的 mapping reference 是 “2.2.4; 2.2.5; 3.3.3
   Figure 13”。手册 §2.2.4/§2.2.5 支持 top 5 cm 和 root layers up to 30 cm，
   但 §3.3.3 Figure 13 实际是 Vegetables/OBT flowchart，不是 soil layer depth
   证据。该语义错配不能以存在 Figure 13 字符串通过。

其他 34 个字段的手册章节/表图/公式、术语、单位和案例值边界未发现独立缺陷；
LAI=3、4 s/cm、60 s/cm、20% 等均被保留为案例/示例而非 D3 默认，未发现 OCR
静默纠正或图中近似值被写成精确实验输入。

## 6. 10 个 MANUAL_DERIVED 字段台账摘要

10 个字段逐项检查了手册公式/过程、原始测量输入、观测与派生的区别、默认值和
H2/H3 参数边界，结果为 9 PASS / 1 FAIL：

~~~text
PASS release_start_end_chronology
PASS plant_height_and_canopy_characteristics
PASS plant_atmosphere_total_resistance
PASS aerodynamic_and_boundary_layer_resistance
PASS actual_evapotranspiration_and_soil_evaporation
PASS top_five_cm_soil_hto_inventory
PASS deeper_soil_hto_inventory
FAIL root_hto_uptake_flux
PASS calculated_reemission_rate
PASS obt_transfer_rates
~~~

root_hto_uptake_flux 的 mapping reference 写成 “2.2.4; 2.2.5; Equation
(37)”，但 Equation (37) 实际位于手册 §2.2.3；D3 derived-data 文档汇总行也
把该公式放在 §2.2.4-§2.2.5。该字段的物理过程虽合理，来源锚点仍不合格。

## 7. 三个未决字段

字段自身的 fail-closed 属性均通过：

| field_id | category | action | requirement | default/model/registry use |
|---|---|---|---|---|
| cultivar_specific_resistance_parameter | UNRESOLVED_NO_SOURCE | DEFER_UNRESOLVED | defer_unresolved | 未发现 |
| chamber_mixing_to_outdoor_wind_transform | UNRESOLVED_NO_SOURCE | DEFER_UNRESOLVED | defer_unresolved | 未发现 |
| root_zone_hto_transfer_function | UNRESOLVED_NO_SOURCE | DEFER_UNRESOLVED | defer_unresolved | 未发现 |

但是三项都声明位置为 requested_file_contract.yaml: unresolved_items，而该合同
实际到 line 120 结束，没有 unresolved_items 节点、字段列表、未来实验室定义/
替代方案入口或对应的可选占位合同。因此：

~~~text
FIELD_LEVEL_DEFERRED_STATUS = PASS_3_OF_3
CONTRACT_LINKAGE_STATUS = FAIL_MISSING_UNRESOLVED_ITEMS_NODE
UNRESOLVED_FIELD_REVIEW = FAIL_DEFERRED_CONTRACT_NOT_TRACEABLE
~~~

mapping 的 future_lab_status = AWAITING_LAB_CONFIRMATION 不能替代缺失的合同
入口；这不满足未来实验室可提供定义或替代方案的可追溯要求。

## 8. D3 固定定义与模板一致性

在计划列出的三份 D3 文档、映射 YAML、请求合同和五个模板中，核心定义大体
一致：

| 定义 | 结果 |
|---|---|
| HTO medium = HTO_IN_CHAMBER_AIR_MOISTURE | PASS |
| setpoint = 5270 Bq/mL air-moisture water | PASS |
| exposure/post follow-up/total = 24/120/144 h | PASS |
| primary times = 0.2, 48, 120 h | PASS |
| diagnostic times = 1, 6, 24, 72 h | PASS |
| planned biological replicates = 5 | PASS |
| primary endpoint = combined stem-and-leaf TFWT | PASS |
| roots/pods/seeds excluded from primary endpoint | PASS |
| planning LOD = 250 Bq/L tissue water, not capability claim | PASS |
| planning total relative uncertainty <=20% | PASS |
| 5 planned vs 3 minimum uncensored | PASS in current QC/package |
| wind/mixing and net-radiation/PAR marked non-equivalent | PASS |
| wind direction/Pasquill/field height/geometry/HT deposition not fabricated | PASS |

模板主键和关联字段也通过：chamber forcing 有 experiment/time/phase/HTO/
temperature/RH/mixing/PAR/location/instrument/calibration/QC；TFWT 有 sample/
plant/biological replicate/time/organ/mass/water/TFWT/LOD/LOQ/uncertainty/QC；
biomass 有 cultivar/batch/growth/material/nutrition/watering/acclimation/
uniformity/height/LAI/organ mass；manifest/QC 有 SHA-256、大小、创建/接收时间、
不可变副本、许可、发表审查、instrument、analyst、batch、blank、duplicate、
standard、calibration、deviation 和 corrective action。

整体不能记为 TEMPLATE_CONSISTENCY = PASS，原因是：

1. 三个 unresolved 字段指向不存在的 unresolved_items 合同节点；
2. derived-data 文档汇总行重复了 root_hto_uptake_flux 的错节引用；
3. 对所有 D3 文档/模板作范围扫描还发现未被本轮修订的历史/状态文本仍使用
   未声明介质的 “5270 Bq/mL water” 或把至少 3 个重复写成设计建议，例如：
   docs/implementation_status.md:111-116、
   docs/v3/benchmarks/h2_h3_minimum_discriminating_experiment_spec.md:12-27、
   docs/v3/external_data/d3_external_evidence_acquisition_report.md:155-166、
   docs/v3/experiments/d3_prospective_experiment_dry_run_report.md:69-78。
   本报告不修改这些被审范围外/历史文本；若“所有文档和模板”按字面纳入门禁，
   这些冲突本身也阻止 PASS。derived-data 文档 line 145 是“澄清为
   air-moisture water”的变更说明，属于有立即解释的例外。

## 9. Verifier、编译与保护范围

在独立 worktree 中执行：

| 检查 | 结果 |
|---|---|
| scripts/verify_acceptance.py --recompute | FAIL；缺 data/era5/era5_surface_2025-06-01_2025-06-02.csv |
| scripts/verify_v2_acceptance.py --recompute | FAIL；V1 recompute 因同一 ERA5 输入失败 |
| scripts/verify_v2_validation_readiness.py | PASS |
| scripts/verify_v3_compatibility.py | FAIL；同一缺失 ERA5 输入 |
| scripts/verify_v3_architecture_readiness.py | FAIL；同一缺失 ERA5 输入 |
| scripts/verify_v3_external_evidence_unblocking.py | blocked fail-closed；未宣称 external evidence |
| scripts/verify_v3_physics_start_gate.py | blocked；FINAL_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA |
| python -m compileall -q src tests era5 scripts validation | PASS |
| git diff --check | PASS |
| protected src/configs/trusted registry diff | empty |
| V3 tag at target | none |

REAL_EXTERNAL_EVIDENCE = FALSE、FORMAL_V3_PHYSICS = NOT_STARTED 和
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA 仍保持正确；
这些 gate 的正确性不能抵消目标测试、手册锚点和合同失败。

## 10. 条件合并决策

~~~text
INDEPENDENT_REVIEW = FAIL
MERGE_RECOMMENDATION = DO_NOT_MERGE
SOURCE_BRANCH_FINAL_HEAD = b88a251f08069329d53290ccf7510080199f0561
MAIN_FINAL_HEAD = f5d18886f3a635cd6c3a813d820b1f3b3e52dd3a
ORIGIN_MAIN_FINAL_HEAD = f5d18886f3a635cd6c3a813d820b1f3b3e52dd3a
SOURCE_BRANCH_MOVED = FALSE
MAIN_MOVED = FALSE
V3_TAG_CREATED = FALSE
SOURCE_BRANCH_FAST_FORWARD = NOT_PERFORMED
MAIN_FAST_FORWARD = NOT_PERFORMED
MAIN_PUSH = NOT_PERFORMED
~~~

失败路径只提交本报告；不提交独立测试、不修改被审对象、不移动源分支和 main。
下一次复核前必须由受控流程解决私有真重盲输入的 fresh-worktree 可复现性、修正
手册锚点、补齐 requested_file_contract.yaml 的 unresolved 合同节点，并重新同步
所有纳入门禁的 D3 文档/模板状态。

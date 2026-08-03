# D3 UFOTRI 手册派生数据要求与实验室交接映射

## 1. 状态边界

```text
DOCUMENT_STATUS = PRE_LAB_MANUAL_DERIVED_DATA_REQUIREMENTS
UFOTRI_MANUAL = PRIMARY_PHYSICAL_DATA_SOURCE
UFOTRI_MANUAL_SHA256 = 82c7c7f07975553a51e7ba1666a912f80096e5af4fc138aba6f45a120e6d3562
D3_DESIGN = FROZEN_PROJECT_SPECIFIC_LAYER
MODERN_QA = ADDITIONAL_NON_UFOTRI_REQUIREMENT
MAPPING_ID = D3_UFOTRI_MANUAL_DATA_FIELD_MAPPING_V1
MAPPING_FIELDS = 100
REAL_EXPERIMENT = NOT_EXECUTED
REAL_EXTERNAL_EVIDENCE = FALSE
H2_H3_FORMAL_SELECTION = NOT_AUTHORIZED
FORMAL_V3_PHYSICS = NOT_STARTED
LAB_FEASIBILITY_STATUS = AWAITING_LAB_CONFIRMATION
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

本报告的逐字段机器可读事实来源是
`validation/external_evidence_acquisition/d3/d3_ufotri_manual_data_field_mapping.yaml`。
本轮只冻结“需要什么数据、数据如何命名、哪些字段不适用、哪些事项仍未决”，
不把手册案例值写成 D3 参数，也不构成实验执行批准或外部验证。

映射字段的分类计数如下。一个字段允许多标签，因此计数不是互斥分区；
`NOT_APPLICABLE_CONTROLLED_CHAMBER` 的 7 个字段同时保留了手册来源标签。

| 分类 | 字段数 | 含义 |
|---|---:|---|
| `MANUAL_EXPLICIT` | 36 | 手册正文、公式、表格或案例明确出现的量/观测。 |
| `MANUAL_DERIVED` | 10 | 手册公式或过程需要、但不是直接观测列的派生量。 |
| `D3_DESIGN_SPECIFIC` | 34 | 当前 D3 设计冻结的项目要求，不是 UFOTRI 手册一般要求。 |
| `MODERN_QA_REQUIRED` | 17 | 现代实验可追溯、质量控制和软件接收所需字段。 |
| `NOT_APPLICABLE_CONTROLLED_CHAMBER` | 7 | 野外释放/扩散字段在当前受控箱体中不适用。 |
| `UNRESOLVED_NO_SOURCE` | 3 | 当前手册和冻结 D3 设计都不能给出依据，保持未决。 |

## 2. 手册证据范围

| 手册位置 | 本轮提取的物理要求 | 交接用途与限制 |
|---|---|---|
| §2.2.2，Eq. (7)-(24) | 植物水与有机物两个组分；HTO 植物/大气交换；总阻力、气动/边界层阻力、LAI、植物类型、温度、PAR、土壤含水量、日/夜阻力。 | 支持植物交换字段和派生阻力字段；`4 s/cm`、`60 s/cm`、`LAI=3` 仅作为手册案例值。 |
| §2.2.3，Eq. (33)-(37) | 土壤类型、含水量、水势/水力传输、土层、向下输运和根系吸水。 | 支持基质、根区和土壤水分要求；不提供当前大豆箱体根途径的实验室能力。 |
| §2.2.4，Eq. (38)-(44-2) | 蒸散、土壤蒸发、降水影响、顶层土壤和再释放。 | 支持背景/根区诊断；D3 不据此推算未测的箱体再释放率。 |
| §2.2.5 | 顶部 5 cm、深层至约 30 cm、根系分布和 HTO 随水吸收。 | 要求明确根途径状态；根样不进入主要终点。 |
| §2.2.6、§3.3.3，Eq. (65)-(66) | 植物 HTO、交换性/非交换性 OBT 及 OBT 转移率。 | OBT 是手册明确过程，但不是当前 D3 主要分类终点。 |
| §5.2.1 | 加拿大野外场地、土壤、含水量、风速、风向、温度、净辐射、RH、降水和测量高度。 | 这些是野外案例证据，不能直接拼接进受控箱体。 |
| §5.2.2，Table 3 | release rate、风场/稳定度、净辐射、土壤水、植物水、有机物、LAI、日/夜阻力、再释放。 | 提取输入字段，但案例参数与 D3 项目参数严格分开。 |
| §5.2.3，Figures 21-28 | 空气、土壤、植被水 HTO/HT 的时序比较。 | 手册说明数日趋势可复现，但单点偏差可达数量级；不是当前项目外部验证。 |
| §5.3，Table 8 | HT/HTO、释放高度、Pasquill 稳定度、风速、温度、降水、土壤和植被 benchmark 参数。 | 仅作 benchmark 案例；不写入 D3 实验协议。 |

手册转换存在 OCR/表格风险。本映射保留了手册原始术语（例如
`anorganic plant water content`），只在显示名中做可读化；发现会影响单位或
定义的歧义时，状态为 `SOURCE_TEXT_AMBIGUOUS` 或 `OCR_REVIEW_REQUIRED`，不静默
修正、不猜测图表数字、不把近似读数当精确实验值。

## 3. 分类规则

- `MANUAL_EXPLICIT`：手册直接列出或明确讨论的物理量、观测量或过程。
- `MANUAL_DERIVED`：由手册公式/过程计算需要，但必须由当前实验数据和明确算法派生。
- `D3_DESIGN_SPECIFIC`：当前 D3 的暴露、样品、植物材料、对照和时序要求；不得称为手册要求。
- `MODERN_QA_REQUIRED`：SHA-256、许可证、批次、方法、LOD/LOQ、QC 和原始文件保留等治理字段。
- `NOT_APPLICABLE_CONTROLLED_CHAMBER`：野外大气扩散字段在本受控箱体中不填值。
- `UNRESOLVED_NO_SOURCE`：没有足够来源决定的字段，动作必须是 `DEFER_UNRESOLVED`。

### 3.1 手册到 D3 的总映射表

下表按物理/交接域汇总字段；每个 `field_id` 的完整手册锚点、单位、动作和
模板列位以机器可读 YAML 为准。

| 数据字段（field_id） | 手册依据 | 分类 | D3 处理 | 模板位置 |
|---|---|---|---|---|
| `tritium_chemical_form`; `air_moisture_hto_concentration`; `release_duration` | §2.2.2；§5.2.2 Table 3；§5.2.3 | `MANUAL_EXPLICIT` | 直接记录 HTO 空气水分时序；持续时间单独采用 D3 24 h | chamber forcing；QC schedule |
| `release_rate`; `total_released_activity`; `release_height`; `source_geometry` | §2.2.1；§5.2；§5.3 Appendix B/Table 8 | `MANUAL_EXPLICIT` + `NOT_APPLICABLE_CONTROLLED_CHAMBER` | 不进入箱体物理；入口几何仅可作工程元数据 | 无 D3 物理列；manifest/metadata 可记录 |
| `wind_direction`; `stability_class` | §2.2.2 Eq. (22)-(24)；§5.2.2 | `MANUAL_EXPLICIT` + `NOT_APPLICABLE_CONTROLLED_CHAMBER` | 不适用，不填猜测值 | 无 |
| `wind_speed`; `air_temperature`; `relative_humidity` | §2.2.2；§5.2.1-5.2.2 | `MANUAL_EXPLICIT` | 风速只映射为箱体混合速度类比；温度/RH 直接测量 | chamber forcing |
| `net_solar_radiation`; `par_day_night_state` | §2.2.2；§2.2.4；§5.2.2 | `MANUAL_EXPLICIT` | 记录 PAR/照明值与单位；不称为净太阳辐射等价物 | chamber forcing |
| `precipitation` | §2.2.2；§2.2.4；§5.2.1 | `MANUAL_EXPLICIT` + `NOT_APPLICABLE_CONTROLLED_CHAMBER` | 干箱体要求记录零/事件状态；湿叶情景另行授权 | chamber forcing |
| `measurement_height`；`release_start_end_chronology` | §5.2.1-5.2.3；§2.2.1 | `MANUAL_EXPLICIT` / `MANUAL_DERIVED` | 保留测点、UTC 时间戳和单调 elapsed time | chamber/TFWT CSV |
| `plant_type`; `plant_water_mass`; `organic_plant_matter` | §2.2.2；§3.3.3；§5.2.2 | `MANUAL_EXPLICIT` | 对应 soybean、组织水、鲜/干质量；手册质量值不作 D3 默认 | TFWT/biomass |
| `leaf_area_index`; `daytime_stomatal_resistance`; `nighttime_epidermal_resistance` | §2.2.2 Eq. (9)-(14)；Table 3 | `MANUAL_EXPLICIT` | LAI/阻力可记录；案例值只标为 example/case parameter | biomass；metadata |
| `soil_type`; `soil_organic_content`; `volumetric_soil_water_content`; `soil_layer_depths` | §2.2.3-2.2.4；§5.2.1；Table 8 | `MANUAL_EXPLICIT` | 基质、含水量时序和必要层深进入实验室交接 | biomass；requested contract |
| `root_distribution`; `soil_hto_concentration`; `drainage_or_downward_flux` | §2.2.3；§2.2.5；Eq. (44-1) | `MANUAL_EXPLICIT` | 记录根途径状态和诊断测量；不默认根区为零 | QC/root pathway |
| `soil_reemission_rate`; `top_five_cm_soil_hto_inventory`; `deeper_soil_hto_inventory` | §2.2.4；Eq. (44-1)/(44-2) | `MANUAL_EXPLICIT` / `MANUAL_DERIVED` | 仅作背景/根区诊断，不从 D3 背景反推 UFOTRI 率 | chamber/background；requested contract |
| `vegetation_water_hto_observation`; `air_hto_observation` | §5.2.3 Figures 25-28；§2.2.2 | `MANUAL_EXPLICIT` | 主要观测为 TFWT，介质和水基准必须显式 | chamber/TFWT |
| `plant_obt_observation`; `obt_transfer_rates` | §2.2.6；§3.3.3 Eq. (65)-(66) | `MANUAL_EXPLICIT` / `MANUAL_DERIVED` | OBT 可作独立诊断，不进入 H2/H3 主分类 | requested contract |
| `air_ht_observation`; `soil_ht_observation`; `soil_ht_deposited_inventory` | §5.2.3 Figures 21-24 | `MANUAL_EXPLICIT` | 当前 HTO 箱体不适用，不移植野外 HT 释放证据 | 无 |
| `plant_atmosphere_total_resistance`; `aerodynamic_and_boundary_layer_resistance`; `actual_evapotranspiration_and_soil_evaporation` | §2.2.2 Eq. (8)-(24)；§2.2.4 Eq. (38)-(43) | `MANUAL_DERIVED` | 保留接口/诊断边界；不进行未授权 D3 参数反演 | requested contract |
| `root_hto_uptake_flux`; `calculated_reemission_rate` | §2.2.3 Eq. (37)；§2.2.4-§2.2.5 Eq. (44-2) | `MANUAL_DERIVED` | 需要真实实验室测量或批准算法；当前不计算 | root pathway |
| `d3_air_moisture_hto_setpoint`; `d3_exposure_duration`; `d3_post_exposure_followup` | 当前 D3 preregistration/commission package | `D3_DESIGN_SPECIFIC` | 5270 Bq/mL air-moisture water；24 h；120 h | checklist/QC/contract |
| `d3_primary_sampling_times`; `d3_diagnostic_sampling_times`; `d3_biological_replicates` | 当前 D3 preregistration/commission package | `D3_DESIGN_SPECIFIC` | 主采样 0.2/48/120 h；五个独立生物重复；诊断点不可替代主点 | checklist/QC |
| `d3_exposed_group`; `d3_pre_exposure_baseline_group`; `d3_zero_hto_control_group`; `d3_reserve_group` | 当前 D3 commission/checklist | `D3_DESIGN_SPECIFIC` | 四类组独立编号、随机化并保留损耗规则 | TFWT/biomass/contract |
| `d3_primary_endpoint_definition`; `d3_primary_endpoint_exclusions` | 当前 D3 protocol/checklist | `D3_DESIGN_SPECIFIC` | 茎叶合并 TFWT；根、豆荚、种子排除；legacy total-plant-body 仅为标签映射 | TFWT/QC/checklist |
| `d3_soybean_cultivar`; `d3_plant_batch`; `d3_sowing_date`; `d3_growth_stage` | 当前 D3 lab handoff | `D3_DESIGN_SPECIFIC` | 增加实验室必须填写的植物材料字段 | biomass/TFWT |
| `d3_substrate_nutrition_watering`; `d3_pre_exposure_acclimation`; `d3_plant_uniformity` | 当前 D3 lab handoff | `D3_DESIGN_SPECIFIC` | 增加材料与暴露前状态记录 | biomass/contract |
| `d3_root_pathway_status`; `d3_substrate_hto_status`; `d3_watering_water_hto_status`; `d3_substrate_moisture_time_series` | 当前 D3 manual-aligned handoff | `D3_DESIGN_SPECIFIC` | 将根区从“未写字段”变成显式控制/测量门槛 | QC/checklist/contract |
| `d3_chamber_mixing_velocity`; `d3_temperature_control`; `d3_relative_humidity_control`; `d3_precipitation_condition`; `d3_forcing_logging_interval` | 当前 D3 commission package | `D3_DESIGN_SPECIFIC` | 记录 0.5 m/s 类比、25±1 °C、70±5% RH、干箱体、5 min 或更细 | chamber/QC/checklist |
| `d3_background_maximum_fraction`; `d3_background_operational_mean` | D3 background amendment/protocol | `D3_DESIGN_SPECIFIC` | 实测最大值 ≤ 名义设定值 0.5%；规划均值与最大值分开 | chamber/QC/checklist |
| `d3_planning_lod`; `d3_planning_total_uncertainty` | 当前 D3 planning contract | `D3_DESIGN_SPECIFIC` | 250 Bq/L 是规划目标；实际 LOD/LOQ/不确定度必须由实验室提供 | TFWT/QC/checklist |
| `d3_blind_analysis_chronology`; `d3_classifier_thresholds` | D3 reblinding/preregistration | `D3_DESIGN_SPECIFIC` | 固定预测—样品—解盲顺序；0.15/0.50 dex 只作不可修改的协议边界 | contract/protocol |
| `sample_and_replicate_identity`; `sample_time_axis`; `sample_organ_definition`; `sample_mass_and_tissue_water`; `tfwt_result` | 现代样品级 QA | `MODERN_QA_REQUIRED` | 新增样品、植株、时间、器官、水基准和未四舍五入结果 | TFWT/biomass |
| `analytical_lod_loq`; `analytical_uncertainty`; `analytical_method_and_instrument`; `analytical_qc_controls`; `analytical_batch_and_analyst` | 现代分析 QA | `MODERN_QA_REQUIRED` | 由实验室填写方法、基质、LOD/LOQ、空白、平行、标准、回收、批次和分析员 | TFWT/QC |
| `deviation_and_corrective_action`; `quality_flags_and_missing_encoding`; `data_dictionary_and_composite_membership` | 现代数据治理 | `MODERN_QA_REQUIRED` | 缺失值、质量标志、偏差和复合样成员不得静默丢失 | all templates/contract |
| `raw_file_identity_and_hash`; `raw_file_times_and_immutable_copy`; `licence_and_publication_rights`; `raw_file_retention` | 现代数据治理 | `MODERN_QA_REQUIRED` | 文件名、SHA-256、大小、时间、只读副本、许可和保留策略进入 manifest | raw manifest/contract |
| `cultivar_specific_resistance_parameter`; `chamber_mixing_to_outdoor_wind_transform`; `root_zone_hto_transfer_function` | 当前没有可授权来源 | `UNRESOLVED_NO_SOURCE` | 保持 `DEFER_UNRESOLVED`；不能转成项目假设或自动参数 | contract unresolved_items |

## 4. 受控箱体替代关系

| UFOTRI/野外字段 | D3 箱体记录 | 关系边界 |
|---|---|---|
| 野外风速 | 箱体混合速度 | 运行类比；不等同于外场风速或阻力输入。 |
| 野外净太阳辐射 | PAR/受控照明值及单位 | 记录光环境；不等同于净辐射。 |
| 野外风向 | 不适用 | 不填猜测值。 |
| Pasquill-Gifford 稳定度 | 不适用 | 不为箱体虚构稳定度类别。 |
| 释放高度 | 箱体入口几何（可选工程记录） | 只作工程追溯，不视为物理等价。 |
| 降水 | 干箱体零值与事件标志 | 当前不适用；只有批准湿叶情景时才扩展。 |

## 5. 不能直接由手册决定的项目要求

以下项目来自冻结 D3 设计或现代 QA，不得写成 UFOTRI 手册要求：

- 主采样 `0.2, 48, 120 h`；诊断点 `1, 6, 24, 72 h`；
- 每个主时间点 5 个独立生物重复；
- `0.15 dex` 不可判别阈值和 `0.50 dex` 双模型均不足阈值；
- `250 Bq/L tissue water` 项目规划 LOD，不是已确认实验室能力；
- 总相对不确定度 `<=20%` 的规划目标，不是手册性能声明；
- 暴露前基线、零 HTO 对照、暴露组和备用植株；
- blind analysis chronology、预测冻结顺序和 SHA-256 manifest；
- 许可证、再分发、发表审查、原始文件只读保留；
- 大豆品种、批次、生长阶段、播种日期、基质、营养、供水、驯化和均一性。

这些字段已分别标记为 `D3_DESIGN_SPECIFIC` 或 `MODERN_QA_REQUIRED`。

## 6. 模板审计与本轮处理

| 文件 | 已覆盖内容 | 本轮增加/澄清 | 结论 |
|---|---|---|---|
| `templates/chamber_forcing_template.csv` | 时间轴、HTO、温度、RH、混合、光、降水、仪器、校准、质量标志 | 改为 `experiment_phase`、空气水分 HTO 明确列、背景比例、PAR/辐射单位、测量高度/位置和 experiment ID | 已修改 |
| `templates/tfwt_sample_template.csv` | 样品、植株、重复、组织、时间、鲜/干重、组织水和 TFWT | 增加暴露组、批次、`COMBINED_STEM_AND_LEAF`、LOD/LOQ、检测下标志、合并不确定度、批次/分析员和校准 | 已修改 |
| `templates/biomass_template.csv` | 植物与组织质量 | 增加品种、批次、播种日期、基质、营养、供水、驯化、均一性、株高、LAI、根/茎/叶/豆荚/种子分项 | 已修改 |
| `templates/quality_control_checklist.yaml` | 24 h/120 h/144 h、背景、采样、分析和原始文件门槛 | 区分计划 5 个重复与至少 3 个未删失重复；明确茎叶主终点、根/豆荚/种子排除、实际 LOD/LOQ、QC、根区和控制组 | 已修改 |
| `templates/raw_manifest_template.yaml` | SHA-256、大小、许可证、只读副本 | 增加创建/接收时间、仪器、数据字典、再分发/发表审查和保留策略 | 已修改 |
| `requested_file_contract.yaml` | 暴露、forcing、观测、分析、语义和 rights | 增加空气水分介质、茎叶端点、植物材料、根区/对照、分析批次和数据治理字段 | 已修改 |
| `d3_lab_feasibility_handoff_checklist.md` | 实验室能力、材料、对照、LOD 和主终点 | 明确根/豆荚/种子排除、根区状态、基质/供水 HTO 和水分时序；加入手册案例值边界 | 已修改 |
| `d3_experiment_commission_package.md` | D3 commissioning 设计 | 将 `5270 Bq/mL water` 澄清为 `5270 Bq/mL air-moisture water`，并把 legacy endpoint 映射到显式茎叶定义 | 已修改 |

未修改 `ufotri_manual.md`、`src/`、正式根级 `configs/`、H2/H3 参数、分类
阈值、主要采样时间、重复数、合成数据、trusted registry 和 V3 tag。映射文件
没有任何自动注册、校准、H2/H3 运行或解盲动作。

## 7. 手册局限与解释边界

1. 手册的植物在大气模块中通常是单一植物 compartment；§5.3 明确指出，
   根菜等地下部分的分区描述不准确，绿色蔬菜被用作代表。对大豆的根、谷物、
   果实/豆荚分区能力不能直接从手册推出。
2. 手册更适合绿色蔬菜和草的环境/摄入链描述；它没有给出当前实验室大豆品种、
   基质、供水、营养或装置能力。
3. 加拿大实验主要检验释放后数日内的空气、土壤和植被水趋势。§5.2.3 说明，
   单个时刻的计算与实测可能相差约一个数量级，根分布、植物重量和阻力简化会
   影响结果；这不是当前项目的 empirical validation。
4. 手册中的 `LAI=3`、日/夜阻力、土壤水分和再释放率是案例或模型参数，不能
   自动成为 D3 正式参数，更不能代表实验室已确认能力。
5. 手册中 HT、野外风向/稳定度、释放高度和场地几何属于外场/事故模型上下文，
   受控箱体只保留明确的工程或诊断记录，不进行不等价拼接。

## 8. 冻结结论

```text
UFOTRI_MANUAL_PHYSICAL_DATA_REQUIREMENTS = MAPPED
D3_PROJECT_SPECIFIC_REQUIREMENTS = FROZEN
MODERN_QA_REQUIREMENTS = SEPARATELY_IDENTIFIED
LAB_HANDOFF_PACKAGE = READY_FOR_FUTURE_REVIEW
LAB_FEASIBILITY_STATUS = AWAITING_LAB_CONFIRMATION
REAL_EXPERIMENT = NOT_EXECUTED
REAL_EXTERNAL_EVIDENCE = FALSE
H2_H3_FORMAL_SELECTION = NOT_AUTHORIZED
FORMAL_V3_PHYSICS = NOT_STARTED
NEXT_STEP = WAIT_FOR_LAB_OR_AUTHORIZED_REAL_DATA
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

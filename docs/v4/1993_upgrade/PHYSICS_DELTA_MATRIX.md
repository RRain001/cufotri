# UFOTRI **4.0（1993）** 物理过程差异矩阵 — KfK 5194

> **版本确认（重要）：此文件审计的目标版本是 W. Raskob 于 1993 年 8 月出版的《Description of the New Version 4.0 of the Tritium Model UFOTRI Including User Guide》，报告编号 KfK 5194。它不是 1990 年 KfK 4605 的公式清单，也不是“CUFOTRI 软件 V4 版本”的完成证明。1990 年 KfK 4605 只作为旧物理基线用于逐项比较。**

**文档身份**：`UFOTRI_4_0_1993` / `KfK 5194` / 1993-08；原报告 PDF 102 页，含正文印刷页与附录；[KIT 官方全文](https://publikationen.bibliothek.kit.edu/270034158/3813483)，[DOI](https://doi.org/10.5445/IR/270034158)。对照文献：W. Raskob，**KfK 4605（1990）**，[KIT 官方全文](https://publikationen.bibliothek.kit.edu/270029395/3813413)。必要时参考 1991 年 KfK 4853 用户指南，以区分从 1990 到 1991 已有的机制与真正的 1993 更新。

**审计状态（首轮）**：`PARTIAL_SOURCE_ANCHORED_AUDIT_IN_PROGRESS`。已对 KfK 5194 的关键章节、方程位置和主要数值进行了原文核查；尚未完成 1993 全部输入卡片/附录默认值与 1990 所有公式的双向逐式复核，更未证明现有程序等价于 1993 UFOTRI 4.0 可执行文件。

**判读原则**：
- 所有“1993 应如何计算”的规范性问题，以 **KfK 5194** 的印刷页、方程、表格、选项为第一依据。KfK 4605 的方程只用于历史比较；**1990 Eq.(33) 与 1993 Eq.(33) 不是同一个公式**。
- “1993 报告记载”与“1990→1993 已确认发生改变”是两种证据强度。1993 中已有的能力，不因再次出现而自动归类为新增。
- “代码存在同名/类似模块”不表示原版 1993 方程和默认值已恢复。`UNVERIFIED` 不得解释成不存在。
- 来源为官方 PDF/手册，不把原始 PDF 复制到公开仓库；若源式图形扫描或 OCR 失真，以印刷页核对结果为准。
- 保持已冻结 **KFK4605_1990** 默认数值行为。未来每项 **KFK5194_1993_V4** 兼容性实现都必须为可选路径；除非另有独立验收，不得重写现有基线或科学容差。

## 1. 1993 原始文献证据清单（初步）

1993 KfK 5194 第 5—6 章明确覆盖植物交换、土壤—大气交换、土壤水、作物发育、光合作用与 OBT、食物链和剂量。下面按报告印刷页列出 **1993 目标规范**；对应的 1990 比较依据取自 KfK 4605 的不同章节。

| ID | 过程 / 1993 目标 | 1993 印刷页与章节 | 版本判定（首轮） | 代码入口 |
|---|---|---|---|---|
| `UF93-01` | MUSEMET primary atmospheric trajectory | §5.1, pp.2–3 | 框架层面延续 | `src/cteas_ufotri/atmosphere/ufotri_native_v4.py` |
| `UF93-02` | Secondary re-emission plume source | §5.1, pp.3 | 1993 详细公式待逐式复核 | `src/cteas_ufotri/coupling/reemission_area_source_v4.py` |
| `UF93-03` | Stomatal and canopy resistance options | §5.2, pp.4–6 | 1993 新增/扩展已证实 | `src/cteas_ufotri/plant/leaf_ufotri_v4/model.py` |
| `UF93-04` | Stability and aerodynamic/boundary resistance | §5.2, pp.4–5 | 1993 详细公式待逐式复核 | `src/cteas_ufotri/plant/leaf_ufotri_v4/model.py` |
| `UF93-05` | HT dry deposition and microbial soil conversion | §5.3.2, pp.8–9 | 1993 详细公式待逐式复核 | `src/cteas_ufotri/atmosphere/deposition.py` |
| `UF93-06` | Monteith vs Penman evapotranspiration | §5.3.1, pp.7–8 | 1993 新增/扩展已证实 | `src/cteas_ufotri/soil/water_balance.py` |
| `UF93-07` | Thin top-soil help layer and soil surface resistance | §5.3.2, pp.9–10 | 1993 新增/扩展已证实 | `src/cteas_ufotri/plant/soil_v4/soil_solver.py` |
| `UF93-08` | HTO whole-plume wet washout | §5.3.3, pp.14 | 1993 详细公式待逐式复核 | `src/cteas_ufotri/atmosphere/wet_deposition.py` |
| `UF93-09` | Soil suction, conductivity and layered water transport | §5.3.4, pp.14–15 | 1993 给出具体闭合关系 | `src/cteas_ufotri/plant/soil_ufotri_v4/model.py` |
| `UF93-10` | Root uptake depth and layer weights | §5.3.4, pp.15–16 | 机理/职责延续 | `src/cteas_ufotri/plant/soil_v4/soil_solver.py` |
| `UF93-11` | Soil HTO re-emission daytime and night branches | §5.3.4, pp.15–16 | 1993 公式修订已证实 | `src/cteas_ufotri/coupling/reemission_area_source_v4.py` |
| `UF93-12` | Crop stage, LAI and plant mass evolution | §5.4, pp.16–18 | 1993 新增/扩展已证实 | `src/cteas_ufotri/crop/phenology.py` |
| `UF93-13` | Photosynthesis-driven net CO2 assimilation | §5.5.1, pp.19–21 | 1993 新机理已证实 | `src/cteas_ufotri/plant/obt_ufotri_v4/model.py` |
| `UF93-14` | OBT formation alternative modes | §5.5.2, pp.21–23 | 1993 新增/扩展已证实 | `src/cteas_ufotri/plant/obt_ufotri_v4/model.py` |
| `UF93-15` | Diurnal factor in 1993 simple and advanced OBT paths | §5.5.2, pp.22–23 | 1993 参数已证实 | `src/cteas_ufotri/plant/obt_ufotri_v4/model.py` |
| `UF93-16` | Grass organic-compartment OBT half-time | §6.2.2, pp.27–28 | 1993 参数修订已证实 | `src/cteas_ufotri/foodchain/ufotri_vegetable_grass_v4.py` |
| `UF93-17` | Leafy vegetable organic-compartment OBT half-time | §6.2.3, pp.28 | 1993 参数修订已证实 | `src/cteas_ufotri/foodchain/ufotri_vegetable_grass_v4.py` |
| `UF93-18` | Potato edible tuber compartment | §6.2.4, pp.28–31 | 1993 新作物路径已证实 | `src/cteas_ufotri/crop/phenology.py` |
| `UF93-19` | Winter-wheat edible seed compartment | §6.2.5, pp.31–33 | 1993 新作物路径已证实 | `src/cteas_ufotri/crop/phenology.py` |
| `UF93-20` | Cow grazing and milking subdaily behavior | §5.6, pp.23–24 | 1993 详细公式待逐式复核 | `src/cteas_ufotri/foodchain/ufotri_cow_milk_beef_v4.py` |
| `UF93-21` | Inhalation and skin dose equation | §5.7, pp.24–25 | 机理/职责延续 | `src/cteas_ufotri/dose/ufotri_manual_v4.py` |
| `UF93-22` | Distinct HTO/OBT ingestion dose and five foods | §5.7;6.1, pp.25–26 | 1993 剂量处理修订已证实 | `src/cteas_ufotri/dose/public.py` |
| `UF93-23` | Per-food fresh-weight restriction option | §5.7, pp.25 | 1993 功能选项已证实 | `src/cteas_ufotri/dose/public.py` |
| `UF93-24` | 1993 FORTRAN input and default loader | §7.1–7.3;appendices, pp.34–91 | 1993 软件接口已证实 | `docs/v4/reports/ufotri_public_source_recovery_reassessment_r1.md` |

## 2. 1993 模型具有决定意义的已核实变化

### 2.1 OBT：光合作用控制是新标准，而不是仅按昼夜加权

- **1993 §5.5.1，正文 p.19–21，Eq.(26)–(31)**：用光合有效辐射（PAR）、叶面积指数与 CO₂ 净同化/呼吸构建实际光合生产率，并考虑植物环境胁迫。Eq.(26)–(27) 明确给出光合动力学与冠层 PAR 的衰减；其单位与中间转换需要正式翻录。
- **1993 §5.5.2，正文 p.22–23，Eq.(32)–(33)**：区分按作物发育与昼夜系数修正的简单分支，以及依据逐小时光合作用及植物氚分布系数调整的推荐分支。Eq.(32) 的 `fact2` 白天/夜间 **1.75/0.25**；Eq.(33) 所示植物分布系数 `dis` 历史默认 **0.5**。原文同时声明夜间 OBT 机理尚未完全建立，不能将经验系数视为已证实的夜间生理过程。
- **1990 KfK 4605 §2.2.6**：旧资料采用平均 OBT 形成速率（0.06%/h）及简单日夜区分的近似描述。当前 `plant/obt_ufotri_v4/` 的 `KFK4605` 兼容算法只能证明对应 1990 手册职责，**不能替代 1993 Eq.(26)–(33)**。

### 2.2 植物交换与蒸散发

- **1993 §5.2，p.4–6，Eq.(7)–(10)**：简单/扩展气孔阻力两种输入模式，扩展项包含物种、温度、PAR、湿度和土壤含水率。查阅代码中类似的阻力或 LAI 公式并不能自动证明与该模式一致。
- **1993 §5.3.1，p.7–8，Eq.(11)**：除 Penman 近似以外，报告推荐 **Monteith 阻力形式**，分别计算植被蒸腾和土壤蒸发。
- **待核对**：各物种经验系数、耐旱及雨天分支、导热/辐射单位与气孔阻力公式的原版参数卡片。

### 2.3 表层土壤、水分与再释放

- **1993 §5.3.2，p.9–10，Eq.(15)–(19)**：引入用于表面阻力计算的**约 1 cm 辅助土层（help layer）**，区别于已有的最上部 **0–5 cm** 土层；辅助层的含水率受降雨与土壤蒸发影响。p.10 明确指出该辅助层处理忽略基质力引起的水输运。
- **1993 §5.3.4，p.14–15，Eq.(21)–(24)**：提供简化排水与基于吸力/导水率的层间土壤水迁移两条分支。现有 `soil_ufotri_v4` 的 KfK4605 Darcy/Richards 接口依赖调用者提供本构表；**不等于** 1993 具体吸力—导水率关系的实现。
- **1993 §5.3.4，p.15–16，Eq.(25)**：再释放为蒸发驱动项与基础扩散项的组合；**1990 KfK 4605 Eq.(44)** 是不同版次的锚点。1993 的白天、夜间、雨天默认值需按原报告的输入选项核对，不能机械套用旧版 `DIFF`。
- **1993 §5.3.3，p.14，Eq.(20)**：HTO 降水清除率依赖降雨强度；文本给出幂律常数 `AW=9.0×10^-5`、`BW=0.6` 以及三雨强档位备选分支。常数单位和适用条件在写入程序前必须复核。

### 2.4 生长季、作物与长期 OBT

- **1993 §5.4，p.16–18，Table 1，Figs 8–10**：小麦、马铃薯的 LAI、生物量及含水量随发育阶段变化；报告提供作为德国案例假设的生长日序和收获时间。这些值不是全球固定物候数据。
- **1993 §6.2.2，p.27–28**：牧草有机库损失半期由 **10 天改为 15 天**；转移系数参照 Table 10。
- **1993 §6.2.3，p.28**：叶菜有机库损失半期由 **10 天改为 22 天**；转移系数参照 Table 9。
- **1993 §6.2.4–6.2.5，p.28–33，Figs 12–13**：马铃薯块茎、小麦籽粒分别设置 HTO/OBT 可食库；块茎分流系数 **5/6（茎叶）/1/6（块茎）** 在原文中属于初步假设，小麦籽粒与植物体水交换的半期取 **2 小时**。不得把当时的推定系数当成普适真值。

### 2.5 食入与剂量

- **1993 §5.7，p.24–25，Eq.(34)–(35)**：吸入/皮肤剂量与食入剂量分开处理；五类食品包括奶、肉、叶菜、马铃薯、谷物。对 HTO 和 OBT 各自配置剂量系数。
- **1990 KfK 4605 §4.1–4.3**：已独立记录 HTO/OBT 摄入，但按 HTO 剂量系数合并处理。本项是两版剂量策略的重要区别。
- **1993 §5.7 p.25**：按每种食品设置新鲜质量浓度的**历史软件食物限制阈值**，报告载有 `1250 Bq/kg` 默认值；它绝不是现代法规限值。当前 `dose/public.py` 有现代分开的 HTO/OBT 计算，不构成历史 UFOTRI 4.0 参数体系的独立证据。

## 3. 逐项版本证据与仓库状态（机器可读表为权威）

[physics_delta_matrix.yaml](physics_delta_matrix.yaml) 有 24 条独立记录，每条均包括：

`id / classification / reference_1993_section / reference_1993_printed_pages / reference_1993_pdf_page_indices / kfk5194_target_fact / reference_1990_section / kfk4605_comparison / repo_paths / repository_assessment / implementation_phase / next_source_audit`。

重要提示：条目 `repo_paths` 代表**需要核验的现有代码入口**，并不意味着与 UFOTRI 4.0 完全一致。`CONFIRMED_1993_*` 只代表 **1993 原始文献中的机制/修订可确认**，不是代码通过验收。

## 4. 未完成的 P0 原文审计及判定门槛

- [ ] 对 KfK 5194 的 **全部**正文/附录、Table 1 及 Table 9–12、NAMELIST 默认参数逐项补录；通过截图复核 PDF 文本提取不清晰的 Eq.(7)–(10)、Eq.(21)–(24)、Eq.(26)–(33)。
- [ ] 按 `1990 原公式/参数 → 1993 公式/参数 → 项目实现` 做**双向**源级审计，并借助 KfK 4853（1991）区分真正的新机制、继承机制及单纯文档修订。上表归类为“框架层面延续”并不证明数值计算未变。
- [ ] 检查 1993 全部模型开关、软件默认值与实际版本对应关系，尤其 `REMRE`、`REMNI`、`REDREM` 及水文/降雨/光合作用模式。
- [ ] 审阅官方原始公式和维度；凡未能复核的 OCR 或隐含本构参数保持 `SOURCE_REVIEW_REQUIRED`，不推测填充。
- [ ] 至少一次独立公式/单位复审；对每行标注 `confirmed / pending / source-limited` 并将审计证据归档。
- [ ] 仅在这些要求闭环时关闭 [Issue #126](https://github.com/RRain001/cufotri/issues/126)。P1–P7 不应因本首轮表格存在而提前声称对应物理过程已实现。

## 5. 软件与科学验收边界

**此次仅更新文档与证据索引，不修改任何现有物理程序、默认参数、浓度单位、食入系数或科研测试的数值门槛。**

- `KFK4605_1990`：已冻结的原有手册重建路径不被替换。
- `KFK5194_1993_V4`：这是目标物理版本的**规划与初步证据表**，不是当前运行时已提供的选项。
- `UFOTRI_1993_ORIGINAL_EXECUTABLE_NUMERIC_EQUIVALENCE=NOT_ESTABLISHED`。
- `UFOTRI_1993_EMPIRICAL_VALIDATION=NOT_ESTABLISHED`；外部验证输入仍属于独立 [Issue #119](https://github.com/RRain001/cufotri/issues/119)。

遵循 [STATUS.md](../../../STATUS.md) 与 [原版源资料恢复记录](../reports/ufotri_public_source_recovery_reassessment_r1.md) 的保守声明。任何后续实现需先通过 P0 原文条目的独立复核。


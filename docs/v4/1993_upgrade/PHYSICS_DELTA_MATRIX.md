# UFOTRI **4.0（1993）** 物理过程差异矩阵 — KfK 5194

> **版本确认（重要）：此文件审计的目标版本是 W. Raskob 于 1993 年 8 月出版的《Description of the New Version 4.0 of the Tritium Model UFOTRI Including User Guide》，报告编号 KfK 5194。它不是 1990 年 KfK 4605 的公式清单，也不是“CUFOTRI 软件 V4 版本”的完成证明。1990 年 KfK 4605 只作为旧物理基线用于逐项比较。**

**文档身份**：`UFOTRI_4_0_1993` / `KfK 5194` / 1993-08；原报告 PDF 102 页，含正文印刷页与附录；[KIT 官方全文](https://publikationen.bibliothek.kit.edu/270034158/3813483)，[DOI](https://doi.org/10.5445/IR/270034158)。对照文献：W. Raskob，**KfK 4605（1990）**，[KIT 官方全文](https://publikationen.bibliothek.kit.edu/270029395/3813413)。必要时参考 1991 年 KfK 4853 用户指南，以区分从 1990 到 1991 已有的机制与真正的 1993 更新。

**审计状态（R2 更新后仍未闭环）**：`PARTIAL_SOURCE_ANCHORED_AUDIT_IN_PROGRESS`。已对 KfK 5194 的关键章节、方程位置和主要数值进行了原文核查；尚未完成 1993 全部输入卡片/附录默认值与 1990 所有公式的双向逐式复核，更未证明现有程序等价于 1993 UFOTRI 4.0 可执行文件。

**判读原则**：
- 所有“1993 应如何计算”的规范性问题，以 **KfK 5194** 的印刷页、方程、表格、选项为第一依据。KfK 4605 的方程只用于历史比较；**1990 Eq.(33) 与 1993 Eq.(33) 不是同一个公式**。
- “1993 报告记载”与“1990→1993 已确认发生改变”是两种证据强度。1993 中已有的能力，不因再次出现而自动归类为新增。
- “代码存在同名/类似模块”不表示原版 1993 方程和默认值已恢复。`UNVERIFIED` 不得解释成不存在。
- 来源为官方 PDF/手册，不把原始 PDF 复制到公开仓库；若源式图形扫描或 OCR 失真，以印刷页核对结果为准。
- 保持已冻结 **KFK4605_1990** 默认数值行为。未来每项 **KFK5194_1993_V4** 兼容性实现都必须为可选路径；除非另有独立验收，不得重写现有基线或科学容差。

## 1. 1993 原始文献证据清单（初步）

1993 KfK 5194 第 5—6 章明确覆盖植物交换、土壤—大气交换、土壤水、作物发育、光合作用与 OBT、食物链和剂量。下面按报告印刷页列出 **1993 目标规范**；对应的 1990 比较依据取自 KfK 4605 的不同章节。

| ID / 过程 | 1990 KfK 4605 对照 | **1993 KfK 5194 目标** | 1993 原文定位 | 状态 / 阶段 |
|---|---|---|---|---|
| `UF93-01` MUSEMET primary atmospheric trajectory | MUSEMET trajectory plus secondary area-source concept already present. (§2.1) | Gaussian trajectory and primary HT/HTO plume retained; original executable numerics not recovered. | §5.1 p.2–3 (PDF0 p.11–12) | UNCHANGED_AT_ARCHITECTURE_LEVEL / [issue #133](https://github.com/RRain001/cufotri/issues/133) |
| `UF93-02` Secondary re-emission plume source | 1990 described Gaussian re-emission area source. (§2.2.1) | Secondary Gaussian area-source plume approximated by centre point with initial plume broadening. | §5.1 p.3 (PDF0 p.12) | 1993_FORMULATION_CHECK_REQUIRED / [issue #130](https://github.com/RRain001/cufotri/issues/130) |
| `UF93-03` Stomatal and canopy resistance options | 1990 leaf resistance Eq.(7)–(31) includes day/night and atmospheric terms but does not alone certify 1993 extended mode. (§2.2.2) | KfK5194 §5.2 Eq.(4)-(10): extended stoma includes (1+c/I_p)/(f_l f_w f_t) with humidity, soil water and temperature factors; Eq.(10) canopy r_c=r_st/LAI; no inferred 1990 structural difference without exact old-version formula. | §5.2 p.4–6 (PDF0 p.13–15) | 1993_FORMULA_VERIFIED_1990_DELTA_PENDING / [issue #129](https://github.com/RRain001/cufotri/issues/129) |
| `UF93-04` Stability and aerodynamic/boundary resistance | 1990 includes resistance analogy and wind-profile terms, but exact branch comparison not yet audited. (§2.2.2) | 1993 uses logarithmic wind-profile/Dyer–Businger relations with aerodynamic and boundary resistance Eq.(4)–(6). | §5.2 p.4–5 (PDF0 p.13–14) | 1993_FORMULATION_CHECK_REQUIRED / [issue #129](https://github.com/RRain001/cufotri/issues/129) |
| `UF93-05` HT dry deposition and microbial soil conversion | 1990 includes HT→HTO soil oxidation and HTO/HT deposition. (§2.2.3) | HT diffusivity and time-dependent deposition Eq.(12)–(13); microbial conversion and winter reduction; HTO constant or resistance-driven dry-deposition Eq.(14). | §5.3.2 p.8–9 (PDF0 p.17–18) | 1993_FORMULATION_CHECK_REQUIRED / [issue #130](https://github.com/RRain001/cufotri/issues/130) |
| `UF93-06` Monteith vs Penman evapotranspiration | 1990 ET treatment uses Penman-style Eq.(38)–(43) and water/HTO balances. (§2.2.3) | KfK5194 §5.3.1 Eq.(11) Monteith bulk-resistance ET, with Penman alternative; canopy/soil radiation split uses exp(-0.398*LAI). IMONT 1=Monteith, 0=Penman, documented default 1. | §5.3.1 p.7–8 (PDF0 p.16–17) | CONFIRMED_1993_EXTENSION / [issue #129](https://github.com/RRain001/cufotri/issues/129) |
| `UF93-07` Thin top-soil help layer and soil surface resistance | 1990 hydraulic discussion lacks confirmed same dedicated 1-cm soil-resistance help-layer contract. (§2.2.3) | KfK5194 §5.3.2 Eq.(15)-(19): extra approx 1 cm help layer is used for soil resistance only; z=z0/phi_h with z0=0.004 m while phi_h stated as mm water and limited to numerical 0.5-5; dimensional convention needs explicit review; RSOIL=150, RSSMIN=50 s/m. | §5.3.2 p.9–10 (PDF0 p.18–19) | CONFIRMED_1993_EXTENSION / [issue #130](https://github.com/RRain001/cufotri/issues/130) |
| `UF93-08` HTO whole-plume wet washout | 1990 already modeled HTO whole-plume washout; historical classification/options may differ. (§2.2.3) | KfK5194 §5.3.3 Eq.(20) lambda_HTO=AW*I^BW; I in mm/h; documented AW=9e-5, BW=0.6; second mode precipitation classes <1, 1-3, >3 mm/h. 1993 IWASH mode/default per NAMELIST must be reviewed before implementation. | §5.3.3 p.14 (PDF0 p.23) | 1993_FORMULATION_CHECK_REQUIRED / [issue #130](https://github.com/RRain001/cufotri/issues/130) |
| `UF93-09` Soil suction, conductivity and layered water transport | 1990 Eq.(33)–(37) develops Darcy/Richards transport but original executable constitutive coefficients are not in repo. (§2.2.3) | KfK5194 §5.3.4 Eq.(21)-(24): S=1.5e5*Psi^(a+b*Psi+c*Psi^n), Psi=(theta_s-theta)/(theta_s-theta_w), K=alpha_q/(S^m+beta), V_ab=K_ab*((S_a-S_b)/avg_layer_thickness-1). ORIGINAL PRINT declares K as mm/day yet V_ab as mm/hour; do not silently choose conversion. | §5.3.4 p.14–15 (PDF0 p.23–24) | 1993_FORMULA_VERIFIED_1990_DELTA_PENDING / [issue #130](https://github.com/RRain001/cufotri/issues/130) |
| `UF93-10` Root uptake depth and layer weights | 1990 also provides nutrient/pasture-specific root profile concept. (§2.2.5;3.3;3.4) | Agricultural crop roots use 20/40/40% and grass 40/60/0% over 0–5,5–15,15–30 cm. | §5.3.4 p.15–16 (PDF0 p.24–25) | UNCHANGED_AT_DOCUMENTED_ROLE_LEVEL / [issue #130](https://github.com/RRain001/cufotri/issues/130) |
| `UF93-11` Soil HTO re-emission daytime and night branches | 1990 KfK4605 Eq.(44) REEM=(E_as/BODWA)*(1-ABFLR)*C1*C2*ZT; followed by REEMG=REEM+DIFF*ZT. Source formula difference is not just renumbering. (§2.2.4) | 1993 KfK5194 Eq.(25) REEM=(E_as/BODWA)*C1*C2*ZT+REB*ZT; printed equation omits (1-ABFLR) factor explicitly present in 1990 KfK4605 Eq.(44). Both versions have a basic diffusion/night contribution; not simply a new term in 1993. | §5.3.4 p.15–16 (PDF0 p.24–25) | CONFIRMED_1993_MODIFIED_FORMULATION / [issue #130](https://github.com/RRain001/cufotri/issues/130) |
| `UF93-12` Crop stage, LAI and plant mass evolution | 1990 has simpler vegetables and grass transfer compartments without these explicit crop profiles. (§3.3;3.4) | Wheat/potato LAI, plant water and dry matter stage curves; model growth starts DOY110/140, harvest DOY225/258; Table 1 and Figs 8–10. | §5.4 p.16–18 (PDF0 p.25–27) | CONFIRMED_1993_EXTENSION / [issue #131](https://github.com/RRain001/cufotri/issues/131) |
| `UF93-13` Photosynthesis-driven net CO2 assimilation | 1990 OBT uptake modeled by average first-order transfer with simple daytime/nighttime split. (§2.2.6) | KfK5194 §5.5.1 Eq.(26)-(31) describes potential CO2 assimilation, PAR attenuation with k=0.6, canopy integration, respiration and stress; in Eq.(26) P_m means maximum CO2 assimilation, distinct from Eq.(33) P_m (mean hourly dry matter production). | §5.5.1 p.19–21 (PDF0 p.28–30) | CONFIRMED_1993_NEW_MECHANISM / [issue #128](https://github.com/RRain001/cufotri/issues/128) |
| `UF93-14` OBT formation alternative modes | 1990 used average OBT formation and nighttime/daytime modulation. (§2.2.6;3.3.3) | KfK5194 §5.5.2 Eq.(32) T_act=T_m*fact1*fact2; Eq.(33) advanced T_act=(P_act/P_m)*T_m*fact2*dis, dis default 0.5. Eq.(33) P_m is mean hourly dry-matter production, NOT Eq.(26) maximum CO2 assimilation. IPHOTO 1=advanced, documented default 1. | §5.5.2 p.21–23 (PDF0 p.30–32) | CONFIRMED_1993_EXTENSION / [issue #128](https://github.com/RRain001/cufotri/issues/128) |
| `UF93-15` Diurnal factor in 1993 simple and advanced OBT paths | 1990 stated increased day and reduced night without an unambiguous normalized 1.75/0.25 pair. (§2.2.6) | KfK5194 §5.5.2 Eq.(32)-(33) fact2=1.75 day and 0.25 night; original states nighttime processes are not physically resolved. Treat factors as historical modeling assumptions rather than mechanistic nighttime photosynthesis. | §5.5.2 p.22–23 (PDF0 p.31–32) | CONFIRMED_1993_DOCUMENTED_VALUES / [issue #128](https://github.com/RRain001/cufotri/issues/128) |
| `UF93-16` Grass organic-compartment OBT half-time | 1990 pasture organic loss half-time stated as about 10 days. (§3.4;3.5) | Grass organic compartment loss half-time changed explicitly 10 days → 15 days; companion exchange coefficients must be derived from Table 10. | §6.2.2 p.27–28 (PDF0 p.36–37) | CONFIRMED_1993_CHANGED_PARAMETER / [issue #128](https://github.com/RRain001/cufotri/issues/128) |
| `UF93-17` Leafy vegetable organic-compartment OBT half-time | 1990 vegetable OBT loss half-time is about 10 days (Eq.65 context). (§3.3.3) | Leafy vegetable organic half-time 10 days → 22 days (45-day growing period); both directions of transfer rates modified; Table 9. | §6.2.3 p.28 (PDF0 p.37) | CONFIRMED_1993_CHANGED_PARAMETER / [issue #128](https://github.com/RRain001/cufotri/issues/128) |
| `UF93-18` Potato edible tuber compartment | 1990 diet model lacks the corresponding distinct potato tuber model documented for 1993. (§3.3.3) | Potato plant-body/tuber HTO and OBT split (Fig.12); documented root 5/6 vs tuber 1/6 assumption, tuber organic sink Eq.(45). | §6.2.4 p.28–31 (PDF0 p.37–40) | CONFIRMED_1993_NEW_CROP_PATH / [issue #131](https://github.com/RRain001/cufotri/issues/131) |
| `UF93-19` Winter-wheat edible seed compartment | 1990 has general vegetable and forage chain without explicit 1993 seed transfer submodel. (§3.3.3) | Separate seed HTO/OBT pools (Fig.13), plant-seed water transfer half-time 2 hours and rate Eq.(46)–(48). | §6.2.5 p.31–33 (PDF0 p.40–42) | CONFIRMED_1993_NEW_CROP_PATH / [issue #131](https://github.com/RRain001/cufotri/issues/131) |
| `UF93-20` Cow grazing and milking subdaily behavior | Similar subdaily grazing/milking roles already described in 1990. (§2.2.7;3.5) | Cow eats grass during daytime; two discrete milkings per day; daily transfer rates adapted hourly. | §5.6 p.23–24 (PDF0 p.32–33) | 1993_FORMULATION_CHECK_REQUIRED / [issue #132](https://github.com/RRain001/cufotri/issues/132) |
| `UF93-21` Inhalation and skin dose equation | 1990 includes inhalation and skin exposure (Eq.106), but numeric coefficient/version remains separate. (§4.2) | Eq.(34): breathing plus skin equivalent intake × dose factor × integrated concentration. | §5.7 p.24–25 (PDF0 p.33–34) | UNCHANGED_AT_DOCUMENTED_ROLE_LEVEL / [issue #132](https://github.com/RRain001/cufotri/issues/132) |
| `UF93-22` Distinct HTO/OBT ingestion dose and five foods | 1990 tracked plant/cow HTO and OBT separately but treated ingested OBT with HTO dose coefficient. (§4.1;4.3) | Eq.(35) distinguishes chemical form for milk, meat, vegetables, potatoes and grain, with separate dose conversion factors. | §5.7;6.1 p.25–26 (PDF0 p.34–35) | CONFIRMED_1993_CHANGED_DOSE_POLICY / [issue #132](https://github.com/RRain001/cufotri/issues/132) |
| `UF93-23` Per-food fresh-weight restriction option | 1990 manual dose path lacks an equally evidenced 1993 per-food restriction interface. (§4.3) | Optional food restriction submodel; user-selectable per-food threshold, historical default 1250 Bq/kg fresh mass. | §5.7 p.25 (PDF0 p.34) | CONFIRMED_1993_DOCUMENTED_OPTION / [issue #132](https://github.com/RRain001/cufotri/issues/132) |
| `UF93-24` 1993 FORTRAN input and default loader | Existing recovery audit documents 1991/1993 loader lineage; original FORTRAN members unavailable. (§1991 user guide KfK4853) | KfK5194 §7.4.2, pp.54-55: IMODEL, ICOVER, IPHOTO, IMONT, IFLAGS, IFLAGR, IDEPHT and IBODEX have printed default=1; §7.4.4 p.61 gives soil parameters/REMRE/REMNI/REDREM defaults. This is documented input contract, NOT evidence of original loader binary behavior. | §7.1–7.3;appendices p.34–91 (PDF0 p.43–100) | CONFIRMED_1993_INTERFACE_DOCUMENTED / [issue #127](https://github.com/RRain001/cufotri/issues/127) |

## 1.1 原始 PDF 视觉复核 R2 — 逐式核对与风险校正

已新增 [**KfK 5194 1993 原始公式/参数审计 R2**](PRIMARY_SOURCE_AUDIT_R2.md) 和 [机器可读主证据表](primary_source_formula_audit_r2.yaml)。R2 对 **22 项选定公式**进行了原始印刷页复核；21 项历史软件默认值中 19 项经页面图像核查、2 项（`IDEPHT`、`IBODEX`）仍待图像复核，并记录 4 类关键不确定性，其中：

- §5.2 Eq.(4)–(10)：气孔/冠层阻力、温湿度与 PAR 因子。
- §5.3.1–5.3.4 Eq.(11)、(15)–(25)：Monteith 蒸散发、辅助土层、导水率、水通量和再释放。
- §5.5.1–5.5.2 Eq.(26)–(33) 的选定公式：光合作用—OBT 形成，以及 `P_m` 在 Eq.(26)/(33) **同名异义**。
- §7.4.2 与 §7.4.4：`IMODEL/ICOVER/IPHOTO/IMONT/IFLAGS/IFLAGR/IDEPHT/IBODEX` 等历史默认值；不代表现有 CUFOTRI 运行配置。
- **源文单位待解释**：1993 Eq.(23) 导水率 K=mm/day、Eq.(24) 层间通量 V=mm/hour；**不要未经验证直接引入换算**。
- **两版打印公式差异**：1990 Eq.(44) 的 `(1-ABFLR)` 项未出现在 1993 Eq.(25) 的蒸发项中；两版均有基础扩散项。具体源程序执行差异仍未证实。

当前 UF93-03、UF93-09 已降级为 `1993_FORMULA_VERIFIED_1990_DELTA_PENDING`：核实 1993 公式存在，**尚不足以认定相较 1990 必然新增**。所有 24 行均记录 `independent_scientific_review=NOT_COMPLETED`。P0 仍保持 Open，不授权物理代码升级。

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
- **1993 §5.3.4，p.14–15，Eq.(21)–(24)**：原文给出具体吸力、归一化水分和导水率闭合关系。但 **Eq.(23) 的 K 为 mm/day，Eq.(24) 的 V_ab 为 mm/hour**，单位之间存在尚未解释的差异；当前 KfK4605 Darcy/Richards 接口不能被宣称为已恢复 1993 关系。
- **1993 §5.3.4，p.15，Eq.(25)**：公式为蒸发项加 `REB×ZT`；与 1990 KfK 4605 Eq.(44) 对照，1993 打印式**未出现 `(1−ABFLR)`**，但旧版同样已经包含基本扩散项。`REMRE=0.3%/h`、`REMNI=1%/h`、`REDREM=1.0` 是 1993 §7.4.4 印刷的历史默认值，原版算法如何使用这些输入仍待复核。
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

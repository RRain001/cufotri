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
| `UF93-03` Stomatal and canopy resistance options | 1990 leaf resistance Eq.(7)–(31) includes day/night and atmospheric terms but does not alone certify 1993 extended mode. (§2.2.2) | KfK5194 §5.2 Eq.(4)-(10), with extended stomatal mode already documented in KfK4853 (1991) §2.1: extended stoma includes (1+c/I_p)/(f_l f_w f_t) with humidity, soil water and temperature factors; Eq.(10) canopy r_c=r_st/LAI; no inferred 1990 structural difference without exact old-version formula. | §5.2 p.4–6 (PDF0 p.13–15) | 1993_FORMULA_VERIFIED_1990_DELTA_PENDING / [issue #129](https://github.com/RRain001/cufotri/issues/129) |
| `UF93-04` Stability and aerodynamic/boundary resistance | 1990 includes resistance analogy and wind-profile terms, but exact branch comparison not yet audited. (§2.2.2) | 1993 uses logarithmic wind-profile/Dyer–Businger relations with aerodynamic and boundary resistance Eq.(4)–(6). | §5.2 p.4–5 (PDF0 p.13–14) | 1993_FORMULATION_CHECK_REQUIRED / [issue #129](https://github.com/RRain001/cufotri/issues/129) |
| `UF93-05` HT dry deposition and microbial soil conversion | 1990 includes HT→HTO soil oxidation and HTO/HT deposition. (§2.2.3) | HT diffusivity and time-dependent deposition Eq.(12)–(13); microbial conversion and winter reduction; HTO constant or resistance-driven dry-deposition Eq.(14). | §5.3.2 p.8–9 (PDF0 p.17–18) | 1993_FORMULATION_CHECK_REQUIRED / [issue #130](https://github.com/RRain001/cufotri/issues/130) |
| `UF93-06` Monteith vs Penman evapotranspiration | 1990 ET treatment uses Penman-style Eq.(38)–(43) and water/HTO balances. (§2.2.3) | KfK5194 §5.3.1 Eq.(11) Monteith bulk-resistance ET, with Penman alternative; canopy/soil radiation split uses exp(-0.398*LAI). IMONT 1=Monteith, 0=Penman, documented default 1. | §5.3.1 p.7–8 (PDF0 p.16–17) | CONFIRMED_1993_EXTENSION / [issue #129](https://github.com/RRain001/cufotri/issues/129) |
| `UF93-07` Thin top-soil help layer and soil surface resistance | 1990 hydraulic discussion lacks confirmed same dedicated 1-cm soil-resistance help-layer contract. (§2.2.3) | KfK5194 §5.3.2 Eq.(15)-(19): extra approx 1 cm help layer is used for soil resistance only; z=z0/phi_h with z0=0.004 m while phi_h stated as mm water and limited to numerical 0.5-5; dimensional convention needs explicit review; RSOIL=150, RSSMIN=50 s/m. | §5.3.2 p.9–10 (PDF0 p.18–19) | CONFIRMED_1993_EXTENSION / [issue #130](https://github.com/RRain001/cufotri/issues/130) |
| `UF93-08` HTO whole-plume wet washout | KfK4605 1990 already handles wet washout, but old program mode/default parity remains pending (§2.2.3). | KfK5194 **§7.3.3 pp.46–47**: **IWASH=0 is DEFAULT**, using rainfall classes split at 1/3 mm/h, HTO washout 6e-5/1e-4/4e-4 s^-1 and precipitation-duration fractions 0.50/0.75/0.72. **IWASH=1 OPTIONAL** uses §5.3.3 Eq.(20) power law (AWASH_HTO=9e-5, BWASH_HTO=0.6). HT default washout 0. | §§5.3.3, 7.3.3, printed pp.14,46–47 (PDF0 23,55–56) | 1993_DOCUMENTED_WASHOUT_MODES_DEFAULT_BRANCH_VERIFIED / [issue #130](https://github.com/RRain001/cufotri/issues/130) |
| `UF93-09` Soil suction, conductivity and layered water transport | 1990 Eq.(33)–(37) develops Darcy/Richards transport but original executable constitutive coefficients are not in repo. (§2.2.3) | KfK5194 §5.3.4 Eq.(21)-(24), with suction–conductivity forms already documented in KfK4853 (1991) §3.4.3: S=1.5e5*Psi^(a+b*Psi+c*Psi^n), Psi=(theta_s-theta)/(theta_s-theta_w), K=alpha_q/(S^m+beta), V_ab=K_ab*((S_a-S_b)/avg_layer_thickness-1). ORIGINAL PRINT declares K as mm/day yet V_ab as mm/hour; do not silently choose conversion. | §5.3.4 p.14–15 (PDF0 p.23–24) | 1993_FORMULA_VERIFIED_1990_DELTA_PENDING / [issue #130](https://github.com/RRain001/cufotri/issues/130) |
| `UF93-10` Root uptake depth and layer weights | 1990 also provides nutrient/pasture-specific root profile concept. (§2.2.5;3.3;3.4) | Agricultural crop roots use 20/40/40% and grass 40/60/0% over 0–5,5–15,15–30 cm. | §5.3.4 p.15–16 (PDF0 p.24–25) | UNCHANGED_AT_DOCUMENTED_ROLE_LEVEL / [issue #130](https://github.com/RRain001/cufotri/issues/130) |
| `UF93-11` Soil HTO re-emission daytime and night branches | 1990 KfK4605 Eq.(44) REEM=(E_as/BODWA)*(1-ABFLR)*C1*C2*ZT; followed by REEMG=REEM+DIFF*ZT. Source formula difference is not just renumbering. (§2.2.4) | 1993 KfK5194 Eq.(25) (E_as kg m^-2 h^-1, versus 1990 kg m^-2 s^-1) REEM=(E_as/BODWA)*C1*C2*ZT+REB*ZT; printed equation omits (1-ABFLR) factor explicitly present in 1990 KfK4605 Eq.(44). Both versions have a basic diffusion/night contribution; not simply a new term in 1993. | §5.3.4 p.15–16 (PDF0 p.24–25) | CONFIRMED_1993_MODIFIED_FORMULATION / [issue #130](https://github.com/RRain001/cufotri/issues/130) |
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
| `UF93-22` Distinct HTO/OBT ingestion dose and five foods | 1990 KfK4605 formula comparison remains open (§4.1;4.3); **1991 KfK4853 §3.4.6 already has separate OBT DOSFOB=4.5e-11 Sv/Bq**. | 1993 Eq.(35) treats five foods; **DOSFOB=4.0e-11 Sv/Bq** in §7.4.8. This is a confirmed 1991→1993 *default change*, not proof that distinct OBT coefficients first appeared in 1993. | §5.7;6.1 p.25–26 (PDF0 p.34–35), §7.4.8 p.65 | 1993_DOSFOB_DEFAULT_CHANGED_VS_1991_1990_PHYSICS_REVIEW_PENDING / [issue #132](https://github.com/RRain001/cufotri/issues/132) |
| `UF93-23` Per-food fresh-weight restriction option | 1990 manual dose path lacks an equally evidenced 1993 per-food restriction interface. (§4.3) | Optional food restriction submodel; user-selectable per-food threshold, historical default 1250 Bq/kg fresh mass. | §5.7 p.25 (PDF0 p.34) | CONFIRMED_1993_DOCUMENTED_OPTION / [issue #132](https://github.com/RRain001/cufotri/issues/132) |
| `UF93-24` 1993 FORTRAN input and default loader | Existing recovery audit documents 1991/1993 loader lineage; original FORTRAN members unavailable. (§1991 user guide KfK4853) | KfK5194 §7.4.2, pp.54-55: IMODEL, ICOVER, IPHOTO, IMONT, IFLAGS, IFLAGR, IDEPHT and IBODEX have printed default=1; §7.4.4 p.61 gives soil parameters/REMRE/REMNI/REDREM defaults. This is documented input contract, NOT evidence of original loader binary behavior. | §7.1–7.3;appendices p.34–91 (PDF0 p.43–100) | CONFIRMED_1993_INTERFACE_DOCUMENTED / [issue #127](https://github.com/RRain001/cufotri/issues/127) |

### UF93-13：P2 R9 源文裁决门禁（未解除）

已将 KfK5194 §5.5.1 **印刷 p.20 / PDF0 p.29** 的 Eq.(28)–(30) 未决问题与禁止接入条件同步至 `physics_delta_matrix.yaml` 的 `UF93-13.p2_r9_source_gate`。印刷 Eq.(28) 与直接积分 Eq.(26)–(27) 存在 **分母额外 k、呼吸项缺少 LAI** 两处差异；Eq.(29) 的 `CO` 印刷单位为 mg CO₂ m⁻² h⁻¹，而 Eq.(26) 的 `P_m` 为 g CO₂ m⁻² h⁻¹；Eq.(30) 的 `W` 是 CO₂ 当量而非可直接复用的干物质量。原版求解顺序、面积基准和单位桥接均未获得独立证据。

[**P2 R9 科学裁决材料与逐项证据要求**](P2_R9_SOURCE_ADJUDICATION_GATE.md) 明确哪些是已核对的印刷事实、哪些只是 R8 条件性数学试验。**1990 默认路径不变；1993 正式耦合、原版等价和独立科学签核仍为 NOT_ESTABLISHED/NOT_RUN。**

### UF93-13：P2 R10 引用文献元数据与摘要审计（仍未解除）

[**Weir (1984) 与 Mitchell (1991) 出版社证据审计**](P2_R10_WEIR_MITCHELL_BIBLIOGRAPHY_AUDIT.md) 已核对 /39/ 和 /21/ 的 DOI、作者、期刊卷页与出版社公开摘要，并在 `UF93-13.p2_r10_bibliography_evidence` 固定证据级别为 `PUBLISHER_METADATA_AND_ABSTRACT_ONLY`。Weir 的作物模拟及 Mitchell 的干质量归一化呼吸研究并不能单独确定 Eq.(29) 经验常数的 mg→g 桥接，也不能确定 Eq.(30) 的面积/CO₂ 当量基准。两篇全文的原始公式审阅仍 `NOT_RUN`，所有 R9 科学门禁维持原状。

### UF93-13：P2 R11 Weir (1984) 原文公式与量纲审计（仍未解除）

[**Weir (1984) 原文 Eq.(19)–(26) 审计**](P2_R11_WEIR_1984_PRIMARY_EQUATION_AUDIT.md) 现已核查 Rothamsted Research 全文印刷 pp.374–375、对应 PDF 页 5–6，并固定 PDF SHA256。Weir Eq.(20) `P_max` 的原始单位为 mg CO₂ m⁻² s⁻¹，CO₂ 浓度为 mg m⁻³，总阻力为 s m⁻¹；Eq.(25) 的每日呼吸采用 g m⁻² day⁻¹。来源事实记录在 `UF93-13.p2_r11_weir_primary_equation_evidence`，而 **KfK5194 Eq.(29) 的 0.158 × 10⁹ 经验因子、每小时单位桥接及冠层面积基准仍 NOT_ESTABLISHED**。Mitchell (1991) 原始方程审阅和独立科学审查仍 NOT_RUN；未修改正式物理求解器及 1990 默认路径。

### UF93-13：P2 R12 Mitchell 原文定位与阻塞

[**R12 存档及 Eq.(30) 量纲举证审计**](P2_R12_MITCHELL_ARCHIVE_AND_EQ30_PROOF_OBLIGATIONS.md) 核验了机构存档与 OpenAlex 文献记录。原始 PDF 返回 HTTP 401，未取得正文，不存在 PDF SHA256 或公式验证。R12 记录了 CO2 当量与干物质、叶面积与地表面积的必要换算证据，所有实际换算因子和原版等价性仍为 NOT_ESTABLISHED。1990 默认路径不变，正式科学审查 NOT_RUN。

### UF93-13：P2 R13 Eq.(28) 正负偏差、渐近界与呼吸面积判别

[**R13 Eq.(28) 独立数学判别**](P2_R13_EQ28_BIAS_SIGN_AND_LIMIT_AUDIT.md) 已按 KfK5194 原始印刷 pp.19–20 再次视觉核验，在 `0<k<1`、PAR>0 的共同量纲假设下独立证明印刷 Eq.(28) 的**光合部分**比 Eq.(26)–(27) 直接积分严格偏高，偏差 `D=(Pm/k)ln[(Pm+eps*Iabs)/(Pm+eps*k*Iabs)]`，上界 `(Pm/k)ln(1/k)`。但**净同化差**为 `D+(LAI-1)Rd`：当 LAI<1 时可因呼吸基准与大小翻转，不得概括为净同化一律偏高。上述判别是条件性数学结论，**不是原版 FORTRAN 算法等价、Eq.(28) 自动修正或科学审查通过**。机器审计见 `UF93-13.p2_r13_eq28_bias_sign_limit_audit`；1990 默认路径保持冻结。

## 1.1 原始 PDF 视觉复核 R2 — 逐式核对与风险校正

已新增 [**KfK 5194 1993 原始公式/参数审计 R2**](PRIMARY_SOURCE_AUDIT_R2.md) 和 [机器可读主证据表](primary_source_formula_audit_r2.yaml)。R2 对 **22 项选定公式**进行了原始印刷页复核；21 项历史软件默认值现均已核对官方 PDF 印刷页（包括 `IDEPHT`、`IBODEX`），并记录 4 类关键不确定性，其中：

- §5.2 Eq.(4)–(10)：气孔/冠层阻力、温湿度与 PAR 因子。
- §5.3.1–5.3.4 Eq.(11)、(15)–(25)：Monteith 蒸散发、辅助土层、导水率、水通量和再释放。
- §5.5.1–5.5.2 Eq.(26)–(33) 的选定公式：光合作用—OBT 形成，以及 `P_m` 在 Eq.(26)/(33) **同名异义**。
- §7.4.2 与 §7.4.4：`IMODEL/ICOVER/IPHOTO/IMONT/IFLAGS/IFLAGR/IDEPHT/IBODEX` 等历史默认值；不代表现有 CUFOTRI 运行配置。
- **源文单位待解释**：1993 Eq.(23) 导水率 K=mm/day、Eq.(24) 层间通量 V=mm/hour；**不要未经验证直接引入换算**。
- **两版打印公式差异**：1990 Eq.(44) 的 `(1-ABFLR)` 项未出现在 1993 Eq.(25) 的蒸发项中；两版均有基础扩散项。具体源程序执行差异仍未证实。

当前 UF93-03、UF93-09 已降级为 `1993_FORMULA_VERIFIED_1990_DELTA_PENDING`：核实 1993 公式存在，**尚不足以认定相较 1990 必然新增**。所有 24 行均记录 `independent_scientific_review=NOT_COMPLETED`。P0 仍保持 Open，不授权物理代码升级。

## 1.2 1993 原版 Table 1 / 9–12 与 NAMELIST 审计 R3

[原始表格审计说明](PRIMARY_SOURCE_TABLE_AUDIT_R3.md) · [原始物质质量与 80 条 COMA 转移率](primary_source_transfer_tables_r3.yaml) · [1993 历史土壤及食入参数](primary_source_input_defaults_r3.yaml)。

- **1993 目标版本明确**：Table 1 的叶菜、草、马铃薯和冬小麦植物/可食部分水质量与干质量已据 KfK 5194 印刷 p.17（PDF 零基 26）复录；所有有印数值满足总质量=干物质量+水质量。缺失的可食列绝不解释为零。
- **四张 COMA 长期食入表**：Table 9/10/11/12 实际印刷页为 p.86/87/88/89（PDF 零基 95–98），逐格复录 **15 + 26 + 21 + 18 = 80** 条 `d^-1` 转移率。这些不是短期逐小时 OBT/叶面速率。
- **草 OBT 半期算术交叉核查**：Table 10 的草 OBT→草 HTO（0.024/d）、牛 HTO（0.018/d）、牛 OBT（0.0029/d）、牛奶 OBT（0.0015/d），四边总移出率 **0.0464/d**，孤立库半期 **14.94 天**；若错误地只用草 OBT→草 HTO 单边，半期约 **28.9 天**。Table 9 叶菜 OBT→叶菜 HTO 的 **0.032/d** 对应 **21.66 天**。这些只是表格内部一致性核查，不代表全食物网特征衰减率或原程序输出。
- **原文排版疑点必须保留**：Table 9/10/11 的部分自回路符号实际指向外部；Table 12（小麦）的首个大气→植物路径却印作 `potato HTO`，还复用马铃薯类 `tp*` 下标。YAML 同时保留印刷库名和印刷符号，P5/P6 禁止未审校就将符号作为邻接矩阵自动生成依据。表目录所列页码也与 PDF 实际印刷页不一致。
- **1993 特定输入分支**：§7.4.4 的 `IBODFX=0`、`BODEIN=0.2`、`SOILMX=0.5`、`WILTP=0.1`、`IARTBO=1` 需要与 P4 的土壤配置分支区分；`IARTBO=4` 为用户自定义七参数，不得把同一组参数无条件套用全部预置土类型。
- **食物限制历史语义**：§7.4.5–7.4.6 的 `FAKC1/2/FAKCP/FAKCW` 合计为 1，`COGRF(5)` 历史默认 5×1250 Bq/kg 鲜重，`TIMEDO(12)` 使用含重复记号的印刷默认输入；有效剂量主记录**不会由限制模块覆盖**，仅在 `IBANWR=1` 时另存限制后结果。该值不是现代监管限值。

**范围限制**：R3 仍未完成 Table 2–8、剩余参数组、1990/1991 原手册的完整逐项比对及独立源校对，不关闭 P0，不改任何现有数值参数和物理求解器。

## 1.3 R4：软件结构、三版默认值和 1993 Table 1 单位校订

新增 [**KfK5194 Table 2–8 与 1991→1993 用户手册差异审计 R4**](PRIMARY_SOURCE_SOFTWARE_AND_CROSSEDITION_R4.md) 和 [机器可读来源](primary_source_software_and_crossedition_r4.yaml)。

- **Table 2–8 不应按物理转移率表处理**：它们分别是 IMSL 旧/新数值例程、I/O 文件单元、JCL 示例、UFOTRI/AUSBPF/COMA 子程序调用清单；以原始印刷页 p.80–85 为锚点。其中 COMA1-EIGENS 与 COMA2-CMACMP 仅确认原软件职责，尚未获得真实数值结果。
- **1991 KfK4853 与 1993 KfK5194 的具体参数变更**：`ISTRGR 1000→200`，`RCMIN 4→2`，`BEWG 400→1440 g/m²`，`BEWGZ 100→160 g/m²`，`IMEAT 300→206 g/day`，`IVEGE 500→165 g/day`，`IMILK 300→315 g/day`，`DOSFOB 4.5e-11→4.0e-11 Sv/Bq`。1991 已有独立 `DOSFOB` 与扩展气孔 `IMODEL=1`，不能笼统当作 1993 才发明。
- **食物链维数及输入迁移**：1991 允许 `NBOX=6` 或 10；1993 指出 6 **未经测试**，推荐 `NBOX=NINI=NINT=NOUT=10`。原 `NTIM/TIMC` 改为 `TIMEDO/ITIMD`。
- **手册默认与历史运行实例不等价**：Table 5 样例的 `FAKC1=0.2`、`FAKC2=0.4`、`BRRATE=2.67e-4`、`DOSHT=6.8e-16` 等不能覆盖 §7.4 的印刷 DEFAULT。
- **R3 Table 1 的严格单位区别**：Table 1 表格格内只印 **g**，但同版 §7.4.3 对 BEWG/BEWGZ 等 TRIDAT 质量输入明确要求 **g/m²**。更正“per plant/crop unit”的模糊措辞，不对裸 g 作每株数解释。

**仍未完成 P0 全部文献比较及独立科学审计**；R4 仅纠正已取得的印刷证据，不启动新版物理计算。

## 1.4 R5：1990 / 1991 / 1993 三版原始物理过程逐页比对

[**R5 三版关键物理公式审计**](PRIMARY_SOURCE_TRIEDITION_PHYSICS_R5.md) · [R5 机器可读原始证据](primary_source_triedition_physics_r5.yaml)。

- **1991 年已经具有扩展气孔模型**：KfK4853 §2.1（p.4）明写 PAR、气温、湿度、土壤水分和 LAI 冠层阻力；因此 UF93-03 不再能够以“1993 首次出现扩展气孔模式”为科学主张。
- **1991 年已经具有吸力—导水率的闭合关系**：KfK4853 §3.4.3（p.29）直接给出与 1993 Eq.(21)–(23) 结构对应的 `SS=1.5E5*PSI1**(AP+BP*PSI1+CP*PSI1**NP)` 和 `COND=AKP/(SS**MKP+BKP)`，以及 `IBODEX/IARTBO` 模式；UF93-09 的“1993 才提出本构关系”说法不成立，但与 1990 数学基线的差异仍需完成。
- **OBT 的昼夜经验近似不是 1993 首创**：1990 KfK4605 p.30 与 1991 KfK4853 p.6 都提到白天升高/夜间降低；1993 的目标是 Eq.(26)–(33) 的**可选定量光合作用路线和植物分配机制**，不能只重命名既有昼夜常数。
- **再释放存在两个独立原文差异**：1990 Eq.(44) 的 `(1−ABFLR)` 在 1993 Eq.(25) 打印式中没有出现；两报告对蒸发通量 `E_as` 的印刷单位分别为 **kg m⁻² s⁻¹** 与 **kg m⁻² h⁻¹**。未核实其代码时步和 `C1/C2` 之前，不允许作未经证实的 3600 倍换算。
- **1991 年已有独立的 OBT 剂量系数**：KfK4853 §3.4.6 `DOSFOB=4.5e−11 Sv/Bq`，1993 KfK5194 §7.4.8 为 `4.0e−11 Sv/Bq`，应称“历史默认值变更”，而不是“1993 首次考虑 OBT 剂量”。
- **剩余单位风险不自动关闭**：1993 土壤 Eq.(23) 的 `K` 为 mm/day、Eq.(24) 的 `V_ab` 为 mm/hour；R5 无原始可执行程序证据，不凭经验决定转换。

这些结论均仅限已核实原文页面，**不表示 P0 已完成**，亦没有激活任何新的运行时 UFOTRI 4.0 选项。

## 1.5 R6：1993 原版源项截断、时钟、旧测试分支与气象文件

[**R6：1993 KfK 5194 运行/输入接口审计**](PRIMARY_SOURCE_RUN_IO_AUDIT_R6.md) · [R6 字段与原文风险机器清单](primary_source_run_io_contract_r6.yaml)。

- **会改变数值/控制流程而非仅影响打印**：`BODFAK=100` 决定再释放面积源最小纳入阈值；`NSTOP=70 h` 关联再释放阶段及土壤库存处理；`IFLENG=0` 采用 14 个网格点的正常面积源几何，改为 1 则是 6 网格点的特殊窄源；`CHIMAX=1e-15 Bq·s/m³` 为空气浓度积分截断，并影响食入路径；`ZEIT=3600 s` 是原手册明确要求的气象记录间隔。
- **气象时间与植物边界**：`LT1/LT2/LT3/LT4=90/303/455/670`；原版每天包含 `WR,IDIFF,IRAIN,WG,ITEMP,ISTRB,RELF,ISOIL1,ISOIL2,ISOIL3` 十类小时字段，每日一个 FORTRAN 直接访问记录，共 24 个小时。缺土壤水时原文件仍保留占位输入，使用 `IBODFX/BODEIN` 路径。
- **1991 与 1993 都保留固定再释放**：`IRFIX=0` 默认动态计算；`IRFIX=1` 以及 `REFEST=5.0%/h` 是旧开发测试能力，1993 文档特别标注仅建议测试。且 `ITEMPE/ISTRBE/RELFA` 的固定气象模式受 `METIN=1` 分支控制。
- **已发现原文约束矛盾**：`IZFREI` 同页记 `0 < IZFREI < 3600` 而 DEFAULT=3600；`RELFA` 文字写 percent 但默认 0.5。**均不能从纸面假定运行时必须采用严格端点检查或某个单位换算**。
- **输出开关不等于物理机理**：`IWRITE=1` 存入逻辑单元 9；此前食物限制的 95 是另一路产物。 `KAUSDR(12)`、`IPRPLT` 等旧式打印/控制参数不能被混入迁移方程与剂量系数。

**进展与边界**：本 R6 只做原文证据及测试契约，补足 §7.4.1/7.4.9/7.4.10/8.2 的选定字段；尚未核查完整原 FORTRAN 二进制记录布局和 1993 全部 NAMELIST。保留现有 1990 物理基线，P0 继续 Open。

## 1.6 R6b：1993 原始输入顺序、核素配置和湿清除默认模式

[**KfK5194 ISOPAR / METPAR / 固定气象和输出卡 R6 原文审计**](PRIMARY_SOURCE_INPUT_WASHOUT_R6.md) · [机器可读来源及分支约束](primary_source_input_washout_r6.yaml)。

- 1993 §7.3.3 **明确规定 HT 在前、HTO 在后**，`NABL=2`；其默认 `IWASH=0` 采用三档雨强和 `AMDA/REGTIM` 数组；**`IWASH=1` 的幂律是备选模式而非默认**。因此 UF93-08 的旧版“可能采用幂律默认”的不确定推断已由官方印刷页 pp.46–47 纠正。
- 三档分界 `IREGGR=[100,300]` 的**原始单位是 0.01 mm/h**，实际相当于 **1、3 mm/h**；HTO 三档清除率 `6e-5,1e-4,4e-4 s^-1`，分档相对降雨持续时间 `0.50,0.75,0.72`。
- 1993 `METPAR` 输入 **`IWNDG` 以 0.01 m/s 为单位**，`IREGN` 以 0.01 mm/h 为单位；`NOSHFT=2` 对应逐小时风向更新。无显式转换不得把现代 m/s 或 mm/h 数组作为原始缩放整数注入。
- 1993 印刷 p.35 的 `ISOTOPE→SOURCE`、`POLGRID→METEOZON`、`PRINTOUT→POLGRID` 和 `END→TRIDAT` 是**条件性输入顺序约束**。
- 1993 固定气象/固定再释放路径被报告明确标为**仅建议测试使用**；`RELFA=0.5` 原文按百分比命名，但可能涉及隐含单位约定，保留 `SOURCE_LIMITED`，不自动解读为 0.5% 或 50%。`KAUSDR` 是输出诊断开关而非物理计算开关。

R6 仍只是**所列页面的版本源证据审计**：没有实际编写或启用 1993 输入解析器，没有完成 KfK4605/KfK4853 全部对应配置比较，更没有原版 UFOTRI 4.0 数值等价的证据。

## 1.7 R7：1993 METEOZON / SOURCE / END 原始卡片与容量约束

[**R7 原始输入卡审计**](PRIMARY_SOURCE_METEOZON_SOURCE_R7.md) · [R7 机器可读证据](primary_source_meteozon_source_r7.yaml)。核实 KfK5194 印刷 pp.36–41 的编译数组最大值（气象序列 144、释放阶段 17）与案例默认输入并不等价；`METEOZON` 的 `LPOPT/LWOPT` 各有 0/1/2 条件分支，显式 `PWET` 的权重总和为 1。`SOURCE` 中 `QH(NP)` 的印刷单位 **cal/s** 表示热释放，而 §7.4.1 中 `Q/Q1` 是另一路放射性源输入，不可混淆。人口卡 `K1.5–K1.7` 被原文标作 COSYMA 相关，未纳入 UFOTRI；`K2.4` 的实际字段仍未在所核页明确。此处仅记录选定原文输入卡，不是原 FORTRAN 解析或数值等价证明。P0 继续 OPEN。

## 1.8 R8：1991 / 1993 固定列输入卡逐字段对照

[**R8 源版输入卡对照**](PRIMARY_SOURCE_INPUT_CARDS_CROSSEDITION_R8.md) · [结构化原文证据与风险](primary_source_input_cards_crossedition_r8.yaml)。1991 KfK4853 印刷 pp.11–12 与 1993 KfK5194 pp.37–38 的 `METEOZON K1.2` 虽然都写 `1X,A8,1X,2I10,5I5`，最后三个整数位置的印刷顺序分别是 **IBEWE/IRAU/IHOM** 和 **IRAU/IHOM/IBEWE**；按相同布局复用旧版气象站读卡可能混淆时间间隔、粗糙度类型和风速测量高度。1991 `SOURCE K2.2` 印刷 `A8,2X,3I10,F10.2`，1993 为 `A8,2X,2I10`，但两版都只列出 `UNFNAM/NPHMAX/IPZ`；不能以纸面超额描述符推出隐藏字段或原 FORTRAN 解析行为。对应的旧版编译维数、气象概率分支、`K2.3` 热释放 `QH` (cal/s)、`END` 字段一致；1993 单独注明人口卡为 COSYMA 相关，不是已证明的 UFOTRI 物理变更。R8 **只对照所列源页**，P0 和原程序数值等价仍未验收。

## 1.9 R9：1991 / 1993 印刷作业输入样例与字段说明交叉检查

[**R9 手册原始作业输入示例审计**](PRIMARY_SOURCE_JOB_CARD_SAMPLES_R9.md) · [R9 可机读源证据与风险表](primary_source_job_card_samples_r9.yaml)。1991 Table 3 印刷 p.43（PDF0 50）及 1993 Table 5 印刷 p.82（PDF0 91）都出现 `FKxy 1 0 0` 的 SOURCE 可见数字序列：虽然两版文字只列 `UNFNAM/NPHMAX/IPZ`，手册 FORMAT 却又各不相同。两版 `KARLSRHE 1 1 0 1 2 10` 示例也保留相似数字，但不能从扫描排版自动恢复 7 个数值固定列以及两版 `IBEWE/IRAU/IHOM` 与 `IRAU/IHOM/IBEWE` 的不同次序。原始卡片字节、读取列表、`K2.4` 内容和可执行程序数值等价仍然未知，不据此开发跨版读卡器或推测新物理。

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

- **1993 §5.7，p.24–25，Eq.(34)–(35)**：吸入/皮肤剂量与食入剂量分开处理；五类食品包括奶、肉、叶菜、马铃薯、谷物。HTO/OBT 有独立剂量系数，但**1991 用户指南已经明确包含独立的 OBT `DOSFOB`**；1993 改动的是值和完整食物链范围，不能将其说成 1993 才开始区分 HTO/OBT。
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

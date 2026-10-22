# KfK 5194（1993）原始公式与默认参数复核 — R2

**研究对象**：UFOTRI **4.0，1993 年 8 月，KfK 5194**。**不是** 1990 年 KfK 4605，也不是 CUFOTRI 内部项目的 V4 开发阶段。1990 年 KfK 4605 只用于差异比较。

**范围**：P0 的原文证据与风险纠错。选定章节已经通过 [KIT 官方 PDF](https://publikationen.bibliothek.kit.edu/270034158/3813483) 的**实际印刷页面图像**核对。机器可读来源：[`primary_source_formula_audit_r2.yaml`](primary_source_formula_audit_r2.yaml)。不修改物理求解器、默认值、源项或科学验证容差；不宣称 1993 原始程序数值等价。

## 1. 已复核的 1993 原文（印刷页，PDF 查看器页码 = 印刷页 + 10）

| 1993 原文 | 关键证据和实施注意事项 | 证据 |
|---|---|---|
| §5.2，p.4–5，Eq.(4)–(10) | `r_g` 汇总气孔、空气动力及边界层阻力；扩展气孔阻力具有光、湿度、土壤水、温度权重；冠层 `r_c=r_st/LAI`。`f_w` 的具体数值函数仍需核对原版输入与分支。 | [p.4](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=14)、[p.5](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=15) |
| §5.3.1，p.7，Eq.(11) | Monteith 水汽输运写成阻力形式；按 `exp(-0.398*LAI)` 分离植物和土壤净辐射；手册提供 Penman 备选。 | [p.7](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=17) |
| §5.3.2，p.9–10，Eq.(15)–(19) | 1 cm 辅助土层主要为表面阻力计算，`z=z0/phi_h`、`r_soil=z/D_eff+r_sm`；`phi_h` 按 mm 水量叙述，需明确历史归一化/数值约定，不擅自重新定义水力库存。 | [p.9](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=19)、[p.10](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=20) |
| §5.3.3，p.14，Eq.(20) | HTO 湿清除可采用 `AW*I^BW`，给出 `AW=9e-5`、`BW=0.6`，雨强 `I` 单位 mm/h；另有小于 1、1–3、大于 3 mm/h 的三档选项。 | [p.14](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=24) |
| §5.3.4，p.14–15，Eq.(21)–(24) | 吸力 `S=1.5e5*Psi^(a+b*Psi+c*Psi^n)`、`Psi=(theta_s-theta)/(theta_s-theta_w)`、导水率 `K=alpha_q/(S^m+beta)`、层间水通量 `V_ab`。**原文把 K 标注为 mm/day，把 V_ab 标为 mm/hour；不能忽略或私自改造。** | [p.14](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=24)、[p.15](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=25) |
| §5.3.4，p.15，Eq.(25) | **1993 的 REEM 蒸发项没有**旧版因子 `(1-ABFLR)`，并有 `REB*ZT` 基础项；1990 Eq.(44) 的蒸发项明确包含 `(1-ABFLR)`，且基本项记为 `DIFF*ZT`。两版源印刷式不同；是否改变原 FORTRAN 算法仍待验证。 | [1993 p.15](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=25)、[1990 p.28](https://publikationen.bibliothek.kit.edu/270029395/3813413#page=40) |
| §5.5.1，p.19–21，Eq.(26)–(31) | PAR、净 CO₂ 同化、冠层衰减、呼吸、环境胁迫。Eq.(26) 中 `P_m` 是最大 CO₂ 同化速率；Eq.(31) 还使用 CO₂→干物质系数 `COA=1.5`。 | [p.19](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=29)、[p.20](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=30)、[p.21](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=31) |
| §5.5.2，p.22–23，Eq.(32)–(33) | 简化 `T_act=T_m*fact1*fact2`；推荐的光合作用分支 `T_act=(P_act/P_m)*T_m*fact2*dis`，历史 `dis=0.5`。**这里的 P_m 是平均小时干物质生产量，不是 Eq.(26) 的最大 CO₂ 同化速率。** | [p.22](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=32)、[p.23](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=33) |
| §6.2.2–6.2.3，p.27–28 | 草类 OBT 有机库损失半期 10→15 天；叶菜 10→22 天；变化只归属于各自历史交换库，而非统一调整所有 OBT 状态。 | [p.27](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=37)、[p.28](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=38) |
| §7.4.2，p.54–55 | `IMODEL/ICOVER/IPHOTO/IMONT/IFLAGS/IFLAGR/IDEPHT/IBODEX` 的原文默认值为 1，开关语义独立；不得作为 1990 现有配置的自动替代默认值。 | [p.54](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=64)、[p.55](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=65) |
| §7.4.4，p.61 | 土壤水力参数与再释放输入定义包括 `SOILAP/BP/CP/NP`、`SOIAKP/BKP/MKP`、`RSOIL/RSSMIN/ZSOILA`、`REMRE/REMNI/REDREM`；详见独立 YAML 的 **21 项历史默认值**。 | [p.61](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=71) |

## 2. 决定性问题与科学风险

**A. 导水率与水通量时间基准不自洽（BLOCKING）：** 源式 `K` 标注 mm/day，但 `V_ab` 标注 mm/hour。执行 1993 土壤路径前，必须复核 FORTRAN 计算周期、`K_ab` 的汇总定义、原始测试输入和可能的内部转换；在不存在可验证的转换关系时保持 `SOURCE_LIMITED`，**不准推断应直接除以 24**。

**B. 光合变量同名异义（BLOCKING）：** Eq.(26) `P_m`（最大 CO₂ 同化速率，面积时间基准）与 Eq.(33) `P_m`（平均小时干物质生产率）不是同一变量。未来 P2 必须定义不同的物理状态、维度及跨层转换，不能根据符号相同直接复用。

**C. 1 cm 辅助水层是特定模型结构（BLOCKING）：** Eq.(18) 中 `z0` 单位 m、`phi_h` 原文单位 mm water（限制在 0.5–5 数值区间），潜在数值单位约定待核查。不能把 1 cm 层误当已验收的 0–5 cm HTO 主层替代品。

**D. 1990→1993 再释放的打印式不同（CONFIRMED PRINT DIFFERENCE）：** 旧 Eq.(44) 的 `(1-ABFLR)` 在 1993 Eq.(25) 中未出现，基础扩散项两版均存在。它可能来自算法变更、模型简化或印刷表示差异，**还不足以判定原 FORTRAN 可执行程序的运行差异**。

**E. 1993 新物理不能从代码模块名推定已实现（NOT ESTABLISHED）：** 已有 `leaf_ufotri_v4` / `soil_ufotri_v4` / `obt_ufotri_v4` 主要按 **KfK4605** 兼容性重建，名称中的 `v4` 同时是项目内部版本语境，不能据此推断属于 1993 UFOTRI 4.0。

## 3. 1993 来源确认 ≠ 完成差异判定

从 **1993 PDF 原文中确认一个公式或参数存在**，不等于已证实它是在 1990 年之后新增。当前 [24 项差异矩阵](PHYSICS_DELTA_MATRIX.md) 中，UF93-03、UF93-09 的分类已下调为 `1993_FORMULA_VERIFIED_1990_DELTA_PENDING`：需要进一步逐式阅读 1990 KfK4605 对应内容。已双版直接核查差异的是 UF93-11 的**打印式**。

`physics_delta_matrix.yaml` 逐项标记 `primary_1993_source_review`、`dual_edition_exact_formula_review`、`independent_scientific_review`。**所有条目的独立科学复核目前均为 NOT_COMPLETED**，不得宣布 P0 闭环。

## 4. 下一轮 P0 任务

- [ ] 逐页检查 1993 其他公式、全部 Table 1/9–12、Fig.11/12/13、每个原始输入模型开关和单位。
- [ ] 使用 1990 KfK4605 与 1991 KfK4853 用户手册逐项复核版本差异，区分确实新增、只变参数、仅换表述和未核实。
- [ ] 核查 `K_ab` 的原始构成、表 9–12 的每天/每小时单位及原版测试数字；若仍不可获得，则明确 source-limited。
- [ ] 独立审查方程/单位和矩阵分类，给出签署和未解决条目的结论，方可完成 [Issue #126](https://github.com/RRain001/cufotri/issues/126)。
- [ ] 若目标为原版完整数值等价，仍需要真实原始 UFOTRI 4.0 源/可执行程序与 golden 参考输出；外部经验资料另见 [#119](https://github.com/RRain001/cufotri/issues/119)。

**结果标签**：`TARGET=UFOTRI_4_0_1993`；`P0=PARTIAL_PRIMARY_SOURCE_AUDIT`；`1993_SOLVER_IMPLEMENTATION=NOT_STARTED`；`ORIGINAL_EXECUTABLE_EQUIVALENCE=NOT_ESTABLISHED`。

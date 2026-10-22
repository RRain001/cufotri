# UFOTRI P0 R8：1991 / 1993 历史输入卡双版源文对照

**版本边界**：1991 年 [KfK 4853](https://publikationen.bibliothek.kit.edu/270030531/3813429) 为中间版本，1993 年 [KfK 5194](https://publikationen.bibliothek.kit.edu/270034158/3813483) 为 UFOTRI 4.0 目标，1990 年 KfK 4605 为冻结的比较基线。本次为**原始印刷手册对照**，非程序读取器实测。审计机读清单：[R8 YAML](primary_source_input_cards_crossedition_r8.yaml)。

经逐页视觉核验：1991 §3.1–3.2 **印刷 pp.10–15 / PDF 零基 17–22**；1993 §7.1–7.2 **印刷 pp.36–41 / PDF 零基 45–50**。源证据在 `comparison_rows` 中分别记录页码、适用版本和事实/未证事项。

## 一、最危险的版本差异：METEOZON K1.2

1991 §3.2.1 pp.11–12 与 1993 §7.2.1 pp.37–38 的 `K1.2` **FORMAT 均印成** `1X,A8,1X,2I10,5I5`，但后续 **5 个 I5 整数位置的字段解释不完全一致**：

| 字段位置 | KfK 4853（1991）印刷列名 | KfK 5194（1993）印刷列名 |
|---|---|---|
| 第 1 个 I5 | LPOPT | LPOPT |
| 第 2 个 I5 | LWOPT | LWOPT |
| 第 3 个 I5 | **IBEWE**：气象序列间隔，h | **IRAU**：粗糙度类别 |
| 第 4 个 I5 | **IRAU**：粗糙度类别 | **IHOM**：风速计高度，m |
| 第 5 个 I5 | **IHOM**：风速计高度，m | **IBEWE**：气象序列间隔，h |

前面的 `ZONNAM, LMAX, NSTMAX` 位置在已查两版中相同。这是**可确认的纸面排序差异**，对跨版原卡复用或固定列解析具有高风险；**但由于缺少原始输入卡样例与 FORTRAN READ 实现，不能断言这一定是程序实际输入顺序的改变**。不得直接将任一版本的印刷字段列表升级为 CUFOTRI 的可运行解析规则。

## 二、SOURCE K2.2 的不匹配 FORMAT

1991 §3.2.2 **印刷 p.14**：`FORMAT A8,2X,3I10,F10.2`；1993 §7.2.2 **印刷 p.40**：`FORMAT A8,2X,2I10`。二者文字都只列三项 `UNFNAM`、`NPHMAX`、`IPZ`，其中后两项为整数。1991 纸面 FORMAT 的额外 `I10` 和 `F10.2` 描述符**不能自动推断有两个隐藏输入字段**，也不能据此断言原 1991 解析器必定读取更多数值；Fortran 格式描述符和实际 I/O 变量列表不是一回事。严格按 `SOURCE_LIMITED` 记录，待原版源代码或真实输入卡确认。

两版 `K2.3` 印刷相同：`FORMAT 2I10,3E10.3`，依次为 `IPHASE(NP),IHO(NP),QH(NP),BR(NP),HOE(NP)`。`QH` 都是 **cal/s 热释放**，**不是放射性源强**；1993 §7.4.1 `Q(NN,J)/Q1(J)` 另行约束。两版都提到 `K2.4` 却未在该 SOURCE 页列明其内容，不能臆造。

## 三、已继承的约束与人口卡适用范围

- **编译维数完全一致**：1991 p.10 与 1993 p.36 同列 `NSITMX=5, LWMAX=144, NPHSMX=17, NTYPMX=2, NUCMAX=2, NRMAX=20, NPHIMX=72`，是数组容量，**不是案例的初始参数或物理机制**。
- **气象抽样模式在所列页面一致**：`LPOPT`、`LWOPT` 分别为 0/1/2 分支；`K1.3` 用 `LWET(L)`（小时），`K1.4` 用 `PWET(L)`（概率总和 1）；当 `LWOPT != 0`，原文规定 `IBEWE` 置零。这不是实际取样计算的等价测试。
- **人口卡文档范围有新说明**：1991 p.12 的 S2 说按站点需 `K1.5–K1.7`，1993 p.38 仍打印这一控制流，却增加 `not considered in UFOTRI, COSYMA relevant` 的适用范围限制。这只能认定为**印刷说明差异**，不能推论 1991/1993 原程序的人口模块发生了物理变化。
- **END K3.1**：1991 p.15 与 1993 p.41 都是 `FORMAT A8` 的 `END` 标志，并有相同的无输入错误文本；它不是科研验收凭据。

## 四、影响和验收边界

R8 建立版本范围内的 **R8-01–R8-07** 比较证据与五条风险登记，但不替代 [R7 的 1993 专项原文审计](PRIMARY_SOURCE_METEOZON_SOURCE_R7.md)；R7 `historical_1991_comparison=NOT_COMPLETED` 指其本身未完成全面对照，而 R8 **仅完成所列页面的部分双版对照**。优先解决 `K1.2` 实际 FORTRAN 变量输入顺序、1991 `K2.2` 超额描述符、`K2.4` 原始卡及 `IPZ` 时标，再决定是否开发真正的版本化读卡接口。

本 PR 不变更 `src/`、`configs/`、冻结的 KfK4605 求解器、科研容差、Docker 或锁文件。**P0=OPEN；1993_RUNTIME_MODE=NOT_ACTIVATED；ORIGINAL_EXECUTABLE_EQUIVALENCE=NOT_ESTABLISHED；EMPIRICAL_VALIDATION=NOT_ESTABLISHED**。所有结论仅是所列原始文献页面的印刷事实，待独立科学复核。

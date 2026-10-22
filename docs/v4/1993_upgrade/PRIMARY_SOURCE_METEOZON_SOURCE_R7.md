# UFOTRI 4.0（1993）P0 R7 — METEOZON / SOURCE / END 原版输入卡审计

**主版本：KfK 5194（August 1993）**。本轮以 [KIT 官方原始 PDF](https://publikationen.bibliothek.kit.edu/270034158/3813483) 的印刷 **p.36–41（PDF 0 基索引 45–50）** 为证据，对选定输入卡作页面级复核；不是 UFOTRI 4.0 原程序输入解析器，也不修改 KfK 4605（1990）基线。机器可读字段见 [R7 证据](primary_source_meteozon_source_r7.yaml)。

## 1. 编译期上限不是物理默认值（§7.1 p.36）

原版 `PARAMETER` 列出 `NSITMX=5`、`LWMAX=144`、`NPHSMX=17`、`NTYPMX=2`、`NUCMAX=2`、`NRMAX=20`、`NPHIMX=72`。它们是历史程序的**数组维数上限**，并非要求现代 CUFOTRI 固定 144 条气象记录、17 段排放或 20 个距离圈。不得把该页翻录的容量误作模型的案例输入默认值。

## 2. METEOZON：气象序列的选择、时标与概率（§7.2.1 pp.37–39）

`K1.1` 为 `METEOZON` 标识卡，`K1.2` 按固定列依次包含 `ZONNAM, LMAX, NSTMAX, LPOPT, LWOPT, IRAU, IHOM, IBEWE`。其中 `LMAX ≤ LWMAX=144`；`IRAU` 是历史粗糙度**类别**（2=较低、3=较高），不能直接作为现代 SI 粗糙度长度；`IHOM` 是风速测量高度（m）；`IBEWE` 为两条气象序列间隔（h），原文明确 `LWOPT≠0` 时将其设为 0。

| 控制值 | 0 | 1 | 2 |
|---|---|---|---|
| `LPOPT` | 各气象序列等概率 `1/LMAX` | 从 `K1.4` 读取 `PWET(L)` | 从 `NUNITS(13)` 读取概率 |
| `LWOPT` | 循环取样 | 从 `K1.3` 读取小时起始 `LWET(L)` | 从 `NUNITS(13)` 读取起始时刻 |

`K1.3` 仅在 `LWOPT=1` 时适用，`K1.4` 仅在 `LPOPT=1` 时适用；当使用显式权重时，原文要求 `ΣPWET(L)=1`。这属于**历史条件分支**，并不表示已复原 FORTRAN 读取器或外部文件的二进制布局。

`K1.5–K1.7` 是人口/站点数据卡，原文标注 *not considered in UFOTRI, COSYMA relevant*。因此不能把这些卡当作现代 CUFOTRI 的强制输入，也不得从 `NSTMAX` 推断已经实现多场址人口剂量计算。非默认极坐标网格需先给出 `POLGRID`，然后才读 `METEOZON`（既有 R6b 顺序约束）。

## 3. SOURCE：分阶段排放输入（§7.2.2 p.40）

`K2.1` 为 `SOURCE` 标识；`K2.2` 是 `UNFNAM/NPHMAX/IPZ`，其中 `NPHMAX ≤ NPHSMX=17`；`IPZ` 调整所有气象序列的起始位置，但**该页未独立明确时间单位**，不能据惯例强行解释。每个 `NP=1..NPHMAX` 有 `K2.3`：

| 原始字段 | 印刷意义 | 单位 |
|---|---|---|
| `IPHASE(NP)` | 链式反应结束至本阶段开始的整小时数 | whole hours |
| `IHO(NP)` | 排放高度 | m |
| `QH(NP)` | **释放热功率（thermal energy rate）** | **cal/s** |
| `BR(NP)` | 反应堆建筑物宽度 | m |
| `HOE(NP)` | 反应堆建筑物高度 | m |

**必须防止的映射错误**：`QH(NP)` 是热释放输入，**不是** §7.4.1 p.52 的 `Q(NN,J)`（HT/HTO 相对份额）或 `Q1(J)`（绝对放射性源强），更不能直接把 `QH` 当 Bq/s。原文还提及各阶段 `K2.4`，但印刷 p.40 未呈现 `K2.4` 详细内容，暂列 `SOURCE_LIMITED`，不补写虚构参数。

## 4. END：历史输入终止标志（§7.2.3 p.41）

`END` 仅有 `K3.1` 标识卡，原程序若无输入错误会打印 `END OF INPUT WITHOUT ERRORS`。该字符串只是**输入读取状态**，不是物理正确性、回归或科学有效性的证明。R6b 对 `END` 之后可附 `TRIDAT` 的约定仍有效。

## 5. P0 后续门槛

当前结论仅限上述 1993 文献页；1990/1991 对应卡片完整对照、`IPZ` 时钟基准、`K2.4` 内容、历史解析器实际行为及独立科学复核**仍未完成**。保持 `P0=OPEN`、`1993_RUNTIME_MODE=NOT_ACTIVATED`、`ORIGINAL_EXECUTABLE_EQUIVALENCE=NOT_ESTABLISHED`。本 R7 不修改 `src/`、`configs/`、`uv.lock`、科研容差或旧版物理模型。

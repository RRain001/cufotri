# UFOTRI 4.0 (1993) — P0 R4: software tables and 1991→1993 user-guide controls

**规范版本始终是 1993 KfK 5194（W. Raskob，UFOTRI 4.0）**：[官方原文](https://publikationen.bibliothek.kit.edu/270034158/3813483)。对照的是 [1991 KfK 4853 用户手册](https://publikationen.bibliothek.kit.edu/270030531/3813429) 与 [1990 KfK 4605 数学报告](https://publikationen.bibliothek.kit.edu/270029395/3813413)。**1993 软件功能、1991→1993 配置变更、1990→1993 物理变更是三种不同证据层次，不能相互替代。**

**本轮范围**：1993 Table 2–8、§7.4.3/§7.4.7/§7.4.8 的可核实参数和 1991 对照；首次纠正 R3 Table 1 的质量单位映射。源锚点、代码符号与分类见 [R4 YAML](primary_source_software_and_crossedition_r4.yaml)。该文档是证据审计，不是可运行的 UFOTRI 4.0 FORTRAN 重建，也不是科学数值验收。

## 1. Table 2–8：主要是软件结构，不是 7 张物理参数表

| 1993 Table | 印刷页（PDF 零基页） | 官方表的内容 | 对开发的意义 |
|---|---:|---|---|
| 2 | 80（89） | 旧版 IMSL 矩阵平衡、特征值、向量和线性代数例程 | 识别旧数值后端；**不是转移率** |
| 3 | 80（89） | 新版 IMSL 特征值、LU 分解和线性代数例程 | 1993 支持多种 IMSL 依赖；符号扫描歧义不得猜成准确 API |
| 4 | 81（90） | FORTRAN I/O 文件单元，包括 5、6、11、13、21、31、91–93、95 | Unit 95 保存包括食物限制在内的剂量输出；不是新剂量方程 |
| 5 | 82–83（91–92） | IBM JCL/FORTRAN 测试作业与示例 NAMELIST | **示例算例取值**不能冒充用户指南 **DEFAULT** |
| 6 | 84（93） | 主程序调用 25 个子程序/模块 | `COVER`、`DOSREL`、`ZEITNE`、`FOOBAN` 等实际职责名称，不能由名字反推精确公式 |
| 7 | 85（94） | AUSBPF 面源：土壤阻力、水迁移、沉降、再释放 | `BODENR-WATER`、`BODENR-RESIST`、`BODENR-MASSCH` 的原版职责边界 |
| 8 | 85（94） | COMA 转移矩阵、特征求解、库存及积分计算 | `COMA1` 装配矩阵、`COMA1-EIGENS` 特征处理、`COMA2` 求库存积分、`COMA2-CMACMP` 处理虚部 |

**R4 科学判断**：Table 2/3/6–8 可为未来 P1/P6 提供算法架构、谱分解计算路径及原版数值库要求的证据，**不是** 1993 “新增七组土壤或植物参数”。即使按谱分解重写 COMA，也不能在无原 FORTRAN 和 golden 输出时声称数值等价。R4 YAML 保留了扫描不清的旧 IMSL 例程名，并标为候选而非验证后的调用接口。

<text>官方页：</text>[p.80](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=90)、[p.81](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=91)、[p.82](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=92)、[p.83](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=93)、[p.84](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=94)、[p.85](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=95)。

## 2. 1991→1993 真实的印刷默认值差异

| 输入 | **1991 KfK 4853** | **1993 KfK 5194** | 单位及影响 |
|---|---:|---:|---|
| `ISTRGR` | 1000 | **200** | 高太阳辐射应激判据，源手册描述 `W/m²×0.357×0.8`，避免用未定义的纯 W/m² |
| `RCMIN` | 4.0 | **2.0** | 区域 1 最小气孔扩散阻力历史参数 |
| `BEWG` | 400 | **1440** | 区域 1 植物水质量，**g/m²** |
| `BEWGZ` | 100 | **160** | 区域 1 植物有机质量，**g/m²** |
| `LEAF` | 3.0 | 3.0 | LAI；数值不变 |
| `IMODEL` | 1 | 1 | 1991 年已提供扩展气孔阻力模式，**不应单凭 1993 记载宣称其在 1993 才被发明** |
| `IMEAT` | 300 | **206** | g/day，肉类摄入 |
| `IVEGE` | 500 | **165** | g/day，叶菜摄入 |
| `IMILK` | 300 | **315** | g/day，奶制品摄入 |
| `DOSF` | 1.7e−11 | 1.7e−11 | HTO Sv/Bq；未变 |
| `DOSHT` | 1.7e−15 | 1.7e−15 | HT Sv/Bq；未变 |
| `DOSFOB` | 4.5e−11 | **4.0e−11** | OBT Sv/Bq；值变了，但**1991 就已独立设置 DOSFOB** |

**特别重要**：1991 年指南已有独立 OBT 剂量转换参数，因此原矩阵如将“对 OBT 使用独立剂量系数”笼统描述为 **1993 首次新增机制**，证据是不充分的。能够确认的是 1991→1993 的 `DOSFOB` **默认数值变化**，和 1993 食物种类扩展；1990 数学报告所述摄入公式的差异仍需另行严格审核。

来源：1991 §3.4.2 p.27 与 §3.4.6 p.33，[PDF 页面图像 p.34](https://publikationen.bibliothek.kit.edu/270030531/3813429#page=35)、[p.40](https://publikationen.bibliothek.kit.edu/270030531/3813429#page=41)；1993 §7.4.3 p.56–59、§7.4.8 p.65，[p.65](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=75)。

## 3. 长期食物链：1991 可用配置不等于 1993 已测试配置

| 审计点 | 1991 §3.4.5（印刷 p.32） | 1993 §7.4.7（印刷 p.64） |
|---|---|---|
| 区室维数 | `NBOX/NINI/NINT/NOUT` 必须一致，可选 6 或 10 | 四者必须一致；**建议 10，旧值 6 在此版本未经测试，可能报错** |
| 转移系数数目 | `NTFX=27` 适用于混合区域，15 适用于仅农业区 | `NTFX=27` 且不建议修改；冬/夏季内部重新组织 |
| 剂量时刻 | `NTIM=3`，`TIMC` 数组，默认 0/30/365 天等 | 旧 `NTIM/TIMC` **删除**，其职责由 `TIMEDO/ITIMD` 承担 |

报告明确说过，若以旧版输入卡尝试将 `NBOX=6` 直接送入 1993 兼容路径，不应因能通过早期模块测试就自动视为已通过新版兼容。**P1 必须设计拒绝无证据配置的校验和版本化迁移。**

来源：[1991 印刷 p.32](https://publikationen.bibliothek.kit.edu/270030531/3813429#page=40)、[1993 印刷 p.64](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=74)。

## 4. 表格取值、NAMELIST 默认值、运行实例不能混用

在 1993 Table 5（印刷 p.83）的示例运行输入，与同一报告中的用户指南默认值存在可确认差别：

| 输入 | §7.4 历史默认值 | Table 5 实例值 |
|---|---:|---:|
| `FAKC1` | 0.4 | **0.2** |
| `FAKC2` | 0.2 | **0.4** |
| `BRRATE` | 3.3e−4 m³/s | **2.67e−4 m³/s** |
| `DOSHT` | 1.7e−15 Sv/Bq | **6.8e−16 Sv/Bq** |
| `BEWGP` | 2400 g/m² | **2700 g/m²** |

**判定**：这并不表示手册自相矛盾。原书明确是 *example of a Job Control file*，即有特定气象、源项和使用参数的算例，**不能替代 §7.4 DEFAULT**。两者在未来的配置模式中必须单独保存为 `HISTORICAL_GUIDE_DEFAULT` 和 `HISTORICAL_EXAMPLE_CASE`。

## 5. 对 R3 Table 1 单位的补充校正

1993 **Table 1**（印刷 p.17）的每个表格数值后写 **g**，并附文献引用标签（如 `/34/`）；表格本身**没有直接印出 g/m²**。但同报告 §7.4.3 对相应的 BEWG、BEWGZ 和马铃薯 BEWGP 等原始配置变量明确要求 **g/m²**，可作为未来将 Table 1 数字映射到每单位土地面积植物库存的依据。

所以最准确的说法是：**Table 1 原始表格单位记为 g；原版 TRIDAT 相关质量输入的单位记为 g/m²。** 不能凭 Table 1 中的裸数值将其理解为“每株作物质量”，也不能忽略输入卡中的面积归一化要求。R3 原先 `per plant/crop unit` 的表述过度具体，本次纠正，但**不追改历史物理数据**。本区别对 P5 植物面积库存与 P6 食品质量剂量换算很关键。

来源：[1993 Table 1 p.17](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=27)、[1993 §7.4.3 p.56–59](https://publikationen.bibliothek.kit.edu/270034158/3813483#page=66)。

## 6. 阶段验收与未闭环项目

- [x] Table 2–8 **用途分类和关键入口审计**；并非物理转移率表的判断已经证实。
- [x] 已交叉检查 16 项 1991→1993 指定默认参数，并记录新增/旧值沿用的证据强弱。**该 16 项清单不是全部 NAMELIST 的完整对比。**
- [x] 1991 NBOX=6/10→1993 建议只使用 10、旧 NTIM/TIMC→TIMEDO/ITIMD 的接口差异。
- [x] 明确区分 1993 用户指南默认值与 Table 5 实例取值。
- [x] 更正 R3 Table 1 的表内 g 与输入卡 g/m² 区别。
- [ ] KfK 4605（1990）的每个默认值/物理方程与 1991 和 1993 的**三方逐式对照**仍未全部完成。
- [ ] 1993 所有剩余 NAMELIST 参数与 Table 2/3 某些 IMSL 符号拼写仍需独立复核。
- [ ] 原版可执行程序/测试 deck 数值、长时食物链矩阵谱计算和任意现代监管参数等价性：**NOT_ESTABLISHED**。
- [ ] [Issue #126](https://github.com/RRain001/cufotri/issues/126) **仍保持 OPEN**；P1 物理接口不在本轮实现。

**约束**：不修改任何 `src/` 方程、`configs/` 默认值、Docker 镜像、依赖锁、守恒阈值或 1990 基线测试。

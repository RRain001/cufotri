# CTEAS_UFOTRI 只读验收审计

审计日期：2026-07-24
审计对象：`/Users/rain/Documents/Doctor/Topic/CETAS_ufotri`
审计基准：`main`，`604f04e feat: add CLI outputs and acceptance workflow`

## 1. 执行摘要

**判定：`ACCEPT_WITH_CONDITIONS`。**

当前代码足以证明一个可运行的、单位主线基本一致的最小 HTO
大气—表层土壤—植物 TFWT/OBT—再释放工程原型已经形成。43 项测试全部通过，
三套短期案例可由当前代码在内存中复现，600 s/300 s 步长差异小于 0.2%。
README 对“不是完整 UFOTRI”以及食物链、剂量、HT、多层土壤等排除项的表述基本准确。

但是，当前还不应无条件保留 `COMPLETE`：

1. `mass_balance` 只闭合每平方米地表的 soil/TFWT/OBT 三库存；原始烟囱排放、
   高斯空气库存、烟羽出域和反馈面积源没有进入同一个守恒域。因此约
   \(10^{-16}\) 主要是显式更新与同一组通量的代数闭合，不是整个
   大气—地表空间域质量守恒。
2. 手册 Eq. (6) 的 fallout/washout 源耗减未实现；沉积从地表角度是输入，
   但没有从高斯烟羽源强扣除。当前文档将高斯模块写成 `PASS` 过强。
3. 可选“径流开启 + 雨水 HTO”路径会把径流雨量的 HTO 也计入土壤。独立诊断中，
   物理入渗应带入 0.6 Bq m-2，代码计入 6.0 Bq m-2，但代数守恒残差仍为 0。
4. 极低但为正的风速没有下限或 calm-wind 策略；同一案例在
   \(u=10^{-12}\) m s-1 时给出 \(8.95\times10^{15}\) Bq m-3，而
   \(u=0\) 时突变为 0。
5. 若称为手册映射完成，还需明确若干实质简化：反馈延迟是一个内部步长
   （默认 600 s），而手册为一小时；顶层根系比例配置为 1.0，而手册文字为约
   20%；Eq. (40) 在代码中遮阴完整 Penman PET，而手册公式只对平衡辐射项写出
   遮阴；高级 REEM/DIFF/ZT 仍是经验重构。

建议先把状态降为“功能完整候选 / conditional baseline”，完成第 12 节列出的
HIGH 项后再建立正式完成基线。

## 2. 仓库状态

| 项目 | 审计结果 |
|---|---|
| 当前路径 | `/Users/rain/Documents/Doctor/Topic/CETAS_ufotri` |
| 分支 | `main` |
| HEAD | `604f04e feat: add CLI outputs and acceptance workflow` |
| 上游 | `origin/main` 与 HEAD 一致 |
| 提交历史 | 已有 5 个提交；“尚无初始提交”不成立 |
| 审计开始时工作树 | 干净，无未跟踪文件 |
| `git diff --check` | 通过，无输出 |
| 敏感文件跟踪检查 | 未发现真实密钥被跟踪；命中仅为 `era5_key.example.txt` 和凭据测试 |
| 本地敏感文件 | 存在被忽略的 `era5_key.txt`；未读取、未输出其内容 |
| 原始数据/输出 | `data/`、`outputs/` 均被忽略 |
| 构建/测试产物 | `.venv/`、`__pycache__/`、`*.egg-info/`、`.pytest_cache/` 等被忽略 |

`.gitignore` 已覆盖本项目当前使用的 `era5_key.txt`、`.env*`、原始数据、
输出和常见 Python 构建产物。缺口是未显式覆盖 `.cdsapirc` 以及更一般的
credential/token 文件名；建立下一次基线前宜补齐。此次没有创建
`audit_tmp/` 或其他临时文件。

## 3. 完成范围判断

### 3.1 可被当前证据支持的范围

- ERA5 固定点 CSV/NetCDF 读取、UTC 解析、区间/累计量转换；
- HTO-only 稳态高斯点源和矩形面积源工程实现；
- 5 cm 单层水桶、土壤 HTO 面库存；
- 常数植物水库存下的 TFWT 和简化非交换 OBT；
- 基础质量通量再释放，以及暂定的 REEM/DIFF/ZT 模式；
- 滞后一个内部时间步的面积源大气反馈；
- 24–48 h 短案例、结果表、网格和诊断图；
- 地表三库存的逐步代数守恒、单元/集成/步长回归测试。

### 3.2 不可声称完成的范围

以下均未实现，仓库主要文档也基本明确排除：

- 完整 UFOTRI/MUSEMET 轨迹与全部公式；
- HT 化学、土壤氧化、HT 专属 C2 修正逻辑；
- 多层土壤 Richards/Darcy 输运；
- 完整植物气孔/边界层阻力与动态物候；
- 动物、食物链、吸入/摄入和剂量；
- 监管级、场址级或观测数据验证；
- 整个大气—地表空间域的质量守恒。

`README.md` 第 3–6、96–104 行的范围限定是准确的。问题主要在
`docs/implementation_status.md` 将高斯和质量守恒写成未限定的 `PASS`，
以及 `docs/completion_audit.md` 声称 43 项测试覆盖“所有计划不变量”；
测试并未覆盖本报告第 11 节列出的关键边界。

## 4. 手册—代码映射表

状态含义采用本次审计指定集合。若一项同时有基础模式和高级模式，分别列出。

| 方程/功能 | 状态 | 实现位置 | 审计结论 |
|---|---|---|---|
| 高斯扩散公式 | `PROJECT_SIMPLIFICATION` | `atmosphere/gaussian.py` | 地面反射基础核与手册 Eq. (6) 主体一致；未实现 Eq. (6) 的 fallout/washout 耗减，也不是手册的分段轨迹模型 |
| PG 农村扩散参数 | `PROJECT_SIMPLIFICATION` | `atmosphere/dispersion_parameters.py` | 使用通用 Turner 式 A–F 系数；不是手册按粗糙度、源高选取的 Mol/Karlsruhe-Jülich 参数集 |
| 烟羽抬升 | `PROJECT_SIMPLIFICATION` | `atmosphere/plume_rise.py` | 默认固定 15 m；可选 `briggs_simple` 明确不是稳定度完整 Briggs |
| 混合层反射 | `PROJECT_SIMPLIFICATION` | `atmosphere/gaussian.py` | 用上下边界镜像源；手册主模型描述的是混合层历史约束和 \(\sigma_z\le0.8h\)，并非同一算法 |
| 空气到土壤沉积 | `MANUAL_DERIVED` | `coupling/integrator.py:65` | \(F_{as}=v_dC_a\) 的 HTO-only 库存写法正确；但烟羽没有对应源耗减 |
| Penman 潜在蒸散发 | `PROVISIONAL` | `meteorology/fallback_fluxes.py:27` | 辐射项量纲闭合；气动项由暂定 SI 系数补足，不能称 Eq. (38) 精确复刻 |
| VPD | `MANUAL_DERIVED` | `meteorology/derived_variables.py:20` | 由 2 m 温度和露点饱和水汽压差得到 Pa，逻辑正确 |
| 净辐射 | `PROVISIONAL` | `meteorology/era5_reader.py:78` | 真净短波+净长波路径正确；缺字段时用吸收短波减固定 50 W m-2 |
| LAI 遮阴 | `PROJECT_SIMPLIFICATION` | `meteorology/fallback_fluxes.py:65` | 指数系数 0.398 来自 Eq. (40)，但代码遮阴完整 Penman PET；手册 Eq. (40) 写的是平衡辐射项 |
| 土壤含水限制因子 | `MANUAL_DERIVED` | `meteorology/fallback_fluxes.py:19` | Eq. (41) 形式和系数一致；用水深比代替百分比比值在固定层深下等价，并增加上限 1 |
| 土壤水量平衡 | `PROJECT_SIMPLIFICATION` | `soil/water_balance.py` | 5 cm 水桶满足 \(P-E_s-T_p-L_s-R_o\)，损失受库存约束；不是多层水势模型 |
| 土壤 HTO 库存平衡 | `MANUAL_DERIVED` | `coupling/integrator.py:112` | Eq. (2) 的 HTO-only 面库存形式，增加雨水 HTO 和衰变；可选径流雨水边界有错误 |
| 根系吸水 | `PROJECT_SIMPLIFICATION` | `case.py:220`, `integrator.py:109` | 默认 \(U_s=T_p\)，可选队列延迟；顶层比例为 1.0，而手册文字约 20%，且水量本身不随 HTO 延迟 |
| 植物 TFWT | `PROJECT_SIMPLIFICATION` | `coupling/integrator.py:130` | 常数 \(W_p\)，根输入、蒸腾输出、OBT 内转移；手册阻力型叶片交换默认关闭 |
| OBT | `PROJECT_SIMPLIFICATION` | `plant/obt.py`, `integrator.py:120` | 0.06% h-1 和 0.3% h-1 数值来自手册文字；昼夜倍率、周转返回 TFWT 是项目闭合 |
| 基础再释放 | `PROJECT_EXTENSION` | `reemission/fluxes.py:6` | \(F_{re}=E_sC_s+T_pC_p\) 是透明、守恒的工程基线，不是手册 Eq. (44) |
| 高级再释放 | `PROVISIONAL` | `reemission/fluxes.py:15` | 有 REEM、DIFF、ZT、C1 标定和 ABFLR 近似；DIFF 未按水浓度修正，雨天专门逻辑缺失，C2 仅为自由乘子 |
| 大气反馈 | `PROJECT_SIMPLIFICATION` | `case.py:173` | 再释放通量以矩形点源求和进入下一内部步；手册是一小时后进入次级模型，当前默认是 600 s |
| 氚衰变 | `PROJECT_EXTENSION` | `coupling/integrator.py:118` | 对 soil/TFWT/OBT 使用统一一阶物理衰变；是合理扩展，但不是 Eq. (1)–(3) 当前摘录中的显式项 |
| HT 氧化 | `NOT_IMPLEMENTED` | — | 明确排除 |
| 多层土壤 | `NOT_IMPLEMENTED` | — | 明确排除 |
| 食物链/人体剂量 | `NOT_IMPLEMENTED` | — | 明确排除 |

因此，`MANUAL_MAPPING_STATUS` 不能为无条件 `PASS`；合适表述是：
“最小 HTO 主线已映射，但包含明确项目简化和暂定闭合，且若干差异尚未在状态表完整披露。”

## 5. 变量与单位审计

| 量 | 代码含义与单位 | 结果 |
|---|---|---|
| \(C_a\) | `air_hto_concentration`，Bq m-3 | 一致 |
| \(M_s\) | `soil_hto_bq_m2`，Bq m-2 | 一致 |
| \(W_s\) | `soil_water_m`，m | 一致；未临时替换为 kg m-2 |
| \(C_s=M_s/W_s\) | Bq m-3 water | 主积分、输出和测试均一致 |
| \(M_p\) | `plant_tfwt_bq_m2`，Bq m-2 | 一致 |
| \(W_p\) | `plant.water_storage_m`，m，常数 | 一致 |
| \(C_p=M_p/W_p\) | Bq m-3 water | 主积分、输出和测试均一致 |
| \(M_{obt}\) | Bq m-2 | 一致 |
| \(F_{as},F_{re}\) | Bq m-2 s-1 | 一致 |
| \(E_s,T_p,U_s,L_s\) | m s-1 | 一致 |

未发现 mm/m、kg m-2/m、Pa/kPa、J m-2/W m-2 或
Bq s-1/Bq m-2 s-1 的静默混用。Eq. (44) 中
\(E/BODWA\) 由水深比计算时水密度相消，量纲仍为 s-1。

需要修正的是边界语义而非基本量纲：径流开启时雨水 HTO 仍按总降水输入；
面积源路径将代表性地表列的 Bq m-2 s-1 通量复制到配置矩形，却没有对应的
空间地表库存定义。

## 6. ERA5 审计

- `read_era5` 将时间解析为带时区 UTC、排序，并在累计转换中拒绝非递增时间。
- 区间累计量按实际相邻时间差除以秒数；`cumulative_with_resets` 对负差使用
  当前累计值作为新周期首段。
- 降水从 m interval-1 转为 m s-1；辐射从 J m-2 interval-1 转为 W m-2。
- 真净辐射使用净短波与净长波相加，约定向下为正。
- 只有向下短波/长波时，不把向下长波误当净长波，而使用明确标为 provisional
  的短波吸收减固定长波损失。
- RH/VPD 由温度、露点计算；10 m 风速和气象“来向”公式正确。独立四方位抽查
  与坐标旋转相符。
- 地面气压和海平面气压仅映射、未进入 PET，因此不存在二者误用；代价是
  psychrometric constant 固定。
- ERA5 潜热通量虽在映射文件列出，但未进入 `prepare_hourly_forcing` 和正式
  Penman 路径，未发生“ERA5 潜热 + Penman 蒸发”重复计入。

状态为 `PASS_PROVISIONAL`。剩余风险包括：真实文件无内嵌单位属性、净辐射
fallback 未经场址验证、主运行只核对 forcing 首时刻而不核对每个时间戳与声明
步长完全对齐。

## 7. 高斯大气模型审计

通过项：

- 上风向和零源项返回 0；
- 气象风向旋转正确，西风下东侧受体为顺风；
- 地面反射的无顶边界形式给出手册地面浓度中的因子 2；
- 点源单位为 Bq s-1，矩形源单元为
  \(F\,\Delta x\,\Delta y\) Bq s-1，面积归一化正确；
- 面积源确实是 midpoint quadrature 下的若干点源求和，线性和网格收敛有测试；
- 主烟羽与次级烟羽只在 `air = primary + secondary` 相加一次。

条件项：

- Eq. (6) 的 fallout/washout 未实现，沉积不削弱 \(Q\)；
- `briggs_simple`、PG 系数和混合层镜像均为项目简化；
- 仅对 `u<=0` 返回 0，没有最小风速、calm persistence 或替代扩散模型；
- 配置同时有 `reemission_feedback_area_m2` 与矩形长宽。面积源模式只使用长宽，
  若两者不一致不会报错；
- 单个代表性土壤列的通量被视为整个矩形均匀通量，没有空间库存与采样映射；
- 手册次级模型延迟一小时，当前延迟一个内部步长；
- 稳态高斯浓度没有空气库存或传播时间语义。

## 8. 土壤、植物与 OBT 审计

### 8.1 水量

更新顺序为降雨（可选先扣径流）→ 蒸发/蒸腾容量限制 → 超过最大持水量的深层
排水。损失不能把水深降到 `minimum_water_m` 以下；表层深度配置为 0.05 m。
水量残差按同一通量计算并闭合。

### 8.2 土壤 HTO

`Cs` 在步首按 \(M_s/W_s\) 计算；蒸发、根吸收、渗漏和衰变并发流出在超过
步首库存时按比例缩放，避免用最终 `max(0)` 掩盖负库存。雨水 HTO 默认关闭。

缺陷：径流开启时，水量只接收入渗部分，但 HTO 输入仍使用总降水。
此外，同步降雨带入的 HTO 在本步不参与随饱和排水流出，这是当前显式算子分裂
的结果，应在数值方案中说明或调整。

### 8.3 TFWT/OBT

- \(W_p\) 是常数；
- 叶片直接吸收默认关闭；
- TFWT→OBT 在 TFWT 扣除、在 OBT 加入；
- OBT 周转在 OBT 扣除、返回 TFWT；
- 生物周转与放射性衰变分别计算；
- 昼夜速率以正净辐射判断，1.5/0.5 只在恰好 12 h/12 h 时保留日均值。

三小时模式只延迟用于 HTO 转移的 `root_uptake_m_s` 队列；土壤水量仍在当前步
按蒸腾扣除，且延迟时使用的是当前 \(C_s\)，不是三小时前的浓度。这是可运行的
算子简化，不是手册水分—HTO 延迟过程的严格复刻。

## 9. 再释放与大气反馈

### 9.1 基础模式

\[
F_{re}=E_sC_s+T_pC_p
\]

两项分别只从土壤和 TFWT 扣除一次，并在下一步作为次级面积源通量使用，
没有同一步重复扣除。该模式质量语义清楚，但属于项目工程扩展。

### 9.2 高级模式

高级土壤模式具备：

- REEM：由 \(E_s/W_s\) 相对参考值标定至 10% h-1；
- DIFF：固定 1% h-1；
- ZT：按配置半衰期指数下降；
- C1：隐含在参考标定中；
- ABFLR：用当步排水/降雨深度比近似；
- C2：`empirical_ht_correction`，当前 HTO 配置为 1.0；
- 白天 REEM+DIFF，夜间 DIFF。

但 DIFF 未按手册所述随不同土壤水浓度修正，雨天 3% 等专门规则未实现，
ABFLR 和 C1/C2 都是工程重构。它可以称“UFOTRI 风格的暂定经验模式”，不能称
严格复刻或物理验证。它通过库存限流达到数值闭合，尚不足以证明经验物理闭合。

### 9.3 反馈

反馈是明确的算子分裂：第 \(n\) 步从地表移出的再释放通量在第 \(n+1\) 个内部步
形成次级浓度。默认 600 s，不是手册一小时。基础/高级模式的地表损失都进入同一
反馈接口。

## 10. 质量守恒独立审计

### 10.1 当前诊断实际守恒域

`State.total_hto_bq_m2` 只含：

\[
M_s+M_p+M_{obt}.
\]

逐步诊断为：

\[
M_0 + (F_{dep}+F_{leaf})\Delta t
-(F_{soil\to air}+F_{plant\to air}+F_{drain})\Delta t
-D\Delta t-M_1.
\]

因此：

1. **当前守恒是地表三库存箱室内部守恒，不是整个大气—地表空间域守恒。**
2. **高斯稳态空气浓度没有被定义为库存。**
3. **烟囱排放和平流出域没有进入该诊断。**
4. **约 \(10^{-16}\) 主要反映更新式和诊断式复用了相同通量后的浮点代数闭合。**

在整个域的视角，再释放本应是地表到空气的内部转移；当前诊断先把它当地表
边界输出，后续若再沉积又当新的外部输入。面积源总 Bq s-1 也没有与空间地表
库存相连接，所以无法从现有输出重建全域守恒。

### 10.2 独立反例

只读内存诊断设置：

- `runoff_enabled=True`
- 降雨 \(10^{-4}\) m s-1
- 入渗能力 \(10^{-5}\) m s-1
- 雨水 HTO 1000 Bq m-3
- \(\Delta t=60\) s

结果：

| 量 | 值 |
|---|---:|
| 物理入渗 HTO | 0.6 Bq m-2 |
| 代码计入土壤/报告外部输入 | 6.0 Bq m-2 |
| 未随径流排出的差额 | 5.4 Bq m-2 |
| 诊断残差 | 0.0 Bq m-2 |

该反例直接证明“残差为零”只能证明实现的账目自洽，不能独立证明边界项完整或
物理正确。

### 10.3 三套案例

| 案例 | 步数 | 最大绝对残差 Bq m-2 | 最大相对残差 | 最终 soil / TFWT / OBT Bq m-2 |
|---|---:|---:|---:|---|
| synthetic 48 h, 600 s | 288 | 2.328306e-10 | 3.999127e-16 | 9.796716e5 / 6.787245e4 / 8.715806e2 |
| ERA5 48 h, 600 s | 288 | 9.313226e-10 | 4.336388e-16 | 2.145552e6 / 1.392569e4 / 1.029638e2 |
| advanced 24 h, 600 s | 144 | 7.275958e-12 | 4.425898e-16 | 2.362912e4 / 5.098441e3 / 1.802967e1 |

这些数值由当前代码重新在内存中计算，与保存的报告一致，但其“守恒”含义必须
按 10.1 节限定。

## 11. 测试覆盖矩阵

### 11.1 方程/功能—实现—测试

| 功能 | 实现文件 | 测试文件 | 覆盖判断 |
|---|---|---|---|
| Gaussian、上风向、面积源、反射、旋转 | `atmosphere/gaussian.py` | `test_gaussian.py`, `test_short_case.py` | 部分充分；缺 calm/低风、耗减 |
| PG/Turner | `dispersion_parameters.py` | `test_gaussian.py` | 分类点覆盖；无参数范围/手册数据表对照 |
| 烟羽抬升 | `plume_rise.py` | `test_plume_rise.py` | 正值和温度响应；无稳定度完整参考 |
| RH/VPD/辐射/风 | `derived_variables.py`, `era5_reader.py` | `test_meteorology.py`, `test_era5_reader.py` | 核心单位与累计重置有覆盖 |
| Penman/LAI/水分限制 | `fallback_fluxes.py` | `test_meteorology.py` | 有范围和单调性；无 Eq. (38)/(40) 独立基准 |
| 水桶/排水/径流 | `water_balance.py` | `test_balances.py` | 饱和溢流、径流、水量覆盖 |
| 土壤 HTO | `hto_balance.py`, `integrator.py` | `test_balances.py` | 面库存和箱室闭合覆盖；径流+雨水 HTO 缺失 |
| TFWT/OBT | `plant/*.py`, `integrator.py` | `test_plant_processes.py` | 转移、昼夜、叶片接口覆盖 |
| 三小时根延迟 | `case.py` | `test_short_case.py` | 只验证前 2 h TFWT 为零；未验证延迟后浓度/累计效应 |
| 基础/高级再释放 | `reemission/fluxes.py` | `test_reemission.py`, `test_balances.py` | 昼夜/ZT和箱室闭合；缺雨天、含水修正、模式对照 |
| 大气反馈 | `case.py` | 无专门测试 | 仅随端到端执行；无开/关、面积或时滞定量对比 |
| 连续参考/步长 | `reference_solver.py`, `integrator.py` | `test_reference_solver.py`, `test_timestep.py` | 单步参考和 2 h 步长回归 |
| 完整短案例/产物 | `case.py`, `outputs/*.py` | `test_short_case.py`, `verify_acceptance.py` | 测试只跑短片段；验收脚本校验已有产物而不重算 |

### 11.2 43 项测试的主类别

以下为每项测试只分配一个“主要目的”的互斥统计，避免重复计数：

| 主类别 | 数量 |
|---|---:|
| 纯执行/兼容性 | 2 |
| 数值范围/参考解 | 4 |
| 单位、映射和接口 | 11 |
| 物理单调性/不变量 | 16 |
| 地表箱室守恒 | 6 |
| 回归快照/步长 | 1 |
| 端到端 | 3 |
| **合计** | **43** |

### 11.3 指定高价值测试核对

| 测试主题 | 状态 |
|---|---|
| 零源项 | 有 Gaussian 单元测试；无完整系统零烟囱源案例 |
| 上风向 | 有 |
| 风向旋转 | 部分；只对西风/地理偏移做定量断言 |
| 极低风速 | 缺失 |
| 辐射累计重置 | 共用累计函数有测试；无专门净辐射重置案例 |
| 零 LAI | 有 |
| 高 LAI | 仅 LAI=3 单调性，不是边界/极值测试 |
| 萎蔫点 | 有低于萎蔫点案例 |
| 土壤饱和溢流 | 有 |
| OBT 转移守恒 | 有 |
| 再释放反馈关闭/开启 | 缺失；当前也没有明确 `off` 模式 |
| 高级模式昼夜切换 | 有通量级测试；无完整耦合切换定量测试 |
| 关闭所有内部交换后的独立守恒 | 有地表箱室测试；无全大气—地表域测试 |

### 11.4 实际重跑

- `pytest`：43 passed，0 failed，1 warning，real 1.06 s。
- 警告：NetCDF fixture 导入出现
  `numpy.ndarray size changed ... Expected 16 ... got 96`；当前不影响测试通过，
  但提示二进制依赖兼容性风险。
- `verify_acceptance.py`：三套案例产物均 PASS；该脚本只读取现有忽略目录中的
  CSV/PNG/报告，不重新运行模型，也不校验产物与 HEAD/config 的哈希关系。
- `compileall`：通过，real 0.06 s。

600 s 对 300 s 的完整 48 h 最终相对差异：

| 量 | 相对差异 |
|---|---:|
| soil HTO | 0.03898% |
| plant TFWT | 0.13154% |
| plant OBT | 0.11007% |
| total re-emission flux | 0.18287% |

## 12. 发现的问题与严重程度

| ID | 严重度 | 问题 | 对完成状态的影响 |
|---|---|---|---|
| A-01 | `HIGH` | 守恒诊断仅是地表三库存代数闭合，却在状态文档中未限定为 surface-box；不含烟囱源、空气库存、平流出域和面积反馈内部转移 | 必须修正文档并增加独立边界/全域或明确降级后的守恒测试 |
| A-02 | `HIGH` | 手册 Eq. (6) fallout/washout 耗减未实现，沉积不削弱高斯源强；映射/高斯 `PASS` 过强 | 在建立正式基线前应标为简化，并决定是否实现源耗减 |
| A-03 | `HIGH` | 极低正风速无下限，浓度随 \(1/u\) 无界；0 风速又直接为 0 | 真实 ERA5 calm 时段可能产生不稳定或非物理结果 |
| A-04 | `MEDIUM` | `runoff_enabled + rain HTO` 把径流部分的 HTO 计入土壤；零残差无法发现 | 修正入渗/径流 HTO 边界并加组合测试 |
| A-05 | `MEDIUM` | 面积反馈把代表性单列通量均匀复制到矩形；`feedback_area_m2` 与长宽可不一致且不报错 | 空间质量语义未闭合 |
| A-06 | `MEDIUM` | 反馈延迟默认 600 s，而手册明确一小时；文档仅称实现手册 sequencing | 应标为项目算子分裂或提供 1 h 配置/测试 |
| A-07 | `MEDIUM` | 顶层根系比例默认 1.0，而手册文字约 20%；差异未进入 assumptions | 显著影响 plant TFWT，应显式冻结为单层项目假设 |
| A-08 | `MEDIUM` | Eq. (40) 遮阴完整 Penman PET，而手册公式遮阴平衡辐射项 | 需选择并记录项目公式或调整实现/测试 |
| A-09 | `MEDIUM` | 高级 DIFF 不随水浓度修正、无专门雨天规则；只有数值闭合 | 保持 `PROVISIONAL`，不能声称 UFOTRI 等价 |
| A-10 | `MEDIUM` | 验收脚本只校验既有 ignored outputs，不能证明产物来自当前 HEAD | 正式基线需增加可重算或 provenance/hash 验收 |
| A-11 | `LOW` | `.gitignore` 未覆盖 `.cdsapirc` 和一般 credential 命名 | 增强防误提交规则 |
| A-12 | `LOW` | NetCDF 测试有 numpy 二进制兼容警告 | 升级/冻结依赖后复测 |
| A-13 | `INFORMATIONAL` | 仓库已有 5 个提交且 HEAD 已与 `origin/main` 对齐 | “建立初始提交”已不适用 |

最高严重度为 `HIGH`。没有发现会让当前三套默认短案例立即崩溃的 BLOCKER，
但 A-01 至 A-03 阻止无条件 `ACCEPT`。

## 13. 是否可建立初始提交

**不建议、且概念上已不适用。** 仓库已有 5 个提交，当前 HEAD 已在
`origin/main`。本次只读审计不提交、不推送。后续应先处理 HIGH 项和相应测试，
再以普通修复/文档提交建立“条件解除后的正式基线”，而不是创建所谓初始提交。

## 14. 下一阶段建议

优先级顺序：

1. 明确守恒域：把现有指标改名/文档化为 surface-box closure；增加独立边界项
   测试。若要声称全系统守恒，定义空气控制体、烟囱输入、平流/沉降/再释放及
   空间面积映射。
2. 冻结高斯简化契约：实现或明确排除 Eq. (6) fallout/washout；增加 calm/低风
   策略和测试。
3. 修复径流雨水 HTO 边界，加入“径流开启 + 非零雨水 HTO”守恒测试。
4. 冻结并文档化反馈面积、600 s/1 h 延迟、顶层根比例、Eq. (40) 解释。
5. 让验收命令能在临时输出目录重算三套轻量案例，记录 HEAD、配置摘要和输入
   provenance，而不是只检查已有 ignored artifacts。
6. 保持高级 REEM/DIFF/ZT 为 provisional，后续再做观测或手册参数基准。

在以上 1–4 完成并通过新增测试前，建议：

```text
complete = conditional / baseline candidate
```

而不是无条件：

```text
complete = 最小完整 HTO 大气—土壤—植物耦合系统已完成
```

## 15. 实际运行的命令

按要求运行：

```bash
pwd
git status --short
git branch --show-current
git log -1 --oneline
git diff --check
find . -maxdepth 3 -type f | sort
git ls-files
git ls-files | grep -Ei 'key|token|secret|credential|cdsapirc' || true
.venv/bin/python -m pytest --collect-only -q
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_acceptance.py
.venv/bin/python -m compileall -q src tests era5 scripts
git diff --check
```

另外运行了只读查询与内存诊断：

- `rg`/`sed`/`nl` 审阅手册、文档、源码、配置、测试和报告；
- 由当前代码在内存中重算 synthetic 600 s、synthetic 300 s、
  advanced 600 s 和 ERA5 600 s；
- 抽查四个基本风向、零风/极低风；
- 构造“径流开启 + 雨水 HTO”单步反例；
- 检查忽略文件、提交数和最近 5 个提交。

## 16. 最终字段

```text
AUDIT_VERDICT = ACCEPT_WITH_CONDITIONS
COMPLETE_SCOPE_VALID = PARTIAL_SCOPE_BOUNDARY_VALID_BUT_COMPLETE_EVIDENCE_CONDITIONAL
MANUAL_MAPPING_STATUS = PARTIAL_WITH_DOCUMENTED_AND_UNDOCUMENTED_SIMPLIFICATIONS
UNITS_STATUS = PASS_CORE_WITH_OPTIONAL_RUNOFF_RAIN_BOUNDARY_DEFECT
ERA5_STATUS = PASS_PROVISIONAL
GAUSSIAN_STATUS = CONDITIONAL_MISSING_DEPLETION_AND_CALM_WIND_HANDLING
SOIL_WATER_STATUS = PASS_CORE
SOIL_HTO_STATUS = CONDITIONAL_RUNOFF_RAIN_HTO_DEFECT
PLANT_TFWT_STATUS = PASS_PROJECT_SIMPLIFICATION
OBT_STATUS = PASS_PROJECT_SIMPLIFICATION
REEMISSION_STATUS = BASIC_PASS_ADVANCED_PROVISIONAL
ATMOSPHERIC_FEEDBACK_STATUS = CONDITIONAL_NOT_SPATIALLY_MASS_CLOSED
MASS_BALANCE_DIAGNOSTIC_STATUS = SURFACE_BOX_ALGEBRAIC_ONLY_NOT_WHOLE_DOMAIN
TEST_COVERAGE_STATUS = PARTIAL_43_PASS_WITH_HIGH_VALUE_GAPS
INITIAL_COMMIT_RECOMMENDATION = NOT_APPLICABLE_ALREADY_5_COMMITS
NEXT_STAGE_RECOMMENDATION = RESOLVE_HIGH_CONDITIONS_BEFORE_FORMAL_COMPLETE_BASELINE
```

## 17. Resolution status

The original findings above are retained unchanged. Resolution was evaluated
on branch `codex/formal-minimal-baseline-v1`.

| ID | Resolution | Evidence / remaining limitation |
|---|---|---|
| A-01 | RESOLVED | diagnostics renamed to surface-box closure; atmospheric source/sink ledger explicitly is not a dynamic inventory |
| A-02 | RESOLVED | dry segment-exponential depletion implemented as `PROJECT_SIMPLIFICATION`; wet scavenging remains absent |
| A-03 | RESOLVED | minimum-effective, skip, and error calm-wind modes tested and diagnosed |
| A-04 | RESOLVED | rainfall HTO uses infiltration only; runoff HTO is a recorded bypass |
| A-05 | RESOLVED | feedback rectangle is authoritative and inconsistent area configuration fails |
| A-06 | RESOLVED | feedback delay frozen at 3600 s and tested for 600/300 s steps |
| A-07 | DOCUMENTED_LIMITATION | single-layer fraction frozen at 1.0; not represented as manual multi-layer 20% |
| A-08 | RESOLVED | formal Eq. (40) mode shades the radiation term only |
| A-09 | DOCUMENTED_LIMITATION | advanced REEM/DIFF/ZT remains `PROVISIONAL` |
| A-10 | RESOLVED | `verify_acceptance.py --recompute` runs five cases in temporary output with provenance |
| A-11 | RESOLVED | `.cdsapirc` and common credential/token patterns added to `.gitignore` |
| A-12 | DOCUMENTED_LIMITATION | tests pass; existing NumPy/NetCDF binary-compatibility warning remains |

Resolution does not change the historical `ACCEPT_WITH_CONDITIONS` verdict of
this read-only audit; the post-resolution verdict is recorded separately in
`formal_minimal_baseline_v1_assessment.md`.

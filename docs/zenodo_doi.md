# Getting a permanent DOI for GPDI Analyzer (Zenodo + GitHub)

为什么需要：GitHub URL 会随分支、tag、账号变动而失效，也不被多数期刊视为
正式的软件引用。Zenodo 会给**某个具体 release** 打一个永久 DOI，审稿人点进去
拿到的就是论文用的那个 build。

---

## 0. 两种 DOI，别搞混

| 类型 | 形式 | 指向 | 论文里用哪个 |
|---|---|---|---|
| Version DOI | `10.5281/zenodo.22973905` | 固定的某一个版本（如 1.0.1） | **用这个**，可精确复现 |
| Concept DOI | `10.5281/zenodo.XXXXXXX` | 所有版本的最新版 | 想让读者拿最新版时用 |

论文正文 / 参考文献里写 **Version DOI**。README 可以两个都挂徽章。

**本项目的实际 DOI（2026-09-26 已归档）：**

| 类型 | DOI |
|---|---|
| Version DOI（v1.0.1） | `10.5281/zenodo.22973905` |
| Concept DOI | `10.5281/zenodo.22973904` |

归档页：<https://zenodo.org/records/22973905>

---

## 1. 前置条件（仓库侧已就绪）

| 项目 | 状态 |
|---|---|
| 正式 Release（`v1.0.1`，带 Windows zip） | 已发布 |
| `LICENSE`（MIT） | 已加入 |
| `CITATION.cff`（Zenodo 用它生成元数据） | 已加入，**作者/ORCID 待你确认** |
| 字表 `data/char_inventory.csv` 不在仓库 | 已确认（`.gitignore` 拦截） |
| — 且打包时也不再以明文形式进入安装包 | 2026-09-26 修复，见第 8 节 |

档案大小 46 MB，远低于 Zenodo 单文件 50 GB 上限。

---

## 2. 在 Zenodo 上操作（需要你本人登录，我无法代做）

1. 打开 <https://zenodo.org>，点右上角 **Log in** → 用 **GitHub** 账号登录
   （不要用邮箱注册，GitHub 登录才能连仓库）。
2. 登录后右上角头像 → **GitHub** → 进入仓库同步页面
   （或直接访问 <https://zenodo.org/account/settings/github/>）。
3. 首次使用会要求给 **Zenodo GitHub App** 授权；在 GitHub 页选择
   **Only select repositories** → 勾 `fancy61333/GPDI-Analyzer` → 保存。
4. 回到 Zenodo 的 GitHub 页面，找到该仓库，把开关拨到 **ON**（启用）。
5. （建议）头像 → **ORCID** → 关联你的 ORCID，这样 DOI 记录会自动带上
   作者标识，也让 DOI 能被你的 ORCID 主页收录。

---

## 3. 触发归档（顺序不能反）

**先完成第 2 节的 Zenodo 启用，再执行本节命令。** Zenodo 只对启用之后创建的
release 归档，启用之前就存在的 release 不会被回溯。

### 已定路线：归档 v1.0.1

v1.0.1 是与论文数值、band 切点、82/82 复现完全一致的版本，论文即引用
*GPDI Analyzer (Version 1.0.1)*。做法：删掉 GitHub 上的 release（**保留 tag**），
再用同一个 tag 重建，webhook 即触发归档。附件文件名不变，所以
`/releases/download/v1.0.1/GPDI-Analyzer-Windows-v1.0.1.zip` 重建后完全一样，
已写出去的链接不受影响。

本地附件 `dist/GPDI-Analyzer-Windows-v1.0.1.zip`（46.4 MB）已就位。命令：

```bash
export GH_CONFIG_DIR="D:/app/wampsever/.gh"
cd /d/app/wampsever/GPDI-Analyzer
"C:/Users/89351/gh-cli/bin/gh.exe" release delete v1.0.1 --yes --repo fancy61333/GPDI-Analyzer
"C:/Users/89351/gh-cli/bin/gh.exe" release create v1.0.1 \
  dist/GPDI-Analyzer-Windows-v1.0.1.zip \
  --title "GPDI Analyzer v1.0.1" \
  --notes-file dist/release_notes_v1.0.1.md \
  --repo fancy61333/GPDI-Analyzer
```

`gh release delete` 默认**不会**删除 git tag——不要加 `--cleanup-tag`。

### 备用路线：另发 v1.1.0

不想重建的话，可在 Zenodo 启用后直接新建 v1.1.0，Zenodo 会自动归档。此时论文
写 Version 1.1.0，`CITATION.cff` 的 `version` 也要同步改。v1.0.0 无论如何都不要
用：它的权重、band 切点与复现数都与论文不一致。

归档通常在几分钟内完成，Zenodo 的 GitHub 页面会显示状态；处理完会给
`10.5281/zenodo.XXXXXXX`（concept）和 `10.5281/zenodo.22973905`（version）。

### 实际发生了什么（2026-09-26）

- 开关拨到 ON 之后第一次重建 release **没有**被归档：Zenodo 只接收启用之后
  发生的 release 事件，启用那一刻它手里是空的，而重建动作发生在 webhook 建立
  之前。**又重建了一次**（`gh release delete v1.0.1 --yes` → `gh release create`）
  才接住，18 秒后状态变成 Received，随后 Published。
- Zenodo 归档的是**仓库在该 tag 处的源码快照**（`fancy61333/GPDI-Analyzer-v1.0.1.zip`，
  79 KB），**不包含** Release 里的那 46 MB 安装包。要让 DOI 直接给出可运行程序，
  需要按第 8 节把 zip 也挂进去。
- **`v1.0.1` 这个 tag 指向的提交早于 `LICENSE` 和 `CITATION.cff` 的加入**
  （tag → `7eeb00b`，两个文件是 9-26 才提交的），所以 Zenodo 没能读到
  `CITATION.cff`，只能用 GitHub 默认值：标题变成 `owner/repo: 标题`、作者取
  GitHub 账号名、许可默认成 CC-BY-4.0。**下一次发版时，务必确保 tag 打在包含
  `CITATION.cff` 的提交上。**

---

## 4. 拿到 DOI 后回填

已完成（2026-09-26）：

1. `CITATION.cff` → `identifiers` 已填入 version DOI 与 concept DOI；
   `affiliation` 与 `orcid` 仍待你确认。
2. `README.md` → 引用段已换成真实 DOI，标题下已挂 concept DOI 徽章。
3. `docs/zenodo_doi.md` → 本文件记下了实际流程与已知问题。

### 归档记录本身还需要修（Zenodo 网页上点 Edit，DOI 不变）

| 字段 | 现在是 | 应改为 |
|---|---|---|
| Title | `fancy61333/GPDI-Analyzer: GPDI Analyzer v1.0.1` | `GPDI Analyzer` |
| Creators | `Fancy-Fang`（GitHub 账号名） | 论文的作者署名（姓、名、单位、ORCID） |
| License | `CC-BY-4.0`（Zenodo 默认值） | `MIT`（与仓库 `LICENSE` 一致） |
| Version | `v1.0.1` | 保持（或去掉 `v`，统一即可） |
| Files | 仅源码快照 | 建议补上 Windows 安装包，见第 8 节 |

修改已发布记录的 metadata 不会改变 DOI，也不必重建 release。

---

## 5. 论文里的写法

APA（*System* 常用）：

> Wang, J. (2026). *GPDI Analyzer* (Version 1.0.1) [Computer software]. Zenodo.
> https://doi.org/10.5281/zenodo.22973905

BibTeX：

```bibtex
@software{gpdi_analyzer_2026,
  author  = {Wang, Junbo},
  title   = {GPDI Analyzer},
  version = {1.0.1},
  year    = {2026},
  publisher = {Zenodo},
  doi     = {10.5281/zenodo.22973905},
  url     = {https://github.com/fancy61333/GPDI-Analyzer}
}
```

正文脚注/数据可用性声明可写：

> The GPDI Analyzer software used in this study is archived at
> https://doi.org/10.5281/zenodo.22973905 (version 1.0.1); source code is
> available at https://github.com/fancy61333/GPDI-Analyzer.

---

## 6. 兜底：手动上传（webhook 一直没反应时）

判断标准：Zenodo 的 GitHub 页面里 GPDI-Analyzer 始终不出现归档记录，且公开接口
检索不到（<https://zenodo.org/api/records?q=GPDI>）。

步骤：New upload → 拖入 `dist/GPDI-Analyzer-Windows-v1.0.1.zip`（46.4 MB）→ 按下面填：

| 字段 | 值 |
|---|---|
| Title | GPDI Analyzer |
| Publication date | 2026-09-24 |
| Creators | Wang Junbo（附 affiliation、ORCID） |
| Resource type | Software |
| Version | 1.0.1 |
| License | MIT |
| Keywords | classical Chinese poetry; readability; text difficulty; graded vocabulary; Chinese as a second language; international Chinese language education; digital humanities |
| Related identifiers | `https://github.com/fancy61333/GPDI-Analyzer`（isSupplementTo）；`https://github.com/fancy61333/GPDI-Analyzer/releases/tag/v1.0.1`（isIdenticalTo） |

Description 用这段（与 `CITATION.cff` 保持一致）：

> GPDI Analyzer computes the Graded Poetry Difficulty Index (GPDI) for classical
> Chinese poetry. A poem is normalised to CJK characters, matched against a graded
> 3,500-character inventory (levels A–E, plus out-of-vocabulary), and scored on
> four components: normalised average character difficulty (ACD*), high-difficulty
> character ratio (HDCR), out-of-vocabulary ratio (OOVR) and normalised text
> length (TL*). GPDI = 100 × (0.45·ACD* + 0.25·HDCR + 0.20·OOVR + 0.10·TL*). The
> tool also reports the character-level component on its own scale, a per-character
> A–E / OOV profile, and the position of the text within a bundled 82-poem reference
> corpus. It ships as a desktop application (PySide6) for Windows and macOS and
> reproduces, for all 82 reference poems, every metric published in the
> accompanying study.

手动上传拿到的 DOI 与自动归档的引用效力完全相同；唯一差别是以后发新版本时要再
手动传一次，不会自动同步。

---

## 7. 后续版本怎么管

- 每次 `gh release create vX.Y.Z` → Zenodo 自动归档 → 新 version DOI。
- Concept DOI 永远不变，指向最新版。
- **论文锁死 version DOI**，之后发 v1.2、v2.0 都不影响论文可复现性。
- 归档一旦发布就不可删除（Zenodo 的长期保存承诺）；metadata 可随时在网页编辑。
- 发新版前记得把 `CITATION.cff` 的 `identifiers` 改成新版本 DOI，否则 GitHub 的
  “Cite this repository” 会一直显示旧版本。

---

## 8. 归档内容：只有源码，没有安装包

Zenodo 的 GitHub 集成归档的是 **tag 处的仓库源码快照**，Release 里上传的
附件（46 MB 的 Windows zip）**不会**被一起归档。因此单看 DOI，读者拿到的是
源码——而源码里没有字表（`data/char_inventory.csv` 被 `.gitignore` 排除），
所以**无法仅凭 DOI 跑出论文数值**，还得去 GitHub Releases 下安装包。

两种收尾方式：

1. **在归档记录里补挂安装包（推荐）**：Zenodo 记录页 → **Edit** → Files →
   上传 `dist/GPDI-Analyzer-Windows-v1.0.1.zip` → Publish。
   注意：给已发布记录增删文件会提示生成一个新版本，DOI 规则由 Zenodo 决定；
   如果它给出新 version DOI，就改引新的那个。
2. **在数据可用性声明里写清楚两层地址**，让读者知道去哪儿拿可执行的 build：

   > The GPDI Analyzer software is archived at
   > https://doi.org/10.5281/zenodo.22973905 (version 1.0.1) and the compiled
   > Windows build is available from
   > https://github.com/fancy61333/GPDI-Analyzer/releases/tag/v1.0.1.

---

## 9. 字表不能再以明文进入安装包（2026-09-26 修复）

**问题**：`build_windows.bat` / `build_macos.sh` 原来用 `--add-data "data;data"`，
把整个 `data/` 目录塞进包里，于是 `char_inventory.csv`（45 KB 明文、含
甲/乙/丙/丁/戊 标签）随公开发布的两版 Release 一起发了出去——下载 zip、解压、
双击就能用 Excel 打开整张 3500 字表。`.gitignore` 只挡住了仓库，没挡住安装包。

**修复**：新增 `tools/pack_inventory.py`，把字表打包成 `build_data/char_inventory.bin`
（魔数 `GPIN1` + zlib 压缩，3495 字，7.7 KB），并把公开的数据文件一起复制到
`build_data/`；三个构建入口全部改为指向 `build_data/`，`data/` 不再进包。
`core/gpdi.py` 的 `load_inventory()` 优先读 `.bin`，没有则回退 `.csv`，
所以源码环境下照旧可用。
`tests/test_inventory_pack.py` 作为守卫：一旦哪个构建脚本又指回 `data/`，测试即失败。

**边界要说清**：这是压缩，不是加密。解包后仍能用几行 Python 还原整张表。
它解决的是“随手下下来就能打开的表”，不是“任何情况下都拿不到”——后者在
客户端软件里做不到。

**已发布的 v1.0.0 / v1.0.1 附件仍含明文表**，如需清理，重打并 `--clobber` 覆盖即可
（GitHub 对已删除的附件不保证不可恢复，Zenodo 归档的源码快照里则没有该文件）。

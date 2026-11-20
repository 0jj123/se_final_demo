# 管院空間與排課系統（軟工期末專案）

使用技術：**FastAPI**（Python 網站框架）+ **PostgreSQL**（資料庫）

---

## 📋 分工

| 模組 | 負責人 | 你的分支名稱 | 你只改這些檔案 |
|---|---|---|---|
| 共用：帳號註冊、審核、登入 | | `feature/auth` | `routes/auth.py`、`templates/auth/` |
| 模組一：管院空間查詢 | | `feature/space` | `routes/space.py`、`templates/space/` |
| 模組二：空間/物品預約借用 | | `feature/booking` | `routes/booking.py`、`templates/booking/` |
| 模組三：志願排課 | | `feature/schedule` | `routes/schedule.py`、`templates/schedule/` |

> ⚠️ **只改自己模組的檔案。** 其他檔案要改之前，先在群組說。

---

## 💻 在哪裡打指令？

| 電腦 | 打開方式 |
|---|---|
| **Windows** | 用 **VS Code** 打開專案資料夾 → 上方選單 **Terminal（終端機）→ New Terminal**（預設是 PowerShell） |
| **Mac** | VS Code 同上，或開「終端機」App |

- 指令**一次打一行**，按 Enter
- 有分 **🪟 Windows** / **🍎 Mac** 的地方，照自己的電腦打；沒分的代表兩邊都一樣

---

## 🚀 第一次開始（新組員照順序做）

### 步驟 1：安裝需要的工具

| 工具 | 用途 | 🪟 Windows 安裝 | 🍎 Mac 安裝 |
|---|---|---|---|
| **PostgreSQL** | 資料庫 | 到 https://www.postgresql.org/download/windows/ 下載安裝檔，一直按 Next | `brew install postgresql@16` 再 `brew services start postgresql@16` |
| **Git** | 版本控制 | 到 https://git-scm.com/download/win 下載安裝，一直按 Next | `xcode-select --install` |
| **uv** | 執行 Python | 在 PowerShell 打下面那行 ⬇️ | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

🪟 Windows 安裝 uv：
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> ⚠️ **Windows 裝 PostgreSQL 時會要你設定密碼，一定要記下來！** 步驟 5 會用到。Port 用預設的 `5432` 不要改。
>
> ⚠️ 全部裝完後，**關掉 VS Code / 終端機再重開**，新指令才會生效。

**確認安裝成功**：依序打這兩行，都要顯示版本號：
```bash
git --version
```
```bash
uv --version
```

PostgreSQL 確認方式：
- 🪟 Windows：開始選單搜尋得到 **pgAdmin 4** 就代表有裝
- 🍎 Mac：`psql --version` 有顯示版本號

---

### 步驟 2：設定 git 的名字（只需做一次）

commit 時會用這個名字記錄是誰寫的，**請用自己的 GitHub 帳號和信箱**：

```bash
git config --global user.name "你的GitHub帳號"
```
```bash
git config --global user.email "你的GitHub信箱"
```

---

### 步驟 3：接受 repo 邀請

到你的**信箱**找 GitHub 寄來的邀請信，點 **Accept invitation**。

> 沒收到的話，請 repo 擁有者到 Settings → Collaborators 加你。

---

### 步驟 4：把專案下載到電腦

1. 移動到你想放專案的資料夾（例如「文件」）：
   ```bash
   cd ~/Documents
   ```
2. 下載專案：
   ```bash
   git clone https://github.com/0jj123/se_final_demo.git
   ```
   > 🔑 如果跳出 GitHub 登入視窗，選 **Sign in with your browser**，在瀏覽器登入並按授權即可。只需登入一次，之後會記住。
3. 進入專案資料夾：
   ```bash
   cd se_final_demo
   ```
4. 用 VS Code 打開這個資料夾（之後都在 VS Code 的終端機打指令）：
   ```bash
   code .
   ```

✅ 成功：VS Code 左邊看得到 `main.py`、`README.md`、`routes` 等檔案

> 📌 **之後所有指令都要在 `se_final_demo` 資料夾裡執行。**VS Code 打開這個資料夾後，新開的終端機就會自動在這裡。

---

### 步驟 5：建立自己的設定檔 `.env`

1. 複製範本：

   🪟 Windows：
   ```powershell
   Copy-Item .env.example .env
   ```
   🍎 Mac：
   ```bash
   cp .env.example .env
   ```

2. 在 VS Code 左邊檔案列表點開 `.env`

3. 把 `你的密碼` 改成**步驟 1 安裝 PostgreSQL 時設定的密碼**，`Ctrl+S` / `Cmd+S` 存檔

改完應該長這樣（假設密碼是 `abc123`）：
```
DATABASE_URL=postgresql://postgres:abc123@localhost:5432/se_final
SECRET_KEY=change-me
```

> ⚠️ 密碼裡如果有 `@`，要改寫成 `%40`。例如密碼 `abc@123` → 寫成 `abc%40123`
>
> ⚠️ 檔名必須是 `.env`，不能是 `.env.txt`（不要用記事本另存新檔）

---

### 步驟 6：建立資料庫

打這一行就會自動**建立資料庫 + 匯入所有資料表**：
```bash
uv run --with-requirements requirements.txt python init_db.py
```

> 第一次執行會下載套件，要等一下。

✅ 成功：
```
✅ 已建立資料庫 se_final
✅ 已匯入 schema.sql，目前的資料表： rooms, users
```

❌ `密碼錯誤` → 回步驟 5 檢查 `.env` 的密碼

❌ `連不上 PostgreSQL` → PostgreSQL 沒安裝或沒啟動，回步驟 1

---

### 步驟 7：啟動網站確認能跑

1. 啟動：
   ```bash
   uv run --with-requirements requirements.txt fastapi dev main.py
   ```
2. 等到出現 `Application startup complete`
3. 打開瀏覽器，前往 👉 http://127.0.0.1:8000
4. 確認上方導覽列「首頁、空間查詢、預約借用、排課」都點得開
5. 回到終端機按 `Ctrl + C` 關閉網站

> 🪟 Windows 第一次啟動如果跳出防火牆視窗，按「允許」。

---

### 步驟 8：建立你自己的分支

> 分支 = 你自己的工作區，在裡面改東西不會影響別人。

1. 建立並切換到你的分支（**名稱看最上面分工表**，下面以 `feature/booking` 為例）：
   ```bash
   git checkout -b feature/booking
   ```
2. 把分支上傳到 GitHub：
   ```bash
   git push -u origin feature/booking
   ```
   > 🔑 第一次 push 如果跳出 GitHub 登入視窗，選 **Sign in with your browser** 登入授權即可。
3. 確認目前在哪個分支：
   ```bash
   git branch
   ```
   ✅ 成功：你的分支前面有 `*` 號，例如 `* feature/booking`

> 💡 VS Code 左下角也會顯示目前所在的分支名稱。

🎉 **到這裡就完成了！之後都在自己的分支上寫程式。**

---

## 🔁 每天開發的流程

> 以下 git 指令 Windows / Mac 都一樣。

### A. 開始寫程式之前：先拿到別人的最新進度

每次開工都做一次，避免最後一次合併時衝突爆炸。

1. 切到 main：
   ```bash
   git checkout main
   ```
2. 下載最新版本：
   ```bash
   git pull
   ```
3. 切回自己的分支：
   ```bash
   git checkout feature/booking
   ```
4. 把 main 的新東西合併進來：
   ```bash
   git merge main
   ```
5. 如果有人改過 `schema.sql`，重新匯入資料表（重複執行沒關係）：
   ```bash
   uv run --with-requirements requirements.txt python init_db.py
   ```

---

### B. 寫完一小段功能：存檔上傳（commit + push）

1. 看看改了哪些檔案：
   ```bash
   git status
   ```
   > ⚠️ 如果清單裡出現 `.env`，**停下來**，不要上傳！（裡面有密碼）
2. 選擇要上傳的檔案（只加自己模組的）：
   ```bash
   git add routes/booking.py templates/booking/
   ```
3. 寫一段說明，記錄這次做了什麼：
   ```bash
   git commit -m "新增教室週借用狀況頁面"
   ```
4. 上傳到 GitHub：
   ```bash
   git push
   ```

📝 **commit 說明要寫清楚**（老師會看每個人的 commit 紀錄）：

| ❌ 不好 | ✅ 好 |
|---|---|
| `update` | `新增預約表單` |
| `push` | `修正借用時段重疊沒有擋下的問題` |
| `aaa` | `管理員審核頁面加上退件意見欄位` |

> 💡 小步 commit：做完一個小功能就 commit 一次，不要累積一整週才 commit。

---

### C. 一個功能完成：合併回 main（開 Pull Request）

1. 確認已經做完上面 B 的 push
2. 到 GitHub repo 網頁，點上方 **Pull requests**
3. 點綠色按鈕 **New pull request**
4. 左邊 `base` 選 **main**，右邊 `compare` 選**你的分支**
5. 點 **Create pull request**，寫一下做了什麼功能
6. 請一位組員看過，再按 **Merge pull request**
7. 在群組通知大家「我合併了」，大家各自做一次 **A 流程**

---

### D. 出現衝突（CONFLICT）怎麼辦

`git merge main` 時看到 `CONFLICT` 字樣，代表你和別人改到同一個地方。

1. 看是哪些檔案衝突：
   ```bash
   git status
   ```
   紅字 `both modified` 的就是衝突的檔案
2. 在 VS Code 打開那個檔案，會看到類似這樣：
   ```
   <<<<<<< HEAD
   你寫的內容
   =======
   別人寫的內容
   >>>>>>> main
   ```
   VS Code 上方會出現按鈕：**Accept Current**（留你的）/ **Accept Incoming**（留別人的）/ **Accept Both**（兩個都留）
3. 選好之後存檔
4. 告訴 git 已經解決：
   ```bash
   git add 衝突的檔案名稱
   ```
5. 完成合併：
   ```bash
   git commit -m "合併 main，解決衝突"
   ```

> ⚠️ 不確定要留哪段，**先問寫那段的組員**，不要直接刪掉別人的程式。

---

## 📁 專案結構

```
se_final_demo/
├── main.py            ← 把各模組接起來（共用，盡量不改）
├── db.py              ← 連資料庫（共用）
├── init_db.py         ← 建資料庫 + 匯入資料表（步驟 6 用）
├── schema.sql         ← 所有資料表（共用，各自在自己模組的區塊加表）
├── requirements.txt   ← 需要的 Python 套件
├── .env.example       ← 設定檔範本
├── .env               ← 你自己的密碼（不會上傳，每人自己建）
├── routes/            ← 後端程式
│   ├── auth.py        ← 登入登出
│   ├── space.py       ← 模組一
│   ├── booking.py     ← 模組二
│   └── schedule.py    ← 模組三
├── templates/         ← 網頁畫面（HTML）
│   ├── base.html      ← 全站共用：導覽列、配色
│   ├── index.html     ← 首頁
│   ├── auth/  space/  booking/  schedule/   ← 各模組自己的頁面
└── static/            ← CSS、圖片
```

### 網站、程式、資料庫的關係

```
瀏覽器 http://127.0.0.1:8000    ← 使用者看到的網站
          ↓
FastAPI（main.py、routes/）      ← 步驟 7 啟動的程式
          ↓
PostgreSQL 資料庫 se_final       ← 存資料的地方
          ↑
pgAdmin / Adminer / psql        ← 用來看資料表的工具（不是資料庫本身）
```

- **資料庫在每個人自己的電腦上**，GitHub 只存程式碼，所以每人都要做步驟 6
- 「DB 共用」= 大家用同一份 `schema.sql`；demo 時用一台電腦跑整合版
- 🪟 Windows 想看資料表：開 **pgAdmin 4** → Servers → PostgreSQL → Databases → `se_final` → Schemas → public → Tables

---

## 🛠️ 寫程式會用到的共用工具

### 檢查登入、權限
```python
from routes.auth import get_current_user, require_login

user = get_current_user(request)                    # 沒登入會得到 None
user = require_login(request)                       # 沒登入 → 擋下（401）
user = require_login(request, roles=("admin",))     # 不是管理員 → 擋下（403）
```

- 登入資訊格式：`{"id": 1, "username": "xxx", "role": "teacher"}`
- 角色只有三種：`admin`（管理員）、`teacher`（老師）、`user`（一般使用者）
- 帳號狀態：`pending`（待審核）、`approved`（已通過）

### 新增資料表
- 寫在 `schema.sql` 裡**自己模組的區塊**，用 `CREATE TABLE IF NOT EXISTS`
- 加完執行 `uv run --with-requirements requirements.txt python init_db.py` 更新
- 別人的資料表**只能讀取（SELECT）**，不要新增、修改或刪除

### 新增網頁
在 `templates/你的模組/` 建 HTML 檔，開頭固定這樣寫，就會自動套用共用導覽列：
```html
{% extends "base.html" %}
{% block title %}頁面標題{% endblock %}
{% block head %}<!-- 只給這頁用的 CSS -->{% endblock %}
{% block content %}
  <!-- 頁面內容寫這裡 -->
{% endblock %}
{% block scripts %}<!-- 只給這頁用的 JavaScript -->{% endblock %}
```

---

## 🎨 美編（畫面樣式）

| 想改什麼 | 改哪個檔案 | 影響範圍 |
|---|---|---|
| 首頁內容 | `templates/index.html` | 只有首頁 |
| 導覽列、全站配色、字體 | `templates/base.html` | ⚠️ **全站所有頁面** |
| 自己模組頁面的樣式 | 自己 HTML 的 `{% block head %}` | 只有自己的頁面 |
| 圖片、logo、CSS 檔 | 放進 `static/` | 看哪頁引用 |

- `base.html`、`index.html` 指定**一個人**負責，改之前在群組說
- 建議等功能都差不多完成，再統一調整整體風格

---

## ✅ 規則總整理

1. **不要直接在 main 上改**，在自己的 `feature/xxx` 分支開發
2. **只改自己模組的檔案**，共用檔案（`main.py`、`db.py`、`schema.sql`、`base.html`、`index.html`）改之前先在群組說
3. **`.env` 絕對不要上傳**（`git status` 看到 `.env` 就停下來）
4. **每次開工先做「A. 拿到別人的最新進度」**
5. **commit 小步、說明寫清楚**

---

## ❓ 常見問題

| 錯誤訊息 | 原因 | 解法 |
|---|---|---|
| `git` / `uv` 不是內部或外部命令（Windows）<br>`command not found`（Mac） | 沒安裝，或裝完沒重開 | 看步驟 1，裝完**關掉 VS Code 重開** |
| `Repository not found` / `Permission denied` / `403` | 沒接受邀請，或登入成別的 GitHub 帳號 | 看步驟 3；Windows 到「認證管理員」→ Windows 認證 → 刪掉 `git:https://github.com` 再重新登入 |
| `密碼錯誤` / `password authentication failed` | `.env` 密碼錯 | 看步驟 5 |
| `連不上 PostgreSQL` | PostgreSQL 沒裝或沒啟動 | 看步驟 1；🪟 Windows 開「服務」確認 `postgresql` 在執行中 |
| `database "se_final" does not exist` | 沒建資料庫 | 看步驟 6 |
| `KeyError: 'DATABASE_URL'` | 沒有 `.env` 檔 | 看步驟 5 |
| `Please tell me who you are` | git 沒設定名字 | 看步驟 2 |
| `Address already in use` | 網站已經在跑 | 去另一個終端機按 `Ctrl + C`，或關掉 VS Code 重開 |
| 網頁改了沒變 | 瀏覽器快取 | `Ctrl + Shift + R`（Mac：`Cmd + Shift + R`）強制重新整理 |

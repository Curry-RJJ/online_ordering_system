# 腾讯云 COS + CDN 接入说明（与仓库代码配合）

本文说明**你在腾讯云控制台与部署环境**需要完成的步骤；应用侧已通过环境变量 **`STATIC_CDN_BASE`** 将 `/static/images/...` 等路径拼成 CDN 绝对地址（见 `app/utils.py` 的 `public_asset_url`）。

---

## 1. 目标形态

- 浏览器请求的图片来源为：`https://你的CDN域名/static/images/...`（与仓库内相对路径一致）。
- 数据库仍保存 **`/static/images/...`**，不存完整域名，便于换 CDN 域名。
- **上传**：当前仍写入服务器 `./app/static/images/`（Docker 挂载卷）；你需**定期或一次性**将文件同步到 COS，使 CDN 可回源到 COS。

---

## 2. 腾讯云控制台（需你操作）

### 2.1 创建 COS 存储桶

1. 登录 [腾讯云 COS 控制台](https://console.cloud.tencent.com/cos)，创建存储桶。
2. **地域**建议与 CVM/容器同地域，降低回源延迟。
3. **访问权限**：若仅通过 CDN 访问，可按官方文档配置「公有读」或「CDN 回源私有桶 + 签名」（后者更复杂，小项目多用公有读 + CDN）。
4. **路径约定**：上传时保持与项目一致的前缀，例如桶内对象键为：  
   `static/images/dishes/xxx.jpg`  
   对应站点路径 `/static/images/dishes/xxx.jpg`，则 CDN 上完整 URL 为：  
   `https://CDN域名/static/images/dishes/xxx.jpg`。

### 2.2 开通 CDN 并绑定源站为 COS

1. 进入 [CDN 控制台](https://console.cloud.tencent.com/cdn)，**新增域名**（如 `img.你的域名.com`）。
2. **源站类型**选择 **COS 源**，选中上一步存储桶。
3. **HTTPS**：为 CDN 域名申请/托管证书（可腾讯云免费证书）。
4. **缓存配置**：对图片后缀（如 `jpg/png/webp`）设置较长缓存；更新图片时依赖**换文件名**或**提交刷新**（见下文）。

### 2.3 解析域名

- 在 DNS 将 CDN 域名 CNAME 到腾讯云分配的 CDN 地址（控制台有提示）。

---

## 3. 应用与部署（环境变量）

在 **`.env`** 或服务器环境中设置（**无尾斜杠**）：

```env
# 示例：CDN 加速域名根
STATIC_CDN_BASE=https://img.example.com
```

- `docker-compose.yml` 已把该变量传入 `web` 服务；修改后需 **`docker compose up -d` 重启 web**。
- 未设置时：行为与以前一致，图片仍为相对路径，由本站 Nginx/Flask 提供。

---

## 4. 把已有图片同步到 COS

任选其一：

- **控制台 / COSBrowser**：按目录上传 `app/static/images/` 下内容，对象键保持 `static/images/...`。
- **命令行**：使用 `coscmd` 或官方工具同步本地目录到桶前缀 `static/images/`。
- **仓库脚本（推荐，与路径约定一致）**：在项目根目录执行 Python 脚本，将 `app/static/images/**` 全部上传为 `static/images/**`。

### 4.1 使用 `scripts/sync_static_images_to_cos.py`

1. 安装依赖（与主项目共用 `requirements.txt` 时已包含 `cos-python-sdk-v5`）：  
   `pip install -r requirements.txt`
2. 使用**子账号**创建 API 密钥，授予该桶的**对象上传/读取**等最小权限；**不要把密钥提交到 Git**。
3. 设置环境变量（示例为香港地域、桶名需带 AppID，以你控制台为准）：

```env
COS_SECRET_ID=AKIDxxxxxxxx
COS_SECRET_KEY=xxxxxxxx
COS_REGION=ap-hongkong
COS_BUCKET=meituan-1416142652
```

`COS_BUCKET` 须为 **COS 控制台「存储桶名称」**（形如 `名称-AppID`），**只允许字母、数字、连字符 `-`**；不要加引号、不要写成 URL、不要用下划线 `_` 代替连字符。若 `.env` 里误加了成对引号，同步脚本会自动剥掉。

4. 在项目根目录执行：

```bash
# 仅列出将要上传的对象键，不实际上传
python scripts/sync_static_images_to_cos.py --dry-run

# 实际上传
python scripts/sync_static_images_to_cos.py
```

脚本会跳过以 `.` 开头的隐藏文件；本地目录默认 `app/static/images/`，可用 `--images-dir` 覆盖。

### 4.2 Windows PowerShell（本机执行脚本）

在项目根目录打开 PowerShell，按需执行（路径按你本机仓库位置修改）：

```powershell
Set-Location "d:\projects\online_ordering_system"
python -m pip install -r requirements.txt
```

仅演练（不需要 COS 密钥）：

```powershell
Set-Location "d:\projects\online_ordering_system"
python scripts\sync_static_images_to_cos.py --dry-run
```

实际上传：先在**当前会话**设置变量（勿把真实密钥提交到 Git；也可把 `COS_*` 写入本地 `.env` 后执行，脚本会尝试加载 `python-dotenv`）：

```powershell
Set-Location "d:\projects\online_ordering_system"

$env:COS_SECRET_ID = "你的SecretId"
$env:COS_SECRET_KEY = "你的SecretKey"
$env:COS_REGION = "ap-hongkong"
$env:COS_BUCKET = "meituan-1416142652"

python scripts\sync_static_images_to_cos.py
```

说明：PowerShell 5.x 用分号 `;` 串联命令；若 `python` 不可用可改用 `py -3`。

### 4.3 生产服务器（Docker Compose，`/opt/online_ordering_system`）

`docker-compose.yml` 已将 `COS_*` 从宿主机 `.env` 传入 `web` 容器。在服务器上把 `COS_SECRET_ID`、`COS_SECRET_KEY`、`COS_REGION`、`COS_BUCKET` 写入 **`.env`**（勿提交 Git）后执行：

```bash
cd /opt/online_ordering_system
docker compose up -d web
docker compose exec web python scripts/sync_static_images_to_cos.py --dry-run
docker compose exec web python scripts/sync_static_images_to_cos.py
```

容器内工作目录为 `/app`，挂载的 `./app/static/images` 即生产上传目录。

同步完成后，用浏览器直接访问一条：  
`https://你的CDN域名/static/images/logos/placeholder.png`  
确认 200 后再打开业务站并设置 `STATIC_CDN_BASE`。

---

## 5. 发版与缓存刷新

- **推荐**：新图片使用**新文件名**（项目上传已带时间戳/uuid），避免强依赖刷新。
- 若必须替换同路径文件：在 **CDN 控制台** 对该 URL 做 **缓存刷新**（或 API 调用刷新）。

---

## 6. 安全说明

- **不要把 COS SecretId/SecretKey 写进代码仓库**；若将来改为「服务端直传 COS」，应使用**子账号 + 最小权限 + 环境变量**。
- 当前实现仅为 **URL 前缀拼接**，不在仓库内保存云凭证。

---

## 7. 与性能文档的对应关系

详见 `docs/性能优化方案.md` §6.2；实施后在方案中勾选「COS/CDN」相关项并补充你的 CDN 域名（可选）。

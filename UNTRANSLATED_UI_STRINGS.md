# Antigravity 未汉化界面文案清单（校正版）

> 批量静态排查：扫描本机已安装客户端 `app.asar` 与 `language_server.exe` 内嵌的 JS/HTML，
> 逐条与当前 `locales/zh-CN.json`（2,816 条）和 `locales/patterns.json`（180 条规则）比对。
> 原始候选 782 条；复核时发现 **21 条已被现有词典精确覆盖**，已剔除并在附录 A 留档。

## 概览

- **原始候选**：782 条（界面文本 611、UI 属性 171）。
- **已由现有词典覆盖**：21 条（附录 A，无需再处理）。
- **当前明细**：761 条 = 建议补译 752 条 + 产品名 8 条 + 非文案 1 条。
- **路径约定**：`language_server.exe!main.js` 表示二进制内嵌压缩包中的成员；`app.asar!dist/xxx.js` 表示 ASAR 归档成员；行号为解压后源码中的实际行号。
- **类型/字段**：`界面文本` 为 JSX/HTML 文本节点；`UI属性 / 字段名` 为 `label`、`title`、`description`、`placeholder` 等 UI 属性。

> ⚠️ 译文为**建议值**。片段型条目（原文以 `(`、`,`、`:` 等结尾，或从句子中间开始）由渲染层文本节点拆分造成，
> 实际入库时可能与相邻词条拼接，建议按上下文复核后再写入 `locales/zh-CN.json`。

### `app.asar!dist/browserStream/browserViewerTabDriver.js`（3 条）

| 行号 | 原文 | 建议中文译文 | 类型/字段 |
| ---: | :--- | :--- | :--- |
| 150 | Failed to stop agent browser | 停止智能体浏览器失败 | UI属性 / message |
| 237 | Take control failed | 接管失败 | UI属性 / message |
| 290 | Browser control action failed | 浏览器控制操作失败 | UI属性 / message |

### `app.asar!dist/browserStream/capturePage.js`（1 条）

| 行号 | 原文 | 建议中文译文 | 类型/字段 |
| ---: | :--- | :--- | :--- |
| 214 | Capture session failed | 截图会话失败 | UI属性 / message |

### `app.asar!dist/computer/hud.js`（1 条）

| 行号 | 原文 | 建议中文译文 | 类型/字段 |
| ---: | :--- | :--- | :--- |
| 245 | AGY Desktop HUD | AGY 桌面 HUD | UI属性 / title |

### `app.asar!dist/computer/hudState.js`（2 条）

| 行号 | 原文 | 建议中文译文 | 类型/字段 |
| ---: | :--- | :--- | :--- |
| 20 | Agent idle | 智能体空闲 | UI属性 / text |
| 32 | AGY is controlling your Mac | AGY 正在控制你的 Mac | UI属性 / text |

### `app.asar!dist/computer/previewIpc.js`（1 条）

| 行号 | 原文 | 建议中文译文 | 类型/字段 |
| ---: | :--- | :--- | :--- |
| 100 | computer preview is not available | 计算机预览不可用 | UI属性 / message |

### `app.asar!dist/computerActuator/scriptRunner.js`（1 条）

| 行号 | 原文 | 建议中文译文 | 类型/字段 |
| ---: | :--- | :--- | :--- |
| 163 | another script is already running | 另一个脚本正在运行 | UI属性 / message |

### `app.asar!dist/remote/remoteManager.js`（5 条）

| 行号 | 原文 | 建议中文译文 | 类型/字段 |
| ---: | :--- | :--- | :--- |
| 346 | Choose another SSH config file | 选择其他 SSH 配置文件 | UI属性 / title |
| 1080 | Could not restart the SSH server | 无法重启 SSH 服务器 | UI属性 / title |
| 1429 | Microphone access | 麦克风访问 | UI属性 / title |
| 1638 | Shared home directory | 共享主目录 | UI属性 / title |
| 1662 | Restart SSH server | 重启 SSH 服务器 | UI属性 / title |

### `app.asar!dist/scriptJail.js`（2 条）

| 行号 | 原文 | 建议中文译文 | 类型/字段 |
| ---: | :--- | :--- | :--- |
| 508 | Script return value exceeded maximum size ( | 脚本返回值超过最大大小（ | UI属性 / errormessage |
| 869 | Script execution failed | 脚本执行失败 | UI属性 / errormessage |

### `app.asar!dist/wcvIpcHandlers.js`（1 条）

| 行号 | 原文 | 建议中文译文 | 类型/字段 |
| ---: | :--- | :--- | :--- |
| 380 | Send failed | 发送失败 | UI属性 / message |

### `language_server.exe!main.js`（735 条）

| 行号 | 原文 | 建议中文译文 | 类型/字段 |
| ---: | :--- | :--- | :--- |
| 1667 | Open in Cider | 在 Cider 中打开 | UI属性 / label |
| 1668 | Side Question Selection | 侧边提问选择 | UI属性 / label |
| 1669 | Select Sidebar Item 1 | 选择侧边栏项 1 | UI属性 / label |
| 1670 | Select Sidebar Item 2 | 选择侧边栏项 2 | UI属性 / label |
| 1670 | Select Sidebar Item 3 | 选择侧边栏项 3 | UI属性 / label |
| 1670 | Select Sidebar Item 4 | 选择侧边栏项 4 | UI属性 / label |
| 1670 | Select Sidebar Item 5 | 选择侧边栏项 5 | UI属性 / label |
| 1670 | Select Sidebar Item 6 | 选择侧边栏项 6 | UI属性 / label |
| 1670 | Select Sidebar Item 7 | 选择侧边栏项 7 | UI属性 / label |
| 1671 | Select Sidebar Item 8 | 选择侧边栏项 8 | UI属性 / label |
| 1671 | Select Sidebar Item 9 | 选择侧边栏项 9 | UI属性 / label |
| 1700 | Project 4K interface without developer tooling. | 项目 4K 界面，无需开发者工具。 | UI属性 / description |
| 4421 | Couldn't connect | 无法连接 | UI属性 / message |
| 5341 | Failed to encode image as PNG | 图像编码为 PNG 失败 | 界面文本 |
| 5573 | Link Settings | 链接设置 | UI属性 / label |
| 5582 | In review | 审核中 | 界面文本 |
| 5592 | Copy gh auth login command | 复制 gh auth login 命令 | 界面文本 |
| 5596 | Grant repository access | 授予仓库访问权限 | 界面文本 |
| 6225 | Failed to read file | 读取文件失败 | UI属性 / message |
| 6284 | Selected element preview | 所选元素预览 | 界面文本 |
| 6287 | Upload to Agent | 上传到智能体 | 界面文本 |
| 6344 | File exceeds the 200MB display limit, so it can't be opened or downloaded here. | 文件超过 200MB 显示限制，无法在此处打开或下载。 | 界面文本 |
| 7534 | script source must not be empty | 脚本内容不能为空 | UI属性 / message |
| 7696 | Web Preview | 网页预览 | 界面文本 |
| 7697 | Intended primarily for previewing local development servers (e.g., | 主要用于预览本地开发服务器（例如， | 界面文本 |
| 7698 | Embedding Limitations | 嵌入限制 | 界面文本 |
| 7698 | Many external websites (such as Google Search, GitHub, or Wikipedia) restrict iframe embedding via | 许多外部网站（如 Google Search、GitHub 或 Wikipedia）会通过以下方式限制 iframe 嵌入： | 界面文本 |
| 7699 | icon in the URL bar. | 地址栏中的图标。 | 界面文本 |
| 7702 | Taking longer than usual to load | 加载时间比平时更长 | 界面文本 |
| 7702 | This page is taking longer than expected to load, or it may be blocking embedded views (via X-Frame-Options or CSP). | 此页面加载时间超出预期，或者它可能阻止了嵌入视图（通过 X-Frame-Options 或 CSP）。 | 界面文本 |
| 7744 | You're viewing a blank page | 你正在查看空白页 | UI属性 / summary |
| 7744 | You're viewing a local or shared file | 你正在查看本地或共享文件 | UI属性 / summary |
| 7745 | Your connection to this site is not secure | 你与此站点的连接不安全 | UI属性 / summary |
| 7747 | Your connection to this site is not fully secure | 你与此站点的连接并非完全安全 | UI属性 / summary |
| 7748 | Connection is secure | 连接安全 | UI属性 / summary |
| 7750 | Connection security information is not available for this page | 此页面没有可用的连接安全信息 | UI属性 / summary |
| 7860 | Address bar suggestions | 地址栏建议 | 界面文本 |
| 7862 | Remove from history | 从历史记录中移除 | 界面文本 |
| 7866 | About embedding | 关于嵌入 | 界面文本 |
| 7892 | Show Error | 显示错误 | 界面文本 |
| 8019 | Not Found | 未找到 | 界面文本 |
| 8628 | This page is blocked in the built-in browser by your organization's Context-Aware Access policy. | 此页面已被你所在组织的 Context-Aware Access 政策在内置浏览器中屏蔽。 | 界面文本 |
| 8629 | Open the page in system browser | 在系统浏览器中打开此页面 | 界面文本 |
| 8630 | Attackers might be trying to steal your information from | 攻击者可能正试图从以下位置窃取你的信息： | 界面文本 |
| 8631 | (for example, passwords, messages, or credit cards). | （例如密码、消息或信用卡）。 | 界面文本 |
| 8632 | Back to safety | 返回安全页面 | 界面文本 |
| 8633 | Proceed to | 继续前往 | 界面文本 |
| 8633 | normally uses encryption to protect your information. When the browser tried to connect to | 通常会使用加密来保护你的信息。当浏览器尝试连接到 | 界面文本 |
| 8633 | this time, the website sent back unusual and incorrect credentials. | 时，该网站返回了异常且不正确的凭据。 | 界面文本 |
| 9077 | An error was thrown. | 出现了错误。 | 界面文本 |
| 9201 | No compatible devices found. | 未找到兼容的设备。 | 界面文本 |
| 9224 | Certificate details | 证书详情 | 界面文本 |
| 9225 | Issued by | 颁发者 | 界面文本 |
| 9225 | Issued to | 颁发给 | 界面文本 |
| 9225 | Valid until | 有效期至 | 界面文本 |
| 9232 | Clearing cookies and site data for | 正在清除以下站点的 Cookie 和网站数据： | 界面文本 |
| 9232 | may sign you out of this site. | 可能会使你从此站点退出登录。 | 界面文本 |
| 9233 | Could not clear site data for | 无法清除以下站点的网站数据： | 界面文本 |
| 9233 | Site data cleared for | 已清除以下站点的网站数据： | 界面文本 |
| 9249 | Close downloads | 关闭下载内容 | 界面文本 |
| 9250 | No recent downloads | 没有最近的下载 | 界面文本 |
| 9260 | Resume 1 comment draft | 继续编辑 1 条评论草稿 | 界面文本 |
| 9468 | Loading preview… | 正在加载预览… | 界面文本 |
| 9472 | Copied to clipboard | 已复制到剪贴板 | 界面文本 |
| 9495 | Enable Browser Agent | 启用浏览器智能体 | UI属性 / label |
| 9610 | Toggle Google Cloud projects | 切换 Google Cloud 项目 | 界面文本 |
| 9831 | QR code | 二维码 | 界面文本 |
| 9965 | Browsing Data | 浏览数据 | UI属性 / label |
| 9965 | Clear history, cookies and site data from the built-in browser, or manage cookies for each site. | 清除内置浏览器的历史记录、Cookie 和网站数据，或管理各站点的 Cookie。 | UI属性 / description |
| 9966 | Clear Browsing Data? | 清除浏览数据？ | UI属性 / title |
| 9966 | Cookies by Site | 按站点划分的 Cookie | UI属性 / title |
| 9967 | Choose what to clear from the built-in browser. It can't be undone. | 选择要从内置浏览器中清除的内容。此操作无法撤销。 | 界面文本 |
| 9968 | Cookies and other site data | Cookie 及其他网站数据 | 界面文本 |
| 9968 | Cookies, site storage and cache. Signs you out of all sites in the built-in browser and reloads its open tabs. | Cookie、网站存储和缓存。将使你退出内置浏览器中的所有站点，并重新加载其打开的标签页。 | 界面文本 |
| 9968 | Visited URLs and autocomplete suggestions. | 访问过的 URL 和自动补全建议。 | 界面文本 |
| 9969 | An agent is using the built-in browser. Clearing its data signs the agent out of sites and may interrupt its task. | 某个智能体正在使用内置浏览器。清除其数据将使该智能体退出各站点，并可能中断其任务。 | 界面文本 |
| 9969 | Couldn't clear browsing data. Try again. | 无法清除浏览数据，请重试。 | 界面文本 |
| 9973 | Loading cookies… | 正在加载 Cookie… | 界面文本 |
| 9974 | Couldn't load cookies. | 无法加载 Cookie。 | 界面文本 |
| 9974 | No sites have cookies in the built-in browser. | 内置浏览器中没有任何站点保存了 Cookie。 | 界面文本 |
| 9975 | Couldn't delete cookies for | 无法删除以下站点的 Cookie： | 界面文本 |
| 9975 | No sites match “ | 没有站点匹配“ | 界面文本 |
| 9975 | Sites with cookies | 保存了 Cookie 的站点 | 界面文本 |
| 9978 | Search sites... | 搜索站点... | UI属性 / placeholder |
| 9979 | e.g., example.com | 例如 example.com | UI属性 / placeholder |
| 9995 | Not referenced by any feature ( | 未被任何功能引用（ | 界面文本 |
| 9998 | Web (desktop, remote agents) | Web（桌面端、远程智能体） | UI属性 / label |
| 9998 | Web (desktop, remote agents, PWA) | Web（桌面端、远程智能体、PWA） | UI属性 / label |
| 9999 | Web (mobile, remote agents) | Web（移动端、远程智能体） | UI属性 / label |
| 9999 | Web (mobile, remote agents, PWA) | Web（移动端、远程智能体、PWA） | UI属性 / label |
| 10005 | Default (Mendel) | 默认（Mendel） | UI属性 / label |
| 10005 | Run Jetski Live on the ELMO composite voice actor. | 在 ELMO 合成配音角色上运行 Jetski Live。 | UI属性 / description |
| 10005 | Type a voice variant name, such as rev27. | 输入语音变体名称，例如 rev27。 | UI属性 / description |
| 10005 | Whatever the voice-engine-addr flag serves you. | 使用 voice-engine-addr 标志提供的地址。 | UI属性 / description |
| 10007 | Voice engine address | 语音引擎地址 | 界面文本 |
| 10020 | No diagnostics main service found | 未找到诊断主服务 | 界面文本 |
| 10202 | Antigravity (AGY) Style | Antigravity (AGY) 样式 | UI属性 / label |
| 10202 | VS Code Default | VS Code 默认 | UI属性 / label |
| 10205 | Choose between non-colliding VS Code defaults or standalone Antigravity chords. | 可在不与现有快捷键冲突的 VS Code 默认方案和独立的 Antigravity 组合键之间选择。 | UI属性 / subtitle |
| 10205 | Keybinding Scheme | 快捷键方案 | UI属性 / title |
| 10205 | Manage your keybinding scheme and customize shortcuts in VS Code. | 在 VS Code 中管理快捷键方案并自定义快捷方式。 | UI属性 / description |
| 10208 | All active Antigravity shortcuts and user keybinding overrides are managed directly by VS Code. | 所有生效的 Antigravity 快捷键和用户自定义键位均由 VS Code 直接管理。 | UI属性 / subtitle |
| 10208 | Customize Shortcuts | 自定义快捷键 | UI属性 / title |
| 10209 | Inspect live bindings or record custom key chords filtered to | 查看当前生效的绑定或录制自定义组合键（筛选范围为 | 界面文本 |
| 10209 | VS Code Keyboard Shortcuts | VS Code 键盘快捷方式 | 界面文本 |
| 10241 | Terminal: Select All | 终端：全选 | UI属性 / label |
| 10336 | Powered by Gemini Live · | 由 Gemini Live 提供支持 · | 界面文本 |
| 10336 | You can change this in | 你可以在以下位置更改： | 界面文本 |
| 10403 | cloud permission preset value | 云端权限预设值 | 界面文本 |
| 10412 | sandbox mode boolean value | 沙箱模式布尔值 | 界面文本 |
| 10483 | Must be positive | 必须为正数 | 界面文本 |
| 10579 | e.g. work | 例如 work | UI属性 / placeholder |
| 10667 | Connect your account to browse | 连接你的账号以浏览 | 界面文本 |
| 10667 | Loading resources... | 正在加载资源... | 界面文本 |
| 10678 | Missing a repository? Configure on GitHub | 缺少仓库？在 GitHub 上配置 | 界面文本 |
| 10688 | Remove resource | 移除资源 | 界面文本 |
| 10698 | Avoid uploading highly sensitive data and verify actions taken by your agent. Make sure you have the | 避免上传高度敏感数据，并核实你的智能体所执行的操作。请确保你已阅读 | 界面文本 |
| 10699 | Prohibited Use Policy | 禁止使用政策 | 界面文本 |
| 10700 | Google Antigravity Terms of Service | Google Antigravity 服务条款 | 界面文本 |
| 10700 | Google Privacy Policy | Google 隐私权政策 | 界面文本 |
| 10706 | Edit title | 编辑标题 | 界面文本 |
| 10715 | Are you sure you want to delete the | 确定要删除 | 界面文本 |
| 10715 | This will permanently delete | 这将永久删除 | 界面文本 |
| 10715 | within it. | 其中的内容。 | 界面文本 |
| 10731 | with this name already exists. | 同名项已存在。 | 界面文本 |
| 10736 | is managed by the | 由自动化管理， | 界面文本 |
| 10737 | automation and can only be deleted by deleting that automation. | 且只能通过删除该自动化来删除。 | 界面文本 |
| 10858 | Nothing said yet | 尚无发言内容 | 界面文本 |
| 10999 | Cannot enable accessibility before Terminal.open | 无法在 Terminal.open 之前启用辅助功能 | 界面文本 |
| 11646 | Failed to revert conversation | 恢复对话失败 | UI属性 / title |
| 11676 | StatusBarComponent context not provded | StatusBarComponent 上下文未提供 | 界面文本 |
| 11837 | Conversation is not open in this Hub window | 此 Hub 窗口中未打开对话 | UI属性 / errormessage |
| 11905 | The Hub sent an unexpected response. | Hub 返回了意外的响应。 | UI属性 / message |
| 11911 | Remove from Recent | 从最近使用项中移除 | UI属性 / tooltip |
| 11914 | Then create the project in its window. | 然后在其窗口中创建项目。 | 界面文本 |
| 11918 | Couldn't connect to | 无法连接到 | 界面文本 |
| 11920 | Hidden hosts | 隐藏的主机 | 界面文本 |
| 11920 | Loading hosts… | 正在加载主机… | 界面文本 |
| 11921 | No hosts in | 以下位置没有主机： | 界面文本 |
| 11923 | Choose File… | 选择文件… | 界面文本 |
| 11924 | Use Default | 使用默认值 | 界面文本 |
| 11962 | Describe your changes | 描述你的更改 | 界面文本 |
| 12008 | Please verify your account to continue using | 请验证你的账号以继续使用 | 界面文本 |
| 12009 | Your session has expired. Please log back in to continue. | 登录会话已过期，请重新登录以继续。 | UI属性 / message |
| 12010 | See our | 请参阅我们的 | 界面文本 |
| 12035 | This may take a few minutes | 这可能需要几分钟 | 界面文本 |
| 12045 | System default app | 系统默认应用 | UI属性 / label |
| 12087 | This link wants to open an app on your device. | 此链接想要在你的设备上打开一个应用。 | 界面文本 |
| 12088 | Always open | 始终打开 | 界面文本 |
| 12089 | Open link | 打开链接 | 界面文本 |
| 12095 | This project uses Firebase. Do you want to download the Firebase skill? | 此项目使用了 Firebase。是否下载 Firebase 技能？ | 界面文本 |
| 12096 | Error occurred during import. | 导入过程中发生错误。 | 界面文本 |
| 12314 | Image rendering blocked (strict mode enabled) | 图片渲染已被阻止（已启用严格模式） | 界面文本 |
| 12315 | Image URL: | 图片 URL： | 界面文本 |
| 12370 | Markdown view mode | Markdown 视图模式 | 界面文本 |
| 12371 | Insert in terminal | 在终端中插入 | 界面文本 |
| 12372 | At mention code block | 提及 (@) 代码块 | 界面文本 |
| 12372 | Insert in Terminal | 在终端中插入 | 界面文本 |
| 12373 | At Mention Code Block | @ 提及代码块 | 界面文本 |
| 12373 | Copy code | 复制代码 | 界面文本 |
| 12374 | Canvas page · display only | 画布页面 · 仅显示 | 界面文本 |
| 12412 | Failed to load media | 加载媒体失败 | 界面文本 |
| 12431 | Copy as Markdown | 复制为 Markdown | 界面文本 |
| 12431 | Preview unavailable | 预览不可用 | 界面文本 |
| 12435 | Artifact image | Artifact 图片 | 界面文本 |
| 12435 | Open image preview | 打开图片预览 | 界面文本 |
| 12438 | Media actions | 媒体操作 | 界面文本 |
| 13252 | Not available | 不可用 | 界面文本 |
| 13254 | Image preview not available | 图片预览不可用 | 界面文本 |
| 13961 | Open Source Code | 打开源代码 | 界面文本 |
| 13961 | Preview disabled (experiment off) | 预览已禁用（实验已关闭） | 界面文本 |
| 13965 | Chief of Staff canvas | 参谋长画布 | UI属性 / title |
| 13968 | Markdown components must render within a CustomMarkdown. | Markdown 组件必须在 CustomMarkdown 中渲染。 | 界面文本 |
| 14043 | Reopen ↗ | 重新打开 ↗ | UI属性 / text |
| 14043 | Settings ↗ | 设置 ↗ | UI属性 / text |
| 14046 | Already on? Select | 已开启？请选择 | 界面文本 |
| 14046 | In System Settings, click | 在“系统设置”中，点击 | 界面文本 |
| 14046 | In System Settings, turn on | 在“系统设置”中，开启 | 界面文本 |
| 14051 | Enable macOS Permissions | 启用 macOS 权限 | 界面文本 |
| 14053 | Relaunch ↻ | 重新启动 ↻ | 界面文本 |
| 14054 | Continue Task → | 继续任务 → | 界面文本 |
| 14060 | Error while editing | 编辑时出错 | 界面文本 |
| 14060 | Error while viewing | 查看时出错 | 界面文本 |
| 14061 | Error while editing notebook | 编辑笔记本时出错 | 界面文本 |
| 14061 | Error while reading notebook | 读取笔记本时出错 | 界面文本 |
| 14069 | Error ID: | 错误 ID： | 界面文本 |
| 14172 | Confirmation required to execute this step | 执行此步骤需要确认 | 界面文本 |
| 14180 | Captured DOM tree for | 已捕获以下目标的 DOM 树： | 界面文本 |
| 14180 | Fetched network request for page. | 已获取该页面的网络请求。 | 界面文本 |
| 14180 | Fetched network requests for page. | 已获取该页面的多个网络请求。 | 界面文本 |
| 14181 | Agent can scroll on browser pages to access more content. | 智能体可以在浏览器页面上滚动以查看更多内容。 | 界面文本 |
| 14181 | Error rendering playback | 渲染回放时出错 | 界面文本 |
| 14181 | Rendering playback | 正在渲染回放 | 界面文本 |
| 14182 | Playback available | 回放可用 | 界面文本 |
| 14183 | The agent will wait for you to install the browser extension. | 智能体将等待你安装浏览器扩展。 | 界面文本 |
| 14190 | Manually Captured | 手动捕获 | 界面文本 |
| 14191 | Cancel Step | 取消步骤 | 界面文本 |
| 14191 | Cancel step | 取消步骤 | 界面文本 |
| 14198 | Unknown Notebook | 未知笔记本 | 界面文本 |
| 14199 | Notebook execution not implemented | 笔记本执行功能尚未实现 | UI属性 / errormessage |
| 14201 | Go to | 前往 | 界面文本 |
| 14201 | Select the latest snapshot from the | 从中选择最新的快照： | 界面文本 |
| 14202 | Open search in external browser | 在外部浏览器中打开搜索 | 界面文本 |
| 14208 | Browser steps | 浏览器步骤 | 界面文本 |
| 14219 | Browser task still running… | 浏览器任务仍在运行… | 界面文本 |
| 14219 | Loading browser steps… | 正在加载浏览器步骤… | 界面文本 |
| 14219 | No browser steps recorded | 未记录任何浏览器步骤 | 界面文本 |
| 14224 | Browser screenshot | 浏览器截图 | 界面文本 |
| 14224 | Open browser screenshot | 打开浏览器截图 | 界面文本 |
| 14273 | Generated media | 生成的媒体 | 界面文本 |
| 14300 | Tool Output | 工具输出 | 界面文本 |
| 14301 | Full output written to | 完整输出已写入： | 界面文本 |
| 14324 | Method not found | 未找到方法 | UI属性 / message |
| 14393 | Could not create Cog workspace | 无法创建 Cog 工作区 | UI属性 / title |
| 14540 | AI Credits are used when you've exceeded your model quota. Keep track of your current AI Credits in the | 当超出模型配额时，将使用 AI Credits。可在以下位置查看当前的 AI Credits | 界面文本 |
| 14540 | Models Tab | 模型标签页 | 界面文本 |
| 14540 | Open System Browser | 打开系统浏览器 | 界面文本 |
| 14546 | Page contents | 页面内容 | 界面文本 |
| 14549 | Read URL rejected | 读取 URL 被拒绝 | 界面文本 |
| 14553 | This command ran in the sandbox. | 此命令在沙箱中运行。 | 界面文本 |
| 14555 | Failed to parse URL in ImageAnswer: | 解析 ImageAnswer 中的 URL 失败： | 界面文本 |
| 14556 | Document Answers | 文档回答 | 界面文本 |
| 14557 | Image Answers | 图片回答 | 界面文本 |
| 14565 | Semantic searched | 已进行语义搜索 | 界面文本 |
| 14570 | Analyzed Task Log | 已分析任务日志 | 界面文本 |
| 14575 | Checked command status | 已检查命令状态 | 界面文本 |
| 14577 | Error Details: | 错误详情： | 界面文本 |
| 14580 | Analyzed content | 已分析内容 | 界面文本 |
| 14581 | A chunk is a section of the page. Long pages are chunked so that only the sections that are relevant to your query are read. | 块是页面的一部分。长页面会被分块，以便仅读取与你的查询相关的部分。 | 界面文本 |
| 14581 | In this case, | 在本例中， | 界面文本 |
| 14590 | No content available for this resource | 此资源没有可用内容 | 界面文本 |
| 14590 | Some non-image binary content was truncated. | 部分非图片二进制内容已被截断。 | 界面文本 |
| 14592 | Unnamed resource | 未命名资源 | 界面文本 |
| 14593 | Show all resources | 显示所有资源 | 界面文本 |
| 14595 | Found references to | 找到对以下内容的引用： | 界面文本 |
| 14608 | Inspected commit | 已检查提交 | 界面文本 |
| 14611 | Web search prioritized results from | 网页搜索优先采用了以下来源的结果： | 界面文本 |
| 14614 | Failed to parse URL in ReadUrlContentTitle: | 解析 ReadUrlContentTitle 中的 URL 失败： | 界面文本 |
| 14614 | Read page | 读取页面 | 界面文本 |
| 14617 | Long pages like this one will be broken down into outlines and read as needed. Read more at our | 像这样的长页面将被拆分为大纲并按需读取。更多信息请参阅我们的 | 界面文本 |
| 14617 | Page was short enough to be read as a single document. | 页面足够短，可作为单个文档读取。 | 界面文本 |
| 14628 | Model Summarization Failed | 模型总结失败 | 界面文本 |
| 14629 | Fallback Summary Used | 已使用备用总结 | 界面文本 |
| 14629 | User Intent | 用户意图 | 界面文本 |
| 14630 | Code Change Summary | 代码更改摘要 | 界面文本 |
| 14630 | Session Summary | 会话摘要 | 界面文本 |
| 14642 | Generation Steps ( | 生成步骤 ( | 界面文本 |
| 14643 | Knowledge Generation | 知识生成 | 界面文本 |
| 14649 | Wait for | 等待 | 界面文本 |
| 14659 | Failed to send command input | 发送命令输入失败 | 界面文本 |
| 14659 | Send command input? | 发送命令输入？ | 界面文本 |
| 14698 | Failed to fork conversation | 派生会话失败 | UI属性 / title |
| 14699 | Fork Conversation | 派生会话 | 界面文本 |
| 14701 | The main conversation's input isn't available right now. | 主会话的输入当前不可用。 | UI属性 / title |
| 14710 | Insert into main conversation | 插入到主会话 | 界面文本 |
| 14726 | No rate card for this model; showing comparable rates. | 此模型没有费率表；显示的是相近费率。 | 界面文本 |
| 14730 | cumulative total for the conversation up to this point | 截至目前该会话的累计总量 | 界面文本 |
| 14732 | Pricing is based on public API pricing | 价格基于公开 API 定价 | 界面文本 |
| 14736 | Click to view more | 点击查看更多 | 界面文本 |
| 14742 | Trajectory ID: | 轨迹 ID： | 界面文本 |
| 14743 | (Specific to this client's truncation and pagination) | （特定于此客户端的截断与分页） | 界面文本 |
| 14743 | Agent ID: | 智能体ID： | 界面文本 |
| 14743 | Trajectory Stats | 运行轨迹统计 | 界面文本 |
| 14744 | Cleared Count | 清除次数 | 界面文本 |
| 14746 | Admin escalation | 管理员升级 | UI属性 / label |
| 14746 | Browser actions | 浏览器操作 | UI属性 / label |
| 14746 | Browser downloads | 浏览器下载 | UI属性 / label |
| 14746 | Unsandboxed commands | 非沙箱命令 | UI属性 / label |
| 14755 | This extension has no declared permissions requiring user input. | 此扩展未声明任何需要用户输入的权限。 | 界面文本 |
| 14755 | needs a few details from you before it can run. | 运行前需要你提供一些信息。 | 界面文本 |
| 14757 | No folder selected | 未选择文件夹 | 界面文本 |
| 14759 | Next: Review Permissions | 下一步：检查权限 | 界面文本 |
| 14760 | Agents created by | 由以下对象创建的智能体： | 界面文本 |
| 14760 | Resolving permissions... | 正在解析权限... | 界面文本 |
| 14760 | with its own permissions, which you can change anytime in the | 拥有自己的权限，你可以随时在以下位置更改 | 界面文本 |
| 14762 | ? This action cannot be undone. | ？此操作无法撤销。 | 界面文本 |
| 14762 | Are you sure you want to delete | 确定要删除 | 界面文本 |
| 14765 | Manage Permissions | 管理权限 | 界面文本 |
| 14765 | Run Now | 立即运行 | 界面文本 |
| 14772 | Command execution | 命令执行 | 界面文本 |
| 14780 | Sidecar error | Sidecar 错误 | 界面文本 |
| 14781 | This sidecar failed to start. | 此 Sidecar 启动失败。 | 界面文本 |
| 14826 | Show submitted ( | 显示已提交 ( | 界面文本 |
| 14827 | Show more ( | 显示更多 ( | 界面文本 |
| 14853 | Type to search file contents | 输入以搜索文件内容 | 界面文本 |
| 14872 | Disk is full. Search will no longer match in conversation bodies until you clear up space and restart. | 磁盘已满。在清理空间并重启之前，搜索将不再匹配会话正文。 | 界面文本 |
| 14877 | Sort and filter conversations | 排序和筛选会话 | 界面文本 |
| 14880 | Recent Conversations | 最近的会话 | 界面文本 |
| 14912 | Couldn't mark conversations as read | 无法将会话标记为已读 | UI属性 / title |
| 14917 | Terms and Privacy: | 条款与隐私： | 界面文本 |
| 14918 | Privacy Notice | 隐私声明 | 界面文本 |
| 14919 | Customize your experience across the agent, plugins, and product from the settings and marketplace. We won’t show you ads or let advertisers influence what | 你可以在设置和市场自定义智能体、插件及产品的体验。我们不会向你展示广告，也不会让广告主影响你所看到的内容 | 界面文本 |
| 14919 | Optimized for you | 为你优化 | UI属性 / title |
| 14920 | Built to help, not hurt | 旨在提供帮助，而非伤害 | UI属性 / title |
| 14921 | does not collect any of your prompts, content, or model responses but will still collect general usage patterns (e.g., feature adoption, active user counts). | 不会收集你的任何提示词、内容或模型回复，但仍会收集一般使用模式（例如功能采用情况、活跃用户数）。 | 界面文本 |
| 14922 | Allow Google to collect and use your Interactions data, subject to the | 允许 Google 收集和使用你的互动数据，但须遵守 | 界面文本 |
| 14934 | Get started | 开始使用 | 界面文本 |
| 14934 | to switch to the Gemini app. Your agents keep working in the background. | 以切换到 Gemini 应用。你的智能体会在后台继续工作。 | 界面文本 |
| 14935 | Please sign in using the Antigravity sidebar panel to view this page. | 请使用 Antigravity 侧边栏面板登录以查看此页面。 | 界面文本 |
| 14946 | Access restricted | 访问受限 | 界面文本 |
| 15364 | Could not load | 无法加载 | 界面文本 |
| 15395 | Close references | 关闭引用 | 界面文本 |
| 15404 | Fold code block | 折叠代码块 | 界面文本 |
| 15501 | Artifact updated by agent | Artifact 已由智能体更新 | 界面文本 |
| 15501 | Dismiss artifact update notice | 关闭 Artifact 更新通知 | 界面文本 |
| 15501 | This side question isn't available in this conversation. | 此旁支问题在当前会话中不可用。 | UI属性 / title |
| 15514 | Failed to export artifact | 导出 Artifact 失败 | UI属性 / title |
| 15517 | Link copied to clipboard. | 链接已复制到剪贴板。 | UI属性 / message |
| 15529 | Failed to load image | 加载图片失败 | 界面文本 |
| 15637 | Unable to resolve audio source URL | 无法解析音频源 URL | 界面文本 |
| 15642 | Unable to load PDF: | 无法加载 PDF： | 界面文本 |
| 15649 | View could not be opened | 无法打开视图 | 界面文本 |
| 15699 | For Turn | 针对回合 | 界面文本 |
| 15703 | Typing your corp password here may trigger a Password Alert reset. | 在此输入公司密码可能会触发 Password Alert 重置。 | 界面文本 |
| 15704 | Don't enter corp passwords | 请勿输入公司密码 | 界面文本 |
| 15707 | Add Terminal | 添加终端 | 界面文本 |
| 15736 | File path breadcrumbs | 文件路径面包屑 | 界面文本 |
| 15744 | File Tree Component is not loaded. | 文件树组件未加载。 | 界面文本 |
| 15793 | Artifacts like Google Docs, PDFs, Office documents (Word, Excel, PowerPoint), etc. Everything else the agent creates is under Artifacts. | 如 Google Docs、PDF、Office 文档（Word、Excel、PowerPoint）等 Artifact。智能体创建的其他内容均属于 Artifacts。 | 界面文本 |
| 15793 | What counts as a document | 哪些内容算作文档 | 界面文本 |
| 15801 | Expand subagents | 展开子智能体 | 界面文本 |
| 15805 | Needs attention | 需要处理 | 界面文本 |
| 15826 | Task not found | 未找到任务 | 界面文本 |
| 15827 | Not started | 未开始 | 界面文本 |
| 15894 | Something went wrong. | 出了点问题。 | 界面文本 |
| 15912 | Resolved in chat | 已在对话中解决 | UI属性 / summary |
| 15922 | Add a note or condition... | 添加备注或条件... | 界面文本 |
| 15924 | Add note | 添加备注 | 界面文本 |
| 15924 | In chat | 在对话中 | 界面文本 |
| 15928 | Replaced by newer request | 已被更新的请求取代 | 界面文本 |
| 15929 | Expired · Action not taken | 已过期 · 未执行操作 | 界面文本 |
| 15930 | Ask to retry | 请求重试 | 界面文本 |
| 15933 | Select one or more options | 选择一个或多个选项 | 界面文本 |
| 15937 | Other answer | 其他答案 | 界面文本 |
| 15946 | Retry requested | 已请求重试 | UI属性 / summary |
| 15968 | You said | 你说 | 界面文本 |
| 15976 | Agent said | 智能体说 | 界面文本 |
| 16016 | Collapse questionnaire | 收起问卷 | 界面文本 |
| 16017 | Cancel Questionnaire and Stop the Agent | 取消问卷并停止智能体 | 界面文本 |
| 16017 | Cancel questionnaire | 取消问卷 | 界面文本 |
| 16017 | Collapse Questionnaire | 收起问卷 | 界面文本 |
| 16041 | Response actions | 回复操作 | 界面文本 |
| 16068 | Permission approval scope | 权限批准范围 | 界面文本 |
| 16071 | Tell the agent what to do instead... | 告诉智能体应该改做什么... | UI属性 / placeholder |
| 16072 | Deny with note | 附带备注拒绝 | 界面文本 |
| 16089 | Conversation Log | 对话日志 | 界面文本 |
| 16103 | Replace with | 替换为 | UI属性 / label |
| 16107 | Review contents | 检查内容 | 界面文本 |
| 16108 | Add anyway | 仍然添加 | 界面文本 |
| 16131 | The suggested plugin isn't in the marketplace. | 推荐的插件不在市场中。 | 界面文本 |
| 16132 | Local only | 仅本地 | 界面文本 |
| 16132 | Remote only | 仅远程 | 界面文本 |
| 16134 | Sign in needed | 需要登录 | 界面文本 |
| 16146 | Unknown error. | 未知错误。 | 界面文本 |
| 16147 | Fix with Agent | 使用智能体修复 | 界面文本 |
| 16157 | Finish signing in to | 完成登录以使用 | 界面文本 |
| 16173 | Accounts tab | 账户选项卡 | 界面文本 |
| 16173 | and make it the default. | 并将其设为默认。 | 界面文本 |
| 16175 | Reconnect account | 重新连接账户 | 界面文本 |
| 16195 | Plugin metadata | 插件元数据 | 界面文本 |
| 16203 | Target Tools: | 目标工具： | 界面文本 |
| 16207 | Unnamed MCP Server | 未命名的 MCP 服务器 | 界面文本 |
| 16210 | Context usage | 上下文用量 | 界面文本 |
| 16211 | Sent Message | 已发送消息 | 界面文本 |
| 16215 | Failed to list logs in modal | 在弹窗中列出日志失败 | 界面文本 |
| 16215 | No logs available. | 暂无可用日志。 | 界面文本 |
| 16227 | Side Pane UI Available | 侧边栏界面可用 | 界面文本 |
| 16227 | Stream and control | 流式传输并控制 | 界面文本 |
| 16227 | directly in the side pane. | 直接在侧边栏中。 | 界面文本 |
| 16228 | Process Error | 进程错误 | 界面文本 |
| 16229 | Process exited with an error | 进程因错误而退出 | 界面文本 |
| 16233 | Full Logs | 完整日志 | 界面文本 |
| 16233 | Recent Events | 最近事件 | 界面文本 |
| 16236 | No events recorded | 暂无记录的事件 | 界面文本 |
| 16236 | Start Plugin | 启动插件 | 界面文本 |
| 16236 | This plugin is currently stopped. Events and stdout streams will appear here once started. | 此插件当前已停止。启动后，事件和标准输出流将在此处显示。 | 界面文本 |
| 16245 | Open Appearance | 打开外观设置 | 界面文本 |
| 16245 | Unnamed Theme | 未命名的主题 | 界面文本 |
| 16262 | Account connected. | 账户已连接。 | UI属性 / message |
| 16262 | Connect an account so the agent can use this app. | 连接账户，以便智能体使用此应用。 | UI属性 / message |
| 16263 | No sign-in required. This app is ready to use. | 无需登录。此应用即可使用。 | UI属性 / message |
| 16282 | To switch accounts, sign out in the | 要切换账户，请在 | 界面文本 |
| 16292 | This plugin requires authentication before the agent can use its tools. | 此插件需要先完成身份验证，智能体才能使用其工具。 | UI属性 / message |
| 16298 | Sign in required. | 需要登录。 | UI属性 / message |
| 16298 | This plugin was force disabled. | 此插件已被强制禁用。 | 界面文本 |
| 16299 | Plugin details | 插件详情 | 界面文本 |
| 16305 | Open plugin page | 打开插件页面 | 界面文本 |
| 16308 | Working Directory: | 工作目录： | 界面文本 |
| 16337 | Docs, Sheets, Slides, and folders | 文档、表格、幻灯片和文件夹 | UI属性 / text |
| 16338 | Browse MCP resources | 浏览 MCP 资源 | UI属性 / text |
| 16339 | Browse rules | 浏览规则 | UI属性 / text |
| 16340 | Attach terminal output | 附加终端输出 | UI属性 / text |
| 16402 | Empty table | 空表格 | 界面文本 |
| 16403 | Clear row filter | 清除行筛选 | 界面文本 |
| 16403 | Filter rows | 筛选行 | 界面文本 |
| 16410 | Resume environment | 恢复环境 | 界面文本 |
| 16411 | Failed to read file content | 读取文件内容失败 | 界面文本 |
| 16411 | File not found | 找不到文件 | 界面文本 |
| 16428 | Toggle checkerboard background | 切换棋盘格背景 | 界面文本 |
| 16469 | Clear file filter | 清除文件筛选 | 界面文本 |
| 16469 | Filter files | 筛选文件 | 界面文本 |
| 16470 | Clear filter | 清除筛选 | 界面文本 |
| 16470 | Couldn't search files | 无法搜索文件 | 界面文本 |
| 16471 | No matching files | 没有匹配的文件 | 界面文本 |
| 16478 | Loading Notebook View... | 正在加载 Notebook 视图... | 界面文本 |
| 16500 | Open Blame in Code Search | 在代码搜索中打开 Blame | UI属性 / tooltip |
| 16507 | Toggle file diff | 切换文件差异显示 | 界面文本 |
| 16541 | Failed to load some diffs | 部分差异加载失败 | 界面文本 |
| 16568 | Merge Conflict | 合并冲突 | 界面文本 |
| 16570 | Failed to fetch diffs | 获取差异失败 | 界面文本 |
| 16577 | Delete Terminal | 删除终端 | 界面文本 |
| 16659 | Entering your corp password in the web terminal triggers a Chrome Password Alert (Watchword) forced password reset, so this prompt was automatically cancelled. | 在网页终端中输入公司密码会触发 Chrome 密码警报（Watchword）强制重置密码，因此此提示已自动取消。 | 界面文本 |
| 16659 | Password Prompt Blocked | 密码提示已被阻止 | 界面文本 |
| 16660 | ), use an external SSH session | ），请使用外部 SSH 会话 | 界面文本 |
| 16660 | For corp passwords (such as | 对于公司密码（例如 | 界面文本 |
| 16661 | Allow Next Non-Corp Prompt | 允许下一次非公司密码提示 | 界面文本 |
| 16666 | Resize terminal panes | 调整终端窗格大小 | 界面文本 |
| 16670 | No active terminals. Click + to create one. | 没有活动的终端。点击 + 创建一个。 | 界面文本 |
| 16671 | Creating terminal... | 正在创建终端... | 界面文本 |
| 16677 | UI view does not exist. | UI 视图不存在。 | 界面文本 |
| 16680 | File Viewer | 文件查看器 | 界面文本 |
| 16682 | Directory Viewer | 目录查看器 | 界面文本 |
| 16683 | Virtual File | 虚拟文件 | 界面文本 |
| 16683 | Virtual File Viewer | 虚拟文件查看器 | 界面文本 |
| 16685 | Artifact Viewer | Artifact 查看器 | 界面文本 |
| 16693 | Sidecar View | Sidecar 视图 | 界面文本 |
| 16695 | MCP App | MCP 应用 | 界面文本 |
| 16695 | Workspace File Explorer | 工作区文件资源管理器 | 界面文本 |
| 16704 | Match case | 区分大小写 | 界面文本 |
| 16705 | Match Case (Aa) | 区分大小写 (Aa) | 界面文本 |
| 16705 | Match whole word | 全词匹配 | 界面文本 |
| 16706 | Match Whole Word (ab) | 全词匹配 (ab) | 界面文本 |
| 16706 | Use regular expression | 使用正则表达式 | 界面文本 |
| 16707 | Use Regular Expression (.*) | 使用正则表达式 (.*) | 界面文本 |
| 16710 | Close (Escape) | 关闭 (Escape) | 界面文本 |
| 16769 | ErrorBoundary Crash | ErrorBoundary 崩溃 | 界面文本 |
| 16809 | A group with this name already exists. | 已存在同名分组。 | 界面文本 |
| 16836 | More options | 更多选项 | 界面文本 |
| 16839 | Forked conversation | 已分叉的对话 | 界面文本 |
| 16851 | Unsent draft | 未发送的草稿 | UI属性 / title |
| 16897 | Not PII/NTK | 非 PII/NTK | 界面文本 |
| 16908 | Loading Repositories… | 正在加载仓库… | 界面文本 |
| 16914 | Failed to create remote project | 创建远程项目失败 | UI属性 / title |
| 16937 | No matching | 无匹配项 | 界面文本 |
| 16940 | Remote Projects | 远程项目 | 界面文本 |
| 16941 | Search Hosts… | 搜索主机… | 界面文本 |
| 16945 | Change VCS in General settings, under Advanced | 在“常规”设置的“高级”下更改 VCS | 界面文本 |
| 16947 | Failed to unarchive local project | 解压本地项目失败 | UI属性 / title |
| 16950 | Failed to clone project locally | 在本地克隆项目失败 | UI属性 / title |
| 16958 | Clones this repo in a cloud environment | 在云环境中克隆此仓库 | 界面文本 |
| 16971 | Waiting for tool permission approval — click Open in full conversation (↗) to approve | 等待工具权限批准 — 点击“在完整对话中打开”(↗) 进行批准 | 界面文本 |
| 16978 | Reply to /help | 回复 /help | 界面文本 |
| 16987 | Resize side question panel | 调整侧边提问面板大小 | 界面文本 |
| 16989 | Previous side question | 上一个侧边提问 | 界面文本 |
| 16990 | Next side question | 下一个侧边提问 | 界面文本 |
| 16991 | Minimize side question | 最小化侧边提问 | 界面文本 |
| 16995 | Thought Process | 思考过程 | 界面文本 |
| 17008 | Start Best-of- | 启动 Best-of- | 界面文本 |
| 17012 | Enable Best-of-2 | 启用 Best-of-2 | 界面文本 |
| 17012 | Tip: Complex tasks get better results with multiple responses. | 提示：复杂任务通过多个回复可获得更好的结果。 | 界面文本 |
| 17013 | Proceed Anyway | 仍要继续 | 界面文本 |
| 17037 | Browse Connectors | 浏览连接器 | 界面文本 |
| 17037 | Loading connectors… | 正在加载连接器… | 界面文本 |
| 17038 | Failed to parse ContextScopeItem: | 解析 ContextScopeItem 失败： | 界面文本 |
| 17055 | Instead of queueing, try asking the agent to do something after the current task. | 不要排队，可尝试让智能体在当前任务完成后执行其他操作。 | UI属性 / message |
| 17055 | Messages now send immediately. Configure in | 消息现在会立即发送。可在 | 界面文本 |
| 17055 | This conversation is also open in another app. Sending messages from both may cause conflicts. | 此对话也在另一个应用中打开。从两处发送消息可能会导致冲突。 | UI属性 / message |
| 17066 | Migrate with Agent | 使用智能体迁移 | 界面文本 |
| 17066 | Workflows are changing on October 19th—stay tuned for updates. You can use the agent to migrate your workflows. | 工作流将于 10 月 19 日变更 — 请关注更新。你可以使用智能体迁移你的工作流。 | 界面文本 |
| 17071 | Workspace mismatch actions | 工作区不匹配操作 | 界面文本 |
| 17074 | Snooze for 24 Hours | 暂停 24 小时 | 界面文本 |
| 17074 | Switch IDE Workspace | 切换 IDE 工作区 | 界面文本 |
| 17094 | Use Global Settings | 使用全局设置 | 界面文本 |
| 17097 | Browser Configuration Required | 需要浏览器配置 | 界面文本 |
| 17099 | If that machine is a cloudtop, reach it via | 如果该机器是云桌面，请通过 | 界面文本 |
| 17099 | Open Google Chrome on the machine running Antigravity. | 在运行 Antigravity 的机器上打开 Google Chrome。 | 界面文本 |
| 17147 | No branches | 无分支 | 界面文本 |
| 17147 | Worktrees are a git feature. This folder is shared as is. | Worktree 是 git 功能。此文件夹按原样共享。 | UI属性 / content |
| 17175 | No environments found | 未找到环境 | 界面文本 |
| 17183 | JJ worktree | JJ 工作树 | 界面文本 |
| 17204 | Your quota for this model is running low. | 此模型的配额即将用尽。 | 界面文本 |
| 17207 | Custom models are only supported on Linux machines. | 自定义模型仅受 Linux 机器支持。 | 界面文本 |
| 17249 | Check that the microphone is unmuted and the right input device is selected. | 请检查麦克风是否未静音，以及是否选择了正确的输入设备。 | UI属性 / message |
| 17281 | Dismiss microphone warning | 关闭麦克风警告 | 界面文本 |
| 17353 | Set up | 设置 | 界面文本 |
| 17366 | Sends after agent finishes working | 在智能体完成工作后发送 | 界面文本 |
| 17367 | Expand queued messages | 展开排队中的消息 | 界面文本 |
| 17369 | Empty message | 空消息 | 界面文本 |
| 17399 | Listening. Ask anything. | 正在聆听。尽管提问。 | 界面文本 |
| 17419 | Couldn't edit queued message | 无法编辑排队中的消息 | UI属性 / title |
| 17419 | It was already sent or couldn't be removed from the queue. | 该消息已发送，或无法从队列中移除。 | UI属性 / message |
| 17448 | Voice dictation unavailable | 语音听写不可用 | UI属性 / title |
| 17451 | Transcribing audio… | 正在转写音频… | 界面文本 |
| 17457 | Chat anyways | 仍要聊天 | 界面文本 |
| 17457 | Interrupt Agent | 中断智能体 | UI属性 / label |
| 17457 | New chats will be grouped by workspace. | 新对话将按工作区分组。 | 界面文本 |
| 17457 | Select CitC workspace | 选择 CitC 工作区 | 界面文本 |
| 17512 | Trouble signing in? Enter authorization code | 登录遇到问题？输入授权码 | 界面文本 |
| 17515 | Authorization code | 授权码 | 界面文本 |
| 17517 | Submit code | 提交授权码 | 界面文本 |
| 17523 | Last Used | 最近使用 | 界面文本 |
| 17525 | Use Business Account | 使用企业账户 | 界面文本 |
| 17527 | Use Advanced SSO Config | 使用高级 SSO 配置 | 界面文本 |
| 17528 | Use this if your admin gave you a WIF config. Paste it below to sign in. | 如果你的管理员提供了 WIF 配置，请使用此项。将其粘贴到下方即可登录。 | 界面文本 |
| 17530 | WIF Config | WIF 配置 | 界面文本 |
| 17531 | Having trouble signing in? | 登录遇到问题？ | 界面文本 |
| 17531 | Sign In with SSO | 使用 SSO 登录 | 界面文本 |
| 17553 | Use Google Cloud project instead | 改用 Google Cloud 项目 | 界面文本 |
| 17555 | There was an unexpected issue setting up your account. | 设置你的账户时出现意外问题。 | 界面文本 |
| 17556 | Continue with different account | 使用其他账户继续 | 界面文本 |
| 17556 | Please verify your account, then sign in again to continue. Learn more by visiting our | 请先验证你的账户，然后重新登录以继续。请访问我们的 | 界面文本 |
| 17556 | We apologize for the inconvenience. Please try again later. | 很抱歉带来不便。请稍后重试。 | 界面文本 |
| 17559 | Learn more by visiting our | 请访问我们的 | 界面文本 |
| 17559 | Sorry, this account is ineligible to use | 抱歉，此账户无权使用 | 界面文本 |
| 17560 | Enter Google Cloud Project Details | 输入 Google Cloud 项目详细信息 | 界面文本 |
| 17561 | Google Cloud Project ID | Google Cloud 项目 ID | 界面文本 |
| 17561 | This Google Cloud project is not supported. Input a different project, or sign in with another account. | 不支持此 Google Cloud 项目。请输入其他项目，或使用其他账户登录。 | 界面文本 |
| 17562 | Sign in with a different account | 使用其他账户登录 | 界面文本 |
| 17574 | Get Anything Done with | 借助 | 界面文本 |
| 17578 | Let's tailor the experience for you. What best describes your work? | 让我们为你量身定制体验。以下哪项最符合你的工作？ | 界面文本 |
| 17582 | Select Theme | 选择主题 | 界面文本 |
| 17615 | No longer available | 不再可用 | UI属性 / label |
| 17615 | Removed from the marketplace. Stays installed until you uninstall it. | 已从市场中移除。在你卸载前将保持安装状态。 | UI属性 / tooltip |
| 17625 | Disabling or removing this bundle doesn't affect it. | 禁用或移除此捆绑包不会影响它。 | UI属性 / tooltip |
| 17625 | Installed separately | 单独安装 | UI属性 / label |
| 17632 | Add bundle | 添加捆绑包 | 界面文本 |
| 17632 | Remove bundle | 移除捆绑包 | 界面文本 |
| 17643 | Review bundle before adding | 添加前查看捆绑包 | UI属性 / title |
| 17648 | Curated sets of plugins for common workflows and roles. | 针对常见工作流和角色精心挑选的插件集。 | 界面文本 |
| 17651 | No bundles available. | 暂无可用的捆绑包。 | 界面文本 |
| 17653 | Loading bundles... | 正在加载捆绑包... | 界面文本 |
| 17657 | Create plugin | 创建插件 | 界面文本 |
| 17675 | ? This will remove it from your MCP configuration. | ？这会将它从你的 MCP 配置中移除。 | 界面文本 |
| 17677 | ? This removes it from your config directory. | ？这会将它从你的配置目录中移除。 | 界面文本 |
| 17679 | Copy the folder elsewhere first if you might want it back. | 如果以后可能还需要，请先将该文件夹复制到其他地方。 | 界面文本 |
| 17679 | This cannot be undone. | 此操作无法撤销。 | 界面文本 |
| 17705 | No skills or rules match this filter. | 没有符合此筛选条件的技能或规则。 | 界面文本 |
| 17706 | No custom agents yet. | 暂无自定义智能体。 | 界面文本 |
| 17736 | No matching plugins found. | 未找到匹配的插件。 | 界面文本 |
| 17784 | Marketplace notice | 市场通知 | 界面文本 |
| 17784 | No plugins available in the marketplace. | 市场中没有可用的插件。 | 界面文本 |
| 17786 | Loading available plugins... | 正在加载可用插件... | 界面文本 |
| 17793 | Customizations views | 自定义视图 | 界面文本 |
| 17794 | Filter plugins | 筛选插件 | 界面文本 |
| 17802 | Clear category | 清除类别 | 界面文本 |
| 17806 | Failed to load shared conversation | 加载共享对话失败 | 界面文本 |
| 17806 | Go to Home | 返回主页 | 界面文本 |
| 17807 | Importing shared conversation... | 正在导入共享对话... | 界面文本 |
| 17810 | Welcome to | 欢迎使用 | 界面文本 |
| 17819 | Edits the conversation title | 编辑对话标题 | 界面文本 |
| 17824 | Toggle Terminal Panel | 切换终端面板 | 界面文本 |
| 17865 | Are you sure you want to delete this side question? This action cannot be undone. | 确定要删除这个侧边提问吗？此操作无法撤销。 | 界面文本 |
| 17898 | Customize Sections | 自定义分区 | 界面文本 |
| 17917 | Open in Hub | 在 Hub 中打开 | 界面文本 |
| 17929 | Open Antigravity IDE | 打开 Antigravity IDE | 界面文本 |
| 17929 | Open IDE | 打开 IDE | 界面文本 |
| 17930 | Open in Antigravity IDE | 在 Antigravity IDE 中打开 | 界面文本 |
| 17931 | Command prompt | 命令提示符 | UI属性 / label |
| 17931 | Terminal window | 终端窗口 | UI属性 / label |
| 17933 | Choose icon and color | 选择图标和颜色 | 界面文本 |
| 17939 | Coordinator name | 协调者名称 | 界面文本 |
| 17939 | e.g. Release helper | 例如：发布助手 | UI属性 / placeholder |
| 17940 | Coordinator goal | 协调者目标 | 界面文本 |
| 17942 | Create Coordinator | 创建协调者 | 界面文本 |
| 17947 | Resolving link… | 正在解析链接… | UI属性 / label |
| 17959 | Conversation link | 对话链接 | 界面文本 |
| 17969 | Toggle Virtual Machine | 切换虚拟机 | 界面文本 |
| 17977 | Back to home | 返回主页 | 界面文本 |
| 17979 | Reload app | 重新加载应用 | 界面文本 |
| 18046 | Scroll turns down | 向下滚动对话轮次 | 界面文本 |
| 18059 | Conversation turns | 对话轮次 | 界面文本 |
| 18066 | Accept all | 全部接受 | 界面文本 |
| 18066 | Reject all | 全部拒绝 | 界面文本 |
| 18113 | Needs Attention | 需要注意 | 界面文本 |
| 18136 | This chat is archived. | 此对话已归档。 | 界面文本 |
| 18173 | Previous card | 上一张卡片 | 界面文本 |
| 18174 | Next card | 下一张卡片 | 界面文本 |
| 18181 | Select a model in the model selector | 在模型选择器中选择模型 | 界面文本 |
| 18186 | Click to Open Docs | 点击打开文档 | 界面文本 |
| 18187 | Click to open docs | 点击打开文档 | 界面文本 |
| 18192 | Agent options | 智能体选项 | 界面文本 |
| 18199 | Set up my environment | 设置我的环境 | 界面文本 |
| 18201 | Dismiss suggestion | 忽略建议 | 界面文本 |
| 18227 | Plugins Options | 插件选项 | 界面文本 |
| 18235 | Move Down | 下移 | UI属性 / label |
| 18235 | Move Up | 上移 | UI属性 / label |
| 18241 | Show or Hide Plugins | 显示或隐藏插件 | 界面文本 |
| 18246 | Loading conversations... | 正在加载对话... | 界面文本 |
| 18248 | Create New | 新建 | 界面文本 |
| 18248 | Use Existing | 使用现有项 | 界面文本 |
| 18249 | Project location | 项目位置 | 界面文本 |
| 18253 | A project with this name already exists. | 已存在同名项目。 | 界面文本 |
| 18254 | Create CitC Workspace | 创建 CitC 工作区 | 界面文本 |
| 18254 | Select CitC Workspace | 选择 CitC 工作区 | 界面文本 |
| 18254 | Select Cog Workspace | 选择 Cog 工作区 | 界面文本 |
| 18299 | Pinned Actions | 置顶操作 | 界面文本 |
| 18300 | Show 10 | 显示 10 项 | UI属性 / label |
| 18300 | Show 5 | 显示 5 项 | UI属性 / label |
| 18306 | Customize Sidebar | 自定义侧边栏 | UI属性 / title |
| 18307 | Auto Pin | 自动置顶 | UI属性 / label |
| 18307 | Idle Conversations | 闲置对话 | UI属性 / label |
| 18308 | Only applies when grouped by status | 仅按状态分组时适用 | 界面文本 |
| 18309 | Show Automation Conversations | 显示自动化对话 | UI属性 / label |
| 18310 | Any time | 任意时间 | UI属性 / label |
| 18310 | Manual Order | 手动排序 | UI属性 / label |
| 18310 | Show Plugin Conversations | 显示插件对话 | UI属性 / label |
| 18312 | Filter and Sort | 筛选和排序 | 界面文本 |
| 18313 | Last Activity | 最近活动 | UI属性 / title |
| 18325 | Needs Input | 需要输入 | UI属性 / label |
| 18489 | Close Panel | 关闭面板 | 界面文本 |
| 18575 | Full View | 完整视图 | 界面文本 |
| 18575 | Subagent Conversation | 子智能体对话 | 界面文本 |
| 18584 | Stop Side Question | 停止侧边提问 | 界面文本 |
| 18619 | Send a message in the main conversation first to start a side question | 请先在主对话中发送消息，再发起侧边提问 | 界面文本 |
| 18649 | No results | 无结果 | 界面文本 |
| 18660 | Keep Open | 保持打开 | UI属性 / label |
| 18683 | Browser is currently being operated by this conversation in another Hub window | 浏览器当前正由另一个 Hub 窗口中的此对话操作 | 界面文本 |
| 18729 | Voice mode in progress | 语音模式进行中 | 界面文本 |
| 18734 | Drag to move | 拖动以移动 | 界面文本 |
| 18738 | Add files | 添加文件 | UI属性 / content |
| 18738 | Message this chat | 向此对话发送消息 | 界面文本 |
| 18741 | Write a message | 输入消息 | 界面文本 |
| 18805 | Maximize Pane | 最大化窗格 | 界面文本 |
| 18821 | See all ( | 查看全部 ( | 界面文本 |
| 18907 | Paused. Resume it to schedule the next run. | 已暂停。恢复后可安排下一次运行。 | 界面文本 |
| 18907 | Pick a model to change it. | 选择模型即可更改。 | 界面文本 |
| 18910 | No instructions. | 无指令。 | 界面文本 |
| 18916 | All runs | 所有运行 | 界面文本 |
| 18934 | Match when the principal belongs to the specified MDB group. | 当主体属于指定的 MDB 组时匹配。 | UI属性 / description |
| 18935 | Ignore events emitted by automated review or robot accounts (groupagent-*). | 忽略由自动审核或机器人账号（groupagent-*）发出的事件。 | UI属性 / description |
| 18935 | Match when the principal equals any listed username or belongs to any listed mdb/ group. | 当主体等于任一列出的用户名或属于任一列出的 mdb/ 组时匹配。 | UI属性 / description |
| 18936 | Match when any modified file path starts with the given depot prefix. | 当任一修改的文件路径以指定的 depot 前缀开头时匹配。 | UI属性 / description |
| 18936 | Match when push_def equals or is a child of the given PushDef prefix. | 当 push_def 等于或属于指定 PushDef 前缀的子级时匹配。 | UI属性 / description |
| 18937 | Match when the issue component equals or is under the given Buganizer component ID. | 当问题组件等于或位于指定 Buganizer 组件 ID 之下时匹配。 | UI属性 / description |
| 18991 | Only for | 仅适用于 | 界面文本 |
| 18992 | Add filter | 添加筛选条件 | 界面文本 |
| 19011 | Set at least one scope filter | 至少设置一个范围筛选条件 | 界面文本 |
| 19012 | Match Condition (CEL) | 匹配条件 (CEL) | 界面文本 |
| 19013 | Invalid CEL | CEL 无效 | 界面文本 |
| 19013 | Valid CEL | CEL 有效 | 界面文本 |
| 19014 | CEL Expression Reference | CEL 表达式参考 | 界面文本 |
| 19014 | Optional boolean filter | 可选的布尔筛选条件 | 界面文本 |
| 19015 | Equality and list membership (e.g. | 相等和列表成员关系 (例如 | 界面文本 |
| 19015 | Include at least one positive | 至少包含一个肯定条件 | 界面文本 |
| 19016 | Boolean AND, OR, and negation | 布尔 AND、OR 和取反 | 界面文本 |
| 19016 | Substring or list check (e.g. | 子串或列表检查 (例如 | 界面文本 |
| 19017 | CEL Reference | CEL 参考 | 界面文本 |
| 19019 | Available CEL field tokens and helpers | 可用的 CEL 字段标记和辅助函数 | 界面文本 |
| 19022 | Indexed CEL helper functions | 已索引的 CEL 辅助函数 | 界面文本 |
| 19027 | Available CEL helper functions | 可用的 CEL 辅助函数 | 界面文本 |
| 19035 | Execution Identity | 执行身份 | 界面文本 |
| 19042 | Connect an account so the agent can run automations. | 连接账号后，智能体即可运行自动化任务。 | 界面文本 |
| 19046 | No events recorded. | 暂无事件记录。 | 界面文本 |
| 19056 | Sidecar feature is not available. | Sidecar 功能不可用。 | 界面文本 |
| 19057 | Back to | 返回 | 界面文本 |
| 19066 | Runs a command | 运行命令 | 界面文本 |
| 19076 | Untrusted sidecar | 不受信任的 Sidecar | 界面文本 |
| 19090 | Always on | 始终开启 | 界面文本 |
| 19105 | Select workspace | 选择工作区 | 界面文本 |
| 19119 | Create a project first. | 请先创建项目。 | 界面文本 |
| 19122 | Remove trigger | 移除触发器 | 界面文本 |
| 19123 | Add schedule | 添加计划 | 界面文本 |
| 19123 | Add trigger | 添加触发器 | 界面文本 |
| 19130 | Where should it run? | 要在哪里运行？ | 界面文本 |
| 19132 | with this name already exists on this computer. Run it remotely, or go back and rename it. | 的名称已在此计算机上存在。可远程运行，或返回重命名。 | 界面文本 |
| 19147 | Create with Prompt | 通过提示词创建 | 界面文本 |
| 19153 | Run command step not found | 未找到运行命令步骤 | 界面文本 |
| 22421 | Failed to load SafeContentFrame | 加载 SafeContentFrame 失败 | 界面文本 |
| 22511 | Pause this agent; it keeps its place and streams. Resume to continue. | 暂停此智能体；它会保留位置和流式输出。恢复后可继续。 | UI属性 / title |
| 22512 | Resume this agent where it paused | 从暂停处恢复此智能体 | UI属性 / title |
| 22512 | Stop this agent | 停止此智能体 | UI属性 / title |
| 22523 | Filter agents | 筛选智能体 | 界面文本 |
| 22524 | All agents | 所有智能体 | 界面文本 |
| 22527 | Stop all agents | 停止所有智能体 | 界面文本 |
| 22578 | Waiting for the agents’ windows… | 正在等待智能体窗口… | 界面文本 |
| 22617 | Hidden by policy | 因策略而隐藏 | 界面文本 |
| 22617 | Starting preview… | 正在启动预览… | 界面文本 |
| 22617 | Stream ended | 流式输出已结束 | 界面文本 |
| 22658 | A new version is available. | 有新版本可用。 | 界面文本 |
| 22658 | Go to the machine you are controlling and quit Antigravity. It installs pending updates the next time it starts. | 请前往你正在控制的设备并退出 Antigravity。下次启动时会安装待处理的更新。 | 界面文本 |
| 22658 | Start it again. | 再次启动它。 | 界面文本 |
| 22659 | Reload this window. | 重新加载此窗口。 | 界面文本 |
| 22688 | Failed to save token to ~/.env | 无法将 Token 保存到 ~/.env | UI属性 / message |
| 22689 | Create a token | 创建 Token | 界面文本 |
| 22689 | Validated with GitHub and stored in | 已通过 GitHub 验证并存储于 | 界面文本 |
| 22691 | Authenticated as | 已通过身份验证为 | 界面文本 |
| 22691 | Show token | 显示 Token | 界面文本 |
| 22698 | Agent can | 智能体可以 | 界面文本 |
| 22699 | Remove policy | 移除策略 | 界面文本 |
| 22700 | Agent can run | 智能体可以运行 | 界面文本 |
| 22700 | Workflow files | 工作流文件 | 界面文本 |
| 22701 | Workflow refs | 工作流引用 | 界面文本 |
| 22705 | Delete repository policy | 删除仓库策略 | 界面文本 |
| 22706 | A comma-separated list like repo-a, repo-b, or * for all. | 以逗号分隔的列表，如 repo-a、repo-b，或使用 * 表示全部。 | 界面文本 |
| 22707 | Read access | 读取权限 | 界面文本 |
| 22707 | Read access to code, refs, commits, and other repository contents. | 对代码、引用、提交及其他仓库内容的读取权限。 | 界面文本 |
| 22707 | Toggle this on to enable read access on contents. | 开启此选项以允许读取内容。 | 界面文本 |
| 22708 | Allow creating issues and grant access to specific issues. | 允许创建议题，并授予对特定议题的访问权限。 | 界面文本 |
| 22709 | Issue creation | 创建议题 | 界面文本 |
| 22709 | Toggle this on to allow creating new issues. | 开启此选项以允许创建新议题。 | 界面文本 |
| 22710 | Access rules | 访问规则 | 界面文本 |
| 22710 | Grant the selected actions on the listed issue numbers — a comma-separated list like 1, 2, 3, or * for all. | 对列出的议题编号授予所选操作——以逗号分隔的列表，如 1、2、3，或使用 * 表示全部。 | 界面文本 |
| 22710 | Issue actions | 议题操作 | 界面文本 |
| 22710 | Issue numbers | 议题编号 | 界面文本 |
| 22712 | Allow opening pull requests and grant access to specific PRs. | 允许发起拉取请求，并授予对特定 PR 的访问权限。 | 界面文本 |
| 22713 | Grant the selected actions on the listed pull request numbers — a comma-separated list like 1, 2, 3, or * for all. | 对列出的拉取请求编号授予所选操作——以逗号分隔的列表，如 1、2、3，或使用 * 表示全部。 | 界面文本 |
| 22713 | Pull request creation | 创建拉取请求 | 界面文本 |
| 22713 | Toggle this on to allow creating new pull requests. | 开启此选项以允许创建新的拉取请求。 | 界面文本 |
| 22714 | Pull request actions | 拉取请求操作 | 界面文本 |
| 22714 | Pull request numbers | 拉取请求编号 | 界面文本 |
| 22715 | Grant create, update, or delete access to specific branches. | 授予对特定分支的创建、更新或删除权限。 | 界面文本 |
| 22715 | Remote branches | 远程分支 | 界面文本 |
| 22716 | Branch actions | 分支操作 | 界面文本 |
| 22716 | Branch names | 分支名称 | 界面文本 |
| 22716 | Grant the selected actions on the listed branch names — a comma-separated list like main, dev, prod (glob patterns like fix-* allowed), or * for all. | 对列出的分支名称授予所选操作——以逗号分隔的列表，如 main、dev、prod（允许使用 fix-* 这样的通配符模式），或使用 * 表示全部。 | 界面文本 |
| 22718 | Grant read access to workflow runs and allow dispatching workflows on specific files and refs. | 授予对工作流转运行的读取权限，并允许对特定文件和引用触发工作流。 | 界面文本 |
| 22718 | Workflow runs | 工作流运行 | 界面文本 |
| 22719 | Allow reading workflow runs (list, view, watch) across the whole repository. | 允许读取整个仓库中的工作流运行（列表、查看、监视）。 | 界面文本 |
| 22722 | Delete organization policy | 删除组织策略 | 界面文本 |
| 22723 | A comma-separated list like org-a, org-b, or * for all. | 以逗号分隔的列表，如 org-a、org-b，或使用 * 表示全部。 | 界面文本 |
| 22825 | Code Preview | 代码预览 | 界面文本 |
| 23625 | Get started with Remote Control | 开始使用远程控制 | 界面文本 |
| 23625 | No instances yet. | 暂无实例。 | 界面文本 |
| 23628 | Loading instances... | 正在加载实例... | UI属性 / displayname |
| 23643 | Show Thumbnail Sidebar | 显示缩略图侧边栏 | 界面文本 |
| 23649 | Zoom Level | 缩放级别 | 界面文本 |
| 23653 | More toolbar actions | 更多工具栏操作 | 界面文本 |
| 23661 | Text Selection | 文本选择 | UI属性 / label |
| 23720 | No Match Found | 未找到匹配项 | 界面文本 |
| 23746 | Cancel Render Page Failed | 取消渲染页面失败 | UI属性 / message |
| 23960 | Cancel Render Thumbnail Failed | 取消渲染缩略图失败 | UI属性 / message |
| 24251 | Document head unavailable | 文档头部不可用 | 界面文本 |
| 24287 | GitHub: not signed in | GitHub：未登录 | 界面文本 |
| 24398 | Switch To | 切换到 | UI属性 / heading |
| 24418 | Mermaid diagram | Mermaid 图表 | 界面文本 |

---

## 附录 A：已由现有词典覆盖（21 条，无需处理）

这 21 条在候选生成后已被当前 `locales/zh-CN.json` 精确覆盖，保留在此说明统计口径；来源行号从略。

| 原文 | 现有译文 |
| :--- | :--- |
| Connect to SSH Host… | 连接到 SSH 主机… |
| Stop SSH Server… | 停止 SSH 服务器… |
| Back 5s (←) | 快退 5 秒 (←) |
| Forward 5s (→) | 快进 5 秒 (→) |
| This site can’t be reached | 无法访问此网站 |
| This page isn’t working | 此网页无法正常运作 |
| Validating setup script… | 正在验证设置脚本… |
| Your agent’s ability to execute commands is also controlled by enterprise security policies. | 智能体执行命令的能力同时受企业安全策略控制。 |
| Waiting for you to finish signing in… | 正在等待您完成登录… |
| Summarizing call… | 正在总结通话… |
| One last thing before getting started… | 开始使用前的最后一步… |
| Uploading to Google Drive… | 正在上传到 Google 云端硬盘… |
| Add an optional message, ⏎ to submit comments | 添加可选留言，按 ⏎ 提交评论 |
| SSH Host… | SSH 主机… |
| Loading Hosts… | 正在加载主机… |
| Starting the conversation… | 正在启动对话… |
| Starting terminal… | 正在启动终端… |
| Loading runs… | 正在加载运行记录… |
| Search filters… | 搜索筛选条件… |
| Search triggers… | 搜索触发器… |
| Loading skills… | 正在加载技能… |

## 附录 B：保持原文的产品/模型名与非文案串

| 来源 | 行号 | 原文 | 处理建议 |
| :--- | ---: | :--- | :--- |
| `language_server.exe!main.js` | 5497 | Google Chat | 产品/模型名，保持原文 |
| `language_server.exe!main.js` | 10005 | ELMO Composite | 产品/模型名，保持原文 |
| `language_server.exe!main.js` | 14206 | Gemini 2.5 Flash Image | 产品/模型名，保持原文 |
| `language_server.exe!main.js` | 14206 | Gemini 3 Pro Image | 产品/模型名，保持原文 |
| `language_server.exe!main.js` | 14206 | Gemini 3.1 Flash Image | 产品/模型名，保持原文 |
| `language_server.exe!main.js` | 14269 | Browser Use | 产品/模型名，保持原文 |
| `language_server.exe!main.js` | 14397 | Gemini Flash Next | 产品/模型名，保持原文 |
| `language_server.exe!main.js` | 18880 | Flash Lite | 产品/模型名，保持原文 |
| `language_server.exe!main.js` | 15362 | clipboard-read; clipboard-write; microphone; fullscreen; bluetooth; autoplay; publickey-credentials-get *; publickey-credentials-create * | 浏览器权限策略串，非界面文案，不翻译 |

---

*本清单只做排查与译法建议，未写入词典、未重新打补丁。配套的项目自身脚本文案清单见 `PROJECT_TEXT_ZH_AUDIT.md`。*

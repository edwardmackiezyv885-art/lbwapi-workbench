# 客户端接入与排错

接 LBW API 时反复踩的坑都在这里。按顺序看，90% 的问题能自己解决。

配套站点：**<https://lbwapi.online/beginner/>**

---

## 一、三个通用参数

| 参数 | 值 | 注意 |
| --- | --- | --- |
| API 地址 | `https://lbwapishop.online/v1` | **必须带 `/v1`**，个别客户端不要，报 404 就换另一种 |
| API Key | `sk-` 开头 | 粘贴后检查首尾没有空格 |
| 模型名 | `deepseek-flash` 或 `deepseek-chat` | 详见下文「同名模型」 |

控制台「API 密钥」页右上角有个 `API 地址` 按钮，点开复制的就是带 `/v1` 的完整地址。

---

## 二、`CONTEXT_WINDOW_EXCEEDED`（最常见）

### 报错长这样

```
pi-ai detected context overflow for model "deepseek-flash"
```

或者客户端里显示「上下文超限」「context window exceeded」。

### 原因

有些客户端（Pi、DeepSeek Harness 等）发消息前要估算「这次多少 token」，再和「模型窗口多大」比。问题在于它怎么知道窗口多大：

- **认识的模型名**（`deepseek-chat`、`claude-sonnet-4-5` 等）→ 内置表里有尺寸，正常
- **不认识的模型名**（`deepseek-flash`、`gpt-6.1-sol` 等）→ 查不到，**按一个很小的默认值算**

窗口被当成 8K，你随便发一句就「超了」。实际上 `deepseek-flash` 有 **100 万**上下文。

### 两个加重因素

1. 上游每次请求自动注入约 **6300 token** 的系统提示，起步就占掉一大截
2. 客户端如果读了项目文件，上下文膨胀更快

### 解法一：用一键工具（推荐）

| 客户端 | 工具 | 入口 |
| --- | --- | --- |
| Pi | `LBW-Pi-Start.bat` | <https://lbwapi.online/pi/LBW-Pi-Start.bat> |
| Pi（清冲突） | `LBW-Pi-Clean.bat` | <https://lbwapi.online/pi/LBW-Pi-Clean.bat> |
| DeepSeek Harness | `LBW-DSH-Setup.bat` | <https://lbwapi.online/pi/LBW-DSH-Setup.bat> |
| 诊断 | `LBW-Pi-diagnose.bat` | <https://lbwapi.online/pi/LBW-Pi-diagnose.bat> |

全部是「双击 → 粘贴 Key → 重启客户端」，会自动备份原配置。

### 解法二：手动补上下文长度

**Pi** — 编辑 `~/.pi/agent/models.json`：

```json
{
  "$schema": "https://pi.dev/schemas/models.schema.json",
  "providers": {
    "lbwapi": {
      "name": "LBW API",
      "baseUrl": "https://lbwapishop.online/v1",
      "api": "openai-completions",
      "apiKey": "sk-你的令牌",
      "models": [
        {
          "id": "deepseek-chat",
          "name": "deepseek-chat",
          "reasoning": true,
          "input": ["text", "image"],
          "contextWindow": 1000000,
          "maxTokens": 32000,
          "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 }
        }
      ]
    }
  }
}
```

改完用 `pi --list-models` 确认，`context` 列应该显示 `1M`。

**DeepSeek Harness** — 编辑 `~/.dsh/profiles/desktop/cordis.patch.yml`，在 `llm-pi-ai` 的 `providers` 下加：

```yaml
      lbwapi:
        displayName: lbwapi
        apiKeyEnv: LBWAPI_API_KEY
        api: openai-completions
        baseURL: https://lbwapishop.online/v1
        models:
          - id: deepseek-chat
            name: deepseek-chat
            reasoning: true
            contextWindow: 1000000
            maxTokens: 32000
```

再把 Key 写进用户环境变量 `LBWAPI_API_KEY`（客户端通过 `apiKeyEnv` 读取，不是写在 yml 里）。

### 解法三：换客户端

**ChatBox**、**Cherry Studio**、**NextChat**、**LobeChat** 都不做这种窗口判断，填上地址和 Key 就能用，不会报这个错。

---

## 三、同名模型冲突（第二个大坑）

现象：明明配好了，或者换了模型名，还是报同一个错。

原因：客户端里如果同时存在多个服务商都提供 `deepseek-flash`（比如上游直连、别的中转站、LBW 中转各一份），**模型列表里会出现多个同名条目**，分属不同服务商。你点的那个可能来自一个没有上下文信息的服务商。

识别方法：看模型列表的分组标题（provider 名），确认选的是 **LBW API / lbwapi** 那一组。

彻底解决：把多余的服务商删掉，只留一个。Pi 用户可以直接跑 `LBW-Pi-Clean.bat`。

---

## 四、速度慢

### 现象

同一个问题，官方 API 一两秒出声，走中转要三四秒，甚至十来秒。

### 原因（三层）

1. **上游注入** — 每次请求自动加约 6300 token 系统提示。模型要先处理完这些才能开始回答，这是 2.4 秒起步延迟的来源。**改不了**。
2. **多一跳** — 你的电脑 → 中转站 → 上游，物理上多一次转发，约 +0.6 秒。
3. **非流式的额外开销** — 非流式请求要等全部生成完才返回，中间层做缓冲和聚合，会多出 3–8 秒且波动大。

### 实测数据

| 模式 | 上游直连 | 经中转 |
| --- | --- | --- |
| 流式 | 2.40s | 3.06s |
| 非流式 | 3.24s | 6–11s |

### 建议

**确保客户端开启「流式输出 / Stream」**。开流式后延迟和上游几乎一样；关着就是 6–11 秒。

---

## 五、报错对照表

| 报错 | 原因 | 解决 |
| --- | --- | --- |
| `401 Unauthorized` | Key 错、过期、或末尾带空格 | 重新生成，粘贴后检查首尾 |
| `404` / `page not found` | API 地址少或多了 `/v1` | 换另一种写法再试 |
| `model not found` | 模型名拼错，或分组没这个模型 | 控制台「模型」页确认可用列表 |
| `CONTEXT_WINDOW_EXCEEDED` | 客户端按模型名猜了小窗口 | 见第二节 |
| `429 Too Many Requests` | 并发或速率超限 | 降低并发，稍等再试 |
| 回复很慢 | 上游注入 6300 token | 开流式；这是上游行为 |
| 能连但回复空白 | 客户端传了模型不支持的参数 | 关掉流式以外的特殊参数，或换模型 |
| `AUTH_SESSION_LIMIT` | 同一账号并发登录过多 | 等几分钟，别频繁登录 |

---

## 六、验证是否真的接对了

三个信号，缺一个都说明还没通：

1. **能正常回复** — 不是报错，不是空白
2. **控制台「使用日志」有记录** — 能看到这次请求的 token 数和扣费
3. **问一个原版会拒的问题** — 能答就说明解锁版生效

第二条最容易被跳过。日志里有记录，才证明请求真的走了中转站，而不是被客户端缓存或转到了别处。

---

## 七、可用模型

| 模型 | 上下文 | 特点 |
| --- | --- | --- |
| `deepseek-flash` | 1M | 便宜快，日常和写代码 |
| `deepseek-v4-pro` | 1M | 深度推理，思考链长 |
| `claude-opus-5-5` | 1M | 代码和长文最强 |
| `claude-fable-5-1` | 1M | Claude 轻量版 |
| `gpt-6.1-sol` | 1.1M | GPT 旗舰 |
| `gpt-6-astra` | 1.1M | GPT 复杂推理 |
| `glm-5.3` | 1M | 中文性价比 |
| `kimi-k3.1-pro` | 1M | 长文档 |
| `grok-4.7` | 500K | Grok |

完整列表看控制台「模型」页。

---

## 八、相关链接

| 用途 | 地址 |
| --- | --- |
| 从零接入教程 | <https://lbwapi.online/beginner/> |
| Pi 专门页面 | <https://lbwapi.online/pi/> |
| 注册拿 Key | <https://lbwapishop.online/register> |
| 控制台 | <https://lbwapishop.online/dashboard> |
| TG 频道 | <https://t.me/lbwapi> |
| TG 私聊 | <https://t.me/jiali66888> |

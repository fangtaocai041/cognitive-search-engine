> **最新**: v5.6.0 · 2026-06-10

## 🔁 v5.6.0: 生产环境加固 — 重连、MCP并行、中文搜索

> **三化升级**：服务端不稳定不再是瓶颈。MCP预热、HTTP重连、中文三层发散确保每次搜索可靠覆盖。

### 新增功能

| 功能 | 说明 | 模块 |
|:-----|:-----|:-----|
| **HTTP自动重连** | PubMed/Crossref/OpenAlex 指数退避重试，60s窗口，5次尝试 | `src/rule_engine.py` |
| **MCP并行** | 7搜索引擎并行启动，as_completed 先完成先返回，3min超时 | `src/mcp_client.py` |
| **MCP预热** | `__init__` 后台并行预热 + JSON-RPC tools/list 健康探测 | `src/mcp_client.py` |
| **中文三层搜索** | Layer1 四中文源 → Layer2 Crossref/OpenAlex → Layer3 tavily降级 | `src/rule_engine.py` |
| **语言路由** | 每个phase标记 language: en/zh/both，分离中英文通道 | `config/search_rules.yaml` |
| **停止机制修复** | Desire.satisfied() 不再因 min_papers=8 截断，diminishing returns驱动 | `src/world_model.py` |

### HTTP 重连

```
每API调用:
  for attempt in 1..5:
      try: urlopen(timeout=15)
      except (URLError, TimeoutError, HTTPError):
          wait = min(2^attempt, 15)  # 指数退避
          retry
  raise → 记录错误，不影响其他源
```

配置：`agent.yaml → timeout.http_retry_max_s: 60`

### MCP 并行 + 预热

```
McpClient.__init__():
  Thread: prewarm_background()  # 不阻塞构造
    for server in [scholar, article, scholarly, tavily, exa]:
      Parallel: _get_or_start_process(name)
                _health_check(name)  # JSON-RPC tools/list
      → 标记 healthy/unhealthy
```

总超时：`mcp_parallel_timeout_s: 180`

### 中文三层搜索

| 层 | 来源 | 查询 |
|:--:|------|------|
| 1 | 百度学术/CNKI/万方/CAS | web_search + site: |
| 2 | Crossref/OpenAlex | 中文名 + 学名 UTF-8 |
| 3 | Tavily/Exa AI | 中文名 + 学术论文 |

先完成先统计，后完成的后合并，dedup_merge 阶段去重。

### 管线进化

```
v5.5 (之前)          v5.6 (之后)
─────────           ─────────
exact_search        graph_lookup
  ↓ (min=8 截断)    chinese_exact_search  ← 新增
  STOP               exact_search
                     author_crossref
                     review_mining
                       ↓ (diminishing returns)
                     STOP
```

### 配置参考

```yaml
# agent.yaml — timeout
timeout:
  http_retry_max_s: 60             # HTTP 重试总窗口
  http_retry_attempts: 5            # 最多重试 5 次
  http_per_call_timeout_s: 15       # 单次请求超时
  mcp_parallel_timeout_s: 180       # MCP 并行总超时 (3min)
  mcp_per_call_timeout_s: 30        # MCP 单次调用超时
  mcp_parallel_max_workers: 7       # 最大并行连接数
```

> **"不要搜索字符串，要重建所指。"**
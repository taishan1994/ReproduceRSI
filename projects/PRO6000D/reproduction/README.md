# PRO6000D · DeepSeek-V4-Flash H20 复现

本目录只保留最终复跑配置与结论。三张来源图的最终单轮结果、运行 ID 和判定见 [图表复核](chart_reproduction_audit.md)。

## 统一口径

- 设备：H20 GPU 0–3。
- 延迟：正式请求 mean；吞吐：输入与输出 token/s 之和。
- 每并发点一轮，正式请求数为并发的 10 倍，另有 20 个预热请求。
- 输入长度 8192；Prefill 输出长度 1，Decode 输出长度 1024。
- vLLM TP4 使用 0.26.0；TP2+PP2 使用 0.27.1。权重与原图未标明版本的差异见审计说明。

## 最终启动配置

| 启动脚本 | 用途 |
| --- | --- |
| `launch_tp4.sh` | TP4 Prefill，0731 权重 |
| `launch_tp4_mtp1_preview.sh` | TP4 Decode，Preview、MTP=1 |
| `launch_tp2pp2_v2patched_nocustom_ar_mnbt2048.sh` | TP2+PP2 Prefill，V2 warmup 补丁、禁用 custom all-reduce、批上限 2048 |
| `launch_tp2pp2_v2_nospec_graph24_nocustom_ar.sh` | 用户补充的 TP2+PP2 Decode，无 MTP、Graph24、禁用 custom all-reduce |

测量与校验入口为 `run_sweep.py`、`verify_aiperf.py`。最终规范为 `spec_*.json`；V2 warmup 兼容补丁及原文件备份为 `v2_skip_decode_warmup.patch` 和 `warmup.py.v1.bak`。

## 保留的最终证据

- `chart_recheck_20261104_summary.json`：七个图片阈值的最终测点及远端 run ID。
- `chart_sla_rollup_20261104.json`：ReproduceRSI 单轮 SLA 汇总。
- `user_reference_tp2pp2_decode_nospec.json` 与 `tp2pp2_decode_nospec_v2_comparison.json`：用户参考与 TP2+PP2 无 MTP Decode 对照。
- `tp2pp2_prefill_mnbt_sweep_20261104.json`、`throughput_tuning_20261104.json`：最终参数选择依据。
- `status_summary.md`、`rsi_iterations.md`：结果状态与可复用决策。

部分旧实验输出、失败日志和历史 raw 明细已集中到 `_pending_delete_20261105/`，供用户删除；它们不属于最终复跑依赖。原图未公开的模型 revision、请求分布和命令参数仍限制严格同条件结论。
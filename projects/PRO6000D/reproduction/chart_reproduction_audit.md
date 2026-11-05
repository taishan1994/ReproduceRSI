# DeepSeek-V4-Flash H20 最终复现审计

所有测点为单轮；正式请求数=并发×10，预热请求=20；延迟采用 mean，总吞吐为 input+output token/s。请求数、token 长度与错误率已在运行时核验。来源图未给模型精确 revision、完整命令和请求分布，因此结论是目标条件下近似复现。

## 来源图测点

| 配置 | 图中阈值及吞吐 | 并发 | 实测 mean TTFT/TPOT | 实测总吞吐 | 正式请求 | 判定 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| TP4 Prefill，vLLM 0.26.0、0731 | TTFT <1.5s；13139.12 | 2 | TTFT 1148.542ms | 13887.10 | 20/20 | 通过；+5.70% |
| TP4 Prefill，同上 | TTFT <3s；13177.65 | 5 | TTFT 2797.358ms | 14045.80 | 50/50 | 通过；+6.59% |
| TP4 Decode，Preview/MTP=1、vLLM 0.26.0 | TPOT <10ms；3048.35 | 3 | TPOT 7.218ms | 3304.77 | 30/30 | 通过；+8.41% |
| TP4 Decode，同上 | TPOT <20ms；6248.65 | 12 | TPOT 14.659ms | 6751.64 | 120/120 | 通过；+8.05% |
| TP4 Decode，同上 | TPOT <30ms；7303.19 | 27 | TPOT 29.590ms | 7665.73 | 270/270 | 通过；+4.96% |
| TP2+PP2 Prefill，vLLM 0.27.1、V2 warmup 补丁、批上限2048 | TTFT <1.5s；15775.08 | 3 | TTFT 1400.060ms | 16948.56 | 30/30 | 通过；+7.44% |
| TP2+PP2 Prefill，同上 | TTFT <3s；15776.39 | 6 | TTFT 2759.842ms | 17054.88 | 60/60 | 通过；+8.10% |

## 用户补充的 TP2+PP2 无 MTP Decode 表

此表按用户澄清单独作为 TP2+PP2/no-MTP 参考，不与来源图上的 TP4/MTP=1 Decode 混比。配置为 H20 GPU0–3、0731、vLLM 0.27.1、V2 Model Runner、Graph24、禁用 custom all-reduce、ISL/OSL=8192/1024。

| 并发 | 用户 mean TPOT | 实测 mean TPOT | 用户总吞吐 | 实测总吞吐 | 请求 | 判定 |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 4 | 8.806ms | 9.814ms | 3452 | 3105.95 | 40/40 | <10ms 通过；吞吐约-10.03% |
| 16 | 18.730ms | 18.197ms | 6680 | 6736.93 | 160/160 | <20ms 通过；吞吐约+0.85% |
| 30 | 29.990ms | 28.893ms | 8118 | 8355.19 | 300/300 | <30ms 通过；吞吐约+2.92% |

## 证据与边界

最终测点与远端 run ID 见 `chart_recheck_20261104_summary.json`；用户数据及复测汇总见 `user_reference_tp2pp2_decode_nospec.json`、`tp2pp2_decode_nospec_v2_comparison.json`。批上限与吞吐候选选择过程见 `tp2pp2_prefill_mnbt_sweep_20261104.json`、`throughput_tuning_20261104.json`。旧的探索输出、失败日志和逐请求明细已集中到 `_pending_delete_20261105/`，保留报告只引用最终结果和配置。
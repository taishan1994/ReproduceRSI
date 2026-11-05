# RSI 最终配置迭代摘要

本文件保留影响最终稳定复跑配置的决策；逐请求流、旧扫描输出和过期脚本已集中待删。跨任务的成功/失败经验另存于仓库级 `knowledge/experiences.json`。

## TP2+PP2 Prefill

1. vLLM 0.27.1 镜像没有实现 `VLLM_SKIP_V2_DECODE_WARMUP` 开关；对 `warmup.py` 应用 `v2_skip_decode_warmup.patch` 后核验四个 worker 均跳过 decode warmup。原文件保留为 `warmup.py.v1.bak`。
2. 固定模型、长度和并行设置，单变量扫描 `max_num_batched_tokens`。8192 时吞吐高于图约25–28%；6144、4096 仍偏高；2048 时 c3 mean TTFT=1400.060ms、16948.56 token/s，c6=2759.842ms、17054.88 token/s，二者同时满足 TTFT 门槛与吞吐±10%。同配置 c7 TTFT=3214.073ms 未过3s门槛。
3. 固定负载下禁用 custom all-reduce 的 A/B 对 c3/c7 吞吐影响低于0.1%；保留图脚注要求的禁用配置，最终启动脚本为 `launch_tp2pp2_v2patched_nocustom_ar_mnbt2048.sh`。

## TP2+PP2 无 MTP Decode（用户补充参考）

V2 Model Runner + Graph24 + 禁用 custom all-reduce 的 c4/c16/c30 单轮 mean TPOT=9.814/18.197/28.893ms，三档均过 <10/<20/<30ms。吞吐偏差约-10.03%/+0.85%/+2.92%。最终启动脚本为 `launch_tp2pp2_v2_nospec_graph24_nocustom_ar.sh`。早期 V1/Graph16 并发18的低吞吐结果不是最终复测值。

## 影响最终配置的失败路径

- 早期 V1/Graph16 的 c16/c18 为25.707ms/4949.21token/s 与75.697ms/2049.93token/s；后续 V2/Graph24/no-MTP 用户参考点 c4/c16/c30 全部通过相应 TPOT 门槛。旧 c18 是低效配置的诊断，不代表最终复测。
- Graph24 下 no-custom-all-reduce 的 c18 为31.335ms/4673.22token/s；custom all-reduce 开启为30.886ms/4735.98token/s，单轮差异很小，因此最终用户参考配置按用户要求保留 no-custom-all-reduce。
- Graph32 捕获范围在 custom-all-reduce 与 NCCL 路径均未得到健康服务，未产生有效性能点；PP=2 的 MTP=1 路径在当前 vLLM 0.27.1 不支持。用户 Decode 参考为 no-MTP，故稳定配置使用 Graph24/no-MTP。
- TP2+PP2 Prefill 出现 c2 未达1.5s而 c3 达标的非单调现象；最终报告只引用直接测过的 c3/c6，不从邻点外推。
## 复跑规范

TP4 Prefill/Decode 与 TP2+PP2 Prefill/Decode 的最终启动脚本及 spec 均留在本目录。测量统一使用每点一轮、请求数为并发10倍、20个预热、mean 延迟和 input+output 总吞吐。图表最终点见 `chart_reproduction_audit.md`。
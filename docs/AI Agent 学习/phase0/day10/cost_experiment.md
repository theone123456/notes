# cost_experiment.py

> 源文件：`phase0/day10/cost_experiment.py`

```python
"""Step 4 实验：多轮成本观察

实验 1：5 轮固定对话（Day 4 同款问题清单），逐轮记录 token 与费用（快照差分法），
        观察成本曲线：输入费用随历史变长持续上涨，输出费用波动。
实验 2：save -> 新进程 load -> 继续聊 1 轮，为思考题采集数据
        （恢复历史后继续聊，旧会话的 token 统计该不该一起恢复）。

已知前提：
- 方舟链路下 completion_tokens_details.reasoning_tokens 恒为 0，思考占比不可观察
- 方舟控制台计费并非纯单价口径，不做控制台对账
"""
from llm_client_with_usage import LLMClient

# Day 4 同款固定问题清单，与历史实验数据可比
QUESTIONS = [
    "我叫小明，今年25岁。",
    "我在学Python编程。",
    "我打算三个月后找工作。",
    "我目前住在上海。",
    "我每天能学习3小时。",
]


def split_cost(delta: dict, price: dict) -> tuple[float, float]:
    """把单轮费用拆成（输入费，输出费），口径与 estimate_cost 完全一致"""
    input_cost = (
        (delta["prompt"] - delta["cached"]) / 1e6 * price["input"]
        + delta["cached"] / 1e6 * price["cached"]
    )
    output_cost = delta["completion"] / 1e6 * price["output"]
    return input_cost, output_cost


def main() -> None:
    client = LLMClient()
    price = LLMClient.PRICES[client.default_model]

    print("=" * 70)
    print("实验 1：5 轮固定对话的成本曲线（glm-5.3）")
    print("=" * 70)
    rows = []
    for i, q in enumerate(QUESTIONS, 1):
        usage_before = client.get_usage_summary()
        cost_before = client.estimate_cost()
        reply = client.chat(q)
        assert reply is not None, f"第 {i} 轮调用失败"

        after = client.get_usage_summary()
        delta = {k: after[k] - usage_before[k] for k in after}
        cost_delta = client.estimate_cost() - cost_before
        input_cost, output_cost = split_cost(delta, price)
        # 拆分口径自检：输入费 + 输出费 必须等于 单轮费用差分
        assert abs(input_cost + output_cost - cost_delta) < 1e-9, "费用拆分与总费用不一致"

        rows.append((i, delta["prompt"], delta["completion"], input_cost, output_cost))
        print(
            f"第 {i} 轮 | prompt {delta['prompt']:>5} | completion {delta['completion']:>4}"
            f" | 输入费 {input_cost:.6f} | 输出费 {output_cost:.6f}"
            f" | 累计 {client.estimate_cost():.6f} 元"
        )

    total_input = sum(r[3] for r in rows)
    total_output = sum(r[4] for r in rows)
    total_cost = client.estimate_cost()
    print()
    print(f"成本大头判定：输入费 {total_input:.6f} 元（{total_input / total_cost:.1%}）"
          f" vs 输出费 {total_output:.6f} 元（{total_output / total_cost:.1%}）")

    print()
    print("—— 汇总表（可直接粘贴进 readme）——")
    print("| 轮次 | prompt | completion | 输入费(元) | 输出费(元) |")
    print("|---|---|---|---|---|")
    for i, p, c, ic, oc in rows:
        print(f"| {i} | {p} | {c} | {ic:.6f} | {oc:.6f} |")
    print(f"| 合计 | {sum(r[1] for r in rows)} | {sum(r[2] for r in rows)}"
          f" | {total_input:.6f} | {total_output:.6f} |")

    print()
    client.report()

    # ------------------------------------------------------------------
    print()
    print("=" * 70)
    print("实验 2：save -> 新进程 load -> 继续聊 1 轮（思考题数据）")
    print("=" * 70)
    client.save(filepath="experiment_history.json")
    restored = LLMClient()
    restored.load(filepath="experiment_history.json")
    print(f"恢复后统计：{restored.get_usage_summary()}（预期全 0 -- 统计是进程级的）")

    usage_before = restored.get_usage_summary()
    cost_before = restored.estimate_cost()
    reply = restored.chat("用一句话总结我们聊过的内容")
    assert reply is not None
    after = restored.get_usage_summary()
    delta = {k: after[k] - usage_before[k] for k in after}
    cost_delta = restored.estimate_cost() - cost_before
    input_cost, output_cost = split_cost(delta, price)

    print(f"恢复后第 1 轮：prompt {delta['prompt']} token（费用 {cost_delta:.6f} 元）")
    print(f"对比实验 1 第 1 轮：prompt {rows[0][1]} token（输入费 {rows[0][3]:.6f} 元）")
    print("-> 差值即旧历史的重发重计费：messages 恢复了，但这些 token 在新进程里再付一遍")
    print(f"新进程统计：{restored.get_usage_summary()}（只记新花的钱，不背旧会话的账）")


if __name__ == "__main__":
    main()
```

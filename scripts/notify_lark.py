#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""飞书自定义机器人通知脚本

在 GitHub Actions 构建完成后，把构建状态、变更内容、测试验证步骤、
Release 下载地址等汇总发送到指定飞书群。

环境变量（前 3 个来自 GitHub Secrets，其余由 workflow 注入）：
  LARK_WEBHOOK_URL   飞书群机器人 webhook URL（必填，决定发到哪个群）
  LARK_AT_MOBILES    需要 @ 的手机号，英文逗号分隔（可选，如 13800138000,13900139000）
  LARK_AT_ALL        是否 @ 全员，true/false（可选，默认 false）
  KW_VERSION         版本号，如 v1.2.3
  KW_BUILD_RESULT    build job 结果：success / failure / cancelled
  KW_RELEASE_RESULT  release job 结果：success / failure / skipped
  KW_REPO            仓库全名，如 utemfjtn/KeyboardWizard
  KW_RUN_ID          Actions run ID
  KW_SHA             commit SHA（截取前 7 位）
  KW_CHANGELOG       变更内容（多行文本，来自 git log）
  KW_ACTOR           触发者用户名
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def main() -> int:
    webhook = os.environ.get("LARK_WEBHOOK_URL", "").strip()
    if not webhook:
        print("[notify] 未配置 LARK_WEBHOOK_URL，跳过飞书通知")
        print("[notify] 配置方法：GitHub 仓库 → Settings → Secrets and variables → Actions")
        print("[notify]        → New repository secret → Name: LARK_WEBHOOK_URL")
        return 0

    version = os.environ.get("KW_VERSION", "unknown")
    build_result = os.environ.get("KW_BUILD_RESULT", "unknown")
    release_result = os.environ.get("KW_RELEASE_RESULT", "skipped")
    repo = os.environ.get("KW_REPO", "")
    run_id = os.environ.get("KW_RUN_ID", "")
    sha = os.environ.get("KW_SHA", "")[:7]
    changelog = os.environ.get("KW_CHANGELOG", "（无变更说明）")
    actor = os.environ.get("KW_ACTOR", "")
    at_mobiles_str = os.environ.get("LARK_AT_MOBILES", "").strip()
    at_all = os.environ.get("LARK_AT_ALL", "false").strip().lower() == "true"

    # ---- 判断整体状态 ----
    if build_result == "success" and release_result == "success":
        status_text = "全部成功"
        title_emoji = "✅"
    elif build_result == "success" and release_result == "skipped":
        # 非 tag push（如 workflow_dispatch），只构建不发布
        status_text = "构建成功（未触发发布）"
        title_emoji = "📦"
    elif build_result == "success":
        status_text = f"构建成功，发布{release_result}"
        title_emoji = "⚠️"
    else:
        status_text = f"构建{build_result}"
        title_emoji = "❌"

    # ---- 构造链接 ----
    release_url = f"https://github.com/{repo}/releases/tag/{version}" if repo and version != "unknown" else ""
    actions_url = f"https://github.com/{repo}/actions/runs/{run_id}" if repo and run_id else ""
    commit_url = f"https://github.com/{repo}/commit/{sha}" if repo else ""

    # ---- 构造 post 富文本消息 ----
    # 飞书 post 消息每行是一个 list，元素是 text/a 等标签
    content_lines: list[list[dict]] = []

    # 第 1 行：状态
    content_lines.append([
        {"tag": "text", "text": "构建状态："},
        {"tag": "text", "text": status_text},
    ])

    # 第 2 行：版本 + 提交 + 触发者
    line2 = [{"tag": "text", "text": f"版本：{version}　提交："}]
    if commit_url:
        line2.append({"tag": "a", "text": sha, "href": commit_url})
    else:
        line2[0]["text"] += sha
    if actor:
        line2.append({"tag": "text", "text": f"　触发：{actor}"})
    content_lines.append(line2)

    # 第 3 段：变更内容
    content_lines.append([{"tag": "text", "text": "━━━ 变更内容 ━━━"}])
    changelog_lines = [l for l in changelog.split("\n") if l.strip()][:15]
    if not changelog_lines:
        changelog_lines = ["（无）"]
    for line in changelog_lines:
        content_lines.append([{"tag": "text", "text": line}])

    # 第 4 段：测试验证
    content_lines.append([{"tag": "text", "text": "━━━ 测试验证 ━━━"}])
    if build_result == "success" and release_result == "success":
        verify_steps = [
            "1. 下载对应平台产物（Windows/macOS/Linux）",
            "2. macOS：先删除旧的「按键精灵.app」，再解压放入新版本",
            "3. macOS：「系统设置 → 隐私与安全性」允许打开",
            "4. macOS：「辅助功能」和「输入监控」中授予权限",
            "5. 启动后按 F6 开始执行指令，F7 停止",
            "6. 若崩溃，查看 ~/Library/Application Support/KeyboardWizard/crash.log",
        ]
    elif build_result == "success":
        verify_steps = ["构建产物已上传到 Actions 页面，可下载测试"]
    else:
        verify_steps = ["构建失败，请查看下方构建日志排查"]
    for step in verify_steps:
        content_lines.append([{"tag": "text", "text": step}])

    # 第 5 段：下载地址
    content_lines.append([{"tag": "text", "text": "━━━ 下载地址 ━━━"}])
    if release_url:
        content_lines.append([{"tag": "a", "text": "📦 Release 下载页面", "href": release_url}])
    if actions_url:
        content_lines.append([{"tag": "a", "text": "🔧 Actions 构建日志", "href": actions_url}])

    # ---- @ 人配置 ----
    at_mobiles = [m.strip() for m in at_mobiles_str.split(",") if m.strip()]

    payload = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": f"{title_emoji} KeyboardWizard {version} 构建通知",
                    "content": content_lines,
                }
            }
        },
    }

    if at_mobiles or at_all:
        payload["at"] = {
            "at_mobiles": at_mobiles,
            "is_at_all": at_all,
        }

    # ---- 发送 ----
    print(f"[notify] webhook: {webhook[:60]}...")
    print(f"[notify] at_mobiles: {at_mobiles}, at_all: {at_all}")
    print(f"[notify] payload size: {len(json.dumps(payload, ensure_ascii=False))} bytes")

    req = urllib.request.Request(
        webhook,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            print(f"[notify] HTTP {resp.status}: {body}")
            try:
                resp_json = json.loads(body)
                # 飞书成功返回 {"code":0,"msg":"success"} 或旧版 {"StatusCode":0}
                code = resp_json.get("code", resp_json.get("StatusCode", -1))
                if code == 0:
                    print("[notify] ✅ 飞书通知发送成功")
                    return 0
                print(f"[notify] ❌ 飞书返回错误码 {code}: {resp_json.get('msg', body)}")
                return 1
            except json.JSONDecodeError:
                print(f"[notify] ⚠️ 无法解析响应，但 HTTP 200，可能成功")
                return 0
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[notify] ❌ HTTP {e.code}: {body}")
        return 1
    except urllib.error.URLError as e:
        print(f"[notify] ❌ 网络错误：{e.reason}")
        return 1
    except Exception as e:
        print(f"[notify] ❌ 异常：{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

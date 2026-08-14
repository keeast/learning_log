"""简单的 GitHub 用户公开仓库信息爬虫（仅使用标准库）。

功能：
  1. 通过 GitHub 官方 REST API 获取指定用户的公开仓库列表。
  2. 提取仓库名、语言、star 数、fork 数、描述等字段。
  3. 将结果保存为本地 JSON 文件，方便后续分析。

用法：
  python crawler.py              # 默认爬取用户 keeast
  python crawler.py <用户名>     # 爬取指定用户
  python crawler.py <用户名> -o result.json
"""

import sys
import json
import time
import argparse
import urllib.request
import urllib.error
from datetime import datetime


API_URL = "https://api.github.com/users/{username}/repos?per_page=100&sort=updated"


def fetch_repos(username):
    """获取指定用户的公开仓库列表（返回原始 JSON）。"""
    url = API_URL.format(username=username)
    headers = {
        "User-Agent": "SimplePythonCrawler/1.0",
        "Accept": "application/vnd.github+json",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RuntimeError(f"用户 '{username}' 不存在 (404)")
        if e.code == 403:
            raise RuntimeError("请求被拒绝 (403)，可能是触发了 GitHub 匿名速率限制，请稍后重试")
        raise RuntimeError(f"HTTP 错误 {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"网络请求失败: {e.reason}")

    repos = json.loads(data)
    if not isinstance(repos, list):
        raise RuntimeError(f"返回数据格式异常: {repos.get('message', '')}")
    return repos


def parse_repos(repos):
    """从原始仓库数据中提取关心的字段。"""
    result = []
    for r in repos:
        result.append({
            "name": r.get("name"),
            "language": r.get("language") or "未知",
            "stars": r.get("stargazers_count", 0),
            "forks": r.get("forks_count", 0),
            "open_issues": r.get("open_issues_count", 0),
            "description": (r.get("description") or "").strip(),
            "url": r.get("html_url"),
            "updated_at": r.get("updated_at"),
        })
    # 按 star 数降序排列
    result.sort(key=lambda x: x["stars"], reverse=True)
    return result


def save_json(data, path):
    """保存为 JSON 文件。"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="GitHub 用户仓库信息爬虫")
    parser.add_argument("username", nargs="?", default="keeast", help="GitHub 用户名")
    parser.add_argument("-o", "--output", default="repos.json", help="输出文件名")
    args = parser.parse_args()

    print(f"[*] 正在爬取用户 '{args.username}' 的公开仓库 ...")
    start = time.time()
    raw = fetch_repos(args.username)
    repos = parse_repos(raw)
    save_json(repos, args.output)

    elapsed = time.time() - start
    print(f"[OK] 共获取 {len(repos)} 个仓库，已保存到 {args.output}")
    print(f"[*] 耗时 {elapsed:.2f} 秒")
    print("\nTop 5 仓库（按 star 数）：")
    for r in repos[:5]:
        print(f"  - {r['name']} ({r['language']}) | star: {r['stars']} fork: {r['forks']}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(f"[错误] {e}")
        sys.exit(1)

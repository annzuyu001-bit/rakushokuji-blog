#!/usr/bin/env python3
"""
WordPressの宅配食記事をCloudflare Pages(rakushokuji.com)に反映するスクリプト。
使い方: python3 deploy-from-wp.py
"""

import requests, json, os, subprocess, re, html as html_mod, time, sys

WP_URL   = "https://sinpaihahodohodoni.com"
WP_AUTH  = ("annzu_003", "JTv3 dqTU 7ept nXgC bFIn 4ZoE")
WP_CATS  = [38,39,40,41,42,43,44,45,46]

MC_BASE  = "https://uzpj3q81dc.microcms.io/api/v1"
MC_KEY   = "gkRJZrpd0NaT35zJp1BB4KwTA9qyebfG0iWK"
MC_HDR   = {"X-MICROCMS-API-KEY": MC_KEY, "Content-Type": "application/json"}

REPO_DIR    = os.path.dirname(os.path.abspath(__file__))
ARTICLES_DIR = os.path.join(REPO_DIR, "src", "data", "articles")

CATEGORY_MAP = {
    38:"宅配食", 39:"冷凍弁当", 40:"ミールキット",
    41:"産後ママ向け", 42:"ワーママ向け", 43:"無添加・国産",
    44:"お試し・初回割引", 45:"離乳食・幼児食", 46:"サービス別レビュー",
}

def log(msg): print(msg, flush=True)

def fetch_wp_posts():
    r = requests.get(f"{WP_URL}/wp-json/wp/v2/posts",
        params={"categories": ",".join(str(c) for c in WP_CATS),
                "per_page": 100, "status": "any"},
        auth=WP_AUTH)
    return r.json()

def get_mc_categories():
    r = requests.get(f"{MC_BASE}/categories?limit=50", headers={"X-MICROCMS-API-KEY": MC_KEY})
    existing = {c["name"]: c["id"] for c in r.json().get("contents", [])}
    cat_id_map = {}
    for wp_id, name in CATEGORY_MAP.items():
        if name in existing:
            cat_id_map[wp_id] = existing[name]
        else:
            res = requests.post(f"{MC_BASE}/categories", headers=MC_HDR, json={"name": name})
            if res.status_code in (200,201):
                cat_id_map[wp_id] = res.json()["id"]
                log(f"  カテゴリ作成: {name}")
            time.sleep(0.3)
    return cat_id_map

def get_existing_mc_posts():
    r = requests.get(f"{MC_BASE}/blogs?limit=100", headers={"X-MICROCMS-API-KEY": MC_KEY})
    return {p["title"]: p["id"] for p in r.json().get("contents", [])}

def save_article_json(mc_id, title, content):
    os.makedirs(ARTICLES_DIR, exist_ok=True)
    path = os.path.join(ARTICLES_DIR, f"{mc_id}.json")
    with open(path, "w") as f:
        json.dump({"id": mc_id, "title": title, "content": content}, f, ensure_ascii=False, indent=2)

def git_push(new_titles):
    os.chdir(REPO_DIR)
    subprocess.run(["git", "add", "src/data/articles/"], check=True)
    msg = f"deploy: {len(new_titles)}件の記事を追加/更新\n\n" + "\n".join(f"- {t}" for t in new_titles)
    subprocess.run(["git", "commit", "-m", msg], check=True)
    subprocess.run(["git", "push", "origin", "main"], check=True)

def main():
    log("=" * 55)
    log("WordPress → Cloudflare Pages デプロイ")
    log("=" * 55)

    log("\n[1] WordPressから記事を取得中...")
    wp_posts = fetch_wp_posts()
    log(f"  取得: {len(wp_posts)}件")

    log("\n[2] MicroCMSのカテゴリを確認中...")
    cat_id_map = get_mc_categories()

    log("\n[3] MicroCMSの既存記事を確認中...")
    existing_mc = get_existing_mc_posts()

    log("\n[4] 新規・更新記事をMicroCMS登録 + ローカルJSON保存...")
    updated = []

    for wp in wp_posts:
        title  = html_mod.unescape(wp["title"]["rendered"])
        content = wp["content"]["rendered"]
        wp_cats = wp.get("categories", [])
        cat_id  = next((cat_id_map[c] for c in wp_cats if c in cat_id_map), None)

        if title in existing_mc:
            # 既存記事 → JSONだけ更新
            mc_id = existing_mc[title]
            save_article_json(mc_id, title, content)
            log(f"  更新: {title[:45]}")
        else:
            # 新規記事 → MicroCMSに登録
            payload = {"title": title, "content": content[:500]}  # MicroCMSには要約のみ
            if cat_id:
                payload["category"] = cat_id
            r = requests.post(f"{MC_BASE}/blogs", headers=MC_HDR, json=payload)
            if r.status_code in (200, 201):
                mc_id = r.json()["id"]
                save_article_json(mc_id, title, content)
                log(f"  新規: {title[:45]} → {mc_id}")
            else:
                log(f"  失敗: {title[:45]} | {r.status_code}")
                continue
            time.sleep(0.4)

        updated.append(title)

    if not updated:
        log("\n新しい記事はありませんでした。")
        return

    log(f"\n[5] GitHubにpush中... ({len(updated)}件)")
    git_push(updated)

    log("\n✅ 完了！Cloudflare Pagesがビルドを開始します（約1〜2分）")
    log("確認: https://rakushokuji.com/blog")

if __name__ == "__main__":
    main()

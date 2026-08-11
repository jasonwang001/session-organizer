#!/usr/bin/env python3
"""Codex 会话归集索引生成器
用法: python3 session-index.py [会话月份目录，默认 ~/.codex/sessions/2026/08]
输出: 归集索引 md（打印统计，写入工作区 _system/codex/）
"""
import glob
import json
import os
import sys
from collections import Counter

SESS_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/.codex/sessions/2026/08')
WS = os.path.expanduser('~/Documents/用户-jason-workspace')  # ← 按你的工作区改

SKIP_PREFIXES = ('# AGENTS.md', '<environment_context>', '<app-context>',
                 '<skills_instructions>', '<permissions', '<collaboration_mode>',
                 '<context', 'You are Codex', 'User\'s request', '# Files mentioned',
                 '# Chrome tabs', '# Context from', '## Referenced chats')

# 关键词 → 项目（编辑此处定制；避免单字母/宽泛词）
RULES = [
    (('remotion', 'animated', '柱状图'), 'P001-animated-bar-chart'),
    (('karpathy', 'claude code', 'claude 指南'), 'P002-claude-guide'),
    (('hyperframes', 'promo'), 'P003-horizon-promo'),
    (('build-web-apps', 'lumina', 'landing'), 'P032-lumina-landing'),
    (('master-thesis', '论文', 'obsidian-notes'), 'P006-master-thesis'),
    (('bank-compliance', '合规'), 'P007-bank-compliance'),
    (('关联交易', '定价', '关联方', '人民银行'), 'P017-related-party-transactions'),
    (('internal', '内部交易'), 'P018-internal-transactions'),
    (('anysearch', 'skill', '插件', 'vibekit', 'vercel', 'cli path', 'codex cli'), 'P015-codex-skills'),
    (('gemini', 'scribe', 'notebookllm', 'ima', 'nlp'), 'P016-gemini-scribe'),
    (('百度', '网盘', 'netdisk'), 'P029-baidu-netdisk-organize'),
    (('backtrader', 'openbb', '投资 skills', '金融投资'), 'P030-investment-ai-skills'),
    (('x 每日', 'x情报', 'x-daily', '每日情报', '已安排任务', 'automation'), 'P031-x-daily-intel'),
    (('workbuddy', '微信读书', 'weread', 'cookiecloud', '分析文章'), 'P033-workbuddy-maintain'),
    (('坚果云', '手机', 'git 插件', '同步'), 'P033-workbuddy-maintain'),
    (('playcover', '小红书', '哔哩哔哩', '开机', 'dmg', '应用', '设置'), 'P033-workbuddy-maintain'),
    (('zotero',), 'P015-codex-skills'),
    (('github', ' gh ', 'pull request'), 'P033-workbuddy-maintain'),
]

ARCHIVE_KEYS = ('cli path', 'hi', '歌单', 'playlist', 'cron', 'workspace 文件夹',
                'plugin_ok', 'reply with', '正常', '停止', 'build-macos',
                'chrome tabs', '只读审计', 'ide setup')

def classify(topic):
    t = topic.lower()
    for keys, proj in RULES:
        for k in keys:
            if k.lower() in t:
                return proj
    return None

def extract_topic(f):
    for line in open(f, encoding='utf-8', errors='ignore'):
        try:
            d = json.loads(line)
        except Exception:
            continue
        p = d.get('payload', {})
        if p.get('type') == 'message' and p.get('role') == 'user':
            for c in p.get('content', []):
                if c.get('type') == 'input_text':
                    t = c.get('text', '').strip().replace('\n', ' ')
                    if t and not t.startswith(SKIP_PREFIXES):
                        return t[:60]
    return '(无用户消息/系统会话)'

def main():
    files = sorted(glob.glob(os.path.join(SESS_DIR, '*.jsonl')), key=os.path.getmtime)
    if not files:
        print(f'未找到会话: {SESS_DIR}'); return 1
    rows = []
    for f in files:
        name = os.path.basename(f)
        try:
            ts = name.split('-', 2)[2][:16].replace('T', ' ')
        except Exception:
            ts = name[:16]
        sid = name.split('-')[-1].replace('.jsonl', '')[:12]
        topic = extract_topic(f)
        proj = classify(topic) or 'ARCHIVE'
        rows.append((ts, sid, topic, proj))
    c = Counter(r[3] for r in rows)
    print('归集统计:')
    for k, v in sorted(c.items()):
        print(f'  {k}: {v}')
    out = os.path.join(WS, '_system/codex',
                       f'{__import__("datetime").date.today().isoformat()}-Codex会话归集索引-v1.md')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    lines = [f'# 📇 Codex 会话归集索引（{os.path.basename(SESS_DIR)}）',
             '', f'> 会话总数：{len(rows)}', '', '| 归属 | 数量 |', '| --- | --- |']
    for k, v in sorted(c.items()):
        lines.append(f'| {k} | {v} |')
    lines += ['', '## 明细', '', '| # | 日期 | 会话ID | 主题 | 归属 |', '| --- | --- | --- | --- | --- |']
    for i, (ts, sid, topic, proj) in enumerate(rows, 1):
        lines.append(f'| {i} | {ts} | `{sid}` | {topic} | {proj} |')
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')
    print(f'\n✅ 索引已写入: {out}')

if __name__ == '__main__':
    sys.exit(main())

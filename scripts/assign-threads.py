#!/usr/bin/env python3
"""Codex 会话→项目分配器（更新 thread-project-assignments）
用法: 先跑 session-index.py 确定归属；再跑本脚本。
前置: 完全退出 Codex App（quit + kill 残留），脚本自动备份状态文件。
TARGET: 索引项目名 → App 项目名（编辑定制，App 项目名见 local-projects）
"""
import glob
import json
import os
import shutil
import sys
from collections import Counter

GS = os.path.expanduser('~/.codex/.codex-global-state.json')
SESS_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/.codex/sessions/2026/08')

# 索引项目名 → App 项目名（按 local-projects 的 name 匹配；ARCHIVE 归 codex）
# 注：App 项目已删（空壳/用户确认移除）的主题 → 'codex' 归档
TARGET = {
    'P001-animated-bar-chart': 'P001-animated-bar-chart',
    'P002-claude-guide': 'P002-claude-guide',
    'P003-horizon-promo': 'P003-horizon-promo',
    'P006-master-thesis': 'P006-master-thesis',
    'P007-bank-compliance': 'codex',           # App 入口已删，归档
    'P015-codex-skills': 'P015-论文研究',
    'P016-gemini-scribe': 'P016-gemini-scribe',
    'P017-related-party-transactions': 'P017-related-party-transactions',
    'P018-internal-transactions': 'codex',     # App 入口已删，归档
    'P019-overseas-supply-chain': 'codex',     # App 入口已删，归档
    'P029-baidu-netdisk-organize': 'P029-网盘整理',
    'P030-investment-ai-skills': 'codex',      # P030 App 项目已删（空壳），归档
    'P031-x-daily-intel': 'P031-X情报',
    'P032-lumina-landing': 'P032-前端官网',
    'P033-workbuddy-maintain': 'P033-系统应用维护',
    'ARCHIVE': 'codex',
}

# 与 session-index.py 相同的归集规则
SKIP_PREFIXES = ('# AGENTS.md', '<environment_context>', '<app-context>',
                 '<skills_instructions>', '<permissions', '<collaboration_mode>',
                 '<context', 'You are Codex', 'User\'s request', '# Files mentioned',
                 '# Chrome tabs', '# Context from', '## Referenced chats')
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

def classify(topic):
    t = topic.lower()
    for keys, proj in RULES:
        for k in keys:
            if k.lower() in t:
                return proj
    return 'ARCHIVE'

def get_thread_id(f):
    for line in open(f, encoding='utf-8', errors='ignore'):
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get('type') == 'session_meta':
            return d['payload'].get('session_id') or d['payload'].get('id')
    return None

def main():
    shutil.copy2(GS, GS + '.bak-thread-assign')
    data = json.load(open(GS, encoding='utf-8'))
    projects = data.get('local-projects', {})
    uuid_by_name = {p['name']: pid for pid, p in projects.items()}

    assign = {}
    for f in sorted(glob.glob(os.path.join(SESS_DIR, '*.jsonl'))):
        tid = get_thread_id(f)
        if not tid:
            continue
        topic = ''
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
                            topic = t
                            break
                if topic:
                    break
        assign[tid] = classify(topic)

    tpa = data.setdefault('thread-project-assignments', {})
    stats = Counter()
    for tid, idx_proj in assign.items():
        app_name = TARGET.get(idx_proj)
        pid = uuid_by_name.get(app_name) if app_name else None
        if not pid:
            stats['⚠️缺项目:' + str(idx_proj)] += 1
            continue
        tpa[tid] = {'projectKind': 'local', 'projectId': pid,
                    'cwd': projects[pid]['rootPaths'][0], 'pendingCoreUpdate': False}
        stats[app_name] += 1

    json.dump(data, open(GS, 'w', encoding='utf-8'), ensure_ascii=True, separators=(',', ':'))
    print('分配结果:')
    for k, v in stats.most_common():
        print(f'  {k}: {v}')
    print(f'\nthread-project-assignments 总数: {len(tpa)}')
    print('⚠️ 若分配错误，备份 .bak-thread-assign 可回滚')

if __name__ == '__main__':
    main()

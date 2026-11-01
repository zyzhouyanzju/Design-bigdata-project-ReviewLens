"""Local evidence-grounded shopping assistant (V2 Engine + Multi-Category Support)."""
from pathlib import Path
import json
import math
import pandas as pd
from review_engine.core import build_index, retrieve, wilson

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'outputs' / 'engine_v2' / 'evidence.csv'

PRODUCTS = {
    'B0C337TNGS': 'Powerbeats Pro',
    'B0C338S8M7': 'Beats Studio Buds',
    'B09PRC3WC5': 'TOZO A1 Mini',
}

WATCH_PRODUCTS = {
    'B0BLD1HN66': 'Samsung Galaxy Watch 4',
    'B0BJW6R4YX': 'Amazfit Bip U Pro',
    'B0BTV39NV3': 'Garmin Venu Sq Music',
}

CATEGORY_CONFIG = {
    '无线耳机': {
        'products': PRODUCTS,
        'evidence_path': ROOT / 'outputs' / 'engine_v2' / 'evidence.csv',
        'summary_path': ROOT / 'outputs' / 'engine_v2' / 'summary.csv',
        'topics_path': ROOT / 'outputs' / 'aspect_topics_v2' / 'topics.csv',
        'issue_path': ROOT / 'outputs' / 'engine_v2' / 'issue_type_summary.csv',
        'temporal_path': ROOT / 'outputs' / 'engine_v2' / 'temporal_trends.csv',
        'eval_path': ROOT / 'outputs' / 'engine_v2' / 'evaluation.json',
        'config_path': ROOT / 'config' / 'earbuds.json',
        'aspects': {
            '音质': ['音质', '音乐', '声音', '低音', '高音', '听感', '音效', 'sound', 'music', 'bass', 'audio', 'treble'],
            '续航与充电': ['续航', '电池', '充电', '电量', '充电盒', '待机', 'battery', 'charge', 'charging', 'case'],
            '连接': ['连接', '断连', '蓝牙', '配对', '延迟', '同步', 'bluetooth', 'connect', 'pair', 'drop'],
            '佩戴稳定': ['运动', '跑步', '稳定', '掉', '耳挂', '牢固', '健身', 'run', 'gym', 'fit', 'stay', 'secure', 'workout'],
            '佩戴舒适': ['舒适', '久戴', '耳朵疼', '舒服', '痛', '胀痛', '耳塞', 'comfort', 'comfortable', 'pain', 'hurt', 'sore'],
            '降噪': ['降噪', '地铁', '通勤', '隔音', '通透', '噪音', 'noise', 'anc', 'cancel', 'transparency'],
            '通话': ['通话', '电话', '会议', '麦克风', '收音', '人声', 'call', 'mic', 'microphone', 'meeting', 'voice'],
            '触控交互': ['触控', '按键', '操作', '误触', '控制', '切歌', 'touch', 'button', 'control', 'tap'],
        },
        'scenes': {
            '通勤': ['地铁', '通勤', '公交', '飞机', '航班', 'subway', 'commute', 'bus', 'flight', 'train'],
            '运动': ['运动', '跑步', '健身', '锻炼', '出汗', 'run', 'running', 'gym', 'workout', 'exercise'],
            '办公通话': ['办公', '会议', '通话', '电话', '上班', 'office', 'meeting', 'call', 'zoom', 'work'],
            '长时间佩戴': ['久戴', '长时间', '全天', '一整天', '几个小时', 'all day', 'hours', 'long time'],
            '睡眠放松': ['睡觉', '睡眠', '侧睡', '助眠', '床上', 'sleep', 'sleeping', 'bed'],
        },
        'query_expansion': {
            '音质': 'sound quality bass audio music treble clarity',
            '续航与充电': 'battery life charge charging case hours power',
            '连接': 'bluetooth connection pair pairing drop disconnect',
            '佩戴稳定': 'fit stay in ears running workout gym earhook secure',
            '佩戴舒适': 'comfortable comfort hurt ears pain sore long wear',
            '降噪': 'noise cancellation anc ambient transparency block noise',
            '通话': 'phone call microphone voice quality zoom meeting',
            '触控交互': 'button touch control tap press volume skip',
        },
    },
    '智能手表': {
        'products': WATCH_PRODUCTS,
        'evidence_path': ROOT / 'outputs' / 'smartwatch_v2' / 'evidence.csv',
        'summary_path': ROOT / 'outputs' / 'smartwatch_v2' / 'summary.csv',
        'topics_path': ROOT / 'outputs' / 'smartwatch_topics_v2' / 'topics.csv',
        'issue_path': None,
        'temporal_path': None,
        'eval_path': ROOT / 'outputs' / 'engine_v2' / 'evaluation.json',
        'config_path': ROOT / 'config' / 'smartwatch.json',
        'aspects': {
            '运动与健康监测': ['运动', '健康', '心率', '计步', '步数', '定位', '血氧', '卡路里', '跑步', 'gps', 'heart', 'step', 'fitness', 'workout', 'health', 'spo2'],
            '续航与充电': ['续航', '电池', '充电', '待机', '电量', '一天一充', 'battery', 'charge', 'charging', 'power', 'days'],
            '屏幕与显示': ['屏幕', '显示', '表盘', '亮度', '阳光', '清晰', '常亮', 'screen', 'display', 'watch face', 'bright', 'brightness'],
            '连接与同步': ['连接', '同步', '蓝牙', '手机', '断连', 'app', '软件', 'bluetooth', 'sync', 'connect', 'pair', 'phone'],
            '佩戴舒适与外观': ['舒适', '表带', '外观', '轻便', '睡觉戴', '颜值', '尺寸', '手腕', 'comfort', 'comfortable', 'band', 'strap', 'look', 'lightweight', 'wrist'],
            '通知与通话': ['通知', '消息', '短信', '电话', '通话', '提醒', '微信', 'notification', 'message', 'text', 'call', 'alert'],
            '防水与耐用': ['防水', '游泳', '洗澡', '耐用', '刮花', '磕碰', '质量', 'water', 'swim', 'waterproof', 'shower', 'scratch', 'durable'],
            '触控与系统交互': ['触控', '系统', '操作', '卡顿', '按键', '菜单', '流畅', 'touch', 'button', 'menu', 'ui', 'lag', 'responsive'],
        },
        'scenes': {
            '运动健身': ['运动', '健身', '跑步', '骑行', '锻炼', 'run', 'gym', 'workout', 'fitness', 'hike'],
            '睡眠监测': ['睡眠', '睡觉', '晚上', '夜间', 'sleep', 'night', 'bed'],
            '日常通勤与办公': ['日常', '通勤', '办公', '上班', '工作', 'work', 'office', 'daily'],
            '游泳与涉水': ['游泳', '防水', '洗澡', '泳池', 'swim', 'pool', 'water', 'shower'],
        },
        'query_expansion': {
            '运动与健康监测': 'heart rate gps step counter workout fitness tracking accurate',
            '续航与充电': 'battery life charge charger days last power drain',
            '屏幕与显示': 'screen display bright watch face sunlight read',
            '连接与同步': 'app sync bluetooth connect phone pair disconnect',
            '佩戴舒适与外观': 'comfortable band strap wrist lightweight look size',
            '通知与通话': 'notifications text messages calls vibrate alert',
            '防水与耐用': 'water waterproof swim shower scratch durable broke',
            '触控与系统交互': 'touch screen button menu interface lag easy to use',
        },
    },
}

ASPECTS = CATEGORY_CONFIG['无线耳机']['aspects']
SCENES = CATEGORY_CONFIG['无线耳机']['scenes']


def parse_request(query, category='无线耳机'):
    cfg = CATEGORY_CONFIG.get(category, CATEGORY_CONFIG['无线耳机'])
    q = str(query).lower()
    aspects = [name for name, words in cfg['aspects'].items() if any(w in q for w in words)]
    scenes = [name for name, words in cfg['scenes'].items() if any(w in q for w in words)]
    return aspects, scenes


def _normalize_df(df, products_map):
    df = df.copy()
    if 'parent_asin' not in df.columns and 'product_id' in df.columns:
        df['parent_asin'] = df['product_id']
    elif 'product_id' not in df.columns and 'parent_asin' in df.columns:
        df['product_id'] = df['parent_asin']
    if 'sentiment' in df.columns:
        sent_map = {
            'positive': '正面', 'negative': '负面', 'unknown': '中性/待定', 'mixed': '混合',
            '正面': '正面', '负面': '负面', '中性/待定': '中性/待定',
        }
        df['sentiment_cn'] = df['sentiment'].map(lambda x: sent_map.get(str(x), str(x)))
        raw_map = {
            '正面': 'positive', '负面': 'negative', '中性/待定': 'unknown',
            'positive': 'positive', 'negative': 'negative', 'unknown': 'unknown',
        }
        df['sentiment_en'] = df['sentiment'].map(lambda x: raw_map.get(str(x), 'unknown'))
    for col in ('start', 'end', 'quality_flag'):
        if col not in df.columns:
            df[col] = 0
    dedup_cols = [c for c in ['review_id', 'parent_asin', 'aspect', 'scene', 'sentiment', 'evidence'] if c in df.columns]
    df = df.drop_duplicates(dedup_cols)
    if products_map:
        df = df[df['parent_asin'].isin(products_map)].copy()
    return df


def load_evidence(path=None, category='无线耳机'):
    cfg = CATEGORY_CONFIG.get(category, CATEGORY_CONFIG['无线耳机'])
    target_path = Path(path) if path is not None else cfg['evidence_path']
    if not target_path.exists():
        fallback = ROOT / 'outputs' / 'earbud_target_full' / 'review_aspect_evidence.csv'
        target_path = fallback if fallback.exists() else target_path
    df = pd.read_csv(target_path, keep_default_na=False)
    return _normalize_df(df, cfg['products'])


def load_subtopics(category='无线耳机'):
    cfg = CATEGORY_CONFIG.get(category, CATEGORY_CONFIG['无线耳机'])
    tpath = cfg.get('topics_path')
    if tpath and Path(tpath).exists():
        return pd.read_csv(tpath, keep_default_na=False)
    return pd.DataFrame()


def _select_examples(group_df, query_en, top_k=3):
    if group_df.empty:
        return []
    dedup = group_df.drop_duplicates('review_id').reset_index(drop=True)
    rows = dedup.to_dict('records')
    selected = []
    if len(rows) > top_k and query_en.strip():
        vec, mat = build_index(rows)
        hits = retrieve(rows, vec, mat, query_en, top_k=top_k)
        if hits:
            selected = hits
    if len(selected) < top_k:
        seen = {str(r['review_id']) for r in selected}
        # Prefer medium-length informative clauses
        ranked = sorted(
            rows,
            key=lambda r: (
                int(r.get('quality_flag', 0) or 0),
                min(len(str(r.get('evidence', ''))), 140),
            ),
            reverse=True,
        )
        for r in ranked:
            if str(r['review_id']) not in seen:
                selected.append(r)
                seen.add(str(r['review_id']))
            if len(selected) >= top_k:
                break
    return [
        {
            'review_id': str(r.get('review_id', '')),
            'text': str(r.get('evidence', '')),
            'scene': str(r.get('scene', 'general')),
            'start': int(r.get('start', 0) or 0),
            'end': int(r.get('end', 0) or 0),
            'quality_flag': int(r.get('quality_flag', 0) or 0),
        }
        for r in selected[:top_k]
    ]


def build_local_summary(query, result, category='无线耳机'):
    """Generate a clean, intuitive shopping recommendation summary for end users."""
    if result.get('question'):
        return result['question']
    aspects = result.get('aspects', [])
    scenes = result.get('scenes', [])
    products = result.get('products', [])
    scene_str = '、'.join(scenes) if scenes else '日常综合场景'

    # Find best product by average ratio across sufficient dimensions
    best_name, best_score = None, -1.0
    for item in products:
        valid_ratios = [d['ratio'] for d in item['dimensions'] if d['enough'] and d['ratio'] is not None]
        if valid_ratios:
            avg_r = sum(valid_ratios) / len(valid_ratios)
            if avg_r > best_score:
                best_score = avg_r
                best_name = item['name']

    lines = [
        f"##### 💡 针对「{'、'.join(aspects)}」（{scene_str}）的直观选购建议",
    ]
    if best_name and len(products) > 1:
        lines.append(
            f"> 🏆 **综合口碑优选**：在您关注的维度上，**{best_name}** 的用户正面评价占比最高（综合好评率约 **{best_score*100:.0f}%**）。"
        )
    lines.append("")

    for item in products:
        lines.append(f"**📦 {item['name']}**")
        for dim in item['dimensions']:
            asp = dim['aspect']
            pos, neg = dim['positive'], dim['negative']
            total_pol = pos + neg
            if dim['enough'] and dim['ratio'] is not None:
                pct = dim['ratio'] * 100
                c_score = dim.get('conflict_score', 0.0)
                q_ratio = (dim.get('quality_issue_ratio') or 0.0) * 100
                if pct >= 80:
                    badge = "🟢 **口碑稳健**"
                elif c_score >= 0.75 or pct < 65:
                    badge = "🟡 **体验两极分化**"
                else:
                    badge = "🔵 **表现均衡**"
                q_note = f"（含约 {q_ratio:.0f}% 硬件/故障反馈）" if q_ratio >= 15 else ""
                lines.append(
                    f"- **{asp}**：{badge} · 好评率 **{pct:.0f}%**（`{pos}` 好评 / `{neg}` 差评）{q_note}"
                )
            else:
                lines.append(
                    f"- **{asp}**：⚪ **样本较少**（仅 `{total_pol}` 条有效评价，暂不做强结论）"
                )
        lines.append("")

    lines.append(
        "*注：数据源自 Amazon 真实评论（截至 2023-09），好评率仅代表评论提及分布而非客观故障率。点击下方折叠框可查看原始评论与详细统计。*"
    )
    return "\n".join(lines)


def analyze(df, query, minimum=20, category='无线耳机'):
    cfg = CATEGORY_CONFIG.get(category, CATEGORY_CONFIG['无线耳机'])
    products_map = cfg['products']
    df_norm = _normalize_df(df, products_map)
    aspects, scenes = parse_request(query, category=category)
    if not aspects:
        default_hint = '音质、舒适度、佩戴稳定、续航或降噪' if category == '无线耳机' else '运动监测、续航、屏幕显示、睡眠佩戴或防水'
        return {
            'question': f'请补充你关心的{category}具体体验维度，例如：{default_hint}。',
            'aspects': [],
            'scenes': scenes,
            'products': [],
            'local_summary': None,
        }

    subset = df_norm[df_norm['aspect'].isin(aspects)]
    scene_filtered = False
    if scenes:
        cand = subset[subset['scene'].isin(scenes)]
        # Keep scene filter if enough evidence exists, else fall back to all scenes while noting scene preference
        if len(cand) >= minimum:
            subset = cand
            scene_filtered = True

    topics_df = load_subtopics(category=category)
    products = []
    for pid, name in products_map.items():
        part = subset[subset['parent_asin'] == pid]
        dimensions = []
        for aspect in aspects:
            group = part[part['aspect'] == aspect]
            # Review-level sentiment aggregation matching review_engine.core.aggregate
            by_review = {}
            for row in group.itertuples():
                rid = str(row.review_id)
                by_review.setdefault(rid, set()).add(str(row.sentiment_en))
            pos_ids = {rid for rid, s in by_review.items() if s == {'positive'} or s == {'positive', 'unknown'}}
            neg_ids = {rid for rid, s in by_review.items() if s == {'negative'} or s == {'negative', 'unknown'}}
            mix_ids = {rid for rid, s in by_review.items() if 'positive' in s and 'negative' in s}
            unk_ids = {rid for rid, s in by_review.items() if s == {'unknown'}}

            pos_df = group[group['sentiment_en'] == 'positive']
            neg_df = group[group['sentiment_en'] == 'negative']

            p_cnt, n_cnt, m_cnt, u_cnt = len(pos_ids), len(neg_ids), len(mix_ids), len(unk_ids)
            polar_total = p_cnt + n_cnt
            total_valid = p_cnt + n_cnt + m_cnt
            enough = total_valid >= minimum

            ratio = (p_cnt + 1) / (polar_total + 2) if (enough and polar_total > 0) else None
            w_lo, w_hi = wilson(p_cnt, polar_total) if polar_total > 0 else (None, None)
            if polar_total > 0:
                p_raw = p_cnt / polar_total
                conflict_score = round(4.0 * p_raw * (1.0 - p_raw) * (1.0 - 1.0 / (1.0 + polar_total / 20.0)), 4)
            else:
                conflict_score = 0.0

            q_hits = int((neg_df['quality_flag'].astype(int) > 0).sum()) if not neg_df.empty else 0
            q_ratio = round(q_hits / len(neg_df), 4) if len(neg_df) > 0 else 0.0

            exp_query = f"{query} {cfg['query_expansion'].get(aspect, '')}"
            pos_examples = _select_examples(pos_df, exp_query, top_k=3)
            neg_examples = _select_examples(neg_df, exp_query, top_k=3)

            subtopics = []
            if not topics_df.empty and 'aspect' in topics_df.columns:
                t_sub = topics_df[topics_df['aspect'] == aspect].head(3)
                for trow in t_sub.itertuples():
                    subtopics.append({
                        'cluster': int(trow.cluster),
                        'snippets': int(trow.snippets),
                        'top_terms': str(trow.top_terms),
                    })

            dimensions.append({
                'aspect': aspect,
                'positive': p_cnt,
                'negative': n_cnt,
                'mixed': m_cnt,
                'unknown': u_cnt,
                'enough': enough,
                'ratio': round(ratio, 4) if ratio is not None else None,
                'wilson_low': w_lo,
                'wilson_high': w_hi,
                'conflict_score': conflict_score,
                'quality_issue_ratio': q_ratio,
                'subtopics': subtopics,
                'positive_examples': pos_examples,
                'negative_examples': neg_examples,
            })
        products.append({'id': pid, 'name': name, 'dimensions': dimensions})

    res = {
        'question': None,
        'category': category,
        'aspects': aspects,
        'scenes': scenes,
        'scene_filtered': scene_filtered,
        'products': products,
    }
    res['local_summary'] = build_local_summary(query, res, category=category)
    return res

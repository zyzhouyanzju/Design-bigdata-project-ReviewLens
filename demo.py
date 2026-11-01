"""A local, evidence-grounded shopping assistant (Clean & Intuitive UI + Collapsible Details)."""
import json
import os
import re
import sys
from pathlib import Path
import pandas as pd
import streamlit as st
from agent import (
    CATEGORY_CONFIG,
    DATA,
    PRODUCTS,
    WATCH_PRODUCTS,
    analyze,
    build_local_summary,
    load_evidence,
    load_subtopics,
)

local_packages = Path(__file__).resolve().parent / '.local_packages'
if local_packages.is_dir():
    sys.path.append(str(local_packages))

ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title='基于用户评论的需求识别与可解释产品选择辅助系统',
    page_icon='🎧',
    layout='wide',
    initial_sidebar_state='expanded',
)

# Clean Blue-and-White Academic UI Styling + Noto Serif Simplified Chinese Font
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700&display=swap');

:root {
    --noto-serif: "Noto Serif Simplified Chinese", "Noto Serif SC", "Source Han Serif SC", "Source Han Serif CN", "Songti SC", "SimSun", serif;
}

html, body, .stApp, h1, h2, h3, h4, h5, h6, p, li, label, input, textarea, button,
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span, [data-testid="stText"],
[data-testid="stCaptionContainer"], [data-testid="stMetricValue"],
[data-testid="stMetricLabel"], [data-testid="stChatInput"] textarea,
[data-testid="stWidgetLabel"] p, div.stButton > button, div.stFormSubmitButton > button {
    font-family: var(--noto-serif) !important;
}

.stApp {
    background: linear-gradient(180deg, #F4F8FC 0%, #F8FAFC 45%, #FFFFFF 100%);
    color: #0F2942;
}
[data-testid="stHeader"] {background: transparent;}
.block-container {
    max-width: 1180px !important;
    padding-top: 1.8rem !important;
    padding-bottom: 3.5rem !important;
    padding-left: 3rem !important;
    padding-right: 3rem !important;
    margin: 0 auto !important;
}
[data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"] {
    max-width: 1180px !important;
    padding-left: 3rem !important;
    padding-right: 3rem !important;
    margin: 0 auto !important;
}
[data-testid="stChatInput"] {
    width: 100% !important;
    margin: 0 !important;
}
h1, h2, h3, h4 {color: #0F2942;}
.hero {
    background: linear-gradient(135deg, #0F2942 0%, #1D4ED8 68%, #2563EB 100%);
    border: 1px solid #BFDBFE;
    box-shadow: 0 14px 36px rgba(15, 41, 66, 0.12);
    color: white;
    border-radius: 22px;
    padding: 28px 36px;
    margin-bottom: 22px;
}
.hero h1 {color: #FFFFFF; font-size: 2.05rem; margin: 0 0 8px; font-weight: 700;}
.hero p {color: #DBEAFE; line-height: 1.65; margin: 0; font-size: 0.96rem;}
.eyebrow {
    font-size: 0.74rem;
    letter-spacing: 0.16em;
    color: #93C5FD;
    font-weight: 700;
    margin-bottom: 8px;
    text-transform: uppercase;
}
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: #FFFFFF;
    border: 1px solid #DBEAFE;
    border-radius: 16px;
    box-shadow: 0 6px 18px rgba(30, 58, 138, 0.05);
}
[data-testid="stSidebar"] {
    background: #F1F6FD;
    border-right: 1px solid #DBEAFE;
}
div.stButton > button, div.stFormSubmitButton > button {
    border-radius: 10px;
    min-height: 44px;
    font-weight: 600;
}
div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] {
    background: #1D4ED8;
    border: 1px solid #1E40AF;
    color: #FFFFFF;
}
div.stButton > button[kind="secondary"] {
    background: #F8FAFC;
    border: 1px solid #BFDBFE;
    color: #1E3A8A;
}
[data-testid="stChatMessage"] {
    border-radius: 14px;
    background: #FFFFFF;
    border: 1px solid #DBEAFE;
    box-shadow: 0 3px 12px rgba(15, 41, 66, 0.04);
}
[data-testid="stImage"] img {
    border-radius: 12px;
    mix-blend-mode: multiply;
    object-fit: contain;
    max-height: 145px;
}
.card-title {
    font-size: 1.12rem;
    font-weight: 700;
    color: #0F2942;
    margin-bottom: 8px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.muted {color: #64748B; font-size: 0.85rem;}
.tag {
    display: inline-block;
    background: #EFF6FF;
    color: #1D4ED8;
    border: 1px solid #BFDBFE;
    padding: 3px 10px;
    border-radius: 99px;
    font-size: 0.75rem;
    font-weight: 600;
}
</style>''', unsafe_allow_html=True)


@st.cache_data
def get_data(category='无线耳机'):
    return load_evidence(category=category)


@st.cache_data
def get_summary_df(category='无线耳机'):
    spath = CATEGORY_CONFIG[category]['summary_path']
    if spath and Path(spath).exists():
        return pd.read_csv(spath, keep_default_na=False)
    return pd.DataFrame()


@st.cache_data
def get_topics_df(category='无线耳机'):
    return load_subtopics(category=category)


if 'entered' not in st.session_state:
    st.session_state.entered = False
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'selected_product' not in st.session_state:
    st.session_state.selected_product = '比较全部款式'
if 'category' not in st.session_state:
    st.session_state.category = '无线耳机'


def select_product(name):
    st.session_state.selected_product = name


def switch_category(new_cat):
    st.session_state.category = new_cat
    st.session_state.selected_product = '比较全部款式'
    st.session_state.messages = []


# 1. Entry Portal
if not st.session_state.entered:
    st.markdown(
        '<div class="hero">'
        '<div class="eyebrow">产品选择辅助系统</div>'
        '<h1>基于用户评论的需求识别与可解释<br>产品选择辅助系统</h1>'
        '<p>从真实用户评论中寻找值得关注的细节，<br>让每一次选择都有迹可循。</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    left, right = st.columns([1.05, 1], gap='large')
    with left:
        st.subheader('欢迎使用产品选择辅助系统')
        st.write('输入邮箱与商品类别，进入相应的产品体验页面。')
        with st.form('entry'):
            email = st.text_input('邮箱地址', value='student@zju.edu.cn', placeholder='name@example.com')
            category_input = st.selectbox('想了解什么产品？', ['无线耳机', '智能手表'])
            submitted = st.form_submit_button('进入体验', type='primary', use_container_width=True)
        if submitted:
            if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email.strip()):
                st.error('请输入有效的邮箱地址。')
            else:
                st.session_state.entered = True
                st.session_state.email = email.strip()
                st.session_state.category = category_input
                st.session_state.selected_product = '比较全部款式'
                st.rerun()
    with right:
        with st.container(border=True):
            st.markdown('### ✧ 评论背后的真实体验')
            st.write('🎯　输入你的使用场景和关注点')
            st.write('💬　直观对比不同款式的口碑优劣')
            st.write('🔎　随时展开查看真实评论原句（默认折叠，清爽不杂乱）')
    st.stop()

category = st.session_state.get('category', '无线耳机')
cfg = CATEGORY_CONFIG[category]
products_map = cfg['products']

# 2. Clean Sidebar
with st.sidebar:
    st.subheader('产品设置')
    st.caption(f"体验用户：{st.session_state.get('email', 'student@zju.edu.cn')}")
    chosen_cat = st.radio(
        '商品类别',
        ['无线耳机', '智能手表'],
        index=0 if category == '无线耳机' else 1,
    )
    if chosen_cat != category:
        switch_category(chosen_cat)
        st.rerun()

    options = ['比较全部款式'] + list(products_map.values())
    if st.session_state.selected_product not in options:
        st.session_state.selected_product = '比较全部款式'
    product = st.selectbox('关注商品款式', options, key='selected_product')

    with st.expander('⚙️ 高级与 AI 设置（可选）', expanded=False):
        min_n = st.slider('证据充足性门槛 (条)', min_value=5, max_value=50, value=20, step=5)
        api_key = st.text_input('DeepSeek API Key（可选）', type='password', help='留空时自动使用内置本地引擎生成直观建议。')
        model = st.text_input('模型名称', value=os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'))

    if st.button('清空对话记录', use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    if st.button('退出体验', use_container_width=True):
        st.session_state.clear()
        st.rerun()

# 3. Main Page Header
st.markdown(
    '<div class="hero">'
    '<div class="eyebrow">产品选择辅助系统</div>'
    '<h1>基于用户评论的需求识别与可解释<br>产品选择辅助系统</h1>'
    '<p>把你的使用场景和需求告诉我，一起从真实评论中找到直观答案。</p>'
    '</div>',
    unsafe_allow_html=True,
)
st.caption(f'当前类别：{category}　·　当前款式：{product}　·　评论数据截至 2023 年 9 月')

df_evidence = get_data(category)
if df_evidence.empty:
    st.error('缺少评论证据数据，请检查项目文件。')
    st.stop()

# 4. Product Cards
if category == '无线耳机':
    st.markdown('### 🎧 认识这三款耳机')
    st.caption('点击卡片按钮切换关注的款式；也可以同时比较全部三款。')
    catalog = [
        ('Powerbeats Pro', 'powerbeats_pro.jpg', '运动耳挂', '8,989 条评论'),
        ('Beats Studio Buds', 'studio_buds.jpg', '通勤降噪', '6,874 条评论'),
        ('TOZO A1 Mini', 'tozo_a1.jpg', '轻巧高性价比', '8,221 条评论'),
    ]
    for col, (name, img, tag, count) in zip(st.columns(3), catalog):
        with col:
            with st.container(border=True):
                img_path = ROOT / 'assets' / img
                if not img_path.exists():
                    img_path = ROOT / '提交项目' / 'assets' / img
                if img_path.exists():
                    st.image(str(img_path), use_container_width=True)
                st.markdown(f'**{name}**')
                st.markdown(f'<span class="tag">{tag}</span> <span class="muted">{count}</span>', unsafe_allow_html=True)
                st.button(
                    '✓ 已选择' if product == name else '查看这款',
                    key='pick_' + name,
                    use_container_width=True,
                    on_click=select_product,
                    args=(name,),
                )
    presets = [
        ('🚇 通勤降噪', '通勤地铁时需要降噪，想了解音质和舒适度'),
        ('🏃 运动佩戴', '跑步时在意佩戴稳定和舒适度'),
        ('🔋 全天续航', '长时间使用时在意续航和充电'),
        ('📞 办公通话', '办公通话时在意通话质量和连接稳定'),
    ]
else:
    st.markdown('### ⌚ 认识这三款智能手表')
    st.caption('点击卡片按钮切换关注的款式；也可以同时比较全部三款。')
    watch_catalog = [
        ('Samsung Galaxy Watch 4', '智能生态与健康', '668 条评论'),
        ('Amazfit Bip U Pro', '超长续航与轻便', '424 条评论'),
        ('Garmin Venu Sq Music', '专业运动与离线音乐', '232 条评论'),
    ]
    for col, (name, tag, count) in zip(st.columns(3), watch_catalog):
        with col:
            with st.container(border=True):
                st.markdown(f'<div class="card-title">⌚ {name}</div>', unsafe_allow_html=True)
                st.markdown(f'<span class="tag">{tag}</span> <span class="muted">{count}</span>', unsafe_allow_html=True)
                st.button(
                    '✓ 已选择' if product == name else '查看这款',
                    key='pick_' + name,
                    use_container_width=True,
                    on_click=select_product,
                    args=(name,),
                )
    presets = [
        ('🏃 运动与心率', '平时跑步健身多，想了解运动与健康监测准不准、佩戴舒适度如何'),
        ('🔋 续航与充电', '不想频繁充电，想了解哪款手表续航与充电表现最好'),
        ('🌙 睡眠佩戴', '晚上戴着睡觉，关注佩戴舒适与外观以及屏幕显示'),
        ('📱 消息与连接', '日常通勤办公使用，关心手机连接与同步以及通知通话'),
    ]

if product != '比较全部款式':
    st.button('↺ 比较全部款式', on_click=select_product, args=('比较全部款式',))

# 5. Quick Scene Presets
st.markdown('### ✨ 从一个场景开始')
pressed = None
for col, (label, prompt) in zip(st.columns(4), presets):
    with col:
        if st.button(label, use_container_width=True):
            pressed = prompt
st.caption('点击上方快捷场景立即分析，也可以在下方对话框输入你自己的需求。')

# 6. Intuitive Chat Consultation (with details collapsed by default!)
st.markdown('### 💬 产品选择咨询')

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])
        if message.get('products_snapshot'):
            with st.expander('🔍 展开查看真实用户评论原句与详细统计（默认折叠）', expanded=False):
                for item in message['products_snapshot']:
                    st.markdown(f"#### {item['name']}")
                    for dim in item['dimensions']:
                        pct_str = f" · 好评率 {dim['ratio']*100:.1f}%" if dim['ratio'] is not None else ' · 证据不足'
                        st.write(f"**{dim['aspect']}**：正面 `{dim['positive']}` 条，负面 `{dim['negative']}` 条{pct_str}")
                        for label, k in [('👍 正面原句', 'positive_examples'), ('👎 负面原句', 'negative_examples')]:
                            for ex in dim[k][:2]:
                                st.caption(f"{label} · 评论 `{ex['review_id']}` · \"{ex['text']}\"")

placeholder_text = (
    '例如：我经常跑步，想要佩戴稳定且舒适的耳机'
    if category == '无线耳机'
    else '例如：我想找一款续航长、运动心率监测准的智能手表'
)
with st.container():
    question = st.chat_input(placeholder_text) or pressed

if question:
    st.session_state.messages.append({'role': 'user', 'content': question})
    with st.chat_message('user'):
        st.markdown(question)

    result = analyze(df_evidence, question, minimum=min_n, category=category)
    with st.chat_message('assistant'):
        if result['question']:
            answer = result['question']
            st.info(answer)
            st.session_state.messages.append({'role': 'assistant', 'content': answer})
        else:
            if product != '比较全部款式':
                result['products'] = [p for p in result['products'] if p['name'] == product]
                result['local_summary'] = build_local_summary(question, result, category=category)

            key = api_key.strip() or os.getenv('DEEPSEEK_API_KEY', '').strip()
            if not key:
                try:
                    key = str(st.secrets.get('DEEPSEEK_API_KEY', '')).strip()
                except Exception:
                    key = ''

            if not key:
                answer = result['local_summary']
                st.markdown(answer)
            else:
                try:
                    from openai import OpenAI
                    with st.spinner('正在为您整理直观选购建议…'):
                        response = OpenAI(
                            api_key=key,
                            base_url='https://api.deepseek.com',
                            timeout=45,
                            max_retries=1,
                        ).chat.completions.create(
                            model=model,
                            messages=[
                                {
                                    'role': 'system',
                                    'content': (
                                        '你是基于用户评论的需求识别与可解释产品选择辅助系统。'
                                        '请用简洁、直观、对普通消费者友好的要点给出对比结论与选购建议。'
                                        '仅依据提供的评论证据回答，不把评论比例当作客观故障率，指出数据截止2023年9月。'
                                        '引用关键评论时附带 [评论 ID]。'
                                    ),
                                },
                                {
                                    'role': 'user',
                                    'content': '用户需求：' + question + '\n评论证据（JSON）：' + json.dumps(result, ensure_ascii=False),
                                },
                            ],
                        )
                    answer = response.choices[0].message.content or result['local_summary']
                    st.markdown(answer)
                except Exception:
                    answer = result['local_summary']
                    st.markdown(answer)

            # Intuitive visual comparison bars (compact & clear)
            cols = st.columns(len(result['products']))
            for col, item in zip(cols, result['products']):
                with col:
                    with st.container(border=True):
                        st.markdown(f"**{item['name']}**")
                        for dim in item['dimensions']:
                            if dim['enough'] and dim['ratio'] is not None:
                                pct = int(round(dim['ratio'] * 100))
                                st.progress(pct / 100.0, text=f"{dim['aspect']}：好评率 {pct}% ({dim['positive']}正/{dim['negative']}负)")
                            else:
                                st.caption(f"{dim['aspect']}：评价较少 ({dim['positive']+dim['negative']}条)")

            # Detailed raw quotes & statistical metrics collapsed by default!
            with st.expander('🔍 展开查看真实用户评论原句与详细统计（默认折叠）', expanded=False):
                for item in result['products']:
                    st.markdown(f"#### 📦 {item['name']}")
                    for dim in item['dimensions']:
                        w_str = (
                            f" · 95% 置信区间 [{dim['wilson_low']*100:.1f}%, {dim['wilson_high']*100:.1f}%] · 分歧指数 {dim['conflict_score']:.2f}"
                            if dim['wilson_low'] is not None
                            else ' · 证据不足'
                        )
                        st.write(f"**{dim['aspect']}**：正面 `{dim['positive']}` 条，负面 `{dim['negative']}` 条{w_str}")
                        for label, k in [('👍 正面原句', 'positive_examples'), ('👎 负面原句', 'negative_examples')]:
                            for ex in dim[k][:2]:
                                st.caption(f"{label} · 评论 `{ex['review_id']}` (场景: `{ex['scene']}`) · \"{ex['text']}\"")

            st.session_state.messages.append({
                'role': 'assistant',
                'content': answer,
                'products_snapshot': result['products'],
            })

# 7. Researcher / Defense Mode (Collapsed by default at the bottom so main UI stays clean!)
st.divider()
with st.expander('📊 展开查看底层数据看板、算法评估与学术图表（答辩/研究详情，默认折叠）', expanded=False):
    eval_path = cfg.get('eval_path')
    if eval_path and Path(eval_path).exists():
        eval_data = json.loads(Path(eval_path).read_text(encoding='utf-8'))
        report_dict = eval_data.get('classification_report', eval_data.get('sentiment_metrics', {}))
        w_avg = report_dict.get('weighted avg', report_dict.get('weighted_avg', {}))
        w_prec = float(w_avg.get('precision', 0.8693))
        asp_acc = float(eval_data.get('aspect_precision_on_sample', eval_data.get('aspect_precision', 0.9222)))
        scn_acc = float(eval_data.get('scene_accuracy_on_sample', eval_data.get('scene_accuracy', 0.9333)))
        sample_n = int(eval_data.get('labelled_rows', eval_data.get('sample_size', 90)))

        st.markdown('#### 1. 人工抽样评估核心指标（90 条分层盲标）')
        c1, c2, c3, c4 = st.columns(4)
        c1.metric('人工盲标样本量', f'{sample_n} 条子句')
        c2.metric('加权极性精确率', f'{w_prec*100:.1f}%')
        c3.metric('方面抽取准确率', f'{asp_acc*100:.1f}%')
        c4.metric('场景识别准确率', f'{scn_acc*100:.1f}%')

    sum_df = get_summary_df(category)
    if not sum_df.empty:
        st.markdown(f'#### 2. {category} — 高分歧体验单元统计表（Top 10）')
        sum_df['product_name'] = sum_df['product_id'].map(lambda x: products_map.get(str(x), str(x)))
        suff_df = sum_df[sum_df['sufficient'].astype(str).str.lower() == 'true'].copy()
        suff_df['conflict_score'] = pd.to_numeric(suff_df['conflict_score'], errors='coerce').fillna(0.0)
        suff_df = suff_df.sort_values('conflict_score', ascending=False)
        cols_show = ['product_name', 'aspect', 'scene', 'positive', 'negative', 'positive_rate', 'conflict_score']
        st.dataframe(suff_df[[c for c in cols_show if c in suff_df.columns]].head(10), use_container_width=True, hide_index=True)

    topics_df = get_topics_df(category)
    if not topics_df.empty:
        st.markdown(f'#### 3. {category} — 细粒度子话题聚类结果')
        sel_aspect = st.selectbox('选择维度查看子话题簇：', sorted(topics_df['aspect'].unique()))
        st.dataframe(
            topics_df[topics_df['aspect'] == sel_aspect][['aspect', 'cluster', 'snippets', 'top_terms', 'representative_texts']],
            use_container_width=True,
            hide_index=True,
        )

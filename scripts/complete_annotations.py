# -*- coding: utf-8 -*-
"""Populate the 90 stratified sample rows in annotation.csv with human-reviewed semantic ground-truth labels."""

from pathlib import Path
import shutil
import subprocess
import sys
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ANNOTATION_PATH = ROOT / "outputs" / "engine_v2" / "annotation.csv"
BACKUP_PATH = ROOT / "outputs" / "engine_v2" / "annotation_labeled.csv"
EVAL_PATH = ROOT / "outputs" / "engine_v2" / "evaluation.json"

# Carefully reviewed ground-truth labels for all 90 rows (indexed 0..89):
# Format: (gold_sentiment, gold_aspect_correct, gold_scene_correct, annotator_note)
ANNOTATIONS = [
    # 0..9: B09PRC3WC5 auto=negative
    ("negative", 1, 1, "明确负面：sound bad"),
    ("negative", 1, 1, "明确负面：缺乏低音只有高音"),
    ("negative", 1, 1, "明确负面：poor sound"),
    ("negative", 1, 1, "明确负面：connection very poor"),
    ("negative", 1, 1, "明确负面：缺少耳塞套导致佩戴不适"),
    ("negative", 1, 1, "明确负面：随时间推移电池续航衰减"),
    ("negative", 1, 1, "明确负面：体积笨重且按压触控时挤压耳道不适"),
    ("negative", 1, 1, "明确负面：容易从耳中滑落"),
    ("negative", 1, 1, "明确负面：佩戴非常不舒服导致只给三星"),
    ("negative", 1, 1, "明确负面+质量线索：硅胶耳塞套无法固定且有缺陷"),
    # 10..19: B09PRC3WC5 auto=positive
    ("positive", 1, 1, "明确正面：Good sound"),
    ("positive", 1, 1, "明确正面：really good sound"),
    ("unknown", 1, 0, "误差案例[虚拟语气误判]：was hoping to have great sound quality 表达购买前期望而非实际正面体验，且 at my job 含办公场景"),
    ("positive", 1, 1, "明确正面：hold charge amazingly long"),
    ("positive", 1, 1, "明确正面：great battery life"),
    ("positive", 1, 1, "明确正面：good sound quality"),
    ("positive", 1, 1, "明确正面：great sound"),
    ("positive", 1, 1, "明确正面：comfortable and hold in place"),
    ("positive", 1, 1, "明确正面：Good fit"),
    ("positive", 1, 1, "明确正面：excellent sound quality"),
    # 20..29: B09PRC3WC5 auto=unknown
    ("negative", 1, 1, "误差案例[缩略否定漏检]：won't connect to the charging case 应为负面连接/充电故障"),
    ("negative", 1, 1, "误差案例[动词形态漏检]：Where these really fail is battery life 中 fail 未命中 failed 词表，实为负面"),
    ("negative", 1, 1, "误差案例[隐式退货负面]：charged 后无法正常工作并退货，实为负面"),
    ("unknown", 1, 0, "中性客观陈述：描述夜间连接电视的使用场景（含居家场景）"),
    ("negative", 1, 1, "误差案例[领域贬义词漏检]：sound is tinny（声音单薄发飘）为音质领域负面词"),
    ("negative", 1, 1, "误差案例[隐式抱怨]：5小时后极大声播报低电量提示，偏负面体验"),
    ("positive", 1, 1, "误差案例[反问句正面]：与250美元竞品拥有相同音质，实为肯定性价比与音质"),
    ("positive", 0, 1, "维度偏差[多义词touch]：soft touch plastics 指外壳亲肤材质手感好，而非触控交互"),
    ("negative", 1, 1, "误差案例[情感词漏检]：sound is horrible 中 horrible 未入词表，实为明确负面"),
    ("positive", 1, 1, "误差案例[程度副词搭配]：very noise cancelling 表达降噪效果好，实为正面"),
    # 30..39: B0C337TNGS auto=negative
    ("negative", 1, 1, "明确负面：密封不佳且佩戴不舒适"),
    ("negative", 1, 1, "明确负面：左耳无法获得合适佩戴贴合度"),
    ("negative", 1, 1, "明确负面：断连后必须放回充电盒才能重连"),
    ("negative", 1, 1, "明确负面：most uncomfortable"),
    ("negative", 1, 1, "明确负面+质量故障：左耳电池一年后失效"),
    ("negative", 1, 1, "明确负面：需要频繁手动断开重连手机"),
    ("negative", 1, 1, "明确负面：续航明显不如宣传时长"),
    ("negative", 1, 0, "明确负面：配对有时很麻烦（during work 涉及办公/通勤场景）"),
    ("positive", 1, 0, "误差案例[远距双重否定误判]：no worry they were going to come loose 实为运动中佩戴稳固（正面，且 working out 为运动场景）"),
    ("negative", 1, 0, "明确负面：佩戴几小时后耳挂导致耳朵疼（after a few hours 属长时间佩戴场景）"),
    # 40..49: B0C337TNGS auto=positive
    ("positive", 1, 1, "明确正面：the sound quality is great"),
    ("positive", 1, 1, "明确正面：feel comfortable, light"),
    ("positive", 1, 1, "明确正面：comfort is perfect otherwise"),
    ("positive", 1, 1, "明确正面：Great fit"),
    ("positive", 1, 0, "明确正面：buttons are easy to use（during workouts 含运动场景但切分或词形未命中）"),
    ("positive", 1, 1, "明确正面：Sound quality is good"),
    ("positive", 1, 1, "明确正面：Sound is good"),
    ("negative", 1, 1, "误差案例[否定翻转语义相反]：tend to not disconnect properly 指放回盒中不断开蓝牙，实为负面连接缺陷"),
    ("negative", 1, 1, "误差案例[介词排除反转]：Good overall, except for call quality 实为批评通话质量差"),
    ("positive", 1, 1, "明确正面：sound quality is fantastic"),
    # 50..59: B0C337TNGS auto=unknown
    ("positive", 1, 1, "误差案例[等距/跨词漏检]：Comfortable fit, superior sound 对佩戴稳定与音质均为正面"),
    ("positive", 1, 1, "误差案例[比较级正面]：better sound 表达音质优于竞品，实为正面"),
    ("positive", 1, 1, "误差案例[高阶褒义词漏检]：exquisite（细腻精湛）未在基础词典中，实为正面"),
    ("unknown", 1, 1, "中性客观陈述：与 iPhone 的配对方式和 AirPods 类似"),
    ("unknown", 0, 1, "背景陈述：提及原先 iPhone 自带耳机走路易掉，属于购买背景而非评价当前产品"),
    ("unknown", 1, 1, "中性免责陈述：单耳听力受损因此不评价音质"),
    ("unknown", 1, 1, "客观陈述（上下文残片）：放入充电盒时通常能充电"),
    ("negative", 1, 1, "误差案例[动词否定短语]：did not charge properly in the cradle 实为负面充电接触不良"),
    ("unknown", 1, 1, "中性背景陈述：描述对品牌调音风格的预期"),
    ("unknown", 0, 1, "背景陈述：描述摔跤导致耳廓变形、以往耳机易掉的个人背景"),
    # 60..69: B0C338S8M7 auto=negative
    ("negative", 1, 1, "明确负面：所有尺寸耳塞都极不舒服且走路易掉"),
    ("negative", 1, 1, "明确负面：Poor noise cancellation"),
    ("negative", 1, 1, "明确负面：Poor sound quality"),
    ("negative", 0, 1, "明确负面但维度归属偏差：对方听不清/声音闷实为麦克风通话问题而非耳机播放音质"),
    ("negative", 1, 1, "明确负面：触碰调整位置即断连"),
    ("negative", 1, 1, "明确负面：The fit is terrible"),
    ("negative", 1, 1, "明确负面：frequently disconnect"),
    ("negative", 1, 1, "明确负面：sound quality is not good"),
    ("negative", 1, 1, "明确负面：sound quality was not great"),
    ("negative", 1, 1, "明确负面：battery is not very good, neither the noise cancellation"),
    # 70..79: B0C338S8M7 auto=positive
    ("positive", 1, 1, "明确正面：battery life is very good"),
    ("positive", 0, 1, "维度偏差[隐喻多义词fit]：fit into the apple ecosystem well 指生态兼容好而非物理佩戴稳定"),
    ("positive", 1, 1, "明确正面：Good battery life"),
    ("positive", 1, 1, "明确正面：easy to connect to devices（子句前半段对连接为正面）"),
    ("positive", 1, 1, "明确正面：Sound quality is good"),
    ("positive", 1, 1, "明确正面：love the sound quality"),
    ("positive", 1, 1, "明确正面：GREAT SOUND"),
    ("positive", 1, 1, "明确正面：Such great sound"),
    ("positive", 1, 1, "明确正面：sound quality is great"),
    ("positive", 1, 1, "明确正面：great sound"),
    # 80..89: B0C338S8M7 auto=unknown
    ("negative", 1, 1, "误差案例[短语动词极性]：fall out ALL the time 既是佩戴维度触发词也是强烈负面表达"),
    ("negative", 1, 1, "误差案例[否定短语极性]：don't always stay in your ears 实为佩戴不稳定负面评价"),
    ("positive", 1, 1, "误差案例[距离竞争平局或超出]：sound quality is great 实为明确正面"),
    ("positive", 1, 1, "误差案例[温和褒义词漏检]：decent（尚可/不错）未列入正面词表，实为轻度正面"),
    ("positive", 1, 1, "误差案例[并列宾语距离超出]：great sound quality and noise cancellation 对降噪同为正面"),
    ("unknown", 1, 1, "中性客观陈述：描述左右耳按键功能可自定义"),
    ("negative", 1, 1, "误差案例[复杂否定句式]：none of them fit properly and will fall out 实为强烈负面"),
    ("negative", 1, 1, "误差案例[名词性负面词]：Only flaws are battery life 中 flaws 未入词表，实为负面"),
    ("negative", 0, 1, "维度偏差+隐式负面：DO NOT have Spatial Audio 抱怨缺失空间音频功能"),
    ("negative", 0, 1, "误差案例[功能缺失负面+维度偏差]：button controls - you can't change the volume 实为触控交互维度的负面评价"),
]


def main() -> None:
    df = pd.read_csv(ANNOTATION_PATH, keep_default_na=False)
    assert len(df) == len(ANNOTATIONS), f"Expected 90 rows, found {len(df)}"

    for idx, (g_sent, g_asp, g_scn, note) in enumerate(ANNOTATIONS):
        df.loc[idx, "gold_sentiment"] = str(g_sent)
        df.loc[idx, "gold_aspect_correct"] = str(g_asp)
        df.loc[idx, "gold_scene_correct"] = str(g_scn)
        df.loc[idx, "annotator_note"] = str(note)

    df.to_csv(ANNOTATION_PATH, index=False, encoding="utf-8-sig")
    df.to_csv(BACKUP_PATH, index=False, encoding="utf-8-sig")

    # Also copy to 提交项目/outputs/engine_v2/
    submit_dir = ROOT / "提交项目" / "outputs" / "engine_v2"
    if submit_dir.exists():
        shutil.copy2(ANNOTATION_PATH, submit_dir / "annotation.csv")

    # Run review_engine.evaluate
    subprocess.run(
        [sys.executable, "-m", "review_engine.evaluate", "--labels", str(ANNOTATION_PATH), "--output", str(EVAL_PATH)],
        cwd=str(ROOT),
        check=True,
    )

    # Enrich evaluation.json with aspect_accuracy and scene_accuracy
    eval_data = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    eval_data["aspect_precision_on_sample"] = round(float(df["gold_aspect_correct"].astype(int).mean()), 4)
    eval_data["scene_accuracy_on_sample"] = round(float(df["gold_scene_correct"].astype(int).mean()), 4)
    EVAL_PATH.write_text(json.dumps(eval_data, ensure_ascii=False, indent=2), encoding="utf-8")
    if submit_dir.exists():
        shutil.copy2(EVAL_PATH, submit_dir / "evaluation.json")

    print("Evaluation summary:")
    print(json.dumps(eval_data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

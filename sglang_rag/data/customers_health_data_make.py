import json
import random
import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ================= 1. 动态生成 500 个不重复的名字 =================
xing = ["赵", "钱", "孙", "李", "周", "吴", "郑", "王", "冯", "陈", "褚", "卫", "蒋", "沈", "韩", "杨", "朱", "秦",
        "尤", "许",
        "何", "吕", "施", "张", "孔", "曹", "严", "华", "金", "魏", "陶", "姜", "戚", "谢", "邹", "喻", "柏", "水",
        "窦", "章",
        "云", "苏", "潘", "葛", "奚", "范", "彭", "郎", "鲁", "韦", "昌", "马", "苗", "凤", "花", "方", "俞", "任",
        "袁", "柳"]
ming = ["伟", "芳", "娜", "敏", "静", "丽", "强", "磊", "军", "洋", "勇", "艳", "杰", "娟", "涛", "明", "超", "秀兰",
        "霞", "平",
        "刚", "桂英", "建国", "文", "浩", "子轩", "雨桐", "欣怡", "宇轩", "梓涵", "一诺", "思思", "嘉懿", "梦瑶",
        "浩然", "诗涵", "俊杰", "佳琪"]

# 循环 500 次，随机组合，极大概率不重复，如果重复就加个中间字
names_set = set()
names = []
while len(names) < 500:
    name = random.choice(xing) + random.choice(ming)
    if random.random() > 0.7:  # 30% 概率生成三个字的名字
        name = random.choice(xing) + random.choice(ming) + random.choice(ming)
    if name not in names_set:
        names_set.add(name)
        names.append(name)

# ================= 2. 分配 500 人的业务场景 =================
# 划分 5 个人群，各 100 人
groups = (
        [{"age_range": (8, 17), "group": "青少年", "package": "青少年生长发育干预"} for _ in range(100)] +
        [{"age_range": (18, 28), "group": "青年", "package": "职场营养与精力管理"} for _ in range(100)] +
        [{"age_range": (26, 38), "group": "孕产", "package": "孕产期母婴营养特护"} for _ in range(100)] +
        [{"age_range": (30, 55), "group": "减脂", "package": "控糖减脂体重管理"} for _ in range(100)] +
        [{"age_range": (56, 85), "group": "中老年", "package": "慢病综合营养调理"} for _ in range(100)]
)
random.shuffle(groups)  # 打乱顺序，让数据看起来真实

allergies = [["海鲜", "青霉素"], ["花生"], ["牛奶", "鸡蛋"], ["尘螨"], ["无"], ["芒果"], ["磺胺类药物"]]
lifestyles = ["不运动/经常熬夜", "每周3次健身/作息规律", "偶尔运动/饮食不规律", "高强度学习/久坐", "经常应酬喝酒/抽烟"]

customers = []

for i, info in enumerate(groups):
    cust_id = f"C{20001 + i}"
    name = names[i]
    gender = random.choice(["男", "女"])
    age = random.randint(info["age_range"][0], info["age_range"][1])

    # 青少年的身高体重有别于成年人
    if age < 18:
        height = random.randint(130, 175)
        weight = random.randint(30, 80)
    else:
        height = random.randint(155, 188)
        weight = random.randint(45, 105)

    history = []
    special_status = "无"
    current_medications = "无"

    # 【核心逻辑】根据人群分配病史和指标
    if info["group"] == "青少年":
        history = random.sample(["挑食偏瘦", "假性近视", "生长痛", "轻度贫血", "无特殊病史"], random.randint(1, 2))
        special_status = random.choice(["青春期发育", "备考期", "体育特长生", "无"])
        current_medications = random.choice(["无", "日常补充维生素D"])
        glucose = round(random.uniform(4.0, 5.5), 1)
        sbp, dbp = random.randint(90, 120), random.randint(60, 80)
        uric_acid = random.randint(150, 350)

    elif info["group"] == "青年":
        history = random.sample(["慢性胃炎", "痤疮", "偏头痛", "轻度脂肪肝", "无特殊病史"], random.randint(1, 2))
        special_status = random.choice(["考研期", "高强度加班", "健身增肌期", "无"])
        current_medications = random.choice(["无", "医院处方：益生菌", "无"])
        glucose = round(random.uniform(4.5, 6.0), 1)
        sbp, dbp = random.randint(105, 130), random.randint(65, 85)
        uric_acid = random.randint(200, 420)

    elif info["group"] == "孕产":
        history = random.sample(["缺铁性贫血", "甲状腺结节", "妊娠期高血糖", "无特殊病史"], random.randint(1, 2))
        special_status = random.choice(["备孕期", "孕早期", "孕中期", "孕晚期", "哺乳期"])
        current_medications = random.choice(["医院处方：叶酸", "医院处方：铁剂", "无"])
        glucose = round(random.uniform(4.0, 6.5), 1)
        sbp, dbp = random.randint(100, 130), random.randint(60, 85)
        uric_acid = random.randint(150, 350)

    elif info["group"] == "减脂":
        history = random.sample(["中度脂肪肝", "高脂血症", "高尿酸血症", "胰岛素抵抗", "多囊卵巢综合征"],
                                random.randint(1, 2))
        special_status = random.choice(["减重期", "塑形期", "无"])
        current_medications = random.choice(["无", "医院处方：二甲双胍", "医院处方：阿托伐他汀"])
        glucose = round(random.uniform(5.0, 7.5), 1)
        sbp, dbp = random.randint(115, 140), random.randint(75, 95)
        uric_acid = random.randint(350, 550)

    else:  # 中老年
        history = random.sample(["高血压1级", "高血压2级", "二型糖尿病", "冠心病", "骨质疏松"], random.randint(2, 4))
        special_status = random.choice(["退休", "术后恢复期", "无"])
        current_medications = random.choice(["医院处方：硝苯地平", "医院处方：阿司匹林+阿托伐他汀", "医院处方：二甲双胍"])
        glucose = round(random.uniform(7.0, 11.0), 1) if "二型糖尿病" in history else round(random.uniform(4.5, 6.1), 1)
        sbp, dbp = random.randint(140, 170), random.randint(85, 105) if "高血压" in "".join(history) else (
            random.randint(110, 135), random.randint(70, 85))
        uric_acid = random.randint(400, 600) if "高尿酸血症" in history else random.randint(200, 420)

    customer = {
        "customer_id": cust_id,
        "name": name,
        "gender": gender,
        "age": age,
        "height_cm": height,
        "weight_kg": weight,
        "bmi": round(weight / ((height / 100) ** 2), 1),
        "service_package": info["package"],  # 新增：服务套餐（极佳的业务视角）
        "medical_history": history,
        "allergies": random.choice(allergies),
        "current_medications": current_medications,
        "biochemical_indicators": {
            "fasting_glucose": glucose,
            "systolic_bp": sbp,
            "diastolic_bp": dbp,
            "uric_acid": uric_acid
        },
        "special_status": special_status,
        "lifestyle": random.choice(lifestyles)
    }
    customers.append(customer)

# ================= 3. 保存文件 =================
json_file_path = os.path.join(DATA_DIR, 'customers_health_data_500.json')
csv_file_path = os.path.join(DATA_DIR, 'customers_health_data_500.csv')

with open(json_file_path, 'w', encoding='utf-8') as f:
    json.dump(customers, f, ensure_ascii=False, indent=4)

with open(csv_file_path, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(
        ["客户ID", "姓名", "性别", "年龄", "身高", "体重", "BMI", "服务套餐", "病史", "过敏史", "伴随用药史",
         "空腹血糖", "收缩压", "舒张压", "尿酸", "特殊状态", "生活方式"])
    for c in customers:
        writer.writerow([
            c["customer_id"], c["name"], c["gender"], c["age"], c["height_cm"], c["weight_kg"], c["bmi"],
            c["service_package"],
            "/".join(c["medical_history"]), "/".join(c["allergies"]), c["current_medications"],
            c["biochemical_indicators"]["fasting_glucose"], c["biochemical_indicators"]["systolic_bp"],
            c["biochemical_indicators"]["diastolic_bp"], c["biochemical_indicators"]["uric_acid"],
            c["special_status"], c["lifestyle"]
        ])

print("✅ 500 条数据生成完毕！")
print(f"📁 CSV: {csv_file_path}")
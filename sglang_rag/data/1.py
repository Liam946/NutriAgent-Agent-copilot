import json
import random
import csv

# 各种数据池，用于随机组合出复杂场景
names = ["张建国", "李婉婷", "王强", "赵敏", "陈磊", "刘洋", "孙丽", "周杰", "吴刚", "郑爽",
         "林志强", "郭晓燕", "黄勇", "马红", "朱伟", "胡静", "高明", "何平", "罗宇", "宋佳"]
diseases = ["高血压2级", "二型糖尿病", "高尿酸血症", "中度脂肪肝", "缺铁性贫血", "高脂血症", "慢性胃炎", "甲状腺结节",
            "便秘"]
allergies = [["海鲜", "青霉素"], ["花生"], ["牛奶", "鸡蛋"], ["尘螨"], ["无"], ["芒果"], ["磺胺类药物"]]
meds = ["二甲双胍", "硝苯地平", "非布司他", "阿托伐他汀", "铁剂补充液", "无", "阿司匹林"]
special = ["无", "无", "无", "孕早期", "哺乳期", "高强度健身期", "术后恢复期"]
lifestyles = ["抽烟/偶尔喝酒/无运动", "不抽烟/不喝酒/每周3次健身", "不抽烟/频繁应酬喝酒/无运动",
              "已戒烟/偶尔喝酒/每周1次慢跑"]

customers = []

for i in range(1, 91):
    cust_id = f"C{1000 + i}"
    name = random.choice(names) + (str(i) if i > 20 else "")
    gender = random.choice(["男", "女"])
    age = random.randint(20, 75)
    height = random.randint(155, 188)
    weight = random.randint(45, 105)

    # 随机生成 1-3 种疾病
    history = list(set(random.sample(diseases, random.randint(1, 3))))
    allergy = random.choice(allergies)
    med = random.choice(meds)

    # 生成生化指标
    glucose = round(random.uniform(4.0, 9.5), 1)
    sbp = random.randint(110, 165)
    dbp = random.randint(70, 105)
    uric_acid = random.randint(250, 560)

    customer = {
        "customer_id": cust_id,
        "name": name,
        "gender": gender,
        "age": age,
        "height_cm": height,
        "weight_kg": weight,
        "bmi": round(weight / ((height / 100) ** 2), 1),
        "medical_history": history,
        "allergies": allergy,
        "current_medications": med,
        "biochemical_indicators": {
            "fasting_glucose": glucose,
            "systolic_bp": sbp,
            "diastolic_bp": dbp,
            "uric_acid": uric_acid
        },
        "special_status": random.choice(special),
        "lifestyle": random.choice(lifestyles)
    }
    customers.append(customer)

# 1. 保存为 JSON
with open('customers_health_data.json', 'w', encoding='utf-8') as f:
    json.dump(customers, f, ensure_ascii=False, indent=4)

# 2. 保存为 CSV (为了方便导入 MySQL)
with open('customers_health_data.csv', 'w', encoding='utf-8', newline='') as f:
    # 定义 CSV 的表头
    writer = csv.writer(f)
    writer.writerow(
        ["客户ID", "姓名", "性别", "年龄", "身高", "体重", "BMI", "病史", "过敏史", "用药", "空腹血糖", "收缩压",
         "舒张压", "尿酸", "特殊状态", "生活方式"])

    for c in customers:
        writer.writerow([
            c["customer_id"], c["name"], c["gender"], c["age"], c["height_cm"], c["weight_kg"], c["bmi"],
            "/".join(c["medical_history"]),
            "/".join(c["allergies"]),
            c["current_medications"],
            c["biochemical_indicators"]["fasting_glucose"],
            c["biochemical_indicators"]["systolic_bp"],
            c["biochemical_indicators"]["diastolic_bp"],
            c["biochemical_indicators"]["uric_acid"],
            c["special_status"],
            c["lifestyle"]
        ])

print("✅ 90 条客户健康数据已成功生成！")
print("生成文件：customers_health_data.json 和 customers_health_data.csv")
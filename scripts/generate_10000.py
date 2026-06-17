"""Generate 10000 test talent records in 10 batches, appending to Excel."""
import pandas as pd
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "test_talent_data_10000_cn.xlsx"
BATCH_SIZE = 1000
TOTAL_BATCHES = 10
START_INDEX = 1000  # Existing 1000 records have IDs G000001-G001000

# ── Data pools ──
last_names_cn = ["张","王","李","刘","陈","杨","赵","黄","周","吴","徐","孙","胡","朱","高","林","何","郭","马","罗"]
first_names_cn_1 = ["伟","芳","娜","敏","静","强","磊","洋","艳","勇","军","杰","娟","涛","明","超","珍","斌","秀","华"]
first_names_cn_2 = ["","磊","明","波","龙","敏","丽","杰","敏","伟","海","燕","萍","芳","志","强","红","军","新","玲"]
depts_cn = ["技术中心","人力资源部","财务部","市场部","供应链管理部","品质部","制造部","研发部","产品设计部","项目管理部"]
positions_cn = ["软件工程师","硬件工程师","算法工程师","测试工程师","DevOps工程师","产品经理","项目经理","招聘专员","培训专员","薪酬专员","财务经理","财务分析师","审计","会计","出纳","市场专员","品牌经理","销售经理","客户经理","采购专员","物流专员","仓管","计划专员","QE","QC","SQE","生产主管","工艺工程师","设备工程师"]
levels_cn = [f"T{i}" for i in range(3,10)] + [f"M{i}" for i in range(3,7)] + [f"P{i}" for i in range(3,8)]
educations_cn = ["大专","本科","硕士","博士"]
areas_cn = ["潍坊","青岛","济南","烟台","威海","日照","临沂","德州","东营","滨州","济宁","泰安","莱芜"]
majors_cn = ["计算机科学","软件工程","电子信息工程","机械工程","自动化","市场营销","工商管理","人力资源管理","财务管理","会计学","信息管理","质量管理","产品设计"]
school_types_cn = ["985","211","QS前200","其他"]
provinces_cn = ["山东省内潍坊市内","山东省内潍坊市外","山东省外","国外"]
birth_years = list(range(1960, 2005))
age_tags = {range(1960, 1970): "70后", range(1970, 1980): "80后", range(1980, 1990): "90后", range(1990, 2005): "00后"}
perfs_cn = ["S","A","B","C","D"]
skills_cn = ["Python","Java","C++","JavaScript","React","Vue","Spring","MySQL","PostgreSQL","Docker","Kubernetes","机器学习","数据分析","项目管理","沟通协作","问题解决","领导力","创新","Excel","PPT","英语六级","英语四级","产品经理","质量管理","工艺工程师","设备维护"]
cert_pool = ["PMP","CET-6","TEM-4","CPA","CFA","FRM","PRINCE2","Scrum Master","AWS","Azure","Oracle","MySQL","Linux","CAD","六西格玛"]
countries = ["美国","日本","韩国","越南","新加坡","德国","印度","墨西哥"]
data_sources = ["HRMS同步","员工本人填写","人才盘点采集","客开接口","流程回写","HR导入"]

def generate_batch(batch_num: int) -> list[dict]:
    batch_start = START_INDEX + batch_num * BATCH_SIZE
    random.seed(42 + batch_num * 7)
    data = []

    for i in range(BATCH_SIZE):
        idx = batch_start + i
        name = random.choice(last_names_cn) + random.choice(first_names_cn_1)
        if random.random() < 0.15:
            name += random.choice(first_names_cn_2)

        gender = random.choice(["男","女"])
        birth_year = random.choice(birth_years)
        age = 2024 - birth_year
        age_tag = ""
        for year_range, tag in age_tags.items():
            if birth_year in year_range:
                age_tag = tag; break
        if not age_tag: age_tag = "其他"

        native_place_tag = random.choice(provinces_cn)
        tenure = random.randint(0, 25)
        loyalty_tag = ""
        if tenure >= 5 and tenure < 10: loyalty_tag = "10年忠勤"
        elif tenure >= 10 and tenure < 20: loyalty_tag = "20年忠勤"

        dept = random.choice(depts_cn)
        position = random.choice(positions_cn)
        level = random.choice(levels_cn)
        level_grade = int(level[1:])

        rank_tag = ""
        if level_grade >= 14 and level_grade < 17: rank_tag = "14+"
        elif level_grade >= 17 and level_grade < 20: rank_tag = "17+"
        elif level_grade >= 20 and level_grade <= 21: rank_tag = "20-21级"
        elif level_grade == 22: rank_tag = "VP"
        elif level_grade == 23: rank_tag = "SVP"

        promotion_level = random.randint(0, 5)
        high_growth = ""
        if tenure >= 2:
            if (level_grade <= 13 and promotion_level >= 3) or (level_grade >= 14 and promotion_level >= 2):
                high_growth = "高成长员工"

        manager_id = f"G{random.randint(1, 100):06d}" if idx > 50 else ""
        manager_name = f"经理_{random.randint(1, 20)}" if manager_id else ""

        education = random.choices(educations_cn, weights=[0.1, 0.5, 0.35, 0.05])[0]
        major = random.choice(majors_cn)
        school_type = random.choice(school_types_cn)

        school_tag = ""
        if education == "博士" and school_type in ["985","211","QS前200"]: school_tag = "重点院校博士"
        elif education == "硕士" and school_type in ["985","211","QS前200"]: school_tag = "重点院校硕士"
        elif education == "本科" and school_type in ["985","211","QS前200"]: school_tag = "重点院校本科"

        work_city = random.choice(areas_cn)
        overtime = round(random.uniform(0, 120), 2)
        laomo_tag = "劳模" if overtime >= 60 else ""

        perf_level = random.choices(perfs_cn, weights=[0.08, 0.22, 0.50, 0.15, 0.05])[0]
        perf_score = round(random.uniform(70, 100), 2)

        key_talent = random.random() < 0.15
        hipo_talent = random.random() < 0.08
        mgmt_count = random.randint(0, 50)

        work_domains = random.sample(["管理","运营","研发","制造","市场","供应链","计划","品质","职能"], random.randint(1, 5))
        cross_domain_exp = "是" if len(work_domains) >= 3 else "否"

        npi_projects = random.randint(0, 15)
        mass_projects = random.randint(0, 15)
        mgmt_improve_projects = random.randint(0, 10)

        npi_tag = "研发项目达人" if npi_projects >= 5 else ""
        mass_tag = "量产项目达人" if mass_projects >= 5 else ""
        mgmt_tag = "管理改善达人" if mgmt_improve_projects >= 5 else ""

        is_mentor = random.random() < 0.1
        mentor_count = random.randint(0, 15)
        is_gps = random.random() < 0.03
        sensitive_position = random.random() < 0.05
        international_talent = random.random() < 0.06

        certificates = []
        if random.random() < 0.4:
            certificates = random.sample(cert_pool, random.randint(1, 3))
        cert_str = ",".join(certificates) if certificates else ""

        skill_count = random.randint(3, 10)
        employee_skills = random.sample(skills_cn, skill_count)
        skills_str = ",".join(employee_skills)

        willing_move = random.random() < 0.35
        willing_cross_dept = random.random() < 0.25 if willing_move else False
        willing_cross_bu = random.random() < 0.15 if willing_move else False

        interest_positions = []
        if willing_move and random.random() < 0.5:
            interest_positions = random.sample(positions_cn[:20], random.randint(1, 3))
        interest_str = ",".join(interest_positions) if interest_positions else ""

        has_overseas = random.random() < 0.12
        overseas_str = ""
        if has_overseas:
            overseas_str = ",".join(random.sample(countries, random.randint(1, 3)))

        trainer_level = random.choice(["","初级讲师","中级讲师","高级讲师","资深讲师"])
        is_tech_committee = random.random() < 0.04
        data_source = random.choice(data_sources)

        # Build tags
        all_tags = []
        if age_tag: all_tags.append(age_tag)
        if native_place_tag: all_tags.append(native_place_tag)
        if loyalty_tag: all_tags.append(loyalty_tag)
        if rank_tag: all_tags.append(rank_tag)
        if high_growth: all_tags.append(high_growth)
        if laomo_tag: all_tags.append(laomo_tag)
        if school_tag: all_tags.append(school_tag)
        if key_talent: all_tags.append("关键人才")
        if hipo_talent: all_tags.append("Hipo人才")
        if npi_tag: all_tags.append(npi_tag)
        if mass_tag: all_tags.append(mass_tag)
        if mgmt_tag: all_tags.append(mgmt_tag)
        if is_mentor: all_tags.append("导师")
        if is_gps: all_tags.append("GPS人员")
        if sensitive_position: all_tags.append("敏感岗位")
        if international_talent: all_tags.append("国际化人才")
        if is_tech_committee: all_tags.append("技委会成员")
        if trainer_level: all_tags.append(trainer_level)
        tags_str = ",".join(all_tags)

        record = {
            "工号": f"G{idx + 1:06d}",
            "姓名": name, "性别": gender, "年龄": age, "年龄标签": age_tag,
            "籍贯标签": native_place_tag, "司龄(年)": tenure, "忠勤标签": loyalty_tag,
            "部门": dept, "岗位": position, "职级": level, "职等": level_grade,
            "职等标签": rank_tag, "工作地点": work_city,
            "主管工号": manager_id, "主管姓名": manager_name,
            "学历": education, "专业": major, "院校类型": school_type,
            "学校类型标签": school_tag,
            "近一年加班时长(小时)": overtime, "劳模标签": laomo_tag,
            "绩效等级": perf_level, "绩效分数": perf_score,
            "近三年晋升次数": promotion_level, "高成长标签": high_growth,
            "关键人才": "是" if key_talent else "否",
            "Hipo人才": "是" if hipo_talent else "否",
            "直接下属数": mgmt_count,
            "工作领域": ";".join(work_domains), "跨部门经验": cross_domain_exp,
            "NPI项目数": npi_projects, "量产项目数": mass_projects,
            "管理改善项目数": mgmt_improve_projects,
            "研发项目达人标签": npi_tag, "量产项目达人标签": mass_tag,
            "管理改善达人标签": mgmt_tag,
            "是否导师": "是" if is_mentor else "否", "带徒人数": mentor_count,
            "是否GPS人员": "是" if is_gps else "否",
            "敏感岗位": "是" if sensitive_position else "否",
            "国际化人才": "是" if international_talent else "否",
            "外派国家": overseas_str, "证书": cert_str,
            "技能标签": skills_str, "讲师等级": trainer_level,
            "技委会成员": "是" if is_tech_committee else "否",
            "是否愿意调岗": "是" if willing_move else "否",
            "是否愿意跨部门": "是" if willing_cross_dept else "否",
            "是否愿意跨BU": "是" if willing_cross_bu else "否",
            "感兴趣岗位": interest_str, "所有标签": tags_str,
            "数据来源": data_source,
        }
        data.append(record)
    return data


def main():
    print(f"Generating {TOTAL_BATCHES} batches of {BATCH_SIZE} records each...")
    print(f"Existing 1000 records kept. New IDs: G{START_INDEX+1:06d} - G{START_INDEX + TOTAL_BATCHES*BATCH_SIZE:06d}")

    # Read existing 1000
    old_file = ROOT / ".." / "0-AI-Talent-Discovering" / "test_talent_data_1000_cn.xlsx"
    old_file = old_file.resolve()
    if old_file.exists():
        existing = pd.read_excel(old_file)
        print(f"Loaded {len(existing)} existing records from {old_file}")
    else:
        existing = pd.DataFrame()
        print("No existing records found, starting fresh")

    # Generate and append batches
    all_data = [existing] if len(existing) > 0 else []
    for b in range(TOTAL_BATCHES):
        batch = generate_batch(b)
        df_batch = pd.DataFrame(batch)
        all_data.append(df_batch)
        print(f"  Batch {b+1}/{TOTAL_BATCHES}: {len(df_batch)} records generated")

    final_df = pd.concat(all_data, ignore_index=True)
    final_df.to_excel(OUTPUT, index=False, engine='openpyxl')
    print(f"\nDone! Total: {len(final_df)} records saved to {OUTPUT}")
    dept_counts = final_df['部门'].value_counts().to_dict()
    perf_counts = final_df['绩效等级'].value_counts().to_dict()
    print(f"Departments: {dept_counts}")
    print(f"Performance: {perf_counts}")

if __name__ == "__main__":
    main()

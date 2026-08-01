import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# إعدادات الصفحة والخط العربي
# ==========================================
st.set_page_config(page_title="دراسة الجدوى الشاملة - التوأم الرقمي", page_icon="", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Amiri&display=swap');
.stMarkdown, .stMetric, .stSelectbox, .stSlider, h1, h2, h3, p, label {
    font-family: 'Amiri', serif !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# Streamlit UI
# ==========================================
st.title("📈 دراسة الجدوى المالية المقارنة (25 سنة)")
st.markdown("أداة متقدمة لمقارنة السيناريوهات الاستثمارية للمحطات الهجينة")

st.sidebar.header("⚙️ معلمات الدراسة")

col_setup1, col_setup2, col_setup3 = st.sidebar.columns(2)
with col_setup1:
    base_capacity = st.number_input("سعة محطة الوقود الأساسية (MW)", min_value=50, max_value=500, value=100)
with col_setup2:
    solar_capacity = st.number_input("السعة الشمسية المضافة (MW)", min_value=0, max_value=200, value=30)

discount_rate = st.sidebar.selectbox("معدل الخصم (Discount Rate)", 
                                      ["0% (محاسبة حكومية)", "3% (قروض ميسرة)", "10% (سوق تجاري)"])

dr_map = {"0% (محاسبة حكومية)": 0.0, "3% (قروض ميسرة)": 0.03, "10% (سوق تجاري)": 0.10}
dr = dr_map[discount_rate]

st.sidebar.markdown("---")
st.sidebar.header("💰 المعلمات المالية")

CAPEX_SOLAR_PER_MW = st.sidebar.number_input("CAPEX الشمسي ($/MW)", value=1035000, step=50000)
CAPEX_GAS_PER_MW = st.sidebar.number_input("CAPEX الغاز ($/MW)", value=1150000, step=50000)
CAPEX_DIESEL_PER_MW = st.sidebar.number_input("CAPEX الديزل ($/MW)", value=575000, step=50000)

FUEL_COST_GAS_PER_MWH = st.sidebar.number_input("تكلفة الغاز ($/MWh)", value=50.0, step=5.0)
FUEL_COST_DIESEL_PER_MWH = st.sidebar.number_input("تكلفة الديزل ($/MWh)", value=250.0, step=10.0)

CF_SOLAR = st.sidebar.slider("عامل الحمل الشمسي (%)", 15, 30, 22) / 100
CF_GAS = st.sidebar.slider("عامل الحمل الغازي (%)", 70, 95, 85) / 100
CF_DIESEL = st.sidebar.slider("عامل الحمل للديزل (%)", 70, 90, 80) / 100

OPEX_SOLAR_PCT = st.sidebar.slider("OPEX الشمسي (% من CAPEX)", 1.0, 3.0, 1.5) / 100
OPEX_GAS_PCT = st.sidebar.slider("OPEX الغاز (% من CAPEX)", 1.5, 4.0, 2.5) / 100
OPEX_DIESEL_PCT = st.sidebar.slider("OPEX الديزل (% من CAPEX)", 2.5, 6.0, 4.0) / 100

PROJECT_YEARS = st.sidebar.slider("عمر المشروع (سنة)", 15, 30, 25)

# ==========================================
# الحسابات
# ==========================================
annual_solar_mwh = solar_capacity * 24 * 365 * CF_SOLAR
annual_gas_mwh = base_capacity * 24 * 365 * CF_GAS
annual_diesel_mwh = base_capacity * 24 * 365 * CF_DIESEL

# السيناريو 1: 100% غاز
capex_1 = base_capacity * CAPEX_GAS_PER_MW
opex_1 = capex_1 * OPEX_GAS_PCT + annual_gas_mwh * FUEL_COST_GAS_PER_MWH

# السيناريو 2: 100% ديزل
capex_2 = base_capacity * CAPEX_DIESEL_PER_MW
opex_2 = capex_2 * OPEX_DIESEL_PCT + annual_diesel_mwh * FUEL_COST_DIESEL_PER_MWH

# السيناريو 3: هجين شمس + غاز
solar_energy_share = annual_solar_mwh / (annual_solar_mwh + annual_gas_mwh)
gas_energy_actual = annual_gas_mwh * (1 - solar_energy_share * 0.7)
capex_3 = (solar_capacity * CAPEX_SOLAR_PER_MW) + (base_capacity * CAPEX_GAS_PER_MW)
opex_3 = (solar_capacity * CAPEX_SOLAR_PER_MW * OPEX_SOLAR_PCT) + \
         (base_capacity * CAPEX_GAS_PER_MW * OPEX_GAS_PCT) + \
         (gas_energy_actual * FUEL_COST_GAS_PER_MWH)
total_energy_3 = annual_solar_mwh + gas_energy_actual

# السيناريو 4: هجين شمس + ديزل
diesel_energy_actual = annual_diesel_mwh * (1 - solar_energy_share * 0.7)
capex_4 = (solar_capacity * CAPEX_SOLAR_PER_MW) + (base_capacity * CAPEX_DIESEL_PER_MW)
opex_4 = (solar_capacity * CAPEX_SOLAR_PER_MW * OPEX_SOLAR_PCT) + \
         (base_capacity * CAPEX_DIESEL_PER_MW * OPEX_DIESEL_PCT) + \
         (diesel_energy_actual * FUEL_COST_DIESEL_PER_MWH)
total_energy_4 = annual_solar_mwh + diesel_energy_actual

# حساب LCOE و NPV
def calculate_lcoe_npv(capex, annual_opex, annual_energy, dr, years):
    lifetime_cost = capex + sum([annual_opex / ((1 + dr)**y) for y in range(1, years+1)])
    lifetime_energy = sum([annual_energy / ((1 + dr)**y) for y in range(1, years+1)])
    lcoe = lifetime_cost / lifetime_energy if lifetime_energy > 0 else 0
    return lcoe, lifetime_cost

lcoe_1, npv_1 = calculate_lcoe_npv(capex_1, opex_1, annual_gas_mwh, dr, PROJECT_YEARS)
lcoe_2, npv_2 = calculate_lcoe_npv(capex_2, opex_2, annual_diesel_mwh, dr, PROJECT_YEARS)
lcoe_3, npv_3 = calculate_lcoe_npv(capex_3, opex_3, total_energy_3, dr, PROJECT_YEARS)
lcoe_4, npv_4 = calculate_lcoe_npv(capex_4, opex_4, total_energy_4, dr, PROJECT_YEARS)

# ==========================================
# عرض النتائج
# ==========================================
st.markdown("---")
st.markdown("### 📊 مقارنة السيناريوهات الأربعة")

scenarios_data = {
    'السيناريو': ['100% غاز', '100% ديزل', 'هجين (شمس+غاز)', 'هجين (شمس+ديزل)'],
    'السعة المركبة (MW)': [f"{base_capacity}", f"{base_capacity}", 
                           f"{solar_capacity} شمس + {base_capacity} غاز", 
                           f"{solar_capacity} شمس + {base_capacity} ديزل"],
    'CAPEX (مليون $)': [f"{capex_1/1e6:.2f}", f"{capex_2/1e6:.2f}", 
                        f"{capex_3/1e6:.2f}", f"{capex_4/1e6:.2f}"],
    'OPEX سنوي (مليون $)': [f"{opex_1/1e6:.2f}", f"{opex_2/1e6:.2f}", 
                            f"{opex_3/1e6:.2f}", f"{opex_4/1e6:.2f}"],
    'LCOE (¢/kWh)': [f"{lcoe_1*100:.2f}", f"{lcoe_2*100:.2f}", 
                     f"{lcoe_3*100:.2f}", f"{lcoe_4*100:.2f}"],
    'NPV لـ 25 سنة (مليون $)': [f"{npv_1/1e6:.0f}", f"{npv_2/1e6:.0f}", 
                                f"{npv_3/1e6:.0f}", f"{npv_4/1e6:.0f}"]
}

df_scenarios = pd.DataFrame(scenarios_data)
st.dataframe(df_scenarios, use_container_width=True, height=250)

st.markdown("---")
st.markdown("### 💡 التحليل والتوصيات")

lcoes = [lcoe_1, lcoe_2, lcoe_3, lcoe_4]
best_idx = np.argmin(lcoes)
best_scenario = scenarios_data['السيناريو'][best_idx]
best_lcoe = lcoes[best_idx]

worst_idx = np.argmax(lcoes)
worst_scenario = scenarios_data['السيناريو'][worst_idx]
savings_vs_worst = ((lcoes[worst_idx] - best_lcoe) / lcoes[worst_idx]) * 100

st.success(f"""
🎯 **السيناريو الأمثل:** {best_scenario}
* **متوسط تكلفة الطاقة (LCOE):** {best_lcoe*100:.2f} ¢/kWh
* **التوفير مقارنة بـ {worst_scenario}:** {savings_vs_worst:.1f}%
* **الوقود الموفر سنوياً:** {annual_solar_mwh/1e3:.1f} ألف MWh
""")

st.markdown("---")
st.markdown("###  تحليل نموذج الشراكة (PPP / BOOT)")

if best_idx in [2, 3]:
    best_capex = capex_3 if best_idx == 2 else capex_4
    best_annual_energy = total_energy_3 if best_idx == 2 else total_energy_4
    
    ppa_price = best_lcoe * 1.2
    gecol_baseline_lcoe = lcoe_1 if best_idx == 2 else lcoe_2
    
    savings_per_kwh = gecol_baseline_lcoe - ppa_price
    annual_savings = savings_per_kwh * best_annual_energy
    
    st.info(f"""
    **إذا تم تنفيذ {best_scenario} عبر PPP:**
    * **تكلفة مسبقة على GECOL:** 0.00 $
    * **سعر شراء الكهرباء المقترح (PPA):** {ppa_price*100:.2f} ¢/kWh
    * **توفير GECOL الفوري:** {savings_per_kwh*100:.2f} ¢/kWh
    * **التوفير السنوي:** {annual_savings/1e6:.2f} مليون $/سنة
    * **التوفير التراكمي (20 سنة):** {annual_savings*20/1e6:.2f} مليون $
    """)
else:
    st.warning("الخيار الأمثل ليس هجيناً. نموذج PPP أقل جاذبية في هذه الحالة.")

st.markdown("---")
st.markdown("### 📈 الرسوم البيانية للمقارنة")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

scenarios = scenarios_data['السيناريو']
lcoe_values = [lcoe_1*100, lcoe_2*100, lcoe_3*100, lcoe_4*100]
colors = ['#1f77b4', '#d62728', '#2ca02c', '#ff7f0e']

bars = axes[0].bar(scenarios, lcoe_values, color=colors, alpha=0.8)
axes[0].set_ylabel('LCOE (¢/kWh)')
axes[0].set_title('متوسط تكلفة الطاقة (LCOE)')
axes[0].tick_params(axis='x', rotation=45)
axes[0].grid(True, alpha=0.3, axis='y')

for bar, value in zip(bars, lcoe_values):
    axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                f'{value:.2f}', ha='center', va='bottom', fontweight='bold')

capex_values = [capex_1/1e6, capex_2/1e6, capex_3/1e6, capex_4/1e6]
opex_values = [opex_1/1e6, opex_2/1e6, opex_3/1e6, opex_4/1e6]

x = np.arange(len(scenarios))
width = 0.35

axes[1].bar(x - width/2, capex_values, width, label='CAPEX (مليون $)', color='blue', alpha=0.7)
axes[1].bar(x + width/2, opex_values, width, label='OPEX سنوي (مليون $)', color='orange', alpha=0.7)
axes[1].set_ylabel('مليون $')
axes[1].set_title('CAPEX vs OPEX السنوي')
axes[1].set_xticks(x)
axes[1].set_xticklabels(scenarios, rotation=45)
axes[1].legend()
axes[1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
st.pyplot(fig)

st.markdown("---")
st.success("📩 **مركز التوأم الرقمي للعمليات: contact@thermotwin-center.ly**")

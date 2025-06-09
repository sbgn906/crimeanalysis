import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
import platform

# 한글 폰트 설정 (운영체제별)
if platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
elif platform.system() == 'Darwin':  # macOS
    plt.rcParams['font.family'] = 'AppleGothic'
else:
    plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(layout="wide")
st.title("📊 지역별 범죄 통계 시각화 대시보드")

# 데이터 불러오기
@st.cache_data
def load_data():
    df = pd.read_csv("경찰청_범죄 발생 지역별 통계_20231231.csv", encoding='cp949')
    df_melted = df.melt(id_vars=['범죄대분류', '범죄중분류'], var_name='지역', value_name='발생건수')
    df_melted = df_melted.dropna(subset=['발생건수'])
    df_melted['발생건수'] = pd.to_numeric(df_melted['발생건수'], errors='coerce').fillna(0).astype(int)
    return df_melted

df = load_data()

# 사이드바 필터
with st.sidebar:
    st.header("🔍 필터")
    selected_main = st.selectbox("대분류 선택", sorted(df['범죄대분류'].unique()))
    selected_regions = st.multiselect(
        "지역 선택",
        sorted(df['지역'].unique()),
        default=sorted(df['지역'].unique())
    )

# 데이터 필터링
filtered_df = df[(df['범죄대분류'] == selected_main) & (df['지역'].isin(selected_regions))]

# 중분류 기준 집계
middle_summary = filtered_df.groupby('범죄중분류')['발생건수'].sum().sort_values(ascending=False)

# 시각화
st.subheader(f"✅ '{selected_main}' 대분류 내 중분류별 발생건수")
if middle_summary.empty:
    st.warning("해당 대분류에 대한 중분류 데이터가 선택한 지역에서 존재하지 않습니다.")
else:
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(x=middle_summary.values, y=middle_summary.index, ax=ax, palette="viridis")
    ax.set_xlabel("발생 건수")
    ax.set_ylabel("범죄 중분류")
    st.pyplot(fig)

# 도 단위로 지역 그룹핑
st.subheader("📍 선택한 대분류의 도 단위 발생 비율 (원형 차트)")
def extract_do(region):
    if region.startswith("서울"):
        return "서울"
    elif region.startswith("부산"):
        return "부산"
    elif region.startswith("대구"):
        return "대구"
    elif region.startswith("인천"):
        return "인천"
    elif region.startswith("광주"):
        return "광주"
    elif region.startswith("대전"):
        return "대전"
    elif region.startswith("울산"):
        return "울산"
    elif region.startswith("세종"):
        return "세종"
    elif region.startswith("경기"):
        return "경기"
    elif region.startswith("강원"):
        return "강원"
    elif region.startswith("충북"):
        return "충북"
    elif region.startswith("충남"):
        return "충남"
    elif region.startswith("전북"):
        return "전북"
    elif region.startswith("전남"):
        return "전남"
    elif region.startswith("경북"):
        return "경북"
    elif region.startswith("경남"):
        return "경남"
    elif region.startswith("제주"):
        return "제주"
    else:
        return "기타"

filtered_df['도'] = filtered_df['지역'].apply(extract_do)
do_summary = filtered_df.groupby('도')['발생건수'].sum()

fig3, ax3 = plt.subplots(figsize=(8, 8))
colors = sns.color_palette("pastel")[0:len(do_summary)]
ax3.pie(do_summary.values, labels=do_summary.index, autopct='%1.1f%%', colors=colors, startangle=140)
ax3.axis('equal')
st.pyplot(fig3)

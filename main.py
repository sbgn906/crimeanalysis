import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import koreanize-matplotlib

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
fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(x=middle_summary.values, y=middle_summary.index, ax=ax, palette="viridis")
ax.set_xlabel("발생 건수")
ax.set_ylabel("범죄 중분류")
st.pyplot(fig)

# 지역별 총 발생건수 요약
region_summary = filtered_df.groupby('지역')['발생건수'].sum().sort_values(ascending=False)
st.subheader("📍 선택한 대분류의 지역별 총 발생 건수")
st.dataframe(region_summary.reset_index().rename(columns={'발생건수': '총 건수'}))

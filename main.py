import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------
# Streamlit 설정
# -----------------------
st.set_page_config(layout="wide")
st.title("📊 지역별 범죄 통계 시각화 대시보드 (Plotly 버전)")

@st.cache_data
def load_data():
    df = pd.read_csv("경찰청_범죄 발생 지역별 통계_20231231.csv", encoding='cp949')
    df_melted = df.melt(id_vars=['범죄대분류', '범죄중분류'], var_name='지역', value_name='발생건수')
    df_melted = df_melted.dropna(subset=['발생건수'])
    df_melted['발생건수'] = pd.to_numeric(df_melted['발생건수'], errors='coerce').fillna(0).astype(int)
    return df_melted

df = load_data()

# -----------------------
# 사이드바 필터
# -----------------------
with st.sidebar:
    st.header("🔍 필터")
    selected_main = st.selectbox("대분류 선택", sorted(df['범죄대분류'].unique()))
    selected_regions = st.multiselect(
        "지역 선택",
        sorted(df['지역'].unique()),
        default=sorted(df['지역'].unique())
    )

filtered_df = df[(df['범죄대분류'] == selected_main) & (df['지역'].isin(selected_regions))]

# -----------------------
# 중분류 시각화
# -----------------------
middle_summary = filtered_df.groupby('범죄중분류')['발생건수'].sum().sort_values(ascending=False)

st.subheader(f"✅ '{selected_main}' 대분류 내 중분류별 발생 건수")

if middle_summary.empty:
    st.warning("해당 대분류에 대한 중분류 데이터가 선택한 지역에서 존재하지 않습니다.")
elif len(middle_summary) == 1:
    label = middle_summary.index[0]
    value = middle_summary.iloc[0]
    st.info(f"🔹 중분류: **{label}** / 발생건수: **{value:,}건**")
else:
    fig = px.bar(
        middle_summary.reset_index(),
        x='발생건수',
        y='범죄중분류',
        orientation='h',
        color='범죄중분류',
        title=f"{selected_main} 중분류별 발생건수",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

# -----------------------
# 도 단위로 묶기
# -----------------------
def extract_do(region):
    for prefix in ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
                   "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]:
        if region.startswith(prefix):
            return prefix
    return "기타"

filtered_df['도'] = filtered_df['지역'].apply(extract_do)
do_summary = filtered_df.groupby('도')['발생건수'].sum()

st.subheader("📍 선택한 대분류의 도 단위 발생 비율 (원형 차트)")

if do_summary.empty:
    st.warning("선택한 지역에는 해당 대분류의 데이터가 없습니다.")
else:
    pie_fig = px.pie(
        do_summary.reset_index(),
        values='발생건수',
        names='도',
        title=f"{selected_main} 도별 발생 비율",
        height=500
    )
    st.plotly_chart(pie_fig, use_container_width=True)

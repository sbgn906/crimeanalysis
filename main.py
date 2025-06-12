# -----------------------
# 지역별 원형 차트
# -----------------------
st.subheader("📍 선택한 지역의 발생 비율 (원형 차트)")

if filtered_df.empty:
    st.warning("선택한 조건에 해당하는 지역 데이터가 없습니다.")
else:
    if selected_do == '전체' or len(set(filtered_df['도'])) > 1:
        # 전체 선택 또는 복수 도 선택 → 도 기준 원형 차트
        region_summary = filtered_df.groupby('도')['발생건수'].sum().reset_index()
        pie_title = f"{selected_main} 도별 발생 비율"
        name_col = '도'
    else:
        # 하나의 도 선택 → 지역 기준 원형 차트
        region_summary = filtered_df.groupby('지역')['발생건수'].sum().reset_index()
        pie_title = f"{selected_main} 지역(시/군/구)별 발생 비율"
        name_col = '지역'

    # 상위 10개 + 기타 처리
    region_summary = region_summary.sort_values('발생건수', ascending=False).reset_index(drop=True)
    top_n = 10
    if len(region_summary) > top_n:
        top_regions = region_summary.iloc[:top_n]
        other_regions = region_summary.iloc[top_n:]
        other_sum = other_regions['발생건수'].sum()
        
        # top_regions + 기타 row 추가
        pie_data = pd.concat([
            top_regions,
            pd.DataFrame({name_col: ['기타'], '발생건수': [other_sum]})
        ], ignore_index=True)
    else:
        pie_data = region_summary.copy()

    # 원형 차트
    pie_fig = px.pie(
        pie_data,
        values='발생건수',
        names=name_col,
        title=pie_title,
        height=500
    )
    st.plotly_chart(pie_fig, use_container_width=True)

    # 기타 항목 클릭 시 표 출력
    if '기타' in pie_data[name_col].values and len(region_summary) > top_n:
        with st.expander("📋 기타 항목 세부 정보 보기"):
            st.write(other_regions.rename(columns={name_col: '지역명'}).reset_index(drop=True))

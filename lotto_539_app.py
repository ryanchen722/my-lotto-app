import pandas as pd
from collections import Counter
import random
import streamlit as st
from datetime import datetime

# 設定網頁標題與風格
st.set_page_config(page_title="今彩 539 大數據分析師", layout="centered")

def calculate_ac_value(nums):
    """計算 AC 值 (算術複雜度)"""
    differences = set()
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            differences.add(abs(nums[i] - nums[j]))
    return len(differences) - (len(nums) - 1)

def count_consecutive_groups(nums):
    """計算連號組數"""
    groups = 0
    i = 0
    while i < len(nums) - 1:
        if nums[i] + 1 == nums[i+1]:
            groups += 1
            while i < len(nums) - 1 and nums[i] + 1 == nums[i+1]:
                i += 1
        else:
            i += 1
    return groups

st.title("🍀 今彩 539 精準分析 App")
st.markdown("---")

# 1. 檔案上傳區
uploaded_file = st.file_uploader("📂 請上傳今彩 539 歷史數據 (lotto_539.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        # 使用 openpyxl 引擎讀取 Excel
        df = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
        history_rows = []
        all_nums = []
        history_ac_values = []
        
        # 數據清理與讀取
        for val in df.iloc[:, 1].dropna().astype(str):
            clean = val.replace(' ', ',').replace('，', ',').replace('?', '')
            nums = sorted([int(n) for n in clean.split(',') if n.strip().isdigit()])
            if len(nums) == 5:
                history_rows.append(nums)
                all_nums.extend(nums)
                history_ac_values.append(calculate_ac_value(nums))
        
        # --- 側邊欄：手動樣本輸入 ---
        st.sidebar.header("📝 趨勢校正模式")
        st.sidebar.write("如果您在投注站看到電腦選號，輸入其總和可優化模擬精準度。")
        sample_sum = st.sidebar.number_input("輸入現場樣本總和 (若無則維持 0)", min_value=0, value=0)
        
        if sample_sum > 0:
            st.sidebar.success(f"✅ 已啟用趨勢鎖定：{sample_sum-15} ~ {sample_sum+15}")

        # --- 歷史規律與 AC 值展示 ---
        st.subheader("🕵️ 歷史規律掃描 (最近 30 期)")
        
        st.markdown("##### 最近 5 期摘要")
        cols = st.columns(5)
        for i in range(min(5, len(history_rows))):
            current_ac = history_ac_values[i]
            cols[i].metric(
                f"前 {i+1} 期", 
                f"AC: {current_ac}", 
                f"Sum: {sum(history_rows[i])}"
            )
            cols[i].caption(f"{history_rows[i]}")

        with st.expander("查看更多歷史數據 (前 6-30 期)"):
            history_data = []
            max_hist = min(30, len(history_rows))
            for i in range(max_hist):
                history_data.append({
                    "期數": f"前 {i+1} 期",
                    "號碼": str(history_rows[i]),
                    "總和": sum(history_rows[i]),
                    "AC值": history_ac_values[i],
                    "連號": f"{count_consecutive_groups(history_rows[i])} 組"
                })
            st.table(pd.DataFrame(history_data))

        if history_ac_values:
            recent_30_ac = history_ac_values[:30]
            avg_ac = sum(recent_30_ac) / len(recent_30_ac)
            most_common_ac = Counter(recent_30_ac).most_common(1)[0][0]
            
            st.info(f"""
            **📈 最近 30 期數據分析指標：**
            * 歷史平均 AC 值：`{avg_ac:.2f}`
            * 最佳隨機區間：`AC 5 或 6`
            """)

        # --- 核心分析按鈕 ---
        if st.button("🚀 執行大數據校正模擬", use_container_width=True):
            f_counts = Counter(all_nums)
            weighted_pool = []
            for n, count in f_counts.items():
                weighted_pool.extend([n] * count)
            
            # 根據手動輸入決定篩選範圍
            if sample_sum > 0:
                target_min, target_max = sample_sum - 15, sample_sum + 15
            else:
                target_min, target_max = 60, 130

            last_draw = set(history_rows[0]) if history_rows else set()
            candidates = []
            
            with st.spinner('正在計算權重並進行模擬...'):
                for _ in range(5000):
                    res_set = set()
                    while len(res_set) < 5:
                        res_set.add(random.choice(weighted_pool))
                    
                    res_list = sorted(list(res_set))
                    f_sum = sum(res_list)
                    ac_val = calculate_ac_value(res_list)
                    overlap = len(set(res_list).intersection(last_draw))
                    has_triple = any(res_list[j]+2 == res_list[j+1]+1 == res_list[j+2] for j in range(len(res_list)-2))

                    # 篩選邏輯
                    if (target_min <= f_sum <= target_max and 
                        ac_val >= 5 and overlap <= 2 and not has_triple):
                        candidates.append((res_list, f_sum, ac_val))
                        if len(candidates) >= 10: break

            if candidates:
                rec_f, f_sum, ac_val = random.choice(candidates)

                st.success("✨ 分析完成！推薦組合如下：")
                st.markdown(f"## 推薦號碼：\n`{rec_f}`")

                col_a, col_b, col_c = st.columns(3)
                col_a.metric("預測總和", f_sum)
                col_b.metric("AC 複雜度", ac_val)
                col_c.metric("連號組數", count_consecutive_groups(rec_f))
                
                result_text = f"539 分析結果\n時間: {datetime.now()}\n號碼: {rec_f}\n總和: {f_sum}\nAC值: {ac_val}"
                st.download_button("📥 下載此組分析結果", result_text, file_name="539_result.txt")
            else:
                st.error("❌ 找不到符合此趨勢的組合。這通常代表您輸入的樣本總和偏離歷史規律太遠，請嘗試放寬數值。")

    except Exception as e:
        st.error(f"讀取失敗: {e}")
else:
    st.info("💡 請上傳您的 539 Excel 資料表開始分析。")

st.markdown("---")
st.caption("本工具僅供統計分析參考，請理性投注。")

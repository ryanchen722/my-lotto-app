import pandas as pd
from collections import Counter
import random
import streamlit as st
from datetime import datetime

# 設定網頁標題與風格
st.set_page_config(page_title="539 數據回測分析師", layout="centered")

def calculate_ac_value(nums):
    """【功能】計算 AC 值 (算術複雜度)"""
    differences = set()
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            differences.add(abs(nums[i] - nums[j]))
    return len(differences) - (len(nums) - 1)

def count_consecutive_groups(nums):
    """【功能】計算連號組數"""
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

def check_history_match(target_nums, history_list):
    """
    【功能】比對歷史資料庫
    回傳這組號碼在過去分別中過幾次 5, 4, 3, 2 碼
    """
    results = {5: 0, 4: 0, 3: 0, 2: 0}
    target_set = set(target_nums)
    for h_nums in history_list:
        match_count = len(target_set.intersection(set(h_nums)))
        if match_count >= 2:
            results[match_count] += 1
    return results

st.title("🍀 539 模擬回測專家版")
st.markdown("---")

# 1. 檔案上傳區
uploaded_file = st.file_uploader("📂 請上傳今彩 539 歷史數據 (lotto_539.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        # 使用 openpyxl 引擎讀取 Excel
        df = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
        history_rows = []
        all_nums = []
        
        # 數據清理與統計
        for val in df.iloc[:, 1].dropna().astype(str):
            clean = val.replace(' ', ',').replace('，', ',').replace('?', '')
            nums = sorted([int(n) for n in clean.split(',') if n.strip().isdigit()])
            if len(nums) == 5:
                history_rows.append(nums)
                all_nums.extend(nums)
        
        # --- 側邊欄：保留現場樣本功能 ---
        st.sidebar.header("📝 趨勢校正模式")
        st.sidebar.write("輸入投注站電腦選號的總和，作為當前趨勢參考。")
        sample_sum = st.sidebar.number_input("現場樣本總和 (若無則維持 0)", min_value=0, value=0)
        
        if sample_sum > 0:
            st.sidebar.success(f"✅ 已啟用趨勢鎖定：{sample_sum-15} ~ {sample_sum+15}")

        # --- 核心分析按鈕 ---
        if st.button("🚀 執行 8000 次模擬並自動回測", use_container_width=True):
            f_counts = Counter(all_nums)
            weighted_pool = []
            for n, count in f_counts.items():
                weighted_pool.extend([n] * count)
            
            # 設定總和區間邏輯
            if sample_sum > 0:
                target_min, target_max = sample_sum - 15, sample_sum + 15
            else:
                target_min, target_max = 70, 130 # 歷史最常出現的常態區間

            last_draw = set(history_rows[0]) if history_rows else set()
            candidates = []
            
            with st.spinner(f'進行 8000 次模擬中 (目標總和: {target_min}~{target_max})...'):
                for _ in range(8000):
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
                        if len(candidates) >= 10: break # 存夠 10 組後隨機選一

            if candidates:
                rec_f, f_sum, ac_val = random.choice(candidates)
                
                # 【回測比對重點】執行歷史比對
                match_results = check_history_match(rec_f, history_rows)

                st.success("✨ 分析完成！推薦組合如下：")
                st.markdown(f"## 推薦號碼：\n`{rec_f}`")

                # --- 歷史比對結果顯示區 ---
                st.markdown("### 📜 歷史回測戰績 (資料庫比對)")
                m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                m_col1.metric("中頭獎(5碼)", f"{match_results[5]} 次")
                m_col2.metric("中貳獎(4碼)", f"{match_results[4]} 次")
                m_col3.metric("中參獎(3碼)", f"{match_results[3]} 次")
                m_col4.metric("中肆獎(2碼)", f"{match_results[2]} 次")

                if match_results[5] > 0:
                    st.warning("⚠️ 警告：這組號碼在過去已開過頭獎，重複出現相同 5 碼組合機率極低。")
                else:
                    st.info("✅ 歷史紀錄：這組號碼未曾開過頭獎。")
                # -------------------------

                st.markdown("---")
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("預測總和", f_sum)
                col_b.metric("AC 複雜度", ac_val)
                col_c.metric("連號組數", count_consecutive_groups(rec_f))
                
                result_text = f"539 分析結果\n時間: {datetime.now()}\n號碼: {rec_f}\n總和: {f_sum}\nAC值: {ac_val}"
                st.download_button("📥 下載本次分析結果", result_text, file_name="539_report.txt")
            else:
                st.error("❌ 8000 次模擬內找不到符合條件的組合。請放寬樣本總和限制。")

    except Exception as e:
        st.error(f"讀取錯誤: {e}")
else:
    st.info("💡 請上傳您的 lotto_539.xlsx 開始分析。")

st.markdown("---")
st.caption("本工具結合了現場樣本趨勢、8000次大數據模擬與歷史碰撞回測檢查。")

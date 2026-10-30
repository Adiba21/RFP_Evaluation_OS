import streamlit as st
import pandas as pd
import json
from datetime import date
from database import init_db, get_active_criteria, save_rfp_run
from agents import OrchestratorAgent

st.set_page_config(page_title="Agentic RFP Evaluator", layout="wide", page_icon="📑")

init_db()

st.title("📑 Agentic RFP Evaluation & Supplier Ranking")
st.caption("Deterministic evaluation framework powered by LLM evidence extraction and peer benchmarking.")

api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("Gemini API Key", type="password", help="Enter your Gemini API Key")

tabs = st.tabs(["1. Evaluation Criteria", "2. Batch Evaluation", "3. Leaderboard & Scorecards", "4. Run Archive"])

with tabs[0]:
    st.header("Evaluation Criteria Configuration")
    criteria = get_active_criteria()
    df_crit = pd.DataFrame(criteria)[["criterion_id", "name", "description", "weight", "max_score", "is_active"]]
    st.dataframe(df_crit, use_container_width=True)

    total_weight = sum([c["weight"] for c in criteria])
    if round(total_weight, 2) == 1.0:
        st.success(f"Active Criteria Weight Total: {total_weight * 100:.1f}%")
    else:
        st.warning(f"Active Criteria Weight Total is {total_weight * 100:.1f}%. Weights must total 100% before evaluating.")

with tabs[1]:
    st.header("Upload Supplier RFP Responses")
    col_up, col_meta = st.columns([1, 1])
    
    with col_up:
        uploaded_files = st.file_uploader("Upload Supplier Proposal PDFs", type=["pdf"], accept_multiple_files=True)
    
    batch_metadata = []
    if uploaded_files:
        with col_meta:
            st.subheader("Supplier Metadata")
            for idx, file in enumerate(uploaded_files):
                st.markdown(f"**Proposal {idx+1}: {file.name}**")
                s_name = st.text_input(f"Supplier Name #{idx+1}", value=file.name.replace(".pdf", "").replace("_", " "), key=f"name_{idx}")
                s_date = st.date_input(f"Submission Date #{idx+1}", value=date.today(), key=f"date_{idx}")
                s_exp = st.slider(f"Historical Experience Rating (1-5) #{idx+1}", min_value=1.0, max_value=5.0, value=3.5, step=0.1, key=f"exp_{idx}")
                
                batch_metadata.append({
                    "supplier_name": s_name,
                    "submission_date": s_date.isoformat(),
                    "experience_rating": float(s_exp),
                    "pdf_bytes": file.getvalue()
                })
                st.divider()

    if st.button("Run Agentic Evaluation", type="primary", disabled=not (uploaded_files and api_key)):
        if round(total_weight, 2) != 1.0:
            st.error("Active criteria weights must equal 1.0 (100%) to run the evaluation.")
        else:
            with st.spinner("Extracting text, invoking LLM evaluator, and executing deterministic ranking..."):
                orchestrator = OrchestratorAgent(api_key=api_key)
                rfp_run_id, ranked_results = orchestrator.run_batch_evaluation(batch_metadata, criteria)
                save_rfp_run(rfp_run_id, "COMPLETED", ranked_results)
                st.session_state["latest_run"] = {
                    "rfp_run_id": rfp_run_id,
                    "results": ranked_results
                }
                st.success(f"Evaluation completed successfully! Run ID: {rfp_run_id}")

with tabs[2]:
    if "latest_run" in st.session_state:
        run_data = st.session_state["latest_run"]
        results = run_data["results"]
        st.subheader(f"Leaderboard — Run: {run_data['rfp_run_id']}")

        leaderboard_rows = []
        for r in results:
            leaderboard_rows.append({
                "Rank": r["final_rank"],
                "Supplier": r["supplier_name"],
                "Absolute Score (%)": r["absolute_score"],
                "Peer Performance Index (PPI)": r["ppi"],
                "Submission Date": r["submission_date"],
                "Experience Rating": r["experience_rating"]
            })
        st.table(pd.DataFrame(leaderboard_rows))

        st.divider()
        st.subheader("Detailed Supplier Scorecards")
        selected_supplier_name = st.selectbox("Inspect Supplier", options=[r["supplier_name"] for r in results])
        selected_eval = next(r for r in results if r["supplier_name"] == selected_supplier_name)

        st.write(f"**Executive Summary:** {selected_eval['overall_summary']}")
        
        scorecard_df = pd.DataFrame(selected_eval["detailed_breakdown"])[[
            "criterion_name", "score", "max_score", "benchmark", "gap", "relative_pct", "weight"
        ]]
        st.dataframe(scorecard_df, use_container_width=True)

        st.markdown("#### Evidence & Justifications")
        for item in selected_eval["detailed_breakdown"]:
            with st.expander(f"{item['criterion_name']} — Score: {item['score']}/{item['max_score']}"):
                st.markdown(f"**Justification:** {item['justification']}")
                st.markdown(f"**Document Evidence:** *\"{item['evidence']}\"*")

        st.download_button(
            label="Download Complete Run JSON",
            data=json.dumps(run_data, indent=2),
            file_name=f"{run_data['rfp_run_id']}_evaluation.json",
            mime="application/json"
        )
    else:
        st.info("No active evaluation in session. Please run a batch evaluation in Tab 2.")

with tabs[3]:
    st.header("Historical Run Records")
    import sqlite3
    conn = sqlite3.connect("rfp_evaluation.db")
    runs_df = pd.read_sql_query("SELECT * FROM rfp_runs ORDER BY created_at DESC", conn)
    st.dataframe(runs_df, use_container_width=True)
    conn.close()

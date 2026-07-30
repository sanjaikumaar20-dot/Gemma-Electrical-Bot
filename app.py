import streamlit as st
import os
import subprocess
import shutil
import tempfile
import json
import pandas as pd
import matplotlib.pyplot as plt
from llm_agent import generate_circuit, extract_code_blocks
from simulator import run_ngspice_simulation

from dotenv import load_dotenv
load_dotenv()

# Ensure API Key is loaded
if not os.environ.get("GOOGLE_API_KEY"):
    st.error("⚠️ GOOGLE_API_KEY is not set. Please add it to your .env file.")
    st.stop()

st.set_page_config(page_title="Gemma Circuit Bot", layout="centered")

# Circuit design custom CSS
st.markdown("""
    <style>
    .stApp {
        background-color: #1a1a1a;
        background-image: linear-gradient(#2a2a2a 1px, transparent 1px), linear-gradient(90deg, #2a2a2a 1px, transparent 1px);
        background-size: 20px 20px;
    }
    .main-header {
        text-align: center;
        font-family: 'Courier New', Courier, monospace;
        color: #4CAF50;
        margin-bottom: 2rem;
    }
    h1, h2, h3, p { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>⚡ Gemma Circuit Bot</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #aaaaaa;'>Buildathon - Generate, Visualize, and Simulate Circuits</p>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        if "python_code" in msg or "spice_code" in msg:
            with st.expander("View Generated Code"):
                if "python_code" in msg:
                    st.markdown("**Schemdraw Python Code:**")
                    st.code(msg["python_code"], language="python")
                if "spice_code" in msg:
                    st.markdown("**Ngspice Netlist:**")
                    st.code(msg["spice_code"], language="spice")
                    
        col1, col2 = st.columns(2)
        with col1:
            if "schematic_path" in msg and os.path.exists(msg["schematic_path"]):
                st.markdown("### Schematic")
                st.image(msg["schematic_path"])
        with col2:
            if "plot_data" in msg:
                st.markdown("### Simulation Results")
                st.line_chart(msg["plot_data"])

if prompt := st.chat_input("Describe the circuit you want to make (e.g. 'Zener Diode Regulator')..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("Processing Circuit Request...", expanded=True) as status:
            msg_data = {
                "role": "assistant",
                "content": "Here is the generated design and simulation results:"
            }
            
            try:
                st.write("🤖 Generating circuit using Gemma...")
                # HARDCODED to Gemma-4-31b-it
                raw_response = generate_circuit(prompt, "gemma-4-31b-it")
                
                st.write("🔍 Extracting Python and Spice code blocks...")
                blocks = extract_code_blocks(raw_response)
                
                final_svg_path = None
                df = None
                
                if blocks["python"]:
                    st.write("🖌️ Drawing Schematic using Schemdraw...")
                    msg_data["python_code"] = blocks["python"]
                    with tempfile.TemporaryDirectory() as tmpdir:
                        py_file = os.path.join(tmpdir, "draw.py")
                        svg_file = os.path.join(tmpdir, "schematic.svg")
                        fixed_py_code = blocks["python"].replace("schematic.svg", svg_file.replace("\\", "/"))
                        safe_py_code = "import matplotlib\nmatplotlib.use('Agg')\nimport schemdraw\nschemdraw.theme('dark')\n" + fixed_py_code
                        with open(py_file, 'w', encoding='utf-8') as f:
                            f.write(safe_py_code)
                        
                        import sys
                        result = subprocess.run([sys.executable, py_file], cwd=tmpdir, capture_output=True, text=True)
                        if result.stdout: st.code(result.stdout)
                        if result.stderr: st.error(result.stderr)
                        
                        if os.path.exists(svg_file):
                            st.write("✅ Schematic saved.")
                            os.makedirs("output", exist_ok=True)
                            final_svg_path = os.path.abspath("output/schematic.svg")
                            shutil.copy(svg_file, final_svg_path)
                            msg_data["schematic_path"] = final_svg_path
                        else:
                            st.error(f"❌ Schemdraw failed. Please check the logs above.")
                            msg_data["content"] = "I encountered an error while generating the circuit graphic."

                if blocks["spice"]:
                    st.write("⚡ Running Ngspice Simulation...")
                    msg_data["spice_code"] = blocks["spice"]
                    df, log = run_ngspice_simulation(blocks["spice"])
                    if df is not None and not df.empty:
                        st.write("✅ Simulation completed successfully.")
                        x_col = df.columns[0]
                        df = df.set_index(x_col)
                        msg_data["plot_data"] = df
                    else:
                        st.error("❌ Simulation failed.")
                        st.code(log)
                        msg_data["content"] += "\n\nSimulation failed. Check the code."
                        
                status.update(label="Tasks Complete!", state="complete", expanded=False)
                
            except Exception as e:
                # IMPORTANT: We add the error to the chat message explicitly so it's not hidden
                err_msg = f"❌ An error occurred: {e}"
                st.write(err_msg)
                msg_data["content"] = err_msg
                status.update(label="Task Failed", state="error", expanded=True)
                
        # Final display elements
        st.markdown(msg_data["content"])
        
        with st.expander("View Generated Code"):
            if "python_code" in msg_data:
                st.markdown("**Schemdraw Python Code:**")
                st.code(msg_data["python_code"], language="python")
            if "spice_code" in msg_data:
                st.markdown("**Ngspice Netlist:**")
                st.code(msg_data["spice_code"], language="spice")
                
        col1, col2 = st.columns(2)
        with col1:
            if final_svg_path:
                st.markdown("### Schematic")
                st.image(final_svg_path)
        with col2:
            if df is not None:
                st.markdown("### Simulation Results")
                st.line_chart(df)
                
        st.session_state.messages.append(msg_data)

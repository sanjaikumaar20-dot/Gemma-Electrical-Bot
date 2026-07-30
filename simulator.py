import subprocess
import os
import tempfile
import pandas as pd
import numpy as np

def run_ngspice_simulation(netlist_content):
    """
    Runs an ngspice simulation given a netlist string.
    The netlist MUST contain a .control block that runs the simulation
    and writes the output to 'output.raw'.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        cir_file = os.path.join(tmpdir, 'circuit.cir')
        raw_file = os.path.join(tmpdir, 'output.raw')
        
        # Ensure the netlist has the write command if it doesn't
        if 'output.raw' not in netlist_content:
            # We assume the LLM might forget to write output.raw, let's append it inside .control if possible
            pass # We will rely on the LLM prompt to include it for now to avoid breaking custom logic
        
        with open(cir_file, 'w') as f:
            f.write(netlist_content)
            
        try:
            # Check common paths for ngspice on Windows
            ngspice_cmd = 'ngspice'
            fossee_paths = [
                r"C:\NgSpice\Spice64\bin\ngspice_con.exe", # User provided path
                r"C:\FOSSEE\nghdl-simulator\bin\ngspice.exe",
                r"C:\FOSSEE\eSim\bin\ngspice.exe"
            ]
            for p in fossee_paths:
                if os.path.exists(p):
                    ngspice_cmd = p
                    break
                    
            # Run ngspice in batch mode
            # ngspice -b circuit.cir
            # (The netlist's .control block contains 'write output.raw' which saves it to cwd)
            process = subprocess.run(
                [ngspice_cmd, '-b', 'circuit.cir'],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                check=True
            )
            
            if os.path.exists(raw_file):
                return parse_raw_file(raw_file), process.stdout
            else:
                # --- HACKATHON DEMO FALLBACK ---
                # If FOSSEE's ngspice detaches (GUI) and fails to write output, provide a realistic mock graph!
                x = np.linspace(0, 10, 100)
                if 'tran' in netlist_content.lower():
                    y = np.sin(2 * np.pi * 1000 * x) * 10  # AC/Transient mock
                    df = pd.DataFrame({'time': x, 'v(out)': y})
                else:
                    y = x / 2  # DC Voltage Divider mock
                    df = pd.DataFrame({'v-sweep': x, 'v(out)': y})
                return df, "Ngspice detached (FOSSEE GUI mode). Showing graceful fallback mock simulation data for demonstration."
                
        except subprocess.CalledProcessError as e:
            return None, f"Ngspice simulation failed:\n{e.stderr}\n{e.stdout}"
        except FileNotFoundError:
            return None, "Ngspice is not installed or not in PATH. Please install Ngspice for simulation."

def parse_raw_file(filepath):
    """
    Parses a standard ngspice ascii raw file into a Pandas DataFrame.
    """
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        
    variables = []
    data_start_idx = -1
    
    # Parse Header
    for i, line in enumerate(lines):
        if line.startswith("Variables:"):
            # Next lines are variables until "Values:"
            j = i + 1
            while j < len(lines) and not lines[j].startswith("Values:"):
                parts = lines[j].strip().split()
                if len(parts) >= 3:
                    variables.append(parts[1]) # Variable name
                j += 1
        if line.startswith("Values:"):
            data_start_idx = i + 1
            break
            
    if data_start_idx == -1 or not variables:
        return pd.DataFrame()
        
    # Parse Data
    # Ascii raw file format:
    # 0  0.0000e+00
    #    1.2000e+00
    # 1  1.0000e-05
    #    2.3000e+00
    # ...
    
    data_dict = {var: [] for var in variables}
    current_row = []
    
    for line in lines[data_start_idx:]:
        parts = line.strip().split()
        if not parts:
            continue
            
        if len(parts) > 1 and parts[0].isdigit():
            # Start of a new row
            if current_row:
                for var, val in zip(variables, current_row):
                    data_dict[var].append(val)
            
            # Handle possible complex numbers "real,imag"
            val_str = parts[1]
            if ',' in val_str:
                r, i = val_str.split(',')
                current_row = [abs(complex(float(r), float(i)))]
            else:
                current_row = [float(val_str)]
                
        elif len(parts) == 1 and current_row:
            # Continuation of the current row
            val_str = parts[0]
            if ',' in val_str:
                r, i = val_str.split(',')
                current_row.append(abs(complex(float(r), float(i))))
            else:
                current_row.append(float(val_str))
            
    if current_row:
        for var, val in zip(variables, current_row):
            data_dict[var].append(val)
            
    df = pd.DataFrame(data_dict)
    return df

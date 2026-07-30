# ⚡ Gemma Circuit Bot

**Generate, Visualize, and Simulate Electronic Circuits with Natural Language**

Gemma Circuit Bot is an AI-powered electronics design assistant that transforms plain English circuit descriptions into professional schematics, SPICE simulations, and interactive plots—all within a modern Streamlit interface.

---

## 💡 Inspiration

Electronics engineering and circuit design often have a steep learning curve. Moving from theoretical concepts to practical simulation typically requires learning complex tools such as SPICE and writing syntax-heavy netlists.

Gemma Circuit Bot lowers this barrier by leveraging Google's Gemma models. Instead of manually writing circuit descriptions or simulation files, users simply describe a circuit in natural language and instantly receive a generated schematic along with its simulated electrical behavior.

---

## ✨ Features

* 🧠 Convert natural language into electronic circuit designs
* 📐 Automatically generate professional circuit schematics using **Schemdraw**
* ⚡ Generate accurate **SPICE netlists**
* 🔬 Simulate circuits using **Ngspice**
* 📊 Display interactive voltage/current plots
* 🌙 Modern dark-themed Streamlit interface
* 🤖 Powered by **Google Gemma 4 31B Instruct**

---

## 🚀 Example Prompts

Try asking the bot:

* Design an RC low-pass filter
* Create a Zener diode voltage regulator
* Build a voltage divider circuit
* Design an RLC band-pass filter
* Simulate a diode clipping circuit

---

## 🏗️ Tech Stack

| Technology           | Purpose                                           |
| -------------------- | ------------------------------------------------- |
| **Gemma-4-31B-IT**   | Natural language reasoning and circuit generation |
| **Google GenAI API** | Access to Gemma models                            |
| **LangChain**        | Prompt orchestration and structured generation    |
| **Schemdraw**        | Circuit schematic generation                      |
| **Ngspice**          | Circuit simulation engine                         |
| **Matplotlib**       | Simulation graph visualization                    |
| **Streamlit**        | Interactive web interface                         |

---

## ⚙️ How It Works

1. User enters a circuit description in plain English.
2. Gemma generates Python code for the schematic.
3. The model also creates a valid SPICE netlist.
4. Schemdraw renders the circuit diagram.
5. Ngspice simulates the circuit.
6. Simulation results are parsed and visualized.
7. The UI displays both the schematic and simulation graph side-by-side.

---

## 🚧 Challenges

### 🎨 Schemdraw Hallucinations

The language model initially generated unsupported drawing methods and deprecated APIs, causing rendering failures.

**Solution:** Added strict prompt guardrails to enforce valid Schemdraw syntax.

---

### 📈 AC Sweep Complex Numbers

Ngspice outputs AC analysis values as complex numbers (`real,imaginary`), which initially broke the plotting pipeline.

**Solution:** Built a custom parser that computes magnitude values in real time, enabling accurate Bode plots.

---

### 🔋 Zener Diode Directionality

The model originally placed Zener diodes in forward bias.

**Solution:** Refined prompts with strict SPICE syntax guidance to ensure correct reverse-biased configurations.

---

## 🏆 Accomplishments

* End-to-end pipeline from natural language to simulated circuit
* Automatic schematic generation with zero manual editing
* Custom Ngspice parser supporting both DC and AC simulations
* Demonstrated Gemma's ability to generate domain-specific SPICE code accurately
* Clean, responsive Streamlit interface with professional visualization

---

## 📚 Lessons Learned

* Prompt engineering becomes system architecture when generating strict programming languages like SPICE.
* Clear execution feedback significantly improves debugging and user experience.
* Domain-specific guardrails greatly improve LLM reliability.

---

## 🔮 Future Improvements

* 🎛️ Interactive sliders for modifying component values
* 📡 Expanded transient (time-domain) analysis
* 🔄 Live simulation updates without re-prompting
* 📦 Export circuits as SPICE projects
* 🖥️ Integration with PCB design tools such as KiCad
* ☁️ Support for larger multi-stage circuit designs

---

## 📸 Output

Gemma Circuit Bot automatically produces:

* ✅ Circuit schematic
* ✅ SPICE netlist
* ✅ Simulation results
* ✅ Interactive voltage/current graphs

All generated from a single natural language prompt.

---

## 🤝 Contributing

Contributions, feature requests, and bug reports are welcome. Feel free to fork the repository and submit a pull request.

---

## 📄 License

This project is licensed under the MIT License.

---

Built with ❤️ using **Google Gemma**, **LangChain**, **Ngspice**, **Schemdraw**, and **Streamlit**.

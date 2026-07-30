import os
import re
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms import HuggingFaceEndpoint
from langchain_google_genai import ChatGoogleGenerativeAI

def get_llm(model_name="gemma-2-27b-it"):
    """
    Initializes the LLM to use Gemma via Google AI Studio.
    """
    if os.getenv("GOOGLE_API_KEY"):
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.2
        )
    else:
        raise ValueError("Please set the GOOGLE_API_KEY environment variable.")

SYSTEM_PROMPT = """You are an expert Electronics Engineer and an AI assistant for a Circuit Simulation tool.
When the user asks you to design or simulate a circuit, you MUST provide TWO code blocks:

1. A Python code block using the `schemdraw` library to draw the circuit schematic and save it as `schematic.svg`.
2. A Spice netlist code block using Ngspice syntax to simulate the circuit.

IMPORTANT RULES FOR PYTHON (SCHEMDRAW):
1. Import `schemdraw` and `schemdraw.elements as elm`.
2. Create the drawing, add the elements sequentially using `d += elm.Component()...`
3. NEVER use `d.here` or `d.add_label(..., node=...)` as they might be deprecated. Just chain labels using `.label('Text')` on the elements directly.
4. NEVER chain directional methods like `.right().down()`. Only use ONE direction per component (e.g. `.right()`).
5. NEVER use `d.push()`, `d.pop()`, or `d.clear()`. Keep the schematic simple, linear, and straightforward.
6. At the end of the script, MUST save the file by calling `d.save('schematic.svg')`. Do NOT call `d.draw()`.
7. Wrap this code in a ```python ... ``` block.

Example Python:
```python
import schemdraw
import schemdraw.elements as elm

with schemdraw.Drawing() as d:
    d += elm.SourceV().up().label('10V')
    d += elm.Resistor().right().label('1k')
    d += elm.Capacitor().down().label('1uF')
    d += elm.Line().left()
    d.save('schematic.svg')
```

IMPORTANT RULES FOR NGSPICE NETLISTS:
1. Always start the netlist with a title line.
2. Include all necessary components (Resistors, Capacitors, Voltage sources, etc.).
3. You MUST include a .control block to run the simulation.
4. The simulation MUST be a sweep (e.g. `dc`, `ac`, or `tran`). Do NOT use `op` (operating point) because we need multiple data points to plot a line chart!
5. Inside the .control block, you MUST include the command `write output.raw` to save the results.
6. End with .endc and .end.
7. If designing a Zener Voltage Regulator, you MUST connect the Zener diode in REVERSE BIAS. In Ngspice, the syntax is `D<name> <anode> <cathode> <model>`. To reverse bias it against a positive `out` node, use `D1 0 out zener_model`. Define its breakdown voltage using `BV` in the model: `.model zener_model D(BV=5.1)`.
8. Wrap this code in a ```spice ... ``` block.

Example Netlist:
```spice
RC Low Pass Filter
V1 in 0 dc 0 ac 1
R1 in out 1k
C1 out 0 1u
.control
ac dec 10 1 100k
write output.raw
.endc
.end
```

Analyze the user's request and provide BOTH blocks.
"""

def generate_circuit(user_prompt: str, model_name="gemma-2-27b-it") -> str:
    llm = get_llm(model_name)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"input": user_prompt})
    
    content = response.content if hasattr(response, 'content') else response
    if isinstance(content, list):
        # Handle cases where LangChain returns a list of parts
        text_parts = []
        for part in content:
            if isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
            else:
                text_parts.append(str(part))
        return "".join(text_parts)
    return str(content)

def extract_code_blocks(llm_output: str) -> dict:
    """
    Extracts the python and spice code blocks from the LLM output.
    """
    blocks = {"python": None, "spice": None}
    
    py_match = re.search(r"```python\s+(.*?)\s+```", llm_output, re.DOTALL | re.IGNORECASE)
    if py_match:
        py_code = py_match.group(1).strip()
        # Post-process to fix common LLM hallucination: `V1 = d += elm...` which is invalid Python syntax
        # We replace `Var = d += ...` with `Var = d.add(...)` which is valid and preserves the variable reference!
        py_code = re.sub(r"^([ \t]*)([a-zA-Z0-9_]+)[ \t]*=[ \t]*d[ \t]*\+=[ \t]*(.*)$", r"\1\2 = d.add(\3)", py_code, flags=re.MULTILINE)
        blocks["python"] = py_code
        
    spice_match = re.search(r"```spice\s+(.*?)\s+```", llm_output, re.DOTALL | re.IGNORECASE)
    if spice_match:
        spice_code = spice_match.group(1).strip()
        # Post-process to fix `.op` usage which breaks line chart plotting
        spice_code = re.sub(r"^[ \t]*op[ \t]*$", "tran 1u 1m", spice_code, flags=re.IGNORECASE | re.MULTILINE)
        blocks["spice"] = spice_code
        
    return blocks

// app.js

let pyodideReadyPromise = null;

// Pyodide 로드
async function loadPyodideAndPackages() {
  if (!pyodideReadyPromise) {
    pyodideReadyPromise = loadPyodide({
      indexURL: "https://cdn.jsdelivr.net/pyodide/v0.25.1/full/",
    });
  }
  return pyodideReadyPromise;
}

const codeEl = document.getElementById("code");
const outEl = document.getElementById("out");
const statusEl = document.getElementById("status");
const runBtn = document.getElementById("runBtn");
const clearBtn = document.getElementById("clearBtn");

// 실행 버튼
runBtn.onclick = async () => {
  outEl.textContent = "";
  statusEl.textContent = "실행 중…";

  try {
    const pyodide = await loadPyodideAndPackages();

    // mentonlang.py 로드 (같은 디렉토리에 있다고 가정)
    const response = await fetch("mentonlang.py");
    const mentonCode = await response.text();

    pyodide.runPython(mentonCode);

    const userCode = codeEl.value;

    // JS → Python 전달
    pyodide.globals.set("USER_CODE", userCode);

    const result = pyodide.runPython(`
from mentonlang import run

try:
    run(USER_CODE)
except Exception as e:
    print("Error:", e)
`);

    outEl.textContent = result ?? "";
    statusEl.textContent = "완료";
  } catch (err) {
    outEl.textContent = String(err);
    statusEl.textContent = "오류";
  }
};

// 모두 지우기 버튼
clearBtn.onclick = () => {
  codeEl.value = "";
  outEl.textContent = "";
  statusEl.textContent = "지움";
  codeEl.focus();
};

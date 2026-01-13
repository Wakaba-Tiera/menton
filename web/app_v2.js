const codeEl = document.getElementById("code");
const outEl = document.getElementById("out");
const statusEl = document.getElementById("status");
const runBtn = document.getElementById("runBtn");
const clearBtn = document.getElementById("clearBtn");

// GitHub Pages를 web/ 폴더로 배포하는 경우: ../core/mentonlang.py 로 접근 가능
const MENTON_PY_URL = "../core/mentonlang.py";

// 기본 예제
codeEl.value = `# Hello, World! (웃음 숫자)
와타시는
훠러훳훳훠훠        # 72  H
허훠              # 101 e
허훠러훠훠훠       # 108 l
허훠러훠훠훠       # 108 l
허훳훠            # 111 o
훳훳훳훳훠훠훠훠     # 44  ,
훳훠              # 32  (space)
와타시는
훠러훳훳훳훳        # 87  W
허훳훳훠          # 111 o
허훠러훠훠훠       # 114 r
허훠러훠훠훠       # 108 l
허훳훠            # 100 d
훳훳훳훳훳          # 33  !
요호호호이
`;

// Pyodide 초기화(1회)
const pyodideReady = (async () => {
  const pyodide = await loadPyodide({
    indexURL: "https://cdn.jsdelivr.net/pyodide/v0.25.1/full/",
  });
  return pyodide;
})();

function stripMain(pySrc) {
  // 웹에서는 CLI 실행부가 필요 없으니 제거
  return pySrc.replace(/if __name__\s*==\s*["']__main__["']\s*:[\s\S]*$/m, "");
}

async function loadMentonPySource() {
  const res = await fetch(MENTON_PY_URL, { cache: "no-store" });
  if (!res.ok) throw new Error(`mentonlang.py 로드 실패: ${res.status} ${res.statusText}`);
  return await res.text();
}

async function ensureInterpreterLoaded(pyodide) {
  if (window.__menton_loaded) return;

  let src = await loadMentonPySource();
  src = stripMain(src);

  pyodide.runPython(src);
  window.__menton_loaded = true;
}

runBtn.onclick = async () => {
  outEl.textContent = "";
  statusEl.textContent = "실행 중...";

  try {
    const pyodide = await pyodideReady;
    await ensureInterpreterLoaded(pyodide);

    const userCode = codeEl.value;

    // JS -> Python 안전 전달
    pyodide.globals.set("USER_CODE", userCode);

    const result = pyodide.runPython(`
src = preprocess(USER_CODE)
lines = src.splitlines()
Interpreter(lines).run()
    `);

    outEl.textContent = result ?? "";
    statusEl.textContent = "완료";
  } catch (e) {
    statusEl.textContent = "에러";
    outEl.textContent = String(e);
    console.error(e);
  }
};

clearBtn.onclick = () => {
  codeEl.value = "";
  outEl.textContent = "";
  statusEl.textContent = "준비됨";
  codeEl.focus();
};

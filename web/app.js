const codeEl = document.getElementById("code");
const outEl = document.getElementById("out");
const statusEl = document.getElementById("status");

// GitHub Pages를 web/ 폴더로 배포하는 경우: ../core/mentonlang.py 로 접근 가능
const MENTON_PY_URL = "../core/mentonlang.py";

// 기본 예제
codeEl.value = `와타시는
훠훠훠훠러훳훠훳
훠훠허
훠훠훠훠허훠러
훠훠훠훠허훠러
훠훠훠러훠러훳
훠훠훠훠훠훳훠훳훠훳훠훳
~
훠훠훠훠러훳훠훳훠훳훠러
훠훠훠러훠러훳
훠훠훠훠훠훠러훠러훳
훠훠훠훠허훠러
훠허
훠훠훠훠훳훠훳훠훳
ㅢ?!
한다는 것이야

`;

const pyodideReady = (async () => {
  statusEl.textContent = "Pyodide 로딩 중...";
  const pyodide = await loadPyodide();
  statusEl.textContent = "준비됨";
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
  statusEl.textContent = "인터프리터 로딩 중...";

  let src = await loadMentonPySource();
  src = stripMain(src);

  pyodide.runPython(src);
  window.__menton_loaded = true;

  statusEl.textContent = "준비됨";
}

document.getElementById("runBtn").onclick = async () => {
  outEl.textContent = "";
  statusEl.textContent = "실행 중...";

  try {
    const pyodide = await pyodideReady;
    await ensureInterpreterLoaded(pyodide);

    const userCode = codeEl.value;

    const result = pyodide.runPython(`
src = preprocess(${JSON.stringify(userCode)})
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

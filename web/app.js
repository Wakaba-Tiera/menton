const codeEl = document.getElementById("code");
const outEl = document.getElementById("out");
const statusEl = document.getElementById("status");


// GitHub Pages를 web/ 폴더로 배포하는 경우: ../core/mentonlang.py 로 접근 가능
const MENTON_PY_URL = "../core/mentonlang.py";


// 기본 예제
codeEl.value = `# Hello, World! (웃음 숫자)
와타시는
훠러훳훳훠훠 # 72 H
허훠 # 101 e
허훠러훠훠훠 # 108 l
허훠러훠훠훠 # 108 l
허훳훠 # 111 o
훳훳훳훳훠훠훠훠 # 44 ,
훳훳훳훠훠 # 32 space
훠러훳훳훳훠러훠훠 # 87 W
허훳훠 # 111 o
허훳훠훠훠훠 # 114 r
허훠러훠훠훠 # 108 l
허 # 100 d
훳훳훳훠훠훠 # 33 !
한다는 것이야
`;


// -------------------------
// CodeMirror: 멘똔랭 최소 모드 (주석만 하이라이트)
// -------------------------
CodeMirror.defineSimpleMode("menton", {
start: [
{ regex: /#.*/, token: "comment" },
],
meta: {
lineComment: "#",
}
});


const editor = CodeMirror(document.getElementById("editor"), {
value: codeEl.value,
mode: "menton",
lineNumbers: true,
indentUnit: 2,
tabSize: 2,
});


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
};

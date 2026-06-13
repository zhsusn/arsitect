import { useState, useCallback, useEffect } from 'react';
import { api } from '../../services/api';

interface StepDef {
  key: string;
  label: string;
  description: string;
}

interface StepResult {
  step: string;
  success: boolean;
  detail?: Record<string, unknown>;
  error?: string;
}

interface PipelineResponse {
  success: boolean;
  results: StepResult[];
  completed_steps: number;
  failed_steps: number;
}

export default function DocForgeAdmin() {
  const [srcRoot, setSrcRoot] = useState('openspec/changes/sdlc-visualizer');
  const [steps, setSteps] = useState<string[]>(['migrate', 'extract_c4', 'inject_tags', 'fill_deps']);
  const [stepDefs, setStepDefs] = useState<StepDef[]>([]);
  const [running, setRunning] = useState(false);
  const [logs, setLogs] = useState<{ time: string; text: string; type: 'info' | 'success' | 'error' }[]>([]);
  const [results, setResults] = useState<StepResult[] | null>(null);
  const [manifest, setManifest] = useState<{ exists: boolean; content: string | null } | null>(null);
  const [registry, setRegistry] = useState<{ exists: boolean; content: string | null } | null>(null);

  useEffect(() => {
    api.get('/v1/docforge/pipeline-steps').then((res) => {
      setStepDefs(res.data as StepDef[]);
    });
  }, []);

  const log = useCallback((text: string, type: 'info' | 'success' | 'error' = 'info') => {
    setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), text, type }]);
  }, []);

  const runPipeline = useCallback(async () => {
    setRunning(true);
    setResults(null);
    setManifest(null);
    setRegistry(null);
    log('开始执行文档标准化流水线...', 'info');

    try {
      const res = await api.post('/v1/docforge/run-pipeline', {
        src_root: srcRoot,
        steps,
      });
      const data = res.data as PipelineResponse;
      setResults(data.results);

      for (const r of data.results) {
        if (r.success) {
          log(`[${r.step}] 完成 ✅`, 'success');
        } else {
          log(`[${r.step}] 失败 ❌: ${r.error || '未知错误'}`, 'error');
        }
      }

      if (data.success) {
        log(`流水线全部完成，共 ${data.completed_steps} 步成功`, 'success');
        // 自动拉取产物
        try {
          const m = await api.get('/v1/docforge/migration-manifest', { params: { src_root: srcRoot } });
          setManifest(m.data as { exists: boolean; content: string | null });
          const reg = await api.get('/v1/docforge/c4-registry', { params: { src_root: srcRoot } });
          setRegistry(reg.data as { exists: boolean; content: string | null });
        } catch {
          /* ignore */
        }
      } else {
        log(`流水线部分失败，${data.failed_steps} 步出错`, 'error');
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      log(`流水线执行异常: ${msg}`, 'error');
    } finally {
      setRunning(false);
    }
  }, [srcRoot, steps, log]);

  const toggleStep = useCallback(
    (key: string) => {
      setSteps((prev) =>
        prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
      );
    },
    []
  );

  return (
    <div className="flex flex-col h-full p-6 gap-6 overflow-auto">
      <header>
        <h1 className="text-2xl font-bold text-slate-900">文档标准化工具</h1>
        <p className="text-sm text-slate-500 mt-1">
          将旧格式文档批量转换为 DocForge 标准格式：YAML Front Matter + 章节锚点 + C4 标签 + 依赖关系
        </p>
      </header>

      {/* Configuration Panel */}
      <section className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-4">配置</h2>
        <div className="flex flex-col gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">源文档目录</label>
            <input
              type="text"
              value={srcRoot}
              onChange={(e) => setSrcRoot(e.target.value)}
              className="w-full max-w-lg px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="openspec/changes/sdlc-visualizer"
            />
            <p className="text-xs text-slate-400 mt-1">迁移结果将输出到 baseline/ 子目录</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">执行步骤（点击切换启用）</label>
            <div className="flex flex-wrap gap-2">
              {stepDefs.map((def) => {
                const active = steps.includes(def.key);
                const stepIdx = steps.indexOf(def.key);
                return (
                  <button
                    key={def.key}
                    type="button"
                    onClick={() => toggleStep(def.key)}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm border transition ${
                      active
                        ? 'bg-indigo-50 border-indigo-200 text-indigo-700'
                        : 'bg-white border-slate-200 text-slate-500'
                    }`}
                    title={def.description}
                  >
                    <span className="flex items-center justify-center w-5 h-5 rounded-full text-xs font-bold bg-white border border-current">
                      {active ? stepIdx + 1 : ' '}
                    </span>
                    <span>{def.label}</span>
                  </button>
                );
              })}
            </div>
            <p className="text-xs text-slate-400 mt-1">点击切换启用/禁用，按固定流水线顺序执行</p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={runPipeline}
              disabled={running || steps.length === 0}
              className={`px-5 py-2.5 rounded-lg text-sm font-medium transition ${
                running || steps.length === 0
                  ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                  : 'bg-indigo-600 text-white hover:bg-indigo-700'
              }`}
            >
              {running ? '执行中...' : '执行流水线'}
            </button>
            <button
              onClick={async () => {
                log('开始同步 C4 基线到数据库...', 'info');
                try {
                  const res = await api.post('/v1/docforge/sync-c4-baseline', {
                    src_root: srcRoot,
                    steps: [],
                  });
                  const data = res.data as Record<string, unknown>;
                  if (data.success) {
                    log(`C4 同步完成 ✅: project=${data.project_id}, version=${data.version}`, 'success');
                    log(`元素统计: ${JSON.stringify(data.elements)}`, 'success');
                  } else {
                    log('C4 同步失败', 'error');
                  }
                } catch (err: unknown) {
                  const msg = err instanceof Error ? err.message : String(err);
                  log(`C4 同步失败 ❌: ${msg}`, 'error');
                }
              }}
              disabled={running}
              className={`px-5 py-2.5 rounded-lg text-sm font-medium transition ${
                running
                  ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                  : 'bg-emerald-600 text-white hover:bg-emerald-700'
              }`}
            >
              同步 C4 基线
            </button>
            {results && (
              <span
                className={`text-sm font-medium ${
                  results.every((r) => r.success) ? 'text-emerald-600' : 'text-rose-600'
                }`}
              >
                {results.every((r) => r.success) ? '全部成功' : '部分失败'}
              </span>
            )}
          </div>
        </div>
      </section>

      {/* Execution Log */}
      <section className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex-1 flex flex-col min-h-[300px]">
        <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-4">执行日志</h2>
        <div className="flex-1 bg-slate-900 rounded-lg p-4 overflow-auto font-mono text-xs leading-relaxed">
          {logs.length === 0 ? (
            <span className="text-slate-500">等待执行...</span>
          ) : (
            logs.map((entry, i) => (
              <div key={i} className="flex gap-3 mb-1">
                <span className="text-slate-500 shrink-0">[{entry.time}]</span>
                <span
                  className={
                    entry.type === 'success'
                      ? 'text-emerald-400'
                      : entry.type === 'error'
                      ? 'text-rose-400'
                      : 'text-slate-200'
                  }
                >
                  {entry.text}
                </span>
              </div>
            ))
          )}
        </div>
      </section>

      {/* Results Panel */}
      {(manifest || registry || results) && (
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {manifest?.exists && (
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-slate-700">迁移清单 (_migration-manifest.md)</h3>
                <a
                  href={`/api/v1/docforge/migration-manifest?src_root=${encodeURIComponent(srcRoot)}`}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-indigo-600 hover:underline"
                >
                  下载
                </a>
              </div>
              <pre className="bg-slate-50 rounded-lg p-3 text-xs text-slate-700 overflow-auto max-h-80">
                {manifest.content}
              </pre>
            </div>
          )}

          {registry?.exists && (
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-slate-700">C4 注册表 (_c4-registry.yaml)</h3>
                <a
                  href={`/api/v1/docforge/c4-registry?src_root=${encodeURIComponent(srcRoot)}`}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-indigo-600 hover:underline"
                >
                  下载
                </a>
              </div>
              <pre className="bg-slate-50 rounded-lg p-3 text-xs text-slate-700 overflow-auto max-h-80">
                {registry.content}
              </pre>
            </div>
          )}

          {results && (
            <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-700 mb-3">执行结果摘要</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {results.map((r) => (
                  <div
                    key={r.step}
                    className={`rounded-lg p-3 border ${
                      r.success ? 'border-emerald-200 bg-emerald-50' : 'border-rose-200 bg-rose-50'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-lg">{r.success ? '✅' : '❌'}</span>
                      <span className="text-sm font-semibold text-slate-800">
                        {stepDefs.find((d) => d.key === r.step)?.label || r.step}
                      </span>
                    </div>
                    {r.detail && (
                      <div className="text-xs text-slate-600 space-y-0.5">
                        {Object.entries(r.detail).map(([k, v]) => (
                          <div key={k}>
                            <span className="text-slate-400">{k}:</span>{' '}
                            {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                          </div>
                        ))}
                      </div>
                    )}
                    {r.error && <p className="text-xs text-rose-600 mt-1">{r.error}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
}

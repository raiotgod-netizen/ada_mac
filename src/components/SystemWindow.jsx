import React, { useMemo, useState } from 'react';
import { Cpu, Activity, ListTodo, BrainCircuit, X, FolderKanban, BookOpenText, Sparkles } from 'lucide-react';

const badgeClass = (ok) => ok ? 'text-green-300 border-green-500/40 bg-green-500/10' : 'text-yellow-300 border-yellow-500/40 bg-yellow-500/10';

const SystemWindow = ({ systemState, liveScreenFrame, screenStreamActive, visualActionResult, onClose, onToggleSkill, onRegisterSkill, onRefreshSystemState, onVisionModeChange, onBluetoothAction, onSpotifyAction, onVisualAction, onRunPlaybook }) => {
    const [skillName, setSkillName] = useState('');
    const [skillId, setSkillId] = useState('');
    const [skillScope, setSkillScope] = useState('custom');
    const [spotifyQuery, setSpotifyQuery] = useState('');
    const [visualQuery, setVisualQuery] = useState('');
    const [visualInputText, setVisualInputText] = useState('');
    const [visualRetryScrolls, setVisualRetryScrolls] = useState(1);
    const [playbookResult, setPlaybookResult] = useState(null);
    const runtime = systemState?.runtime || {};
    const manager = systemState?.manager || {};
    const queue = systemState?.queue || { counts: {}, recent: [] };
    const orchestrator = systemState?.orchestrator || {};
    const gemini = manager?.providers?.gemini || {};
    const project = systemState?.project || {};
    const memory = systemState?.memory || {};
    const improvements = systemState?.improvements || [];
    const capabilities = systemState?.capabilities || {};
    const vision = systemState?.vision || {};
    const email = systemState?.email || {};
    const observer = systemState?.system_observer || {};
    const globalMemory = systemState?.global_memory || {};
    const runtimeMemory = systemState?.runtime_memory || {};
    const agentCore = systemState?.agent_core || {};
    const worldState = systemState?.world_state || {};
    const routines = systemState?.routines || {};
    const security = systemState?.security || {};
    const bluetooth = systemState?.bluetooth || {};
    const desktopCognition = systemState?.desktop_cognition || {};
    const visualMemory = systemState?.visual_action_result?.visual_memory || systemState?.visual_memory || {};
    const visualPlaybook = systemState?.visual_playbook || {};
    const capabilityFramework = systemState?.capability_framework || {};
    const awareness = agentCore?.capability_awareness || {};
    const skillToolMap = capabilityFramework?.skill_tool_map || {};
    const skillMappings = useMemo(() => {
        return (capabilityFramework?.skills || []).map((skill) => ({
            ...skill,
            mappedTools: skillToolMap[skill.id] || skill.tools || [],
        }));
    }, [capabilityFramework, skillToolMap]);

    return (
        <div className="w-full h-full relative bg-[#0f1115] rounded-lg overflow-hidden flex flex-col border border-gray-800">
            <div className="h-8 bg-[#222] border-b border-gray-700 flex items-center justify-between px-2 shrink-0 cursor-grab active:cursor-grabbing">
                <div className="flex items-center gap-2 text-gray-300 text-xs font-mono">
                    <Cpu size={14} className="text-cyan-500" />
                    <span>SYSTEM_CORE</span>
                </div>
                <button onClick={onClose} className="hover:bg-red-500/20 text-gray-400 hover:text-red-400 p-1 rounded transition-colors">
                    <X size={14} />
                </button>
            </div>

            <div className="p-3 grid grid-cols-2 gap-3 text-xs overflow-auto">
                <div className="rounded border border-gray-800 bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-cyan-400 mb-2"><Activity size={14} /> Runtime</div>
                    <div className="space-y-2 text-gray-300">
                        <div>Core: <span className="text-white">{manager?.core?.status || 'unknown'}</span></div>
                        <div>Runtime mode: <span className="text-white">{runtime?.mode || 'idle'}</span></div>
                        <div className={`inline-flex px-2 py-1 rounded border ${badgeClass(gemini?.available)}`}>
                            Gemini: {gemini?.available ? 'available' : (gemini?.mode || 'degraded')}
                        </div>
                        <div>Vision: <span className="text-white">{vision?.source || 'camera'}</span> {vision?.streaming ? '(streaming)' : '(idle)'}</div>
                        <div>Email: <span className="text-white">{email?.configured ? (email?.address || 'configurado') : 'sin configurar'}</span></div>
                        <div>Visión: <span className="text-white">{vision?.context?.available ? 'contexto visual activo' : 'sin contexto visual'}</span></div>
                        <div className="flex flex-wrap gap-2 pt-1">
                            <button onClick={onRefreshSystemState} className="px-2 py-1 rounded border border-cyan-800 text-cyan-200 hover:bg-cyan-950/30">Refresh</button>
                            <button onClick={() => onVisionModeChange?.('screen')} className="px-2 py-1 rounded border border-cyan-800 text-cyan-200 hover:bg-cyan-950/30">Screen</button>
                            <button onClick={() => onVisionModeChange?.('camera')} className="px-2 py-1 rounded border border-cyan-800 text-cyan-200 hover:bg-cyan-950/30">Camera</button>
                            <button onClick={() => onVisionModeChange?.('none')} className="px-2 py-1 rounded border border-gray-700 text-gray-300 hover:bg-gray-900/40">None</button>
                        </div>
                        {runtime?.last_error && (
                            <div className="text-yellow-300 whitespace-pre-wrap">{runtime.last_error}</div>
                        )}
                    </div>
                </div>

                <div className="rounded border border-gray-800 bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-cyan-400 mb-2"><BrainCircuit size={14} /> Orchestrator</div>
                    <div className="space-y-2 text-gray-300">
                        <div>Intent: <span className="text-white">{orchestrator?.intent || 'idle'}</span></div>
                        <div>Route: <span className="text-white">{orchestrator?.route || 'conversation'}</span></div>
                        <div>Confidence: <span className="text-white">{orchestrator?.confidence ?? 0}</span></div>
                        <div>Tools: <span className="text-white">{(orchestrator?.tools || []).join(', ') || 'none'}</span></div>
                    </div>
                </div>

                <div className="rounded border border-gray-800 bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-cyan-400 mb-2"><FolderKanban size={14} /> Proyecto</div>
                    <div className="space-y-2 text-gray-300">
                        <div>Actual: <span className="text-white">{project?.current || 'sin iniciar'}</span></div>
                        <div className="break-all opacity-80">{project?.path || 'sin ruta activa'}</div>
                        <div>Docs: <span className="text-white">{project?.documents_count ?? 0}</span> · Screens: <span className="text-white">{project?.screenshots_count ?? 0}</span></div>
                        <div>Downloads: <span className="text-white">{project?.downloads_count ?? 0}</span> · Uploads: <span className="text-white">{project?.uploads_count ?? 0}</span></div>
                        <div>Mejoras: <span className="text-white">{project?.improvements_count ?? 0}</span></div>
                    </div>
                </div>

                <div className="rounded border border-gray-800 bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-cyan-400 mb-2"><BookOpenText size={14} /> Memoria</div>
                    <div className="space-y-2 text-gray-300">
                        <div>Reglas: <span className="text-white">{memory?.rules_count ?? 0}</span></div>
                        <div>Idioma: <span className="text-white">{memory?.preferences?.language || 'es'}</span></div>
                        <div>Usuario: <span className="text-white">{memory?.preferences?.address_user_as || 'usuario'}</span></div>
                        <div>Journal: <span className="text-white">{(memory?.recent_journal || []).length}</span> eventos</div>
                    </div>
                </div>

                <div className="col-span-2 rounded border border-gray-800 bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-cyan-400 mb-2"><BrainCircuit size={14} /> Agent Core</div>
                    <div className="grid grid-cols-2 gap-3 text-[11px] text-gray-300">
                        <div>
                            <div>Estado: <span className="text-white">{agentCore?.status || 'idle'}</span></div>
                            <div>Objetivo actual: <span className="text-white">{agentCore?.current_goal || 'sin objetivo'}</span></div>
                            <div>Modo: <span className="text-white">{agentCore?.policy?.mode || 'supervised'}</span></div>
                            <div>Riesgo último: <span className="text-white">{agentCore?.last_plan?.policy?.risk || 'n/a'}</span></div>
                        </div>
                        <div>
                            <div>Runs recientes: <span className="text-white">{(agentCore?.recent_runs || []).length}</span></div>
                            <div>Último intent: <span className="text-white">{agentCore?.last_plan?.intent || 'none'}</span></div>
                            <div>Última ruta: <span className="text-white">{agentCore?.last_plan?.route || 'none'}</span></div>
                            <div>Progreso: <span className="text-white">{agentCore?.last_plan?.progress?.completed_steps || 0}/{agentCore?.last_plan?.progress?.total_steps || 0}</span></div>
                            <div>Routines activas: <span className="text-white">{agentCore?.routines?.active || 0}</span></div>
                        </div>
                    </div>
                </div>

                <div className="col-span-2 rounded border border-gray-800 bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-cyan-400 mb-2"><BrainCircuit size={14} /> Desktop cognition</div>
                    <div className="grid grid-cols-3 gap-3 text-[11px] text-gray-300">
                        <div>
                            <div className="text-white font-semibold mb-1">Modo inferido</div>
                            <div>{desktopCognition?.mode || 'general'}</div>
                            <div>Confianza: <span className="text-white">{desktopCognition?.confidence ?? 0}</span></div>
                            <div>Proceso: <span className="text-white">{desktopCognition?.focus?.process || 'n/a'}</span></div>
                            <div>Ventana: <span className="text-white">{desktopCognition?.focus?.window_title || 'n/a'}</span></div>
                            <div>OCR real listo: <span className="text-white">{desktopCognition?.perception?.ocr_ready ? 'sí' : 'no'}</span></div>
                            <div>Líneas OCR: <span className="text-white">{desktopCognition?.perception?.ocr_lines_count || 0}</span></div>
                            <div>Bloques texto: <span className="text-white">{desktopCognition?.perception?.text_regions_count || 0}</span></div>
                            <div>Targets UI: <span className="text-white">{desktopCognition?.perception?.ui_targets_count || 0}</span></div>
                        </div>
                        <div>
                            <div className="text-white font-semibold mb-1">Intención probable</div>
                            <div className="opacity-80 max-h-24 overflow-auto">
                                {(desktopCognition?.activity?.likely_intents || []).map((item, idx) => (
                                    <div key={`intent-${idx}`}>• {item}</div>
                                ))}
                                {(!(desktopCognition?.activity?.likely_intents || []).length) && <div className="text-gray-500">Sin inferencias todavía.</div>}
                            </div>
                        </div>
                        <div>
                            <div className="text-white font-semibold mb-1">Recomendaciones</div>
                            <div className="opacity-80 max-h-24 overflow-auto">
                                {(desktopCognition?.recommendations || []).map((item, idx) => (
                                    <div key={`rec-${idx}`}>• {item}</div>
                                ))}
                                {(!(desktopCognition?.recommendations || []).length) && <div className="text-gray-500">Sin recomendaciones todavía.</div>}
                            </div>
                        </div>
                    </div>
                    <div className="mt-3 grid grid-cols-2 gap-3 text-[11px] text-gray-300 border-t border-gray-800 pt-3">
                        <div>
                            <div className="text-white font-semibold mb-1">Riesgos</div>
                            <div className="opacity-80 max-h-24 overflow-auto">
                                {(desktopCognition?.risk_flags || []).map((item, idx) => (
                                    <div key={`risk-${idx}`}>• {item}</div>
                                ))}
                                {(!(desktopCognition?.risk_flags || []).length) && <div className="text-gray-500">Sin flags de riesgo relevantes.</div>}
                            </div>
                        </div>
                        <div>
                            <div className="text-white font-semibold mb-1">Automatizaciones sugeridas</div>
                            <div className="opacity-80 max-h-24 overflow-auto">
                                {(desktopCognition?.suggested_automations || []).map((item) => (
                                    <div key={item.id}>• {item.title}</div>
                                ))}
                                {(!(desktopCognition?.suggested_automations || []).length) && <div className="text-gray-500">Sin automatizaciones sugeridas todavía.</div>}
                            </div>
                        </div>
                    </div>
                    <div className="mt-3 text-[11px] text-cyan-200">{desktopCognition?.summary || 'Sin resumen cognitivo todavía.'}</div>
                </div>

                <div className="col-span-2 rounded border border-gray-800 bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-cyan-400 mb-2"><Activity size={14} /> Percepción visual avanzada</div>
                    <div className="grid grid-cols-3 gap-3 text-[11px] text-gray-300">
                        <div>
                            <div className="text-white font-semibold mb-1">OCR</div>
                            <div className="opacity-80 max-h-28 overflow-auto">
                                {(vision?.context?.screen?.ocr_lines || []).slice(0, 8).map((item, idx) => (
                                    <div key={`ocr-${idx}`}>• {item.text} <span className="text-gray-500">({item.confidence})</span></div>
                                ))}
                                {(!(vision?.context?.screen?.ocr_lines || []).length) && <div className="text-gray-500">Sin texto OCR todavía.</div>}
                            </div>
                        </div>
                        <div>
                            <div className="text-white font-semibold mb-1">Regiones de texto</div>
                            <div className="opacity-80 max-h-28 overflow-auto">
                                {(vision?.context?.screen?.text_regions || []).slice(0, 8).map((item, idx) => (
                                    <div key={`txt-${idx}`}>• ({item.x}, {item.y}) {item.w}x{item.h} · conf {item.confidence}</div>
                                ))}
                                {(!(vision?.context?.screen?.text_regions || []).length) && <div className="text-gray-500">Sin bloques detectados todavía.</div>}
                            </div>
                        </div>
                        <div>
                            <div className="text-white font-semibold mb-1">Objetivos UI</div>
                            <div className="opacity-80 max-h-28 overflow-auto">
                                {(vision?.context?.screen?.ui_targets || []).slice(0, 8).map((item, idx) => (
                                    <div key={`ui-${idx}`}>• {item.semantic_role || item.type} @ ({item.cx}, {item.cy}) · conf {item.confidence}{item.nearby_text ? ` · ${item.nearby_text}` : ''}</div>
                                ))}
                                {(!(vision?.context?.screen?.ui_targets || []).length) && <div className="text-gray-500">Sin controles detectados todavía.</div>}
                            </div>
                        </div>
                    </div>
                    <div className="mt-3 text-[11px] text-cyan-200">{vision?.context?.screen?.ocr_summary || vision?.context?.screen?.target_summary || 'Sin resumen de targets todavía.'}</div>
                </div>

                <div className="col-span-2 rounded border border-gray-800 bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-cyan-400 mb-2"><Cpu size={14} /> Estado del mundo</div>
                    <div className="grid grid-cols-4 gap-3 text-[11px] text-gray-300">
                        <div>
                            <div className="text-white font-semibold mb-1">Runtime</div>
                            <div>{worldState?.runtime_mode || 'idle'}</div>
                            <div>Ventana activa: {worldState?.desktop?.active_window || 'ninguna'}</div>
                            <div>Visión: {worldState?.vision?.available ? 'sí' : 'no'}</div>
                        </div>
                        <div>
                            <div className="text-white font-semibold mb-1">Proyecto</div>
                            <div>{worldState?.project?.current || 'sin proyecto'}</div>
                            <div>Docs: {worldState?.project?.documents || 0}</div>
                            <div>Mejoras: {worldState?.project?.improvements || 0}</div>
                        </div>
                        <div>
                            <div className="text-white font-semibold mb-1">Memoria</div>
                            <div>Reglas: {worldState?.memory?.rules || 0}</div>
                            <div>Proyectos: {worldState?.memory?.projects_known || 0}</div>
                            <div>Macros: {worldState?.memory?.macros_known || 0}</div>
                            <div>Caps runtime: {worldState?.memory?.runtime_capabilities || 0}</div>
                        </div>
                        <div>
                            <div className="text-white font-semibold mb-1">Queue</div>
                            <div>Running: {worldState?.queue?.running || 0}</div>
                            <div>Queued: {worldState?.queue?.queued || 0}</div>
                            <div>Failed: {worldState?.queue?.failed || 0}</div>
                        </div>
                    </div>
                    <div className="mt-3 text-[11px] text-gray-300 border-t border-gray-800 pt-3">
                        <div className="text-white font-semibold mb-1">Resumen visual</div>
                        <div>{worldState?.vision?.summary || 'Sin resumen visual todavía.'}</div>
                        <div className="mt-2 text-white font-semibold">Pistas de acción</div>
                        <div className="opacity-80 max-h-20 overflow-auto">
                            {(worldState?.vision?.screen?.action_hints || []).map((hint, idx) => (
                                <div key={idx}>• {hint}</div>
                            ))}
                            {(!(worldState?.vision?.screen?.action_hints || []).length) && <div className="text-gray-500">Sin pistas de acción todavía.</div>}
                        </div>
                    </div>
                </div>

                <div className="col-span-2 rounded border border-gray-800 bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-cyan-400 mb-2"><Sparkles size={14} /> Capacidades / mejoras</div>
                    <div className="flex flex-wrap gap-2 mb-3 text-[11px]">
                        {Object.entries(capabilities).map(([key, enabled]) => (
                            <div key={key} className={`px-2 py-1 rounded border ${badgeClass(enabled)}`}>
                                {key}
                            </div>
                        ))}
                    </div>
                    <div className="mb-3 text-[11px] text-gray-300">
                        <div className="text-white font-semibold mb-1">Conciencia operativa</div>
                        <div className="flex flex-wrap gap-2">
                            {Object.entries(awareness).map(([key, enabled]) => (
                                <div key={key} className={`px-2 py-1 rounded border ${badgeClass(enabled)}`}>
                                    {key}
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="space-y-2 max-h-32 overflow-auto text-[11px] text-gray-300">
                        {improvements.map((item) => (
                            <div key={item.id} className="rounded border border-gray-800 p-2">
                                <div className="flex items-center justify-between gap-2">
                                    <div className="text-white font-semibold">{item.title}</div>
                                    <div className="text-cyan-300">{item.status}</div>
                                </div>
                                <div className="opacity-70">{item.id}</div>
                            </div>
                        ))}
                        {improvements.length === 0 && <div className="text-gray-500">Sin mejoras registradas todavía.</div>}
                    </div>
                </div>

                <div className="col-span-2 rounded border border-gray-800 bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-cyan-400 mb-2"><ListTodo size={14} /> Routines</div>
                    <div className="grid grid-cols-2 gap-3 text-[11px] text-gray-300">
                        <div>
                            <div>Total: <span className="text-white">{routines?.count || 0}</span></div>
                            <div>Activas: <span className="text-white">{routines?.enabled || 0}</span></div>
                            <div>Vencidas: <span className="text-white">{routines?.due || 0}</span></div>
                            <div>Último evento: <span className="text-white">{agentCore?.routines?.last_event || 'sin eventos'}</span></div>
                        </div>
                        <div className="opacity-80 max-h-24 overflow-auto">
                            {(routines?.items || []).slice(0, 6).map((item) => (
                                <div key={item.id}>• {item.name} ({item.enabled ? 'on' : 'off'}) · {item.schedule_type || 'manual'} · next: {item.next_run_at ? 'programada' : 'n/a'}</div>
                            ))}
                            {(!routines?.items || routines.items.length === 0) && <div className="text-gray-500">Sin routines todavía.</div>}
                        </div>
                    </div>
                </div>

                <div className="col-span-2 rounded border border-gray-800 bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-cyan-400 mb-2"><BookOpenText size={14} /> Memoria global</div>
                    <div className="grid grid-cols-3 gap-3 text-[11px] text-gray-300">
                        <div>
                            <div className="text-white font-semibold mb-1">Proyectos</div>
                            <div>{globalMemory?.projects_count ?? 0} totales</div>
                            <div className="opacity-80 max-h-24 overflow-auto">
                                {(globalMemory?.recent_projects || []).slice(0, 6).map((item, idx) => (
                                    <div key={`${item.name}-${idx}`}>• {item.name}</div>
                                ))}
                            </div>
                        </div>
                        <div>
                            <div className="text-white font-semibold mb-1">Mejoras</div>
                            <div>{globalMemory?.improvements_count ?? 0} registradas</div>
                            <div className="opacity-80 max-h-24 overflow-auto">
                                {(globalMemory?.recent_improvements || []).slice(0, 6).map((item, idx) => (
                                    <div key={`${item.id}-${idx}`}>• {item.project}: {item.title}</div>
                                ))}
                            </div>
                        </div>
                        <div>
                            <div className="text-white font-semibold mb-1">Macros</div>
                            <div>{(globalMemory?.automation_macros || []).length} guardadas</div>
                            <div className="opacity-80 max-h-24 overflow-auto">
                                {(globalMemory?.automation_macros || []).slice(0, 6).map((item, idx) => (
                                    <div key={`${item.name}-${idx}`}>• {item.name}</div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                <div className="col-span-2 rounded border border-gray-800 bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-cyan-400 mb-2"><BrainCircuit size={14} /> Framework de capacidades</div>
                    <div className="grid grid-cols-2 gap-3 text-[11px] text-gray-300 mb-3">
                        <div className="col-span-2 rounded border border-gray-800 bg-black/20 p-2">
                            <div className="text-white font-semibold mb-2">Registrar skill dinámica</div>
                            <div className="grid grid-cols-4 gap-2">
                                <input value={skillId} onChange={(e) => setSkillId(e.target.value)} placeholder="id_skill" className="bg-black/40 border border-gray-700 rounded px-2 py-1 text-gray-200" />
                                <input value={skillName} onChange={(e) => setSkillName(e.target.value)} placeholder="Nombre visible" className="bg-black/40 border border-gray-700 rounded px-2 py-1 text-gray-200" />
                                <input value={skillScope} onChange={(e) => setSkillScope(e.target.value)} placeholder="scope" className="bg-black/40 border border-gray-700 rounded px-2 py-1 text-gray-200" />
                                <button
                                    onClick={() => {
                                        if (!skillId.trim()) return;
                                        onRegisterSkill && onRegisterSkill({
                                            id: skillId.trim(),
                                            name: skillName.trim() || skillId.trim(),
                                            scope: skillScope.trim() || 'custom',
                                            enabled: true,
                                        });
                                        setSkillId('');
                                        setSkillName('');
                                    }}
                                    className="px-2 py-1 rounded border border-cyan-500/40 text-cyan-300"
                                >
                                    registrar
                                </button>
                            </div>
                        </div>
                        <div>
                            <div>Skills activas: <span className="text-white">{capabilityFramework?.skills_enabled || 0}</span></div>
                            <div className="opacity-80 max-h-40 overflow-auto mt-2 space-y-2">
                                {skillMappings.slice(0, 10).map((item, idx) => (
                                    <div key={`skill-wrap-${idx}`} className="rounded border border-gray-800 p-2">
                                    <div className="flex items-center justify-between gap-2">
                                        <span>• {item.name} ({item.enabled ? 'on' : 'off'})</span>
                                        <button
                                            onClick={() => onToggleSkill && onToggleSkill(item.id, !item.enabled)}
                                            className={`px-2 py-0.5 rounded border text-[10px] ${item.enabled ? 'border-green-500/40 text-green-300' : 'border-yellow-500/40 text-yellow-300'}`}
                                        >
                                            {item.enabled ? 'desactivar' : 'activar'}
                                        </button>
                                    </div>
                                    <div className="mt-1 text-[10px] text-gray-500">{item.id} · scope: {item.scope || 'custom'}</div>
                                    <div className="mt-1 text-[10px] text-gray-400">tools: {(item.mappedTools || []).join(', ') || 'sin mapping todavía'}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div>
                            <div>Tools activas: <span className="text-white">{capabilityFramework?.tools_enabled || 0}</span></div>
                            <div className="opacity-80 max-h-24 overflow-auto mt-2">
                                {(capabilityFramework?.tools || []).slice(0, 10).map((item, idx) => (
                                    <div key={`tool-${idx}`}>• {item.name} [{item.risk}]</div>
                                ))}
                            </div>
                            <div className="mt-2 text-[10px] text-gray-500">Mappings: {(Object.keys(capabilityFramework?.skill_tool_map || {})).length} skills con tools asociadas.</div>
                        </div>
                    </div>
                </div>

                <div className="col-span-2 rounded border border-gray-800 bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-cyan-400 mb-2"><BrainCircuit size={14} /> Memoria operativa del runtime</div>
                    <div className="grid grid-cols-2 gap-3 text-[11px] text-gray-300">
                        <div>
                            <div className="text-white font-semibold mb-1">Capacidades</div>
                            <div className="opacity-80 max-h-24 overflow-auto">
                                {(runtimeMemory?.capabilities || []).map((item, idx) => (
                                    <div key={`cap-${idx}`}>• {item}</div>
                                ))}
                                {(!(runtimeMemory?.capabilities || []).length) && <div className="text-gray-500">Sin capacidades registradas.</div>}
                            </div>
                        </div>
                        <div>
                            <div className="text-white font-semibold mb-1">Mejoras activas</div>
                            <div className="opacity-80 max-h-24 overflow-auto">
                                {(runtimeMemory?.improvements || []).map((item, idx) => (
                                    <div key={`imp-${idx}`}>• {item}</div>
                                ))}
                                {(!(runtimeMemory?.improvements || []).length) && <div className="text-gray-500">Sin mejoras activas registradas.</div>}
                            </div>
                        </div>
                        <div>
                            <div className="text-white font-semibold mb-1">Limitaciones conocidas</div>
                            <div className="opacity-80 max-h-24 overflow-auto">
                                {(runtimeMemory?.known_issues || []).map((item, idx) => (
                                    <div key={`issue-${idx}`}>• {item}</div>
                                ))}
                                {(!(runtimeMemory?.known_issues || []).length) && <div className="text-gray-500">Sin issues registrados.</div>}
                            </div>
                        </div>
                        <div>
                            <div className="text-white font-semibold mb-1">Flujos recomendados</div>
                            <div className="opacity-80 max-h-24 overflow-auto">
                                {(runtimeMemory?.recommended_flows || []).map((item, idx) => (
                                    <div key={`flow-${idx}`}>• {item}</div>
                                ))}
                                {(!(runtimeMemory?.recommended_flows || []).length) && <div className="text-gray-500">Sin flujos recomendados.</div>}
                            </div>
                        </div>
                    </div>
                </div>

                <div className="col-span-2 rounded border border-gray-800 bg-black/30 p-3">
                    <div className="flex items-center justify-between gap-2 text-cyan-400 mb-2">
                        <div className="flex items-center gap-2"><Activity size={14} /> Bluetooth</div>
                        <div className="flex flex-wrap gap-2 text-[11px]">
                            <button onClick={() => onBluetoothAction?.('inventory')} className="px-2 py-1 rounded border border-cyan-800 text-cyan-200 hover:bg-cyan-950/30">Refresh</button>
                            <button onClick={() => onBluetoothAction?.('service_on')} className="px-2 py-1 rounded border border-green-800 text-green-200 hover:bg-green-950/30">On</button>
                            <button onClick={() => onBluetoothAction?.('service_off')} className="px-2 py-1 rounded border border-yellow-800 text-yellow-200 hover:bg-yellow-950/30">Off</button>
                            <button onClick={() => onBluetoothAction?.('settings')} className="px-2 py-1 rounded border border-gray-700 text-gray-300 hover:bg-gray-900/40">Settings</button>
                        </div>
                    </div>
                    <div className="grid grid-cols-3 gap-3 text-[11px] text-gray-300">
                        <div>
                            <div className="text-white font-semibold mb-1">Estado</div>
                            <div>Disponible: <span className="text-white">{bluetooth?.available ? 'sí' : 'no'}</span></div>
                            <div>Emparejados: <span className="text-white">{bluetooth?.paired_count || 0}</span></div>
                            <div>Conectados: <span className="text-white">{bluetooth?.connected_count || 0}</span></div>
                        </div>
                        <div>
                            <div className="text-white font-semibold mb-1">Adaptadores</div>
                            <div className="opacity-80 max-h-24 overflow-auto">
                                {(bluetooth?.adapters || []).slice(0, 6).map((item, idx) => (
                                    <div key={`bt-adapter-${idx}`}>• {item.FriendlyName || item.friendlyName || item.name || 'Bluetooth'} ({item.Status || item.status || 'n/a'})</div>
                                ))}
                                {(!(bluetooth?.adapters || []).length) && <div className="text-gray-500">Sin adaptadores visibles.</div>}
                            </div>
                        </div>
                        <div>
                            <div className="text-white font-semibold mb-1">Dispositivos conocidos</div>
                            <div className="opacity-80 max-h-24 overflow-auto">
                                {(bluetooth?.known || []).slice(0, 6).map((item, idx) => (
                                    <div key={`bt-known-${idx}`}>• {item.name}</div>
                                ))}
                                {(!(bluetooth?.known || []).length) && <div className="text-gray-500">Sin memoria Bluetooth todavía.</div>}
                            </div>
                        </div>
                    </div>
                </div>

                <div className="col-span-2 rounded border border-gray-800 bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-cyan-400 mb-2"><Sparkles size={14} /> ADA Proactiva</div>
                    <div className="flex items-center gap-4 text-[11px] text-gray-300 mb-2">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={systemState?.proactive_engine?.enabled ?? true}
                                onChange={(e) => {
                                    const evt = new CustomEvent('socket_event', { detail: { event: 'toggle_proactive', data: { enabled: e.target.checked } } });
                                    window.dispatchEvent(evt);
                                }}
                                className="accent-cyan-500 w-3.5 h-3.5"
                            />
                            <span>ADA proactiva</span>
                        </label>
                        {systemState?.proactive_engine?.suppressed ? (
                            <span className="text-yellow-400">Silenciada hasta {new Date(systemState.proactive_engine.suppress_until * 1000).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</span>
                        ) : (
                            <span className="text-green-400">Escuchando</span>
                        )}
                        {systemState?.proactive_engine?.last_spoke > 0 && (
                            <span className="text-gray-500">Última: hace {Math.round((Date.now()/1000 - systemState.proactive_engine.last_spoke)/60)} min</span>
                        )}
                        <button
                            onClick={() => {
                                const evt = new CustomEvent('socket_event', { detail: { event: 'set_quiet_mode', data: { minutes: 30 } } });
                                window.dispatchEvent(evt);
                            }}
                            className="px-2 py-0.5 rounded border border-yellow-800 text-yellow-300 hover:bg-yellow-900/20 text-[11px]"
                        >Callate (30 min)</button>
                    </div>
                </div>

                <div className="col-span-2 rounded border border-gray-800 bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-cyan-400 mb-2"><BrainCircuit size={14} /> Memoria de Largo Plazo</div>
                    <div className="text-[11px] text-gray-400 mb-2">
                        <span className="text-white">{systemState?.long_term_memory?.total ?? 0}</span> bloques —{" "}
                        {Object.entries(systemState?.long_term_memory?.by_category || {}).map(([cat, count]) => (
                            <span key={cat} className="mr-2">{cat}: <span className="text-white">{count}</span></span>
                        ))}
                    </div>
                    <div className="mb-2">
                        <div className="flex gap-2 mb-1">
                            <input
                                type="text"
                                id="mem-search-input"
                                placeholder="Buscar en memoria..."
                                className="flex-1 bg-black/50 border border-gray-700 rounded px-2 py-0.5 text-[11px] text-gray-200 placeholder-gray-600 focus:border-cyan-600 outline-none"
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter') {
                                        const q = e.target.value;
                                        if (q.trim()) {
                                            const evt = new CustomEvent('socket_event', { detail: { event: 'memory_search', data: { query: q, top_k: 5 } } });
                                            window.dispatchEvent(evt);
                                        }
                                    }
                                }}
                            />
                            <button
                                onClick={() => {
                                    const inp = document.getElementById('mem-search-input');
                                    const q = inp?.value || '';
                                    if (q.trim()) {
                                        const evt = new CustomEvent('socket_event', { detail: { event: 'memory_search', data: { query: q, top_k: 5 } } });
                                        window.dispatchEvent(evt);
                                    }
                                }}
                                className="px-2 py-0.5 rounded border border-cyan-800 text-cyan-300 hover:bg-cyan-900/30 text-[11px]"
                            >Buscar</button>
                        </div>
                        <div className="flex gap-2">
                            <input
                                type="text"
                                id="mem-add-input"
                                placeholder="Agregar dato: 'Mi nombre es ...'"
                                className="flex-1 bg-black/50 border border-gray-700 rounded px-2 py-0.5 text-[11px] text-gray-200 placeholder-gray-600 focus:border-green-600 outline-none"
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter') {
                                        const q = e.target.value;
                                        if (q.trim()) {
                                            const evt = new CustomEvent('socket_event', { detail: { event: 'memory_add', data: { content: q, category: 'user_facts', importance: 4 } } });
                                            window.dispatchEvent(evt);
                                            e.target.value = '';
                                        }
                                    }
                                }}
                            />
                            <button
                                onClick={() => {
                                    const inp = document.getElementById('mem-add-input');
                                    const q = inp?.value || '';
                                    if (q.trim()) {
                                        const evt = new CustomEvent('socket_event', { detail: { event: 'memory_add', data: { content: q, category: 'user_facts', importance: 4 } } });
                                        window.dispatchEvent(evt);
                                        inp.value = '';
                                    }
                                }}
                                className="px-2 py-0.5 rounded border border-green-800 text-green-300 hover:bg-green-900/30 text-[11px]"
                            >+ Guardar</button>
                        </div>
                    </div>
                    <div className="text-[11px] text-gray-300 space-y-1">
                        {(systemState?.long_term_memory?.recent || []).map((item, idx) => (
                            <div key={`mem-rec-${idx}`} className="text-gray-400 truncate">• {item}</div>
                        ))}
                        {!(systemState?.long_term_memory?.recent || []).length && <div className="text-gray-600">Sin memorias todavía.</div>}
                    </div>
                </div>

                <div className="col-span-2 rounded border border-gray-800 bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-cyan-400 mb-2"><Activity size={14} /> Seguridad / observación del PC</div>
                    <div className="mb-3 text-[11px] text-gray-300 border-b border-gray-800 pb-3">
                        <div className="text-white font-semibold mb-2">Vista en tiempo real</div>
                        <div className="mb-2">Estado: <span className="text-white">{screenStreamActive ? 'stream activo' : 'stream inactivo'}</span></div>
                        <div className="rounded border border-gray-800 overflow-hidden bg-black aspect-video flex items-center justify-center">
                            {liveScreenFrame ? (
                                <img src={`data:image/jpeg;base64,${liveScreenFrame}`} alt="Live screen" className="w-full h-full object-contain" />
                            ) : (
                                <div className="text-gray-500">Sin frame de pantalla todavía.</div>
                            )}
                        </div>
                    </div>
                    <div className="mb-3 text-[11px] text-gray-300 border-b border-gray-800 pb-3">
                        <div className="text-white font-semibold mb-1">Auditoría defensiva</div>
                        <div>Eventos: <span className="text-white">{security?.count || 0}</span></div>
                        <div className="opacity-80 max-h-24 overflow-auto mt-2">
                            {(security?.recent || []).slice(0, 6).map((item, idx) => (
                                <div key={`${item.kind}-${idx}`}>• {item.kind}</div>
                            ))}
                            {(!(security?.recent || []).length) && <div className="text-gray-500">Sin eventos de seguridad todavía.</div>}
                        </div>
                    </div>
                    <div className="grid grid-cols-3 gap-3 text-[11px] text-gray-300">
                        <div>
                            <div className="text-white font-semibold mb-1">Ventanas</div>
                            <div>{observer?.windows?.count ?? 0} detectadas</div>
                            {observer?.active_window?.title && (
                                <div className="text-cyan-300 mb-1">Activa: {observer.active_window.title}</div>
                            )}
                            <div className="opacity-80 max-h-24 overflow-auto">
                                {(observer?.windows?.items || []).slice(0, 6).map((item, idx) => (
                                    <div key={`${item.pid}-${idx}`}>• {item.title}</div>
                                ))}
                            </div>
                        </div>
                        <div>
                            <div className="text-white font-semibold mb-1">Navegadores</div>
                            <div>{observer?.browser_windows?.count ?? 0} ventanas</div>
                            <div className="opacity-80 max-h-24 overflow-auto">
                                {(observer?.browser_windows?.items || []).slice(0, 6).map((item, idx) => (
                                    <div key={`${item.pid}-${idx}`}>• {item.process}: {item.title}</div>
                                ))}
                            </div>
                        </div>
                        <div>
                            <div className="text-white font-semibold mb-1">Procesos</div>
                            <div>{observer?.processes?.count ?? 0} visibles</div>
                            <div className="opacity-80 max-h-24 overflow-auto">
                                {(observer?.processes?.items || []).slice(0, 6).map((item, idx) => (
                                    <div key={`${item.Id || item.pid}-${idx}`}>• {item.Name || item.name} ({item.MemoryMB || 0} MB)</div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                <div className="col-span-2 rounded border border-gray-800 bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-cyan-400 mb-2"><Activity size={14} /> Acciones visuales</div>
                    <div className="space-y-2 text-[11px] text-gray-300 mb-3">
                        <input
                            value={visualQuery}
                            onChange={(e) => setVisualQuery(e.target.value)}
                            placeholder="Texto visible o target, por ejemplo: Google, Resumir, search"
                            className="w-full bg-black/40 border border-gray-800 rounded px-2 py-1 text-gray-200 outline-none"
                        />
                        <div className="flex flex-wrap gap-2 items-center">
                            <button onClick={() => visualQuery.trim() && onVisualAction?.('resolve', visualQuery.trim(), { retry_scrolls: visualRetryScrolls })} className="px-2 py-1 rounded border border-cyan-800 text-cyan-200 hover:bg-cyan-950/30">Resolver</button>
                            <button onClick={() => visualQuery.trim() && onVisualAction?.('click', visualQuery.trim(), { retry_scrolls: visualRetryScrolls })} className="px-2 py-1 rounded border border-green-800 text-green-200 hover:bg-green-950/30">Click</button>
                            <div className="flex items-center gap-2 text-gray-400">
                                <span>Reintentos scroll</span>
                                <input type="number" min="0" max="5" value={visualRetryScrolls} onChange={(e) => setVisualRetryScrolls(parseInt(e.target.value || '0', 10))} className="w-14 bg-black/40 border border-gray-800 rounded px-2 py-1 text-gray-200 outline-none" />
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <input
                                value={visualInputText}
                                onChange={(e) => setVisualInputText(e.target.value)}
                                placeholder="Texto para escribir en el target"
                                className="flex-1 bg-black/40 border border-gray-800 rounded px-2 py-1 text-gray-200 outline-none"
                            />
                            <button onClick={() => visualQuery.trim() && onVisualAction?.('type', visualQuery.trim(), { text: visualInputText, press_enter: false, retry_scrolls: visualRetryScrolls })} className="px-3 py-1 rounded border border-yellow-800 text-yellow-200 hover:bg-yellow-950/30">Escribir</button>
                        </div>
                    </div>
                    {visualActionResult && (
                        <div className="mt-2 border-t border-gray-800 pt-2 text-[11px]">
                            {visualActionResult.ok ? (
                                <div className="text-green-300">✓ {visualActionResult.result}</div>
                            ) : (
                                <div className="text-yellow-300">⚠ {visualActionResult.result}</div>
                            )}
                        </div>
                    )}
                </div>

                <div className="col-span-2 rounded border border-gray-800 bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-cyan-400 mb-2"><BookOpenText size={14} /> Memoria visual</div>
                    <div className="text-[11px] text-gray-300">
                        <div>Contextos: <span className="text-white">{visualMemory?.contexts || 0}</span></div>
                        <div className="opacity-80 max-h-24 overflow-auto mt-2">
                            {(visualMemory?.sample || []).map((item, idx) => (
                                <div key={`vm-${idx}`} className="mb-2">
                                    <div className="text-white">{item.context}</div>
                                    {(item.targets || []).map((target, tidx) => (
                                        <div key={`vmt-${idx}-${tidx}`}>• {target.query} → {target.label || 'target'}</div>
                                    ))}
                                </div>
                            ))}
                            {(!(visualMemory?.sample || []).length) && <div className="text-gray-500">Sin memoria visual todavía.</div>}
                        </div>
                    </div>
                </div>

                <div className="col-span-2 rounded border border-purple-900/60 bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-purple-400 mb-2"><Sparkles size={14} /> Playbook visual</div>
                    <div className="text-[11px] text-gray-300">
                        <div>App activa: <span className="text-white">{visualPlaybook?.active_app || 'no detectada'}</span></div>
                        <div className="mt-1 text-gray-500">Spotify · Edge · Explorer · Settings · Discord · PowerShell</div>
                        {playbookResult && (
                            <div className="mt-2 border-t border-gray-800 pt-2">
                                <div>Resultado: <span className="text-white">{playbookResult.result || '—'}</span></div>
                                {playbookResult.playbook_app && <div>App: <span className="text-purple-300">{playbookResult.playbook_app}</span></div>}
                                {playbookResult.confidence !== undefined && <div>Confianza: <span className="text-white">{playbookResult.confidence}</span></div>}
                                {playbookResult.fallback_hint && <div className="text-yellow-300 mt-1">Fallback: {playbookResult.fallback_hint.reason || JSON.stringify(playbookResult.fallback_hint)}</div>}
                                {(playbookResult.playbook_hints || []).length > 0 && (
                                    <div className="mt-1">Estrategias: {playbookResult.playbook_hints.map((h, i) => <span key={i} className="inline-block mx-1 px-1 bg-purple-900/50 rounded text-purple-200">{h.strategy}</span>)}</div>
                                )}
                            </div>
                        )}
                        <div className="mt-2 flex flex-wrap gap-2">
                            <button onClick={() => { if (visualQuery.trim() && onRunPlaybook) onRunPlaybook(visualQuery.trim()); }} className="px-2 py-1 rounded border border-purple-800 text-purple-200 hover:bg-purple-950/40">Playbook</button>
                            <span className="text-gray-500 text-[10px]">Estrategia por app</span>
                        </div>
                    </div>
                </div>

                <div className="col-span-2 rounded border border-gray-800 bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-cyan-400 mb-2"><Activity size={14} /> Spotify / media</div>
                    <div className="flex flex-wrap gap-2 text-[11px] text-gray-300 mb-3">
                        <button onClick={() => onSpotifyAction?.('open')} className="px-2 py-1 rounded border border-cyan-800 text-cyan-200 hover:bg-cyan-950/30">Abrir</button>
                        <button onClick={() => onSpotifyAction?.('toggle')} className="px-2 py-1 rounded border border-cyan-800 text-cyan-200 hover:bg-cyan-950/30">Play/Pause</button>
                        <button onClick={() => onSpotifyAction?.('previous')} className="px-2 py-1 rounded border border-gray-700 text-gray-300 hover:bg-gray-900/40">Prev</button>
                        <button onClick={() => onSpotifyAction?.('next')} className="px-2 py-1 rounded border border-gray-700 text-gray-300 hover:bg-gray-900/40">Next</button>
                    </div>
                    <div className="flex gap-2 text-[11px]">
                        <input
                            value={spotifyQuery}
                            onChange={(e) => setSpotifyQuery(e.target.value)}
                            placeholder="Canción, artista o playlist"
                            className="flex-1 bg-black/40 border border-gray-800 rounded px-2 py-1 text-gray-200 outline-none"
                        />
                        <button
                            onClick={() => spotifyQuery.trim() && onSpotifyAction?.('search', spotifyQuery.trim())}
                            className="px-3 py-1 rounded border border-green-800 text-green-200 hover:bg-green-950/30"
                        >
                            Buscar y reproducir
                        </button>
                    </div>
                </div>

                <div className="col-span-2 rounded border border-gray-800 bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-cyan-400 mb-2"><ListTodo size={14} /> Task Queue</div>
                    <div className="flex gap-2 mb-3 text-[11px]">
                        {Object.entries(queue?.counts || {}).map(([key, value]) => (
                            <div key={key} className="px-2 py-1 rounded border border-cyan-900 text-cyan-200 bg-cyan-950/20">
                                {key}: {value}
                            </div>
                        ))}
                    </div>
                    <div className="space-y-2 max-h-56 overflow-auto">
                        {(queue?.recent || []).map((task) => (
                            <div key={task.id} className="rounded border border-gray-800 p-2 text-[11px] text-gray-300">
                                <div className="flex items-center justify-between gap-2">
                                    <div className="text-white font-semibold">{task.title}</div>
                                    <div className="text-cyan-300">{task.status}</div>
                                </div>
                                <div className="opacity-70">{task.kind} · {task.id}</div>
                                {task.error && <div className="text-red-300 mt-1">{task.error}</div>}
                                {task.result && <div className="text-green-300 mt-1">{task.result}</div>}
                            </div>
                        ))}
                        {(!queue?.recent || queue.recent.length === 0) && (
                            <div className="text-gray-500">No hay tareas todavía.</div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SystemWindow;

import React, { useEffect, useState } from 'react';
import { Terminal, Play, RefreshCw, X } from 'lucide-react';

const ScriptsWindow = ({ socket, onClose }) => {
    const [scripts, setScripts] = useState([]);
    const [output, setOutput] = useState('');
    const [selected, setSelected] = useState('');
    const [argsText, setArgsText] = useState('');

    const loadScripts = () => {
        socket.emit('list_scripts_ui');
    };

    useEffect(() => {
        loadScripts();

        const handleScripts = (data) => {
            setScripts(data?.scripts || []);
        };

        const handleRunResult = (data) => {
            setOutput(data?.result || 'Sin salida');
        };

        socket.on('scripts_registry', handleScripts);
        socket.on('script_run_result', handleRunResult);

        return () => {
            socket.off('scripts_registry', handleScripts);
            socket.off('script_run_result', handleRunResult);
        };
    }, [socket]);

    const runSelected = () => {
        if (!selected) return;
        const args = argsText.trim() ? argsText.split(' ').filter(Boolean) : [];
        socket.emit('run_script_ui', { name: selected, args });
    };

    return (
        <div className="w-full h-full relative group bg-[#0f1115] rounded-lg overflow-hidden flex flex-col border border-gray-800">
            <div className="h-8 bg-[#222] border-b border-gray-700 flex items-center justify-between px-2 shrink-0 cursor-grab active:cursor-grabbing">
                <div className="flex items-center gap-2 text-gray-300 text-xs font-mono">
                    <Terminal size={14} className="text-cyan-500" />
                    <span>CUSTOM_SCRIPTS</span>
                </div>
                <button onClick={onClose} className="hover:bg-red-500/20 text-gray-400 hover:text-red-400 p-1 rounded transition-colors">
                    <X size={14} />
                </button>
            </div>

            <div className="grid grid-cols-[260px_1fr] flex-1 min-h-0">
                <div className="border-r border-gray-800 p-3 overflow-y-auto">
                    <div className="flex items-center justify-between mb-3">
                        <div className="text-xs uppercase tracking-wider text-cyan-400">Scripts</div>
                        <button onClick={loadScripts} className="text-cyan-400 hover:text-cyan-200">
                            <RefreshCw size={14} />
                        </button>
                    </div>
                    <div className="space-y-2">
                        {scripts.map((script) => (
                            <button
                                key={script.safe_name || script.name}
                                onClick={() => setSelected(script.name)}
                                className={`w-full text-left rounded border p-2 text-xs transition ${selected === script.name ? 'border-cyan-400 bg-cyan-500/10 text-cyan-100' : 'border-gray-800 bg-black/30 text-gray-300 hover:border-cyan-700'}`}
                            >
                                <div className="font-semibold">{script.name}</div>
                                <div className="opacity-70 mt-1">{script.description || 'Sin descripción'}</div>
                                <div className="opacity-50 mt-1">{script.language || 'python'}</div>
                            </button>
                        ))}
                    </div>
                </div>

                <div className="p-3 flex flex-col min-h-0">
                    <div className="text-xs uppercase tracking-wider text-cyan-400 mb-2">Ejecución</div>
                    <div className="flex gap-2 mb-3">
                        <input
                            value={selected}
                            onChange={(e) => setSelected(e.target.value)}
                            placeholder="Nombre del script"
                            className="flex-1 bg-black/40 border border-cyan-800 rounded p-2 text-xs text-cyan-100 outline-none"
                        />
                        <button onClick={runSelected} className="px-3 rounded border border-green-500 text-green-400 hover:bg-green-500/10">
                            <Play size={14} />
                        </button>
                    </div>
                    <input
                        value={argsText}
                        onChange={(e) => setArgsText(e.target.value)}
                        placeholder="Argumentos separados por espacio"
                        className="mb-3 bg-black/40 border border-cyan-900 rounded p-2 text-xs text-cyan-100 outline-none"
                    />
                    <div className="text-xs uppercase tracking-wider text-cyan-400 mb-2">Salida</div>
                    <pre className="flex-1 min-h-0 overflow-auto bg-black/40 border border-gray-800 rounded p-3 text-[11px] text-green-400 whitespace-pre-wrap">{output || 'Sin ejecución aún.'}</pre>
                </div>
            </div>
        </div>
    );
};

export default ScriptsWindow;

import React, { useEffect, useState } from 'react';
import { Mail, FileText, Sheet, Presentation, Send, X, Download, Upload } from 'lucide-react';

const baseButton = 'px-3 py-2 rounded border text-xs transition';

const CommsWindow = ({ socket, onClose }) => {
    const [tab, setTab] = useState('word');
    const [title, setTitle] = useState('Documento ADA');
    const [body, setBody] = useState('');
    const [rowsText, setRowsText] = useState('Nombre,Rol\nJefe,Usuario');
    const [slidesText, setSlidesText] = useState('Portada|Resumen rápido\nEstado|ADA sigue mejorando');
    const [filename, setFilename] = useState('');
    const [emailTo, setEmailTo] = useState('');
    const [emailSubject, setEmailSubject] = useState('Mensaje de ADA');
    const [emailBody, setEmailBody] = useState('');
    const [downloadUrl, setDownloadUrl] = useState('');
    const [downloadName, setDownloadName] = useState('');
    const [uploadPath, setUploadPath] = useState('');
    const [uploadUrl, setUploadUrl] = useState('');
    const [uploadField, setUploadField] = useState('file');
    const [result, setResult] = useState('');

    useEffect(() => {
        const handleDocumentResult = (data) => setResult(data?.result || 'Operación completada.');
        const handleEmailResult = (data) => setResult(data?.result || 'Operación completada.');
        const handleTransferResult = (data) => setResult(data?.result || 'Operación completada.');
        socket.on('document_result', handleDocumentResult);
        socket.on('email_result', handleEmailResult);
        socket.on('transfer_result', handleTransferResult);
        return () => {
            socket.off('document_result', handleDocumentResult);
            socket.off('email_result', handleEmailResult);
            socket.off('transfer_result', handleTransferResult);
        };
    }, [socket]);

    const createDocument = () => {
        if (tab === 'word') {
            socket.emit('create_document_ui', { kind: 'word', title, body, filename });
        } else if (tab === 'excel') {
            const rows = rowsText.split('\n').filter(Boolean).map(line => line.split(',').map(x => x.trim()));
            socket.emit('create_document_ui', { kind: 'excel', title, rows, filename, sheet_name: 'Hoja1' });
        } else if (tab === 'ppt') {
            const slides = slidesText.split('\n').filter(Boolean).map(line => {
                const [slideTitle, ...rest] = line.split('|');
                return { title: (slideTitle || 'Diapositiva').trim(), bullets: rest.length ? rest.map(x => x.trim()).filter(Boolean) : ['Contenido generado por ADA'] };
            });
            socket.emit('create_document_ui', { kind: 'powerpoint', title, slides, filename });
        }
    };

    const sendEmail = () => {
        socket.emit('send_email_ui', { to: emailTo, subject: emailSubject, body: emailBody });
    };

    const downloadFile = () => {
        socket.emit('download_file_ui', { url: downloadUrl, filename: downloadName });
    };

    const uploadFile = () => {
        socket.emit('upload_file_ui', { file_path: uploadPath, target_url: uploadUrl, field_name: uploadField || 'file' });
    };

    return (
        <div className="w-full h-full relative bg-[#0f1115] rounded-lg overflow-hidden flex flex-col border border-gray-800">
            <div className="h-8 bg-[#222] border-b border-gray-700 flex items-center justify-between px-2 shrink-0 cursor-grab active:cursor-grabbing">
                <div className="flex items-center gap-2 text-gray-300 text-xs font-mono">
                    <Mail size={14} className="text-cyan-500" />
                    <span>DOCS_MAIL_TRANSFER</span>
                </div>
                <button onClick={onClose} className="hover:bg-red-500/20 text-gray-400 hover:text-red-400 p-1 rounded transition-colors">
                    <X size={14} />
                </button>
            </div>

            <div className="p-3 flex gap-2 border-b border-gray-800 text-xs flex-wrap">
                <button onClick={() => setTab('word')} className={`${baseButton} ${tab === 'word' ? 'border-cyan-400 text-cyan-300 bg-cyan-500/10' : 'border-gray-800 text-gray-300'}`}><FileText size={14} /></button>
                <button onClick={() => setTab('excel')} className={`${baseButton} ${tab === 'excel' ? 'border-green-400 text-green-300 bg-green-500/10' : 'border-gray-800 text-gray-300'}`}><Sheet size={14} /></button>
                <button onClick={() => setTab('ppt')} className={`${baseButton} ${tab === 'ppt' ? 'border-orange-400 text-orange-300 bg-orange-500/10' : 'border-gray-800 text-gray-300'}`}><Presentation size={14} /></button>
                <button onClick={() => setTab('email')} className={`${baseButton} ${tab === 'email' ? 'border-fuchsia-400 text-fuchsia-300 bg-fuchsia-500/10' : 'border-gray-800 text-gray-300'}`}><Mail size={14} /></button>
                <button onClick={() => setTab('download')} className={`${baseButton} ${tab === 'download' ? 'border-sky-400 text-sky-300 bg-sky-500/10' : 'border-gray-800 text-gray-300'}`}><Download size={14} /></button>
                <button onClick={() => setTab('upload')} className={`${baseButton} ${tab === 'upload' ? 'border-emerald-400 text-emerald-300 bg-emerald-500/10' : 'border-gray-800 text-gray-300'}`}><Upload size={14} /></button>
            </div>

            <div className="p-3 flex-1 overflow-auto text-xs text-gray-200 space-y-3">
                {['word', 'excel', 'ppt'].includes(tab) && (
                    <>
                        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Título" className="w-full bg-black/40 border border-cyan-900 rounded p-2" />
                        <input value={filename} onChange={(e) => setFilename(e.target.value)} placeholder="Nombre de archivo opcional" className="w-full bg-black/40 border border-cyan-900 rounded p-2" />
                        {tab === 'word' && <textarea value={body} onChange={(e) => setBody(e.target.value)} placeholder="Contenido del documento" className="w-full min-h-40 bg-black/40 border border-cyan-900 rounded p-2" />}
                        {tab === 'excel' && <textarea value={rowsText} onChange={(e) => setRowsText(e.target.value)} placeholder="Fila1Col1,Fila1Col2" className="w-full min-h-40 bg-black/40 border border-cyan-900 rounded p-2" />}
                        {tab === 'ppt' && <textarea value={slidesText} onChange={(e) => setSlidesText(e.target.value)} placeholder="Título|bullet1|bullet2" className="w-full min-h-40 bg-black/40 border border-cyan-900 rounded p-2" />}
                        <button onClick={createDocument} className="px-3 py-2 rounded border border-cyan-400 text-cyan-300 hover:bg-cyan-500/10">Crear archivo</button>
                    </>
                )}

                {tab === 'email' && (
                    <>
                        <input value={emailTo} onChange={(e) => setEmailTo(e.target.value)} placeholder="Destinatario" className="w-full bg-black/40 border border-cyan-900 rounded p-2" />
                        <input value={emailSubject} onChange={(e) => setEmailSubject(e.target.value)} placeholder="Asunto" className="w-full bg-black/40 border border-cyan-900 rounded p-2" />
                        <textarea value={emailBody} onChange={(e) => setEmailBody(e.target.value)} placeholder="Mensaje" className="w-full min-h-40 bg-black/40 border border-cyan-900 rounded p-2" />
                        <button onClick={sendEmail} className="px-3 py-2 rounded border border-fuchsia-400 text-fuchsia-300 hover:bg-fuchsia-500/10 inline-flex items-center gap-2"><Send size={14} />Enviar correo</button>
                    </>
                )}

                {tab === 'download' && (
                    <>
                        <input value={downloadUrl} onChange={(e) => setDownloadUrl(e.target.value)} placeholder="https://..." className="w-full bg-black/40 border border-cyan-900 rounded p-2" />
                        <input value={downloadName} onChange={(e) => setDownloadName(e.target.value)} placeholder="Nombre local opcional" className="w-full bg-black/40 border border-cyan-900 rounded p-2" />
                        <button onClick={downloadFile} className="px-3 py-2 rounded border border-sky-400 text-sky-300 hover:bg-sky-500/10 inline-flex items-center gap-2"><Download size={14} />Descargar</button>
                    </>
                )}

                {tab === 'upload' && (
                    <>
                        <input value={uploadPath} onChange={(e) => setUploadPath(e.target.value)} placeholder="Ruta del archivo local" className="w-full bg-black/40 border border-cyan-900 rounded p-2" />
                        <input value={uploadUrl} onChange={(e) => setUploadUrl(e.target.value)} placeholder="https://endpoint-de-subida" className="w-full bg-black/40 border border-cyan-900 rounded p-2" />
                        <input value={uploadField} onChange={(e) => setUploadField(e.target.value)} placeholder="Campo multipart, por ejemplo file" className="w-full bg-black/40 border border-cyan-900 rounded p-2" />
                        <button onClick={uploadFile} className="px-3 py-2 rounded border border-emerald-400 text-emerald-300 hover:bg-emerald-500/10 inline-flex items-center gap-2"><Upload size={14} />Subir</button>
                    </>
                )}

                <div className="border border-gray-800 bg-black/30 rounded p-3 text-[11px] text-green-300 whitespace-pre-wrap min-h-20">
                    {result || 'Sin acciones todavía.'}
                </div>
            </div>
        </div>
    );
};

export default CommsWindow;

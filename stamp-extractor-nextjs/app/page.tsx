'use client';

import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, CheckCircle, Copy, Loader2, ChevronLeft, ChevronRight } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

interface StampResult {
  page: number;
  symbol_type: string;
  bounding_box: [number, number, number, number];
  engineer_name: string | null;
  license_number: string | null;
  units: string;
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [pageCount, setPageCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const [pageImage, setPageImage] = useState<string | null>(null);
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<StampResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setResult(null);
      setError(null);

      const formData = new FormData();
      formData.append('file', selectedFile);

      try {
        setIsProcessing(true);
        const res = await fetch(`${API_BASE}/get-info`, {
          method: 'POST',
          body: formData,
        });

        if (!res.ok) throw new Error('Failed to load PDF info');

        const data = await res.json();
        setPageCount(data.page_count);
        setCurrentPage(0);
        await loadPageImage(selectedFile, 0);
      } catch (err) {
        console.error(err);
        setError('Failed to load PDF. Make sure the backend is running.');
      } finally {
        setIsProcessing(false);
      }
    }
  };

  const loadPageImage = async (selectedFile: File, pageNum: number) => {
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('page', pageNum.toString());

    try {
      setIsProcessing(true);
      const res = await fetch(`${API_BASE}/get-page-image`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) throw new Error('Failed to load page image');

      const data = await res.json();
      setPageImage(data.image);
      setImageSize({ width: data.width, height: data.height });
    } catch (err) {
      console.error(err);
      setError('Failed to load page image');
    } finally {
      setIsProcessing(false);
    }
  };

  const handlePageChange = (delta: number) => {
    const newPage = Math.max(0, Math.min(pageCount - 1, currentPage + delta));
    if (newPage !== currentPage && file) {
      setCurrentPage(newPage);
      setResult(null);
      loadPageImage(file, newPage);
    }
  };

  const handleExtractStamp = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('page', currentPage.toString());

    try {
      setIsProcessing(true);
      setError(null);
      const res = await fetch(`${API_BASE}/extract-stamp`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) throw new Error('Extraction failed');

      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      setError('Extraction failed. Make sure the backend is running.');
    } finally {
      setIsProcessing(false);
    }
  };

  const copyToClipboard = () => {
    if (result) {
      navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === 'application/pdf') {
        // Manually trigger file selection
        const event = { target: { files: [droppedFile] } } as any;
        handleFileChange(event);
      } else {
        setError('Please upload a PDF file');
      }
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100 font-sans text-gray-800 overflow-hidden">

      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-1.5 rounded-lg">
            <FileText className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-xl font-bold text-gray-900">
            Stamp Extractor <span className="text-blue-600 font-medium">Pro</span>
          </h1>
        </div>
        <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded border border-blue-400">
          Next.js + FastAPI
        </span>
      </header>

      {/* Main Workspace */}
      <main className="flex flex-1 overflow-hidden">

        {/* Left Panel: Controls & Results */}
        <aside className="w-1/3 bg-white border-r border-gray-200 flex flex-col h-full overflow-y-auto">

          {/* Upload Section */}
          <div className="p-6 border-b border-gray-100">
            <h2 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-3">1. Input</h2>

            <div
              onClick={() => fileInputRef.current?.click()}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer ${
                file ? 'border-green-400 bg-green-50' : 'border-gray-300 hover:bg-gray-50'
              }`}
            >
              <UploadCloud className={`mx-auto h-10 w-10 mb-2 ${file ? 'text-green-500' : 'text-gray-400'}`} />
              {file ? (
                <p className="text-sm text-green-700 font-medium">{file.name} loaded</p>
              ) : (
                <>
                  <p className="text-sm text-gray-600">Drag & drop your PDF drawing here</p>
                  <p className="text-xs text-gray-400 mt-1">or click to browse</p>
                </>
              )}
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                className="hidden"
                accept=".pdf"
              />
            </div>

            {error && (
              <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            {file && (
              <div className="mt-4 flex gap-4 items-end">
                <div className="flex-1">
                  <label className="block text-xs font-medium text-gray-700 mb-1">Select Page</label>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handlePageChange(-1)}
                      disabled={currentPage === 0 || isProcessing}
                      className="p-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </button>
                    <div className="flex-1 text-center text-sm font-medium">
                      Page {currentPage + 1} of {pageCount}
                    </div>
                    <button
                      onClick={() => handlePageChange(1)}
                      disabled={currentPage === pageCount - 1 || isProcessing}
                      className="p-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <button
                  onClick={handleExtractStamp}
                  disabled={!file || isProcessing}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md text-sm transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    'Extract Stamp'
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Results Section */}
          {result && (
            <div className="p-6 flex-col flex-1 animate-in fade-in duration-500">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <h2 className="text-sm font-bold text-gray-500 uppercase tracking-wider">2. Extraction Results</h2>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 shadow-sm">
                  <p className="text-xs text-gray-500 font-medium mb-1">Engineer Name</p>
                  <p className="text-sm font-bold text-gray-900">
                    {result.engineer_name || 'NOT DETECTED'}
                  </p>
                </div>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 shadow-sm">
                  <p className="text-xs text-gray-500 font-medium mb-1">License Number</p>
                  <p className="text-sm font-bold text-gray-900">
                    {result.license_number || 'NOT DETECTED'}
                  </p>
                </div>
              </div>

              <h2 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-2">JSON Output</h2>
              <div className="bg-gray-900 rounded-lg shadow-inner flex-1 flex flex-col max-h-[300px]">
                <div className="flex justify-between items-center px-4 py-2 border-b border-gray-700">
                  <span className="text-xs text-gray-400 font-mono">output.json</span>
                  <button
                    onClick={copyToClipboard}
                    className="text-xs text-gray-400 hover:text-white transition-colors flex items-center gap-1"
                  >
                    <Copy className="w-3 h-3" /> Copy
                  </button>
                </div>
                <pre className="p-4 text-xs text-green-400 font-mono overflow-auto custom-scrollbar">
                  <code>{JSON.stringify(result, null, 2)}</code>
                </pre>
              </div>
            </div>
          )}
        </aside>

        {/* Right Panel: Document Preview */}
        <section className="w-2/3 bg-gray-200 p-8 flex items-center justify-center overflow-auto relative">

          {!file ? (
            <div className="text-center text-gray-400">
              <FileText className="mx-auto h-16 w-16 mb-4 opacity-50" />
              <p>Upload a drawing to view preview</p>
            </div>
          ) : isProcessing && !pageImage ? (
            <div className="text-center text-gray-400">
              <Loader2 className="mx-auto h-16 w-16 mb-4 animate-spin" />
              <p>Loading page...</p>
            </div>
          ) : pageImage ? (
            <div className="relative inline-block">
              <img
                src={pageImage}
                alt={`PDF Page ${currentPage + 1}`}
                className="max-w-full max-h-full shadow-2xl border border-gray-300 block"
                style={{ maxHeight: 'calc(100vh - 200px)' }}
              />

              {/* Bounding Box Overlay */}
              {result && result.bounding_box && (
                <div
                  className="absolute border-4 border-red-500 bg-red-500/20 transition-all duration-500"
                  style={{
                    left: `${(result.bounding_box[0] / imageSize.width) * 100}%`,
                    top: `${(result.bounding_box[1] / imageSize.height) * 100}%`,
                    width: `${(result.bounding_box[2] / imageSize.width) * 100}%`,
                    height: `${(result.bounding_box[3] / imageSize.height) * 100}%`,
                    pointerEvents: 'none',
                  }}
                >
                  <div className="absolute -top-6 left-0 bg-red-500 text-white text-xs px-2 py-1 font-bold rounded shadow-lg whitespace-nowrap">
                    APPROVAL STAMP DETECTED
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </section>
      </main>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar { width: 8px; height: 8px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: #1f2937; border-radius: 8px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #4b5563; border-radius: 8px; }
        @keyframes in {
          from {
            opacity: 0;
            transform: scale(0.95);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }
        .animate-in {
          animation: in 0.5s ease-out;
        }
        .fade-in {
          animation: in 0.5s ease-out;
        }
        .zoom-in-95 {
          animation: in 0.5s ease-out;
        }
      `}</style>
    </div>
  );
}

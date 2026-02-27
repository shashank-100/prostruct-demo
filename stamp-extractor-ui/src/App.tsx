import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Upload, FileText, Crosshair, ChevronRight, ChevronLeft, Loader2, Database } from 'lucide-react';
import './App.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

interface StampData {
  page: number;
  symbol_type: string;
  bounding_box: [number, number, number, number];
  engineer_name: string | null;
  license_number: string | null;
  units: string;
}

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [pageCount, setPageCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const [pageImage, setPageImage] = useState<string | null>(null);
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });
  const [stampData, setStampData] = useState<StampData | null>(null);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setStampData(null);
      
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      try {
        setLoading(true);
        const res = await axios.post(`${API_BASE}/get-info`, formData);
        setPageCount(res.data.page_count);
        setCurrentPage(0);
        await loadPageImage(selectedFile, 0);
      } catch (err) {
        console.error(err);
        alert('Failed to load PDF info');
      } finally {
        setLoading(false);
      }
    }
  };

  const loadPageImage = async (selectedFile: File, pageNum: number) => {
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('page', pageNum.toString());
    
    try {
      setLoading(true);
      const res = await axios.post(`${API_BASE}/get-page-image`, formData);
      setPageImage(res.data.image);
      setImageSize({ width: res.data.width, height: res.data.height });
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const extractStamp = async () => {
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('page', currentPage.toString());
    
    try {
      setLoading(true);
      const res = await axios.post(`${API_BASE}/extract-stamp`, formData);
      setStampData(res.data);
    } catch (err) {
      console.error(err);
      alert('Extraction failed');
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (delta: number) => {
    const newPage = Math.max(0, Math.min(pageCount - 1, currentPage + delta));
    if (newPage !== currentPage && file) {
      setCurrentPage(newPage);
      setStampData(null);
      loadPageImage(file, newPage);
    }
  };

  return (
    <div className="app-container">
      <main className="preview-section">
        <div className="image-canvas-container">
          {loading && (
            <div className="loading-overlay">
              <Loader2 className="animate-spin" size={48} color="#f97316" />
            </div>
          )}
          
          {pageImage ? (
            <div className="image-wrapper">
              <img 
                src={pageImage} 
                alt="PDF Page" 
                style={{ maxWidth: '100%', display: 'block' }}
              />
              {stampData && (
                <div 
                  className="bounding-box-overlay"
                  style={{
                    position: 'absolute',
                    border: '3px solid #f97316',
                    backgroundColor: 'rgba(249, 115, 22, 0.15)',
                    boxShadow: '0 0 0 9999px rgba(0, 0, 0, 0.3)',
                    left: `${(stampData.bounding_box[0] / imageSize.width) * 100}%`,
                    top: `${(stampData.bounding_box[1] / imageSize.height) * 100}%`,
                    width: `${(stampData.bounding_box[2] / imageSize.width) * 100}%`,
                    height: `${(stampData.bounding_box[3] / imageSize.height) * 100}%`,
                    zIndex: 5
                  }}
                >
                  <div style={{
                    position: 'absolute',
                    top: -24,
                    left: -3,
                    backgroundColor: '#f97316',
                    color: 'white',
                    padding: '2px 8px',
                    fontSize: '10px',
                    fontWeight: 'bold',
                    textTransform: 'uppercase',
                    whiteSpace: 'nowrap'
                  }}>
                    Approval Stamp Detected
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="upload-placeholder" onClick={() => fileInputRef.current?.click()}>
              <Upload size={48} color="#2d3135" />
              <p>Upload a structural drawing to begin</p>
            </div>
          )}
        </div>
      </main>

      <aside className="sidebar">
        <div className="header">
          <h1>PROSTRUCT / <span style={{color: 'white'}}>STAMP-X</span></h1>
          <p>Structural Engineering Stamp Extractor</p>
        </div>

        <div className="controls">
          <div className="control-group">
            <label>Source Document</label>
            <div className="upload-zone" onClick={() => fileInputRef.current?.click()}>
              <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handleFileChange} 
                accept=".pdf" 
                style={{ display: 'none' }}
              />
              {file ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <FileText size={16} color="#f97316" />
                  <span style={{ fontSize: '0.875rem', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {file.name}
                  </span>
                </div>
              ) : (
                <span style={{ fontSize: '0.875rem', color: '#64748b' }}>Select PDF Drawing</span>
              )}
            </div>
          </div>

          {file && (
            <>
              <div className="control-group">
                <label>Page Selection</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <button onClick={() => handlePageChange(-1)} disabled={currentPage === 0}>
                    <ChevronLeft size={16} />
                  </button>
                  <div style={{ flex: 1, textAlign: 'center', fontSize: '0.875rem' }}>
                    PAGE {currentPage + 1} OF {pageCount}
                  </div>
                  <button onClick={() => handlePageChange(1)} disabled={currentPage === pageCount - 1}>
                    <ChevronRight size={16} />
                  </button>
                </div>
              </div>

              <button className="primary" onClick={extractStamp} disabled={loading}>
                {loading ? 'Processing...' : 'Run Extraction'}
              </button>
            </>
          )}
        </div>

        {stampData && (
          <div className="results-section">
            <div className="control-group" style={{ marginBottom: '1rem' }}>
              <label>Extracted Fields</label>
              <div style={{ background: '#0f1113', padding: '1rem', borderRadius: '4px', border: '1px solid var(--border-color)' }}>
                <div style={{ marginBottom: '0.75rem' }}>
                  <div style={{ fontSize: '0.625rem', color: '#64748b', textTransform: 'uppercase' }}>Engineer Name</div>
                  <div style={{ fontWeight: '600', color: 'white' }}>{stampData.engineer_name || 'NOT DETECTED'}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.625rem', color: '#64748b', textTransform: 'uppercase' }}>License Number</div>
                  <div style={{ fontWeight: '600', color: 'white' }}>{stampData.license_number || 'NOT DETECTED'}</div>
                </div>
              </div>
            </div>

            <div className="control-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Database size={12} />
                JSON Output
              </label>
              <pre className="json-output">
                {JSON.stringify(stampData, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}

export default App;

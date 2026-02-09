import React, { useState, useEffect, useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.js';

function PDFViewer({ paperNo, apiBase }) {
  const [numPages, setNumPages] = useState(null);
  const [containerWidth, setContainerWidth] = useState(null);
  const containerRef = useRef(null);

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
  };

  useEffect(() => {
    const observer = new ResizeObserver((entries) => {
      if (entries[0]) {
        // Subtract padding/scrollbar space to avoid horizontal scrollbar
        setContainerWidth(entries[0].contentRect.width - 20);
      }
    });

    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <div className="pdf-viewer scrollable-pdf" ref={containerRef}>
      <Document
        file={`${apiBase}/api/pdf/${paperNo}`}
        onLoadSuccess={onDocumentLoadSuccess}
        onLoadError={(error) => console.error('Error loading PDF:', error)}
        loading={<div className="pdf-loading">Loading PDF...</div>}
        error={<div className="pdf-error">Failed to load PDF</div>}
      >
        {numPages && Array.from(new Array(numPages), (el, index) => (
          <Page
            key={`page_${index + 1}`}
            pageNumber={index + 1}
            width={containerWidth || undefined}
            renderTextLayer={true}
            renderAnnotationLayer={true}
            className="pdf-page"
            loading=""
          />
        ))}
      </Document>
    </div>
  );
}

export default PDFViewer;

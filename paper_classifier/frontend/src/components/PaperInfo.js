import React from 'react';

function PaperInfo({ paper }) {
  return (
    <div className="paper-info">
      <div className="paper-header">
        <h2>Paper #{paper.no}</h2>
        <p className="paper-date">
          <a href={paper.arxiv_url} target="_blank" rel="noopener noreferrer">
            {paper.arxiv_url}
          </a>
        </p>
      </div>
      
      <h3 className="paper-title">{paper.title}</h3>
      
      <div className="paper-authors">
        <strong>Authors:</strong> {paper.authors}
      </div>

      <div className="abstract-section">
        <h4>Abstract (English)</h4>
        <div className="abstract-content scrollable">
          {paper.abstract}
        </div>
      </div>

      {paper.abstract_kor && (
        <div className="abstract-section">
          <h4>초록 (한국어)</h4>
          <div className="abstract-content scrollable">
            {paper.abstract_kor}
          </div>
        </div>
      )}
    </div>
  );
}

export default PaperInfo;

import React from 'react';
import { ScriptError } from '../../types';

// Helper function to render JSON data in a readable format
const renderJsonData = (data: any, depth = 0): React.ReactNode => {
  if (data === null || data === undefined) return null;
  
  if (typeof data === 'string') {
    // Check if it's a JSON string
    try {
      const parsed = JSON.parse(data);
      return renderJsonData(parsed, depth);
    } catch (e) {
      return data;
    }
  }
  
  if (Array.isArray(data)) {
    return (
      <ul style={{ margin: 0, paddingLeft: '20px' }}>
        {data.map((item, i) => (
          <li key={i} style={{ marginBottom: '4px' }}>{renderJsonData(item, depth + 1)}</li>
        ))}
      </ul>
    );
  }
  
  if (typeof data === 'object') {
    return (
      <div style={{ marginLeft: depth > 0 ? '10px' : '0' }}>
        {Object.entries(data).map(([key, value]) => (
          <div key={key} style={{ marginBottom: '4px' }}>
            <strong>{key}:</strong> {renderJsonData(value, depth + 1)}
          </div>
        ))}
      </div>
    );
  }
  
  return String(data);
};

interface OutputPanelProps {
  output: string;
  onClear: () => void;
  isRunning: boolean;
  scriptError: ScriptError | null;
}

export const OutputPanel: React.FC<OutputPanelProps> = ({ output, onClear, isRunning, scriptError }) => {
  return (
    <div className="dashboard-card">
      <div className="dashboard-card__header">
        <h3 className="dashboard-card__title">
          {scriptError ? (
            <span>{scriptError.error_type || 'Error Details'}</span>
          ) : 'Output'}
        </h3>
        {(output || scriptError) && (
          <button 
            className="clear-output"
            onClick={onClear}
            disabled={isRunning}
            aria-label={scriptError ? 'Clear error' : 'Clear output'}
          >
            Clear {scriptError ? 'Error' : 'Output'}
          </button>
        )}
      </div>
      <div className="output-content">
        {scriptError ? (
          <div className="error-details">
            <div className="error-message">
              <div className="error-summary">
                <p className="error-description">{scriptError.error}</p>
                
                <div className="error-metadata">
                  {scriptError.error_type && (
                    <div className="metadata-item">
                      <span className="metadata-label">Type:</span>
                      <span className="metadata-value error-type">
                        {scriptError.error_type}
                      </span>
                    </div>
                  )}
                  
                  {scriptError.returncode !== undefined && (
                    <div className="metadata-item">
                      <span className="metadata-label">Exit Code:</span>
                      <span className="metadata-value">{scriptError.returncode}</span>
                    </div>
                  )}
                  
                  {scriptError.timestamp && (
                    <div className="metadata-item">
                      <span className="metadata-label">Time:</span>
                      <span className="metadata-value">
                        {new Date(scriptError.timestamp).toLocaleString()}
                      </span>
                    </div>
                  )}
                </div>
              </div>
              
              {scriptError.suggestions && scriptError.suggestions.length > 0 && (
                <div className="error-section">
                  <h5 className="section-title">Suggestions</h5>
                  <ul className="suggestions">
                    {scriptError.suggestions.map((suggestion, i) => (
                      <li key={i} className="suggestion-item">
                        <span className="bullet">•</span>
                        {suggestion}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {scriptError.possible_causes && scriptError.possible_causes.length > 0 && (
                <div className="error-section">
                  <h5 className="section-title">Possible Causes</h5>
                  <ul className="causes">
                    {scriptError.possible_causes.map((cause, i) => (
                      <li key={i} className="cause-item">{cause}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {scriptError.stderr && (
                <div className="error-section">
                  <h5 className="section-title">Error Output</h5>
                  <pre className="error-output">
                    {scriptError.stderr}
                  </pre>
                </div>
              )}
              
              {scriptError.traceback && (
                <div className="error-section">
                  <h5 className="section-title">Stack Trace</h5>
                  <pre className="traceback">
                    {scriptError.traceback}
                  </pre>
                </div>
              )}
              
              {scriptError.details && Object.keys(scriptError.details).length > 0 && (
                <div className="error-section">
                  <h5 className="section-title">Additional Details</h5>
                  <div className="details-content">
                    {renderJsonData(scriptError.details)}
                  </div>
                </div>
              )}
              
              {scriptError.page_history && scriptError.page_history.length > 0 && (
                <div className="error-section">
                  <h5 className="section-title">Page History
                  </h5>
                  <div className="page-history">
                    {scriptError.page_history.map((page, i) => (
                      <div key={i} className="page-history-item">
                        <div className="page-url">{page.url}</div>
                        {page.title && <div className="page-title">{page.title}</div>}
                        {page.timestamp && (
                          <div className="page-timestamp">
                            {new Date(page.timestamp).toLocaleString()}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="script-output">
            {output ? (
              <pre>{output}</pre>
            ) : (
              <p className="empty-state">Script output will appear here</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

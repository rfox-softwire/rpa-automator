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
          {scriptError ? 'Error Details' : 'Output'}
        </h3>
        {(output || scriptError) && (
          <button 
            className="clear-output"
            onClick={onClear}
            disabled={isRunning}
          >
            Clear {scriptError ? 'Error' : 'Output'}
          </button>
        )}
      </div>
      <div className="output-content">
        {scriptError && (
          <div className="error-details">
            <div className="error-message">
              <div className="error-summary">
                <p><strong>Error:</strong> {scriptError.error}</p>
                {scriptError.error_type && <p><strong>Type:</strong> {scriptError.error_type}</p>}
                {scriptError.returncode !== undefined && <p><strong>Exit Code:</strong> {scriptError.returncode}</p>}
              </div>
              
              {scriptError.suggestions && scriptError.suggestions.length > 0 && (
                <div className="error-section">
                  <h5>Suggestions:</h5>
                  <ul className="suggestions">
                    {scriptError.suggestions.map((suggestion, i) => (
                      <li key={i} className="suggestion-item">{suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {scriptError.details && (
                <div className="error-section">
                  <h5>Additional Details:</h5>
                  <div className="details-content">
                    {renderJsonData(scriptError.details)}
                  </div>
                </div>
              )}
              
              {scriptError.stderr && (
                <div className="error-section">
                  <h5>Error Output:</h5>
                  <pre className="error-output">{scriptError.stderr}</pre>
                </div>
              )}
              
              {scriptError.traceback && (
                <div className="error-section">
                  <h5>Traceback:</h5>
                  <pre className="traceback">{scriptError.traceback}</pre>
                </div>
              )}
              
              {scriptError.script_path && (
                <div className="error-section">
                  <h5>Script Path:</h5>
                  <pre className="script-path">{scriptError.script_path}</pre>
                </div>
              )}
              
              {scriptError.page_history && scriptError.page_history.length > 0 && (
                <div className="error-section">
                  <h5>Page History:</h5>
                  <div className="page-history">
                    {scriptError.page_history.map((page, i) => (
                      <div key={i} className="page-history-item">
                        <div className="page-history-url">
                          <strong>URL:</strong> {page.url}
                        </div>
                        {page.title && (
                          <div className="page-history-title">
                            <strong>Title:</strong> {page.title}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        {output && (
          <pre>{output}</pre>
        )}
        {!output && (
          <p className="empty-state">Script output will appear here</p>
        )}
      </div>
    </div>
  );
};

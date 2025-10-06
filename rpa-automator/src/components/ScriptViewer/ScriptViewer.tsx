import React from 'react';
import { LlmResponse, ScriptError } from '../../types';

interface ScriptViewerProps {
  llmResponse: LlmResponse | null;
  scriptError: ScriptError | null;
}

export const ScriptViewer: React.FC<ScriptViewerProps> = ({ llmResponse, scriptError }) => {
  return (
    <div className="dashboard-card">
      <h3 className="dashboard-card__title">
        {llmResponse?.isRepaired ? 'Repaired Script' : 'LLM Response'}
      </h3>
      <div className="llm-response">
        {scriptError && (
          <div className="error-details">
            <h4>Error Details:</h4>
            <div className="error-message">
              <p><strong>Error:</strong> {scriptError.error}</p>
              {scriptError.error_type && <p><strong>Type:</strong> {scriptError.error_type}</p>}
              {scriptError.returncode !== undefined && <p><strong>Exit Code:</strong> {scriptError.returncode}</p>}
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
            </div>
          </div>
        )}
        {llmResponse && (
          <div className="script-content">
            <div className="script-info">
              <p><strong>Script ID:</strong> {llmResponse.scriptId}</p>
              <p><strong>Path:</strong> {llmResponse.scriptPath}</p>
            </div>
            {llmResponse.scriptContent && (
              <pre className="code-block">
                <code className="language-python">
                  {llmResponse.scriptContent}
                </code>
              </pre>
            )}
          </div>
        )}
        {!llmResponse && !scriptError && (
          <p className="empty-state">Submit a prompt to generate a script</p>
        )}
      </div>
    </div>
  );
};

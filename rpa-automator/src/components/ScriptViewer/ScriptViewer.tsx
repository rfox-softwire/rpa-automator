import React from 'react';
import { LlmResponse, ScriptError } from '../../types';

interface ScriptViewerProps {
  llmResponse: LlmResponse | null;
  scriptError: ScriptError | null;
}

export const ScriptViewer: React.FC<ScriptViewerProps> = ({ llmResponse, scriptError }) => {
  // Get the script content from either llmResponse or scriptError
  const scriptContent = llmResponse?.scriptContent || scriptError?.script_content;
  const scriptId = llmResponse?.scriptId || scriptError?.script_id;
  const scriptPath = llmResponse?.scriptPath || scriptError?.script_path;

  return (
    <div className="dashboard-card">
      <h3 className="dashboard-card__title">
        {llmResponse?.isRepaired ? 'Repaired Script' : 'LLM Response'}
      </h3>
      <div className="llm-response">
        {scriptContent && (
          <div className="script-content">
            <div className="script-info">
              {scriptId && <p><strong>Script ID:</strong> {scriptId}</p>}
              {scriptPath && <p><strong>Path:</strong> {scriptPath}</p>}
            </div>
            <pre className="code-block">
              <code className="language-python">
                {scriptContent}
              </code>
            </pre>
          </div>
        )}
        {!scriptContent && (
          <p className="empty-state">Submit a prompt to generate a script</p>
        )}
      </div>
    </div>
  );
};

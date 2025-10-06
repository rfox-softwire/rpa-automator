import React from 'react';

interface OutputPanelProps {
  output: string;
  onClear: () => void;
  isRunning: boolean;
}

export const OutputPanel: React.FC<OutputPanelProps> = ({ output, onClear, isRunning }) => {
  return (
    <div className="dashboard-card">
      <div className="dashboard-card__header">
        <h3 className="dashboard-card__title">Output</h3>
        {output && (
          <button 
            className="clear-output"
            onClick={onClear}
            disabled={isRunning}
          >
            Clear Output
          </button>
        )}
      </div>
      <div className="output-content">
        {output ? (
          <pre>{output}</pre>
        ) : (
          <p className="empty-state">Script output will appear here</p>
        )}
      </div>
    </div>
  );
};

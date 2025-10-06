import React from 'react';

interface ActionFooterProps {
  isSubmitting: boolean;
  hasError: boolean;
  isRunning: boolean;
  isRepairing: boolean;
  hasScript: boolean;
  onSubmit: (e: React.FormEvent) => void;
  onRun: () => void;
  onRepair: () => void;
}

export const ActionFooter: React.FC<ActionFooterProps> = ({
  isSubmitting,
  hasError,
  isRunning,
  isRepairing,
  hasScript,
  onSubmit,
  onRun,
  onRepair,
}) => {
  return (
    <footer className="action-footer">
      <div className="button-group">
        <button 
          type="submit" 
          form="instruction-form"
          className={`instruction-form__submit ${isSubmitting ? 'is-loading' : ''}`}
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <>
              <span className="spinner"></span>
              <span>{hasError ? 'Repairing...' : 'Processing...'}</span>
            </>
          ) : (hasError ? 'Regenerate Script' : 'Generate Script')}
        </button>
        
        {hasScript && (
          <button 
            type="button" 
            className="instruction-form__run"
            onClick={onRun}
            disabled={isRunning || isSubmitting}
          >
            {isRunning ? 'Running...' : 'Run Script'}
          </button>
        )}
        
        {hasError && (
          <button 
            type="button" 
            className="instruction-form__repair"
            onClick={onRepair}
            disabled={isRepairing || isSubmitting}
          >
            {isRepairing ? 'Repairing...' : 'Auto-Repair'}
          </button>
        )}
      </div>
    </footer>
  );
};

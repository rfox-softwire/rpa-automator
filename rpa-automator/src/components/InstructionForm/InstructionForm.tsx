import React, { useRef } from 'react';
import { StatusMessage } from '../../types';

interface InstructionFormProps {
  formData: { content: string };
  isSubmitting: boolean;
  hasError: boolean;
  status: StatusMessage | null;
  onInputChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onSubmit: (e: React.FormEvent) => void;
  children?: React.ReactNode;
}

export const InstructionForm: React.FC<InstructionFormProps> = ({
  formData,
  isSubmitting,
  hasError,
  status,
  onInputChange,
  onSubmit,
  children
}) => {
  const instructionInputRef = useRef<HTMLTextAreaElement>(null);

  return (
    <form id="instruction-form" onSubmit={onSubmit} className="instruction-form">
      <h3 className="instruction-form__title">Enter Your Instructions</h3>
      <textarea 
        ref={instructionInputRef}
        name="content"
        value={formData.content}
        onChange={onInputChange}
        className="instruction-form__input"
        placeholder="Type your instructions here..."
        required
        rows={6}
        disabled={isSubmitting}
      />
      
      <div className="form-actions">
        <p className="form-hint">
          {hasError 
            ? "Review the error details below and click 'Regenerate Script' or 'Auto-Repair' in the footer."
            : "Enter your instructions and click 'Generate Script' in the footer."}
        </p>
        {status && (
          <div className="status-message">
            <div className={`status-${status.type}`}>
              {status.message}
            </div>
          </div>
        )}
      </div>
      {children}
    </form>
  );
};

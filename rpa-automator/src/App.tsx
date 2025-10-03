import React, { useState, useRef } from 'react';
import TaskListSidebar from './components/Sidebar';
import './App.css';

interface ApiResponse {
  status: string;
  message: string;
  filepath?: string;
}

const App: React.FC = () => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<{type: 'success' | 'error', message: string} | null>(null);
  const instructionInputRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmitInstruction = async (event: React.FormEvent) => {
    event.preventDefault();
    const instruction = instructionInputRef.current?.value.trim();
    
    if (!instruction) {
      setSubmitStatus({ type: 'error', message: 'Please enter an instruction' });
      return;
    }

    setIsSubmitting(true);
    setSubmitStatus(null);

    try {
      const response = await fetch('http://localhost:8000/api/instructions/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content: instruction }),
      });

      const data: ApiResponse = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'Failed to save instruction');
      }

      setSubmitStatus({ 
        type: 'success', 
        message: `Instruction saved successfully: ${data.filepath}` 
      });
      
      if (instructionInputRef.current) {
        instructionInputRef.current.value = '';
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
      setSubmitStatus({ 
        type: 'error', 
        message: `Error: ${errorMessage}` 
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="rpa-dashboard">
      <TaskListSidebar />
      <main className="dashboard-content">
        <section className="dashboard-column">
          <form onSubmit={handleSubmitInstruction} className="instruction-form">
            <h3 className="instruction-form__title">Enter Your Instructions</h3>
            <textarea 
              ref={instructionInputRef}
              className="instruction-form__input"
              placeholder="Type your instructions here..."
              required
            />
            <div className="form-actions">
              <button 
                type="submit" 
                className={`instruction-form__submit ${isSubmitting ? 'is-loading' : ''}`}
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Saving...' : 'Submit Instruction'}
              </button>
              {submitStatus && (
                <div className={`status-message status-${submitStatus.type}`}>
                  {submitStatus.message}
                </div>
              )}
            </div>
          </form>
        </section>
        
        <section className="dashboard-column">
          <div className="dashboard-card">
            <h3 className="dashboard-card__title">Task Details</h3>
            <p className="dashboard-card__content">Task information will appear here.</p>
          </div>
        </section>
        
        <section className="dashboard-column dashboard-column--wide">
          <div className="dashboard-card">
            <h3 className="dashboard-card__title">Output</h3>
            <p className="dashboard-card__content">Task output will be displayed here.</p>
          </div>
        </section>
      </main>
    </div>
  );
};

export default App;
